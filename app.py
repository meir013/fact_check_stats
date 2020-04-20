# -*- coding: utf-8 -*-
"""
Created on Sun Oct 29 00:08:23 2017

@author: olevi
"""

from flask import Flask, request,render_template
#from flask import Markup

app = Flask(__name__)

import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
from wordcloud import WordCloud

cols=['author','claimReviewed','title','datePublished','dateCreated','itemReviewed','url']

data=pd.read_csv('olddata_oct12.csv',header=None,names=cols)
#data = pd.DataFrame(columns=cols)   

url='https://storage.googleapis.com/datacommons-feeds/claimreview/latest/data.json'
df = pd.read_json(url, orient='columns')

#data = pd.DataFrame(columns=cols)
count=0
for x in df['dataFeedElement']:
    count+=1
    if count>1000:
        break
    try:
        dic={}
        if x['item'] is None:
            continue
        item=x['item'][0]
        if 'url' in item and item['url'] in set(data['url']):
            continue
        if 'dateCreated' in x:
            dic['dateCreated']=x['dateCreated']
        else:
            if 'dateModified' in x:
                dic['dateCreated']=x['dateModified']
            else:
                dic['dateCreated']=None
        if 'author' in item:
            if 'name' in item['author']:
                dic['author']=item['author']['name'].strip()
            else:
                if 'url' in item['author']:
                    dic['author']=item['author']['url']
        else:
            dic['author']=None
        if 'claimReviewed' in item:
                dic['claimReviewed']=item['claimReviewed']
                if len(dic['claimReviewed'])>50:  
                    j=50
                    while j>0 and dic['claimReviewed'][j]!=' ':
                        j=j-1
                    dic['title']=dic['claimReviewed'][:j]+" ..."
                else:
                    dic['title']=dic['claimReviewed']
        else:
            dic['claimReviewed']=None
            dic['title']=None
        if 'datePublished' in item:
            dic['datePublished']=item['datePublished']
        else:
            dic['datePublished']=None
        if 'itemReviewed' in item and 'author' in item['itemReviewed'] and 'name' in item['itemReviewed']['author']:
            dic['itemReviewed']=item['itemReviewed']['author']['name']
        else:
            dic['itemReviewed']=None
        if 'url' in item:
            dic['url']=item['url']
        else:
            dic['url']=None    
        data = data.append(dic, ignore_index=True)
    except Exception as e: 
        print(e)
        
data.to_csv('olddata_oct12.csv', mode='a', header=False)
#import datetime
from datetime import datetime, timedelta,date
import pytz

cols = ['author','Country Name', 'Country Code']
country=pd.read_csv("map_fact_check_country.csv",header=None,names=cols)
fc_country = country.merge(data,left_on='author', right_on='author',how='inner')
fc_country_df=fc_country['Country Name'].value_counts().rename_axis('country').reset_index(name='count')

#import urllib.request
#from urllib.request import urlopen

#from bs4 import BeautifulSoup
#import json
#import codecs
#import requests

res={}
data['dateCreated2'] = pd.to_datetime(data['dateCreated'],utc=True)
lastweek=len(data[data['dateCreated2']>datetime.now(tz=pytz.utc)-timedelta(days=7)])
res['total']=len(data)
res['lastweek']=lastweek
data['dateCreatedFormat']=data['dateCreated2'].dt.strftime("%Y-%m-%d %H:%M:%S")
res['recent']=data.head(5).T.to_dict().values()
res['countries']=fc_country_df.head(10).T.to_dict().values()
res['dt']=date.today().strftime("%d/%m/%Y")

filename='fc_leaderboard.png'
plt.figure(1)
topcheckers=data['author'].value_counts().head(5)
topcheckers_df=topcheckers.rename_axis('author').reset_index(name='counts')
sns.barplot(x='counts', y='author', data=topcheckers_df, palette="Blues_d")
sns.despine()
plt.tight_layout()
plt.savefig('static/images/'+filename)
res['fc_leaderboard']='images/'+filename

filename='fc_per_week.png'
fc_per_week = data[data['dateCreated2']>'01-01-2019']['dateCreated2'].dt.week.value_counts().sort_index()
plt.figure(2)
plt.xlabel('Week Number')
plt.box(on=None)
fc_per_week.plot(color='blue')
plt.savefig('static/images/'+filename)
res['fc_per_week']='images/'+filename

filename='us_cloud.png'
textdata=data[data['author'].isin(["FactCheck.org","PolitiFact"])]
#(["Fact Crescendo","FACTLY"])]
text=" ".join(textdata['claimReviewed'].fillna(""))
WordCloud(width=800,height=400,margin=10,background_color='white',colormap="Blues",collocations=True).generate(text).to_file('static/images/'+filename)
res['us_cloud']='images/'+filename

@app.route('/leaderboard')
def leaderboard():
    return render_template('leaderboard.html',result=res)

@app.route('/recent')
def recent():
    return render_template('recent.html',result=res)

@app.route('/keywords')
def keywords():
    return render_template('keywords.html',result=res)
    
@app.route('/time')
def time():
    return render_template('time.html',result=res)

@app.route('/')
def all():
    return render_template("main.html",result=res)

if __name__ == '__main__':
    app.run()
    
    