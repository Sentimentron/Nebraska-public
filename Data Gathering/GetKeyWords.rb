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
    tech_words = 'Mark Zuckerberg, Zynga, YouTube, Yahoo, Jerry Yang, Xbox, Windows, Evan Williams, Wikipedia, Web 2.0, Jimmy Wales, Twitter, Tumblr, Telecoms, Tablet computers, Symbian, Oracle,, Spotify, Sony, Smartphones, Skype, Steven Sinofsky, Clive Sinclair, Samsung, Sheryl Sandberg, Reddit, Oracle, Nokia, Nintendo, Acer, Acta,  Activision Blizzard, Adobe, Amazon.com, Android, AOL, Apple, Asus, Steve Ballmer, Carol Bartz, Tim Berners-Lee, Jeff Bezos, Bing, Bitcoin, BitTorrent, BlackBerry, Chatroulette, snapchat, Cloud computing, Tim Cook, Craigslist, Dell, Digg, ebay, Facebook, Firefox, Flickr, Foursquare, Bill Gates, gmail, google, groupon, htc, ibm, Instagram, Intel, Internet Explorer, iPad, iPad mini, iPhone,iPhone 5,iPhone 5c,iPhone 5s, ipod, iTunes, Jonathan Ive, Steve Jobs, Jack Dorsey, Kickstarter, Kindle, Kindle Fire, Kinect, LinkedIn, Linux, Macworld, Marissa Mayer, Megaupload,
Microsoft, Microsoft Surface, Mozilla, Myspace'
    politics_words = 'Congress, Obama, Boehner, Eric Cantor, Biden, Pelosi, Democrats, Republicans, Cruz, Constitution, Federal, Legislature,  Senate, Tea Party, Obamacare, Debt Ceiling, house of representatives, hillary clinton, white house, sarah palin, ted cruz'
    finance_words = 'Acquisition, AMEX, Amortization, Arbitrage, Balloon payment, Bank, Bankrupt, Barter, Bear, Beneficiary, Bond, Broker, Brokerage, Bull, Buying, Buyout, Call Option, Collateral, Commodity, Credit, Debenture, Debit, Debt, Default, Delinquency, Demand, Depository, Depreciation, Depression, Deregulation, Dow Jones Average, Embezzlement, Exchange rate, Federal, Fees, Fiscal, Foreclosure, Hedge Fund, Mutual Funds, Futures Options, LBO (leveraged buyout), Lending rate, Leverage, Liability, Lien, Liquidity, Long-term, Low risk, Merger, NYSE, OTC, Preferred stock, Recession, Regulation, Securities, Short Sell, Long Sell, Equity Swap, Interest Rate Swap, Takeover, Underwriter'

    TweetStream::Client.new.on_error do |message|
      puts "Error: #{message.to_s} "
    end.track(tech_words + politics_words + finance_words) do |status|
        if status.text.language.to_s == "english"
          prep = @conn.prepare("INSERT INTO stream(response) VALUES(?)")
          prep.execute status.to_yaml
          prep.close
        end
    end
  end

end

a = GetData.new
a.getIncomingTweets
