# third party imports
import logging
import time
import random
from colorama import Fore
from gymnasium import Env
from gymnasium.spaces import Discrete, Box
import numpy as np
# local imports
from src.row import Row
import src.utils as utils
#from src.player import Human, ArtificialRetardation
from src.cards import Booster
#from src.cards import CardName
from src.player import ArtificialRetardation


class Board(Env): # Env -> gym Environment
    """Represents the game board environment for a card game.

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
        self.empty_deck = []
        self.empty_hand = []

        # Player attributes
        self.reward1 = 0
        self.reward2 = 0
        self.turn_score1 = 0
        self.turn_score2 = 0
        self.row_score1 = {}
        self.row_score2 = {}
        self.turn_number1 = 0
        self.turn_number2 = 0
        self.passed1 = False
        self.passed2 = False
        self.rounds_won1 = 0
        self.rounds_won2 = 0

        player1 = ArtificialRetardation("Trained Monkey", "pc")
        player2 = ArtificialRetardation("Neural Nutjob", "nn")
        self.players = player1, player2
        
        # Setup for game
        self.setup_logging()
        self.initialize_Board()
        self.setup_network_feedback()

    def clear_deck(self):
        """Clears the game board"""
        self.deck1 = self.empty_deck.copy()
        self.deck2 = self.empty_deck.copy()
        return

    def clear_board(self):
        """Clears the game board"""
        self.half_board_top = self.half_board.copy()
        self.half_board_bottom = self.half_board.copy()
        return
    
    def clear_hands(self):
        """Clears the hands"""
        self.hand1 = self.empty_hand.copy()
        self.hand2 = self.empty_hand.copy()
        return

    def get_board(self):
        """Returns the game board as a vector with shape (76,3)
                Empty card slots will be filled with zeros
        """
        board_vector = np.zeros((76,3))
        for row, cards_in_row in self.half_board_top.items():
            for card in cards_in_row:
                card_vector = card.get_card_vector()  # Assuming get_card_vector method returns the vector representation
                board_vector[row.value] += card_vector
        for row, cards_in_row in self.half_board_bottom.items():
            for card in cards_in_row:
                card_vector = card.get_card_vector()  # Assuming get_card_vector method returns the vector representation
                board_vector[row.value] += card_vector
        
        return board_vector

    def setup_logging(self): # Possible Problem: Now creates log file for every individual game (might cause problems with training sessions)
        """Sets up logging for the game, creating a log file with a unique timestamp."""
    
        time_stamp = time.strftime("%d%m%Y_%H%M%S", time.localtime())
        logging.basicConfig(level=logging.DEBUG, filename='logs/' + str(time_stamp) + '.log', filemode='w', format='%(message)s')
        self.log_time_stamp = time.strftime("%d/%m/%Y - %H:%M:%S", time.localtime())

    def initialize_Board(self):
        """Initializes the board and players for the start of the game."""
        self.clear_deck()  # Generate empty player decks
        self.clear_board() # Generate empty player boards
        self.clear_hands() # Generate empty player hands
        utils.clear_screen()
        self.round_number = 1

    def initialize_decks(self) -> None:
        """Initializes decks and hands for all players in the game.

        Args:
            players (list): The list of players who will have their decks initialized.
        """
        booster_instance = Booster()
        self.deck1 = self.players[0].build_deck(booster_instance)
        self.hand1 = self.draw_cards_to_hand(self.hand1, self.deck1, 10, True) # draw_cards_to_hand(self, hand, deck, num_cards=2,shuffle=False):
        self.deck2 = self.players[1].build_deck(booster_instance)
        self.hand2 = self.draw_cards_to_hand(self.hand2, self.deck2, 10, True)
        logging.debug("Players drew 10 cards from their shuffled deck.")

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

    def get_valid_choices(self):
        valid_choices = ["{:1d}".format(x) for x in range(len(self.hand1))],["{:1d}".format(x) for x in range(len(self.hand2))]
        return valid_choices
        
    def get_ar_action_meaning(self, ar_action):
        """Translates an action received from an AI into a meaningful game action.

        Args:
            ar_action (int): The action id to be interpreted.

        Raises:
            NotImplementedError: Indicates the method needs to be implemented.
        """
        raise NotImplementedError

    def get_row_sum(self, rows, row) -> list[int]:
        return sum(card.strength for card in rows[row])

    def get_state(self): # 38 max hand cards + 76 max board cards +2 turn scores + 1 win points
        """Compiles the current game state into a structured format.

        This includes the hand vector, board vector, and score vector representing
        the current situation of the game from the perspective of the AI.

        Returns:
            np.array: A numpy array representing the current state of the game.
        """
        hand_vector = np.zeros((38,3))
        for i in range(len(self.hand1)):
            hand_vector[i] = self.hand1[i].get_card_vector()
            if i>38:
                raise ValueError

        board_vector = self.get_board()

        self.update_row_scores()
        score_vector = np.zeros(6)

        i = 0
        for row in self.half_board:
            if row == Row.EFFECTS:
                continue
            score_vector[i] = int(self.row_score1[row])
            score_vector[i+1] = int(self.row_score2[row])
            i+=2
        state = np.zeros(348)
        state = np.concatenate([hand_vector.flatten(), board_vector.flatten(), score_vector.flatten()])
        logging.debug("State: %s",state)
        # Flatten the row scores and card hands into one long vector
        #state = state.astype(np.uint32)
        #print(state.shape) #DEBUG
        return state.flatten()

    def reward_function(self,player):
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
            reward += win_reward * (self.rounds_won1 - self.rounds_won2)

        # Incremental rewards for positive actions
        # For example, playing a card that increases the player's score or strategically passing
        reward += 1 * player.turn_score

        if self.passed2:
            reward += 1 + (self.turn_score2 - self.turn_score1)

        player.reward = reward
        logging.debug("REWARD: %s %s",player.name, player.reward)
        return player.reward

    def draw_cards_to_hand(self, hand, deck, num_cards=2,shuffle=False):
        """Allows a player to draw a specified number of cards into their hand.
        Args:
            hand: The player who will draw cards.
            deck:
            num_cards (int, optional): The number of cards to draw. Defaults to 2.
            shuffle (boolean, optional)
        """
        if shuffle:
            random.shuffle(deck)
        # Draw cards from the deck
        hand = hand + deck[:num_cards]
        # Remove drawn cards from the deck
        deck = deck[num_cards:]

    def play_card(self, hand, action, player, h_b) -> None:
        chosen_card = hand[action]
        row = chosen_card.type
        if row == Row.ANY:
            row = player.make_row_choice()
        # add card to row to play it and remove it from the hand
        if h_b==1:
            self.half_board_bottom[row].append(chosen_card)
        else:
            self.half_board_top[row].append(chosen_card)

        card_index = hand.index(chosen_card)
        hand = hand[:card_index] + hand[card_index+1:]
        return

    def calculate_round_result(self) -> None:
        """Logs the result of the current round, including the winner and updated scores."""
        
        winner = ""
        if self.turn_score1 > self.turn_score2:
            winner = self.players[0].name
        elif self.turn_score1 < self.turn_score2:
            winner = self.players[1].name
        else:
            logging.debug("The round was a draw, one point to both players!")
        if winner:
            logging.debug("\n--- Player {winner} won round {self.round_number} ---")
        logging.debug("Current Round Score: %s : %s, %s : %s",
                        self.players[0].name,
                        self.rounds_won1,
                        self.players[1].name,
                        self.rounds_won2)

    def resolve_effect(self,player,card):
        """Applies the effect of a special card played by a player.

        Args:
            player (Player): The player who played the card.
            card (Card): The card whose effect needs to be resolved.
        """
        if card.name=="DRAW1":
            player.draw_cards_to_hand(1)
        elif card.name=="DRAW2":
            player.draw_cards_to_hand(2)
        else:
            logging.debug("unknown effect, bro")
            raise NotImplementedError

    def row_sort_order(self,row_card_tuple: tuple):
        """Determines the sorting order for cards in a row.

        Args:
            row_card_tuple (tuple): A tuple containing a row identifier and its associated card.

        Returns:
            int: A numeric value representing the sort order based on the row type.
        """
        row, _ = row_card_tuple

        if row == Row.SUPPORT:
            return 3
        elif row == Row.WISE:
            return 2
        elif row == Row.FRONT:
            return 1
        return 0

    def render(self): # gym required method
        pass

    def update_win_points(self):
        """Updates the win points for each player based on the current round's results.

        Returns:
            list: A list containing the updated rounds won by each player and a placeholder value.
        """
        if self.turn_score1 >= self.turn_score2:
            self.rounds_won1+=1
        if self.turn_score2 >= self.turn_score1:
            self.rounds_won2+=1
        return [self.rounds_won1, self.rounds_won2, 0]

    def update_row_scores(self):
        """Updates the score for each row based on the current cards in play, affecting the overall game state."""

        player1_score = 0
        player2_score = 0
        for row in self.half_board:
            if row == Row.EFFECTS:
                continue
            bottom = self.get_row_sum(self.half_board_bottom, row)
            top = self.get_row_sum(self.half_board_top, row)

            self.row_score1[row] = bottom
            self.row_score2[row] = top

            if bottom >= top:
                if bottom==0 and top==0:
                    continue
                else:
                    player1_score += 1
            if bottom <= top:
                if bottom==0 and top==0: # Probably not necessary twice
                    continue
                else:
                    player2_score += 1

        self.turn_score1 = player1_score # How many rows are won by this player at the time the function is called
        self.turn_score2 = player2_score # How many rows are won by this player at the time the function is called
        return

    def check_winner(self):
        """Determines and logs the winner of the game based on the final scores."""

        winner = ""
        reward = 0
        if self.rounds_won1 < self.rounds_won2:
            winner = self.players[1].name
            reward = self.reward2
        elif self.rounds_won1 > self.rounds_won2:
            winner = self.players[0].name
            reward = self.reward1
        if winner:
            logging.debug("%s won the Board!", winner)
        else:
            logging.debug("Draw - No one won the Board")
        time_stamp = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime())
        logging.debug("%s won the Board!", winner)
        logging.debug("Final reward %s (to compare with NN)", reward)
        logging.debug("\nBoard ended - %s", time_stamp)
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
