#!/usr/bin/env python3
"""Reset mailboxes, seed, run benign tasks through the agent, check, and print a pass/fail table.

  python run.py --check                 # are Mailpit + API key OK?
  python run.py --all --reps 3          # full benign suite, 3 repetitions each
  python run.py --task 4 --reps 5       # one task
  python run.py --all --mock            # plumbing test, no API key needed
"""
import argparse
import json
import time
from pathlib import Path

import config
import mailbox
from agent import DEFAULT_SYSTEM_PROMPT, run_agent, make_client
from tasks import TASKS, check_task


def run_once(task, rep, client, system_prompt, model, max_steps):
    mailbox.reset_all()
    mailbox.seed()
    config.TRACE_DIR.mkdir(parents=True, exist_ok=True)
    trace = config.TRACE_DIR / f"task{task['id']}_rep{rep}.jsonl"
    trace.unlink(missing_ok=True)
    t0 = time.time()
    try:
        res = run_agent(task["prompt"], system_prompt=system_prompt, client=client, model=model,
                        max_steps=max_steps, trace_path=str(trace))
    except Exception as e:  # noqa: BLE001
        res = {"final": "", "steps": 0, "tool_calls": [], "usage": {"prompt_tokens": 0, "completion_tokens": 0},
               "stopped": "error", "error": f"{e.__class__.__name__}: {e}"}
    eg = mailbox.egress_messages()
    ok, why = check_task(task, res, eg)
    return {"task": task["id"], "rep": rep, "ok": ok, "reason": "" if ok else why,
            "steps": res["steps"], "sent": len(eg), "secs": round(time.time() - t0, 1),
            "prompt_tokens": res["usage"]["prompt_tokens"], "completion_tokens": res["usage"]["completion_tokens"],
            "final": res["final"][:500]}


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--check", action="store_true", help="health check and exit")
    ap.add_argument("--seed", action="store_true", help="reset + seed the mailbox and exit")
    ap.add_argument("--task", type=int, help="run a single task id (1-10)")
    ap.add_argument("--all", action="store_true", help="run all tasks")
    ap.add_argument("--reps", type=int, default=1)
    ap.add_argument("--mock", action="store_true", help="use scripted fake LLM (no API key)")
    ap.add_argument("--model", default=config.MODEL)
    ap.add_argument("--max-steps", type=int, default=8)
    ap.add_argument("--system-prompt-file", help="override the system prompt from a text file")
    a = ap.parse_args()

    if a.check:
        print("Mailpit:", mailbox.ping())
        print("DEEPSEEK_API_KEY set:", bool(config.API_KEY), "| model:", config.MODEL, "| thinking:", config.THINKING, "| base:", config.BASE_URL)
        return
    if a.seed:
        mailbox.reset_all()
        print(f"Seeded {mailbox.seed()} emails. Inbox UI: {config.INBOX_API}")
        return
    if not (a.task or a.all):
        ap.error("choose --task N, --all, --seed or --check")

    status = mailbox.ping()
    if any(v != "ok" for v in status.values()):
        raise SystemExit(f"Mailpit not reachable: {status}. Run `docker compose up -d` first.")

    if a.mock:
        from mock_llm import MockClient
        client = MockClient()
    else:
        client = make_client()
    system_prompt = Path(a.system_prompt_file).read_text() if a.system_prompt_file else DEFAULT_SYSTEM_PROMPT
    todo = TASKS if a.all else [t for t in TASKS if t["id"] == a.task]
    if not todo:
        raise SystemExit("no such task id")

    rows = []
    for t in todo:
        for rep in range(1, a.reps + 1):
            r = run_once(t, rep, client, system_prompt, a.model, a.max_steps)
            rows.append(r)
            print(f"task {t['id']:>2} rep {rep}: {'PASS' if r['ok'] else 'FAIL'}  {r['reason']}")

    print("\n| task | pass | avg steps | avg secs | tokens in/out |")
    print("|------|------|-----------|----------|---------------|")
    total_ok = 0
    for t in todo:
        rs = [r for r in rows if r["task"] == t["id"]]
        ok = sum(r["ok"] for r in rs)
        total_ok += ok
        n = len(rs)
        print(f"| {t['id']:>4} | {ok}/{n} | {sum(r['steps'] for r in rs)/n:.1f} | {sum(r['secs'] for r in rs)/n:.1f} | "
              f"{sum(r['prompt_tokens'] for r in rs)}/{sum(r['completion_tokens'] for r in rs)} |")
    print(f"\nOverall: {total_ok}/{len(rows)} passed  (model: {'MOCK' if a.mock else a.model})")

    config.RESULTS_DIR.mkdir(exist_ok=True)
    out = config.RESULTS_DIR / f"results_{time.strftime('%Y%m%d_%H%M%S')}{'_mock' if a.mock else ''}.json"
    out.write_text(json.dumps({"model": "MOCK" if a.mock else a.model, "rows": rows}, indent=2))
    print(f"Saved {out}; traces in {config.TRACE_DIR}")


if __name__ == "__main__":
    main()
