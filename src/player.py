from abc import ABC
import random
import gymnasium as gym #TEST
from colorama import Fore
from src.row import Row
from src.utils import get_user_input
from src.cards import Card

any_row_choice = {
    1: Row.FRONT,
    2: Row.WISE,
    3: Row.SUPPORT
}

class Player(ABC):
    def __init__(self, name, idiot):
        self.name = name
        self.idiot = idiot
        self.deck = []
        self.hand = [] # Add a hand attribute
        self.score_vector = []
        self.turn_score = 0
        self.turn_number = 0
        self.passed = False
        self.rounds_won = 0
        self.rows = {
            Row.FRONT: [],
            Row.WISE: [],
            Row.SUPPORT: [],
            Row.EFFECTS: [],
        }

    def clear_rows(self):
        self.rows = {
            Row.FRONT: [],
            Row.WISE: [],
            Row.SUPPORT: [],
            Row.EFFECTS: [],
        }
    
    def get_row_sum(self, row) -> list[int]:
        return sum(card.strength for card in self.rows[row])
    
    def draw_hand(self, num_cards=10,shuffle=False):
        if shuffle:
            random.shuffle(self.deck)
        # Draw cards from the deck
        self.hand = self.hand + self.deck[:num_cards]
        # Remove drawn cards from the deck
        self.deck = self.deck[num_cards:]

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
    
    def play_card(self) -> None:
        if self.make_pass_choice():
            self.passed = True
            return

        valid_choices = ["{:1d}".format(x) for x in range(len(self.hand))]
        choosen_card = self.make_card_choice(valid_choices)
        
        row = choosen_card.type
        if row == Row.ANY:
            row = self.make_row_choice(choosen_card)
        # add card to row to play it and remove it from the hand
        self.rows[row].append(choosen_card)
        card_index = self.hand.index(choosen_card)
        self.hand = self.hand[:card_index] + self.hand[card_index+1:]
        print(f"{self.name}: Played {choosen_card.name} with strength {choosen_card.strength} in {choosen_card.type}.")
    
    def make_pass_choice(self) -> bool:
        """
        Function that determines if the player passes
        """
        raise NotImplementedError

    def make_card_choice(self, valid_choices: list) -> Card:
        """
        Interface function that must return exactly one card that is played by the player.
        The card must be in the valid_choices.
        
        Args:
            valid_choices (list[Card]): Possible cards to play
        
        Returns:
            Card: Card that is played"""
        raise NotImplementedError
    
    def make_row_choice(self, card: Card) -> Row:
        """
        Interface function that must return exactly one row where the given card should be played in.

        Args: 
            card (Card): Card that is played
        
            Returns:
                Row: the row in which the card should be played
        """
        raise NotImplementedError

class Human(Player):
    def make_card_choice(self, valid_choices):
        valid_choices = [str(int(x)+1) for x in valid_choices] # User friendly numbers
        self.display_hand()
        return self.hand[int(get_user_input(
            "Choose a card from your hand:",
            valid_choices
        ))-1]
    
    def make_row_choice(self, card) -> Row:
        return any_row_choice[
            int(get_user_input(
                "Chose any row for your card",
                [str(row_number) for row_number in any_row_choice.keys()]
            ))
        ]
    
    def make_pass_choice(self) -> bool:
        return bool(int(get_user_input(
            "Pass? 0 - No, 1 - Yes: ",
            ["0", "1"]
        )))
    
    
    def build_deck(self, booster):
        loop_flag = True
        auto_build_deck=get_user_input(
            f"Do you want a random deck? 0 - No, 1 - Yes: ",
            ["0", "1"]
            )
        while loop_flag:
            #clear_screen()
            print(f"{self.name} is building his deck")
            booster_pack = booster.open(5) # Create a Boosterpack with 5 random cards
            if not auto_build_deck:
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

class ArtificialRetardation(Player):
    def __init__(self, name, idiot):
        super().__init__(name, idiot)
        self.reward = 0

    def make_card_choice(self, valid_choices):
        return self.hand[int(random.choice(valid_choices))-1]
    
    def make_row_choice(self, card) -> Row:
        return random.choice(list(any_row_choice.values()))
    
    def make_pass_choice(self) -> bool:
        if len(self.hand)==0:
            print(f"{self.name} passed due to no cards to play.")
            self.passed = True
        else:
            self.passed = random.choices([False, True],[0.8,0.2],k=1)[0]
        return self.passed
    
    def build_deck(self, booster):
        loop_flag = True
        while loop_flag:
            #clear_screen()
            booster_pack = booster.open(5) # Create a Boosterpack with 5 random cards
            print(f"{self.name} is building his deck")
            self.display_deck()# cpu chooses a random card
            chosen_card = random.choice(booster_pack)
            # deck building checks
            if sum(card.strength for card in self.deck) + chosen_card.strength <= 38:
                self.deck.append(chosen_card)
            elif sum(card.strength for card in self.deck) == 38:
                break
            else:
                #print("Value exceeds maximum deck strength, try again. (not your fault)")
                # If adding the card exceeds the total strength constraint, try another card
                continue
