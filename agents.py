from abc import ABC, abstractmethod
import random
from typing import List
from collections import Counter, defaultdict
from functools import partial
import math
from concurrent.futures import ProcessPoolExecutor
from itertools import islice
import os
from wordle_env import compute_feedback

# Abstract base class
class WordleAgent(ABC):
    def __init__(self, word_list: List[str]):
        self.word_list = word_list
        self.history: list[str] = None
        self.round: int = None
        self.remaining: set[str] = None  # will be set in reset()
        self.reset()

    def reset(self):
        self.remaining = set(self.word_list)
        self.history = []
        self.round = 0
        compute_feedback.cache_clear()

    @abstractmethod
    def guess(self) -> str:
        pass

    def process_feedback(self, guess: str, result: str):
        self.history.append((guess, result))
        self.round += 1

    @staticmethod
    def match_feedback(guess: str, result: str, word: str) -> bool:
        """Check if a word matches the feedback from a guess.

        This method checks if the word matches the feedback given for a guess.
        It verifies that:
        - Letters marked as 'g' (green) are in the correct position.
        - Letters marked as 'y' (yellow) are present in the word but not in the guessed position.
        - Letters marked as 'b' (black) are not present in the word at all.

        Args:
            guess (str): The guessed word.
            result (str): The feedback string ('g' for green, 'y' for yellow, 'b' for black).
            word (str): The target word to check against.
        Returns:
            bool: True if the word matches the feedback, False otherwise.
        """
        for i, (g, r) in enumerate(zip(guess, result)):
            if r == "g" and word[i] != g:
                return False
            if r == "y":
                if g not in word or word[i] == g:
                    return False
            if r == "b" and g in word:
                return False
        return True


class RandomAgent(WordleAgent):
    """Agent that guesses words randomly from the remaining list (avoids repeating previous guesses)."""

    def guess(self) -> str:
        return random.choice(self.remaining)

    def process_feedback(self, guess: str, result: str):
        super().process_feedback(guess, result)
        self.remaining.remove(guess)


class DiverseRandomAgent(RandomAgent):
    """Agent that selects words randomly but tries to favor different letters in further guesses."""

    def guess(self) -> str:
        # Calculate letter diversity in remaining words
        letter_counts = Counter(c for word in self.remaining for c in word)
        # Sort remaining words by the number of unique letters they contain
        sorted_remaining = sorted(
            self.remaining, key=lambda word: len(set(word)), reverse=True
        )
        # Select a word that has the most unique letters
        return (
            sorted_remaining[0] if sorted_remaining else random.choice(self.remaining)
        )


class FrequencyAgent(WordleAgent):
    def __init__(self, word_list: List[str]):
        super().__init__(word_list)
        self._letter_counters = {word: Counter(word) for word in self.word_list}

    def letter_frequency_score(self, guess: str, letter_freq: Counter) -> int:
        # print(f"Calculating frequency score for guess: {guess}")
        return sum(letter_freq[c] for c in self._letter_counters[guess])

    def guess(self) -> str:
        letter_freq = sum((self._letter_counters[w] for w in self.remaining), Counter())
        letter_freq_score = partial(
            self.letter_frequency_score, letter_freq=letter_freq
        )

        return max(self.remaining, key=letter_freq_score)

    def process_feedback(self, guess: str, result: str):
        super().process_feedback(guess, result)
        self.remaining = [
            w for w in self.remaining if self.match_feedback(guess, result, w)
        ]


_worker_candidate_set = None  # will be set once per worker

def _init_worker(candidate_set: frozenset[str]):
    """
    Called once when each worker process starts.
    Stores the shared candidate_set in a module‐global inside that worker.

    This allows each worker to access the same candidate set without passing it
    around for every guess, which is more efficient.

    Args:
        candidate_set (frozenset): The set of candidate words to use for entropy computation.
    """
    global _worker_candidate_set
    _worker_candidate_set = candidate_set

def entropy_task_simple(guess: str) -> float:
    """
    Compute entropy of `guess` against the already-loaded
    `_worker_candidate_set` inside each worker.
    This function is called by each worker process to compute the entropy score
    for a given guess based on the feedback from all target words in the candidate set.
    It uses the `compute_feedback` function to get feedback for each target word
    and calculates the entropy score based on the distribution of feedback.
    This is a simple version that does not use multiprocessing.
    It is designed to be called by worker processes in a multiprocessing setup.

    Args:
        guess (str): The word to compute entropy for.
    Returns:
        float: The entropy score for the guess.
    """
    buckets = defaultdict(int)
    # print(f"Calculating entropy score for guess: {guess}")

    # Compute feedback for each target word in the candidate set
    for target in _worker_candidate_set:
        fb = compute_feedback(guess, target)
        buckets[fb] += 1
    total = len(_worker_candidate_set)

    return -sum((count/total) * math.log2(count/total) for count in buckets.values())

class EntropyAgent(WordleAgent):

    def __init__(
        self,
        word_list: List[str],
        init_entropy_cache_file: str = None,
        num_samples_entropy: int = None,
        multiprocessing: bool = True
    ):
        """
        EntropyAgent that uses precomputed initial entropy cache and/or computes entropy on-the-fly.
        Args:
            word_list (List[str]): List of words to use for guessing.
            init_entropy_cache_file (str): Path to a file containing precomputed initial entropy cache.
            num_samples_entropy (int): Number of samples to use for entropy calculation if cache is not provided.
        """
        super().__init__(word_list)
        self.remaining: set[str] = None  # will be set in reset()
        self.num_samples_entropy = num_samples_entropy
        self.multiprocessing = multiprocessing

        if init_entropy_cache_file:
            # load precomputed initial entropy cache from file
            print(f"Loading initial entropy cache from {init_entropy_cache_file}...")
            with open(init_entropy_cache_file, mode="r", encoding="utf-8") as f:
                self.init_entropy_cache = {
                    line.split(":")[0].strip(): float(line.split(":")[1].strip())
                    for line in f.readlines()
                }
        else:
            self.init_entropy_cache = {}

    def dispatch_compute_entropy(self) -> list[float]:
        """Dispatch entropy computation tasks to a process pool executor.
        
        Returns:
            list[float]: List of entropy scores for each word in the candidate set.
        """

        # the candidate set is the always set of all remaining words
        guesses = list(self.remaining)

        # if we do not set a sampling strategy, we compute on all candidates
        if self.num_samples_entropy is None:
            # print("Using all candidates for entropy...")
            entropy_set = guesses[:]  # full remaining set
        # or else we sample a subset of the word list for entropy computation
        else:
            num_samples = min(self.num_samples_entropy, len(guesses))
            # print(f"Using a sample of {num_samples} candidates for entropy...")           
            entropy_set = random.sample(guesses, k=num_samples)

        # Freeze into an immutable set (workers share this once)
        shared_set = frozenset(entropy_set)

        # Choose a safe number of workers (you can tune max_workers manually):

        if self.multiprocessing:
            max_workers = max(1, (os.cpu_count() or 2) // 2)

            # Each worker will run _init_worker(shared_set) exactly once,
            # then reuse `_worker_candidate_set` for every guess it sees.        
            with ProcessPoolExecutor(
                max_workers=max_workers,
                initializer=_init_worker,
                initargs=(shared_set,)
            ) as executor:
                # Now each worker just receives a single `guess` at a time.
                results = executor.map(entropy_task_simple, guesses, chunksize=50)

            return list(results)

        else:
            # If multiprocessing is disabled, compute entropy in the main thread
            _init_worker(shared_set)  # Initialize the worker set
            return [entropy_task_simple(guess) for guess in guesses]

    def guess(self) -> str:
        """Select the word with the highest entropy score.
        
        If it's the first round, use precomputed initial entropy cache.
        Otherwise, compute entropy for all remaining words in parallel.
        Returns:
            str: The word with the highest entropy score.
        """

        must_save_cache = False
        if self.round == 0:
            if self.init_entropy_cache:
                # print("Round 1. Using initial entropy cache...")
                return max(self.init_entropy_cache, key=self.init_entropy_cache.get)
            else:
                print(f"No initial entropy cache found. Will precompute and save to disk...")
                must_save_cache = True
        else:
            # print(f"Round {self.round+1}. Starting entropy parallel computation...")
            pass


        entropies = self.dispatch_compute_entropy()

        if must_save_cache:
            # print("Saving initial entropy cache...")

            # Store results in cache - entropies are always computed on remaining as candidate set
            self.init_entropy_cache = dict(zip(self.remaining, entropies))

            # rewrite the full cache to the file, sorted by score
            with open(
                "data/init_entropy_cache.txt", mode="w", encoding="utf-8"
            ) as f:
                for word, score in sorted(
                    self.init_entropy_cache.items(),
                    key=lambda x: x[1],
                    reverse=True,
                ):
                    f.write(f"{word}: {score}\n")

        # pair guesses with their scores and return best one
        return max(zip(self.remaining, entropies), key=lambda x: x[1])[0]

    def process_feedback(self, guess: str, result: str):
        super().process_feedback(guess, result)
        self.remaining = [
            w for w in self.remaining if self.match_feedback(guess, result, w)
        ]


class ExploreExploitAgent(EntropyAgent):

    def __init__(self, word_list: List[str], exploration_rounds: int = 3, init_entropy_cache_file: str = None, num_samples_entropy: int = None):
        super().__init__(word_list, init_entropy_cache_file=init_entropy_cache_file, num_samples_entropy=num_samples_entropy)
        self.exploration_rounds = exploration_rounds
        self._letter_counters = {word: Counter(word) for word in self.word_list}

    def letter_frequency_score(self, guess: str, letter_freq: Counter) -> int:
        # print(f"Calculating frequency score for guess: {guess}")
        return sum(letter_freq[c] for c in self._letter_counters[guess])

    def guess(self) -> str:
        """Select the word based on exploration or exploitation strategy.
        During the first few rounds, it uses entropy to select the best word.
        After that, it uses letter frequency to select the best word.
        Returns:
            str: The word selected based on the current strategy.
        """
        if self.round < self.exploration_rounds:
            # During exploration, use entropy to select the best word
            return super().guess()
        else:
            # During exploitation, use letter frequency to select the best word
            letter_freq = sum(
                (self._letter_counters[w] for w in self.remaining), Counter()
            )
            letter_freq_score = partial(
                self.letter_frequency_score, letter_freq=letter_freq
            )

            return max(self.remaining, key=letter_freq_score)


# Evaluation function
agent_classes = {
    "RandomAgent": RandomAgent,
    "DiverseRandomAgent": DiverseRandomAgent,
    "FrequencyAgent": FrequencyAgent,
    "EntropyAgent": EntropyAgent,
    "ExploreExploitAgent": ExploreExploitAgent,
}
