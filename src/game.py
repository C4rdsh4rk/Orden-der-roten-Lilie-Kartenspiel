import logging
import time
from colorama import Fore
from gymnasium import Env
from gymnasium.spaces import Discrete, Box
from src.row import Row
import src.utils as utils
from src.player import Human, ArtificialRetardation
from src.cards import Booster
import numpy as np

class game(Env): # Env -> gym Environment
    def __init__(self, training=False):
        time_stamp = time.strftime("%d%m%Y_%H%M%S", time.localtime())
        logging.basicConfig(level=logging.DEBUG, filename='logs/'+str(time_stamp)+'.log', filemode='w', format='%(message)s')
        time_stamp = time.strftime("%d/%m/%Y - %H:%M:%S", time.localtime())
        logging.debug(f"Game started - {time_stamp}")
        self.done = False
        if training:
            self.players=self.initialize_players(training)
        else:
            self.players=self.initialize_players()
        # Build decks for each player
        booster_instance = Booster()
        for player in self.players:
            player.build_deck(booster_instance)
        # Display the decks
        for player in self.players:
            player.display_deck()
        self.round_number=1
        if training:
            self.update_win_points()
            self.action_space = Discrete(40)
            state_dict = {
                'player_0_row_score': np.concatenate([np.array([[0],[0],[0]])]).flatten(),
                'player_0_rounds_won': np.array([0]),  # Use np.array instead of np.concatenate
                'player_1_row_score': np.concatenate([np.array([[0],[0],[0]])]).flatten(),
                'player_1_rounds_won': np.array([0]),  # Use np.array instead of np.concatenate
                'player_0_passed': np.array([0]),  # Use np.array instead of np.concatenate
                'player_1_passed': np.array([0])   # Use np.array instead of np.concatenate
                        }
            state = np.concatenate([np.array(value) for value in state_dict.values()])
            self.observation_space = np.array(state)
            for player in self.players:
                player.draw_hand(10,True)
        else:
            self.game_loop()# Start game loop

    def display_winner(self):
        winner = ""
        if self.players[0].rounds_won < self.players[1].rounds_won:
            winner = self.players[1].name
        elif self.players[0].rounds_won > self.players[1].rounds_won:
            winner = self.players[0].name
        if winner:
            print(f"{winner} won the game!")
        else:
            print("Draw - No one won the game")
        time_stamp = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime())
        logging.debug(f"Game ended - {time_stamp}")
        return
    
    def reset_game(self):
        for player in self.players:
            player.deck = []
            player.hand = []
            player.passed = False
            player.rounds_won = 0
            player.clear_rows()
            #self.__init__()# infinite game loop
            self.round_number=5

    def close(self): # gym method
        # Implement any necessary cleanup
        raise NotImplementedError

    def reset(self): # gym method
        self.reset_game()
        return True

    def _get_info(self): # gym method
        return {
        }

    def _get_obs(self): # gym method
        return {
        }
    
    def get_ar_action_meaning(self, ar_action):
        pass

    def reward_function(self,player):
        if player.idiot == "nn":
            player.reward+=player.turn_score + player.rounds_won*10
            logging.debug(f"REWARD:{player.name} {player.reward}")
        return player.reward
    
    def step(self,ar_action): # Training turn for gym
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
        ''' np.array([
            np.concatenate(self.players[0].hand),
            np.concatenate(self.players[0].deck),
            np.concatenate([np.array(value) for value in self.players[0].rows.values()]),
            np.concatenate([np.array(value) for value in self.players[1].rows.values()]),
            self.players[0].turn_number,
            self.round_number
        ])'''
        state_dict = {
                'player_0_row_score': np.concatenate([np.array([[0],[0],[0]])]).flatten(),
                'player_0_rounds_won': np.array([0]),  # Use np.array instead of np.concatenate
                'player_1_row_score': np.concatenate([np.array([[0],[0],[0]])]).flatten(),
                'player_1_rounds_won': np.array([0]),  # Use np.array instead of np.concatenate
                'player_0_passed': np.array([0]),  # Use np.array instead of np.concatenate
                'player_1_passed': np.array([0])   # Use np.array instead of np.concatenate
                }
        '''{
            'player_0_row_score': np.concatenate([np.array(value) for value in self.players[0].row_score.values()]).flatten(),
            'player_0_rounds_won': np.concatenate(self.players[0].rounds_won).flatten(),
            'player_1_row_score': np.concatenate([np.array(value) for value in self.players[1].row_score.values()]).flatten(),
            'player_1_rounds_won': np.concatenate(self.players[1].rounds_won).flatten(),
            'player_0_passed': np.concatenate(self.players[0].passed).flatten(),
            'player_1_passed': np.concatenate(self.players[1].passed).flatten()
        }'''
        state = state = np.concatenate([np.array(value) for value in state_dict.values()]) # Row and winning score are relevant state
        #logging.debug(f"{info},{state}")
        if self.done:
            self.display_winner()
        return state, self.reward_function(self.players[0]), self.done, info
    
    def play_turn(self,player,ar_action=None): # Normal turn
        player.turn_number+=1
        logging.debug(f"ROUND: {self.round_number}")
        logging.debug(f"{player.name}'s hand: {len(player.hand)}")
        logging.debug(f"{player.name}'s turn: {player.turn_number}")
        logging.debug(f"AR action: {ar_action}")

        if len(player.hand)==0:
            player.passed = True
            logging.debug(f"{player.name} has no cards left and PASSED")
        if not ar_action==None and not player.passed:
            logging.debug(f"AR_case")
            if ar_action == 40:
                player.passed = True
                logging.debug(f"AR passed")
            elif ar_action:
                played_card = player.play_card()
                logging.debug(f"AR played card: {played_card}")
        if not player.passed and ar_action==None:
            player.make_pass_choice()
            print(f"\n{player.name}'s Turn:")
            played_card = player.play_card()
            logging.debug(f"CPU played card: {played_card}")
            self.render(self.players)
            self.update_row_scores()
        return

    def draw_cards(self,player,num_cards=2):
        player.draw_hand(num_cards)
        return

    def play_round(self):
        # Draw hands for each player in the second and third rounds
        if self.round_number>3:
            print(Fore.RED+f"WTF THIS SHOULDN'T BE POSSIBLE - anyhow, enjoy the rest of your bugged game")
            logging.debug(f"ROUND OUT OF BOUNDS")
        if self.round_number > 1:
            for player in self.players:
                player.draw_hand(2)
                player.passed = False
                player.clear_rows()
                logging.debug(f"{player.name} drew 2 cards.")
        else:
            for player in self.players:
                player.draw_hand(10,True)
                logging.debug(f"{player.name} drew 10 cards.")

        while True:
            # Take turns playing cards
            for player in self.players:
                print(f"\n{player.name}'s Turn:")
                self.play_turn(player)
                self.render(self.players)
            # Display the current score
            print(f"\nCurrent Rows Won - {self.players[0].name}: {self.players[0].turn_score}, {self.players[1].name}: {self.players[1].turn_score}")
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
            print("The round was a draw, one point to both players!")
        if winner:
            print(f"\n--- Player {winner} won round {self.round_number} ---")
        print(f"Current Round Score: {self.players[0].name}: {self.players[0].rounds_won}, {self.players[1].name}: {self.players[1].rounds_won}")

    def initialize_players(self,training=False):
        utils.clear_screen()
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
        return player1, player2

    def resolve_effect(self,player,card):
        if card.name=="DRAW1":
            player.draw_hand(1)
        elif card.name=="DRAW2":
            player.draw_hand(2)
        else:
            print("unknown effect, bro")

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
            print(colors[row],f"{row.value}:")
            print(f"{'+----------+ '*len(cards)}")
            print(f"{'|          | '*len(cards)}")
            print(" ".join([f"| {card.name}" + " "*(19-len(card.name))+"|" for card in cards]))
            print(" ".join([f"| Str: {card.strength}   |" for card in cards]))
            print(f"{'|          | '*len(cards)}")
            print(f"{'+----------+ '*len(cards)}")
            print(Fore.WHITE)

    def render(self,players): # gym required method 
        print(f"\nCurrent Score - Round: {self.round_number} Turn Score:{self.players[0].name}: {self.players[0].turn_score}\t,\t{self.players[1].name}: {self.players[1].turn_score}")
        print("\n------ Current Board ------")
        print("###############################################################################################################")
        for player in players:
            # Display Player 1's Board
            print(f"{player.name}'s Board:")
            self.display_rows(list(player.rows.items()), False, player==players[0])
            print("###############################################################################################################")

    def display_sum(self,player):
        print(f"{player.name}'s Current Sums:")
        for row, cards in player.rows.items():
            print(f"{row}: {sum(card.strength for card in cards)}")

    def update_win_points(self):
        if self.players[0].turn_score >= self.players[1].turn_score:
            self.players[0].rounds_won+=1
        if self.players[1].turn_score >= self.players[0].turn_score:
            self.players[1].rounds_won+=1

    def update_row_scores(self):
        player1_score = 0
        player2_score = 0
        for row in self.players[0].rows:
            self.players[0].row_score[row] = self.players[0].get_row_sum(row)
            self.players[1].row_score[row] = self.players[1].get_row_sum(row)
            #print(self.players[0].row_score[row]) # DEBUG
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
    
    def display_row_scores(self):
        logging.debug(
            f"{self.players[0].name}'s wins {self.players[0].turn_score} rows\n"\
            f"{self.players[1].name}'s wins {self.players[1].turn_score} rows"
        )
    
    def game_loop(self):
      # Play three rounds
        self.round_number = 1
        for player in self.players:
            self.draw_cards(player, 8)  # Draw first 8 hand cards (+ 2 in first round later)
        
        while not self.done:  # Using 'not' to check the condition and simplify the loop condition
            self.play_round()
        self.display_winner()
        self.reset_game() 
