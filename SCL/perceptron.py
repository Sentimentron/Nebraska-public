import numpy
import pdb
import cProfile
import math

max_itterations = 5000
learning_rate = 0.1
pivots_to_keep = 50

# sentiment_input is a matrix of columns containing unigrams and rows containing instances. The final column is the class label
def learnPerceptron(sentiment_input, learning_rate):
    # Number of rows in sentiment_input
    number_instances = sentiment_input.shape[0]
    # Number of columns in sentiment_input minus the classlabel
    number_features = sentiment_input.shape[1] -1
    # The last column of the input contains the label and the columns are indexed from 0
    class_label_index = number_features
    # The standard set of weights for sentiment classification has 1 column and number_unigram rows
    weights = numpy.zeros(number_features)
    # numpy.zeroes takes the number of rows then the number of columns
    # 3 Constants
    bias = 0
    converged = False
    number_itterations = 0
    while converged == False and number_itterations < max_itterations:
        converged = True
        # For every training example
        for instance in range(0,number_instances):
            # Each training example needs to be used to train the sentiment weights once
            instance_without_label = sentiment_input[instance,0:number_features]
            class_label = sentiment_input[instance][class_label_index]
            # Train the sentiment weights
            # Rule for checking the output is: class_label * weight_vector . instance

            result = numpy.dot(weights,instance_without_label) + bias

            test = class_label*result
            if test <= 0: 
                weights = weights+(class_label*learning_rate*instance_without_label)
                bias = bias+learning_rate
                converged=False


            # positive_result = numpy.dot(positive_weights, instance_without_label) + positive_bias
            # negative_result = numpy.dot(negative_weights, instance_without_label) + negative_bias
            # neutral_result = numpy.dot(neutral_weights, instance_without_label) + neutral_bias
            # prediction = max(positive_result,negative_result,neutral_result)

            # if prediction == positive_result:
            #     label = 1
            # elif prediction == neutral_result:
            #     label = 0
            # else:
            #     label = -1

            # # If this was misclassified then update the weights
            # if class_label != label:
            #     if class_label == 1:
            #         positive_weights = positive_weights + learning_rate * instance_without_label
            #         positive_bias = positive_bias + learning_rate
            #     elif class_label == 0:
            #         neutral_weights = neutral_weights + learning_rate * instance_without_label
            #         neutral_bias = neutral_bias + learning_rate
            #     else:
            #         negative_weights = negative_weights + learning_rate * instance_without_label
            #         negative_bias = negative_bias + learning_rate

            #     if label == 1:
            #         positive_weights = positive_weights - learning_rate * instance_without_label
            #     elif label == 0:
            #         neutral_weights = neutral_weights - learning_rate * instance_without_label
            #     else:
            #         negative_weights = negative_weights - learning_rate * instance_without_label

            #     converged = False

        number_itterations = number_itterations+1

    #return (positive_weights, negative_weights, neutral_weights, positive_bias, negative_bias, neutral_bias)
    return (weights,bias)


# Runs sentiment_input through the perceptron and reports the accuracy
def  testPerceptron(sentiment_input, positive_weights, negative_weights, neutral_weights, positive_bias, negative_bias, neutral_bias):
    # Number of rows in sentiment_input
    number_instances = sentiment_input.shape[0]
    # Number of columns in sentiment_input minus the classlabel
    number_features = sentiment_input.shape[1] -1
    # The last column of the input contains the label and the columns are indexed from 0
    class_label_index = number_features

    correct = 0
    incorrect = 0
    # For every test example
    for instance in range(0,number_instances):
        instance_without_label = sentiment_input[instance,0:number_features]
        class_label = sentiment_input[instance][class_label_index]
        # Rule for checking the output is: class_label * weight_vector . instance
        positive_result = numpy.dot(positive_weights, instance_without_label + positive_bias)
        negative_result = numpy.dot(negative_weights, instance_without_label + negative_bias)
        neutral_result = numpy.dot(neutral_weights, instance_without_label + neutral_bias)

        if positive_result < 0:
            positive_result = -1
        else:
            positive_result = 1

        if negative_result < 0:
            negative_result = -1
        else:
            negative_result = 1

        if neutral_result < 0:
            neutral_result = -1
        else:
            neutral_result = 1

        if positive_result==1:
           prediction = 1
        elif negative_result==1:
            if positive_result == -1 & neutral_result == -1:
                prediction = -1
            elif positive_result == 1:
                prediction = 1
            elif positive_result == 0 & neutral_result == 0:
                prediction = -1
            else:
                prediction = 0
        elif neutral_result == 1:
            if positive_result == 1:
                prediction = 1
            elif positive_result==-1 & negative_result == 1:
                prediction = 0
            else:
                prediction = 0


        if prediction==class_label:
            correct = correct+1
        else:
            incorrect = incorrect+1

    print(incorrect)
    print(correct)

# Learns the Thi matrix which is a set of weights for predicting the pivot features.
# pivot_input contains the unigrams for each instance followed by 1 / 0 for each pivot features depending on if it appears in the tweet
def learnPivotPerceptron(pivot_input, learning_rate, number_unigrams):
    # The number of pivot features are the number of features minus the number of unigrams as they appear along side the unigrams in the training data
    number_pivot_features = pivot_input.shape[1] - number_unigrams
    # The weights for the pivot features have number_pivot columns and number_unigram rows
    pivot_weights = numpy.zeros((number_unigrams, number_pivot_features))
    # Number of rows in pivot input is more as we have data from both domains
    number_pivot_instances = pivot_input.shape[0]

    # For each pivot feature we need to learn the weights
    for pivot in range(0, number_pivot_features):
        converged = False
        iterations = 0
        while converged == False and iterations < max_itterations:
            converged = True
            # For every training example for our pivot predictors
            for instance in range(0,number_pivot_instances):
                # The label for whether or not this pivot appears in the tweet appears after the unigrams
                class_label = pivot_input[instance][number_unigrams+pivot]
                if class_label < 0.0005:
                    continue
                # The instance is the unigrams in the tweet
                instance_without_label = pivot_input[instance,0:number_unigrams]

                # Train the pivot weights
                # Rule for checking the output is: class_label * weight_vector . instance
                # The pivot weights matrix is large and contains a column for each pivot so we just select the appropriate column
                actual_result = numpy.dot(pivot_weights[:,pivot], instance_without_label) * class_label

                # If this was misclassified then update the weights
                if actual_result <= 0:
                    pivot_weights[:,pivot] = pivot_weights[:,pivot] + class_label * learning_rate * instance_without_label
                    converged = False
            iterations = iterations + 1
    return pivot_weights

# Learns the final perceptron for SCL
# Needs the weights for the sentiment classification, the training examples, the weights for the pivot predictors and a learning rate
def learnSCLPerceptron(sentiment_input, learning_rate):
    # Number of rows in sentiment_input
    number_instances = sentiment_input.shape[0]
    # Number of columns in sentiment_input minus the classlabel
    number_features = sentiment_input.shape[1] -1
    # The last column of the input contains the label and the columns are indexed from 0
    class_label_index = number_features
    # The number of pivot features is the number of rows in thi
    number_of_pivots = thi.shape[0]
    # The weights for v have number_of_pivot columns
    v_weights = numpy.zeros(number_of_pivots)

    # Offsets
    v_bias = 0

    converged = False
    number_itterations = 0
    while converged == False and number_itterations < max_itterations:
        converged = True
        # For every training example
        for instance in range(0,number_instances):

            # The instance is the unigrams in the tweet
            instance_without_label = sentiment_input[instance,0:number_features]
            class_label = sentiment_input[instance][class_label_index]
            # Train the v weights
            # Rule for checking the output is: sentiment_weights * input + v * thi(x)
            intermediate_result = numpy.dot(sentiment_weights_weights, instance_without_label)+sentiment_bias

            second_intermediate_result = numpy.dot(thi, instance_without_label)
            prediction = intermediate_result+numpy.dot(v_weights, second_intermediate_result) + v_bias * class_label

            # If this was misclassified then update the weights
            if prediction <= 0:
                v_weights = v_weights + class_label * learning_rate * instance_without_label
                converged = False

        number_itterations = number_itterations + 1

    return (v_weights, v_bias)

# Learns the final perceptron for SCL
# Needs the weights for the sentiment classification, the training examples, the weights for the pivot predictors and a learning rate
def testSCLPerceptron(sentiment_input, positive_sentiment_weights, negative_sentiment_weights, neutral_sentiment_weights, positive_sentiment_bias, negative_sentiment_bias, neutral_sentiment_bias):
    # Number of rows in sentiment_input
    number_instances = sentiment_input.shape[0]
    # Number of columns in sentiment_input minus the classlabel
    number_features = sentiment_input.shape[1] -1
    # The last column of the input contains the label and the columns are indexed from 0
    class_label_index = number_features
    # The number of pivot features is the number of rows in thi
    number_of_pivots = thi.shape[0]

    converged = False
    number_itterations = 0
    correct = 0
    incorrect = 0
    # For every training example
    for instance in range(0,number_instances):

        # The instance is the unigrams in the tweet
        instance_without_label = sentiment_input[instance,0:number_features]
        class_label = sentiment_input[instance][class_label_index]
        # Train the v weights
        # Rule for checking the output is: sentiment_weights * input + v * thi(x)

        if class_label == 1:
            intermediate_result = numpy.dot(positive_sentiment_weights, instance_without_label)+positive_sentiment_bias
        elif class_label == 0:
            intermediate_result = numpy.dot(neutral_sentiment_weights, instance_without_label)+neutral_sentiment_bias
        else:
            intermediate_result = numpy.dot(negative_sentiment_weights, instance_without_label)+negative_sentiment_bias

        second_intermediate_result = numpy.dot(thi, instance_without_label)
        positive_prediction = numpy.dot(positive_v_weights, instance_without_label) 
        negative_prediction = numpy.dot(negative_v_weights, instance_without_label) 
        neutral_prediction = numpy.dot(neutral_v_weights, instance_without_label) 

        prediction = max(positive_prediction, negative_prediction, neutral_prediction)

        if prediction == positive_prediction:
            label = 1
        elif prediction == neutral_prediction:
            label = 0
        else:
            label = -1

        if class_label != label:
            incorrect = incorrect +1
        else:
            correct = correct +1

    print(incorrect)
    print(correct)



def main():
## Perform SCL
#     print("Reading data")
# # Standard sentiment training data from a single domain with the class label of -1,0,1 in the final column
#     sentiment_data = numpy.genfromtxt(open("tech_training.arff","rb") , invalid_raise=False, delimiter=",",skiprows=0)
#     print(sentiment_data.shape)
# # Pivot training data which contains the unigrams followed by a binary value for each pivot indicating if the pivot appears in the tweet or not
#     pivot_data = numpy.genfromtxt(open("politics_test.arff","rb"),delimiter=",",skiprows=0)
#     number_unigrams = sentiment_data.shape[1] -1

# # Learn the Sentiment Weights
#     print("Learning Sentiment Weights")
#     positive_sentiment_weights, negative_sentiment_weights, neutral_sentiment_weights, positive_sentiment_bias, negative_sentiment_bias, neutral_sentiment_bias  = learnPerceptron(sentiment_data, learning_rate)
# # Convinence methods for saving / loading the weights for faster testing
# # sentiment_weights = numpy.load("sentiment_weights.npy")
# # print(sentiment_weights)
# # numpy.save("sentiment_weights", sentiment_weights)
# # Now learn the Thi Matrix
#     print("Learning Thi Weights")
#     thi_weights = learnPivotPerceptron(pivot_data, learning_rate, number_unigrams)
#     print thi_weights
# Convinence methods for saving / loading the weights for faster testing
# numpy.save("thi_weights", thi_weights)
# thi_weights = numpy.load("thi_weights.npy")

# Now we have to perform SVD on Thi as we don't need all of the pivots as many are likely synomns
#     print("Performing SVD")
#     u, s, v = numpy.linalg.svd(thi_weights)

#     u = numpy.transpose(u)
# # Now keep the top pivots
#     u = u[0:pivots_to_keep][:]
# Finally we can train the final classifier
    print("Training Final Classifier")
    positive_or_not = numpy.genfromtxt(open("positive_tech.arff","rb") , invalid_raise=False, delimiter=",",skiprows=0)
    negative_or_not = numpy.genfromtxt(open("negative_tech.arff","rb") , invalid_raise=False, delimiter=",",skiprows=0)
    neutral_or_not = numpy.genfromtxt(open("neutral_tech.arff","rb") , invalid_raise=False, delimiter=",",skiprows=0)
    positive_v_weights, positive_v_bias = learnPerceptron(positive_or_not, learning_rate)
    negative_v_weights, negative_v_bias = learnPerceptron(negative_or_not, learning_rate)
    neutral_v_weights, neutral_v_bias = learnPerceptron(neutral_or_not, learning_rate)
    print positive_v_weights
    print negative_v_weights
    print neutral_v_weights
# Convinence methods for saving / loading the weights for faster testing
# numpy.save("v_weights", v_weights)
# v_weights = numpy.load("v_weights.npy")
# print(v_weights)
# print(v_weights)
# Now we can test the classifiers performance on the test domain

    print("Testing Final Classifier")
    test_data = numpy.genfromtxt(open("politics_training.arff","rb"),delimiter=",",skiprows=0)
    testPerceptron(test_data, positive_v_weights, negative_v_weights, neutral_v_weights, positive_v_bias, negative_v_bias, neutral_v_bias)

if __name__ == "__main__":
    main()
