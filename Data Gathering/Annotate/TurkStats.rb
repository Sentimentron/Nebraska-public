require 'csv'
class TurkStats


    def initialize filename
        @filename = filename
    end

    def computeEntropy
        count = 1
        rows = []
        result = ''
        avg_time = 0
        score = [0,0,0]
        entropy = 0
        CSV.foreach(@filename, :headers => true) do |row|
            if count % 4 == 0
                rows << row
                rows.each do |row|
                    # Need to figure out how many of each classification we got to work out entropy
                    score[nominalToInt(row['Answer.sentiment'])] = score[nominalToInt(row['Answer.sentiment'])] + 1
                    avg_time = avg_time + row['WorkTimeInSeconds'].to_i
                end
                score.each do |item|
                    entropy = entropy + -(item / 4.0) * logBase2(item/4.0)
                end
                avg_time = avg_time / 4
                result << avg_time.to_s + ',' + entropy.to_s << "\n"
                rows = []
                entropy = 0
                score = [0,0,0]
                avg_time = 0
                count = 1
            else
                rows << row
                count = count +1
            end

        end
        puts result
    end

    def computeStandardDeviation
        count = 1
        rows = []
        result = ''
        avg_time = 0
        score = [0,0,0]
        times = []
        entropy = 0
        CSV.foreach(@filename, :headers => true) do |row|
            if count % 4 == 0
                rows << row
                rows.each do |row|
                    # Need to figure out how many of each classification we got to work out entropy
                    score[nominalToInt(row['Answer.sentiment'])] = score[nominalToInt(row['Answer.sentiment'])] + 1
                    times << row['WorkTimeInSeconds'].to_i
                end
                score.each do |item|
                    entropy = entropy + -(item / 4.0) * logBase2(item/4.0)
                end
                avg_time = calculateAverage times
                standard_dev = Math.sqrt(calculateSD(times, avg_time))

                result << standard_dev.to_s + ',' + entropy.to_s << "\n"
                rows = []
                times = []
                entropy = 0
                score = [0,0,0]
                avg_time = 0
                count = 1
            else
                rows << row
                count = count +1
            end

        end
        puts result
    end

    def calculateAverage data
        data.inject{ |result, element| result + element}.to_f / data.size
    end

    def calculateSD data, average
        data.inject{ |result, element| result + (element - average) **2 }
    end

    def nominalToInt nominal
        if nominal == 'positive'
            return 2
        elsif nominal == 'negative'
            return 1
        else
            return 0
        end
    end

    def logBase2 num
        if num == 0
            return 0
        else
            return Math.log2(num)
        end
    end




end

test = TurkStats.new('results.csv')
test.computeStandardDeviation
