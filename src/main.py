from src.board import Board
from src.player import Human,ArtificialRetardation

def main():
   env = Board()
   player1 = Human("Test Subject", "human")
   player2 = ArtificialRetardation("Neural Nutjob", "nn")
   players = player1, player2
   model = DQN.load('DQNAgent', env=env)
   # Make two turns per step; 1/Player
   done = False
   observation = env.reset()
   while not done:
      action, _states = model.predict(observation, deterministic=True)
      observation, _, _ , done, _ = env.step(action,players)
      #env.render()
      #env.update()

if __name__ == "__main__":
   main()