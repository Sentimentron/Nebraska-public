import numpy
max_itterations = 1
learning_rate = 0.1
pivots_to_keep = 800

# sentiment_input is a matrix of columns containing unigrams and rows containing instances. The final column is the class label
def learnPerceptron(sentiment_input, learning_rate):
    # Number of rows in sentiment_input
    number_instances = sentiment_input.shape[0]
    # Number of columns in sentiment_input minus the classlabel
    number_features = sentiment_input.shape[1] -1
    # The last column of the input contains the label and the columns are indexed from 0
    class_label_index = number_features
    # The standard set of weights for sentiment classification has 1 column and number_unigram rows
    standard_weights = numpy.zeros(number_features)
    # numpy.zeroes takes the number of rows then the number of columns

    converged = False
    number_itterations = 0
    while converged == False and number_itterations < max_itterations:
        converged = True
        # For every training example
        for instance in range(0,number_instances):
            if sentiment_input[instance][class_label_index] == 0:
                continue
            # Each training example needs to be used to train the sentiment weights once
            instance_without_label = sentiment_input[instance,0:number_features]
            class_label = sentiment_input[instance][class_label_index]
            # Train the sentiment weights
            # Rule for checking the output is: class_label * weight_vector . instance
            actual_result = numpy.dot(standard_weights, instance_without_label) * class_label

            # If this was misclassified then update the weights
            if actual_result<= 0:
                standard_weights = standard_weights + class_label * learning_rate * instance_without_label
                converged = False
        number_itterations = number_itterations+1

    return standard_weights

# Runs sentiment_input through the perceptron and reports the accuracy
def  testPerceptron(sentiment_input, weights):
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
        if sentiment_input[instance][class_label_index] == 0:
            continue

        instance_without_label = sentiment_input[instance,0:number_features]
        class_label = sentiment_input[instance][class_label_index]
        # Rule for checking the output is: class_label * weight_vector . instance
        actual_result = numpy.dot(weights, instance_without_label) * class_label

        if actual_result<= 0:
            incorrect = incorrect +1
        else:
            correct = correct +1
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
        number_itterations = 0
        while converged == False and number_itterations < max_itterations:
            converged = True
            # For every training example for our pivot predictors
            for instance in range(0,number_pivot_instances):
                # The instance is the unigrams in the tweet
                instance_without_label = pivot_input[instance,0:number_unigrams]
                # The label for whether or not this pivot appears in the tweet appears after the unigrams
                class_label = pivot_input[instance][number_unigrams+pivot]
                # Train the pivot weights
                # Rule for checking the output is: class_label * weight_vector . instance
                # The pivot weights matrix is large and contains a column for each pivot so we just select the appropriate column
                actual_result = numpy.dot(pivot_weights[:,pivot], instance_without_label) * class_label

                # If this was misclassified then update the weights
                if actual_result<= 0:
                    pivot_weights[:,pivot] = pivot_weights[:,pivot] + class_label * learning_rate * instance_without_label
                    converged = False
            number_itterations = number_itterations + 1
    return pivot_weights

# Learns the final perceptron for SCL
# Needs the weights for the sentiment classification, the training examples, the weights for the pivot predictors and a learning rate
def learnSCLPerceptron(sentiment_weights, sentiment_input, thi, learning_rate):
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
    print(thi.shape)
    converged = False
    number_itterations = 0
    while converged == False and number_itterations < max_itterations:
        converged = True
        # For every training example
        for instance in range(0,number_instances):
            if sentiment_input[instance][class_label_index] == 0:
                continue
            # The instance is the unigrams in the tweet
            instance_without_label = sentiment_input[instance,0:number_features]
            class_label = sentiment_input[instance][class_label_index]
            # Train the v weights
            # Rule for checking the output is: sentiment_weights * input + v * thi(x)
            intermediate_result = numpy.dot(sentiment_weights, instance_without_label)
            second_intermediate_result = numpy.dot(thi, instance_without_label)
            actual_result = class_label * (intermediate_result + numpy.dot(v_weights,second_intermediate_result))

            # If this was misclassified then update the weights
            if actual_result <= 0:
                v_weights = v_weights + class_label * learning_rate * second_intermediate_result
                converged = False
        number_itterations = number_itterations +1
    return v_weights

def testSCLPerceptron(sentiment_weights, test_input, v_weights, thi):
    # Number of rows in test_input
    number_instances = test_input.shape[0]
    # Number of columns in test_input minus the classlabel
    number_features = test_input.shape[1] -1
    # The last column of the input contains the label and the columns are indexed from 0
    class_label_index = number_features

    correct = 0
    incorrect = 0
    # For every test example
    for instance in range(0,number_instances):
        if test_input[instance][class_label_index] == 0:
            continue

        instance_without_label = test_input[instance,0:number_features]
        class_label = test_input[instance][class_label_index]
        # Rule to check the output is sentiment_weights * input + v * thi(x)
        intermediate_result = numpy.dot(sentiment_weights, instance_without_label)
        second_intermediate_result = numpy.dot(thi, instance_without_label)
        actual_result = intermediate_result + numpy.dot(v_weights,second_intermediate_result)
        if actual_result > 0:
            classification = 1
        else:
            classification = -1

        if classification == test_input[instance][class_label_index]:
            correct = correct +1
        else:
            incorrect = incorrect +1

    print(correct / (incorrect + correct) )
    print(incorrect)
    print(correct)

## Perform SCL
print("Reading data")
# Standard sentiment training data from a single domain with the class label of -1,0,1 in the final column
sentiment_data = numpy.genfromtxt(open("tech_training.arff","rb"),delimiter=",",skiprows=0)
# Pivot training data which contains the unigrams followed by a binary value for each pivot indicating if the pivot appears in the tweet or not
pivot_data = numpy.genfromtxt(open("politics_test.arff","rb"),delimiter=",",skiprows=0)
number_unigrams = sentiment_data.shape[1] -1
# Learn the Sentiment Weights
print("Learning Sentiment Weights")
sentiment_weights = learnPerceptron(sentiment_data, learning_rate)
# Convinence methods for saving / loading the weights for faster testing
# sentiment_weights = numpy.load("sentiment_weights.npy")
print(sentiment_weights)
numpy.save("sentiment_weights", sentiment_weights)
# Now learn the Thi Matrix
print("Learning Thi Weights")
thi_weights = learnPivotPerceptron(pivot_data, learning_rate, number_unigrams)
# Convinence methods for saving / loading the weights for faster testing
numpy.save("thi_weights", thi_weights)
# thi_weights = numpy.load("thi_weights.npy")

# Now we have to perform SVD on Thi as we don't need all of the pivots as many are likely synomns
print("Performing SVD")
u, s, v = numpy.linalg.svd(thi_weights)

u = numpy.transpose(u)
# Now keep the top pivots
u = u[0:pivots_to_keep][:]
# Finally we can train the final classifier
print("Training Final Classifier")
v_weights = learnSCLPerceptron(sentiment_weights, sentiment_data, u, learning_rate)
# Convinence methods for saving / loading the weights for faster testing
numpy.save("v_weights", v_weights)
# v_weights = numpy.load("v_weights.npy")
print(v_weights)
# print(v_weights)
# Now we can test the classifiers performance on the test domain
print("Testing Final Classifier")
test_data = numpy.genfromtxt(open("politics_training.arff","rb"),delimiter=",",skiprows=0)
testSCLPerceptron(sentiment_weights, test_data, v_weights, u)
