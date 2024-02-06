import logging
import time
from colorama import Fore
from gymnasium import Env
from gymnasium.spaces import Discrete, Box
from src.row import Row
import src.utils as utils
from src.player import Human, ArtificialRetardation
from src.cards import Booster
from src.display import CardTable, Live


class game(Env): # Env -> gym Environment
    def __init__(self, training=False):
        time_stamp = time.strftime("%d%m%Y_%H%M%S", time.localtime())
        logging.basicConfig(level=logging.DEBUG, filename='logs/'+str(time_stamp)+'.log', filemode='w', format='%(message)s')
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
        self.display = CardTable()
        if not training:
            self.game_loop()# Start game loop
    

    def update_player_info(self, player, bottom_player) -> None:
        self.display.set_player_info(
            player.name,
            len(player.deck),
            len(player.graveyard),
            player.last_move,
            player.turn_score,
            player.rounds_won,
            bottom_player
        )

    def display_winner(self):
        winner = ""
        if self.players[0].rounds_won < self.players[1].rounds_won:
            winner = self.players[1].name
        elif self.players[0].rounds_won > self.players[1].rounds_won:
            winner = self.players[0].name
        if winner:
            self.display.write_message(f"{winner} won the game!")
        else:
            self.display.write_message("Draw - No one won the game")
        time_stamp = time.strftime("%d/%m/%Y, %H:%M:%S", time.localtime())
        logging.debug(f"Game ended - {time_stamp}")
    
    def reset_game(self):
        for player in self.players:
            player.deck = []
            player.hand = []
            player.score_vector = []
            player.passed = False
            player.rounds_won = 0
            player.clear_rows()
            player.last_move = "Not move"
            #self.__init__()# infinite game loop
            self.round_num=5

    def reward_function(self):
        for player in self.players:
            if player.idiot == "pc":
                player.reward+=player.turn_score
                logging.debug(f"REWARD:{player.name} {player.reward}")
        return
    
    def play_round(self):
        # Draw hands for each player in the second and third rounds
        for player in self.players:
            if self.round_num > 1:
                player.draw_hand(2)
                player.passed = False
                player.clear_rows()
            else:
                player.draw_hand(10,True)
            logging.debug("%s drew cards", player.name)
            self.display.update_card_hand(player.hand, player==self.players[0])
            self.update_player_info(player, player==self.players[0])
        while(True):
            # Take turns playing cards
            for player in self.players:
                # skip player if he has passed
                if player.passed:
                    continue
                player.play_card(self.display)
            self.update_row_scores()
            # update view
            for player in self.players:
                bottom_player = player == self.players[0]
                self.display.set_player_cards(list(player.rows.items()), bottom_player)
                self.update_player_info(player, bottom_player)
                self.display.update_card_hand(player.hand, bottom_player)
            logging.debug("%s's wins %s rows", self.players[0].name, self.players[0].turn_score)
            logging.debug("%s's wins %s rows", self.players[1].name, self.players[1].turn_score)
            if(self.players[0].passed and self.players[1].passed):
                self.update_win_points()
                break
        winner = self.get_round_winner()
        if len(winner) == 2:
            win_message = "Draw! Both players receive a point!"
        else:
            win_message = f"{winner[0].name} wins the round!"
        self.display.write_message(win_message)
        for player in self.players:
            bottom_player = player == self.players[0]
            self.update_player_info(player, bottom_player)
        time.sleep(2)
        self.display._setup_board()
        self.reset_row_scores()
        return self.players#, self.check_winning()# gym needs return game state, reward(?), done and info

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
    
    def reset_row_scores(self):
        for player in self.players:
            player.turn_score = 0
            player.turn_score = 0

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

    def get_round_winner(self) -> list:
        if self.players[0].turn_score > self.players[1].turn_score:
            return [self.players[0]]
        elif self.players[1].turn_score > self.players[0].turn_score:
            return [self.players[1]]
        else:
            return [self.players[0], self.players[1]]

    def update_win_points(self):
        if self.players[0].turn_score >= self.players[1].turn_score:
            self.players[0].rounds_won+=1
        if self.players[1].turn_score >= self.players[0].turn_score:
            self.players[1].rounds_won+=1

    def update_row_scores(self):
        player1_score = 0
        player2_score = 0
        for row in self.players[0].rows:
            if row == Row.EFFECTS:
                continue
            if self.players[0].get_row_sum(row) >= self.players[1].get_row_sum(row):
                player1_score += 1
            if self.players[0].get_row_sum(row) <= self.players[1].get_row_sum(row):
                player2_score += 1
        self.players[0].turn_score = player1_score
        self.players[1].turn_score = player2_score
    
    def game_loop(self):
        # setup display
        with Live(self.display.layout, refresh_per_second=4):
            self.display.set_player_info(self.players[0].name, len(self.players[0].deck), len(self.players[0].graveyard), "No move", 0, 0, True)
            self.display.set_player_info(self.players[1].name, len(self.players[1].deck), len(self.players[1].graveyard), "No move", 0, 0, False)
            # Play three rounds
            self.round_num = 1
            while(self.players[0].rounds_won<3 and self.players[1].rounds_won<3):
                self.play_round()
                self.round_num+=1
            self.display_winner()
            self.reset_game()