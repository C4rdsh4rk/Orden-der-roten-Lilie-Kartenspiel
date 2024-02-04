from game import game


def main():
    env = game()
    while(True):
        episodes=input(f"How many games should be played for training?")
        if isinstance(episodes,int) and episodes>0:
            break
        else:
            print(f"Wrong input, try again")
            
    for episode in range(1, episodes+1):
    state = env.reset()
    done = False
    score = 0 
        while not done:
            #env.render()
            action = env.action_space.sample()
            n_state, reward, done, info = env.step(action)
        print('Episode:{} Score:{}'.format(episode, reward))

if __name__ == "__main__":
    main()