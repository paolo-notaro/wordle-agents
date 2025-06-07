---
title: How Entropy Guides Decisions — and When It Fails
tags: [Information Theory, Decision Making, Entropy, Exploration, Wordle, Agent Design]
style: fill
color: gray
description: Entropy is central to learning and decision-making — but is it enough? We tested this idea in Wordle, and discovered where information gain alone breaks down.
---------------------------------------------------------------------------------------------------------------------------------------------------------------------------

# Story-First Hook: The Safecracker's Dilemma

> *"You have six chances to open a safe. Each test reveals a click or a clunk. Do you probe every tumbler for clues, or go straight for the code you suspect?"*

This is **decision science**: the field that studies how to act under uncertainty. From medical diagnostics to marketing campaigns, from autonomous robots to games and quizzes like Wordle, every decision boils down to the same tension: **should you explore to learn more**, or **exploit what you already know**?

The most powerful tool in this dilemma is entropy — the math of surprise. But while entropy shines as a compass, it's not always a complete map. In this article, we explore entropy’s journey from steam engines to guessing games, and why a smarter agent must know when to stop being curious.

---

# 1. Entropy’s Origin: From Steam Engines to Secret Messages

Let’s begin in the 19th century, with a man staring at a kettle.

### Clausius: Taming Heat (1865)

Rudolf Clausius was born in 1822 in Köslin, Prussia (modern-day Poland), and spent much of his academic life in Zürich, Switzerland. A quiet, methodical thinker, Clausius was fascinated by thermodynamics. Working during the industrial revolution, he aimed to understand and improve steam engines — the cutting-edge tech of the time.

He noticed a fundamental limit: not all heat could be converted to work. This inefficiency wasn't due to engineering flaws, but something deeper. He introduced the concept of **entropy** to describe this inevitable loss:

$dS = \frac{dQ_{rev}}{T}$

Here, $dQ_{rev}$ is the infinitesimal heat added reversibly to the system — i.e., the tiny amount of energy transferred as **heat flow** under ideal conditions — and $T$ is the temperature. Entropy became a way to track the "spread" of energy and the irreversibility of real processes.

### Boltzmann: Counting Chaos (1877)

Ludwig Boltzmann, born in Vienna in 1844, brought entropy to the microscopic scale. A fervent believer in atoms when many scientists were skeptical, he taught in Graz and Leipzig and spent his life defending statistical mechanics.

Boltzmann sought to ground Clausius’ formula in particle behavior. He reasoned: if entropy measures disorder, then more microstates (ways atoms can be arranged) must mean more entropy:

$S = k_B \ln \Omega$

Here, $\Omega$ is the number of microscopic configurations consistent with a macrostate. Differentiating this definition — and assuming energy is conserved across states — recovers the Clausius formula. In this sense, Boltzmann’s view **explains** entropy as a count of possible hidden arrangements behind observed states.

Tragically, Boltzmann faced academic resistance and personal despair. He took his own life in 1906 while in Duino, near Trieste — not living to see his theory vindicated by atomic theory’s full acceptance.

### Shannon: Information and Surprise (1948)

Claude Shannon was born in 1916 in Petoskey, Michigan. A brilliant mathematician and engineer, he worked at Bell Labs during WWII and later at MIT.

Shannon wanted to optimize communication channels. He asked: *how much uncertainty does a message contain?* The result was his **entropy formula**:

$H = -\sum_i p_i \log_2 p_i$

Where $p_i$ is the probability of a message or symbol. Like Boltzmann’s equation, it measured how "spread out" or uncertain a distribution is. A uniform distribution (each outcome equally likely) has the highest entropy. A deterministic one has zero entropy.

**Example:** “It will be sunny tomorrow in the Sahara” is not very surprising — it has **low entropy**. “A snowstorm is coming” would carry more information — **higher entropy** — and provoke action.

### Key Parallel

Whether it’s atoms or emails, entropy quantifies uncertainty. It tells you: *“how much can I learn from this observation?”* — and that makes it a powerful guide in decisions.

---

# 2. The Cost of Curiosity: When Exploration Backfires

So if entropy tells you what’s most informative, why not always pick the option with highest entropy?

Because exploration has a cost.

* In **quizzes** like Wordle, you only get 6 guesses. Burn 3 learning the alphabet, and you may never reach the word.
* In **medicine**, every test costs money and time — and might delay treatment.
* In **business**, A/B tests that never end stall profits.

### The Exploration–Exploitation Trade-off

This is a classic problem in reinforcement learning, operations research, and cognitive psychology. You must choose between:

* **Exploration**: ask high-entropy questions to gather more information
* **Exploitation**: act on current knowledge to maximize reward

Entropy shines early on — it helps uncover the landscape. But real-world agents must know when to stop exploring and start acting. Pure entropy maximizers may remain curious to their own detriment.

In practice, the most successful decision strategies **combine entropy with reward-driven heuristics**. One approach is to decay exploration over time — another is to balance them probabilistically. Wordle makes this transition painfully clear: once you're down to two turns, even the most informative guess isn't helpful if it doesn’t solve the puzzle.

---

# 3. Wordle as a Lab for Decision Science

Games like Wordle offer a clean environment to explore these trade-offs.

## How Wordle Works

Wordle is a word guessing game invented by Josh Wardle, a software engineer from Wales. Created as a personal project for his partner, it was released publicly in 2021 and quickly became a global hit. *The New York Times* acquired it in early 2022.

Players have 6 tries to guess a secret 5-letter English word. After each guess, feedback is given:

* 🟩 **Green**: correct letter, correct position
* 🟨 **Yellow**: correct letter, wrong position
* ⬛ **Gray**: letter not in the word

This format makes it ideal for testing decision-making strategies:

* Discrete, known action space
* Structured, rule-based feedback
* Hard cap on number of decisions (6 rounds)

### Simulation Framework

We built a full Python simulation, inspired by Gym environments:

* `WordleEnv` encapsulates the game rules and feedback logic
* Multiple agents implement strategies using a shared API
* High-entropy computations use multiprocessing and optional caching
* Word lists and targets can be swapped for scale

---

# 4. Agent Architectures: From Curiosity to Strategy

Here’s who we invited to play:

### 🎲 RandomAgent

Guesses randomly. A control case — shows how bad pure chance can perform.

### 🧊 FrequencyAgent

Ranks words by how often their letters appear across the word list. Exploits known patterns.

### ✨ EntropyAgent

Computes expected information gain (entropy) for each guess. Picks the word that splits the remaining space the most. Precise — but compute-heavy.

### 🌀 ExploreExploitAgent

Maximizes entropy for the first few rounds, then switches to frequency.

### ⚖️ SmartEntropyAgent

Dynamically blends entropy and frequency based on the remaining candidate set size. Starts curious, ends decisive.

### Observations

* Entropy picks weird words (e.g., “fjord”) to test rare letters. Great early, bad late.
* Frequency shines when only a few candidates remain.
* Hybrids offer balance and often win.

---

# 5. Evaluation Results: What Strategies Reveal

We ran thousands of games across varied word lists, tracking:

* Average guesses
* Win rate
* Compute time

### Key Takeaways

* EntropyAgent wins in fewest rounds, but is slow.
* SmartEntropyAgent balances accuracy and cost.
* FrequencyAgent often outperforms pure entropy late-game.

### Visual Suggestions

* Heatmaps: entropy per round
* Charts: guess efficiency vs strategy
* Outliers: when entropy fails or succeeds brilliantly

---

# 6. Beyond Wordle: Entropy in the Real World

These trade-offs appear everywhere:

* **Medicine**: How many tests are enough before acting?
* **Cybersecurity**: Which signal tells us the most about an intrusion?
* **Business**: When to stop A/B testing and choose a product?

> *"Wordle is bounded: 6 tries. So is your budget, your battery, your patient’s time. Entropy isn’t wrong — it’s just incomplete."*

Entropy helps us ask better questions. Strategy helps us decide when to stop asking.

---

# 7. Conclusion: Decisions Need Both Questions and Answers

Entropy is beautiful math. It gives us a lens to quantify surprise — to formalize curiosity.

But decision-making demands closure. It’s not just about learning — it’s about acting.

> *"Curiosity opens the door. Strategy walks through it."*

From thermodynamics to texting, from Vienna to the Sahara, from entropy to action — the best agents explore wisely, then commit.

---

# 🔗 Fork & Share Topics

* "Entropy is not enough" (agent failures)
* "From molecules to Wordle: the story of entropy"
* "Balancing exploration and exploitation in real decisions"
* "Implementing SmartEntropyAgent in Python"
* "Benchmarking Wordle solvers: insights and surprises"
