import timeit
def shortLong(string):
    split = string.split()
    split = [i for i in split if (i != "the") & (i != "a")]
    l = 0
    for i in split:
        if len(i) > 8:
            l += 1
    return l / len(split)


#LOAD STRING
example = ""
with open("formalSentences.txt",encoding="utf8") as f:
    for line in f:
        example = example + line

#PRINT RESULT
print("Pure Python: ")
print(str(int(shortLong(example) * 100)) + "%")

#TIMEIT
print("Elapsed time: {:.5f}s".format(sum(timeit.repeat("shortLong(example)",globals=globals(),number=1,repeat=1))/1))