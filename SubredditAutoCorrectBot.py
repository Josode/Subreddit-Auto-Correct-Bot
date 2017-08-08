import praw
from prawcore import NotFound
from SubAutoCorrectBot import Config
import time
import re
import traceback
import logging

past_comments = []  # comment id's already replied to
blacklist = []  # wont reply to users or in subs
subs_all = []  # over a million subreddits to test percent similarity with
subs_popular = []  # over a thousand popular subreddits which are weighted more


close = list("qwertyuiop[asdfghjkl;zxcvbnm,")  # letters and char's that are close together on keyboard
sub = "all"
comment_fetch_limit = 800
threshold = 75.0  # the percent certainty the program must be in order to reply.

# ignores comments like "someone
ignore_phrases = ['we need a', 'someone make a', 'there should be a ', 'we need an', 'someone make an',
                  'there should be an', 'needs to make', 'should be a thing', 'needs to be a thing', 'needs to make a',
                  'needs to be', 'needs to be a', 'be called the', 'call it', 'make it', 'name it', 'someone make',
                  'isnt already a', "isn't already a", "should be called", 'rename this sub', 'rename', 'renamed']

# get each word from subs.txt and append to subs_all
with open("subs.txt", "r")as file:
    data = file.readlines()
    for line in data:
        subs_all.append(line.replace('\n', ''))

# get each word from sub_popular.txt and append to subs_popular
with open("subs_popular.txt", "r")as file:
    data = file.readlines()
    for line in data:
        subs_popular.append(line.replace('\n', ''))


# Checks if subreddit exists
def sub_exists(subreddit, r):
    exists = True
    try:
        r.subreddits.search_by_name(subreddit, exact=True)
    except NotFound:
        exists = False
    return exists


# open past comments txt file and append all id's to list. create new file if doesnt exist
def past_replies():
    try:
        with open("PastComments.txt", 'r')as _file:
            for comment in _file.readlines():
                comment = comment.replace("\n", "").lower()
                past_comments.append(comment)

    except FileNotFoundError:
        with open("PastComments.txt", 'w'):
            print("No PastComments.txt file found. Creating.")
            pass


# opens past repliess file and writess all current past replies
def update_past_replies():
    with open("PastComments.txt", 'w') as file_:
        for item in past_comments:
            file_.write(str(item) + "\n")


# open blacklist file, if doesnt exist makes new one
def blacklist_file():
    try:
        with open("Blacklist.txt", 'r')as file_:
            for item in file_.readlines():
                item = item.replace("\n", "").lower()
                blacklist.append(item)

    except FileNotFoundError:
        with open("Blacklist.txt", 'w'):
            print("No Blacklist.txt file found. Creating.")
            pass


def bot_login():
    _reddit_ = praw.Reddit(username=Config.username,
                           password=Config.password,
                           client_id=Config.client_id,
                           client_secret=Config.client_secret,
                           user_agent="Auto-corrects mentions of subreddits By /u/Josode")
    print(_reddit_.user.me())

    return _reddit_


# test similarity between user inputted sub and 1 mil + subs in subs.txt. returns closest sub and percent similarity
def test_similarity(sub_extracted, comment, r):
    sub_extracted_str = sub_extracted
    sub_extracted = list(sub_extracted)
    sub_type = comment.subreddit.subreddit_type

    results = {}

    for testcase in subs_all:
        testcase_list = list(testcase.lower())
        testcase_str = testcase

        # remove excess spaces
        for char in sub_extracted:
            if char == " ":
                sub_extracted.remove(char)

        # count of equal/not equal
        equal = 0
        notequal = 0
        len_difference = abs(len(sub_extracted) - len(testcase_list))

        if testcase_str in subs_popular:
            equal += 1

        if sub_type == 'public':
            equal += 0.15
        elif sub_type == 'private' or sub_type == 'restricted':
            notequal += 0.15

        # accounts for difference in length
        notequal += (len_difference / 3) * 2

        # test similarity
        for i in range(0, len(testcase_list)):
            try:
                if sub_extracted[i] == testcase_list[i]:
                    equal += 1
                # tests if it equals any keys nearby on keyboard for mis-clicks
                elif (testcase_list[i] == close[close.index(sub_extracted[i]) - 1]) or \
                     (testcase_list[i] == close[close.index(sub_extracted[i]) + 1]):
                    equal += 0.45
                # if chars at index don't equal, checks neighboring indexes for extra-clicks
                elif sub_extracted[i+1] == testcase_list[i] or sub_extracted[i-1] == testcase_list[i]:
                    equal += 0.6
                elif sub_extracted[i+2] == testcase_list[i] or sub_extracted[i-2] == testcase_list[i]:
                    equal += 0.2
                elif sub_extracted[i + 3] == testcase_list[i] or sub_extracted[i - 3] == testcase_list[i]:
                    equal += 0.05
                else:
                    notequal += 1
            except IndexError:
                pass
            except ValueError:
                pass

        # determines if testcase_list or sub_extracted is longer, and uses longer one as numerator
        if len(testcase_list) > len(sub_extracted):
            results[testcase_str] = equal / (len(testcase_list)+notequal) * 100
        else:
            results[testcase_str] = equal / (len(testcase_list)+notequal) * 100

    # creates individual lists for keys and values to determine max percent and for which key/testcase
    percents_list = list(results.values())
    keys = list(results.keys())

    # best match
    print("\nTop matches for \"" + sub_extracted_str + "\":")
    top_match_sub = keys[percents_list.index(max(percents_list))]
    top_match_percent = max(percents_list)
    print(top_match_sub + ': ' + str(top_match_percent) + " %")

    # sorts percents and gets 2nd and 3rd best matches
    percents_list.sort()
    second_match_sub = keys[percents_list.index(percents_list[-2])]
    second_match_percent = str(percents_list[-2])
    print(second_match_sub + ': ' + second_match_percent + " %")

    third_match_sub = keys[percents_list.index(percents_list[-3])]
    third_match_percent = str(percents_list[-3])
    print(third_match_sub + ': ' + third_match_percent + " %\n")

    return [top_match_sub, top_match_percent]


def run_bot(r):
    subreddit = r.subreddit(sub)
    comments = subreddit.stream.comments()
    start = round(time.time(), 1)
    print("start time: " + str(start))

    for comment in comments:

        if comment.created < start:
            continue

        if str(comment.subreddit) in blacklist or str(comment.author) in blacklist or comment.id in past_comments:
            continue

        comment_string = comment.body
        comment_html = comment.body_html

        # attempts to filter out most bots
        if 'bot' in comment_string.lower() or 'bot' in str(comment.author).lower() or 'was performed automatically'\
                in comment_string.lower():
            continue

        for phrase in ignore_phrases:
            if str(phrase) + " /r/" in comment_string or "/r/ " + phrase in comment_string:
                continue

        # find comments with sub mention
        if '/r/' in comment_string:

            # grabs comments html and finds subreddit name.
            extracted_sub = re.search('<a href="/r/(.+?)">', comment_html)

            # reply and display info on comment
            def reply_to_comment(sub):
                print("\n\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
                print("Comment found with id '" + str(comment.id) + "' by /u/" + str(comment.author) + " in" + " /r/"
                      + str(comment.subreddit))
                print("Threshold: {}".format(threshold))
                print("Comment source: " + comment.body)
                print("\nExtracted subreddit: " + sub)
                top_match = test_similarity(sub_extracted=sub, comment=comment, r=r)
                top_match_sub = top_match[0]
                top_match_percent = round(top_match[1], 2)

                if top_match_percent >= 100.0:
                    top_match_percent = 99.9

                # adds nsfw warning in comment if nsfw
                sub_nsfw = r.subreddit(top_match_sub).over18
                nsfw = ''
                if sub_nsfw:
                    print(str(top_match_sub) + " is NSFW.")
                    nsfw = ' (NSFW)'

                if top_match_percent >= threshold:
                    try:
                        comment.reply('It looks like "/r/' + sub_extracted + '" is not a subreddit.'
                                      "\n\n Maybe you're looking for **/r/"+top_match_sub+nsfw+"** with a **" +
                                      str(top_match_percent) + "%** match."
                                      "\n\n***\n"
                                      "^^I'm ^^a ^^bot, ^^beep ^^boop "
                                      "^^| ^^Downvote ^^to ^^DELETE. "
                                      "^^| [^^Contact ^^me]"
                                      "(http://www.reddit.com/message/compose/?to=SubAutoCorrectBot&subject="
                                      "Contact+creator) ^^| ^^[Opt-out]"
                                      "(http://www.reddit.com/message/compose/?to=SubAutoCorrectBot&subject="
                                      "Opt+Out&message=Click+send+to+opt+out" +
                                      ") ^^| ^^[Feedback]"
                                      "(https://www.reddit.com/r/SubAutoCorrectBot/comments/6s2sht/"
                                      "feedback_questions_concerns_bugs_suggestions_etc"
                                      "/) ")

                        print("REPLY SENT!")
                        past_comments.append(comment.id)
                        update_past_replies()
                        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n")
                    except:
                        pass
                else:
                    print("Percent below threshold. NOT replying.")
                    update_past_replies()
                    past_comments.append(comment.id)
                    print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n")

            if extracted_sub:
                sub_extracted = extracted_sub.group(1).lower()

                # removes occasional / found at end of sub
                slash_count = 0
                for char in sub_extracted:
                    if char == '/':
                        slash_count += 1

                if sub_exists(sub_extracted, r) or slash_count > 0 or len(sub_extracted) <= 2:
                    continue
                else:
                    reply_to_comment(sub_extracted)

        update_past_replies()

    print("No Comments found...")

past_replies()
blacklist_file()
reddit = bot_login()
print("Running bot on /r/" + sub)

while True:
    try:
        run_bot(reddit)
    except Exception as e:
        logging.error(traceback.format_exc())
    time.sleep(1)
