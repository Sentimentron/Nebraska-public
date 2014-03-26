import numpy

# sentiment_input is a matrix of columns containing unigrams and rows containing instances. The final column is the class label
# pivot_input is a matrix of columns containing pivots and rows contatining whether or not a tweet contains this pivot.
def learnPerceptron(sentiment_input, learning_rate):
    # Number of rows in sentiment_input
    number_instances = sentiment_input.shape[0]
    print(sentiment_input.shape)
    # Number of columns in sentiment_input minus the classlabel
    number_features = sentiment_input.shape[1] -1
    # number_pivot_features = pivot_input.shape[1]
    # The last column of the input contains the label and the columns are indexed from 0
    class_label_index = number_features
    # We need two sets of weights one set for the standard sentiment classification and another for the sets of pivot features
    # The standard set of weights for sentiment classification has 1 column and number_unigram rows
    standard_weights = numpy.zeros(number_features)
    # The weights for the pivot features have number_pivot columns and number_unigram rows
    # numpy.zeroes takes the number of rows then the number of columns

    converged = False
    number_itterations = 0
    max_itterations = 100000000
    while converged == False:
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

    return standard_weights


def  testPerceptron(sentiment_input, weights):
    # Number of rows in sentiment_input
    number_instances = sentiment_input.shape[0]
    # Number of columns in sentiment_input minus the classlabel
    number_features = sentiment_input.shape[1] -1
    # number_pivot_features = pivot_input.shape[1]
    # The last column of the input contains the label and the columns are indexed from 0
    class_label_index = number_features
    # We need two sets of weights one set for the standard sentiment classification and another for the sets of pivot features
    # The standard set of weights for sentiment classification has 1 column and number_unigram rows
    standard_weights = numpy.zeros(number_features)
    # The weights for the pivot features have number_pivot columns and number_unigram rows
    # numpy.zeroes takes the number of rows then the number of columns
    # pivot_weights = numpy.zeros(number_features, number_pivot_features)
    correct = 0
    incorrect = 0
    # For every training example
    for instance in range(0,number_instances):
        if sentiment_input[instance][class_label_index] == 0:
            continue
        # Each training example needs to be used to train the sentiment weights once
        instance_without_label = sentiment_input[instance,0:number_features]
        class_label = sentiment_input[instance][class_label_index]
        # Train the sentiment weights
        # Rule for checking the output is: class_label * weight_vector . instance
        actual_result = numpy.dot(weights, instance_without_label) * class_label

        # If this was misclassified then update the weights
        if actual_result<= 0:
            incorrect = incorrect +1
        else:
            correct = correct +1

    print(incorrect)
    print(correct)





def learnPivotPerceptron(pivot_input, learning_rate):
    # The weights for the pivot features have number_pivot columns and number_unigram rows
    # numpy.zeroes takes the number of rows then the number of columns
    pivot_weights = numpy.zeros(number_features, number_pivot_features)
    # Number of rows in pivot input is more as we have data from both domains
    number_pivot_instances = pivot_input.shape[0]

    # Now we need to train the pivot classifiers
    for pivot in range(0, number_pivot_features):
        number_itterations = 0
        max_itterations = 100000000
        while converged == False and number_itterations < max_itterations:
            converged = True
            # For every training example for our pivot predictors
            for instance in range(0,number_pivot_instances):
                # Each training example needs to be used to train the sentiment weights once
                instance_without_label = pivot_input[instance,0:number_unigrams_in_pivots]
                class_label = pivot_input[instance][number_unigrams_in_pivots+pivot]
                # Train the pivot weights
                # Rule for checking the output is: class_label * weight_vector . instance
                actual_result = numpy.dot(pivot_weights[:,pivot], instance_without_label) * class_label

                # If this was misclassified then update the weights
                if actual_result<= 0:
                    pivot_weights = pivot_weights + class_label * learning_rate * instance_without_label
                    converged = False

    return pivot_weights

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

    converged = False
    number_itterations = 0
    max_itterations = 100000000
    while converged == False:
        converged = True
        # For every training example
        for instance in range(0,number_instances):
            if sentiment_input[instance][class_label_index] == 0:
                continue
            instance_without_label = sentiment_input[instance,0:number_features]
            class_label = sentiment_input[instance][class_label_index]
            # Train the sentiment weights
            # Rule for checking the output is: class_label * weight_vector . instance
            intermediate_result = dot(thi, instance_without_label)
            actual_result = numpy.dot(sentiment_weights, instance_without_label) + dot(v_weights , intermediate_result)

            # If this was misclassified then update the weights
            if actual_result <= 0:
                v_weights = v_weights + class_label * learning_rate * instance_without_label
                converged = False

    return v_weights


# sentiment_data = numpy.genfromtxt(open("unigrams.arff","rb"),delimiter=",",skiprows=0)
sentiment_data = numpy.matrix([ [1, 2], [3, 4] ])
print(sentiment_data.shape)
# pivot_data = numpy.genfromtxt(open("pivots.arff","rb"),delimiter=",",skiprows=0)

# So we need to train the sentiment weights
sentiment_weights = learnPerceptron(sentiment_data,0.1)
# Then the weights for thi
# thi_weights = learnPivotPerceptron(pivot_data, 0.1)
# u, s, v = np.linalg.svd(thi_weights)
# u = transpose(u)
# u = u[800,:]
# # Now train the final perceptron
# learnSCLPerceptron(sentiment_weights, sentiment_data, u, 0.1)
