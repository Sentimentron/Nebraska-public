require 'csv'
require './Tweet'
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
            @tweets << Tweet.new(row['tweet'])
        end
    end

end
