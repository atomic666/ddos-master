
import numpy as np
import random
import csv
from nn import neural_net, LossHistory
import os.path
import timeit

NUM_INPUT = 2
GAMMA = 0.9 # Forgetting.
TUNING = False  # If False, just use arbitrary, pre-selected params.

nn_param = [128, 128]
params = {
    "batchSize": 64,
    "buffer": 50000,
    "nn": nn_param
    }
model = neural_net(NUM_INPUT, nn_param)
train_net(model, params, environment, modelname)

def train_net(model, params, environment, modelname="untitle", train_packets = 50000):
    filename = modelname #params_to_filename(params)
    observe = 1000  # Number of packets to observe before training.
    epsilon = 1
    train_packets = train_packets  # Number of packets to play.
    batchSize = params['batchSize']
    buffer = params['buffer']
    distance = 0

    # max_distance = 0
    # istance = 0
    t = 0
    data_collect = []
    loss_log = []

    # # Assain environment State instance.
    env_state = environment

    # # Get initial state by doing nothing and getting the state.
    _, state, SAVE = env_state.run(0,"T")

    # # Let's time it.
    start_time = timeit.default_timer()

    while (t < train_packets) and not env_state.exit:
        yield True
        t += 1
        distance += 1
        # Choose an action.
        if random.random() < epsilon or t < observe:
            action = np.random.randint(0, 3)  # random
        else:
            # Get Q values for each action.
            qval = model.predict(state, batch_size=1)
            action = (np.argmax(qval))  # best
        yield action
        # Take action, observe new state and get our treat.
        reward, new_state, SAVE = env_state.run(action,"T")

def log_results(filename, data_collect, loss_log, istest = False):
    # Save the results to a file so we can graph it later.
    if(istest):
        drt = "../"
    else:
        drt = ""
    with open(drt+'results/sonar-frames/learn_data-' + filename + '.csv', 'w') as data_dump:
        wr = csv.writer(data_dump)
        wr.writerows(data_collect)

    with open(drt+'results/sonar-frames/loss_data-' + filename + '.csv', 'w') as lf:
        wr = csv.writer(lf)
        for loss_item in loss_log:
            wr.writerow(loss_item)

def process_minibatch2(minibatch, model):
    # by Microos, improve this batch processing function
    #   and gain 50~60x faster speed (tested on GTX 1080)
    #   significantly increase the training FPS

    # instead of feeding data to the model one by one,
    #   feed the whole batch is much more efficient

    mb_len = len(minibatch)

    old_states = np.zeros(shape=(mb_len, 3))
    actions = np.zeros(shape=(mb_len,))
    rewards = np.zeros(shape=(mb_len,))
    new_states = np.zeros(shape=(mb_len, 3))

    for i, m in enumerate(minibatch):
        old_state_m, action_m, reward_m, new_state_m = m
        old_states[i, :] = old_state_m[...]
        actions[i] = action_m
        rewards[i] = reward_m
        new_states[i, :] = new_state_m[...]

    old_qvals = model.predict(old_states, batch_size=mb_len)
    new_qvals = model.predict(new_states, batch_size=mb_len)

    maxQs = np.max(new_qvals, axis=1)
    y = old_qvals
    non_term_inds = np.where(rewards > 0)[0]
    term_inds = np.where(rewards <= 0)[0]

    y[non_term_inds, actions[non_term_inds].astype(int)] = rewards[non_term_inds] + (GAMMA * maxQs[non_term_inds])
    y[term_inds, actions[term_inds].astype(int)] = rewards[term_inds]

    X_train = old_states
    y_train = y
    return X_train, y_train


def process_minibatch(minibatch, model):
    """This does the heavy lifting, aka, the training. It's super jacked."""
    X_train = []
    y_train = []
    # Loop through our batch and create arrays for X and y
    # so that we can fit our model at every step.
    for memory in minibatch:
        # Get stored values.
        old_state_m, action_m, reward_m, new_state_m = memory
        # Get prediction on old state.
        old_qval = model.predict(old_state_m, batch_size=1)
        # Get prediction on new state.
        newQ = model.predict(new_state_m, batch_size=1)
        # Get our predicted best move.
        maxQ = np.max(newQ)
        y = np.zeros((1, 3))
        y[:] = old_qval[:]
        # Check for terminal state.
        if reward_m < 0:  # non-terminal state
            update = (reward_m + (GAMMA * maxQ))
        else:  # terminal state
            update = reward_m
        # Update the value for the action we took.
        y[0][action_m] = update
        X_train.append(old_state_m.reshape(NUM_INPUT,))
        y_train.append(y.reshape(3,))

    X_train = np.array(X_train)
    y_train = np.array(y_train)

    return X_train, y_train


def params_to_filename(params):
    return str(params['nn'][0]) + '-' + str(params['nn'][1]) + '-' + \
            str(params['batchSize']) + '-' + str(params['buffer'])


def launch_learn(params,environment, modelname):
    filename = modelname
    print("Trying %s" % filename)
    # Make sure we haven't run this one.
    if not os.path.isfile('results/sonar-frames/loss_data-' + filename + '.csv'):
        # Create file so we don't double test when we run multiple
        # instances of the script at the same time.
        open('results/sonar-frames/loss_data-' + filename + '.csv', 'a').close()
        print("Starting test.")
        # Train.
        model = neural_net(NUM_INPUT, params['nn'])
        train_net(model, params, environment, modelname)
    else:
        print("Already tested.")

def train(environment, modelname="untitle"):
    if TUNING:
        param_list = []
        nn_params = [[164, 150], [256, 256],
                     [512, 512], [1000, 1000]]
        batchSizes = [40, 100, 400]
        buffers = [10000, 50000]
        for nn_param in nn_params:
            for batchSize in batchSizes:
                for buffer in buffers:
                    params = {
                        "batchSize": batchSize,
                        "buffer": buffer,
                        "nn": nn_param
                    }
                    param_list.append(params)

        for param_set in param_list:
            launch_learn(param_set, environment, modelname)
    else:
        nn_param = [128, 128]
        params = {
            "batchSize": 64,
            "buffer": 50000,
            "nn": nn_param
        }
        model = neural_net(NUM_INPUT, nn_param)
        train_net(model, params, environment, modelname)

if __name__ == "__main__":
    environment = Environment.Environment()
    train(environment, "untitle")