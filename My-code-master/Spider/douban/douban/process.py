import jieba
from wordcloud import WordCloud
import matplotlib.pyplot as plt



def build():
    text = open('/Users/LiweiHE/acquisition/douban.txt','rb').read()

    text_jieba = jieba.cut(text) # 默认是精确模式
    text_jieba = " ".join(text_jieba)

    font = r'/Users/LiweiHE/PycharmProjects/simfang.ttf'
    wc = WordCloud(background_color="black", width=1000, font_path=font,height=1000, margin=2).generate(text_jieba)

    plt.imshow(wc)
    plt.axis("off")
    plt.show()
    wc.to_file('test.png')


build()