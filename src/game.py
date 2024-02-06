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

class Game(Env): # Env -> gym Environment
    def __init__(self, training=False):
        super().__init__()
        self.round_number=0
        self.training = training
        self.setup_logging()
        self.done = False
        self.players = self.initialize_game(training)
        self.display_decks()
        if training:
            self.setup_training_environment()
        else:
            self.game_loop()

    def setup_logging(self):
        time_stamp = time.strftime("%d%m%Y_%H%M%S", time.localtime())
        logging.basicConfig(level=logging.DEBUG, filename='logs/' + str(time_stamp) + '.log', filemode='w', format='%(message)s')
        self.log_time_stamp = time.strftime("%d/%m/%Y - %H:%M:%S", time.localtime())

    def initialize_game(self, training):
            utils.clear_screen()
            self.round_number = 1
            players = self.get_players(training)
            self.initialize_decks(players)
            return players
    
    def get_players(self, training):
            if training:
                logging.debug(f"Training started - {self.log_time_stamp}")
                return [ArtificialRetardation("Neural Nutjob", "nn"), ArtificialRetardation("Trained Monkey", "pc")]
            else:
                logging.debug(f"Game started - {self.log_time_stamp}")
                choice = utils.get_user_input("Choose a game mode (type '1' to play yourself or '2' to simulate): ", ['1', '2'])
                if choice == '1':
                    name = input("Enter your name: ").lower()
                    return [Human(name, "human"), ArtificialRetardation("Trained Monkey", "pc")]
                else:
                    return [ArtificialRetardation("Trained Monkey", "pc"), ArtificialRetardation("Clueless Robot", "pc")]

    def initialize_decks(self, players) -> None:
        booster_instance = Booster()
        for player in players:
            player.build_deck(booster_instance)
            player.draw_hand(10, True)
        logging.debug("Players drew 10 cards from their shuffled deck.")

    def display_decks(self) -> None:  
        for player in self.players:
            logging.debug(player.deck)
            if not self.training:
                player.display_deck()

    def setup_training_environment(self) -> None:
        self.action_space = Discrete(39)
        for player in self.players:
            player.draw_hand(10, True)
        self.observation_space = Box(low=0, high=38, shape=(234,), dtype=np.float64)

    def game_loop(self) -> None:
        # Play three rounds
        self.round_number = 1
        while not self.done:
            self.play_round()
        self.display_winner()
        self.reset_game()

    def reset_game(self):
        for player in self.players:
            player.deck = [] # Deck of cards
            player.hand = [] # Hand cards attribute
            player.turn_score = 0
            player.turn_number = 0
            player.passed = False
            player.rounds_won = 0
            player.row_score = {}
            player.clear_rows()
            #self.__init__()# infinite game loop
            self.round_number=1
        return self.get_state()

    def close(self): # gym method
        # Implement any necessary cleanup
        raise NotImplementedError

    def reset(self,seed=None): # gym wrapper method
        return self.reset_game(),{}

    def _get_info(self): # gym method
        raise NotImplementedError

    def _get_obs(self): # gym method
        info = {}
        return self.get_state(), self.reward_function(self.players[0]), self.done, info
    
    def get_ar_action_meaning(self, ar_action):
        raise NotImplementedError

    def get_state(self): # 38 max hand cards + 76 max board cards +2 turn scores + 1 win points
        hand_vector = np.zeros((38,3))
        for i in range(len(self.players[0].hand)):
            hand_vector[i] = self.players[0].hand[i].get_card_vector()

        board_vector = self.players[0].get_board() + self.players[1].get_board()  
        #logging.debug(f"Board: {board_vector}")
        #logging.debug(f"Hand: {hand_vector}")

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
        logging.debug(f"State:{self.state}")
        # Flatten the row scores and card hands into one long vector
        return self.state

    def reward_function(self,player):
        if player.idiot == "nn":
            player.reward+=player.turn_score + player.rounds_won*10
            logging.debug(f"REWARD:{player.name} {player.reward}")
        return player.reward

    def step(self, ar_action): # Training turn for gym
        self.play_turn(self.players[0],ar_action)
        self.play_turn(self.players[1])
        if self.players[0].passed and self.players[1].passed:
            self.display_round_result()
            self.round_number+=1
            self.update_win_points()
            for player in self.players:
                player.clear_rows()
            self.done = (self.players[0].rounds_won >= 2 or self.players[1].rounds_won >= 2)
        info = {} 
        if self.done:
            self.display_winner()
        return self.get_state(), self.reward_function(self.players[0]), self.done, self.done, info
    
    def play_turn(self,player,ar_action=None): # Normal turn
        player.turn_number+=1
        logging.debug(f"\n{player.name}'s Turn:")
        logging.debug(f"\nROUND: {self.round_number}")
        logging.debug(f"{player.name}'s hand: {len(player.hand)}")
        logging.debug(f"{player.name}'s turn: {player.turn_number}")
        logging.debug(f"AR action: {ar_action}")

        if len(player.hand)==0:
            player.passed = True
            logging.debug(f"{player.name} has no cards left and PASSED")
            logging.debug(f"{player.name} has no cards left and passed!")
        if not ar_action==None and not player.passed:
            logging.debug(f"AR_case")
            if ar_action == 39: # max Deck length + passing option
                player.passed = True
                logging.debug(f"AR passed")
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

    def draw_cards(self,player,num_cards=2):
        player.draw_hand(num_cards)
        return

    def play_round(self):
        # Draw hands for each player in the second and third rounds
        if self.round_number>3:
            logging.debug(Fore.RED+f"WTF THIS SHOULDN'T BE POSSIBLE - anyhow, enjoy the rest of your bugged game")
            logging.debug(f"ROUND OUT OF BOUNDS")
        if self.round_number > 1:
            for player in self.players:
                player.clear_rows()
                player.draw_hand(2)
                player.passed = False
                logging.debug(f"{player.name} drew 2 cards. Rows were cleared.")
        while True:
            # Take turns playing cards
            for player in self.players:
                self.play_turn(player)
                #self.render(self.players)
            # Display the current score
            logging.debug(f"\nCurrent Rows Won - {self.players[0].name}: {self.players[0].turn_score}, {self.players[1].name}: {self.players[1].turn_score}")
            if self.players[0].passed and self.players[1].passed:
                self.update_win_points()
                break

        self.display_round_result()
        self.round_number += 1
        self.done = (self.players[0].rounds_won >= 2 or self.players[1].rounds_won >= 2)

    def display_round_result(self) -> None:
        winner = ""
        if self.players[0].turn_score > self.players[1].turn_score:
            winner = self.players[0].name
        elif self.players[0].turn_score < self.players[1].turn_score:
            winner = self.players[1].name
        else:
            pass
            logging.debug("The round was a draw, one point to both players!")
        if winner:
            pass
            logging.debug(f"\n--- Player {winner} won round {self.round_number} ---")
        logging.debug(f"Current Round Score: {self.players[0].name}: {self.players[0].rounds_won}, {self.players[1].name}: {self.players[1].rounds_won}")

    def resolve_effect(self,player,card):
        if card.name=="DRAW1":
            player.draw_hand(1)
        elif card.name=="DRAW2":
            player.draw_hand(2)
        else:
            logging.debug("unknown effect, bro")
            pass

    def row_sort_order(self,row_card_tuple: tuple):
        row, _ = row_card_tuple

        if row == Row.SUPPORT:
            return 3
        elif row == Row.WISE:
            return 2
        elif row == Row.FRONT:
            return 1
        return 0

    def display_rows(self,deck: list[tuple], display_effects=False, backwards=False):
        colors = {Row.FRONT: Fore.RED, Row.WISE: Fore.WHITE, Row.SUPPORT: Fore.GREEN, Row.EFFECTS: Fore.MAGENTA}
        deck.sort(reverse=backwards, key=self.row_sort_order)
        for row, cards in deck:
            if row == Row.EFFECTS and not display_effects:
                continue
            logging.debug(colors[row],f"{row}:")
            logging.debug(f"{'+----------+ '*len(cards)}")
            logging.debug(f"{'|          | '*len(cards)}")
            logging.debug(" ".join([f"| {card.name}" + " "*(9-len(card.name))+"|" for card in cards]))
            logging.debug(" ".join([f"| Str: {card.strength}   |" for card in cards]))
            logging.debug(f"{'|          | '*len(cards)}")
            logging.debug(f"{'+----------+ '*len(cards)}")
            logging.debug(Fore.WHITE)

    def render(self,players): # gym required method 
        logging.debug(f"\nCurrent Score - Round: {self.round_number} Turn Score:{self.players[0].name}: {self.players[0].turn_score}\t,\t{self.players[1].name}: {self.players[1].turn_score}")
        logging.debug("\n------ Current Board ------")
        logging.debug("###############################################################################################################")
        for player in players:
            # Display Player 1's Board
            logging.debug(f"{player.name}'s Board:")
            self.display_rows(list(player.rows.items()), False, player==players[0])
            logging.debug("###############################################################################################################")

    def display_sum(self,player):
        logging.debug(f"{player.name}'s Current Sums:")
        for row, cards in player.rows.items():
            logging.debug("%s: %i", row, sum(card.strength for card in cards))
            

    def update_win_points(self):
        if self.players[0].turn_score >= self.players[1].turn_score:
            self.players[0].rounds_won+=1
        if self.players[1].turn_score >= self.players[0].turn_score:
            self.players[1].rounds_won+=1
        return [self.players[0].rounds_won, self.players[1].rounds_won, 0]

    def update_row_scores(self):
        player1_score = 0
        player2_score = 0
        for row in self.players[0].rows:
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
        self.players[0].turn_score = player1_score # How many rows are won by this player at the time the function is called
        self.players[1].turn_score = player2_score # How many rows are won by this player at the time the function is called
        return 
    
    def display_row_scores(self):
        logging.debug(
            f"{self.players[0].name}'s wins {self.players[0].turn_score} rows\n"\
            f"{self.players[1].name}'s wins {self.players[1].turn_score} rows"
            )
    
    def display_winner(self):
        winner = ""
        if self.players[0].rounds_won < self.players[1].rounds_won:
            winner = self.players[1].name
        elif self.players[0].rounds_won > self.players[1].rounds_won:
            winner = self.players[0].name
        if winner:
            logging.debug(f"{winner} won the game!")
        else:
            logging.debug("Draw - No one won the game")
        time_stamp = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime())
        logging.debug(f"{winner} won the game!")
        logging.debug(f"\nGame ended - {time_stamp}")
        return













'''
    def __init__(self, training=False):
        super().__init__()
        time_stamp = time.strftime("%d%m%Y_%H%M%S", time.localtime())
        logging.basicConfig(level=logging.debug, filename='logs/'+str(time_stamp)+'.log', filemode='w', format='%(message)s')
        time_stamp = time.strftime("%d/%m/%Y - %H:%M:%S", time.localtime())
        self.done = False
        if training:
            logging.debug(f"Training started - {time_stamp}")
            self.players=self.initialize_game(training)
        else:
            logging.debug(f"Game started - {time_stamp}")
            self.players=self.initialize_game()
        # Display the decks
        for player in self.players:
            player.display_deck()
        if training:           
            self.action_space = Discrete(39)
            for player in self.players:
                player.draw_hand(10,True)
            self.observation_space =  Box(low=0, high=38, shape=(234,), dtype=np.uint8) # self.get_state() #38 max hand cards + 76 max board cards +2 turn scores + 1 win points  
        else:
            self.game_loop()# Start game loop

    def initialize_game(self,training=False):
        utils.clear_screen()
        self.round_number=1
        if not training:
            while True:
                choice = utils.get_user_input("Choose a game mode (type '1' to play yourself or '2' to simulate): ", ['1', '2'])
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
            logging.debug(f"NN Player activated")
            player1 = ArtificialRetardation("Neural Nutjob", "nn")
            player2 = ArtificialRetardation("Trained Monkey", "pc")
        
        # Build decks for each player
        booster_instance = Booster()
        player1.build_deck(booster_instance)
        player2.build_deck(booster_instance)
        
        player1.draw_hand(10,True)
        player2.draw_hand(10,True)
        logging.debug(f"Players drew 10 cards from their shuffled deck.")
        return player1, player2

    def game_loop(self):
      # Play three rounds
        self.round_number = 1       
        while not self.done:  # Using 'not' to check the condition and simplify the loop condition
            self.play_round()
        self.display_winner()
        self.reset_game() 
'''
