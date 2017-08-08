import time
from time import sleep
import praw
from LinkRepairBot import Config

r = praw.Reddit(username=Config.username,
                password=Config.password,
                client_id=Config.client_id,
                client_secret=Config.client_secret,
                user_agent="Deletes comments under threshold for /u/SubAutoCorrectBot")

print('Delete downvoted comments for /u/SubAutoCorrectBot')

user = r.redditor('SubAutoCorrectBot')
comments = user.comments.new(limit=None)

threshold = 0
past_deleted = []


def past_replies():
    try:
        with open("PastDeleted.txt", 'r')as file:
            print("Existing file found.")
            for id in file.readlines():
                id = id.replace("\n", "").lower()
                past_deleted.append(id)

    except FileNotFoundError:
        with open("PastDeleted.txt", 'w'):
            print("No file found. New one created.")
            pass

past_replies()

while True:
    for comment in comments:
        try:
            if comment.score < threshold and comment.id not in past_deleted:
                comment.delete()
                past_deleted.append(comment.id)
                print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
                print("\n\nComment in " + str(comment.subreddit) + " deleted on " +
                      time.asctime(time.localtime(time.time())) + ": \n\n" + str(comment.body) + "\n")
                print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-")
        except:
            time.sleep(5)
            continue

    with open("PastDeleted.txt", 'w') as file:
        for item in past_deleted:
            file.write(str(item) + "\n")
    sleep(3)
