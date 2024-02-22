import torch
import numpy as np

class PolicyNetwork(torch.nn.Module):
    def __init__(self, input_shape=(40), output_size=40):  # Update according to your state/action size
        super().__init__()
        self.input_layer = torch.nn.Linear(input_shape, 64)
        self.hidden1 = torch.nn.ReLU()
        self.dropout1 = torch.nn.Dropout(0.2)
        self.hidden2 = torch.nn.Linear(64, 32)
        self.batchnorm = torch.nn.BatchNorm1d(32)
        self.output_layer = torch.nn.Linear(32, output_size)
        self.softmax = torch.nn.Softmax(dim=1)

    def forward(self, state):
        x = self.input_layer(state)
        x = self.hidden1(x)
        x = self.dropout1(x)
        x = self.hidden2(x)
        x = self.batchnorm(x)
        x = self.output_layer(x)
        return self.softmax(x)

class Memory:
    def __init__(self):
        self.states = []
        self.actions = []
        self.rewards = []
        self.next_states = []
        self.dones = []

    def add(self, state, action, reward, next_state, done):
        self.states.append(state)
        self.actions.append(action)
        self.rewards.append(reward)
        self.next_states.append(next_state)
        self.dones.append(done)
    
    def sample(self, batch_size=128):
        states = np.array(self.states[-batch_size:]) # Get a batch of data from memory
        actions = np.array(self.actions[-batch_size:])
        rewards = np.array(self.rewards[-batch_size:])
        next_states = np.array(self.next_states[-batch_size:])
        dones = np.array(self.dones[-batch_size:])
        return states, actions, rewards, next_states, dones


class MCTS(object):
    def __init__(self, state, policy_net, env):
        self.root = Node(state, env, policy_net)
        self.policy_net = policy_net
        self.env = env
        
    def simulate(self):
        node = self.root
        while not node.terminal:
            action = self._select(node)
            child = node.children[action]
            reward, done = child.simulate()
            self._backup(child, reward, done)
            node = child
            
    def get_action_probabilities(self):
        action_visits = [0]*len(self.env.get_valid_actions())
        for i in range(len(self.root.children)):
            action_visits[i] = self.root.children[i].N
        total_visits = sum(action_visits)
        return action_visits / total_visits
        
class Node:
    def __init__(self, state, env, policy_net, parent=None, action=None):
        self.state = torch.from_numpy(state.astype(np.float64))
        self.parent = parent
        self.action = action
        self.children = []
        self.N = 0 # Number of visits
        self.Q = 0 # Value of node
        self.env = env
        self.terminal = self.env.done # Check if it is a terminal state or not
        if not self.terminal:
            action_probs, _states = policy_net(self.state)
            self._expand(action_probs)
            
    def _expand(self, action_probs):
        for i in range(len(self.env.action_space)):
            if self.env.is_valid_action(self.state,i):
                self.children.append(Node(self.env.simulate_action(self.state,i), self, i))
                
    def simulate(self):
        # Get a random action based on the probabilities predicted by policy net
        action = np.random.choice([i for i in range(len(self.children))], p=action_probs)
        reward, done = self.env.simulate_action(self.state, action)
        return reward, done
        
    def _backup(self, child, reward, done):
        self.N += 1
        if not self.terminal:
            self.Q += reward
        if done:
            self._update_ancestors(reward)
            
    def _update_ancestors(self, reward):
        node = self
        while node is not None:
            node.N += 1
            node.Q += reward
            node = node.parent
