library(infotheo)

data = read.csv("~/Desktop/Nebraska/SCL/unigrams.arff")
number_cols = ncol(data)
result1 = mutinformation(data, method="emp")
result = mutinformation(data[,-number_cols], data[,number_cols], method="emp")


