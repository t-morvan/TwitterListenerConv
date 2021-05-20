import tweepy
import pandas as pd
from listener import *



#authentification
oauth_dict={}
with open('twitter_keys.txt','r') as f:
    for line in f:
        data=line.split()
        oauth_dict[data[0]]=data[1]

# v1 for streaming
auth = tweepy.OAuthHandler(oauth_dict['API_KEY'], oauth_dict['API_SECRET'])
auth.set_access_token(oauth_dict['TOKEN'], oauth_dict['TOKEN_SECRET'])
api = tweepy.API(auth, wait_on_rate_limit=True)

# v2 for conversation
api_v2 = tweepy.Client( consumer_key=oauth_dict['API_KEY'], consumer_secret=oauth_dict['API_SECRET'], access_token=oauth_dict['TOKEN'], access_token_secret=oauth_dict['TOKEN_SECRET'], wait_on_rate_limit=True)

# read follow list for the stream filter
data=pd.read_csv("ids.csv",sep=",")
ids=list(data['0'])

# time to wait before collecting the conversation
conv_lifetime=4

# threads set up
tweets_queue = Queue()
tweets_process_thread = ProcessTweets(tweets_queue)
tweets_replies_thread = GetReplies(conv_lifetime,api_v2)


#First arg is the max number of Tweets you want to collect
myStreamListener = MyStreamListener(process_thread=tweets_process_thread, replies_thread=tweets_replies_thread,consumer_key=oauth_dict['API_KEY'], consumer_secret=oauth_dict['API_SECRET'], access_token=oauth_dict['TOKEN'], access_token_secret=oauth_dict['TOKEN_SECRET'])


try:
    myStreamListener.filter(follow=ids)
except KeyboardInterrupt:
    tweets_process_thread.stop = True
    tweets_process_thread.join()
    tweets_replies_thread.stop = True
    tweets_replies_thread.join()
    raise

