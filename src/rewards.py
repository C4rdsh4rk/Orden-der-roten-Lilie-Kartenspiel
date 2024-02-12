    def get_reward(self, player=True):
        # Initialize the base reward
        reward = 0.0

        # Standardize rewards to encourage both immediate and strategic play
        base_win_reward = 1.0
        base_loss_penalty = -1.0

        # Calculate the difference in rounds won between the player and the opponent
        rounds_won_difference = self.board.get_rounds_won(player) - self.board.get_rounds_won(not player)

        # Reward/Penalty for round outcomes
        if rounds_won_difference > 0:
            reward += base_win_reward * rounds_won_difference
        elif rounds_won_difference < 0:
            reward += base_loss_penalty * rounds_won_difference

        # Major reward for winning the game, encouraging the agent to aim for a win
        if self.board.get_rounds_won(player) >= 2:
            reward += 5.0  # Substantial reward for winning the game

        # Adjust rewards based on strategic passing
        if self.board.has_passed(player):
            passed_penalty = -0.5  # Penalize less for strategic passing
            reward += passed_penalty

        # Incorporate a decay factor for future rewards to promote strategic thinking
        gamma = 0.9  # Decay factor for future rewards
        future_rewards_estimate = self.estimate_future_rewards(player, reward) * gamma
        reward += future_rewards_estimate

        # Normalize reward to be within a specific range to maintain consistency
        max_possible_reward = 10.0
        reward = max(min(reward, max_possible_reward), -max_possible_reward)

        # Update the player's accumulated rewards
        self.rewards[player] += reward
        return reward

    def estimate_future_rewards(self, player):
        # Heuristic-based future reward estimation
        
        # Example heuristic: Balance between aggression and defense based on the current state
        aggression_factor = 0.1  # Reward more aggressive play slightly
        defense_factor = 0.05  # Reward defensive play to a lesser extent

        # Calculate the current advantage or disadvantage in terms of rounds won
        rounds_advantage = self.board.get_rounds_won(player) - self.board.get_rounds_won(not player)

        # Adjust the future reward estimation based on the player's current position
        if rounds_advantage > 0:
            # Player is leading: encourage maintaining or extending the lead (defensive strategy)
            future_reward_estimation = rounds_advantage * defense_factor
        elif rounds_advantage < 0:
            # Player is trailing: encourage catching up or overtaking (aggressive strategy)
            future_reward_estimation = rounds_advantage * aggression_factor
        else:
            # No clear advantage: neutral encouragement for both aggression and defense
            future_reward_estimation = 0.0

        # Example adjustment based on additional game state considerations
        # If the opponent has passed and the player has a winning hand, increase the future reward estimation
        # if self.board.has_passed(not player) and self.has_winning_hand(player):
        #    future_reward_estimation += 0.5  # Adjust based on your game's logic

        return future_reward_estimation
################################################################################################
    def get_reward(self, player=True):
        """Calculates and returns the reward for a given player's actions.

        Args:
            player (boolean): The player for whom to calculate the reward.

        Returns:
            float: The calculated reward based on the player's performance and actions.
        """

        # Incremental rewards for positive actions
        # For example, playing a card that increases the player's score or strategically passing

        reward = 0
        win_reward = 1  # Normalized winning reward
        loss_penalty = -1  # Normalized losing penalty

        rounds_won = self.board.get_rounds_won(player)
        rounds_lost = self.board.get_rounds_won(not player)
        round_difference = rounds_won - rounds_lost

        # Simplify the reward for winning rounds
        if rounds_won > 0:
            reward += win_reward * round_difference

        # Additional reward for winning the game
        if rounds_won >= 2:
            reward += 5  # More significant reward for winning the game

        # Adjust for strategic passing, simplified
        if self.board.has_passed(player):
            if round_difference < 0:
                reward += loss_penalty  # Penalize if passing when losing

        self.rewards[player] += reward
        logging.debug("Reward: %s", self.rewards[player])
        return reward
###############################################################################################
def get_reward(self, player=True):
    reward = 0.0

    # Base rewards and penalties
    base_win_reward = 1.0
    base_loss_penalty = -1.0
    early_pass_penalty = -2.0  # Stronger penalty for early passing without strategic consideration

    # Calculate rounds won difference
    rounds_won_difference = self.board.get_rounds_won(player) - self.board.get_rounds_won(not player)

    # Reward for rounds won or lost
    if rounds_won_difference > 0:
        reward += base_win_reward * rounds_won_difference
    elif rounds_won_difference < 0:
        reward += base_loss_penalty * rounds_won_difference

    # Significant reward for winning the game
    if self.board.get_rounds_won(player) >= 2:
        reward += 5.0

    # Penalty for early passing
    if self.board.has_passed(player) and self.is_early_pass(player):
        reward += early_pass_penalty

    # Future rewards estimation with decay factor
    gamma = 0.9
    reward += self.estimate_future_rewards(player) * gamma

    # Normalize reward to prevent scaling issues
    max_possible_reward = 10.0
    reward = max(min(reward, max_possible_reward), -max_possible_reward)

    self.rewards[player] += reward
    return reward


def is_early_pass(self, player):
    # Determine if a pass is early based on the game state
    # Assuming 'True' for early pass if no beneficial moves are left or it's the first opportunity to pass
    # This should be adjusted based on the specific game mechanics and strategy
    beneficial_moves_left = self.check_for_beneficial_moves(player)
    return not beneficial_moves_left