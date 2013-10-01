Multilingual Sentiment Dataset
----------------------------------------------

The dataset contains tweets that have been human-annotated with sentiment labels by 3 Mechanical Turk workers. 

* Files: One file containing all separate tweets and their sentiment labels (xx_sentiment.tsv), two files containing merged tweets that at least n annotators agreed on (xx_sentiment_agree<n>.tsv). So 'de_sentiment_agree2.tsv' contains tweets that either 2 or 3 annotators assigned the same sentiment label to.
* Format: Tab-separated files with one header line.
* Columns:
	- sentiment: The sentiment label, either "positive", "negative", "neutral" or "na" (for irrelevant/unclear).
	- (numberagreed): The number of annotators agreeing on the tweet's label.
	or
	- (workerid): Mechanical Turk worker id of the worker that labeled the tweet.
	- tweetid: Arbitrary id for each tweet (not the real id of that tweet on Twitter)
	- tweet: The tweet text. Linebreaks and tab spaces have been removed. Usernames and URLs have been replaced by tokens (@user and ~http).


Note: For a few tweets, there are annotator agreements of over 3. This was because we erroneously posted a a very small number of tweets twice to Mechanical Turk.




Contact:
Sascha Narr (sascha.narr@dai-labor.de)
http://www.dai-labor.de/~narr/sentimentdataset