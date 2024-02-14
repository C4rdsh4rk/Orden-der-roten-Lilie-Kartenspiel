# third party imports
import gymnasium as gym
import torch.nn as nn
import torch as th
from typing import Callable
import numpy as np
#from gymnasium.wrappers import RewardWrapper
from stable_baselines3.common.torch_layers import BaseFeaturesExtractor
from stable_baselines3.common.callbacks import BaseCallback
########################################################################################
# Evolutionary training
def mutate(params: dict[str, th.Tensor]) -> dict[str, th.Tensor]:
    """Mutate parameters by adding normal noise to them"""
    return dict((name, param + th.randn_like(param)) for name, param in params.items())
########################################################################################
# Learning rate schedule
def linear_schedule(initial_value: float) -> Callable[[float], float]:
    """
    Linear learning rate schedule.

    :param initial_value: Initial learning rate.
    :return: schedule that computes
      current learning rate depending on remaining progress
    """
    def func(progress_remaining: float) -> float:
        """
        Progress will decrease from 1 (beginning) to 0.

        :param progress_remaining:
        :return: current learning rate
        """
        return progress_remaining * initial_value

    return func
######################################################################################
class SaveOnBestTrainingRewardCallback(BaseCallback):
    """
    Callback for saving a model (the check is done every ``check_freq`` steps)
    based on the training reward (in practice, we recommend using ``EvalCallback``).

    :param check_freq: (int)
    :param log_dir: (str) Path to the folder where the model will be saved.
      It must contains the file created by the ``Monitor`` wrapper.
    :param verbose: (int)
    """

    def __init__(self, check_freq: int, log_dir: str, save_dir: str, verbose=1):
        super().__init__(verbose)
        self.check_freq = check_freq
        self.log_dir = log_dir
        self.save_path = os.path.join(log_dir, "best_model")
        self.best_mean_reward = -np.inf

    def _init_callback(self) -> None:
        # Create folder if needed
        if self.save_path is not None:
            os.makedirs(self.save_path, exist_ok=True)

    def _on_step(self) -> bool:
        if self.n_calls % self.check_freq == 0:

            # Retrieve training reward
            x, y = ts2xy(load_results(self.log_dir), "timesteps")
            if len(x) > 0:
                # Mean training reward over the last 100 episodes
                mean_reward = np.mean(y[-100:])
                if self.verbose > 0:
                    print(f"Num timesteps: {self.num_timesteps}")
                    print(
                        f"Best mean reward: {self.best_mean_reward:.2f} - Last mean reward per episode: {mean_reward:.2f}"
                    )

                # New best model, you could save the agent here
                if mean_reward > self.best_mean_reward:
                    self.best_mean_reward = mean_reward
                    # Example for saving best model
                    if self.verbose > 0:
                        print(f"Saving new best model to {self.save_path}.zip")
                    self.model.save(self.save_path)

        return True

'''
######################################################################################
class DuelingQRDQNFeaturesExtractor(BaseFeaturesExtractor):
    def __init__(self, observation_space, features_dim=256):
        super(DuelingQRDQNFeaturesExtractor, self).__init__(observation_space, features_dim)
        # Assuming observations are flat vectors
        self.fc = nn.Sequential(nn.Linear(observation_space.shape[0], features_dim),
                                nn.ReLU(),
                                nn.Linear(features_dim, features_dim),
                                nn.ReLU())

        self.value_stream = nn.Sequential(nn.Linear(features_dim, features_dim),
                                          nn.ReLU(),
                                          nn.Linear(features_dim, 1))

        self.advantage_stream = nn.Sequential(nn.Linear(features_dim, features_dim),
                                              nn.ReLU(),
                                              nn.Linear(features_dim, observation_space.n))

    def forward(self, observations):
        features = self.fc(observations)
        values = self.value_stream(features)
        advantages = self.advantage_stream(features)
        q_vals = values + (advantages - advantages.mean(dim=1, keepdim=True))
        return q_vals
######################################################################################    
class CustomQRDQNNetwork(nn.Module):
    def __init__(self, input_dim, output_dim):
        super(CustomQRDQNNetwork, self).__init__()
        self.network = nn.Sequential(
            nn.Linear(input_dim, 128),
            nn.ReLU(),
            nn.Linear(128, 256),
            nn.ReLU(),
            nn.Dropout(0.2),
            nn.Linear(256, output_dim)
        )

    def forward(self, x):
        return self.network(x)
######################################################################################    
class EpsilonGreedyStrategy:
    def __init__(self, epsilon_start, epsilon_end, epsilon_decay):
        self.current_step = 0
        self.epsilon_start = epsilon_start
        self.epsilon_end = epsilon_end
        self.epsilon_decay = epsilon_decay

    def get_exploration_rate(self):
        exploration_rate = self.epsilon_end + \
            (self.epsilon_start - self.epsilon_end) * \
            np.exp(-1. * self.current_step / self.epsilon_decay)
        self.current_step += 1
        return exploration_rate
######################################################################################'''
# Reward shaper
#class CustomRewardShaping(RewardWrapper): # NOTE: Wrapper import Error
#    def reward(self, reward):
#        # Example: Increase the reward for a certain condition
#        if reward > 0:
#            return reward * 2  # Double the reward for positive outcomes
#        return reward
######################################################################################'''
#class StateNormalizer:
#    '''State normalizer for get state in game controller'''
#    def __init__(self, environment):
#        self.low = environment.observation_space.low
#        self.high = environment.observation_space.high#
#
#    def normalize(self, state):
#        # Normalize to [0, 1]
#        normalized_state = (state - self.low) / (self.high - self.low)
#        return normalized_state
######################################################################################
