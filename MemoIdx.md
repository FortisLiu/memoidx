# Abstraction

This file introduces how to use memoidx memory framework.

# MemoIdx Memory Elements

### Basic Unit

A memoidx memory unit includes fact(content), memory id and latest used time.

Saving format:

```text
Memory id: <id>
Latest used time: <timestamp>
Content:
<content>
```

### File

A memoidx memory file contains one or several memory units, abstraction, file id and latest used time.

Saving format:

```text
Abstraction:
<abstraction in three lines>
file id: <id>
Latest used time: <timestamp>

<memory unit 1>

<memory unit 2>
```

### Folder

A memoidx memory folder contains several memory files and a README.md files.

The README.md files is abstraction of memory files in this folder

# Operation

- Writing: Before writing, call 'wfm' subagent to check if an existing memory file already fits the content. Write into that file if found; otherwise create a new file. Then use `memoidx-write` skill.
- Editing: use `memoidx-edit` skill. If memory id is unknown, call 'wfm' subagent to find it at first.
- Deleting: use `memoidx-forget` skill. If memory id is unknown, call 'wfm' subagent to find it at first.
- Abstraction: After writing, edition and deleting, call 'wfm' subagent to modify the memory file abstraction and folder README.md file.
- Retrieval: Always read the abstraction first using `Read(file_path, limit=4)` (do not read the full file), then decide whether to load the entire memory file or dig into the memory folder. Also read README.md files the same way when browsing a folder.
- Touch: Reading a memory file in full auto-touches every unit in it (PostToolUse hook; abstraction-only `Read(limit=4)` peeks are skipped). To touch specific unit(s) manually, use the `memoidx-touch-units` skill (`--ids ...`); if the memory id is unknown, call the 'wfm' subagent to find it first.

# Timing

Save whatever you require whenever needed.

# MemoIdx Memory structure

# Abstraction & README format

### File abstraction

The `Abstraction:` block is exactly three lines (so retrieval reads it with `Read(file_path, limit=4)` — the header plus three lines):

```text
Abstraction:
<line 1: topic/domain this file is about>
<line 2: scope — what the units in this file collectively cover>
<line 3: keywords for matching, comma-separated>
```

Rewrite the abstraction whenever a unit in the file is created, appended, edited, or forgotten. Keep it three lines; never leave the `(auto-generated)` placeholder.

### Folder README.md

`README.md` is a folder-level index, also read with `Read(path, limit=4)` for the top block:

```text
Abstraction:
<line 1: what this folder groups>
<line 2: when to look here>
<line 3: keywords, comma-separated>

Files:
- <filename> — <one-line summary> (file id: <id>)
- ...
```

Refresh the `Files:` list and the top block whenever a file is added to or removed from the folder.
