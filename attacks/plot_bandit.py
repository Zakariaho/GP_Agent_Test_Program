#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Person C -- learning-curve figure for the report.

Averages the bandit attacker over many random seeds (free sim mode, replaying our measured
per-arm attack-success rates) and plots cumulative successful attacks vs number of sends, for
the learning attacker (UCB1) against the try-everything-equally baseline (uniform). One panel
per agent configuration. Also writes a budget-allocation bar showing where the bandit spends
its sends.

    .venv/bin/python attacks/plot_bandit.py            # writes results/figures/*.png
"""
import random
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

from bandit import UCB1, RoundRobin
from run_bandit import GROUND_TRUTH
from multilingual import ATTACKS

ARMS = [x["id"] for x in ATTACKS]
ROUNDS = 150
SEEDS = 400

# Colorblind-safe, separable by hue AND lightness.
C_BANDIT = "#1F6FEB"   # blue
C_UNIFORM = "#E07A2F"  # amber
FIG_DIR = Path(__file__).resolve().parent.parent / "results" / "figures"


def averaged(policy_cls, truth):
    """Mean cumulative-success curve over SEEDS, plus final per-arm pull counts (last seed)."""
    acc = [0.0] * ROUNDS
    sq = [0.0] * ROUNDS
    last_pol = None
    for s in range(SEEDS):
        rng = random.Random(s)
        pol = policy_cls(ARMS)
        total = 0
        for r in range(ROUNDS):
            arm = pol.select()
            rew = 1 if rng.random() < truth[arm] else 0
            pol.update(arm, rew)
            total += rew
            acc[r] += total
            sq[r] += total * total
        last_pol = pol
    mean = [a / SEEDS for a in acc]
    std = [max(0.0, (sq[r] / SEEDS - mean[r] ** 2)) ** 0.5 for r in range(ROUNDS)]
    return mean, std, last_pol


def learning_curves():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4.4), sharex=True)
    titles = {"permissive": "Permissive agent", "default": "Hardened agent"}
    x = range(1, ROUNDS + 1)
    for ax, prompt in zip(axes, ["permissive", "default"]):
        truth = GROUND_TRUTH[prompt]
        bm, bs, _ = averaged(UCB1, truth)
        um, us, _ = averaged(RoundRobin, truth)
        ax.fill_between(x, [m - s for m, s in zip(bm, bs)], [m + s for m, s in zip(bm, bs)],
                        color=C_BANDIT, alpha=0.15, linewidth=0)
        ax.fill_between(x, [m - s for m, s in zip(um, us)], [m + s for m, s in zip(um, us)],
                        color=C_UNIFORM, alpha=0.15, linewidth=0)
        ax.plot(x, bm, color=C_BANDIT, lw=2.2, label="Learning attacker (UCB1 bandit)")
        ax.plot(x, um, color=C_UNIFORM, lw=2.2, ls="--", label="Try every attack equally")
        ax.set_title(titles[prompt], fontsize=12, weight="bold")
        ax.set_xlabel("Attack emails sent")
        ax.grid(True, alpha=0.25, linewidth=0.6)
        ax.spines[["top", "right"]].set_visible(False)
        gap = bm[-1] - um[-1]
        ax.annotate(f"+{gap:.0f} leaks", xy=(ROUNDS, bm[-1]), xytext=(ROUNDS * 0.62, bm[-1] * 0.78),
                    color=C_BANDIT, fontsize=10, weight="bold")
    axes[0].set_ylabel("Cumulative successful attacks")
    axes[0].legend(frameon=False, fontsize=9, loc="upper left")
    fig.suptitle("A learning attacker leaks more with the same number of sends",
                 fontsize=13, weight="bold", y=1.02)
    fig.text(0.5, -0.04, f"Mean of {SEEDS} runs; bands = ±1 SD. Arms = 12 D5 attacks "
             "(goals G1/G4/G2 × EN/MSA/Gulf/Arabizi). Reward rates from reps=3 live measurements.",
             ha="center", fontsize=8, color="#555")
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "bandit_learning_curve.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"wrote {out}")


def budget_allocation():
    """Where the bandit spends its sends on the permissive agent (last-seed snapshot)."""
    _, _, pol = averaged(UCB1, GROUND_TRUTH["permissive"])
    order = sorted(ARMS, key=lambda a: -pol.counts[a])
    counts = [pol.counts[a] for a in order]
    good = [GROUND_TRUTH["permissive"][a] >= 0.5 for a in order]
    colors = [C_BANDIT if g else "#B9C2D0" for g in good]
    fig, ax = plt.subplots(figsize=(8.5, 4.2))
    ax.bar(range(len(order)), counts, color=colors)
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels(order, rotation=45, ha="right", fontsize=9)
    ax.set_ylabel(f"Sends (out of {ROUNDS})")
    ax.set_title("The bandit concentrates its sends on the attacks that work",
                 fontsize=12, weight="bold")
    ax.grid(True, axis="y", alpha=0.25, linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    ax.annotate("Blue = working arms: forward-invoice, in every language",
                xy=(1.5, max(counts)), xytext=(4.1, max(counts) * 0.72),
                color="#14213D", fontsize=10, weight="bold",
                arrowprops=dict(arrowstyle="->", color="#14213D", lw=1.2))
    out = FIG_DIR / "bandit_budget_allocation.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    learning_curves()
    budget_allocation()
