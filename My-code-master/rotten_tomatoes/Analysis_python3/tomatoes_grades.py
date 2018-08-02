#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sat Apr 14 23:20:57 2018

@author: LiweiHE
"""

import pandas as pd
import matplotlib.pyplot as plt 
import matplotlib


address = "/Users/LiweiHE/acquisition/comments.xls"
comment = pd.read_excel(address, sheetname=0, index_col=None, na_values=["NA"])

# line chart
plt.figure(1)

# delete all the record Grades valued 0
comment = comment[comment['Grades']>0]

# grab the Grades attribute of all records
record = comment['Grades'] 
comment = comment.to_excel('/Users/LiweiHE/acquisition/finalised_dataset.xls')
print(record.describe())
list = record.value_counts().sort_index()

x = list.index
y = list
# b--: 蓝色虚线， o-：带点实线
plt.plot(x,y,"o-",linewidth=1) 
plt.xlabel("grades") 
plt.ylabel("amount")
# 将 x轴的值旋转90度
# plt.xticks(rotation=90)
plt.ylim(0, 60)
plt.title("the distribution of grades")
plt.savefig("grades_linechart.png")







