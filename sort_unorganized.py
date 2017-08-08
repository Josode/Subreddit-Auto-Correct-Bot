
sub_list_mil = []
sub_list_popular = []


with open('subs.txt', 'r') as stuff:
    data = stuff.readlines()
    for sub in data:
        sub_list_mil.append(sub)

with open('subs_popular.txt', 'r') as stuff:
    data = stuff.readlines()
    for sub in data:
        sub_list_popular.append(sub)

print("subs total in popular: " + str(len(sub_list_popular)))
print("subs total in mil: " + str(len(sub_list_mil)))
