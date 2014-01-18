require 'sinatra'
require_relative 'CSVHandler'
@@all_tweets = CSVHandler.new('results.csv')
get '/' do
    @tweet = @@all_tweets.getTweet
    erb :tweet
end

get '/next' do
    @tweet = @@all_tweets.getTweet
    erb :tweet
end
