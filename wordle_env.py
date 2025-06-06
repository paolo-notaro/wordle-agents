import random
import numpy as np
import gymnasium as gym
from gymnasium import spaces
from functools import lru_cache


@lru_cache(maxsize=None)
def compute_feedback(guess: str, target: str) -> str:
    feedback = ['b'] * 5
    used = [False] * 5
    for i in range(5):
        if guess[i] == target[i]:
            feedback[i] = 'g'
            used[i] = True
    for i in range(5):
        if feedback[i] != 'g':
            for j in range(5):
                if not used[j] and guess[i] == target[j]:
                    feedback[i] = 'y'
                    used[j] = True
                    break
    return ''.join(feedback)


class WordleEnv(gym.Env):
    """
    A Gym environment for the Wordle game.
    Action: index of the guessed word in the dictionary.
    Observation: 5x3 matrix where each row corresponds to a letter (0=grey, 1=yellow, 2=green).
    """
    metadata = {"render_modes": ["human"]}

    def __init__(self, word_list):
        super().__init__()
        self.word_list = word_list
        self.word_to_idx = {word: i for i, word in enumerate(word_list)}
        self.idx_to_word = {i: word for i, word in enumerate(word_list)}
        self.observation_space = spaces.Box(low=0, high=2, shape=(5, 3), dtype=np.int8)
        self.action_space = spaces.Discrete(len(word_list))
        self.max_attempts = 6
        self.reset()

    def _feedback(self, guess, target):
        result = np.zeros((5, 3), dtype=np.int8)
        target_letters = list(target)
        used = [False]*5

        # Green pass
        for i in range(5):
            if guess[i] == target[i]:
                result[i, 2] = 1
                used[i] = True
            else:
                result[i, 0] = 1  # initially grey

        # Yellow pass
        for i in range(5):
            if result[i, 2] == 0 and guess[i] in target_letters:
                for j in range(5):
                    if not used[j] and guess[i] == target[j]:
                        result[i, 1] = 1
                        result[i, 0] = 0  # not grey anymore
                        used[j] = True
                        break
        return result

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        self.target = random.choice(self.word_list)
        self.attempts = 0
        self.done = False
        return np.zeros((5, 3), dtype=np.int8), {}

    def step(self, action):
        guess = self.idx_to_word[action]
        self.attempts += 1

        obs = self._feedback(guess, self.target)
        reward = 1.0 if guess == self.target else 0.0
        terminated = guess == self.target or self.attempts >= self.max_attempts
        truncated = self.attempts >= self.max_attempts

        return obs, reward, terminated, truncated, {}

    def render(self, mode="human"):
        print(f"Target: {self.target} | Attempts: {self.attempts}")
