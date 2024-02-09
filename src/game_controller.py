# third party imports
import random
import numpy as np
from gymnasium import Env, spaces

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
        self.coin_flip = self.get_coin_flip()
        self.players = ArtificialRetardation("Trained Monkey"), ArtificialRetardation("Clueless Robot") 
        self.board = Board(self.players[0].name, self.players[1].name)

    def step(self, action):
        info = {}
        player = True

        if self.coin_flip:
            self.board.get_hand(player)
            card_index = action
            self.board.play_card(player, card_index, row) # (bool, card_index -> int, row (Enum))
            player = not player            
            self.board.get_hand(player)
            card_index = action
            self.board.play_card(player, card_index, row) # (bool, card_index -> int, row (Enum))

        else:
            player = not player
            self.board.get_hand(player)
            card_index = action
            self.board.play_card(player, card_index, row) # (bool, card_index -> int, row (Enum))
            player = not player
            self.board.get_hand(player)
            card_index = action
            self.board.play_card(player, card_index, row) # (bool, card_index -> int, row (Enum))



        truncated = False
        done = self.board.update_board()
        observation = self.board.get_state()
        reward = self.get_reward(self.players[0])
        return observation, reward, truncated , done, info

    def reset(self, seed=None, options={}):
        """Reset the environment to its initial state and returns the starting observation.
        
        Args:
            seed (int, optional): Seed for randomizing the board. Defaults to None.
        
        Returns:
            np.array: The starting observation.
        """
        # Reset the environment to its initial state
        super().reset(seed=seed)
        self.board.reset()
        self._state = self.get_state()
        return self._state

    def render(self, mode='human'):
        pass  # Render the environment for visualization

    def get_state(self): # AR will always be player flag False
        state = np.zeros((464,))
        
        top_board = np.array(self.board.player_states["top_player"]["half_board"]).flatten()
        bot_board = np.array(self.board.player_states["bottom_player"]["half_board"]).flatten()
        hand = np.array(self.board.get_hand(False)).flatten()
        row_scores = np.concatenate(self.board.get_row_scores(True).flatten(), self.board.get_row_scores(False).flatten())
        #graveyard = np.concatenate(self.board.get_graveyard(False).flatten())
        skip = 0
        for i,entry in enumerate(bot_board):
            state[i] = entry
        skip += 114 # 38 * card vector of 3
        for i,entry in enumerate(top_board):
            state[i+skip] = entry
        skip += 114
        for i,entry in enumerate(hand):
            state[i+skip] = entry
        skip += 114
        #for i,entry in enumerate(graveyard)):
        #    state[i+skip] = entry
        skip += 114
        for i,entry in enumerate(row_scores):
            state[i+skip] = entry
        
        state[-2] = self.board.get_rounds_won(True) # 462
        state[-1] = self.board.get_rounds_won(False) # 463

        self._state = state
        return self._state # Board 76 * 3 + Hand 38 * 3 + Graveyard 38 * 3 + turn score 6 + rounds won 2 = 464

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
    
    def get_coin_flip(self):
        return bool(random.getrandbits(1))
