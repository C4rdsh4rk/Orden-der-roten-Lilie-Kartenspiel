# third party imports
import torch as th
import os
from stable_baselines3 import PPO,DQN
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.logger import configure
# local imports
from src.game_controller import Game_Controller

def main():
   env = Game_Controller()
   observation, _ = env.reset()
   check_env(env, warn=True)

   episodes = 10
   observation, _ = env.reset()
   for episode in range(1, episodes+1):
      done = False
      score = 0 
      while not done:
            env.render()
            action = env.action_space.sample()
            observation, reward, truncated , done, info = env.step(action)
      print(f"Episode:{episode} Score:{reward}")
      observation = env.reset()



if __name__ == "__main__":
   main()