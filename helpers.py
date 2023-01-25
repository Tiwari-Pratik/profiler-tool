import tweepy
import pandas as pd
from datetime import datetime
from dateutil import tz
import math
import plotly.offline as pyo
import plotly.graph_objs as go
from wordcloud import WordCloud, STOPWORDS , ImageColorGenerator
import matplotlib.pyplot as plt 
import numpy as np
from PIL import Image
import json
import streamlit as st

@st.cache
def get_handle_info(api,handle):

    user = api.get_user(screen_name=handle)
    # print(user._json)
    F_ID = user._json['id']
    F_ID_STR = user._json['id_str']
    F_NAME = user._json['name']
    F_SNAME = user._json['screen_name']
    F_LOC = user._json['location']
    F_DESC = user._json['description']
    F_FOLLOWERS_COUNT = user._json['followers_count']
    F_FOLLOWING_COUNT = user._json['friends_count']
    F_STATUS_COUNT = user._json['statuses_count']
    F_CREATED_AT = user._json['created_at']
    F_VERIFIED = user._json['verified']
    F_IMAGE_URL = user._json['profile_image_url_https']

    return [F_ID, F_ID_STR,F_NAME,F_SNAME,F_LOC,F_DESC,F_FOLLOWERS_COUNT, F_FOLLOWING_COUNT, F_STATUS_COUNT, F_CREATED_AT, F_VERIFIED, F_IMAGE_URL]
   

@st.cache(allow_output_mutation=True)
def get_handle_tweets(client,handle_id):

    tweet_fields = ['created_at','conversation_id','referenced_tweets','attachments','geo','entities','public_metrics']
    expansions = ['attachments.poll_ids', 'attachments.media_keys', 'author_id', 'entities.mentions.username', 'geo.place_id', 'in_reply_to_user_id', 'referenced_tweets.id', 'referenced_tweets.id.author_id']
    media_fields = ['duration_ms', 'height', 'media_key', 'preview_image_url', 'type', 'url', 'width', 'public_metrics', 'alt_text']
    user_fields=['created_at','id','name','username','location','verified','description','entities','public_metrics']
    place_fields=['contained_within', 'country', 'country_code', 'full_name', 'geo', 'id', 'name', 'place_type']

    tweet_df = pd.DataFrame()
    tweet_data_tweets = []
    tweet_includes_users = []
    tweet_includes_tweets = []
    tweet_includes_media = []
    tweets_pulled = 0
    total_tweet_data_df = pd.DataFrame()
    total_tweet_includes_tweets_df = pd.DataFrame()
    total_tweet_includes_user_df = pd.DataFrame()
    total_tweet_includes_media_df = pd.DataFrame()


    for tweet in tweepy.Paginator(client.get_users_tweets,id=handle_id,user_fields=user_fields,place_fields=place_fields,media_fields=media_fields,tweet_fields=tweet_fields,expansions=expansions,max_results=100):
    #     print(tweet.data)
    #     print(tweet.meta)
        if(tweet.data):
            # print(len(tweet.data))
            tweets_pulled += len(tweet.data)
        tweet_data_df = pd.DataFrame(tweet.data)
        total_tweet_data_df = pd.concat([total_tweet_data_df,tweet_data_df],ignore_index=True)
        
        if 'tweets' in tweet.includes.keys():
            tweet_includes_tweets_df = pd.DataFrame(tweet.includes['tweets'])
            total_tweet_includes_tweets_df = pd.concat([total_tweet_includes_tweets_df,tweet_includes_tweets_df],ignore_index=True)
        
        if 'users' in tweet.includes.keys():
            tweet_includes_user_df = pd.DataFrame(tweet.includes['users'])
            total_tweet_includes_user_df = pd.concat([total_tweet_includes_user_df,tweet_includes_user_df],ignore_index=True)

            #     tweet_includes_media_df = pd.DataFrame(tweet.includes['media'])
        

        
        
            #     total_tweet_includes_media_df = total_tweet_includes_media_df.append(tweet_includes_media_df,ignore_index=True)

        print("Total number of tweets pulled: ",tweets_pulled)

    # return [total_tweet_data_df, total_tweet_includes_tweets_df, total_tweet_includes_user_df]
    # Tweet_data_df = process_data(total_tweet_data_df, total_tweet_includes_tweets_df, total_tweet_includes_user_df,api)
    return [total_tweet_data_df, total_tweet_includes_tweets_df,total_tweet_includes_user_df]

@st.cache
def process_data(total_tweet_data_df, total_tweet_includes_tweets_df, total_tweet_includes_user_df):
    Tweet_data = []

    for i in range(0, len(total_tweet_data_df)):
        data_dict = {}
        data_dict['Tweet Id'] = total_tweet_data_df.loc[i,'id']
        data_dict['Tweet Id Str'] = str(total_tweet_data_df.loc[i,'id'])
        data_dict['Tweet Created Date'] = total_tweet_data_df.loc[i,'created_at']
        data_dict['Tweet Created Date String'] = total_tweet_data_df.loc[i,'created_at'].strftime("%d-%b-%Y (%H:%M:%S.%f)")
        data_dict['Tweet Text'] = total_tweet_data_df.loc[i,'text']
        
        
        data_dict['Retweet Count'] = total_tweet_data_df.loc[i,'public_metrics']['retweet_count']
        data_dict['Reply Count'] = total_tweet_data_df.loc[i,'public_metrics']['reply_count']
        data_dict['Like Count'] = total_tweet_data_df.loc[i,'public_metrics']['like_count']
        data_dict['Quote Count'] = total_tweet_data_df.loc[i,'public_metrics']['quote_count']
        
        rtype = type(total_tweet_data_df.loc[i,'referenced_tweets'])
        if rtype != float:
            data_dict['Reference Tweet Type'] = total_tweet_data_df.loc[i,'referenced_tweets'][0]['type']

        else:
            data_dict['Reference Tweet Type'] = 'tweeted'
        
        if type(total_tweet_data_df.loc[i,'entities']) != float:
            if 'mentions' in total_tweet_data_df.loc[i,'entities'].keys():
                usernames = []
                for data in total_tweet_data_df.loc[i,'entities']['mentions']:
                    usernames.append(data['username'])
                user_mentions = usernames
            else:
                user_mentions = []
            
            if 'hashtags' in total_tweet_data_df.loc[i,'entities'].keys():
                hashtags = []
                for data in total_tweet_data_df.loc[i,'entities']['hashtags']:
                    hashtags.append(data['tag'])
                tweet_hashtags = hashtags
            else:
                tweet_hashtags = []
        else:
            user_mentions = []
            tweet_hashtags = []
        
        # Entities_dict = {}
        data_dict['User Mentions'] = user_mentions
        data_dict['Hashtags'] = tweet_hashtags
        
           
        Tweet_data.append(data_dict)
    Tweet_data_df = pd.DataFrame(Tweet_data)
    return Tweet_data_df
        
@st.cache
def update_zone(adate):

    from_zone = tz.tzutc()
    to_zone = tz.tzlocal()

    utc = adate.replace(tzinfo=from_zone)
    local = utc.astimezone(to_zone)

    return local

@st.cache
def get_tweets_timeline(df,sampling,line_color,mark_color):
    dates = []
    ids = []
    for i in range(0,len(df)):
        dates.append(df.loc[i,'Tweet Created Date'])
        ids.append(df.loc[i,'Tweet Id'])

    date_data = [(dates[i],ids[i]) for i in range(0,len(dates))]

    date_df = pd.DataFrame(date_data,columns=['date','ids'])

    date_df['date'] = date_df['date'].apply(update_zone)

    date_df.set_index('date',inplace=True)
    date_df.sort_index(inplace=True)
    sample_by = ""
    if(sampling=="daywise"):
        sample_by = "d"
    if(sampling=="monthwise"):
        sample_by = "m"
    if(sampling=="yearwise"):
        sample_by = "ys"
    # print(sample_by)
    tweet_dates = list(date_df.resample(sample_by).count().index)
    tweet_counts = list(date_df.resample(sample_by)['ids'].count())

    data = [go.Scatter(x=tweet_dates, y=tweet_counts, mode='lines+markers', line=dict(color=line_color,width=3,dash='dash',shape='spline'),marker=dict(color=mark_color,size=5))]
    layout = go.Layout(xaxis=dict(title='Timeline', nticks=16), yaxis=dict(title='No. of Tweets'), paper_bgcolor='rgba(0, 0, 0,1)',
        plot_bgcolor='rgba(0, 0, 0,1)',
        font=dict(
            family="Gravitas One",
            size=22,
            color="#CA054D"
        ))
    fig=go.Figure(data=data,layout=layout)
    fig.update_xaxes(showgrid=False)
    fig.update_yaxes(showgrid=False)
    fig.update_xaxes(showline=True, linewidth=3, linecolor='white')
    fig.update_yaxes(showline=True, linewidth=3, linecolor='white')
    # fig.update_layout(template = 'ggplot2')
    #pyo.plot(fig, filename='tweets_timeline.html')
    # pyo.plot(fig, filename='Dravidnadu_tweets_created_timeline_monthwise_new.html')
    fig_str = fig.to_json()
    fig_data = json.loads(fig_str)
    x_val = fig_data["data"][0]["x"]
    y_val = fig_data["data"][0]["y"]
    fig_data_df = pd.DataFrame()
    fig_data_df['Dates'] = x_val
    fig_data_df['Tweet Count'] = y_val
    return [fig, fig_data_df]


def get_info_data(df):

    all_users_list = df['User Mentions'].to_list()
    all_usernames = [item for sublist in all_users_list for item in sublist]
    udf = pd.DataFrame(all_usernames, columns=['User Mentions'])
    usernames = udf['User Mentions'].value_counts().index
    usernames_counts = udf['User Mentions'].value_counts().values
    username_df = pd.DataFrame()
    username_df['Usernames'] = usernames
    username_df['Count'] = usernames_counts

    all_hashtags_list = df['Hashtags'].to_list()
    all_usernames = [item for sublist in all_hashtags_list for item in sublist]
    hdf = pd.DataFrame(all_usernames, columns=['Hashtags'])
    hashtags = hdf['Hashtags'].value_counts().index
    hashtags_counts = hdf['Hashtags'].value_counts().values
    hashtags_df = pd.DataFrame()
    hashtags_df['Hashtags'] = hashtags
    hashtags_df['Count'] = hashtags_counts

    ref_tweet_types = df['Reference Tweet Type'].value_counts().index
    ref_tweet_types_counts = df['Reference Tweet Type'].value_counts().values
    ref_tweet_types_df = pd.DataFrame()
    ref_tweet_types_df['Tweet Type'] = ref_tweet_types
    ref_tweet_types_df['Tweet Counts'] = ref_tweet_types_counts


    return [username_df, hashtags_df, ref_tweet_types_df]


def generate_info_figures(username_df, hashtags_df, ref_tweet_types_df, user_col,tweet_col):
    
    udata = go.Bar(x=username_df['Usernames'], y = username_df['Count'])
    ulayout = go.Layout(xaxis=dict(title="Accounts"), yaxis=dict(title="Mention Count"),paper_bgcolor='rgba(0, 0, 0,1)',
        plot_bgcolor='rgba(0, 0, 0,1)',
        font=dict(
            family="Gravitas One",
            size=22,
            color="#ffffff"
        ))
    

    ufig = go.Figure(data=udata, layout = ulayout)
    ufig.update_xaxes(showgrid=False)
    ufig.update_yaxes(showgrid=False)
    ufig.update_xaxes(showline=True, linewidth=3, linecolor='white')
    ufig.update_yaxes(showline=True, linewidth=3, linecolor='white')
    ufig.update_traces(marker_color=user_col)
    u_fig_str = ufig.to_json()
    u_fig_data = json.loads(u_fig_str)
    u_x_val = u_fig_data["data"][0]["x"]
    u_y_val = u_fig_data["data"][0]["y"]
    u_fig_data_df = pd.DataFrame()
    u_fig_data_df['Usernames'] = u_x_val
    u_fig_data_df['Interaction Count'] = u_y_val
    # pyo.plot(fig, filename='Dravidnadu_retweeting_accounts.html')
    tdata = go.Bar(x=ref_tweet_types_df['Tweet Type'], y = ref_tweet_types_df['Tweet Counts'])
    tlayout = go.Layout(xaxis=dict(title="Tweet Types"), yaxis=dict(title="Tweet Type Count"),paper_bgcolor='rgba(0, 0, 0,1)',
        plot_bgcolor='rgba(0, 0, 0,1)',
        font=dict(
            family="Gravitas One",
            size=22,
            color="#ffffff"
        ))
    

    tfig = go.Figure(data=tdata, layout = tlayout)
    tfig.update_xaxes(showgrid=False)
    tfig.update_yaxes(showgrid=False)
    tfig.update_xaxes(showline=True, linewidth=3, linecolor='white')
    tfig.update_yaxes(showline=True, linewidth=3, linecolor='white')
    tfig.update_traces(marker_color=tweet_col)
    t_fig_str = tfig.to_json()
    t_fig_data = json.loads(t_fig_str)
    t_x_val = t_fig_data["data"][0]["x"]
    t_y_val = t_fig_data["data"][0]["y"]
    t_fig_data_df = pd.DataFrame()
    t_fig_data_df['Tweet types'] = t_x_val
    t_fig_data_df['Tweet Types Count'] = t_y_val

    comment_words = '' 
    stopwords = set(STOPWORDS) 
    mask = np.array(Image.open('./comment.png'))
    # print(mask.shape)

    comment_words += " ".join(hashtags_df['Hashtags'].to_list())+" "

    wordcloud = WordCloud(
        width = 100, height = 100,
        random_state=2, background_color='black',
        colormap='rainbow', collocations=False,
        min_font_size = 6,
        stopwords = stopwords,
        contour_color='#dd0f24',
        contour_width=1,
        mask=mask
        ).generate(comment_words)

    # image_colors = ImageColorGenerator(mask)

    # plot the WordCloud image                        
    plt.figure(figsize = (2, 2), facecolor = None) 
    plt.imshow(wordcloud) 
    plt.axis("off") 
    plt.tight_layout(pad = 0) 
    # plt.savefig("Dravidnadu_hashtag_Wordcloud.jpg",dpi=600)
    # plt.show()
    plt_df = hashtags_df.copy()
    return [ufig,u_fig_data_df,tfig,t_fig_data_df,plt,plt_df] 



