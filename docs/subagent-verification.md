# Verify native MemoIdx delegation

Supported generated adapters: Codex custom-agent TOML and Claude Code
subagent Markdown. Other hosts can pass memoidx-scout.md to their native
child tool; without that tool, report main-agent-fallback. This is not a
claim that every host automatically discovers these files. The child now
executes the complete requested memory operation, including maintenance and
verification.

## Install

Install the current checkout/wheel, then run:

```
memoidx-init --workspace PATH_TO_WORKSPACE
```

Generated files:
- memoidx-scout.md: shared selection contract
- .codex/agents/memoidx_scout.toml: Codex native definition
- .claude/agents/memoidx-scout.md: Claude native definition
- AGENTS.md and CLAUDE.md: delegation routing appended once

Existing MemoIdx.md and custom agent definitions are preserved. Review kept
definitions if the platform does not discover the scout. Restart the host
session after installing. No model is pinned and no permission setting or
global platform configuration is changed. CLI must be on the child PATH.

## Isolated acceptance exercise

Use a disposable workspace and isolated user root, not real memories:

```
memoidx-init --workspace PATH_TO_PROBE --user-root PATH_TO_PROBE_USER
```

In the probe directory run:

```
memoidx remember --content "scout_probe_731 callback uses /oauth/callback" --source "test fixture"
memoidx edit show --id RETURNED_ID
```

Save the ID and LUT from edit show. Open a NEW host session in this directory.
Send this prompt (replace the native name for the host):

> Delegate the complete retrieval of scout_probe_731 to the native
> memoidx_scout subagent (Claude: memoidx-scout). Pass this workspace, project
> scope and limit 1. Do not search in the main agent. Wait for the child to
> complete the operation and return its JSON report with the native child
> task/thread event.
> If delegation is unavailable, report it; do not simulate a subagent.

## Codex

Inspect the host's tool/activity transcript for an actual child creation event
(commonly spawn_agent), its child ID and a completion/wait result. Open the
child activity if the surface exposes it and confirm search ran there. Check
the selected custom role/name is memoidx_scout, not just text in a response.
If the host/version does not load custom TOML, ask it to spawn a generic native
child with the shared contract and label that path explicitly. If no spawn
tool is available, the test is unavailable, not passed. Merely opening a
second independent Codex session is not parent-child delegation evidence.

## Claude Code

Use /agents to confirm memoidx-scout is discovered. That proves registration
only. For execution, inspect the Agent tool invocation (older versions may
label it Task), requested subagent type, child tool activity and returned
completion. /agents alone and the sentence "I used the scout" do not prove
execution. Expand the task/tool activity in the interface when available.

## Result checks for either platform

1. Native parent-child event and completion exist in the host transcript.
2. Returned ID equals the fixture ID and search_id refers to a real trace.
3. `memoidx explain --search-id SEARCH_ID --id ID` confirms candidate evidence.
4. `memoidx edit show --id ID` has the original LUT: selection did not touch.
5. Ask the MAIN agent to recall that ID. Its recall event should be in the
   parent activity and a subsequent edit show should have a newer LUT.

Search traces prove searches, not identity: the main agent could generate
the same trace. A returned agent_id or execution label is also not proof
without a matching host event. Keep host transcript evidence for acceptance.
Shell access allows more than the scout instructions permit; this contract
is behavioral guidance, not an enforced command whitelist. No hooks are used.

The automated suite checks generation, preservation, packaging and CLI
semantics. Live native delegation must be exercised in each installed host;
it cannot be certified by unit tests or a CLI self-reported flag.

Official references (verify against your installed host version):
- https://developers.openai.com/codex/subagents
- https://code.claude.com/docs/en/subagents
