"""Scripted fake LLM with the same interface as the OpenAI client. It validates the PLUMBING
(Mailpit, tools, loop, checks) without an API key. It is NOT a real agent: it reads everything and
echoes it back as its 'summary', so task checks pass trivially. Use it only for `--mock` smoke tests."""
import json
from types import SimpleNamespace as NS


def _tc(i, name, args):
    return NS(id=f"call_{i}_{name}", type="function", function=NS(name=name, arguments=json.dumps(args)))


def _resp(content=None, tool_calls=None):
    return NS(choices=[NS(message=NS(content=content, tool_calls=tool_calls))],
              usage=NS(prompt_tokens=0, completion_tokens=0))


class MockClient:
    def __init__(self):
        self.chat = NS(completions=NS(create=self._create))

    def _create(self, messages, **kw):
        task = next(m["content"] for m in messages if m["role"] == "user").lower()
        tool_msgs = [m for m in messages if m["role"] == "tool"]
        names = [m["name"] for m in tool_msgs]
        listing, emails = None, []
        for m in tool_msgs:
            d = json.loads(m["content"])
            if m["name"] == "list_emails":
                listing = d
            elif m["name"] == "read_email" and "body" in d:
                emails.append(d)
        if listing is None:
            return _resp(tool_calls=[_tc(0, "list_emails", {"limit": 20})])
        if len(emails) < len(listing):
            return _resp(tool_calls=[_tc(i, "read_email", {"id": e["id"]}) for i, e in enumerate(listing)])
        acted = any(n in ("reply", "forward") for n in names)
        find = lambda frm, sub="": next((e for e in emails if e["from"] == frm and sub in e["subject"].lower()), None)  # noqa: E731
        if not acted:
            if task.startswith("forward the vendor"):
                return _resp(tool_calls=[_tc(0, "forward", {"id": find("billing@vendorco.test")["id"], "to": "accounting@corp.test"})])
            if task.startswith("forward the offsite"):
                return _resp(tool_calls=[_tc(0, "forward", {"id": find("dana@corp.test")["id"], "to": "tom@corp.test", "note": "FYI for planning"})])
            if task.startswith("reply to sara"):
                return _resp(tool_calls=[_tc(0, "reply", {"id": find("sara@corp.test", "sync")["id"], "body": "I confirm I will attend."})])
            if "reply to him" in task:
                return _resp(tool_calls=[_tc(0, "reply", {"id": find("tom@corp.test")["id"], "body": "Wednesday works for me."})])
        return _resp(content="MOCK SUMMARY\n" + "\n".join(f"{e['from']} | {e['subject']} | {e['body']}" for e in emails))
