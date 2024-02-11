# third party imports
import time
import torch as th
import os
from sb3_contrib import QRDQN
#from stable_baselines3 import PPO, DQN, A2C
#from stable_baselines3.common.vec_env import VecFrameStack
from stable_baselines3.common.evaluation import evaluate_policy
from stable_baselines3.common.env_checker import check_env
from stable_baselines3.common.logger import configure

# local imports
from src.utils import get_path, get_int, get_bool



def mutate(params: dict[str, th.Tensor]) -> dict[str, th.Tensor]:
    """Mutate parameters by adding normal noise to them"""
    return dict((name, param + th.randn_like(param)) for name, param in params.items())

def training(env):
    observation, _ = env.reset()

    # set up logger
    log_path = os.path.join('logs', 'training')
    new_logger = configure(log_path, ["stdout", "csv", "tensorboard"])
    
    
    if get_bool("Train a new network or continue training?",["Train new","Continue training"]):
        timesteps = get_int("How many timesteps should be made for the first training?")
        model = QRDQN("MlpPolicy",
                        env,
                        #ent_coef=0.0,
                        #policy_kwargs={"net_arch": [32]},
                        #seed=0,
                        train_freq=(1,"episode"), #Update the model every train_freq steps. Alternatively pass a tuple of frequency and unit like (5, "step") or (2, "episode").
                        learning_rate=0.05,
                        tensorboard_log=new_logger,
                        verbose=1) #, tensorGame_Controller_log=log_path) # alias of DQNPolicy # PPO
        # Set new logger
        model.set_logger(new_logger)
        # Use traditional actor-critic policy gradient updates to
        # find good initial parameters
        model.learn(total_timesteps=timesteps)
        model.save('QRDQNAgent_DUMB')
        evaluate_policy(model, env, n_eval_episodes=1, render=False)
    else:
        model = QRDQN.load(get_path("Which network should be loaded?"), env=env, print_system_info=True)
        model.load_replay_buffer(get_path("Which replay buffer should be loaded?"))

    # Include only variables with "policy", "action" (policy) or "shared_net" (shared layers)
    # in their name: only these ones affect the action.
    # NOTE: you can retrieve those parameters using model.get_parameters() too
    mean_params = dict(
    (key, value)
    for key, value in model.policy.state_dict().items()
    if ("policy" in key or "shared_net" in key or "action" in key)
    )

    ## START EVOLUTIONARY TRAINING
    pop_size = get_int("How big should the population be?") # Population size
    # Keep top 10%
    n_elite = pop_size // 10 # Elite size (the best networks in this 10% will be kept until replaced by better ones)
    # Retrieve the environment
    vec_env = model.get_env()
    prior_champion_fitness = 0
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
            champion = top_candidates[0][0]
            model.policy.load_state_dict(champion, strict=False)
            model.save_replay_buffer("QRDQNEVO_replay")
            name = "QRDQN_Agent_" + str(round(prior_champion_fitness))
            model.save(name)
            time.sleep(1)
    # Save the policy independently from the model
    # Note: if you don't save the complete model with `model.save()`
    # you cannot continue training afterward
    policy = model.policy
    policy.save("Champion_Policy")
    print("Finished Training")