import jieba
jieba.load_userdict("../dictionary/mycardict.txt")
seg_list = jieba.cut("看看家用车")
words = "/ ".join(seg_list)
print(words)