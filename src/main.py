# third party imports
#import torch as th

from typing import Dict

import gymnasium as gym
import numpy as np
import torch as th

import os
from stable_baselines3 import PPO, DQN, A2C
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.logger import configure

# local imports
from src.game_controller import Game_Controller
from src.utils import get_user_input


def mutate(params: dict[str, th.Tensor]) -> dict[str, th.Tensor]:
    """Mutate parameters by adding normal noise to them"""
    return dict((name, param + th.randn_like(param)) for name, param in params.items())


def main():
   input = int(get_user_input("Do you want to play [1], simulate [2] or train a network [3]?",['1','2','3']))
   env = Game_Controller()
   if input == 1:
      # Load the trained agent
      # NOTE: if you have loading issue, you can pass `print_system_info=True`
      # to compare the system on which the model was trained vs the current one
      model = DQN.load("DQNAgentEVO", env=env, print_system_info=True)
      observation, _ = env.reset()
      env.render()
      while not env.done:
           action, _states = None, None #  TODO: model.predict gives array not int??? model.predict(observation, deterministic=True)
           observation, reward, truncates, done, info = env.step(action)
           env.render()
      env.close()
   elif int(input) == 2:
      raise NotImplementedError
   else:
      env = Game_Controller(True)
      observation, _ = env.reset()
      check_env(env, warn=True)

      episodes = 1
      observation, _ = env.reset()

      '''for episode in range(1, episodes+1):
         done = False
         score = 0 
         while not done:
               env.render()
               action = env.action_space.sample()
               observation, reward, truncated , done, info = env.step(action)
         print(f"Episode:{episode} Score:{reward}")
         observation = env.reset()'''

      timesteps = 1000#get_user_input("How many timesteps should be made for training?", list(range(1,100000)))
      # set up logger
      log_path = os.path.join('logs', 'training')
      new_logger = configure(log_path, ["stdout", "csv", "tensorboard"])
      '''
      model = DQN("MlpPolicy",
                     env,
                     #ent_coef=0.0,
                     #policy_kwargs={"net_arch": [32]},
                     #seed=0,
                     learning_rate=0.05,
                     verbose=1) #, tensorGame_Controller_log=log_path) # alias of DQNPolicy # PPO
      # Set new logger
      model.set_logger(new_logger)
      # Use traditional actor-critic policy gradient updates to
      # find good initial parameters
      model.learn(total_timesteps=timesteps)
      model.save('DQNAgent')
      evaluate_policy(model, env, n_eval_episodes=1, render=False)'''



      model = DQN.load("DQNAgent_53", env=env, print_system_info=True)
      # Include only variables with "policy", "action" (policy) or "shared_net" (shared layers)
      # in their name: only these ones affect the action.
      # NOTE: you can retrieve those parameters using model.get_parameters() too
      mean_params = dict(
      (key, value)
      for key, value in model.policy.state_dict().items()
      if ("policy" in key or "shared_net" in key or "action" in key)
      )

      ## START EVOLUTIONARY TRAINING

      pop_size = 200 # Population size
      # Keep top 10%
      n_elite = pop_size // 10 # Elite size (the best networks in this 10% will be kept until replaced by better ones)
      # Retrieve the environment
      vec_env = model.get_env()
      prior_champion_fitness = 0
      for iteration in range(500):
         # Create population of candidates and evaluate them
         population = []
         for population_i in range(pop_size):
               candidate = mutate(mean_params)
               # Load new policy parameters to agent.
               # Tell function that it should only update parameters
               # we give it (policy parameters)
               model.policy.load_state_dict(candidate, strict=False)
               # Evaluate the candidate
               fitness, _ = evaluate_policy(model, vec_env)
               population.append((candidate, fitness))
         # Take top 10% and use average over their parameters as next mean parameter
         top_candidates = sorted(population, key=lambda x: x[1], reverse=True)[:n_elite]
         mean_params = dict(
               (
                  name,
                  th.stack([candidate[0][name] for candidate in top_candidates]).mean(dim=0),
               )
               for name in mean_params.keys()
         )
         mean_fitness = sum(top_candidate[1] for top_candidate in top_candidates) / n_elite
         print(f"Iteration {iteration + 1:<3} Mean top fitness: {mean_fitness:.2f}")
         print(f"Best fitness this iteration: {top_candidates[0][1]:.2f} vs Champion: {prior_champion_fitness}")
         if top_candidates[0][1] > prior_champion_fitness:
            print("Saving new Champion")
            prior_champion_fitness = top_candidates[0][1]
            model.policy.load_state_dict(top_candidates[0][0], strict=False)
            model.save_replay_buffer(f"DQNEVO_with_replay_{prior_champion_fitness}")
            model.save(f'DQNAgentEVO_{prior_champion_fitness}')
      print("Finished Training")

if __name__ == "__main__":
   main()