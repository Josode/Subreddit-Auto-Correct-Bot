import praw
import Config
from prawcore import NotFound
import time
import re
import traceback
import logging
import popularsubs_subscribercount


# SubAutoCorrectBot2 attempting to re-orginize reply to comment to allow for more checks

past_comments = []  # comment id's already replied to
blacklist = []  # wont reply to users or in subs
subs_all = []  # over a million subreddits to test percent similarity with
subs_popular = []  # over a thousand popular subreddits which are weighted more

close = list("1234567890qwertyuiop[asdfghjkl:zxcvbnm,")  # letters and char's that are close together on keyboard
sub = "all"
comment_fetch_limit = 1000
threshold = 80.0  # the percent certainty the program must be above in order to reply. (80.0 generally best)

# ignores comments like "someone make an /r/newsubreddit"
ignore_phrases = ['we need a', 'someone make a', 'there should be a ', 'we need an', 'someone make an',
                  'there should be an', 'needs to make', 'should be a thing', 'needs to be a thing', 'needs to make a',
                  'needs to be', 'needs to be a', 'be called the', 'call it', 'make it', 'name it', 'someone make',
                  'isnt already a', "isn't already a", "should be called", 'rename this sub', 'rename', 'renamed']

reply_footer = "\n\n***\n^^I'm ^^a ^^bot, ^^beep ^^boop "\
               "^^| ^^downvote ^^to ^^DELETE. "\
               "^^| [^^Contact ^^creator]"\
               "(http://www.reddit.com/message/compose/?to=SubAutoCorrectBot&subject="\
               "Contact+creator) ^^| ^^[Opt-out]"\
               "(http://www.reddit.com/message/compose/?to=SubAutoCorrectBot&subject="\
               "Opt+Out&message=Click+send+to+opt+out"\
               ") ^^| ^^[Feedback]"\
               "(https://np.reddit.com/r/SubAutoCorrectBot/) "\
               "^^| ^^[Code]"\
               "(https://github.com/Josode/Subreddit-Auto-Correct-Bot) "

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
                           user_agent="Auto-corrects misspelled mentions of subreddits By /u/Josode")

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

        # adds different weights for different subscriber counts to popular subreddits
        try:
            if testcase_str in subs_popular:

                subscribers_count = popularsubs_subscribercount.subscribercount
                subscribers = subscribers_count[testcase_str]

                if 0 >= subscribers < 5000:
                    equal += 0.8
                elif 5000 >= subscribers < 20000:
                    equal += 0.85
                elif 20000 >= subscribers < 100000:
                    equal += 0.95
                elif 100000 >= subscribers < 300000:
                    equal += 1.3
                elif 300000 >= subscribers < 500000:
                    equal += 1.45
                elif 500000 >= subscribers < 2000000:
                    equal += 1.55
                elif 2000000 >= subscribers < 7000000:
                    equal += 1.8
                elif 7000000 >= subscribers:
                    equal += 1
        except KeyError:
            continue

        # prefer not to reply to private subs
        if sub_type == 'private' or sub_type == 'restricted':
            notequal += 0.5

        # accounts for difference in length
        notequal += (len_difference / 10) * 6.5

        # test similarity
        for i in range(0, len(testcase_list)):
            try:
                if sub_extracted[i] == testcase_list[i]:
                    equal += 1
                # tests if it equals any keys nearby on keyboard for mis-clicks
                elif (testcase_list[i] == close[close.index(sub_extracted[i]) - 1]) or \
                     (testcase_list[i] == close[close.index(sub_extracted[i]) + 1]):
                    equal += 0.35
                # if chars at index don't equal, checks neighboring indexes for extra-clicks
                elif sub_extracted[i+1] == testcase_list[i] or sub_extracted[i-1] == testcase_list[i]:
                    equal += 0.7
                elif sub_extracted[i+2] == testcase_list[i] or sub_extracted[i-2] == testcase_list[i]:
                    equal += 0.65
                elif sub_extracted[i + 3] == testcase_list[i] or sub_extracted[i - 3] == testcase_list[i]:
                    equal += 0.4
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
    percents_list.remove(top_match_percent)

    # sorts percents and gets 2nd and 3rd best matches
    percents_list.sort()
    second_match_sub = keys[percents_list.index(max(percents_list))]
    second_match_percent = max(percents_list)
    print(second_match_sub + ': ' + str(second_match_percent) + " %")
    percents_list.remove(second_match_percent)

    third_match_sub = keys[percents_list.index(max(percents_list))]
    third_match_percent = max(percents_list)
    print(third_match_sub + ': ' + str(third_match_percent) + " %\n")
    percents_list.remove(third_match_percent)

    return [top_match_sub, top_match_percent]


def run_bot(r):
    subreddit = r.subreddit(sub)
    comments = subreddit.stream.comments()
    start = round(time.time(), 1)
    print("start time: " + str(start))

    for comment in comments:

        if comment.created < start:
            continue

        if str(comment.subreddit).lower() in blacklist or str(comment.author).lower() in blacklist or comment.id in \
                past_comments:
            continue

        comment_string = comment.body
        comment_html = comment.body_html
        comment_id = comment.id

        def reply_to_comment(sub, type):
            if type == 'sub':
                # change "a" to "an" if percent in 80s.
                a = 'a'
                if str(top_match_percent)[0] == '8':
                    a = 'an'

                normal_reply = 'It looks like "/r/' + sub + '" is not a subreddit.' + \
                              "\n\n Maybe you're looking for **/r/" + top_match_sub + nsfw + "**. " + reply_footer
                # + "** "with "+a+" **" + str(top_match_percent) + "%** match." + reply_footer +"** "

                april_fools ='It looks like "[/r/' + sub + '](' \
                               'https://www.youtube.com/watch?v=dQw4w9WgXcQ)" is not a subreddit.' + \
                              "\n\n Maybe you're looking for [**/r/" + top_match_sub + nsfw + "**](" \
                              "https://www.youtube.com/watch?v=dQw4w9WgXcQ) with "+a+" **" + \
                              str(top_match_percent) + "%** match." + reply_footer

                comment.reply(normal_reply)
            elif type == 'user':
                print("\nUser most likely meant to mention a user.")
                comment.reply('It looks like "/r/' + sub + '" is not a subreddit.'
                              "\n\n Maybe you meant to mention the user " + "**/u/" + sub + "**."
                              + reply_footer)

            print("REPLY SENT!")
            past_comments.append(comment_id)
            update_past_replies()

        for phrase in ignore_phrases:
            if phrase + " /r/" in comment_string.lower() or "/r/ " + phrase in comment_string.lower()\
                    or phrase + " r/" in comment_string.lower() or "r/ " + phrase in comment_string.lower():
                continue

        # find comments with sub mention
        if '/r/' in comment_string or 'r/' in comment_string:

            # grabs comments html and finds subreddit name.
            extracted_sub = re.search('<a href="/r/(.+?)">', comment_html)

            if extracted_sub:
                sub_extracted = extracted_sub.group(1).lower()

                # removes occasional / found at end of sub
                slash_count = 0
                for char in sub_extracted:
                    if char == '/':
                        slash_count += 1

                if sub_exists(sub_extracted, r) or slash_count > 0 or len(sub_extracted) <= 2:
                    continue

                # comment now eligible to be replied to. Continue with checks
                print("\n==-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
                print("Comment found with id '" + str(comment_id) + "' by /u/" + str(comment.author) + " in" + " /r/"
                      + str(comment.subreddit))
                print("Threshold: {}".format(threshold))
                print("Comment source: " + comment.body)
                print("\nExtracted subreddit: {}".format(sub_extracted))


                '''
                # see if non-existing sub is really a user (people sometimes do /r/ instead of /u/)
                try:
                    user_id = r.redditor(sub_extracted).id
                    print("User exists with id: " + user_id)
                    reply_to_comment(sub_extracted, type='user')
                    continue
                except:
                    print("User doesnt exist!")
                '''

                # returns list: [top_match_sub, top_match_percent]
                top_match = test_similarity(sub_extracted=sub_extracted, comment=comment, r=r)

                top_match_sub = top_match[0]
                top_match_percent = round(top_match[1], 2)
                top_sub_r = r.subreddit(top_match_sub)  # praw object of top subreddit

                if sub_extracted == "traaa" or sub_extracted == "traaaa":
                    top_match_sub = "traaaaaaannnnnnnnnns"

                if top_match_percent >= 100.0:
                    top_match_percent = 99.9

                submissions = 0
                for submission in top_sub_r.hot(limit=5):
                    title = submission.title
                    submissions += 1


                if submissions <= 2:
                    print("2 or less posts on subreddit. NOT replying.")
                    continue


                # adds nsfw warning in comment if nsfw
                sub_nsfw = top_sub_r.over18
                nsfw = ''
                if sub_nsfw:
                    print(str(top_match_sub) + " is NSFW.")
                    nsfw = ' (NSFW)'


                # do secondary check to see if comment has been edited
                new_comment_string = r.comment(comment_id).body
                if new_comment_string != comment_string:
                    print("comment edited while running auto correct. NOT replying")
                    print("Before: " + comment_string)
                    print("After: " + new_comment_string)
                    continue
                

                # call function to send comment
                if top_match_percent >= threshold:
                    try:
                        reply_to_comment(sub_extracted, type="sub")
                    except Exception as e:
                        logging.error(traceback.format_exc())
                        print("\n\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-"
                              "\nERROR when trying to run reply_to_comment\n\n"
                              "-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n")
                        continue
                else:
                    print("Percent below threshold. NOT replying.")
                    update_past_replies()
                    past_comments.append(comment_id)

        update_past_replies()

    print("No Comments found...")

past_replies()
blacklist_file()
reddit = bot_login()

while True:
    try:
        run_bot(reddit)
    except Exception as e:
        logging.error(traceback.format_exc())
    time.sleep(0)
