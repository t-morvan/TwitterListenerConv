from tweepy import Stream,Paginator
from queue import Queue
from threading import Thread
from time import sleep
import os
import json
from datetime import datetime, timedelta,timezone
from dateutil.parser import parse

def create_file_name(base,date):
    '''Créer un nom de fichier en fonction de la date mais t'avais deviné'''

    return "collected/"+base+"/"+ str(date.day) + '_' + str(date.month) + '_' + str(date.year) + '.json'



class GetReplies(Thread):
    def __init__(self,conv_lifetime,api_v2):
        Thread.__init__(self)
        self.last_date=datetime.now(timezone.utc)
        self.conv_lifetime=conv_lifetime
        self.api_v2=api_v2
        self.stop=False
        self.collected_replies=0

    def run(self):
        while not self.stop:
           if self.last_date.day!=datetime.now(timezone.utc).day:
                    # if new day fetch the replies for tweets tweeted conv_lifetime days before
                    self.last_date=datetime.now(timezone.utc)
                    # name of the file to open
                    input_file_name=create_file_name("tweets",self.last_date-timedelta(days=self.conv_lifetime))
                    # handle exception because if current_time<conv_lifetime, no file has been created yet
                    try :
                        with open(input_file_name,'r') as f:
                            all_replies=[]
                            for line in f:
                                tweet = json.loads(line)
                                replies=self.get_replies(tweet['id'])
                                all_replies.append(replies)
                    except :
                        continue    

                    # save as json all the replies for this day
                    with open(create_file_name("replies",self.last_date-timedelta(days=self.conv_lifetime)), 'w') as outfile:
                        json.dump(all_replies, outfile)

                    # save logs 
                    n=len(all_replies)
                    self.collected_replies+=n
                    out_txt = "Date : {}, Collected replies : {}, Total collected replies : {}\n".format(self.last_date.date(),n,self.collected_replies)
                    print(out_txt)
                    with open('collected/logs.txt','a') as f:
                        f.write(out_txt)  

                    # sleep for some time (15h) as it shoudn't take the whole day
                    sleep(54000)

    def get_replies(self,tweet_id):
        replies=Paginator(self.api_v2.search_recent_tweets,max_results=100,
        user_auth=True,query="conversation_id:{}".format(tweet_id),tweet_fields=["in_reply_to_user_id","author_id","created_at","conversation_id","public_metrics","referenced_tweets.id"]).flatten()
        return [reply.data for reply in replies]

class ProcessTweets(Thread):

    def __init__(self, tweets_queue):
        Thread.__init__(self)
        # total number of processed tweets
        self.tweets_processed = 0
        # processed tweets for thecurrent day
        self.date_tweets_processed = 0
        # tweets to process queue
        self.queue = tweets_queue
        # last tweet date to detect day change 
        self.last_date= datetime.now(timezone.utc)
        # current file to write tweets
        self.outfile=create_file_name("tweets", datetime.now(timezone.utc))
        self.stop = False

        print("Processing thread opened.") 

    def __del__(self):
        
        out_txt = "End of collect. Tweets processed  : {}"\
                .format(self.tweets_processed)
        print(out_txt)

    def run(self): 
        
        while not self.stop:
            while not self.queue.empty():
                 # process tweets from the listener
                
                try:
                    status = self.queue.get(timeout=3)
                except Queue.Empty:
                    break
                
                self.update_date(status)
                self.process_tweet(status)       

            sleep(120)    
            
           #Small break if the queue is empty in order to wait for new Tweets

    def process_tweet(self, status):
        # save only if a 'true' tweet
        if (not status.get('retweeted_status')) and (not status.get('in_reply_to_status_id_str')) and (not status.get('in_reply_to_user_id_str')):
            with open(self.outfile, 'a') as f:
                f.write('{}\n'.format(json.dumps(status)))
            self.tweets_processed += 1
            self.date_tweets_processed +=1

                    

    def update_date(self,status):     
        date = parse(status['created_at'])
        if date.day!=self.last_date.day:
            # save logs for the last date
            out_txt = "Date : {}, Processed tweets : {}, Total processed tweets : {}\n".format(self.last_date.date(), self.date_tweets_processed,self.tweets_processed)
            print(out_txt)
            with open('collected/logs.txt','a') as f:
                f.write(out_txt) 
            # update date and outfile
            self.last_date=date
            self.outfile=create_file_name("tweets", date)
            self.date_tweets_processed = 0
        return None


  


      
class MyStreamListener(Stream):

    def __init__(self, process_thread, replies_thread, *args, **kwargs):
        
        super(MyStreamListener, self).__init__(*args, **kwargs)
        self.nb_tweets_streamed = 0
     
        
        self.process_thread = process_thread
        self.to_process = self.process_thread.queue
        self.process_thread.start()

        self.replies_thread = replies_thread
        self.replies_thread.start()
        


    def __del__(self):

        self.process_thread.stop = True #Tell the thread to end
        self.replies_thread.stop = True 

        self.process_thread.join()
        self.replies_thread.join()

    
    
   
    def on_status(self, status):
            
        self.to_process.put(status._json)
    

    def on_error(self, status_code):
        
        out_txt = "Error : {}\n".format(status_code)
        with open('collected/logs.txt','a') as f:
            f.write(out_txt[:-1])
        return False

    def on_exception(self, exception):
        
        print(exception)
        
