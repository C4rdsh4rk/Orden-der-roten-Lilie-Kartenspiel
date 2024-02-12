# third party imports
import os
import time
import torch as th
import gymnasium as gym
import numpy as np
from sb3_contrib import QRDQN
from typing import Dict
from stable_baselines3 import PPO, DQN, A2C
from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.logger import configure
# local imports
from src.game_controller import Game_Controller
from src.utils import get_path, get_int, get_index, get_bool, get_choice, get_user_input

def mutate(params: dict[str, th.Tensor]) -> dict[str, th.Tensor]:
    """Mutate parameters by adding normal noise to them"""
    return dict((name, param + th.randn_like(param)) for name, param in params.items())

def main():
   index = get_index("Do you want to play , simulate or train a network? ",
                  ['play','simulate [not implemented]','train'])

   if index == 0:
      env = Game_Controller()
      # Load the trained agent
      # NOTE: if you have loading issue, you can pass `print_system_info=True`
      # to compare the system on which the model was trained vs the current one
      model = QRDQN.load(get_path("Which network should be loaded?", "Choose a zip file",["*.zip"]),
                           env=env, print_system_info=True)
      observation, _ = env.reset()
      env.render()
      while not env.done:
         action, _states = model.predict(observation, deterministic=True)
         action = action.item()  # cast 0 dim array containing int
         observation, reward, truncates, done, info = env.step(action)
         env.render()
      env.close()
   elif index == 1:
      raise NotImplementedError
   else:
      env = Game_Controller(True)
      observation, _ = env.reset()
      check_env(env, warn=True)
      observation, _ = env.reset()

      # set up logger
      log_path = os.path.join('logs', 'training')
      new_logger = configure(log_path, ["stdout", "tensorboard"])

      if get_bool("Train a new network or continue training?",["Train new","Continue training"]):
         timesteps = get_int("How many timesteps should be made for the first training?", 0, 5000000)
         lr_choice = get_choice("Which learnrate should be used?",[0.1, 0.05, 0.005, 0.0005, 0.0001, 0.00005])
         lr_choice = float(lr_choice)
         train_index = get_index("In what interval should the networks weights be adjusted?",
                                      ["1,episode","2,episode","3,episode","4,episode","1, step","2, step","3, step","4, step"])
         frequencies = [(1,"episode"),(2,"episode"),(3,"episode"),(4,"episode"),(1, "step"),(2, "step"),(3, "step"),(4, "step")]
         model = QRDQN("MlpPolicy",
                        env,
                        learning_rate=lr_choice,
                        buffer_size=1000000,
                        learning_starts=100,
                        batch_size=32,
                        tau=1.0,
                        gamma=0.99,
                        train_freq=frequencies[train_index],
                        gradient_steps=1,
                        replay_buffer_class=None,
                        replay_buffer_kwargs=None,
                        optimize_memory_usage=False,
                        target_update_interval=10000,
                        exploration_fraction=0.1,
                        exploration_initial_eps=1.0,
                        exploration_final_eps=0.05,
                        max_grad_norm=10,
                        stats_window_size=100,
                        tensorboard_log=None,
                        policy_kwargs=None,
                        verbose=1,
                        seed=None,
                        device='auto',
                        _init_setup_model=True)
         # Set new logger
         model.set_logger(new_logger)
         # Use traditional actor-critic policy gradient updates to
         # find good initial parameters
         model.learn(total_timesteps=timesteps)
         model.save('QRDQNAgent_DUMB')
         model.save_replay_buffer("QRDQNAgent_DUMB_replay")
         mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10, render=False)
      else:
         model = QRDQN.load(get_path("Which network should be loaded?", "Choose a zip file",["*.zip"]), env=env, print_system_info=True)
         model.load_replay_buffer(get_path("Which replay buffer should be loaded?", "Choose a pkl file",["*.pkl"]))
         mean_reward, std_reward = evaluate_policy(model, env, n_eval_episodes=10, render=False)

      # Include only variables with "policy", "action" (policy) or "shared_net" (shared layers)
      # in their name: only these ones affect the action.
      # NOTE: you can retrieve those parameters using model.get_parameters() too
      mean_params = dict(
      (key, value)
      for key, value in model.policy.state_dict().items()
      if ("policy" in key or "shared_net" in key or "action" in key)
      )

      ## START EVOLUTIONARY TRAINING
      pop_size = get_int("How big should the population be?",10) # Population size
      # Keep top 10%
      n_elite = pop_size // 10 # Elite size (the best networks in this 10% will be kept until replaced by better ones)
      # Retrieve the environment
      vec_env = model.get_env()
      prior_mean_champion_fitness = mean_reward
      prior_std_champion_fitness = std_reward
      for iteration in range(get_int("How many iterations?")):
         # Create population of candidates and evaluate them
         population = []
         for population_i in range(pop_size):
               candidate = mutate(mean_params)
               # Load new policy parameters to agent.
               # Tell function that it should only update parameters
               # we give it (policy parameters)
               model.policy.load_state_dict(candidate, strict=False)
               # Evaluate the candidate
               fitness, _ = evaluate_policy(model, vec_env, n_eval_episodes=10, render=False)
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
         print(f"Best fitness this iteration: {top_candidates[0][1]:.2f} vs Champion: {prior_mean_champion_fitness:.2f}")
         if top_candidates[0][1] > prior_mean_champion_fitness:
            #model.policy.load_state_dict(top_candidates[0][0], strict=False)
            #mean_reward, std_reward = evaluate_policy(model, vec_env, n_eval_episodes=10, render=False)
            #if mean_reward > prior_mean_champion_fitness: #and std_reward > prior_std_champion_fitness:
            print("Saving new Champion")
            name = "QRDQN_Agent_" + str(round(prior_mean_champion_fitness))
            prior_mean_champion_fitness = top_candidates[0][1]
            champion = top_candidates[0][0]
            model.policy.load_state_dict(champion, strict=False)
            model.save_replay_buffer(name)
            model.save(name)
            time.sleep(1)

      # Save the policy independently from the model
      # Note: if you don't save the complete model with `model.save()`
      # you cannot continue training afterward
      policy = model.policy
      policy.save("Champion_Policy")
      print("Finished Training")

if __name__ == "__main__":
   main()