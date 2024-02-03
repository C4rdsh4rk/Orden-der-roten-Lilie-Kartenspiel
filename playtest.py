import random
import os
from colorama import Fore
from player import Player
from row import Row
from utils import get_user_input


def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear') # Clear screen for Linux and Windows


def resolve_effect(player,card):
    if card.name=="DRAW1":
        player.draw_hand(1)
    elif card.name=="DRAW2":
        player.draw_hand(2)
    else:
        print("unknown effect, bro")

def play_card(player: Player, card: Card, row: Row) -> None:
    player.rows[row].append(card)
    print(f"{player.name}: Played {card.name} with strength {card.strength} in {card.type}.")

def rule_check_move(player, card):
    available_choices={
        1: Row.FRONT,
        2: Row.WISE,
        3: Row.SUPPORT
    }
    row = card.type
    if card.type == Row.ANY:

        row = available_choices[get_user_input(
            "Choose any row to play the card",
            list(available_choices.keys())
        )]
    play_card(player, card, row)

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
        print(f"{'+----------+ '*len(cards)}")
        print(f"{'|          | '*len(cards)}")
        print(" ".join([f"| {card.name}" + " "*(19-len(card.name))+"|" for card in cards]))
        print(" ".join([f"| Str: {card.strength}   |" for card in cards]))
        print(f"{'|          | '*len(cards)}")
        print(f"{'+----------+ '*len(cards)}")
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
                        play_card_success = rule_check_move(player, player.hand[int(action)])
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