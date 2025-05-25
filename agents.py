from abc import ABC, abstractmethod
import random
from typing import List
from collections import Counter, defaultdict
import math

from wordle_env import compute_feedback  # ✅ add this at the top

# Abstract base class
class WordleAgent(ABC):
    def __init__(self, word_list: List[str]):
        self.word_list = word_list
        self.reset()

    def reset(self):
        self.remaining = self.word_list.copy()
        self.history = []
        self.round = 0

    @abstractmethod
    def guess(self) -> str:
        pass

    def process_feedback(self, guess: str, result: str):
        self.history.append((guess, result))
        self.round += 1

    @staticmethod
    def match_feedback(guess: str, result: str, word: str) -> bool:
        for i, (g, r) in enumerate(zip(guess, result)):
            if r == 'g' and word[i] != g:
                return False
            if r == 'y':
                if g not in word or word[i] == g:
                    return False
            if r == 'b' and g in word:
                return False
        return True

class RandomAgent(WordleAgent):
    def guess(self) -> str:
        return random.choice(self.remaining)


class DiverseRandomAgent(WordleAgent):
    def guess(self) -> str:
        return random.choice(self.remaining)

    def process_feedback(self, guess: str, result: str):
        super().process_feedback(guess, result)
        self.remaining.remove(guess)


class FrequencyAgent(WordleAgent):

    def letter_frequency_score(self, guess: str) -> int:
        print(f"Calculating frequency score for guess: {guess}")
        letter_freq = Counter(c for word in self.remaining for c in word)
        return sum(letter_freq[c] for c in set(guess))

    def guess(self) -> str:
        return max(self.remaining, key=self.letter_frequency_score)

    def process_feedback(self, guess: str, result: str):
        super().process_feedback(guess, result)
        self.remaining = [
            w for w in self.remaining
            if self.match_feedback(guess, result, w)
        ]

class EntropyAgent(WordleAgent):

    def entropy(self, guess: str) -> float:
        buckets = defaultdict(int)
        for potential_target in self.remaining:
            fb = compute_feedback(guess, potential_target)
            buckets[fb] += 1
        total = len(self.remaining)
        return -sum((n / total) * math.log2(n / total) for n in buckets.values())

    def guess(self) -> str:
        return max(self.word_list, key=self.entropy)

    def process_feedback(self, guess: str, result: str):
        super().process_feedback(guess, result)
        self.remaining = [
            w for w in self.remaining
            if self.match_feedback(guess, result, w)
        ]

class ExploreExploitAgent(EntropyAgent):

    def __init__(self, word_list: List[str], exploration_rounds: int = 3):
        super().__init__(word_list)
        self.exploration_rounds = exploration_rounds

    def letter_frequency_score(self, guess: str) -> int:
        letter_freq = Counter(c for word in self.remaining for c in word)
        return sum(letter_freq[c] for c in set(guess))

    def guess(self) -> str:
        if self.round < self.exploration_rounds:
            # During exploration, use entropy to select the best word
            return max(self.word_list, key=self.entropy)
        else:
            # During exploitation, use letter frequency to select the best word
            return max(self.remaining, key=self.letter_frequency_score)


# Evaluation function
agent_classes = {
    "RandomAgent": RandomAgent,
    "DiverseRandomAgent": DiverseRandomAgent,
    "FrequencyAgent": FrequencyAgent,
    "EntropyAgent": EntropyAgent,
    "ExploreExploitAgent": ExploreExploitAgent
}