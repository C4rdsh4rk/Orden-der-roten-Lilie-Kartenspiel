# third party imports
from itertools import chain
import random
import numpy as np
from gymnasium import Env, spaces
import logging
import time
# local imports
from src.player import Human,ArtificialRetardation
from src.board import Board, Row
from src.display import CardTable
from src.cards import Booster


class Game_Controller(Env):
    """A gym-like environment that simulates a card game between two players.
    
    The game is played on a board with 4 rows and a hand of 10 cards for each player. The objective is to score points by playing cards in a specific order, combining their elements. Actions are performed by playing cards from the hand, which are removed from the hand after being used. The game ends when all cards have been played or a certain number of rounds has been won.
    
    Attributes:
        action_space (gym.spaces.Discrete): The space of possible actions, represented as an integer index corresponding to a card in the player's hand.
        observation_space (gym.spaces.Box): The space of possible observations, representing the state of the game board and players' hands."""

    def __init__(self, training = False):
        """Initialize the environment with a random seed and initial state."""

        super().__init__()
        self.training = training
        self.display = CardTable()
        # Define action and observation space
        self.action_space = spaces.Discrete(40)  # Example: two possible actions - 0 or 1
        self.observation_space = spaces.Box(low=0, high=50, shape=(465,), dtype=np.uint8)
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

        self.board = Board(self.players[0].name, self.players[1].name)

        if not self.coin_flip:
            self.players.reverse()

        self.rewards = {
            True : 0,
            False : 0
            }
        
        self.steps=0

        time_stamp = time.strftime("%d%m%Y_%H%M%S", time.localtime())
        logging.basicConfig(level=logging.DEBUG, filename='logs/'+str(time_stamp)+'.log', filemode='w', format='%(message)s')

    def setup_hand_for_new_round(self) -> None:
        self.board.set_deck(True, Booster().open(20))
        self.board.draw_cards_to_hand(True, 10)
        self.board.set_deck(False, Booster().open(20))
        self.board.draw_cards_to_hand(False, 10)

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
        action = int(action)
        self.steps+=1
        logging.debug("Step: %s", self.steps)
        logging.debug("Action: %s", action)
        info = {}
        # Note: if not coinflip, human begins
        first_player_is_bottom_player = not self.coin_flip

        for player, is_bottom_player in zip(self.players, [first_player_is_bottom_player, not first_player_is_bottom_player]):
            # we have already passed
            if self.board.has_passed(is_bottom_player):
                continue
            
            if action and action >= len(self.board.get_hand(is_bottom_player))+1:
                action = 0

            card_index = player.make_choice(self.board.get_valid_choices(is_bottom_player),
                                            action=action)
            # we are passing this turn
            if card_index == 0:
                self.board.pass_round(is_bottom_player)
                continue
            card_index = card_index - 1
            # otherwise play card
            played_card = self.board.get_hand(is_bottom_player)[card_index]
            played_row = played_card.type
            if played_row == Row.ANY:
                played_row = player.make_row_choice(played_card, [Row.FRONT, Row.WISE, Row.SUPPORT])
            self.board.play_card(is_bottom_player, card_index, played_row) # (bool, card_index -> int, row (Enum))
            if not self.training and not first_player_is_bottom_player:
                self.render()
 
        if self.board.has_passed(True) and self.board.has_passed(False):
            self.board.end_round()
            self.board.draw_cards_to_hand(True)
            self.board.draw_cards_to_hand(False)

        truncated = self.steps == 100

        self.done = self.board.game_ended()
        if not self.training and self.done:
            winner = self.board.get_winner()
            if len(winner) == 1:
                message = f"{winner[0]} won the game!"
            else:
                message = "Draw, no one won the game"
            self.display.write_message(message)

        observation = self.get_state()
        reward = self.get_reward()
        logging.debug("Round Number: %s",self.board.round_number)
        if truncated:
            logging.debug("TRUNCATED")
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
        self.rewards = {
            True : 0,
            False : 0
            }
        self.board.reset()
        self.setup_hand_for_new_round()
        self._state = self.get_state()
        logging.debug("NEW GAME")
        return self._state, info

    def render(self, mode='human'):
        """Render the environment for visualization."""
        for bottom_player in [True, False]:
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

        state = np.zeros((465,), dtype=np.uint8)
        
        top_board_cards = list(chain(*list(self.board.get_half_board(False).values())))
        bottom_board_cards = list(chain(*list(self.board.get_half_board(True).values())))

        top_board_card_vectors = np.array([
            card.get_card_vector() for card in top_board_cards
        ], dtype=np.uint8).flatten()

        bot_board_card_vectors = np.array([
            card.get_card_vector() for card in bottom_board_cards
        ], dtype=np.uint8).flatten()

        hand = np.array([
            card.get_card_vector() for card in self.board.get_hand(False)
        ], dtype=np.uint8).flatten()
        row_scores = np.array(
            [score for row, score in self.board.get_row_scores(True).items()]+
            [score for row, score in self.board.get_row_scores(False).items()]
        ).flatten()
        #graveyard = np.concatenate(self.board.get_graveyard(False).flatten())
        skip = 0
        state[skip:len(bot_board_card_vectors)] = bot_board_card_vectors
        skip += 114 # 38 * card vector of 3
        state[skip:skip+len(top_board_card_vectors)] = top_board_card_vectors
        skip += 114 # 38 * card vector of 3
        state[skip:skip+len(hand)] = hand
        skip += 114 # 38 * card vector of 3
        state[skip:skip+len(row_scores)] = row_scores
        state[-3] = self.board.round_number             # 462
        state[-2] = self.board.get_rounds_won(True)     # 463
        state[-1] = self.board.get_rounds_won(False)    # 464

        self._state = state
        return self._state

    def get_reward(self, player=True):
        """Calculates and returns the reward for a given player's actions.

        Args:
            player (boolean): The player for whom to calculate the reward.

        Returns:
            float: The calculated reward based on the player's performance and actions.
        """
        reward = 0
        win_reward = 10

        # Reward for winning a round
        if self.board.get_rounds_won(player) > 0:
            reward += win_reward * (self.board.get_rounds_won(player)
                                    - self.board.get_rounds_won(not player))

        # Incremental rewards for positive actions
        # For example, playing a card that increases the player's score or strategically passing
        #reward += 1 * self.board.player_states[player]["turn_score"]
        won_rows = self.board.get_won_rows()
        if self.board.has_passed(not player):
            reward += 2 + (won_rows[int(not player)] - won_rows[int(player)])

        for row, score in self.board.get_row_scores(player).items():
            reward += score

        self.rewards[player] += reward
        logging.debug("Reward: %s", self.rewards[player])
        return reward

    def get_coin_flip(self):
        """Determine whether the first player starts by coin flip (True) or fixed order (False).
    
        Returns:
        bool: True if the coin flip determines the starting player, False otherwise."""
        return bool(random.getrandbits(1))

    def close(self):
        self.display.stop_render()
    
