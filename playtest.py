import random
import os
from colorama import Fore
from enum import Enum

class Row(Enum):
    FRONT = "FRONT"
    WISE = "WISE"
    SUPPORT = "SUPPORT"
    EFFECTS = "EFFECTS"
    ANY = "ANY"

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear') # Clear screen for Linux and Windows

class Card:  
    def __init__(self, name, strength, row_restriction=None):
        self.name = name
        self.type = row_restriction
        self.strength = strength
    
    def __str__(self):
        return f"{self.name} (Str: {self.strength}, Row: {self.type})"

class Booster:
    def __init__(self):
        self.available_strength = [1,2,3,4,5]
        self.available_cards_weights = [0.3, 0.3, 0.3, 0.05, 0.05] # Probabilities
        self.strength_weights = [0.35, 0.25, 0.2, 0.15, 0.05] # Probabilities
        self.available_effects = ["DRAW1","DRAW2"] # Add effects here TODO match number to effect string with rule check
        self.available_cards = [
                            Card(Fore.RED + "KNIGHT"+Fore.WHITE, random.choices(self.available_strength,self.strength_weights)[0], Row.FRONT),
                            Card(Fore.WHITE +"CLERIC"+Fore.WHITE, random.choices(self.available_strength,self.strength_weights)[0], Row.WISE),
                            Card(Fore.GREEN +"HEALER"+Fore.WHITE, random.choices(self.available_strength,self.strength_weights)[0], Row.SUPPORT),
                            Card(Fore.YELLOW +"HERO"+Fore.WHITE, random.choices(self.available_strength,self.strength_weights)[0], Row.ANY), # Can be played in any row
                            Card(Fore.MAGENTA +random.choice(self.available_effects)+Fore.WHITE, 1, Row.EFFECTS), # Can be played in any row
                            ]
        
    def open(self,size):
        return random.choices(self.available_cards, self.available_cards_weights, k=size)

class Player:
    def __init__(self, name, idiot):
        self.name = name
        self.idiot = idiot
        self.deck = []
        self.hand = [] # Add a hand attribute
        self.passed = False
        self.rows = {
            Row.FRONT: [],
            Row.WISE: [],
            Row.SUPPORT: [],
            Row.EFFECTS: [],
        }

    def build_deck(self, booster):
        loop_flag = True
        while loop_flag:
            #clear_screen()
            print(f"{self.name} is building his deck")
            booster_pack = booster.open(5) # Create a Boosterpack with 5 random cards
            if self.idiot == "human":
                print("Choose cards for your deck")
                print("Available Cards:\n" + Fore.WHITE)
                print(f"{'+----------+ '*len(booster_pack)}")
                print(f"{'|          | '*len(booster_pack)}")
                print(" ".join([f"| {card.name}" + " "*(19-len(card.name))+"|" for card in booster_pack]))
                print(" ".join([f"| Str: {card.strength}   |" for card in booster_pack]))
                print(f"{'|          | '*len(booster_pack)}")
                print(f"{'+----------+ '*len(booster_pack)}")

                self.display_deck()

                choice = get_user_input(
                    f"Enter a number 1-{len(booster_pack)} to choose a card\n",
                    [str(number) for number in range(1, len(booster_pack)+1)]
                )
                choice = int(choice)
                chosen_card = booster_pack[choice - 1]
            else:  # cpu chooses a random card
                chosen_card = random.choice(booster_pack)
            # deck building checks
            if sum(card.strength for card in self.deck) + chosen_card.strength <= 38:
                self.deck.append(chosen_card)
            elif sum(card.strength for card in self.deck) == 38:
                break
            else:
                print("Value exceeds maximum deck strength, try again. (not your fault)")
                # If adding the card exceeds the total strength constraint, try another card
                continue

    def draw_hand(self, num_cards=10,shuffle=False):
        if shuffle:
            random.shuffle(self.deck)
        # Draw cards from the deck
        self.hand = self.deck[:num_cards]
        # Remove drawn cards from the deck
        self.deck = [card for card in self.deck if card not in self.hand]

    def display_deck(self):
        #clear_screen()
        print(f"{self.name}'s Deck:")
        for card in self.deck:
            print(f"{card.name} ({card.strength})")

    def display_hand(self):
        #clear_screen()
        print(f"{self.name}'s Hand:")
        card_number=1
        for card in self.hand:
            print(f"[{card_number}]{card.name} ({card.strength})", end="")
            card_number+=1

def resolve_effect(player,card):
    if card.name=="DRAW1":
        player.draw_hand(1)
    elif card.name=="DRAW2":
        player.draw_hand(2)
    else:
        print("unknown effect, bro")

def play_card(player, card):
    if card.type!=Row.EFFECTS or card.type!=Row.ANY:
        player.rows[card.type].append(card)
        print(f"{player.name}: Played {card.name} with strength {card.strength} in {card.type}.")
    elif card.type==None:
        row = get_user_input("Which row?\n(1: FRONT)\n(2: WISE)\n(3: SUPPORT)", [1, 2, 3])
        row-=1
        player.rows[row].append(card)
    else:
        player.rows[card.type].append(card)
        print(f"{player.name}: Played effect {card.name}.")
        resolve_effect(player,card)

    return True # TODO implement rule checks and return false if rule violated

def row_sort_order(row_card_tuple: tuple):
    row, _ = row_card_tuple

    if row == Row.SUPPORT:
        return 3
    elif row == Row.WISE:
        return 2
    elif row == Row.FRONT:
        return 1
    return 0

def display_rows(deck: list[tuple], display_effects=False, backwards=False):
    colors = {Row.FRONT: Fore.RED, Row.WISE: Fore.WHITE, Row.SUPPORT: Fore.GREEN, Row.EFFECTS: Fore.MAGENTA}
    deck.sort(reverse=backwards, key=row_sort_order)
    for row, cards in deck:
        if row == Row.EFFECTS and not display_effects:
            continue
        print(colors[row],f"{row.value}:")
        print(f"{'+----------+ '*len(row)}")
        print(f"{'|          | '*len(row)}")
        print(" ".join([f"| {card.name}" + " "*(19-len(card.name))+"|" for card in row]))
        print(" ".join([f"| Str: {card.strength}   |" for card in row]))
        print(f"{'|          | '*len(row)}")
        print(f"{'+----------+ '*len(row)}")
        print(Fore.WHITE)

def display_board(players):
    print("\n------ Current Board ------")
    print("###############################################################################################################")
    for player in players:
        # Display Player 1's Board
        print(f"{player.name}'s Board:")
        display_rows(list(player.rows.items()), False, player==players[0])
        print("###############################################################################################################")

def display_sum(player):
    print(f"{player.name}'s Current Sums:")
    for row, cards in player.rows.items():
        print(f"{row}: {sum(card.strength for card in cards)}")

def check_winner(players):
    player1_score = 0
    player2_score = 0
    for row in players[0].rows:
        if sum(card.strength for card in players[0].rows[row]) >= sum(card.strength for card in players[1].rows[row]):
            player1_score += 1
        if sum(card.strength for card in players[0].rows[row]) <= sum(card.strength for card in players[1].rows[row]):
            player2_score += 1
    return player1_score, player2_score

def initialize_players():
    clear_screen()
    while True:
        choice = get_user_input("Choose a game mode (type '1' to play yourself or '2' to simulate): ", ['1', '2'])
        if choice == '1':
            name = input("Enter your name: ").lower()
            player1 = Player(name, "human")
            player2 = Player("Trained Monkey", "pc")
            break
        else:
            player1 = Player("Trained Monkey", "pc")
            player2 = Player("Clueless Robot", "pc")
            break
    return player1, player2
    
def get_user_input(prompt, valid_choices):
    while True:
        user_input = input(prompt)
        if user_input in valid_choices:
            return user_input
        else:
            print(f"Invalid input. Please enter one of {valid_choices}.")

def game_loop(players):
    # Play three rounds
    for round_num in range(1, 4):
        print(f"\n--- Round {round_num} ---")
        # Draw hands for each player in the second and third rounds
        for player in players:
            if round_num > 1:
                player.draw_hand(2)
                player.passed = False
            else:
                player.draw_hand(10,True)
        while(True):
            # Take turns playing cards
            for player in players:
                while True:
                    print(f"\n{player.name}'s Turn:")
                    # Display the current board and sums after each turn
                    valid_card = ["{:1d}".format(x) for x in range(len(player.hand))]
                    valid_choices = valid_card + ['p'] 
                    if player.idiot == "human":
                        display_board(players)             
                        player.display_hand()
                        #valid_card = list(range(len(player.hand)))
                        action = get_user_input("Enter 'p' to pass or number of card to play: ", valid_choices)
                    else:
                        action = random.choice(valid_choices) # Bot chooses move
                    if action == 'p':
                        print(f"{player.name} passed.")
                        player.passed = True
                        break
                    else:
                        play_card_success = play_card(player, player.hand[int(action)])
                    if play_card_success:
                        break
            player1_score, player2_score = check_winner(players)
            # Display the current score
            print(f"Current Score - Player 1: {player1_score}, Player 2: {player2_score}")
            if(players[0].passed == True and players[1].passed == True):                
                break
            


def main():
    player1,player2=initialize_players()
    players = player1,player2 # maybe merge
    # Build decks for each player
    booster_instance = Booster()

    for player in players:
        player.build_deck(booster_instance)

    # Display the decks
    for player in players:
        player.display_deck()
        
    game_loop(players)


if __name__ == "__main__":
    main()