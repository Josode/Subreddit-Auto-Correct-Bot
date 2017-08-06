import praw
from SubAutoCorrectBot import Config
import time
import re

# to do: add weight for more popular subs (in subs_popular.txt)

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
                  'needs to be', 'needs to be a']

# get each word from file and append to list
with open("subs.txt", "r")as file:
    data = file.readlines()
    for line in data:
        subs_all.append(line.replace('\n', ''))


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
                           user_agent="Auto-corrects mentions of subreddits (ex: /r/asjreddut -> "
                                      "/r/askreddit). By /u/Josode")

    _reddit_.login(username=Config.username, password=Config.password, disable_warning=True)
    return _reddit_


# test similarity between user inputted sub and 1 mil + subs in subs.txt. returns closest sub and percent similarity
def test_similarity(sub_extracted):
    sub_extracted_str = sub_extracted
    sub_extracted = list(sub_extracted)

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

        # accounts for difference in length
        notequal += len_difference

        # test similarity
        for i in range(0, len(testcase_list)):
            try:
                if sub_extracted[i] == testcase_list[i]:
                    equal += 1
                # tests if it equals any keys nearby on keyboard for mis-clicks
                elif (testcase_list[i] == close[close.index(sub_extracted[i]) - 1]) or \
                     (testcase_list[i] == close[close.index(sub_extracted[i]) + 1]):
                    equal += 0.70
                # if chars at index don't equal, checks neighboring indexes for extra-clicks
                elif sub_extracted[i+1] == testcase_list[i] or sub_extracted[i-1] == testcase_list[i]:
                    equal += 0.65
                elif sub_extracted[i+2] == testcase_list[i] or sub_extracted[i-2] == testcase_list[i]:
                    equal += 0.30
                elif sub_extracted[i + 3] == testcase_list[i] or sub_extracted[i - 3] == testcase_list[i]:
                    equal += 0.03
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
    subreddit = r.get_subreddit(sub)
    comments = subreddit.get_comments(limit=comment_fetch_limit)

    for comment in comments:
        if str(comment.subreddit) in blacklist or str(comment.author) in blacklist or comment.id in past_comments:
            break

        comment_string = comment.body
        comment_html = comment.body_html

        '''
        # attempts to filter out most bots
        if 'bot' in comment_string.lower() or 'bot' in str(comment.author).lower():
            break
        '''

        for phrase in ignore_phrases:
            if str(phrase) + " /r/" in comment_string or "/r/ " + phrase in comment_string:
                continue

        if '/r/' in comment_string:
            
            # grabs comments html and finds subreddit name.
            extracted_sub = re.search('<a href="/r/(.+?)">', comment_html)

            def reply_to_comment(sub):
                print("\n\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
                print("Comment found with id '" + str(comment.id) + "' by /u/" + str(comment.author))
                print("Threshold: {}".format(threshold))
                print("Comment source: " + comment.body)
                print("\nExtracted subreddit: " + sub)
                print("Link: https://www.reddit.com/r/" + sub)
                top_match = test_similarity(sub_extracted=sub)
                top_match_sub = top_match[0]
                top_match_percent = round(top_match[1], 2)

                if top_match_percent >= threshold and top_match_percent != 100.0:
                    try:
                        comment.reply('Oops... It looks like you missspelled "/r/' + sub_extracted + '".'
                                      "\n\n I am **" + str(top_match_percent) + "%** sure that you meant **/r/"
                                      + top_match_sub+"**."
                                      "\n\n***\n"
                                      "^^ ^^I'm ^^a ^^bot, ^^beep ^^boop "
                                      "^^| ^^Downvote ^^to ^^DELETE. "
                                      "^^| [^^Contact ^^me]"
                                      "(http://www.reddit.com/message/compose/?to=LinkFixBot&subject=Contact+creator) "
                                      "^^| ^^[Opt-out]"
                                      "(http://www.reddit.com/message/compose/?to=LinkFixBot&subject=Opt+Out&message="
                                      + str(comment.author) +
                                      ") ^^| ^^[Feedback]"
                                      "(https://www.reddit.com/r/LinkFixBot/comments/6qys25/feedback_questions"
                                      "_complaints_etc_can_be_made_here/) ")

                        print("REPLY SENT!")
                        past_comments.append(comment.id)
                        update_past_replies()
                        print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n")
                    except:
                        pass
                else:
                    print("Percent too low or exact match. NOT replying.")
                    update_past_replies()
                    past_comments.append(comment.id)
                    print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n")

            if extracted_sub:
                sub_extracted = extracted_sub.group(1).lower()

                # removes occasional / found at end of sub
                _sub_ = []
                for char in sub_extracted:
                    if char != '/':
                        _sub_.append(char)
                sub_extracted = ''.join(_sub_)

                reply_to_comment(sub_extracted)

        update_past_replies()

    print("No Comments found...")

past_replies()
blacklist_file()
reddit = bot_login()
print("Running bot on /r/" + sub)

while True:
    run_bot(reddit)
    time.sleep(0)
