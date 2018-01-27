"""
@file
@brief Taken from `Tutorial on logistic regression <http://deeplearning.net/tutorial/logreg.html>`_

This tutorial introduces logistic regression using Theano and stochastic
gradient descent. Logistic regression is a probabilistic, linear classifier. It is parametrized
by a weight matrix :math:`W` and a bias vector :math:`b`. Classification is
done by projecting data points onto a set of hyperplanes, the distance to
which is used to determine a class membership probability.
Mathematically, this can be written as:

.. math::

      P(Y=i|x, W,b) &= f_i(W x + b) \\\\
                    &= \\frac {e^{W_i x + b_i}} {\\sum_j e^{W_j x + b_j}}

:math:`f_i`` is the activation function attached to the neuron *i*
(see `rectifier <https://en.wikipedia.org/wiki/Rectifier_(neural_networks)>`_).
The output of the model or prediction is then done by taking the argmax of
the vector whose i'th element is :math:`P(Y=i|x)`.

.. math::

    y_{pred} = \\arg \\max_i P(Y=i|x,W,b)


This tutorial presents a stochastic gradient descent optimization method
suitable for large datasets. Example:

::

    from src.ensae_teaching_cs.examples.theano_logreg import sgd_optimization_mnist, predict
    from pyensae.datasource import download_data

    dataset = "mnist.pkl.gz"
    if not os.path.exists(dataset):
        download_data(dataset, website ="http://deeplearning.net/data/mnist/")

    model = "log_reg_theano.bin"
    sgd_optimization_mnist(dataset=dataset, saved_model=model, n_epochs=2, fLOG=print)
    pred = predict(model, dataset, 10)

"""
import gzip
import os
import sys
import timeit
import pickle

import numpy

from pyquickhelper.loghelper import noLOG


class TheanoLogisticRegression(object):
    """
    Multi-class Logistic Regression Class

    The logistic regression is fully described by a weight matrix :math:`W`
    and bias vector :math:`b`. Classification is done by projecting data
    points onto a set of hyperplanes, the distance to which is used to
    determine a class membership probability.
    """

    def __init__(self, input, n_in, n_out):
        """ Initialize the parameters of the logistic regression

        :type input: theano.tensor.TensorType
        :param input: symbolic variable that describes the input of the
                      architecture (one minibatch)

        :type n_in: int
        :param n_in: number of input units, the dimension of the space in
                     which the datapoints lie

        :type n_out: int
        :param n_out: number of output units, the dimension of the space in
                      which the labels lie

        """
        # Delayed import as theano is not maintained anymore.
        import theano
        import theano.tensor as T

        self._theano = theano
        self._T = T

        # start-snippet-1
        # initialize with 0 the weights W as a matrix of shape (n_in, n_out)
        self.W = theano.shared(
            value=numpy.zeros(
                (n_in, n_out),
                dtype=theano.config.floatX
            ),
            name='W',
            borrow=True
        )
        # initialize the biases b as a vector of n_out 0s
        self.b = theano.shared(
            value=numpy.zeros(
                (n_out,),
                dtype=theano.config.floatX
            ),
            name='b',
            borrow=True
        )

        # symbolic expression for computing the matrix of class-membership
        # probabilities
        # Where:
        # W is a matrix where column-k represent the separation hyperplane for
        # class-k
        # x is a matrix where row-j  represents input training sample-j
        # b is a vector where element-k represent the free parameter of
        # hyperplane-k
        self.p_y_given_x = self._T.nnet.softmax(
            self._T.dot(input, self.W) + self.b)

        # symbolic description of how to compute prediction as class whose
        # probability is maximal
        self.y_pred = self._T.argmax(self.p_y_given_x, axis=1)
        # end-snippet-1

        # parameters of the model
        self.params = [self.W, self.b]

        # keep track of model input
        self.input = input

    def __getstate__(self):
        """
        Avoids pickling modules (_T, _theano).
        """
        return {k: v for k, v in self.__dict__ if k in {'W', 'b', 'p_y_given_x', 'params', 'input', 'y_pred'}}

    def __setstate__(self, d):
        """
        Unpickles information, restore members pointing to modules.
        """
        self.__dict__ = d
        import theano
        import theano.tensor as T
        self._theano = theano
        self._T = T

    def negative_log_likelihood(self, y):
        """
        Return the mean of the negative log-likelihood of the prediction
        of this model under a given target distribution.

        .. math::

            \\frac{1}{|\\mathcal{D}|} \\mathcal{L} (\\theta=\\{W,b\\}, \\mathcal{D}) =
            \\frac{1}{|\\mathcal{D}|} \\sum_{i=0}^{|\\mathcal{D}|}
                \\log(P(Y=y^{(i)}|x^{(i)}, W,b)) \\\\
            \\ell (\\theta=\\{W,b\\}, \\mathcal{D})

        :type y: theano.tensor.TensorType
        :param y: corresponds to a vector that gives for each example the
                  correct label

        Note: we use the mean instead of the sum so that
              the learning rate is less dependent on the batch size
        """
        # start-snippet-2
        # y.shape[0] is (symbolically) the number of rows in y, i.e.,
        # number of examples (call it n) in the minibatch
        # T.arange(y.shape[0]) is a symbolic vector which will contain
        # [0,1,2,... n-1] T.log(self.p_y_given_x) is a matrix of
        # Log-Probabilities (call it LP) with one row per example and
        # one column per class LP[T.arange(y.shape[0]),y] is a vector
        # v containing [LP[0,y[0]], LP[1,y[1]], LP[2,y[2]], ...,
        # LP[n-1,y[n-1]]] and T.mean(LP[T.arange(y.shape[0]),y]) is
        # the mean (across minibatch examples) of the elements in v,
        # i.e., the mean log-likelihood across the minibatch.
        return -self._T.mean(self._T.log(self.p_y_given_x)[self._T.arange(y.shape[0]), y])
        # end-snippet-2

    def errors(self, y):
        """
        Return a float representing the number of errors in the minibatch
        over the total number of examples of the minibatch ; zero one
        loss over the size of the minibatch

        :type y: theano.tensor.TensorType
        :param y: corresponds to a vector that gives for each example the
                  correct label
        """

        # check if y has same dimension of y_pred
        if y.ndim != self.y_pred.ndim:
            raise TypeError(
                'y should have the same shape as self.y_pred',
                ('y', y.type, 'y_pred', self.y_pred.type)
            )
        # check if y is of the correct datatype
        if y.dtype.startswith('int'):
            # the T.neq operator returns a vector of 0s and 1s, where 1
            # represents a mistake in prediction
            return self._T.mean(self._T.neq(self.y_pred, y))
        else:
            raise NotImplementedError()


def theano_load_data(dataset):
    '''
    Loads the dataset

    :type dataset: string
    :param dataset: the path to the dataset (here MNIST)
    '''
    # delayed import as theano is not maintained anymore
    import theano
    import theano.tensor as T

    if not os.path.exists(dataset):
        raise FileNotFoundError(dataset)

    # Load the dataset
    with gzip.open(dataset, 'rb') as f:
        try:
            train_set, valid_set, test_set = pickle.load(f, encoding='latin1')
        except Exception:
            train_set, valid_set, test_set = pickle.load(f)

    # train_set, valid_set, test_set format: tuple(input, target)
    # input is a numpy.ndarray of 2 dimensions (a matrix)
    # where each row corresponds to an example. target is a
    # numpy.ndarray of 1 dimension (vector) that has the same length as
    # the number of rows in the input. It should give the target
    # to the example with the same index in the input.

    def shared_dataset(data_xy, borrow=True):
        """ Function that loads the dataset into shared variables

        The reason we store our dataset in shared variables is to allow
        Theano to copy it into the GPU memory (when code is run on GPU).
        Since copying data into the GPU is slow, copying a minibatch everytime
        is needed (the default behaviour if the data is not in a shared
        variable) would lead to a large decrease in performance.
        """
        data_x, data_y = data_xy
        shared_x = theano.shared(numpy.asarray(data_x,
                                               dtype=theano.config.floatX),
                                 borrow=borrow)
        shared_y = theano.shared(numpy.asarray(data_y,
                                               dtype=theano.config.floatX),
                                 borrow=borrow)
        # When storing data on the GPU it has to be stored as floats
        # therefore we will store the labels as ``floatX`` as well
        # (``shared_y`` does exactly that). But during our computations
        # we need them as ints (we use labels as index, and if they are
        # floats it doesn't make sense) therefore instead of returning
        # ``shared_y`` we will have to cast it to int. This little hack
        # lets ous get around this issue
        return shared_x, T.cast(shared_y, 'int32')

    test_set_x, test_set_y = shared_dataset(test_set)
    valid_set_x, valid_set_y = shared_dataset(valid_set)
    train_set_x, train_set_y = shared_dataset(train_set)

    rval = [(train_set_x, train_set_y), (valid_set_x, valid_set_y),
            (test_set_x, test_set_y)]
    return rval


def theano_sgd_optimization_mnist(saved_model, dataset, learning_rate=0.13, n_epochs=1000, batch_size=600, fLOG=noLOG):
    """
    Demonstrates stochastic gradient descent optimization of a log-linear
    model. This is demonstrated on MNIST.

    :type learning_rate: float
    :param learning_rate: learning rate used (factor for the stochastic
                          gradient)

    :type n_epochs: int
    :param n_epochs: maximal number of epochs to run the optimizer

    :type dataset: string
    :param dataset: the path of the MNIST dataset ``mnist.pkl.gz``

    :param saved_model: filename used to saved the model
    :param fLOG: logging function

    :type batch_size: int
    :param batch_size: batch size
    """
    datasets = theano_load_data(dataset)

    train_set_x, train_set_y = datasets[0]
    valid_set_x, valid_set_y = datasets[1]
    test_set_x, test_set_y = datasets[2]

    # compute number of minibatches for training, validation and testing
    n_train_batches = train_set_x.get_value(borrow=True).shape[0] // batch_size
    n_valid_batches = valid_set_x.get_value(borrow=True).shape[0] // batch_size
    n_test_batches = test_set_x.get_value(borrow=True).shape[0] // batch_size

    ######################
    # BUILD ACTUAL MODEL #
    ######################
    fLOG('... building the model')

    # allocate symbolic variables for the data
    import theano.tensor as T
    index = T.lscalar()  # index to a [mini]batch

    # generate symbolic variables for input (x and y represent a
    # minibatch)
    x = T.matrix('x')  # data, presented as rasterized images
    y = T.ivector('y')  # labels, presented as 1D vector of [int] labels

    # construct the logistic regression class
    # Each MNIST image has size 28*28
    classifier = TheanoLogisticRegression(input=x, n_in=28 * 28, n_out=10)

    # the cost we minimize during training is the negative log likelihood of
    # the model in symbolic format
    cost = classifier.negative_log_likelihood(y)

    # compiling a Theano function that computes the mistakes that are made by
    # the model on a minibatch
    import theano
    test_model = theano.function(
        inputs=[index],
        outputs=classifier.errors(y),
        givens={
            x: test_set_x[index * batch_size: (index + 1) * batch_size],
            y: test_set_y[index * batch_size: (index + 1) * batch_size]
        }
    )

    validate_model = theano.function(
        inputs=[index],
        outputs=classifier.errors(y),
        givens={
            x: valid_set_x[index * batch_size: (index + 1) * batch_size],
            y: valid_set_y[index * batch_size: (index + 1) * batch_size]
        }
    )

    # compute the gradient of cost with respect to theta = (W,b)
    g_W = T.grad(cost=cost, wrt=classifier.W)
    g_b = T.grad(cost=cost, wrt=classifier.b)

    # start-snippet-3
    # specify how to update the parameters of the model as a list of
    # (variable, update expression) pairs.
    updates = [(classifier.W, classifier.W - learning_rate * g_W),
               (classifier.b, classifier.b - learning_rate * g_b)]

    # compiling a Theano function `train_model` that returns the cost, but in
    # the same time updates the parameter of the model based on the rules
    # defined in `updates`
    train_model = theano.function(
        inputs=[index],
        outputs=cost,
        updates=updates,
        givens={
            x: train_set_x[index * batch_size: (index + 1) * batch_size],
            y: train_set_y[index * batch_size: (index + 1) * batch_size]
        }
    )
    # end-snippet-3

    ###############
    # TRAIN MODEL #
    ###############
    fLOG('... training the model')
    # early-stopping parameters
    patience = 5000  # look as this many examples regardless
    patience_increase = 2  # wait this much longer when a new best is
    # found
    improvement_threshold = 0.995  # a relative improvement of this much is
    # considered significant
    validation_frequency = min(n_train_batches, patience // 2)
    # go through this many
    # minibatche before checking the network
    # on the validation set; in this case we
    # check every epoch

    best_validation_loss = numpy.inf
    test_score = 0.
    start_time = timeit.default_timer()

    done_looping = False
    epoch = 0
    while (epoch < n_epochs) and (not done_looping):
        epoch = epoch + 1
        for minibatch_index in range(n_train_batches):

            minibatch_avg_cost = train_model(minibatch_index)
            # iteration number
            iter = (epoch - 1) * n_train_batches + minibatch_index

            if (iter + 1) % validation_frequency == 0:
                # compute zero-one loss on validation set
                validation_losses = [validate_model(i)
                                     for i in range(n_valid_batches)]
                this_validation_loss = numpy.mean(validation_losses)

                fLOG(
                    'epoch %i, minibatch %i/%i, validation error %f %% minibatch_avg_cost=%f' %
                    (
                        epoch,
                        minibatch_index + 1,
                        n_train_batches,
                        this_validation_loss * 100.,
                        minibatch_avg_cost
                    )
                )

                # if we got the best validation score until now
                if this_validation_loss < best_validation_loss:
                    # improve patience if loss improvement is good enough
                    if this_validation_loss < best_validation_loss *  \
                       improvement_threshold:
                        patience = max(patience, iter * patience_increase)

                    best_validation_loss = this_validation_loss
                    # test it on the test set

                    test_losses = [test_model(i)
                                   for i in range(n_test_batches)]
                    test_score = numpy.mean(test_losses)

                    fLOG(('     epoch %i, minibatch %i/%i, test error of best model %f %%') %
                         (epoch, minibatch_index + 1, n_train_batches, test_score * 100.))

                    # save the best model
                    with open(saved_model, 'wb') as f:
                        pickle.dump(classifier, f)

            if patience <= iter:
                done_looping = True
                break

    end_time = timeit.default_timer()
    fLOG(('Optimization complete with best validation score of %f %%,'
          'with test performance %f %%')
         % (best_validation_loss * 100., test_score * 100.))
    fLOG('The code run for %d epochs, with %f epochs/sec' % (
         epoch, 1. * epoch / (end_time - start_time)))
    fLOG(('The code for file ' + os.path.split(__file__)[1] +
          ' ran for %.1fs' % ((end_time - start_time))), file=sys.stderr)


def theano_predict(model, dataset, nfirst=-1):
    """
    An example of how to load a trained model and use it
    to predict labels.

    @param      model       model to load
    @param      dataset     dataset to apply to
    @param      nfirst      predict for the nfirst or -1 for all
    @return                 prediction
    """
    # delayed import as theano is not maintained anymore
    import theano

    with open(model, "rb") as f:
        classifier = pickle.load(f)

    # compile a predictor function
    predict_model = theano.function(
        inputs=[classifier.input],
        outputs=classifier.y_pred)

    # We can test it on some examples from test test
    datasets = theano_load_data(dataset)
    test_set_x, test_set_y = datasets[2]
    test_set_x = test_set_x.get_value()

    if nfirst > 0:
        test_set_x = test_set_x[:10]
    predicted_values = predict_model(test_set_x)
    return predicted_values
