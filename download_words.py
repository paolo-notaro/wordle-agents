import urllib.request

# URLs from Tab Atkins' Wordle list
WORDS_URL = "https://raw.githubusercontent.com/tabatkins/wordle-list/main/words"
ANSWERS_URL = "https://gist.githubusercontent.com/cfreshman/a03ef2cba789d8cf00c08f767e0fad7b/raw/wordle-answers-alphabetical.txt"

# Local file paths
WORDS_PATH = "data/wordle_full_vocab.txt"
ANSWERS_PATH = "data/wordle_answers.txt"

# Download the files
urllib.request.urlretrieve(WORDS_URL, WORDS_PATH)
urllib.request.urlretrieve(ANSWERS_URL, ANSWERS_PATH)

print("Downloaded:")
print(f"- Full guessable words -> {WORDS_PATH}")
print(f"- Official answers -> {ANSWERS_PATH}")