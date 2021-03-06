import utility as util
import numpy as np
import itertools as it
from enum import Enum

class KNN:
    """Implements the K-nearest-neighbours algorithm.

    Calling `predict` with an array of unlabeled samples calculates and returns an array of labels, one for each sample in the same position.
    
    Before calling `predict()`, the best value for K has to be determined using a set of training samples and validation samples and the corresponding labels.
    Manually invoking `determine_best_K()` determines the success rate of each K from 1 up to and including `max_K` and selects the best K to use.
    `predict()` can be called multiple times after calling `determine_best_K()`.
    
    For convenience, instances of this class maintain references to the training labels and samples that were passed to the constructor.

    The algorithm used the Minkowski distance and supports specifying weights for each dimension in the input data.
    """

    class NeighbourWeightingStrategy(Enum):
        MAJORITY_VOTE = 1
        WEIGHTED_MAJORITY_VOTE = 2

    class KNNOptions:
        """Configures the KNN algorithm."""

        def __init__(self, max_K, P, weights, neighbour_weighting_strategy):
            """
            `max_K` -- The maximum value for K that `determine_best_K()` will try.\n
            `P` -- The power parameter for the Minkowski distance algorithm.\n
            `weights` -- A NumPy ndarray of numbers with shape `[n]` where `n` equal to the number of elements in a sample.
            These can be used to scale the contribution each dimension of the input samples during the calculation of the distance between samples.\n
            `neighbour_weighting_strategy` -- A member of `NeighbourWeightingStrategy` indicating how neighbours of samples should be weighted during label prediction.
            """
            self.max_K, self.P = max_K, P
            self.weights, self.neighbour_weighting_strategy = weights, neighbour_weighting_strategy

    @staticmethod
    def __predict(samples, K, weights, P, training_labels, training_samples, neighbour_weighting_func):
        labels = []
        for sample in samples:
            # Calculate the Minkowski distances from sample to each training sample and store the results in an array
            distances_squared = np.empty(training_samples.shape[0])
            for distance, training_sample in zip(np.nditer(distances_squared, op_flags=['writeonly']), training_samples):
                distance[...] = util.minkowski_squared(sample, training_sample, weights, P)

            # Calculate the indices of the K nearest neighbours by partitioning our distances array using K-1 as the pivot.
            # Then use the indices to look up the corresponding labels and distances.
            neighbour_indices = np.argpartition(distances_squared, K-1)[:K]
            neighbour_labels = training_labels[neighbour_indices]
            neighbour_distances_squared = distances_squared[neighbour_indices]

            # Count each label, take the most common label, and append it to the labels array as a result.
            labels.append(neighbour_weighting_func(neighbour_labels, neighbour_distances_squared))

        return np.array(labels)

    def __init__(self, options, training_labels, training_samples):
        """
        `options` -- A `KNNOptions` instance.\n
        `training_labels` -- A NumPy array of 1 dimension containing the labels for the training samples.\n
        `training_samples` -- A NumPy array with at least 2 dimensions. It contains the training samples.
        """
        self.__options, self.__training_labels = options, training_labels
        self.__training_samples, self.__K = training_samples, None

        if options.neighbour_weighting_strategy == KNN.NeighbourWeightingStrategy.MAJORITY_VOTE:
            self.__neighbour_weighting_func = util.majority_vote
        elif options.neighbour_weighting_strategy == KNN.NeighbourWeightingStrategy.WEIGHTED_MAJORITY_VOTE:
            self.__neighbour_weighting_func = util.weighted_majority_vote

    def determine_best_K(self, validation_labels, validation_samples):
        """Determine the best K to use according to its performance. This can take a long time!

        Calculates the performance (# of correctly guessed labels of the validation samples) of each K from 1 up to and including `max_K` (which was specified in the options object).
        Then selects and stores the best value for K. It will be used for all subsequent calls to `predict()`.

        `validation_labels` -- An array of strings containing the labels of the validation sample.\n
        `validation_samples` -- A NumPy array with the same shape as the training data. It contains the validation samples that the algorithm is going to guess the labels for.\n
        Returns the choosen K and its performance (as the number of correctly guessed labels)
        """

        best_K = 0
        best_performance = 0
        for K in range(1, self.__options.max_K + 1):
            labels = KNN.__predict(validation_samples, \
                K, \
                self.__options.weights, \
                self.__options.P, \
                self.__training_labels, \
                self.__training_samples, \
                self.__neighbour_weighting_func)
            performance = (labels == validation_labels).sum()
            
            print('K {}. Correct {} out of {} ({}%)'.format( \
                K, performance, len(validation_samples), (100 * performance / len(validation_samples)))) # Here for for demo purposes
                
            if performance > best_performance:
                best_performance, best_K = performance, K

        print('Done! Best perf. of {}. K = {}'.format(best_performance, best_K)) # Here for for demo purposes
        self.__K = best_K
        return best_K, best_performance

    def predict(self, samples, training_labels = None, training_samples = None):
        """Predicts the labels for the given `samples` and returns it as a 1 dimensional NumPy array.

        `samples` -- An array of strings containing the labels of the sample that the algorithm is going to predict the labels for.\n
        `training_labels` -- An array containing the training labels. If `None`, uses the labels passed to the constructor. (Default = `None`)\n
        `training_samples` -- A NumPy array containing the training samples. If `None`, uses the samples passed to the constructor. (Default = `None`)
        
        Returns the predicted labels as a 1 dimensional NumPy array.

        Raises an error if `determine_best_K()` was never called.
        """
        if not self.__K:
            raise Exception('K was not determined. Call determine_best_K() first before calling predict().')
       
        if training_labels is None:
            training_labels = self.__training_labels
        if training_samples is None:
            training_samples = self.__training_samples
        return KNN.__predict(samples, \
            self.__K, \
            self.__options.weights, \
            self.__options.P, \
            training_labels, \
            training_samples, \
            self.__neighbour_weighting_func)
