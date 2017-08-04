import praw
import Config
import time
import re


past_comments = []
blacklist = []
test_words = []
close = list("qwertyuiop[asdfghjkl;zxcvbnm,")
sub = "all"
comment_fetch_limit = 500


# FOR TESTING:
whitelist = 'LinkFixBot'


# get each word from file and append to list
with open("subs_list.txt", "r")as words:
    data = words.readlines()
    for line in data:
        line = line.replace('/r/', '')
        test_words.append(line.replace('\n', ''))


# open past comments txt file and append all id's to list. create new file if doesnt exist
def past_replies():
    try:
        with open("PastComments.txt", 'r')as file:
            for comment in file.readlines():
                comment = comment.replace("\n", "").lower()
                past_comments.append(comment)

    except FileNotFoundError:
        with open("PastComments.txt", 'w'):
            print("No PastComments.txt file found. Creating.")
            pass


def blacklist_file():
    try:
        with open("Blacklist.txt", 'r')as file:
            for item in file.readlines():
                item = item.replace("\n", "").lower()
                blacklist.append(item)

    except FileNotFoundError:
        with open("Blacklist.txt", 'w'):
            print("No Blacklist.txt file found. Creating.")
            pass


def bot_login():
    reddit = praw.Reddit(username=Config.username,
                         password=Config.password,
                         client_id=Config.client_id,
                         client_secret=Config.client_secret,
                         user_agent="I auto-correct subreddit mentions.")

    reddit.login(username=Config.username, password=Config.password, disable_warning=True)
    return reddit


def test_similarity(sub_extracted):
    sub_extracted_str = sub_extracted
    sub_extracted = list(sub_extracted)

    results = {}

    for testcase in test_words:
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
                    equal += 0.65
                # if chars at index don't equal, checks neighboring indexes for extra-clicks
                elif sub_extracted[i+1] == testcase_list[i] or sub_extracted[i-1] == testcase_list[i]:
                    equal += 0.65
                elif sub_extracted[i+2] == testcase_list[i] or sub_extracted[i-2] == testcase_list[i]:
                    equal += 0.25
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
    print("Top matches for \"" + sub_extracted_str + "\":\n")
    top_match_sub = keys[percents_list.index(max(percents_list))]
    print(top_match_sub)
    top_match_percent = max(percents_list)
    print(str(top_match_percent) + " %\n")

    # sorts percents and gets 2nd and 3rd best matches
    percents_list.sort()
    print(keys[percents_list.index(percents_list[-2])])
    print(str(percents_list[-2]) + " %\n")

    print(keys[percents_list.index(percents_list[-3])])
    print(str(percents_list[-3]) + " %")

    return [top_match_sub, top_match_percent]


def run_bot(r):
    subreddit = r.get_subreddit(sub)
    comments = subreddit.get_comments(limit=comment_fetch_limit)

    for comment in comments:
        if str(comment.subreddit) in blacklist or str(comment.author) in blacklist or comment.id in past_comments:
            continue

        comment_string = comment.body

        if 'bot' in comment_string.lower() or 'bot' in str(comment.author).lower():
            continue

        if '/r/' in comment_string:
            extracted_sub = re.search('/r/(.+?) ', comment_string)

            def start_test(sub):
                print("\n\n-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n")
                print("Comment found: " + comment_string)
                print("\nExtracted subreddit: " + sub)
                top_match = test_similarity(sub_extracted=sub)
                top_match_sub = top_match[0]
                top_match_percent = round(top_match[1], 2)

                if top_match_percent >= 90.0 and top_match_percent != 100.0:
                    comment.reply("Oops... It looks like you miss-spelled a subreddit name."
                                  "\n\n I am **" + str(top_match_percent) + "%** sure that you meant **/r/"
                                  + top_match_sub+"**."
                                  "\n\n This bot is **testing**. The current threshold is **90%**."
                                  "\n\n***\n"
                                  "^^| ^^I'm ^^a ^^bot, ^^beep ^^boop "
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
                    print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n")
                else:
                    print("Percent too low or exact match. NOT replying.")
                    past_comments.append(comment.id)
                    print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n")

            if extracted_sub:
                alphabet = 'qwertyuiopasdfghjklzxcvbnm_'

                sub_extracted = extracted_sub.group(1).lower()

                for char in sub_extracted:
                    if char not in alphabet:
                        sub_extracted.replace(char, '')

                print(sub_extracted.upper())

                start_test(sub_extracted)

        with open("PastComments.txt", 'w') as file:
            for item in past_comments:
                file.write(str(item) + "\n")

    print("No Comments found...")

past_replies()
blacklist_file()
r = bot_login()

while True:
    run_bot(r)
    time.sleep(0)
