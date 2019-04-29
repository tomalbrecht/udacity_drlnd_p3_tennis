import numpy as np
import random
import copy
from collections import namedtuple, deque

from ddpg_model import Actor, Critic

import torch
import torch.nn.functional as F
import torch.optim as optim

MU = 0.           # mean reversion level (default: 0.)
THETA = 0.05      # mean reversion speed oder mean reversion rate (default: 0.15) --> TODO: 0.05
SIGMA = 0.02      # random factor influence (sigma: 0.2) --> TODO: 0.02

N_TIME_STEPS = 2  # only learn every n time steps

device = torch.device("cuda:0" if torch.cuda.is_available() else "cpu")

class Agent():
    """Interacts with and learns from the environment."""
    
    # class variables, shared information for all agents
    memory = None
    
    actor_local = None
    actor_target = None
    actor_optimizer = None

    critic_local = None
    critic_target = None
    critic_optimizer = None
    
    def __init__(self, 
                 state_size=None, 
                 action_size=None, 
                 random_seed=0,
                 buffer_size=int(1e6),  # replay buffer size
                 batch_size=128,        # minibatch size
                 gamma=0.99,            # discount factor
                 tau=1e-3,              # for soft update of target parameters
                 lr_actor=1e-4,         # learning rate of the actor 
                 lr_critic=1e-3,        # learning rate of the critic
                 weight_decay=0.0001    # L2 weight decay
                ):
        """Initialize an Agent object.
        
        Params
        ======
            state_size (int): dimension of each state
            action_size (int): dimension of each action
            random_seed (int): random seed
        """
        self.state_size = state_size
        self.action_size = action_size
        self.seed = random.seed(random_seed)
        self.buffer_size = buffer_size       # replay buffer size
        self.batch_size = batch_size         # minibatch size
        self.gamma = gamma                   # discount factor
        self.tau = tau                       # for soft update of target parameters
        self.lr_actor = lr_actor             # learning rate of the actor 
        self.lr_critic = lr_critic           # learning rate of the critic
        self.weight_decay = weight_decay     # L2 weight decay

        # initialization for first class instance
        if Agent.actor_local is None:
            Agent.actor_local = Actor(state_size, action_size, random_seed).to(device)
        if Agent.actor_target is None:
            Agent.actor_target = Actor(state_size, action_size, random_seed).to(device)
        if Agent.actor_optimizer is None:
            Agent.actor_optimizer = optim.Adam(Agent.actor_local.parameters(), lr=lr_actor)
        
        # Actor Network (w/ Target Network)
        self.actor_local = Agent.actor_local
        self.actor_target = Agent.actor_target
        self.actor_optimizer = Agent.actor_optimizer

        # initialization for first class instance
        if Agent.critic_local is None:
            Agent.critic_local = Critic(state_size, action_size, random_seed).to(device)
        if Agent.critic_target is None:
            Agent.critic_target = Critic(state_size, action_size, random_seed).to(device)
        if Agent.critic_optimizer is None:
            Agent.critic_optimizer = optim.Adam(Agent.critic_local.parameters(), lr=lr_critic, weight_decay=weight_decay)
        
        # Critic Network (w/ Target Network)
        self.critic_local = Agent.critic_local
        self.critic_target = Agent.critic_target
        self.critic_optimizer = Agent.critic_optimizer

        # Noise process
        self.noise = OUNoise(action_size, random_seed, mu=MU, theta=THETA, sigma=SIGMA)
        #TODO: Maybe self.noise = OUNoise((20, action_size), random_seed)

        # Replay memory
        if Agent.memory is None:
            Agent.memory = ReplayBuffer(action_size, buffer_size, batch_size, random_seed)
    
    def step(self, time_step, state, action, reward, next_state, done):
        """Save experience in replay memory, and use random sample from buffer to learn."""
        # Save experience / reward
        Agent.memory.add(state, action, reward, next_state, done)

        # only learn every n_time_steps
        if time_step % N_TIME_STEPS == 0:
            # Learn, if enough samples are available in memory
            if len(Agent.memory) > self.batch_size:
                experiences = Agent.memory.sample()
                self.learn(experiences, self.gamma)

    def act(self, state, add_noise=True):
        """Returns actions for given state as per current policy."""
        state = torch.from_numpy(state).float().to(device)
        self.actor_local.eval()
        with torch.no_grad():
            action = self.actor_local(state).cpu().data.numpy()
        self.actor_local.train()
        if add_noise:
            action += self.noise.sample()
        return np.clip(action, -1, 1)

    def reset(self):
        self.noise.reset()

    def learn(self, experiences, gamma):
        """Update policy and value parameters using given batch of experience tuples.
        Q_targets = r + É¡ * critic_target(next_state, actor_target(next_state))
        where:
            actor_target(state) -> action
            critic_target(state, action) -> Q-value

        Params
        ======
            experiences (Tuple[torch.Tensor]): tuple of (s, a, r, s', done) tuples 
            gamma (float): discount factor
        """
        states, actions, rewards, next_states, dones = experiences

        # ---------------------------- update critic ---------------------------- #
        # Get predicted next-state actions and Q values from target models
        actions_next = self.actor_target(next_states)
        Q_targets_next = self.critic_target(next_states, actions_next)
        # Compute Q targets for current states (y_i)
        Q_targets = rewards + (gamma * Q_targets_next * (1 - dones))
        # Compute critic loss
        Q_expected = self.critic_local(states, actions)
        critic_loss = F.mse_loss(Q_expected, Q_targets)
        # Minimize the loss
        self.critic_optimizer.zero_grad()
        critic_loss.backward()
        self.critic_optimizer.step()

        # ---------------------------- update actor ---------------------------- #
        # Compute actor loss
        actions_pred = self.actor_local(states)
        actor_loss = -self.critic_local(states, actions_pred).mean()
        # Minimize the loss
        self.actor_optimizer.zero_grad()
        actor_loss.backward()
        self.actor_optimizer.step()

        # ----------------------- update target networks ----------------------- #
        self.soft_update(self.critic_local, self.critic_target, self.tau)
        self.soft_update(self.actor_local, self.actor_target, self.tau)                     

    def soft_update(self, local_model, target_model, tau):
        """Soft update model parameters.
        É∆_target = É—*É∆_local + (1 - É—)*É∆_target

        Params
        ======
            local_model: PyTorch model (weights will be copied from)
            target_model: PyTorch model (weights will be copied to)
            tau (float): interpolation parameter 
        """
        for target_param, local_param in zip(target_model.parameters(), local_model.parameters()):
            target_param.data.copy_(tau*local_param.data + (1.0-tau)*target_param.data)

class OUNoise:
    """Ornstein-Uhlenbeck process."""

    def __init__(self, size, seed, mu=0., theta=0.15, sigma=0.2):
        """Initialize parameters and noise process."""
        self.mu = mu * np.ones(size)
        self.theta = theta
        self.sigma = sigma
        self.seed = random.seed(seed)
        self.reset()

    def reset(self):
        """Reset the internal state (= noise) to mean (mu)."""
        self.state = copy.copy(self.mu)

    def sample(self):
        """Update internal state and return it as a noise sample."""
        x = self.state
        dx = self.theta * (self.mu - x) + self.sigma * np.array([random.random() for i in range(len(x))])
        self.state = x + dx
        return self.state

class ReplayBuffer:
    """Fixed-size buffer to store experience tuples."""

    def __init__(self, action_size, buffer_size, batch_size, seed):
        """Initialize a ReplayBuffer object.
        Params
        ======
            buffer_size (int): maximum size of buffer
            batch_size (int): size of each training batch
        """
        self.action_size = action_size
        self.memory = deque(maxlen=buffer_size)  # internal memory (deque)
        self.batch_size = batch_size
        self.experience = namedtuple("Experience", field_names=["state", "action", "reward", "next_state", "done"])
        self.seed = random.seed(seed)
    
    def add(self, state, action, reward, next_state, done):
        """Add a new experience to memory."""
        e = self.experience(state, action, reward, next_state, done)
        self.memory.append(e)
    
    def sample(self):
        """Randomly sample a batch of experiences from memory."""
        experiences = random.sample(self.memory, k=self.batch_size)

        states = torch.from_numpy(np.vstack([e.state for e in experiences if e is not None])).float().to(device)
        actions = torch.from_numpy(np.vstack([e.action for e in experiences if e is not None])).float().to(device)
        rewards = torch.from_numpy(np.vstack([e.reward for e in experiences if e is not None])).float().to(device)
        next_states = torch.from_numpy(np.vstack([e.next_state for e in experiences if e is not None])).float().to(device)
        dones = torch.from_numpy(np.vstack([e.done for e in experiences if e is not None]).astype(np.uint8)).float().to(device)

        return (states, actions, rewards, next_states, dones)

    def __len__(self):
        """Return the current size of internal memory."""
        return len(self.memory)