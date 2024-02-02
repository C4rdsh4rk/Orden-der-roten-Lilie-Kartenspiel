import random
import os
from colorama import Fore
class Card:
    def __init__(self, name, strength, row_restriction=None):
        self.name = name
        self.type = row_restriction
        self.strength = strength

class Player:
    def __init__(self, name, idiot):
        self.name = name
        self.idiot = idiot
        self.deck = []
        self.rows = {
            "FRONT": [],
            "GELEHRTE": [],
            "UNTERSTUETZUNG": [],
        }
    def build_deck(self):
        loop_flag = True
        while loop_flag:
            os.system('cls')
            print(f"{self.name} is building his deck")
            available_cards = [
                Card(Fore.RED + "RITTER  "+Fore.WHITE, random.randint(1, 5), "FRONT"),
                Card(Fore.WHITE +"KLERIKER"+Fore.WHITE, random.randint(1, 5), "GELEHRTE"),
                Card(Fore.GREEN +"HEILER  "+Fore.WHITE, random.randint(1, 5), "UNTERSTUETZUNG"),
                Card(Fore.YELLOW +"HELD    "+Fore.WHITE, random.randint(2, 5)),  # Can be played in any row
            ]
            if self.idiot=="human":
                while True:
                    print(f"Choose cards for your deck")
                    print(f"Available Cards:")
                    for card in available_cards:
                        print(f"+----------+ ", end="")     
                    print()  # Move to the next line for the next row
                    for card in available_cards:
                        print(f"|          | ", end="")
                    print()  # Move to the next line for the next row
                    for card in available_cards:
                        print(f"| {card.name} | ", end="")
                    print()  # Move to the next line for the next row
                    for card in available_cards:
                        print(f"| Str: {card.strength}   | ", end="")
                    print()  # Move to the next line for the next row
                    for card in available_cards:
                        print(f"|          | ", end="")
                    print()  # Move to the next line for the next row
                    for card in available_cards:
                        print(f"+----------+ ", end="")
                    print()  # Move to the next line for the next row

                    print(f"\n{self.name}'s Deck:")
                    display_rows(self.rows.items())

                    choice = input("Enter a number 1-4 to choose a card\n").lower()
                    choice = int(choice)
                    if choice>4 or choice<1:
                        os.system('cls')
                        print(Fore.RED + "Invalid choice you muppet!")
                    else:
                        chosen_card = available_cards[choice-1]  
                        break
            else: #cpu chooses a random card
                chosen_card = random.choice(available_cards)
            #deck building checks
            if sum(card.strength for card in self.deck) + chosen_card.strength <= 38:
                self.deck.append(chosen_card)
            if sum(card.strength for card in self.deck)==38:
                break
            else:
                # If adding the card exceeds the total strength constraint, try another card
                continue

    def display_deck(self):
        os.system('cls')
        print(f"{self.name}'s Deck:")
        for card in self.deck:
            print(f"{card.name} ({card.strength})")

def play_card(player, card, row):
    if card.type and row != card.type and card.type is not None:
        print(f"{player.name}: Cannot play {card.name} in {row}. Must be played in {card.type}.")
    else:
        player.rows[row].append(card)
        print(f"{player.name}: Played {card.name} with strength {card.strength} in {row}.")

def display_rows(deck):
    for row, cards in deck:
        print(f"{row}: ")
        for card in cards:
            print(f"+----------+ ", end="")     
        print()  # Move to the next line for the next row
        for card in cards:
            print(f"|          | ", end="")
        print()  # Move to the next line for the next row
        for card in cards:
            print(f"| {card.name} | ", end="")
        print()  # Move to the next line for the next row
        for card in cards:
            print(f"| Str: {card.strength}   | ", end="")
        print()  # Move to the next line for the next row
        for card in cards:
            print(f"|          | ", end="")
        print()  # Move to the next line for the next row
        for card in cards:
            print(f"+----------+ ", end="")
        print()  # Move to the next line for the next row

def display_board(player1, player2):
    print("\n------ Current Board ------")
    # Display Player 1's Board
    print(f"{player1.name}'s Board:")
    display_rows(player1.rows.items())
    print("###############################################################################################################")
    # Display Player 2's Board
    print(f"{player2.name}'s Board:")
    display_rows(player2.rows.items())
    display_sum(player1)
    display_sum(player2)
    print("\n---------------------------")

def display_sum(player):
    print(f"{player.name}'s Current Sums:")
    for row, cards in player.rows.items():
        print(f"{row}: {sum(card.strength for card in cards)}")

def check_winner(player1, player2):
    player1_wins = 0
    player2_wins = 0

    for row in player1.rows:
        if sum(card.strength for card in player1.rows[row]) > sum(card.strength for card in player2.rows[row]):
            player1_wins += 1
        elif sum(card.strength for card in player1.rows[row]) < sum(card.strength for card in player2.rows[row]):
            player2_wins += 1

    return player1_wins, player2_wins

def choose_game_mode():
    while True:
        choice = input("Choose a game mode (type '1' to play or '2' to playtest): ").lower()
        choice = int(choice)
        if choice == 1 or choice == 2:
            if int(choice) == 1:
                name = input("Enter your name: ").lower()
                player1=Player(name,"human")
                player2=Player("CPU","pc")
            else:
                player1=Player("CPU1","pc")
                player2=Player("CPU2","pc")
            return player1,player2
        else:
            print("Invalid choice. Please enter '1' or '2'.")

def initialize_players():
    while True:
        try:
            choice = int(input("Choose a game mode (type '1' to play or '2' to playtest): "))
            if choice == 1 or choice == 2:
                if choice == 1:
                    name = input("Enter your name: ").lower()
                    player1 = Player(name, "human")
                    player2 = Player("CPU", "pc")
                else:
                    player1 = Player("CPU1", "pc")
                    player2 = Player("CPU2", "pc")
                return player1, player2
            else:
                print("Invalid choice. Please enter '1' or '2'.")
        except ValueError:
            print("Invalid input. Please enter a number.")

def main():
    player1,player2=initialize_players()
    # Build decks for each player
    player1.build_deck()
    player2.build_deck()
    # Display the decks
    player1.display_deck()
    player2.display_deck()

    # Take turns playing cards
    for i in range(10):  # Assuming 10 turns for demonstration purposes
        # Player 1's turn
        play_card(player1, player1.deck[i], "FRONT")
        play_card(player1, player1.deck[i], "GELEHRTE")
        play_card(player1, player1.deck[i], "UNTERSTUETZUNG")

        # Player 2's turn
        play_card(player2, player2.deck[i], "FRONT")
        play_card(player2, player2.deck[i], "GELEHRTE")
        play_card(player2, player2.deck[i], "UNTERSTUETZUNG")

        # Display the current board and sums after each turn
        display_board(player1, player2)

        # Check for winners after each turn
        player1_wins, player2_wins = check_winner(player1, player2)

        # Display the current score
        print(f"Current Score - Player 1: {player1_wins}, Player 2: {player2_wins}")

    # Final winner determination
    player1_wins, player2_wins = check_winner(player1, player2)
    if player1_wins > player2_wins:
        print("Player 1 wins!")
    elif player1_wins < player2_wins:
        print("Player 2 wins!")
    else:
        print("It's a tie!")

if __name__ == "__main__":
    main()
