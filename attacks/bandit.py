# -*- coding: utf-8 -*-
"""Person C -- the learning attacker: a multi-armed bandit over attack strategies.

No training, no GPU, no dependencies -- just counts and a formula. Each arm is one attack
strategy; pulling an arm = sending that attack and seeing if it leaked (reward 1) or was
blocked (reward 0). UCB1 spends most of its budget on the arms that work while still
occasionally probing the rest, so it finds the effective attack with far fewer sends than
trying every strategy equally.

    bandit = UCB1(arm_ids)
    arm = bandit.select()
    bandit.update(arm, reward)   # reward in {0, 1}
"""
import math
import random


class UCB1:
    """Upper Confidence Bound (UCB1). Deterministic given the reward stream."""

    def __init__(self, arms, c=1.4):
        self.arms = list(arms)
        self.c = c                       # exploration weight (sqrt(2) ~ 1.4 is standard)
        self.counts = {a: 0 for a in self.arms}
        self.value = {a: 0.0 for a in self.arms}   # running mean reward
        self.t = 0

    def select(self):
        self.t += 1
        # Try each arm once before using the UCB formula.
        for a in self.arms:
            if self.counts[a] == 0:
                return a
        best, best_score = None, -1.0
        for a in self.arms:
            bonus = self.c * math.sqrt(math.log(self.t) / self.counts[a])
            score = self.value[a] + bonus
            if score > best_score:
                best, best_score = a, score
        return best

    def update(self, arm, reward):
        self.counts[arm] += 1
        n = self.counts[arm]
        self.value[arm] += (reward - self.value[arm]) / n   # incremental mean

    def best_arm(self):
        return max(self.arms, key=lambda a: self.value[a])


class EpsilonGreedy:
    """Simple baseline: explore at random with prob. epsilon, else exploit the best mean."""

    def __init__(self, arms, epsilon=0.1, rng=None):
        self.arms = list(arms)
        self.epsilon = epsilon
        self.rng = rng or random.Random(0)
        self.counts = {a: 0 for a in self.arms}
        self.value = {a: 0.0 for a in self.arms}

    def select(self):
        if self.rng.random() < self.epsilon or all(self.counts[a] == 0 for a in self.arms):
            return self.rng.choice(self.arms)
        return max(self.arms, key=lambda a: self.value[a])

    def update(self, arm, reward):
        self.counts[arm] += 1
        n = self.counts[arm]
        self.value[arm] += (reward - self.value[arm]) / n

    def best_arm(self):
        return max(self.arms, key=lambda a: self.value[a])


class RoundRobin:
    """Uniform allocation baseline: spend the budget equally across all arms."""

    def __init__(self, arms):
        self.arms = list(arms)
        self.i = -1
        self.counts = {a: 0 for a in self.arms}
        self.value = {a: 0.0 for a in self.arms}

    def select(self):
        self.i = (self.i + 1) % len(self.arms)
        return self.arms[self.i]

    def update(self, arm, reward):
        self.counts[arm] += 1
        n = self.counts[arm]
        self.value[arm] += (reward - self.value[arm]) / n

    def best_arm(self):
        return max(self.arms, key=lambda a: self.value[a])
