"""Native wrappers around the shared, workspace-local scout contract."""

import json

SCOUT_FILES = ("memoidx-scout.md", ".claude/agents/memoidx-scout.md",
               ".codex/agents/memoidx_scout.toml")

ROUTING = """<!-- memoidx-scout-routing-v2 -->
Delegate every MemoIdx memory operation to the native MemoIdx operator
(Codex: memoidx_scout; Claude Code: memoidx-scout). Pass the absolute workspace
path, the requested operation, the user's intent, and the relevant scope. The
child must read memoidx-scout.md there and complete the entire operation:
search, inspect, decide, write, maintain summaries, and verify. Wait for its
structured report; do not duplicate its CLI work in the main agent. If native
delegation is unavailable, explicitly report main-agent-fallback and perform
the same complete workflow yourself. Never claim a subagent ran without a
platform child-task/thread event.
<!-- /memoidx-scout-routing-v2 -->
"""


def native_templates():
    prompt = ("You are the MemoIdx memory operator. Read memoidx-scout.md at the absolute "
              "workspace path supplied by the parent and follow its end-to-end operator contract. "
              "Do not delegate again. Complete the requested memory operation yourself using "
              "the MemoIdx CLI, including search, inspection, writing, maintenance and verification. "
              "Return only the contract's compact JSON operation report. If the contract or CLI "
              "is unavailable, report blocked rather than inventing memories.")
    return {
        SCOUT_FILES[1]: "---\nname: memoidx-scout\ndescription: Complete MemoIdx memory operations for the parent agent.\ntools: Read, Bash\nmodel: inherit\n---\n\n" + prompt + "\n",
        SCOUT_FILES[2]: 'name = "memoidx_scout"\ndescription = "Complete MemoIdx memory operations for the parent agent."\ndeveloper_instructions = ' + json.dumps(prompt) + "\n",
    }
