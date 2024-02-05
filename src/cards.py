import random
from colorama import Fore
from src.row import Row

class Card:  
    def __init__(self, name, strength, row_restriction=None, color="white"):
        self.name = name
        self.type = row_restriction
        self.strength = strength
        self.color = color
    
    def __str__(self):
        return f"{self.name} (Str: {self.strength}, Row: {self.type})"

class Booster:
    def __init__(self):
        self.available_strength = [1,2,3,4,5]
        self.available_cards_weights = [0.3, 0.3, 0.3, 0.05, 0.05] # Probabilities
        self.strength_weights = [0.35, 0.25, 0.2, 0.15, 0.05] # Probabilities
        self.available_effects = ["DRAW1","DRAW2"] # Add effects here TODO match number to effect string with rule check
        self.available_cards = [
                            Card("KNIGHT", random.choices(self.available_strength,self.strength_weights)[0], Row.FRONT, color="red"),
                            Card("CLERIC", random.choices(self.available_strength,self.strength_weights)[0], Row.WISE, color="white"),
                            Card("HEALER", random.choices(self.available_strength,self.strength_weights)[0], Row.SUPPORT, color="green"),
                            Card("HERO", random.choices(self.available_strength,self.strength_weights)[0], Row.ANY, color="yellow"), # Can be played in any row
                            Card(random.choice(self.available_effects), 1, Row.EFFECTS, color="white"), # Can be played in any row
                            ]
        
    def open(self,size):
        return random.choices(self.available_cards, self.available_cards_weights, k=size)