#!/usr/bin/env python3
"""Verify the SteganoPrompt encoding: round-trip correctness, payload
invisibility, and visible-text preservation.

Run from this folder:  python test_encoding.py
Requires no access token and makes no network calls.
"""
import sys
import evaluate as E

ok = True


def check(name, cond):
    global ok
    print(f"  [{'PASS' if cond else 'FAIL'}] {name}")
    ok = ok and cond


# 1. Known example: E("Hi!\n") = <U+E0048, U+E0069, U+E0021, U+E000A>
enc = E.encode_tags("Hi!\n")
expected = "".join(chr(cp) for cp in (0xE0048, 0xE0069, 0xE0021, 0xE000A))
check("known example E('Hi!\\n')", enc == expected)

# 2. Round-trip identity on the payload and every assignment prompt
check("round-trip on the integrity payload",
      E.decode_tags(E.encode_tags(E.FIXED_POLICY)) == E.FIXED_POLICY)
for t in E.ASSIGNMENTS:
    check(f"round-trip on task '{t['id']}'",
          E.decode_tags(E.encode_tags(t["text"])) == t["text"])

# 3. Encoded payload is fully invisible (every char sits in the Tag block)
payload = E.encode_tags(E.compose_hidden())
check("payload is 100% Unicode-Tag chars",
      all(E.TAG_RANGE_LO <= ord(c) <= E.TAG_RANGE_HI for c in payload))

# 4. Watermarked prompt: visible text unchanged, hidden payload decodes back,
#    and it ends with the integrity token
for t in E.ASSIGNMENTS:
    wm = E.build_prompt(t["text"], "end")
    visible = "".join(c for c in wm if not (E.TAG_RANGE_LO <= ord(c) <= E.TAG_RANGE_HI))
    hidden = E.decode_tags(wm)
    check(f"visible text preserved for '{t['id']}'", visible == t["text"])
    check(f"hidden decodes to payload for '{t['id']}'", hidden == E.compose_hidden())
    check(f"decoded payload ends with token for '{t['id']}'",
          hidden.strip().endswith(E.INTEGRITY_TOKEN))

# 5. Placement variants
start = E.build_prompt("Hello world.", "start")
check("start placement puts payload first",
      start.endswith("Hello world.")
      and E.TAG_RANGE_LO <= ord(start[0]) <= E.TAG_RANGE_HI)

print("\nRESULT:", "ALL PASS" if ok else "FAILURES PRESENT")
sys.exit(0 if ok else 1)
