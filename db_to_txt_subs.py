import sqlite3
sql = sqlite3.connect('sb.db')
cur = sql.cursor()

# Takes 1 mil+ subs from sb.db file and puts them into subs.txt

# 'SELECT last_seen FROM popular'
# 'SELECT idstr FROM popular'
# 'SELECT name FROM subreddits'

cur.execute('SELECT name FROM subreddits')

names = [x[0] for x in cur.fetchall()]

with open('subs.txt', 'w') as handle:
    for name in names:
        if '\n' in str(name):
            name.replace('\n', '')
        handle.write(str(name) + '\n')