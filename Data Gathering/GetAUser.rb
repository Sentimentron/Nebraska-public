#require 'tweetstream'
gem 'twitter', '>= 5.3.0'
require 'twitter'
require 'whatlanguage'
require 'mysql'
require 'yaml'

class GetData

  def initialize
    @client = Twitter::REST::Client.new do |config|
      config.consumer_key       = "0nMytWPQyIVRrCW7GnA"
      config.consumer_secret    = "WsIW31xDD75KMEDNqXmAZUzmK2dYCbg2pY89oabxjE"
      config.oauth_token        = "10909152-eWHWKB5KjSFTuO2TNRhUZwt5X3HnZQGRKyT0NgKgs"
      config.oauth_token_secret = "lRsoIxBCv258wzrxCNry6ZLBIfMqdYMhAH0qn2rFw4"
    end
  end

  # Connect to the streaming API and pull in live tweets
  def getIncomingTweets
    @client.user_timeline("StockTwits", :count => 200, :max_id => 360024446179869000




).each do |tweet|
      puts "\"" + tweet.text.gsub(/"/, '').gsub(/(?:f|ht)tps?:\/[^\s]+/, '') + "\"," + tweet.id.to_s
    end
  end

end

a = GetData.new
a.getIncomingTweets
