# MemoIdx CLI reference

Global flags precede commands: `memoidx [--config FILE] [--json] COMMAND`.
Use `memoidx COMMAND --help` for arguments. Default scope is project except
context (both). Use --scope user for cross-project preferences. The nearest
.memoidx is discovered from nested directories; roots.json supplies custom
roots. Explicit --config wins. Relative roots resolve against the config file.
config.json inside each root contains retention settings, not root discovery.

## Frequent operations

```
memoidx context "auth OAuth" --limit 5 --max-chars 6000
memoidx --json context "auth" --scope project
memoidx remember --content "fact" --source "user decision" --file decisions.md
memoidx remember --stdin --source "user decision" --scope user --retention pinned
memoidx edit show --id ID
memoidx update --id ID --expected-revision REV --content "replacement"
memoidx update --id ID --expected-revision REV --stdin
```

Context uses keyword scoring, the top ten candidate window and score-first
ordering (project wins ties). Limit is 1–10. max-chars caps total returned
content characters, NOT tokens or metadata. Oversized units are skipped whole
without touching them. Only returned units refresh LUT. JSON returns memories,
skipped and content_chars. Text returns one JSON-escaped memory per line with
scope, ID, path, revision, source and content. Missing roots are skipped;
malformed existing roots fail. No model is called. Search writes a trace.

Remember defaults to inbox.md and normal retention. Within one root lock,
identical active content/source/retention returns status=duplicate without
touching it; otherwise status=created. This is exact deduplication, not semantic
matching. Search for related facts before storing. It does not generate summaries.
Update requires the revision you actually read and changes content only.

## Retrieval and diagnostics

```
memoidx search "keywords" --scope project
memoidx recall --id ID --scope project
memoidx explain --search-id SEARCH_ID --id ID
memoidx browse file --path decisions.md
memoidx browse folder --path .
memoidx tree
memoidx doctor
memoidx recover
```

Search returns up to ten candidates, snippets, scores and search IDs without
refreshing LUT. Recall returns and touches one complete unit. Browse, show and
maintenance do not touch. Resolve RECOVERY_REQUIRED using recover in the affected
scope. For REVISION_CONFLICT reread and reconsider, never blindly replace REV.
REQUEST_CONFLICT means a request ID was reused with different input.

## Low-level writes (UTF-8 JSON files)

`memoidx edit add --input add.json` requires:
`{"request_id":"retry-key","file":"facts.md","content":"fact","source":"source","retention":"normal"}`.
`memoidx edit update --input update.json` requires:
`{"request_id":"retry-key","id":"u_UUID","expected_revision":"HASH","content":"replacement"}`.
Reuse identical request IDs and payloads only for retries. Program generates
IDs and timestamps. High-level remember generates its own request ID; exact
active duplicates are handled separately.

## Summary maintenance

```
memoidx maintenance plan
memoidx maintenance check
memoidx maintenance read --file facts.md
memoidx maintenance apply --input summary.json
memoidx maintenance folders
memoidx maintenance read-folder --folder .
memoidx maintenance apply-folder --input folder.json
```

File apply input: `{"file":"facts.md","expected_source_hash":"HASH_FROM_READ","summary":["topic","scope","keywords"]}`.
Folder apply input: `{"folder":".","expected_source_hash":"HASH_FROM_READ","summary":["topic","when to look","keywords"]}`.
The agent supplies exactly three nonempty single-line strings. After writes,
repair file summaries, refresh listings if needed, then apply folder summaries
from children upward. Listing refresh neutralizes existing folder summaries.
Stale summaries are excluded from scoring. Python never launches an LLM.

## Lifecycle

```
memoidx gc --dry-run
memoidx gc --if-due
memoidx trash list
memoidx restore --id ID
memoidx forget --id ID
memoidx init --scope user
memoidx init --scope project
```

All lifecycle commands accept --scope user/project. GC defaults to six calendar
months since use, excludes pinned units and keeps trash 30 days. It runs only
when invoked; --if-due limits runs to daily. Restore refreshes LUT. Forget is
explicit permanent removal within managed storage, not backups or conversations.
Never edit memory or transaction files directly.
