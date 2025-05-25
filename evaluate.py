
from typing import Type
import random
import time

from utils import load_word_list
from agents import WordleAgent, agent_classes
from wordle_env import compute_feedback

WORD_LIST = load_word_list("data/wordle_full_vocab.txt")
ANSWER_LIST = load_word_list("data/wordle_answers.txt")

def evaluate_agent(agent_cls: Type[WordleAgent], word_list: list[str], target: str) -> int:
    agent = agent_cls(word_list)
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
    print(f"Evaluating {len(agent_classes)} agents on {len(WORD_LIST)} words...")
    for name, agent_cls in agent_classes.items():
        t_start = time.time()
        scores = [evaluate_agent(agent_cls=agent_cls, word_list=WORD_LIST, target=target) for target in ANSWER_LIST[:10]]
        t_end = time.time()
        avg = sum(scores) / len(scores)
        print(f"{name}: Avg. Attempts = {avg:.2f}, Avg. Time = {(t_end - t_start) / len(ANSWER_LIST):.4f} seconds per target")
