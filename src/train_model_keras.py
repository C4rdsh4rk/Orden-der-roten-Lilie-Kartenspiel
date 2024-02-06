from src.game import Game
import tensorflow as tf
from tensorflow.keras.models import Sequential
from tensorflow.keras.layers import Dense, Flatten
from tensorflow.keras.optimizers import Adam
import tensorflow.keras as keras
import numpy as np
from rl.agents import DQNAgent
from rl.policy import BoltzmannQPolicy
from rl.memory import SequentialMemory

def build_model(env):
    model = Sequential()    
    model.add(Dense(24, activation='relu', input_shape=env.observation_space.shape))
    model.add(Dense(24, activation='relu'))
    model.add(Dense(env.action_space.n, activation='linear'))
    return model

def build_agent(model, actions):
    policy = BoltzmannQPolicy()
    memory = SequentialMemory(limit=50000, window_length=1)
    dqn = DQNAgent(model=model, memory=memory, policy=policy, 
                  nb_actions=actions, nb_steps_warmup=10, target_model_update=1e-2)
    return dqn

def main():
    env = Game(True)
    while(True):
        episodes=input(f"How many games should be played for training?")
        episodes=int(episodes)
        if isinstance(episodes,int) and episodes>0:
            break
        else:
            print(f"Wrong input, try again")
    
    for episode in range(1, episodes+1):
        done = False
        score = 0 
        while not done:
            #env.render()
            action = env.action_space.sample()
            observation, reward, done, info = env.step(action)
        print(f"Episode:{episode} Score:{reward}")
        observation = env.reset()
    NN_architecture = build_model(env)
    NN_architecture.summary()
    
    neural_nutjob = build_agent(NN_architecture, env.action_space.n)
    print(f"Agent build")
    neural_nutjob.compile(optimizer=Adam(learning_rate=0.001), metrics=[keras.metrics.Accuracy()])
    print(f"Model compiled")
    print(f"{env.observation_space.shape}")
    print(f"Starting fitting...")
    neural_nutjob.fit(env, nb_steps=10, visualize=False, verbose=1)
    print(f"Finished fitting...")
    _ = neural_nutjob.test(env, nb_episodes=2, visualize=True)
    print(f"Finished test and saving weights!")
    neural_nutjob.save_weights('dqn_weights.h5f', overwrite=True)

if __name__ == "__main__":
    main()


