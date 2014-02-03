require 'sinatra'
require 'uri'
require 'csv'
require_relative 'CSVHandler'
@@all_tweets = CSVHandler.new('results.csv')
@@csv_file = CSV.parse(File.open('results.csv'), {:headers => true}).to_a()

get '/' do
    @tweet = @@all_tweets.getTweet
    erb :tweet
end

get '/next' do
    accept_column = 34
    reject_column = 35
    # If we confirmed this result then do nothing otherwise update the approval / rejection
    id = params[:id].to_i
    puts @@csv_file[id][34]
    puts @@csv_file[id][35]
    if params[:accept] == 'false'
        # If we had originally rejected this work now accept it
        if @@csv_file[34][id] = ''
            @@csv_file[34][id] = 'x'
            @@csv_file[35][id] = ''
        elsif csv_file[34][id] = 'x'
            @@csv_file[34][id] = ''
            @@csv_file[35][id] = URI.unescape(params[:feedback])
        end
    end
    File.open('new_results.csv','w'){ |f| f << @@csv_file.map(&:to_csv).join() }
    @tweet = @@all_tweets.getTweet
    if(@tweet.nil?)
        @tweet = 'Finished'
    end
    erb :tweet
end
