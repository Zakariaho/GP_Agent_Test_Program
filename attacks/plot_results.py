#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Person C -- render the measured attack results as clean figures for the report.

No live runs: these draw the numbers we already measured (reps=3 sweeps, saved in
results/multiling_*.json) so the whole evidence pack is consistent image files.

    .venv/bin/python attacks/plot_results.py     # writes results/figures/*.png
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.colors import LinearSegmentedColormap

from run_bandit import GROUND_TRUTH  # per-arm ASR from the reps=3 live sweeps

FIG_DIR = Path(__file__).resolve().parent.parent / "results" / "figures"
GOALS = ["G1", "G4", "G2"]
LANGS = ["EN", "MSA", "Gulf", "Arabizi"]
GOAL_LABEL = {"G1": "G1 forward invoice", "G4": "G4 exfil contacts", "G2": "G2 leak code"}
BLUES = LinearSegmentedColormap.from_list("b", ["#F4F7FB", "#1F6FEB", "#0B2E66"])


def heatmap():
    """ASR heatmap: rows = goal x language, cols = agent config. Method = D5 (reps=3)."""
    rows = [f"{g}.{l}" for g in GOALS for l in LANGS]
    cols = ["Permissive agent", "Hardened agent"]
    data = [[GROUND_TRUTH["permissive"][r], GROUND_TRUTH["default"][r]] for r in rows]

    fig, ax = plt.subplots(figsize=(6.2, 7.4))
    im = ax.imshow(data, cmap=BLUES, vmin=0, vmax=1, aspect="auto")
    ax.set_xticks(range(len(cols)), cols, fontsize=11, weight="bold")
    ax.set_yticks(range(len(rows)), rows, fontsize=10)
    for i in range(len(rows)):
        for j in range(len(cols)):
            v = data[i][j]
            ax.text(j, i, f"{v:.0%}", ha="center", va="center", fontsize=11,
                    color="white" if v >= 0.45 else "#14213D",
                    weight="bold" if v > 0 else "normal")
    # separate the three goal blocks
    for y in (3.5, 7.5):
        ax.axhline(y, color="white", lw=3)
    ax.set_title("Attack success rate by language and agent\n"
                 "method = D5 borrowed authority, 3 reps each",
                 fontsize=12, weight="bold", pad=12)
    cb = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cb.set_label("attack success rate", fontsize=9)
    fig.text(0.5, -0.02, "Hardening the agent's prompt drops success toward zero in every "
             "language; Arabic/Arabizi are no safer than English.",
             ha="center", fontsize=8.5, color="#555", wrap=True)
    FIG_DIR.mkdir(parents=True, exist_ok=True)
    out = FIG_DIR / "asr_heatmap.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"wrote {out}")


def goal_bars():
    """ASR by goal on the permissive agent (reps=3, averaged over the 4 languages)."""
    asr = {}
    for g in GOALS:
        vals = [GROUND_TRUTH["permissive"][f"{g}.{l}"] for l in LANGS]
        asr[g] = sum(vals) / len(vals)
    labels = [GOAL_LABEL[g] for g in GOALS]
    vals = [asr[g] for g in GOALS]
    colors = ["#1F6FEB" if v >= 0.5 else ("#7FB2E5" if v > 0 else "#C7CED9") for v in vals]

    fig, ax = plt.subplots(figsize=(8.2, 4.3))
    bars = ax.bar(labels, vals, color=colors, width=0.6)
    for b, v in zip(bars, vals):
        ax.text(b.get_x() + b.get_width() / 2, v + 0.02, f"{v:.0%}", ha="center",
                fontsize=12, weight="bold", color="#14213D")
    ax.set_ylim(0, 1.08)
    ax.set_ylabel("attack success rate")
    ax.set_title("Which goals the attacker can reach (permissive agent)",
                 fontsize=12, weight="bold")
    ax.yaxis.set_major_formatter(lambda x, _: f"{x:.0%}")
    ax.grid(True, axis="y", alpha=0.25, linewidth=0.6)
    ax.spines[["top", "right"]].set_visible(False)
    note = ("Forwarding an existing, innocent-looking email succeeds; making the agent reveal a "
            "secret code never does.\nGoals G3/G5/G8 (impersonate, steal prompt, fake approval) "
            "also measured 0%. Goals G6/G7 and methods D3/D7 need\nagent features this harness "
            "lacks, so they are out of scope here.")
    fig.text(0.5, -0.13, note, ha="center", fontsize=8.5, color="#555")
    out = FIG_DIR / "asr_by_goal.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"wrote {out}")


def scoreboard():
    """One-glance summary card of the headline numbers."""
    fig, ax = plt.subplots(figsize=(8.6, 3.0))
    ax.axis("off")
    cards = [
        ("Permissive, English", "44%", "#1F6FEB"),
        ("Permissive, Arabic", "37%", "#1F6FEB"),
        ("Hardened, English", "11%", "#6B7687"),
        ("Hardened, Arabic", "7%", "#6B7687"),
    ]
    for i, (label, num, col) in enumerate(cards):
        x = 0.02 + i * 0.245
        ax.add_patch(plt.Rectangle((x, 0.18), 0.22, 0.64, transform=ax.transAxes,
                                   facecolor="#F4F7FB", edgecolor=col, lw=2))
        ax.text(x + 0.11, 0.60, num, transform=ax.transAxes, ha="center", fontsize=30,
                weight="bold", color=col)
        ax.text(x + 0.11, 0.30, label, transform=ax.transAxes, ha="center", fontsize=10,
                color="#14213D")
    ax.text(0.5, 0.94, "Attack success rate (D5, reps=3): prompt hardening matters far more "
            "than language", transform=ax.transAxes, ha="center", fontsize=11.5, weight="bold")
    out = FIG_DIR / "asr_scoreboard.png"
    fig.savefig(out, dpi=200, bbox_inches="tight")
    print(f"wrote {out}")


if __name__ == "__main__":
    heatmap()
    goal_bars()
    scoreboard()
