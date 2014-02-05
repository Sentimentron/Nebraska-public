require 'sinatra'
require 'uri'
require 'csv'
require './CSVHandler'

@@all_tweets = CSVHandler.new('results.csv')
get '/' do
    @tweet = @@all_tweets.getTweet
    erb :tweet
end

get '/next' do
    tweet = URI.unescape(params[:tweet])
    tweet ||= 'empty'
    annotation = params[:annotation]
    annotation ||= 'empty'
    File.open('inspection.csv', 'a') { |file| file.write( "\""+tweet+"\""+','+annotation+"\n") }
    @tweet = @@all_tweets.getTweet
    erb :tweet
end
