from colorama import Fore
from row import Row
import random


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