
sub_list_mil = []
sub_list_popular = []
subs_private = 0
subs_public = 0


with open('subs.txt', 'r') as stuff:
    data = stuff.readlines()
    for sub in data:
        sub_list_mil.append(sub)

with open('subs_popular.txt', 'r') as stuff:
    data = stuff.readlines()
    for sub in data:
        sub_list_popular.append(sub)

print("subs public: ") + str(subs_public)
print("subs private: " + str(subs_private))
print("subs total in popular: " + str(len(sub_list_popular)))
print("subs total in mil: " + str(len(sub_list_mil)))
