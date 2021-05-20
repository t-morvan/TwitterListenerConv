# Twitter listener + conversation collection 

Given a set of Twitter ids :

1. listen and collect tweets posted by the users.
2. Collect the conversation sparked by the tweets.

It uses Tweepy with Twitter API v1 for the listener and v2 for retrieving the conversation

## Parameters 
1. `ids` : list of twitter
2. `conv_lifetime` : time to wait before collecting the conversation sparked by a tweet.

## Outputs
 Data is grouped by day as shown below :
```
collected  
│
└───tweets
│   │   20-5-2021.json
│   │   21-5-2021.json
|      ...
│   
└───replies
|   │   20-5-2021.json
|   │   21-5-2021.json
|    ...
|
└── logs.txt
```
Tweets and replies are saved as raw json, one per line in each file.

## Remarks
Depending on the activity of the users, it might be useful to tweak the sleeping time of the processing and replies thread accordingly.
  
