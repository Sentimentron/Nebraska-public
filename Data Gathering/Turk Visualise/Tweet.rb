class Tweet
  attr_accessor :tweet, :sentiment, :subphrases, :tweet_id

  def initialize tweet, sentiment, subphrases, tweet_id
    @tweet = tweet
    @sentiment = sentiment
    @subphrases = subphrases
    @tweet_id = tweet_id
  end

end
