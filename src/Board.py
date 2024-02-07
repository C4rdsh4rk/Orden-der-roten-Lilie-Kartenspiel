import logging
import time
from colorama import Fore
from gymnasium import Env
from gymnasium.spaces import Discrete, Box
from src.row import Row
import src.utils as utils
from src.player import Human, ArtificialRetardation
from src.cards import Booster
from src.cards import CardName
import numpy as np
import random

class Board(Env): # Env -> gym Environment
    """Represents the game board environment for a card game.

    This class extends the gym Environment to create a customizable card game environment
    with options for human and AI players, logging, and network play.
    
    Attributes:
        round_number (int): The current round number in the game.
        network_active (bool): Flag indicating whether network features are active.
        done (bool): Flag indicating whether the game is finished.
        players (list): List of players in the game, which can include both human and AI players.
    """
    def __init__(self, network_active=False):
        """Initializes the game board with optional network play.

        Args:
            network_active (bool): If True, sets up the environment for network play.
        """
        super().__init__()
        self.round_number=0
        self.network_active = network_active
        self.half_board = {
            Row.FRONT: [],
            Row.WISE: [],
            Row.SUPPORT: [],
            Row.EFFECTS: []
        }
        self.empty_deck = []
        self.empty_hand = []
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
        self.setup_logging()
        self.done = False
        self.initialize_Board()
        self.display_decks()
        if network_active:
            self.setup_network_active_environment()

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

    def setup_logging(self):
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
        return
 '''
    def get_players(self, network_active):
        """Creates and returns a list of players based on the game mode.

        Args:
            network_active (bool): Determines whether the game will include network-based players.
        
        Returns:
            list: A list of player instances, which can be human or AI.
        """
        if network_active:
            logging.debug("Training started - %s",self.log_time_stamp)
            return [ArtificialRetardation("Neural Nutjob", "nn"), ArtificialRetardation("Trained Monkey", "pc")]
        else:
            logging.debug("Board started - %s",self.log_time_stamp)
            choice = utils.get_user_input("Choose a Board mode (type '1' to play yourself or '2' to simulate): ", ['1', '2'])
            if choice == '1':
                name = input("Enter your name: ").lower()
                #return [Human(name, "human"), ArtificialRetardation("Trained Monkey", "pc")]
                return [Human(name, "human"), ArtificialRetardation("Neural Nutjob", "nn")]
            else:
                return [ArtificialRetardation("Trained Monkey", "pc"), ArtificialRetardation("Clueless Robot", "pc")]
'''
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

    def display_decks(self) -> None:
        """Displays the decks of all players. Logs the deck information if network is not active."""
   
        for player in self.players:
            logging.debug(player.deck)
            if not self.network_active:
                player.display_deck()

    def setup_network_active_environment(self) -> None:
        """Sets up the environment specifically for network play, including action and observation spaces."""
        
        self.action_space = Discrete(39)
        for player in self.players:
            player.draw_cards_to_hand(10, True)
        self.observation_space = Box(low=0, high=38, shape=(234,), dtype=np.float64)

    def board_loop(self) -> None:
        """Runs the main game loop, playing through rounds until the game is concluded."""
        
        # Play three rounds
        self.round_number = 1
        while not self.done:
            self.play_round()
        self.display_winner()
        self.reset_Board()

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
        return self.reset_Board(),{}

    def _get_info(self): # gym method
        """Returns diagnostic information useful for debugging."""
       
        raise NotImplementedError

    def _get_obs(self): # gym method
        """Returns the current observation of the game state.

        Returns:
            tuple: The observation, reward, done flag, and additional info.
        """
        info = {}
        return self.get_state(), self.reward_function(self.players[0]), self.done, info
    
    def get_ar_action_meaning(self, ar_action):
        """Translates an action received from an AI into a meaningful game action.

        Args:
            ar_action (int): The action id to be interpreted.

        Raises:
            NotImplementedError: Indicates the method needs to be implemented.
        """
        raise NotImplementedError

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

        board_vector = self.get_board()

        self.update_row_scores()
        score_vector = np.zeros(6)
        
        i = 0
        for row in self.players[0].rows:
            if row == Row.EFFECTS:
                continue
            score_vector[i] = int(self.players[0].row_score[row])
            score_vector[i+1] = int(self.players[1].row_score[row])
            i+=2
        
        self.state = np.concatenate([hand_vector.flatten(), board_vector.flatten(), score_vector])
        logging.debug("State: %s",self.state)
        # Flatten the row scores and card hands into one long vector
        return self.state

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
        reward += 0.1 * player.turn_score
            
        if self.players[1].passed:
            reward += 1 + (self.turn_score2 - self.turn_score1)

        player.reward = reward
        logging.debug("REWARD: %s %s",player.name, player.reward)
        return player.reward

    def step(self, ar_action): # network_active turn for gym
        """Performs a step in the environment for network play, processing an action and updating the state.

        Args:
            ar_action (int): The action to be performed by the AI player.

        Returns:
            tuple: A tuple containing the new state, reward, done flag, and info dict.
        """
        self.play_turn(self.players[0],ar_action)
        self.play_turn(self.players[1])
        if self.players[0].passed and self.players[1].passed:
            self.display_round_result()
            self.round_number+=1
            self.update_win_points()
            self.clear_board()
            self.done = (self.rounds_won1 >= 2 or self.rounds_won2 >= 2)
        info = {} 
        if self.done:
            self.display_winner()
        return self.get_state(), self.reward_function(self.players[0]), self.done, self.done, info
    
    def play_turn(self,player,ar_action=None): # Normal turn
        """Executes a turn for the given player, optionally processing an AI action.

        Args:
            player (Player): The player whose turn it is.
            ar_action (int, optional): The action to be performed if the player is an AI.

        Note:
            This method updates the game state based on the player's action and logs the turn.
        """
        player.turn_number+=1
        logging.debug(f"\n{player.name}'s Turn:")
        logging.debug(f"\nROUND: {self.round_number}")
        logging.debug(f"{player.name}'s hand: {len(player.hand)}")
        logging.debug(f"{player.name}'s turn: {player.turn_number}")
        logging.debug("AR action: %s",ar_action)

        if len(player.hand)==0:
            player.passed = True
            logging.debug(f"{player.name} has no cards left and PASSED")
            logging.debug(f"{player.name} has no cards left and passed!")
        if not ar_action==None and not player.passed:
            logging.debug("AR_case")
            if ar_action == 39: # max Deck length + passing option
                player.passed = True
                logging.debug("AR passed")
            elif ar_action:
                played_card = player.play_card()
                logging.debug(f"AR played card: {played_card}")
        if not player.passed and ar_action==None:
            player.make_pass_choice()
            if player.passed:
                logging.debug(f"{player.name} passed")
                logging.debug(f"{player.name} passed")
            
            played_card = player.play_card()
            logging.debug(f"{player.name} played card: {played_card}")
            self.render(self.players)
            self.update_row_scores()
        return
    
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


    def play_round(self):
        """Plays through a single round of the game, with each player taking turns until the round concludes."""
        
        # Draw hands for each player in the second and third rounds
        if self.round_number>3:
            print(Fore.RED+f"WTF THIS SHOULDN'T BE POSSIBLE - anyhow, enjoy the rest of your bugged Board")
            logging.debug("ROUND OUT OF BOUNDS")
        if self.round_number > 1:
            for player in self.players:
                player.clear_board()
                player.draw_cards_to_hand(2)
                player.passed = False
                logging.debug("{player.name} drew 2 cards. Rows were cleared.")
        while True:
            # Take turns playing cards
            for player in self.players:
                self.play_turn(player)
                self.reward_function(player)
                #self.render(self.players)
            # Display the current score
            print(f"\nCurrent Rows Won - {self.players[0].name}: {self.turn_score1}, {self.players[1].name}: {self.turn_score2}")
            if self.players[0].passed and self.players[1].passed:
                self.update_win_points()
                break

        self.display_round_result()
        self.round_number += 1
        self.done = (self.rounds_won1 >= 2 or self.rounds_won2 >= 2)

    def display_round_result(self) -> None:
        """Logs the result of the current round, including the winner and updated scores."""
        
        winner = ""
        if self.turn_score1 > self.turn_score2:
            winner = self.players[0].name
        elif self.turn_score1 < self.turn_score2:
            winner = self.players[1].name
        else:
            pass
            logging.debug("The round was a draw, one point to both players!")
        if winner:
            pass
            logging.debug("\n--- Player {winner} won round {self.round_number} ---")
        logging.debug("Current Round Score: %s : %s, %s : %s",self.players[0].name, self.rounds_won1, self.players[1].name, self.rounds_won2)

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
            pass

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

    def display_rows(self,deck: list[tuple], display_effects=False, backwards=False):
        """Displays the cards in each row, optionally including special effects cards, in a formatted output.

        Args:
            deck (list[tuple]): A list of tuples, each containing a row identifier and its associated cards.
            display_effects (bool, optional): Whether to include special effects cards in the display. Defaults to False.
            backwards (bool, optional): Whether to display the rows in reverse order. Defaults to False.
        """
        colors = {Row.FRONT: Fore.RED, Row.WISE: Fore.WHITE, Row.SUPPORT: Fore.GREEN, Row.EFFECTS: Fore.MAGENTA}
        deck.sort(reverse=backwards, key=self.row_sort_order)
        for row, cards in deck:
            if row == Row.EFFECTS and not display_effects:
                continue
            print(colors[row],f"{row}:")
            print(f"{'+----------+ '*len(cards)}")
            print(f"{'|          | '*len(cards)}")
            print(" ".join([f"| {card.name}" + " "*(9-len(card.name))+"|" for card in cards]))
            print(" ".join([f"| Str: {card.strength}   |" for card in cards]))
            print(f"{'|          | '*len(cards)}")
            print(f"{'+----------+ '*len(cards)}")
            print(Fore.WHITE)

    def render(self,players): # gym required method 
        """Renders the current game state to the console or log, showing the board and player scores.

        Args:
            players (list): The list of players in the game to be displayed.
        """
        logging.debug("\nCurrent Score - Round: {self.round_number} Turn Score:{self.players[0].name}: {self.turn_score1}\t,\t{self.players[1].name}: {self.turn_score2}")
        logging.debug("\n------ Current Board ------")
        #logging.debug("###############################################################################################################")
        for player in players:
            # Display Player 1's Board
            logging.debug("%s's Board:", player.name)
            self.display_rows(list(player.rows.items()), False, player==players[0])
            #logging.debug("###############################################################################################################")

    def display_sum(self,player):
        """Logs the sum of card strengths for each row for the specified player.

        Args:
            player (Player): The player whose row sums are to be displayed.
        """
        logging.debug("{player.name}'s Current Sums:")
        for row, cards in player.rows.items():
            logging.debug("%s: %i", row, sum(card.strength for card in cards))
            

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
            self.players[0].row_score[row] = self.players[0].get_row_sum(row)
            self.players[1].row_score[row] = self.players[1].get_row_sum(row)
            #logging.debug(self.players[0].row_score[row]) # DEBUG
            if row == Row.EFFECTS:
                continue
            if self.players[0].get_row_sum(row) >= self.players[1].get_row_sum(row):
                if self.players[0].get_row_sum(row)==0 and self.players[1].get_row_sum(row)==0:
                    continue
                else:
                    player1_score += 1
            if self.players[0].get_row_sum(row) <= self.players[1].get_row_sum(row):
                if self.players[0].get_row_sum(row)==0 and self.players[1].get_row_sum(row)==0: # Probably not necessary twice
                    continue
                else:
                    player2_score += 1
        self.turn_score1 = player1_score # How many rows are won by this player at the time the function is called
        self.turn_score2 = player2_score # How many rows are won by this player at the time the function is called
        return 
    
    def display_row_scores(self):
        """Logs the current row scores for each player, indicating the state of the game."""
        
        logging.debug(
                    "%s's wins %s rows\n"\
                    "%s's wins %s rows"
                    ,self.players[0].name,
                    self.turn_score1,
                    self.players[1].name,
                    self.turn_score2)
    
    def display_winner(self):
        """Determines and logs the winner of the game based on the final scores."""
        
        winner = ""
        reward = 0
        if self.rounds_won1 < self.rounds_won2:
            winner = self.players[1].name
            reward = self.players[1].reward
        elif self.rounds_won1 > self.rounds_won2:
            winner = self.players[0].name
            reward = self.players[0].reward
        if winner:
            logging.debug("%s won the Board!", winner)
        else:
            logging.debug("Draw - No one won the Board")
        time_stamp = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime())
        logging.debug("%s won the Board!", winner)
        logging.debug("Final reward %s (to compare with NN)", reward)
        logging.debug("\nBoard ended - %s", time_stamp)
        return













'''
    def __init__(self, network_active=False):
        super().__init__()
        time_stamp = time.strftime("%d%m%Y_%H%M%S", time.localtime())
        logging.basicConfig(level=logging.debug, filename='logs/'+str(time_stamp)+'.log', filemode='w', format='%(message)s')
        time_stamp = time.strftime("%d/%m/%Y - %H:%M:%S", time.localtime())
        self.done = False
        if network_active:
            logging.debug("network_active started - {time_stamp}")
            self.players=self.initialize_Board(network_active)
        else:
            logging.debug("Board started - {time_stamp}")
            self.players=self.initialize_Board()
        # Display the decks
        for player in self.players:
            player.display_deck()
        if network_active:           
            self.action_space = Discrete(39)
            for player in self.players:
                player.draw_cards_to_hand(10,True)
            self.observation_space =  Box(low=0, high=38, shape=(234,), dtype=np.uint8) # self.get_state() #38 max hand cards + 76 max board cards +2 turn scores + 1 win points  
        else:
            self.board_loop()# Start Board loop

    def initialize_Board(self,network_active=False):
        utils.clear_screen()
        self.round_number=1
        if not network_active:
            while True:
                choice = utils.get_user_input("Choose a Board mode (type '1' to play yourself or '2' to simulate): ", ['1', '2'])
                if choice == '1':
                    name = input("Enter your name: ").lower()
                    player1 = Human(name, "human")
                    player2 = ArtificialRetardation("Trained Monkey", "pc")
                    break
                else:
                    player1 = ArtificialRetardation("Trained Monkey", "pc")
                    player2 = ArtificialRetardation("Clueless Robot", "pc")
                    break
        else:
            logging.debug("NN Player activated")
            player1 = ArtificialRetardation("Neural Nutjob", "nn")
            player2 = ArtificialRetardation("Trained Monkey", "pc")
        
        # Build decks for each player
        booster_instance = Booster()
        player1.build_deck(booster_instance)
        player2.build_deck(booster_instance)
        
        player1.draw_cards_to_hand(10,True)
        player2.draw_cards_to_hand(10,True)
        logging.debug("Players drew 10 cards from their shuffled deck.")
        return player1, player2

    def board_loop(self):
      # Play three rounds
        self.round_number = 1       
        while not self.done:  # Using 'not' to check the condition and simplify the loop condition
            self.play_round()
        self.display_winner()
        self.reset_Board() 
'''