# third party imports
from itertools import chain
import random
import numpy as np
from gymnasium import Env, spaces

# local imports
from src.player import Human,ArtificialRetardation
from src.board import Board, Row
from src.display import CardTable

class Game_Controller(Env):
    """A gym-like environment that simulates a card game between two players.
    
    The game is played on a board with 4 rows and a hand of 10 cards for each player. The objective is to score points by playing cards in a specific order, combining their elements. Actions are performed by playing cards from the hand, which are removed from the hand after being used. The game ends when all cards have been played or a certain number of rounds has been won.
    
    Attributes:
        action_space (gym.spaces.Discrete): The space of possible actions, represented as an integer index corresponding to a card in the player's hand.
        observation_space (gym.spaces.Box): The space of possible observations, representing the state of the game board and players' hands."""

    def __init__(self, training = False):
        """Initialize the environment with a random seed and initial state."""

        super().__init__()
        self.display = CardTable()
        # Define action and observation space
        self.action_space = spaces.Discrete(40)  # Example: two possible actions - 0 or 1
        self.observation_space = spaces.Box(low=0, high=50, dtype=np.float32)
        # Initialize state
        self._state = None
        self.done = False
        self.coin_flip = self.get_coin_flip()
        self.turn_indicator = self.coin_flip
        if training:
            self.players =  [
                ArtificialRetardation("Trained Monkey"),
                ArtificialRetardation("Clueless Robot")
                ]
        else:
            self.display.start_render()
            self.players =  [
                ArtificialRetardation("Clueless Robot"),
                Human("IQ Test Subject", self.display.ask_prompt)
            ]
        if not self.coin_flip:
            self.players.reverse()

        self.board = Board(self.players[0].name, self.players[1].name)
        self.rewards = {
            True : 0,
            False : 0
            }

    def step(self, action):
        """Update the environment based on the provided action and return the new observation, reward, etc.
    
        Args:
            action (int): The index of the card to play.
            
        Returns:
            tuple: A tuple containing the new observation, 
            the reward obtained by the player, 
            a boolean indicating if the episode has been truncated, 
            a boolean indicating whether the episode has ended, 
            and a dictionary with additional information."""

        info = {}
        # Note: if conflip, human begins
        bottom_player = self.coin_flip

        for player in self.players:
            # we have already passed
            if self.board.has_passed(bottom_player):
                continue

            card_index = player.make_choice(self.board.get_valid_choices(bottom_player),
                                            action=action)
            # we are passing this turn
            if card_index == 0:
                self.board.pass_round(bottom_player)
                continue
            card_index - 1
            # otherwise play card
            played_card = self.board.get_hand(bottom_player)[card_index]
            played_row = played_card.type
            if played_row == Row.ANY:
                played_row = player.make_row_choice(played_card, [Row.FRONT, Row.WISE, Row.SUPPORT])
            self.board.play_card(bottom_player, card_index, played_row) # (bool, card_index -> int, row (Enum))
            # switch player for next turn
            bottom_player = not bottom_player
        if self.board.has_passed(True) and self.board.has_passed(False):
            self.board.end_round()

        truncated = False
        self.done = self.board.game_ended()
        observation = self.get_state()
        reward = 0 #self.get_reward(player)

        return observation, reward, truncated , self.done, info

    def reset(self, seed=None, options=None):
        """Reset the environment to its initial state and returns the starting observation.
        
        Args:
            seed (int, optional): Seed for randomizing the board. Defaults to None.
        
        Returns:
            np.array: The starting observation.
        """
        # Reset the environment to its initial state
        super().reset(seed=seed)
        info = {}
        self.board.reset()
        self._state = self.get_state()
        return self._state, info

    def render(self, mode='human'):
        """Render the environment for visualization."""
        # Render the environment for visualization
        bottom_player = self.coin_flip
        for player in self.players:
            self.display.update_card_hand(
                self.board.get_hand(bottom_player),
                 bottom_player
            )
            self.display.set_player_cards(
                list(self.board.get_half_board(bottom_player).items()),
                bottom_player
            )
            self.display.set_player_info(
                self.board.get_player_name(bottom_player),
                len(self.board.get_deck(bottom_player)),
                len(self.board.get_graveyard(bottom_player)),
                "NOT IMPLEMENTED :(",
                self.board.get_won_rows()[int(bottom_player)],
                self.board.get_rounds_won(bottom_player),
                bottom_player
            )
            bottom_player = not bottom_player

    def get_state(self): # AR will always be player flag False
        """Return the current state of the environment.
    
        Returns:
        np.array: The current state of the environment as a vector."""

        # Board 76 * 3 +
        # Hand 38 * 3 +
        # Graveyard 38 * 3 +
        # turn score 6 +
        # rounds won 2 +
        # current round 1
        # = 465

        state = np.zeros((465,))

        top_board = np.array(list(chain(*list(self.board.player_states["top_player"]["half_board"].values())))).flatten() # TODO implement get method
        bot_board = np.array(list(chain(*list(self.board.player_states["bottom_player"]["half_board"].values())))).flatten()
        hand = np.array(self.board.get_hand(False)).flatten()
        row_scores = np.array(
            [score for row, score in self.board.get_row_scores(True).items()]+
            [score for row, score in self.board.get_row_scores(False).items()]
        )
        #graveyard = np.concatenate(self.board.get_graveyard(False).flatten())
        """skip = 0
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

        state[-3] = self.board.round_number             # 462
        state[-2] = self.board.get_rounds_won(True)     # 463
        state[-1] = self.board.get_rounds_won(False)    # 464

        self._state = state"""
        return self._state

    def get_reward(self, player):
        """Calculates and returns the reward for a given player's actions.

        Args:
            player (boolean): The player for whom to calculate the reward.

        Returns:
            float: The calculated reward based on the player's performance and actions.
        """

        # player.reward+=player.turn_score + player.rounds_won*10 # V1
        reward = 0
        win_reward = 10

        # Reward for winning a round
        if self.board.player_states[player]["rounds_won"] > 0:
            reward += win_reward * (self.board.player_states[player]["rounds_won"]
                                    - self.board.player_states[not player]["rounds_won"])

        # Incremental rewards for positive actions
        # For example, playing a card that increases the player's score or strategically passing
        reward += 1 * player.turn_score

        if self.board.player_states[not player]["passed"]:
            reward += 2 + (self.board.player_states[player]["current_rows_won"]
                           - self.board.player_states[not player]["current_rows_won"])

        self.rewards[player] = reward
        return self.rewards[player]

    def get_coin_flip(self):
        """Determine whether the first player starts by coin flip (True) or fixed order (False).
    
        Returns:
        bool: True if the coin flip determines the starting player, False otherwise."""
        return bool(random.getrandbits(1))

    def close(self):
        self.display.stop_render()
    
