require 'csv'
doc = File.open("data.csv")
result = ""
CSV.parse(doc).each do |row|
	result = result + row[0] + ", \"" + row[1].gsub(/"/, '').gsub("\n", ' ') + "\" \n"
end

File.open("result.arff", 'w') do |file|
	file.write(result)
end
