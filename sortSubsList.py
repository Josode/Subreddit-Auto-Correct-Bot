
# copy and pasted cotent of https://www.reddit.com/r/ListOfSubreddits/wiki/listofsubreddits
# this program simply filters out non-subreddit content from copy
# result: clean list of 1000 plus subs

subs = []

with open('subreddits_list_unsorted.txt', 'r')as file:
    data = file.readlines()
    for line in data:
        if '/r/' not in line or ' ' in line:
            line.replace(line, '')
        else:
            subs.append(line)

with open('subs_list.txt', 'w')as file:
    for item in subs:
        file.write(item)