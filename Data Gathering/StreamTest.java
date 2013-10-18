import twitter4j.conf.ConfigurationBuilder;
import twitter4j.*;
import java.io.IOException;

public class StreamTest {

    public static void main(String[] args) throws TwitterException, IOException {
        ConfigurationBuilder cb = new ConfigurationBuilder();
        cb.setDebugEnabled(true)
          .setOAuthConsumerKey("HBxV2xRiHIL3tKgJhYX0Kg")
          .setOAuthConsumerSecret("WTcxJuTwJ3yAUpzkXpaiifc0mERfPwcjx1FuSyipY")
          .setOAuthAccessToken("10909152-KemJP71hkd6s027NHvNki9zbNwAdwiteioQcaOxWB")
          .setOAuthAccessTokenSecret("HdVQYgqrEyU5nq2MSi7G7PaewIPHT5hTNubGMMUVRw");

        StatusListener listener = new StatusListener(){
            public void onStatus(Status status) {
                System.out.println(status.getUser().getName() + " : " + status.getText());
            }
            public void onDeletionNotice(StatusDeletionNotice statusDeletionNotice) {}
            public void onTrackLimitationNotice(int numberOfLimitedStatuses) {}
            public void onException(Exception ex) {
                ex.printStackTrace();
            }
            public void onStallWarning(StallWarning warning) {}
            public void  onScrubGeo(long a, long b){}
        };
        TwitterStream twitterStream = new TwitterStreamFactory(cb.build()).getInstance();
        twitterStream.addListener(listener);

        String[] keywords = {"Zynga","YouTube","Yahoo","Xbox","Windows","Wikipedia","Twitter","Tumblr","Telecoms","Symbian","Oracle","Spotify","Sony","Smartphones","Skype","Samsung","Reddit","Oracle","Nokia","Nintendo","Acer","Acta","Activision","Blizzard","Adobe","Amazon","Android","AOL","Apple","Asus","Bing","Bitcoin","BitTorrent","BlackBerry","Chatroulette","snapchat","Craigslist","Dell","Digg","ebay","Facebook","Firefox","Flickr","Foursquare","gmail","google","groupon","htc","ibm","Instagram","Intel","iPad","iPadmini","iPhone","ipod","iTunes","Kickstarter","Kindle","KindleFire","Kinect","LinkedIn","Linux","Macworld","Megaupload","Microsoft","Mozilla","Myspace","Congress","Obama","Boehner","EricCantor","Biden","Pelosi","Democrats","Republicans","Cruz","Constitution","Federal","Legislature","Senate","Obamacare", "Acquisition","AMEX","Amortization","Arbitrage","Bank","Bankrupt","Barter","Bear","Beneficiary","Bond","Broker","Brokerage","Bull","Buying","Buyout","Collateral","Commodity","Credit","Debenture","Debit","Debt","Default","Delinquency","Demand","Depository","Depreciation","Depression","Deregulation","Embezzlement","Federal","Fees","Fiscal","Foreclosure","Lendingrate","Leverage","Liability","Lien","Liquidity","Long-term","Lowrisk","Merger","NYSE","OTC","Recession","Regulation","Securities","Takeover","Underwriter"};
        FilterQuery words = new FilterQuery(0, null, keywords);
        twitterStream.filter(words);
    }
}
