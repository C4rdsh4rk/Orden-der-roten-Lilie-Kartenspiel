import os
from easygui import *

def get_user_input(prompt, valid_choices):
    while True:
        user_input = input(prompt)
        if user_input in valid_choices:
            return user_input
        else:
            print(f"Invalid input. Please enter one of {valid_choices}.")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear') # Clear screen for Linux and Windows

def get_path(title="Kartenspiel will wissen ", msg=None, filetypes=None):
    return fileopenbox(msg=msg, title=title, default='*', filetypes=filetypes, multiple=False)

def get_int(msg="Kartenspiel will wissen ",lowerbound=0, upperbound=1000000):
    return integerbox(msg, lowerbound=lowerbound, upperbound=upperbound)

def get_bool(msg, choices):
    return boolbox(msg,"Training",choices)

def get_index(msg, choices, title="Orden der roten Lilie - Kartenspiel"):
    return indexbox(msg, title, choices)

def get_name():
    return enterbox("What's your name?",title="Orden der roten Lilie - Kartenspiel")

def get_choice(msg, choices, title="Orden der roten Lilie - Kartenspiel"):
    return choicebox(msg, title, choices)