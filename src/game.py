import logging
import time
from colorama import Fore
from gymnasium import Env
from gymnasium.spaces import Discrete, Box
from src.row import Row
import src.utils as utils
from src.player import Human, ArtificialRetardation
from src.cards import Booster

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
        if not training:
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
    
    def reset_game(self):
        for player in self.players:
            player.deck = []
            player.hand = []
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
        self.players[0].display_hand()
        while(True):
            # Take turns playing cards
            for player in self.players:
                # skip player if he has passed
                if player.passed:
                    continue
                print(f"\n{player.name}'s Turn:")
                player.play_card()
                self.render(self.players)
                if player.passed:
                    print(f"{player.name} passed!")
                    continue
            self.render(self.players)
            self.players[0].display_hand()
            self.update_row_scores()
            self.display_row_scores()
            # Display the current score
            print(f"\nCurrent Rows Won - {self.players[0].name}: {self.players[0].turn_score},{self.players[1].name}: {self.players[1].turn_score}")
            if(self.players[0].passed and self.players[1].passed):
                self.update_win_points()
                break
        self.display_round_result()
        
        return self.players#, self.check_winning()# gym needs return game state, reward(?), done and info

    def display_round_result(self) -> None:
        winner = ""
        if self.players[0].turn_score > self.players[1].turn_score:
            winner = self.players[0].name
        elif self.players[0].turn_score < self.players[1].turn_score:
            winner = self.players[1].name
        else:
            print("The round was a draw, one point to both players!")
        if winner:
            print(f"\n--- Player {winner} won round {self.round_num} ---")
        print(f"Current Round Score: {self.players[0].name}: {self.players[0].rounds_won}, {self.players[1].name}: {self.players[1].rounds_won}")


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

    def render(self,players): # gym required method 
        print(f"\nCurrent Score - {self.players[0].name}: {self.players[0].turn_score}\t,\t{self.players[1].name}: {self.players[1].turn_score}")
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
            if row == Row.EFFECTS:
                continue
            if self.players[0].get_row_sum(row) >= self.players[1].get_row_sum(row):
                player1_score += 1
            if self.players[0].get_row_sum(row) <= self.players[1].get_row_sum(row):
                player2_score += 1
        self.players[0].turn_score = player1_score
        self.players[1].turn_score = player2_score
    
    def display_row_scores(self):
        logging.debug(
            f"{self.players[0].name}'s wins {self.players[0].turn_score} rows\n"\
            f"{self.players[1].name}'s wins {self.players[1].turn_score} rows"
        )
    
    def game_loop(self):
        # Play three rounds
        self.round_num=1
        while(self.players[0].rounds_won<3 and self.players[1].rounds_won<3):
            self.step()
            self.round_num+=1
        self.display_winner()
        self.reset_game()