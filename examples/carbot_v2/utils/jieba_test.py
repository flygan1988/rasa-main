import jieba
jieba.load_userdict("../dictionary/mycardict.txt")
seg_list = jieba.cut("看看朗逸中最便宜的车型")
words = "/ ".join(seg_list)
print(words)