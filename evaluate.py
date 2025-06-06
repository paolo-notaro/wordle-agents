
from typing import Type
import random
import time
from os import path
from utils import load_word_list
from agents import WordleAgent, agent_classes
from wordle_env import compute_feedback

WORD_LIST = load_word_list("data/wordle_full_vocab.txt")
ANSWER_LIST = load_word_list("data/wordle_answers.txt")

def evaluate_agent(agent: WordleAgent, word_list: list[str], target: str) -> int:
    agent.reset()
    for attempt in range(1, 6):
        if not agent.remaining:
            guess = random.choice(word_list)
        else:
            guess = agent.guess()
        result = compute_feedback(guess, target)
        agent.process_feedback(guess, result)
        if result == 'ggggg':
            return attempt
    return 6 # if not solved in 5 attempts, return 6

if __name__ == "__main__":

    eval_set = ANSWER_LIST[:100] # Use a small subset for quick evaluation; adjust as needed
    print(f"Evaluating {len(agent_classes)} agents on {len(eval_set)} words...")
    for name, agent_cls in agent_classes.items():
        if agent_cls.__name__ in ('EntropyAgent', 'ExploreExploitAgent'):
            kwargs = {'init_entropy_cache_file': 'data/init_entropy_cache.txt' 
                      if path.exists('data/init_entropy_cache.txt') 
                      else None, "num_samples_entropy": None, "multiprocessing": False}
        else:
            kwargs = {}
            continue
        agent = agent_cls(WORD_LIST, **kwargs)
        t_start = time.time()
        scores = [evaluate_agent(agent=agent, word_list=WORD_LIST, target=target) 
                  for target in eval_set]
        t_end = time.time()
        avg = sum(scores) / len(scores)
        success_rate = sum(1 for score in scores if score < 6) / len(scores)
        print(f"{name}: Success Rate: {success_rate * 100:.2f}%, avg. Attempts = {avg:.2f}, avg. Time = {(t_end - t_start) / len(ANSWER_LIST):.4f} seconds per target")
