# third party imports
import logging
import time
import random
from colorama import Fore
from gymnasium import Env
from gymnasium.spaces import Discrete, Box
import numpy as np
# local imports
from src.cards import Card
from src.row import Row
import src.utils as utils
#from src.player import Human, ArtificialRetardation
from src.cards import Booster, EffectCard
#from src.cards import CardName
from src.player import ArtificialRetardation


class Board(Env): # Env -> gym Environment
    """Represents the game board environment (including state) for a card game.

    This class extends the gym Environment to create a customizable card game environment
    with options for human and AI players, logging, and network play.
    """
    def __init__(self):
        """Initializes the game board with optional network play."""
        super().__init__()
        self.round_number=0
        self.done = False
        self.half_board = {
            Row.FRONT: [],
            Row.WISE: [],
            Row.SUPPORT: [],
            Row.EFFECTS: []
        }
        # Player attributes
        self.player_states = {
            "top_player":{
                "name": "",
                "half_board": self.half_board.copy(),
                "passed": False,
                "deck": [],
                "hand": [],
                "graveyard": [],
                "reward": 0,
                "current_rows_won": 0,
                "rounds_won": 0
            },
            "bottom_player":{
                "name": "",
                "half_board": self.half_board.copy(),
                "passed": False,
                "deck": [],
                "hand": [],
                "graveyard": [],
                "reward": 0,
                "current_rows_won": 0,
                "rounds_won": 0
            }
        }
        # Setup for game
        self.setup_logging()
        self.initialize_Board()
        self.setup_network_feedback()

    def clear_deck(self):
        """Clears the game board"""
        self.player_states["top_player"]["deck"] = []
        self.player_states["bottom_player"]["deck"] = []
        return

    def clear_board(self):
        """Clears the game board"""
        self.player_states["top_player"]["half_board"] = self.half_board.copy()
        self.player_states["bottom_player"]["half_board"] = self.half_board.copy()
        return
    
    def clear_hands(self):
        """Clears the hands"""
        self.player_states["top_player"]["hand"] = []
        self.player_states["bottom_player"]["hand"] = []
        return

    def get_board_vector(self):
        """
        Returns the game board as a vector with shape (76,3), empty card slots will be filled with zeros.
        (76, 3) since the maximal state can be with 76 cards of value 1.
        """
        cards_p1 = [card.get_card_vector() for card in self.player_states["top_player"]["half_board"]]
        cards_p2 = [card.get_card_vector() for card in self.player_states["top_player"]["half_board"]]
        # TODO add constant length
        board_vector = np.ndarray(cards_p1 + cards_p2)
        return board_vector
    
    def get_hands_vector(self):
        pass  # np.zeros((38,3))

    def get_score_vector(self):
        pass

    def setup_logging(self): # Possible Problem: Now creates log file for every individual game (might cause problems with training sessions)
        """
        Sets up logging for the game, creating a log file with a unique timestamp.
        """
        time_stamp = time.strftime("%d%m%Y_%H%M%S", time.localtime())
        logging.basicConfig(level=logging.DEBUG, filename='logs/' + str(time_stamp) + '.log', filemode='w', format='%(message)s')
        self.log_time_stamp = time.strftime("%d/%m/%Y - %H:%M:%S", time.localtime())

    def initialize_Board(self):
        """
        Initializes the board and players for the start of the game.
        """
        self.clear_deck()  # Generate empty player decks
        self.clear_board() # Generate empty player boards
        self.clear_hands() # Generate empty player hands
        self.round_number = 1

    def set_deck(self, deck: list[Card], player: str) -> None:
        self.player_states[player]["deck"] = deck

    def setup_network_feedback(self) -> None:
        """Sets up the environment specifically for network play, including action and observation spaces."""
        self.action_space = Discrete(39)
        self.observation_space = Box(low=0, high=38, shape=(348,), dtype=np.float64)

    def close(self): # gym method
        """Cleans up the environment, to be called when the game is closed."""
        
        # Implement any necessary cleanup
        raise NotImplementedError

    def reset(self,seed=None): # gym wrapper method
        """Resets the environment for a new episode. Wrapper method for gym environments.

        Args:
            seed (int, optional): The seed for random number generators.
        
        Returns:
            tuple: The initial state of the environment, and an empty info dict.
        """
        self.__init__()
        return self.get_state(), {}

    def get_valid_choices(self, player):
        valid_choices = list(range(len(self.player_states[player]["hand"])))
        return valid_choices
        
    def get_ar_action_meaning(self, ar_action):
        """Translates an action received from an AI into a meaningful game action.

        Args:
            ar_action (int): The action id to be interpreted.

        Raises:
            NotImplementedError: Indicates the method needs to be implemented.
        """
        raise NotImplementedError

    def get_row_sum(self, player, row) -> list[int]:
        return sum(card.strength for card in self.player_states[player]["half_board"][row])

    def get_state(self): # 38 max hand cards + 76 max board cards + 2 turn scores + 1 win points
        """Compiles the current game state into a structured format.

        This includes the hand vector, board vector, and score vector representing
        the current situation of the game from the perspective of the AI.

        Returns:
            np.array: A numpy array representing the current state of the game.
        """
        hand_vector = self.get_hands_vector()
        board_vector = self.get_board_vector()
        score_vector = self.get_score_vector()
        state = np.zeros(348)
        state = np.concatenate([hand_vector.flatten(), board_vector.flatten(), score_vector.flatten()])
        logging.debug("State: %s",state)
        # Flatten the row scores and card hands into one long vector
        #state = state.astype(np.uint32)
        #print(state.shape) #DEBUG
        return state.flatten()

    def reward_function(self, player):
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
        logging.debug("REWARD: %s %s",player.name, player.reward)
        return player.reward

    def draw_cards_to_hand(self, player, num_cards=2, shuffle=False) -> None:
        """Allows a player to draw a specified number of cards into their hand.
        Args:
            player: The player who will draw cards.
            num_cards (int, optional): The number of cards to draw. Defaults to 2.
            shuffle (boolean, optional)
        """
        deck = self.player_states[player]["deck"]
        hand = self.player_states[player]["hand"]
        if shuffle:
            random.shuffle(deck)
        # Draw cards from the deck
        hand = hand + deck[:num_cards]
        # Remove drawn cards from the deck
        deck = deck[num_cards:]

    def end_round(self):
        # update round scores
        
        # update round ticker
        self.round_number += 1
        # update graveyard
        pass

    def play_card(self, player, card_index, row) -> None:
        """
        Method to player a card into a given round

        Args:
            player (str): identifier of the player
            card (int): index of the card that is played (index in hand)
            row (Row): row in which the card is played
        """
        hand = self.player_states[player]["hand"]
        played_card = hand[card_index]
        # special case if effect card
        if isinstance(played_card, EffectCard):
            played_card.execute_effect(self)
        else:
            # add it to the players board
            self.player_states[player]["half_board"][row] += hand[card_index]
        # remove card from hand
        hand = hand[:card_index] + hand[card_index+1:]

    def log_round_result(self) -> None:
        """Logs the result of the current round, including the winner and updated scores."""
        p1 = self.player_states["top_player"]
        p2 = self.player_states["bottom_player"]
        winner = ""
        if p1["current_rows_won"] > p2["current_rows_won"]:
            winner = p1["name"]
        elif p1["current_rows_won"] < p2["current_rows_won"]:
            winner = p2["name"]
        else:
            logging.debug("The round was a draw, one point to both players!")
        if winner:
            logging.debug("\n--- Player {winner} won round {self.round_number} ---")
        logging.debug("Current Round Score: %s : %s, %s : %s",
            p1["name"],
            p1["rounds_won"],
            p2["name"],
            p2["rounds_won"]
        )

    def render(self): # gym required method
        pass

    def get_row_scores(self) -> tuple[int, int]:
        """
        Gets the score for each row based on the current cards in play, affecting the overall game state.

        Returns:
            tuple[dict, dict]: tuple that contains the scores for both players, (top, bottom)
        """
        top_rows = [row for row in self.player_states["top_player"]["half_board"] if row != Row.EFFECTS]
        row_scores_top = {row: sum(card.strength for card in row) for row in top_rows}

        bottom_rows = [row for row in self.player_states["bottom_player"]["half_board"] if row != Row.EFFECTS]
        row_scores_bottom = {row: sum(card.strength for card in row) for row in bottom_rows}
        return row_scores_top, row_scores_bottom

    def get_winner(self) -> list[str]:
        """
        Determines and the winner of the game based on the final scores.

        Returns:
            List[str]: list of winning player identifiers (could be one or two, if draw)
        """

        winner = []
        rounds_top_player_won = self.player_states["top_player"]["rounds_won"]
        rounds_bottom_player_won = self.player_states["top_player"]["rounds_won"]
        
        if rounds_top_player_won <= rounds_bottom_player_won:
            winner += ["top_player"]
        if rounds_top_player_won >= rounds_bottom_player_won:
            winner += ["bottom_player"]
        return winner

    def play_round(self, action, players):
        """Plays through a single round of the game, with each player taking turns until the round concludes."""
        # Draw hands for each player in the second and third rounds
        if self.round_number>3:
            logging.debug("ROUND OUT OF BOUNDS")
            self.done = True

        if self.round_number > 1:
            valid_choices = self.get_valid_choices()
            if not self.passed1:
                players[0].make_pass_choice(self.hand1)
                if not self.passed1:
                    action1 = players[0].make_card_choice(valid_choices[0])
                    self.play_card(self.hand1, action1, players[0], 1)

            if not self.passed2:
                players[1].make_pass_choice(self.hand2)
                if not self.passed2:
                    action2 = players[1].make_card_choice(valid_choices[1])
                    self.play_card(self.hand2, action2, players[1], 2)

    def step(self, action):
        self.play_round(action, self.players)
        info = {}
        return self.get_state(), self.reward_function(self.players[0]), self.done, self.done, info # gym required return
