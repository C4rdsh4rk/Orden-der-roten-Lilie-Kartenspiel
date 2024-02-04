import os
from row import Row
import gymnasium as gym
from gymnasium import spaces
from colorama import Fore
import utils
from player import Player, Human, ArtificialRetardation
from cards import Booster
import logging
import time

class game(gym.Env):
    def __init__(self):
        time_stamp = time.strftime("%d%m%Y_%H%M%S", time.localtime())
        logging.basicConfig(level=logging.DEBUG, filename=str(time_stamp)+'.log', filemode='w', format='%(message)s')
        time_stamp = time.strftime("%d/%m/%Y - %H:%M:%S", time.localtime())
        logging.debug(f"Game started - {time_stamp}")
        self.players=self.initialize_players()
        # Build decks for each player
        booster_instance = Booster()
        for player in self.players:
            player.build_deck(booster_instance)
        # Display the decks
        for player in self.players:
            player.display_deck()
        self.round_num=0
        self.game_loop()# Start game loop

    def _get_obs_AR(self): # gym env method used in step and reset
        return

    def _get_info_AR(self): # gym env method
        return

    def reset_game(self,winner): #
        print(f"{winner.name} won the game!")
        logging.debug(f"{winner.name} won the game!")
        time_stamp = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime())
        logging.debug(f"Game ended - {time_stamp}")
        for player in self.players:
            player.deck = []
            player.hand   = []
            player.score_vector = []
            player.passed = False
            player.rounds_won = 0
            player.clear_rows()
            #self.__init__()# infinite game loop
            self.round_num=5
            
    def step(self):
        print(f"\n--- Round {self.round_num} ---")
        # Draw hands for each player in the second and third rounds
        for player in self.players:
            if self.round_num > 1:
                player.draw_hand(2)
                player.passed = False
                player.clear_rows()
            else:
                player.draw_hand(10,True)
            logging.debug(f"{player.name} drew cards")
        while(True):
            # Take turns playing cards
            for player in self.players:
                # skip player if he has passed
                if player.passed:
                    continue
                print(f"\n{player.name}'s Turn:")
                player.play_card()
                self.display_board(self.players)
                player.display_hand()
            self.check_score()
            # Display the current score
            print(f"\nCurrent Score - {self.players[0].name}: {self.players[0].turn_score},{self.players[1].name}: {self.players[1].turn_score}")
            if(self.check_winning()):
                break
        return

    def initialize_players(self):
        utils.clear_screen()
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

    def display_board(self,players):
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

    def check_winning(self):
        if(self.players[0].passed == True and self.players[1].passed == True):
            if self.players[0].turn_score>self.players[1].turn_score:
                self.players[0].rounds_won+=1
            elif self.players[1].turn_score>self.players[0].turn_score:
                self.players[1].rounds_won+=1
            else:
                self.players[0].rounds_won+=1
                self.players[1].rounds_won+=1 
            if (self.players[0].rounds_won>=2 and self.players[1].rounds_won<self.players[0].rounds_won):
                winner=self.players[0]
                self.reset_game(winner)
            elif (self.players[1].rounds_won>=2 and self.players[0].rounds_won<self.players[1].rounds_won):
                winner=self.players[1]
                self.reset_game(winner)
            return True
        else:
            return False

    def check_score(self):
        player1_score = 0
        player2_score = 0
        for row in self.players[0].rows:
            if self.players[0].get_row_sum(row) >= self.players[1].get_row_sum(row):
                player1_score += 1
            if self.players[0].get_row_sum(row) <= self.players[1].get_row_sum(row):
                player2_score += 1
        self.players[0].turn_score = player1_score
        self.players[1].turn_score = player2_score
        print(f"\n{self.players[0].name} won {self.players[0].rounds_won} rounds\t",end="")
        print(f"{self.players[1].name} won {self.players[1].rounds_won} rounds")
        logging.debug(f"{self.players[0].name} won {self.players[0].rounds_won} rounds\n{self.players[1].name} won {self.players[1].rounds_won} rounds")
        logging.debug(f"{self.players[0].name}'s score: {self.players[0].turn_score}\n{self.players[1].name}'s score: {self.players[1].turn_score}")
        return player1_score, player2_score
    
    def game_loop(self):
        # Play three rounds
        self.round_num=1
        while(self.round_num<4):
            self.step()
            self.round_num+=1