"""Native wrappers around the shared, workspace-local scout contract."""

import json

SCOUT_FILES = ("memoidx-scout.md", ".claude/agents/memoidx-scout.md",
               ".codex/agents/memoidx_scout.toml")

ROUTING = """<!-- memoidx-scout-routing-v1 -->
For memory lookup and candidate selection, delegate to the native MemoIdx
scout (Codex: memoidx_scout; Claude Code: memoidx-scout). Pass the absolute
workspace path, task, requested scopes and limit; the child must read
memoidx-scout.md there. Wait for its selection, then recall selected IDs in
the main agent using the returned scopes. Do not run context before delegation.
If native delegation is unavailable, explicitly report main-agent-fallback
and follow the scout contract yourself. Never claim a subagent ran without
a platform child task/thread event. This routing applies even to an older
MemoIdx.md that recommends context by default.
<!-- /memoidx-scout-routing-v1 -->
"""


def native_templates():
    prompt = ("You are the MemoIdx memory scout. Read memoidx-scout.md at the absolute "
              "workspace path supplied by the parent and follow its selection-only contract. "
              "Do not delegate again. Use search/browse/edit show, never context or recall. "
              "Return compact JSON selections with search_id evidence. If the contract "
              "or CLI is unavailable, report blocked rather than inventing memories.")
    return {
        SCOUT_FILES[1]: "---\nname: memoidx-scout\ndescription: Select relevant MemoIdx memories for the parent agent.\ntools: Read, Bash\nmodel: inherit\n---\n\n" + prompt + "\n",
        SCOUT_FILES[2]: 'name = "memoidx_scout"\ndescription = "Select relevant MemoIdx memories for the parent agent."\ndeveloper_instructions = ' + json.dumps(prompt) + "\n",
    }
