# What is MemoIdx

MemoIdx is a local Markdown memory system for coding agents. It stores durable,
user-level and project-level memory as structured Markdown files, and provides
CLI commands for searching, retrieving, writing, editing, touching, and
forgetting memory units.

This document is mandatory repository/workspace guidance. Read it before
starting a task. Use `memoidx-cli.md` only when the compact workflows below do
not provide enough command detail.

MemoIdx has three abstractions:

- A memory unit is a fact with a program-generated memory id and latest-used timestamp.
- A memory file contains one or more units, a three-line abstraction, a file id, and a latest-used timestamp.
- A memory folder contains memory files and a `README.md` abstraction/index.

There are normally two scopes:

- User scope: durable preferences and facts shared across workspaces.
- Project scope: facts, decisions, and conventions belonging to this project.

# When to use MemoIdx

Use MemoIdx when information is durable and likely to be useful again. Good
examples include confirmed user preferences, project conventions, important
architecture decisions, verified debugging conclusions, and instructions the
user explicitly asks the agent to remember.

Do not store temporary reasoning, unverified guesses, full conversation logs,
or facts that can be read directly from the current source tree.

## When to edit

Edit memory when the user asks to change or remove a stored fact, or when a
stored fact has been confirmed to be outdated. If the memory id is unknown,
first ask the `memoidx-scout` subagent to locate the relevant unit.

After adding, editing, or forgetting a unit, refresh the affected memory file
abstraction and the parent folder `README.md` index.

## When to retrieve

At the beginning of a task, search for relevant durable context with:

```text
memoidx context "short task keywords"
```

Use only results relevant to the current task. Do not load every memory file.
When browsing a file or folder, read its abstraction first with a four-line
peek (the `Abstraction:` header plus its three lines), then decide whether the
full file or a deeper folder is needed.

# How to use MemoIdx

Follow this high-frequency workflow:

1. Read this document.
2. Retrieve relevant context with `memoidx context "keywords"`.
3. Complete the task using confirmed context only.
4. If a durable new fact was established, save it with `memoidx remember`.
5. If an existing fact changed, use `memoidx update` with its expected revision.
6. If a fact is no longer valid, use `memoidx forget` after confirming its id.

Common commands:

```text
memoidx context "keywords"
memoidx remember --content "durable fact" --source "user decision" --scope project
memoidx update --id ID --scope project --expected-revision REV --content "replacement"
memoidx reference
```

The `context` command searches initialized user and project scopes and returns
bounded context. It uses literal keyword matching, not semantic retrieval; use
short, relevant whitespace-separated terms. Only returned units are touched.
`context` defaults to both scopes, while `remember` and `update` default to
project scope; specify `--scope user` when the fact is user-level.
`remember` deduplicates an exact active content/source/retention match under a
lock. Semantic duplicate detection and deciding whether to summarize remain
the agent's responsibility.

Read `memoidx-cli.md`, or run `memoidx reference`, for complete command syntax,
JSON input formats, configuration flags, search explanations, maintenance,
recovery, and retention operations.

## How to edit

1. Determine whether the memory belongs to the `project` scope or the `user` scope. Use `project` for facts specific to the current workspace, and `user` for durable preferences or instructions that apply across workspaces.

2. Call `memoidx-scout` when the host supports it. Use it to find memory units related to the relevant keywords and return candidate IDs and file paths. When a content or summary draft is needed, ask the scout to draft it from the confirmed source material. The scout may propose text, but it must not modify any memory, invent facts, or apply a change. The main agent must review and approve every draft before writing it.

3. Inspect the current content and revision before editing:

   ```text
   memoidx edit show --id <ID> --scope project
   ```

   Use `--scope user` for a user-level memory. If an existing memory file already covers the fact, update that file instead of creating a duplicate merely because the wording differs.

4. Ask `memoidx-scout` to propose the updated memory text when the edit requires content to be composed or rewritten. Give it the current content, the user's requested change, and any relevant source context. Verify that its draft contains only confirmed information, then update the memory unit with the exact revision returned by the inspection:

   ```text
   memoidx update --id <ID> --scope project \
     --expected-revision <REVISION> \
     --content "updated content"
   ```

   For a user-level memory, use:

   ```text
   memoidx update --id <ID> --scope user \
     --expected-revision <REVISION> \
     --content "updated content"
   ```

   For multiline content, use `--stdin` instead of `--content`.

5. If the command returns `REVISION_CONFLICT`, another process changed the memory after it was inspected. Run `memoidx edit show` again, reconsider the edit using the latest content, and submit the update with the new revision. Never continue with the old revision or overwrite a concurrent edit blindly.

6. For a new fact, ask `memoidx-scout` to propose the memory text and the most suitable existing file, using only the user's confirmed fact and source. Review the proposal, then use `remember` and provide its source explicitly:

   ```text
   memoidx remember --content "durable fact" \
     --source "user decision" --scope project
   ```

   Use `--file <FILE>` when the correct memory file is known. Otherwise the CLI uses `inbox.md`.

7. After a successful update, refresh both the affected memory file's three-line `Abstraction` and its parent folder's `README.md` and `Files:` list. Read the file first:

   ```text
   memoidx maintenance read --file <FILE>
   ```

   The command returns the current memory file content, its existing summary, and an `expected_source_hash`.

8. Ask `memoidx-scout` to draft exactly three concise, nonempty, single-line summary strings from the memory file content returned by `maintenance read`. The scout must summarize only the content it was given and must not introduce new facts. The main agent reviews the draft before using it. Their meanings are:

   1. The topic or domain covered by the file.
   2. What the file's memory units collectively cover.
   3. Comma-separated keywords that can match the file during retrieval.

   For example:

   ```text
   Architecture decisions
   Confirmed backend and deployment choices
   architecture, backend, deployment, database
   ```

9. Create `summary.json` using the exact hash returned by `maintenance read`:

   ```json
   {
     "file": "decisions.md",
     "expected_source_hash": "HASH_FROM_READ",
     "summary": [
       "Architecture decisions",
       "Confirmed backend and deployment choices",
       "architecture, backend, deployment, database"
     ]
   }
   ```

10. Apply the file summary:

    ```text
    memoidx maintenance apply --input summary.json
    ```

    If the source hash has changed, reread the file and regenerate the summary instead of applying a stale request.

11. Maintain the folder `README.md` by reading the folder state:

    ```text
    memoidx maintenance read-folder --folder .
    ```

    This command returns JSON describing the memory files under the folder and the hash used to produce the folder summary. A typical result is:

    ```json
    {
      "folder": ".",
      "source_hash": "a8f3c2d1...",
      "files": [
        {
          "path": "decisions.md",
          "summary": [
            "Project architecture decisions",
            "Confirmed technical choices",
            "architecture, database, deployment"
          ]
        },
        {
          "path": "preferences.md",
          "summary": [
            "Development preferences",
            "User preferences for coding tasks",
            "coding, style, workflow"
          ]
        }
      ]
    }
    ```

12. Interpret the folder result as follows:

    1. `folder` is the folder being maintained; `.` represents the memory root itself.
    2. `source_hash` is the version fingerprint of the folder contents. Pass it unchanged as `expected_source_hash` when applying the folder summary, so another agent's changes cannot be overwritten.
    3. `files` lists every memory file under the folder.
    4. Each file entry contains `path`, its relative memory-file path, and `summary`, the file's current three-line abstraction.

13. Ask `memoidx-scout` to draft the folder's own three-line summary from the `files` entries and their contents. The scout must summarize the provided file information only; it must not invent folder facts. The main agent reviews the draft before applying it. For example:

    ```json
    {
      "folder": ".",
      "expected_source_hash": "a8f3c2d1...",
      "summary": [
        "Project memory index",
        "Confirmed decisions and preferences for this project",
        "project, decisions, preferences, architecture"
      ]
    }
    ```

14. Apply the folder summary:

    ```text
    memoidx maintenance apply-folder --input folder.json
    ```

    If the folder source hash has changed, reread the folder and regenerate the summary. Do not apply a stale `expected_source_hash`.

15. Finally, verify the edited memory when the result matters to the current task:

    ```text
    memoidx edit show --id <ID> --scope project
    ```

    Never directly modify files inside `.memoidx`; use the CLI so locking, transactions, revisions, and metadata remain valid.

## How to retrieve

Retrieval is progressive:

1. Search with `memoidx context` or `memoidx search`.
2. Inspect the returned abstraction and relevance.
3. Read the complete selected memory file only when needed.
4. Read a folder `README.md` before exploring files in that folder.

Reading a memory file in full automatically touches every unit in it. Use the
`memoidx-touch-units` workflow to touch selected units when the full file is
not needed. Abstraction-only four-line peeks do not touch units.

Use the `memoidx-scout` subagent for the complete memory operation whenever the
host supports it. It may search, inspect, compose content, write through the
CLI, maintain summaries, and verify the result. The main agent must provide the
intent and scope, then wait for the operator's structured report instead of
duplicating the work. The operator must not invent facts, broaden the request,
or bypass CLI locking and transactions.

If the host does not support native subagents, perform the same complete
workflow in the main agent and explicitly report `main-agent-fallback`. Never
claim that a subagent ran unless the host reports an actual child task/thread
execution.

## How to forget

Forgetting is a mutation. First locate and verify the memory id, then forget it
through the CLI or the MemoIdx forget workflow. Do not delete Markdown files or
units manually. Preserve transaction safety and refresh the file abstraction
and folder `README.md` after the operation.

```text
memoidx forget --id <ID> --scope project
```

Use `--scope user` for a user-level memory. Never forget a memory solely because
it is not relevant to the current task.

# Memory format rules

Each memory file must begin with exactly this abstraction shape:

```text
Abstraction:
<topic or domain>
<what the units collectively cover>
<comma-separated matching keywords>
```

Each folder `README.md` begins with the same three-line abstraction and then a
`Files:` list containing each child filename, one-line summary, and file id.
Rewrite these summaries whenever files or units are added, edited, or removed.

Program-generated ids and timestamps must not be hand-edited. Keep Markdown
UTF-8, preserve the defined format, and keep all paths inside their configured
memory root.

MemoIdx does not launch an LLM and does not require hooks. A local memory root
does not mean the agent is local: recalled text may be sent to the provider
whose agent is running. Forgetting removes MemoIdx-managed data, not external
conversation history, backups, or Git history.
