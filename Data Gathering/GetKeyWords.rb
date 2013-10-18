require 'tweetstream'
require 'twitter'
require 'whatlanguage'
require 'mysql'
require 'yaml'

class GetData

  def initialize
    TweetStream.configure do |config|
      config.consumer_key       = "0nMytWPQyIVRrCW7GnA"
      config.consumer_secret    = "WsIW31xDD75KMEDNqXmAZUzmK2dYCbg2pY89oabxjE"
      config.oauth_token        = "10909152-eWHWKB5KjSFTuO2TNRhUZwt5X3HnZQGRKyT0NgKgs"
      config.oauth_token_secret = "lRsoIxBCv258wzrxCNry6ZLBIfMqdYMhAH0qn2rFw4"
      config.auth_method        = :oauth
    end
     @conn = Mysql.new('localhost', 'twitterstream', 'rootfish', 'twitterstream')
  end

  # Connect to the streaming API and pull in live tweets
  def getIncomingTweets
    words = ['Zynga','YouTube','Yahoo','Xbox','Windows','Wikipedia','Twitter','Tumblr','Telecoms','Symbian','Oracle','Spotify','Sony','Smartphones','Skype','Samsung','Reddit','Oracle','Nokia','Nintendo','Acer','Acta','Activision','Blizzard','Adobe','Amazon','Android','AOL','Apple','Asus','Bing','Bitcoin','BitTorrent','BlackBerry','Chatroulette','snapchat','Craigslist','Dell','Digg','ebay','Facebook','Firefox','Flickr','Foursquare','gmail','google','groupon','htc','ibm','Instagram','Intel','iPad','iPadmini','iPhone','ipod','iTunes','Kickstarter','Kindle','KindleFire','Kinect','LinkedIn','Linux','Macworld','Megaupload','Microsoft','Mozilla','Myspace','Congress','Obama','Boehner','EricCantor','Biden','Pelosi','Democrats','Republicans','Cruz','Constitution','Federal','Legislature','Senate','Obamacare', 'Acquisition','AMEX','Amortization','Arbitrage','Bank','Bankrupt','Barter','Bear','Beneficiary','Bond','Broker','Brokerage','Bull','Buying','Buyout','Collateral','Commodity','Credit','Debenture','Debit','Debt','Default','Delinquency','Demand','Depository','Depreciation','Depression','Deregulation','Embezzlement','Federal','Fees','Fiscal','Foreclosure','Lendingrate','Leverage','Liability','Lien','Liquidity','Long-term','Lowrisk','Merger','NYSE','OTC','Recession','Regulation','Securities','Takeover','Underwriter']
    TweetStream::Client.new.on_error do |message|
      puts "Error: #{message.to_s} "
    end.track('Zynga','YouTube','Yahoo','Xbox','Windows','Wikipedia','Twitter','Tumblr','Telecoms','Symbian','Oracle','Spotify','Sony','Smartphones','Skype','Samsung','Reddit','Oracle','Nokia','Nintendo','Acer','Acta','Activision','Blizzard','Adobe','Amazon','Android','AOL','Apple','Asus','Bing','Bitcoin','BitTorrent','BlackBerry','Chatroulette','snapchat','Craigslist','Dell','Digg','ebay','Facebook','Firefox','Flickr','Foursquare','gmail','google','groupon','htc','ibm','Instagram','Intel','iPad','iPadmini','iPhone','ipod','iTunes','Kickstarter','Kindle','KindleFire','Kinect','LinkedIn','Linux','Macworld','Megaupload','Microsoft','Mozilla','Myspace','Congress','Obama','Boehner','EricCantor','Biden','Pelosi','Democrats','Republicans','Cruz','Constitution','Federal','Legislature','Senate','Obamacare', 'Acquisition','AMEX','Amortization','Arbitrage','Bank','Bankrupt','Barter','Bear','Beneficiary','Bond','Broker','Brokerage','Bull','Buying','Buyout','Collateral','Commodity','Credit','Debenture','Debit','Debt','Default','Delinquency','Demand','Depository','Depreciation','Depression','Deregulation','Embezzlement','Federal','Fees','Fiscal','Foreclosure','Lendingrate','Leverage','Liability','Lien','Liquidity','Long-term','Lowrisk','Merger','NYSE','OTC','Recession','Regulation','Securities','Takeover','Underwriter') do |status|
        if status.text.language.to_s == "english" && !status.retweet?
          if words.any? {|word| status.text.include?(word)}
            prep = @conn.prepare("INSERT INTO stream(response) VALUES(?)")
            prep.execute status.text
            prep.close
          end
        end
    end
  end

end

a = GetData.new
a.getIncomingTweets
