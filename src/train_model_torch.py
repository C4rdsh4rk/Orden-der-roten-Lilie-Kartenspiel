from typing import Dict
import gymnasium as gym


from src.game_controller import Game_Controller

def mutate(params: Dict[str, th.Tensor]) -> Dict[str, th.Tensor]:
    """Mutate parameters by adding normal noise to them"""
    return dict((name, param + th.randn_like(param)) for name, param in params.items())

def main():
    log_path = os.path.join('Training', 'Logs')
    env = Game_Controller()
    check_env(env, warn=True)

    episodes = 10

    observation, _ = env.reset()
    for episode in range(1, episodes+1):
        done = False
        score = 0 
        while not done:
            #env.render()
            action = env.action_space.sample()
            observation, reward, truncated , done, info = env.step(action)
        print(f"Episode:{episode} Score:{reward}")
        observation = env.reset()

    # set up logger
    new_logger = configure(log_path, ["stdout", "csv", "tensorGame_Controller"])

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
    model.learn(total_timesteps=1000)
    model.save('DQNAgent')
    evaluate_policy(model, env, n_eval_episodes=10, render=False)

    # Include only variables with "policy", "action" (policy) or "shared_net" (shared layers)
    # in their name: only these ones affect the action.
    # NOTE: you can retrieve those parameters using model.get_parameters() too
    mean_params = dict(
    (key, value)
    for key, value in model.policy.state_dict().items()
    if ("policy" in key or "shared_net" in key or "action" in key)
    )

    ## START EVOLUTIONARY TRAINING

    pop_size = 10 # Population size
    # Keep top 10%
    n_elite = pop_size // 10 # Elite size (the best networks in this 10% will be kept until replaced by better ones)
    # Retrieve the environment
    vec_env = model.get_env()

    for iteration in range(10):
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
        print(f"Best fitness: {top_candidates[0][1]:.2f}")
    model.save_replay_buffer("DQN_with_replay")
    model.save('DQNAgent')

if __name__ == "__main__":
    main()