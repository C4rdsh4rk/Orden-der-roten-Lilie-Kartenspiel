from abc import ABC
import random
from colorama import Fore
from src.row import Row
from src.utils import get_user_input
from src.cards import Card
from stable_baselines3 import PPO,DQN

any_row_choice = {
    1: Row.FRONT,
    2: Row.WISE,
    3: Row.SUPPORT
}
class Player(ABC):
    def __init__(self, name, idiot):
        self.name = name
        self.reward = 0
        self.idiot = idiot # Human, PC or NN
        self.turn_score = 0
        self.turn_number = 0
        self.passed = False
        self.rounds_won = 0
        self.row_score = {}

    def display_deck(self,deck):
        #clear_screen()
        print(f"{self.name}'s Deck:")
        for card in deck:
            print(f"{card.name} ({card.strength})")

    def display_hand(self):
        #clear_screen()
        print(f"{self.name}'s Hand:")
        card_number=1
        for card in self.hand:
            print(f"|[{card_number}]{card.name} ({card.strength})| ", end="")
            card_number+=1

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
        self.passed = bool(int(get_user_input(
            "Pass? 0 - No, 1 - Yes: ",
            ["0", "1"]
        )))
        return self.passed
    
    
    def build_deck(self, booster):
        deck = []
        loop_flag = True
        auto_build_deck=get_user_input(
            f"Do you want a random deck? 0 - No, 1 - Yes: ",
            ["0", "1"]
            )
        while loop_flag:
            #clear_screen()
            print(f"{self.name} is building his deck")
            booster_pack = booster.open(5) # Create a Boosterpack with 5 random cards
            if not bool(int(auto_build_deck)):
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
            if sum(card.strength for card in deck) + chosen_card.strength <= 38:
                deck.append(chosen_card)
            elif sum(card.strength for card in deck) == 38:
                break
            else:
                print("Value exceeds maximum deck strength, try again. (not your fault)")
                # If adding the card exceeds the total strength constraint, try another card
                continue
        return deck

class ArtificialRetardation(Player):
    def __init__(self, name, idiot):
        super().__init__(name, idiot)

    def make_card_choice(self, hand, valid_choices, action=None):
        if action:
            return hand[action]
        else:
            return hand[int(random.choice(valid_choices))-1]

    def make_row_choice(self, card) -> Row:
        return random.choice(list(any_row_choice.values()))

    def make_pass_choice(self) -> bool:
        if len(self.hand)==0:
            print(f"{self.name} passed due to no cards to play.")
            self.passed = True
        else:
            self.passed = random.choices([False, True],[0.97,0.03],k=1)[0]
        return self.passed

    def build_deck(self, booster):
        deck = []
        while True:
            #clear_screen()
            booster_pack = booster.open(5)
            chosen_card = random.choice(booster_pack)
            # deck building checks
            if sum(card.strength for card in deck) + chosen_card.strength <= 38:
                deck.append(chosen_card)
            elif sum(card.strength for card in deck) == 38:
                break
            else:
                #print("Value exceeds maximum deck strength, try again. (not your fault)")
                # If adding the card exceeds the total strength constraint, try another card
                continue
        return deck
