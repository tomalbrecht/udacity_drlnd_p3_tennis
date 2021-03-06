# Report

This project is based on my former project [`Continuous Control`](https://github.com/tomalbrecht/udacity_drlnd_p2) from this drlnd course. I used this as base project, because I already implemented the code to run multiple agents.

I chose the DDPG (Deep Deterministic Policy Gradients) algorithm because it is able to handle continuous spaces, which is needed for this environment and seemed easier as discretization (see Chapter 1 of the course). Continuous spaces make it more difficult to train an agent, because the action space gets highly dimensional. In contrast DQN (with Q-tables)solves problems with high-dimensional observation spaces, but it can only handle discrete and low-dimensional action spaces. Using a neural network to approximate these values in a convinient way.

The algorithm also benefits from two separate neural network (actor and critic) - so the target network will only be updated with every second training step (see hyperparameters for details). 

For this training I extended the agent with `n_time_steps=2`, so the target network will update every n steps. To boost the learning at this update stept, I implemented n_learn_updates, to learn multiple times from the current local network.

For more details see [`Continuous Control with Deep Reinforcement Learning`](https://arxiv.org/pdf/1509.02971.pdf)

## State and Action Space

This project uses an adapted [`tennis environment`](https://github.com/Unity-Technologies/ml-agents/blob/master/docs/Learning-Environment-Examples.md#tennis) from unity.

In this environment, two agents control rackets to bounce a ball over a net. If an agent hits the ball over the net, it receives a reward of +0.1. If an agent lets a ball hit the ground or hits the ball out of bounds, it receives a reward of -0.01. Thus, the goal of each agent is to keep the ball in play.

The observation space consists of 8 variables corresponding to the position and velocity of the ball and racket. Each agent receives its own, local observation. Two continuous actions are available, corresponding to movement toward (or away from) the net, and jumping.

The task is episodic, and in order to solve the environment, your agents must get an average score of +0.5 (over 100 consecutive episodes, after taking the maximum over both agents). Specifically,

* Set-up: Two-player game where agents control rackets to bounce ball over a net.
* Goal: The agents must bounce ball between one another while not dropping or sending ball out of bounds.
* Agents: The environment contains two agent linked to a single Brain named TennisBrain. After training you can attach another Brain named MyBrain to one of the agent to play against your trained model.
* Agent Reward Function (independent):
    * +0.1 To agent when hitting ball over net.
    * -0.1 To agent who let ball hit their ground, or hit ball out of bounds.
* Brains: One Brain with the following observation/action space.
* Vector Observation space: 8 variables corresponding to position and velocity of ball and racket.
* Vector Action space: (Continuous) Size of 2, corresponding to movement toward net or away from net, and jumping.
* Visual Observations: None.
* Reset Parameters: One, corresponding to size of ball.
* Benchmark Mean Reward: 2.5
* Optional Imitation Learning scene: TennisIL.

## Learning algorithm

The program is structured in the following way:

- `Continuous_Control.ipynb` - Notebook with additional information about the program structure
- `ddpg_agent.py` - There the Agent class is defined, which will be used in the notebook
- `ddpg_model.py` - Defines the DQN neural network for local and target network
- `README.md` - Instructions how to setup this repository and start the agent
- `Report.md` - This file
- `rewards_plot.png` - Plot of the rewards per episode for the best training
- `solved_model_weights.pth` - Saved model weights (pytorch)
- `unity-environment.log` - wasn't me. autogenerated file from unity environment


### Basic setup of the environment

The base function for `ddpg` was copied from my former project `udacity_drlnd_p2` to get the main loops running. I changed the environment setup according to my 2nd project. This code already had an implementation to use more than one agent - depending on the number of agents the environment provides. 

## Hyper Parameters  

### Agent

buffer_size=int(1e6)   # replay buffer size (default: int(1e6))
batch_size=1024        # minibatch size (default: 128)
gamma=0.98             # discount factor (default: 0.99)
tau=1e-3               # for soft update of target parameters (default: 1e-3)
lr_actor=1e-4          # learning rate of the actor (default: 1e-3)
lr_critic=1e-5         # learning rate of the critic (default: 1e-4)
weight_decay=0.        # L2 weight decay (default: 3e-4)
n_time_steps=2         # 2 only learn every n time steps
n_learn_updates=6      # 5 when learning, boost the learning n times


### OU Noise

mu=0.                 # mean reversion level (default: 0.)
theta=0.00015         # mean reversion speed oder mean reversion rate (default: 0.15)
sigma=0.0002          # random factor influence (sigma: 0.2)
source: [`Wikipedia`](https://de.wikipedia.org/wiki/Ornstein-Uhlenbeck-Prozess)

### NN Model

* `Actor` contains 2 fully connected layers (256, 128) with leaky relu activations.
* `Critic` contains 3 fully connected layers (256, 256, 128) with leaky relu activations. The network builds a critic (value) network that maps (state, action) pairs -> Q-values. See Code `ddpg_model.py --> class Critic(nn.Module)` for more details.

### Search method for Hyper Parameters

First I started with the same values as from my former project - there seemed no learning at all. So I played around with OUNoise (`MU`,`THETA`, `SIGMA`). Reducing the parameters seemed to have a positive effect. After a few empirical tests, I could not get any further improvement.

But the learning was too slow, so I implemented some kind of learning boost (`N_LEARN_UPDATE`). Setting this parameter between 5 and 6 had an positive effect to learning. Setting it to 12 and above had a negative effect and no learning took place anymore. Setting `n_time_steps` to 6 had a negative effect, so I left the parameter untouched at 2.

Raising the learning rate of the networks `LR_ACTOR` and `LR_CRITIC`had an negative effekt, so I reduced the learning rate below the default value. Because the LR seemed verly low, I reduced the `weight_decay` corresponding to the learning rates as well.
The learning startet, but it stalled around 800 episodes. I finally disabled `weight_decay` completely

After this I reduced the `batch_size` to 256, 512, 1024 and 2048. With higher values the learning slowed down extremely. I think this is because the neural network won't be able to train the outliers. So I reduced the batch size more and stopped at 256 because the learning stalled again. I kept 512.

Then I tested a few parameters for the learn rates (`LR_ACTOR` and `LR_CRITIC`). I testet the following setup (1e-4/1e-5), (1e-3/1e-4) and (1e-3/1e-3). (1e-3/1e-3) looked promising, so I stopped.

Setting `gamma` to 0.99 made the learning worse. So I tried reducing it to 0.95. Finally gamma 0.98 seemed to work well for me.

I've included a few (not all of them) plots into `./figures/`. For later manual testing, I've inluded model weights from different episodes. I want to manually compare them.


## Performance plot

See: `results_plot.png` included in this repository.

```
...
Episode 1349	Timestep 361	Score: 0.90	min: 0.90	max: 0.90
Episode 1349	Timestep 362	Score: 0.90	min: 0.90	max: 0.90
Episode 1349	Timestep 363	Score: 0.90	min: 0.90	max: 0.90
Episode 1349	Timestep 364	Score: 0.90	min: 0.90	max: 0.90
Episode 1349	Timestep 365	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 366	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 367	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 368	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 369	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 371	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 372	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 373	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 374	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 375	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 376	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 377	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 378	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 379	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 381	Score: 0.95	min: 0.90	max: 1.00
Episode 1349	Timestep 382	Score: 0.95	min: 0.89	max: 1.00
Episode 1349	Average Score: 0.50	Score: 0.95
Environment solved in 1249 episodes!	Average Score: 0.50
...
```

## Ideas for Future Work
* Reduce the layers of the critic network to see if it will learn faster (and still be stable in training)
* Implement a grid search algorithm to find better combinations of hyper parameters
* CPU and GPU usage is around 30% - find a way to utilize 100% of the hardware
* Use [`Stable Baselines`](https://github.com/hill-a/stable-baselines) based on OpenAI to compare different algorithms
* check the saved models in `models` in real play, to see if there is a difference (overfitting)?