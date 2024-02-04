import os

def get_user_input(prompt, valid_choices):
    while True:
        user_input = input(prompt)
        if user_input in valid_choices:
            return user_input
        else:
            print(f"Invalid input. Please enter one of {valid_choices}.")

def clear_screen():
    os.system('cls' if os.name == 'nt' else 'clear') # Clear screen for Linux and Windows