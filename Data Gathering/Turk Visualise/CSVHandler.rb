require 'csv'
require_relative 'Tweet'
class CSVHandler

    def initialize filename
        @filename = filename
        @position = 0
        @tweets = []
        loadTweets
    end

    def getTweet
        element = @tweets[@position]
        @position = @position + 1
        puts @position
        return element
    end

    def loadTweets
        CSV.foreach(@filename, :headers => true) do |row|
            @tweets << Tweet.new(row['Input.tweet'], row['Answer.sentiment'], row['Answer.subphrases'], row['Answer.tweet_id'])
        end
    end

end
