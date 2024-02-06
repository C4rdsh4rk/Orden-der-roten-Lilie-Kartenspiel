from src.game import Game

#from gym import Env
#from gym.spaces import Discrete, Box, Dict, Tuple, MultiBinary, MultiDiscrete 
#import numpy as np
#import random
import os

from stable_baselines3 import PPO,DQN
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_checker import check_env

def main():
    log_path = os.path.join('Training', 'Logs')
    env = Game(True)
    check_env(env, warn=True)
    '''
    while(True):
        episodes=input(f"How many games should be played before training?")
        episodes=int(episodes)
        if isinstance(episodes,int) and episodes>0:
            break
        else:
            print(f"Wrong input, try again")
    '''
    episodes = 50000
    for episode in range(1, episodes+1):
        done = False
        score = 0 
        while not done:
            #env.render()
            action = env.action_space.sample()
            observation, reward, truncated , done, info = env.step(action)
        #print(f"Episode:{episode} Score:{reward}")
        observation = env.reset()

    model = DQN("MlpPolicy", env, verbose=1, tensorboard_log=log_path) # alias of DQNPolicy # PPO
    model.learn(total_timesteps=10000)
    model.save('PPO')
    evaluate_policy(model, env, n_eval_episodes=1000, render=False)

if __name__ == "__main__":
    main()