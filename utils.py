def load_word_list(path: str) -> list:
    with open(path, "r") as f:
        return [line.strip().lower() for line in f if len(line.strip()) == 5]
