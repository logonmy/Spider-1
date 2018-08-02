#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Created on Sun Apr 15 17:34:12 2018

@author: LiweiHE
"""
import pandas as pd
import matplotlib.pyplot as plt 
import numpy as np    

from sklearn.cluster import Birch    
from sklearn.cluster import KMeans   

address = "/Users/LiweiHE/acquisition/comments.xls"
comment = pd.read_excel(address, sheetname=0, index_col=None)

# delete all the record Grades valued 0
comment = comment[comment['Grades']>0]

# grab the Grades and length of comment attributes of all records
record = comment.loc[:,['Grades','length of Comment']]

clf = KMeans(n_clusters=3)    
y_pred = clf.fit_predict(record)    

x = comment['Grades']
y = comment['length of Comment']


plt.scatter(x, y, c=y_pred, marker='x')     
plt.title("Kmeans-comments")     
plt.xlabel("Grades")    
plt.ylabel("length of Comments")    
plt.legend(["Rank"])     
plt.savefig("Kmeans-comments.png")