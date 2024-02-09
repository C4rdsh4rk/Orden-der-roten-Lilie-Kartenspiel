# third party imports
from gymnasium import Env, spaces
import numpy as np
# local imports
from src.player import Human,ArtificialRetardation
from src.board import Board

class game_controller(Env):
    def __init__(self):
        super().__init__()
        # Define action and observation space
        self.action_space = spaces.Discrete(40)  # Example: two possible actions - 0 or 1
        self.observation_space = spaces.Box(low=0, high=50, dtype=np.float32)
        # Initialize state
        self._state = None
        self.players = ArtificialRetardation("Trained Monkey"), ArtificialRetardation("Clueless Robot") 
        self.board = Board()

    def step(self, action):
        info = {}
        card_index = 
        self.board.play_card(player, card_index, row) # (bool, card_index -> int, row (Enum))
        truncated = False
        done = self.board.update_board()
        observation = self.board.get_state()
        reward = self.get_reward(self.players[0])
        return observation, reward, truncated , done, info

    def reset(self,seed=None):
        # Reset the environment to its initial state
        self._state = self.board.get_state()
        self.board.reset()
        return self._state

    def render(self, mode='human'):
        pass  # Render the environment for visualization

    def get_reward(self, player):
        """Calculates and returns the reward for a given player's actions.

        Args:
            player (Player): The player for whom to calculate the reward.

        Returns:
            float: The calculated reward based on the player's performance and actions.
        """

        # player.reward+=player.turn_score + player.rounds_won*10 # V1
        reward = 0
        win_reward = 10

        # Reward for winning a round
        if player.rounds_won > 0:
            reward += win_reward * (self.player_states[player] - self.player_states[""])

        # Incremental rewards for positive actions
        # For example, playing a card that increases the player's score or strategically passing
        reward += 1 * player.turn_score

        if self.player_states["top_player"]["passed"]:
            reward += 1 + (self.turn_score2 - self.turn_score1)

        player.reward = reward
        return player.reward