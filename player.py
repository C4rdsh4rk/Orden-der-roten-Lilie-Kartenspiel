from row import Row
import random
from utils import get_user_input

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