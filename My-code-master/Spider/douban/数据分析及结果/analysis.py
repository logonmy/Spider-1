import pandas as pd
import matplotlib.pyplot as plt 
import matplotlib


address = "/Users/LiweiHE/acquisition/comments.xls"
comment = pd.read_excel(address, sheetname=0, index_col=None, na_values=["NA"])
comment['Time'] = pd.to_datetime(comment['Time'])
comment = comment.sort_values(by='Time')
old = comment[comment.Time < "2018-01-12"]
new = comment[comment.Time >= "2018-01-12"]
comment = old.append(new)
old.to_csv("old_comments.csv")
new.to_csv("new_comments.csv")


# Chinese display
font = r'/Users/LiweiHE/PycharmProjects/simfang.ttf'
myfont = matplotlib.font_manager.FontProperties(fname=font)

# create a window called figure1 for the painting 
plt.figure(1)
# left: position of bars, height: the height of bars, width: the width of bar, 
# yerr: to aviod reaching celling of picture
rects =plt.bar(left = (0.2,0.6),height = (len(old),len(new)),color=('r','g'),width = 0.2,align="center",yerr=0.000001)
# add the text above the bar
def autolabel(rects):
    for rect in rects:
        height = rect.get_height()
        # (x,y, value, size)
        plt.text(rect.get_x()+0.03,1.05*height, '%s' % int(height),size = 15)
        
autolabel(rects)
# place the name of bars 
plt.xticks((0.2,0.6),("上映前就发表的评论","上映后才发表的评论"),fontproperties=myfont)
# x-axis range 
plt.xlim(0,1)
# y-axis range
plt.ylim(0,350)

plt.ylabel("人数", fontproperties=myfont)
plt.title('无问东西评论的分类', fontproperties=myfont)
plt.savefig("无问东西评论的分类_bar.png")

# pie
plt.figure(2)
# label of every part
labels = ["Before", "After"]
# weight of every part, 自动百分比化
sizes = [len(old),len(new)]
# colors of every part
colors = ['red','green']
# 割裂pie的痕迹宽度
explode = (0.05,0)
# labeldistance: 标签与图片的距离 倍径， autopct：accuracy, pctdistance:百分比的text离圆心的距离
patches,l_text,p_text = plt.pie(sizes, colors=colors, explode=explode, 
                                labels=labels, labeldistance = 1.1, 
                                startangle=90, pctdistance = 0.6,
                                autopct = '%3.1f%%',shadow = False)
# x=y
plt.axis('equal')
# https://blog.csdn.net/helunqu2017/article/details/78641290
# 右上角标签
plt.legend(prop=myfont)
plt.title('无问东西评论的分类', fontproperties=myfont)
plt.savefig("无问东西评论的分类_pie.png")

# line chart
plt.figure(3)
# grab the Time attribute of all records
record = comment['Time']

# delete all the duplicates
record = record.drop_duplicates()

# calculate the number of comments coming out in a same day
time_array = []
for time in record:
    count =len(comment[comment.Time==time])
    time_array.append(count)

x = record
y = time_array
# b--: 蓝色虚线， o-：带点实线
plt.plot(x,y,"o-",linewidth=1) 
plt.xlabel("日期", fontproperties=myfont) 
plt.ylabel("发表数量", fontproperties=myfont)
# 将 x轴的值旋转90度
plt.xticks(rotation=90)
plt.ylim(0, 110)
plt.title("每日发表评论的数量", fontproperties=myfont)
plt.savefig("无问东西评论的发布时间_linechart.png")






