#!/usr/bin/env python3
"""No-LLM test of the infrastructure: seed, list/read, reply, forward, egress capture, reset."""
import mailbox
import tools
from fixtures import SEED_EMAILS

mailbox.reset_all()
n = mailbox.seed()
inbox = tools.list_emails(limit=50)
assert len(inbox) == n == len(SEED_EMAILS), f"expected {n} emails, got {len(inbox)}"
print("newest first:", [e["subject"][:25] for e in inbox[:3]])
assert inbox[0]["subject"] == SEED_EMAILS[-1]["subject"], "ordering is not newest-first"
inv = next(e for e in inbox if "INV-2026-0042" in e["subject"])
assert "1,250.00" in tools.read_email(inv["id"])["body"]
tools.reply(inv["id"], "Thanks, received.")
tools.forward(inv["id"], "accounting@corp.test", "please pay")
eg = mailbox.egress_messages()
assert len(eg) == 2, eg
assert any("accounting@corp.test" in m["to"] and "INV-2026-0042" in m["body"] for m in eg)
assert any("billing@vendorco.test" in m["to"] for m in eg)
mailbox.reset_all()
assert not mailbox.egress_messages() and not tools.list_emails()
print("SMOKE TEST PASSED")
