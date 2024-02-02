import random

class Card:
    def __init__(self, name, strength, row_restriction=None):
        self.name = name
        self.type = row_restriction
        self.strength = strength

class Player:
    def __init__(self, name):
        self.name = name
        self.rows = {
            "FRONT": [],
            "GELEHRTE": [],
            "UNTERSTUETZUNG": [],
        }
        self.deck = []

    def build_deck(self):
        print(f"{self.name} is building his deck")
        while len(self.deck) < 20:
            available_cards = [
                Card("RITTER  ", random.randint(1, 5), "FRONT"),
                Card("KLERIKER", random.randint(1, 5), "GELEHRTE"),
                Card("HEILER  ", random.randint(1, 5), "UNTERSTUETZUNG"),
                Card("HELD    ", random.randint(2, 5)),  # Can be played in any row
            ]
            chosen_card = random.choice(available_cards)
            if sum(card.strength for card in self.deck) + chosen_card.strength <= 38:
                self.deck.append(chosen_card)
            if sum(card.strength for card in self.deck)==38:
                break
            else:
                # If adding the card exceeds the total strength constraint, try another card
                continue

    def display_deck(self):
        print(f"{self.name}'s Deck:")
        for card in self.deck:
            print(f"{card.name} ({card.strength})")

def play_card(player, card, row):
    if card.type and row != card.type and card.type is not None:
        print(f"{player.name}: Cannot play {card.name} in {row}. Must be played in {card.type}.")
    else:
        player.rows[row].append(card)
        print(f"{player.name}: Played {card.name} with strength {card.strength} in {row}.")

def display_board(player1, player2):
    print("\n------ Current Board ------")

    # Display Player 1's Board
    print(f"{player1.name}'s Board:")
    for row, cards in player1.rows.items():
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
    print("###############################################################################################################")
    # Display Player 2's Board
    print(f"{player2.name}'s Board:")
    for row, cards in player2.rows.items():
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

def main():
    player1 = Player("Player 1")
    player2 = Player("Player 2")

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
