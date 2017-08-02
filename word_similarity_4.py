
test_words = []

# get each word from file and append to list
with open("word_list", "r")as words:
    data = words.readlines()
    for line in data:
        test_words.append(line.replace('\n', ''))


userinput = input("enter word: \n").lower()
# holds percent match for each word in order to calculate best match
results = {}

close = list("qwertyuiop[asdfghjkl;zxcvbnm,")


def test_similarity(testcase, input):
    print("\ncomparing \""+input+"\" with \""+testcase+"\"")

    inputlist = list(input)
    testcase = list(testcase.lower())

    # remove excess spaces
    for char in inputlist:
        if char == " ":
            inputlist.remove(char)

    # count of equal/not equal
    equal = 0
    notequal = 0
    len_difference = len(userinput) - len(testcase)

    # accounts for difference in length
    notequal += len_difference
    # make len difference positive
    if len_difference < 0:
        len_difference *= -1

    # test similarity
    for i in range(0, len(testcase)):
        try:
            if inputlist[i] == testcase[i]:
                equal += 1
            # tests if it equals any keys nearby on keyboard for mis-clicks
            elif (testcase[i] == close[close.index(inputlist[i]) - 1]) or \
                 (testcase[i] == close[close.index(inputlist[i]) + 1]):
                equal += 0.85
            # if chars at index don't equal, checks neighboring indexes for extra-clicks
            elif inputlist[i+1] == testcase[i] or inputlist[i-1] == testcase[i]:
                equal += 1
            elif inputlist[i + 2] == testcase[i] or inputlist[i - 2] == testcase[i]:
                equal += .4
            else:
                notequal += 1
        except IndexError:
            pass

    print("equal: "+str(equal) + "\nnot equal: "+str(notequal))

    # determines if testcase or input is longer, and uses longer one as numerator
    if len(testcase) > len(inputlist):
        print("\nSimilarity: " + str(equal / len(testcase) * 100) + " %\n")
        print("----------------------------------------------\n")
        return equal / len(testcase) * 100
    else:
        print("\nSimilarity: " + str(equal / len(inputlist) * 100) + " %\n")
        print("----------------------------------------------\n")
        return equal / len(inputlist) * 100

# adds key and value for each testcase word and percent calculated to dict
for word in test_words:
    results[word] = (test_similarity(word, userinput))

# creates individual lists for keys and values to determine max percent and for which key/testcase
percents_list = list(results.values())
keys = list(results.keys())

# best match
print("-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-=-\n")
print("Top matches for \""+userinput+"\":\n")
print(keys[percents_list.index(max(percents_list))])
print(str(max(percents_list))+" %\n")

# sorts percents and gets 2nd and 3rd best matches
percents_list.sort()
print(keys[percents_list.index(percents_list[-2])])
print(str(percents_list[-2])+" %\n")

print(keys[percents_list.index(percents_list[-3])])
print(str(percents_list[-3])+" %")