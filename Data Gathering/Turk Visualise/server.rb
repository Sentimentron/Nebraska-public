require 'sinatra'
require 'uri'
require 'csv'
require_relative 'CSVHandler'
@@all_tweets = CSVHandler.new('results.csv')
get '/' do
    @tweet = @@all_tweets.getTweet
    erb :tweet
end

get '/next' do
    tweet = URI.unescape(params[:tweet])
    tweet ||= 'empty'
    status = params[:status]
    status ||='empty'
    annotation = params[:annotation]
    annotation ||= 'empty'
    File.open('inspection.csv', 'a') { |file| file.write( "\""+tweet+"\""+','+status+','+annotation+"\n") }
    @tweet = @@all_tweets.getTweet
    erb :tweet
end
