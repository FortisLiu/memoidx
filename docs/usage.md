# Development CLI

Run from the checkout with `python -m memoidx`, or install the package and use
`memoidx`. Global flags such as `--config` and `--json` precede the subcommand.

Create a configuration in a test directory:

```json
{"user_root":"user/.memoidx","project_root":"project"}
```

Relative paths are anchored to the configuration file. Project paths point to
the project directory; `.memoidx` is appended when it is not already present.

```text
python -m memoidx --config path/to/config.json init --scope project
python -m memoidx --config path/to/config.json edit add --input path/to/add.json
python -m memoidx --config path/to/config.json search "keywords"
python -m memoidx --config path/to/config.json recall --id <returned-unit-id>
python -m memoidx --config path/to/config.json maintenance plan
python -m memoidx --config path/to/config.json maintenance read --file preferences.md
python -m memoidx --config path/to/config.json maintenance apply --input summary.json
python -m memoidx --config path/to/config.json maintenance folders
python -m memoidx --config path/to/config.json maintenance read-folder --folder .
python -m memoidx --config path/to/config.json maintenance apply-folder --input folder.json
python -m memoidx --config path/to/config.json gc --dry-run
python -m memoidx --config path/to/config.json gc --if-due
python -m memoidx --config path/to/config.json trash list
python -m memoidx --config path/to/config.json restore --id <returned-unit-id>
python -m memoidx --config path/to/config.json forget --id <returned-unit-id>
python -m memoidx --config path/to/config.json recover
python -m memoidx --config path/to/config.json doctor
python -m memoidx protocol
```

Add input contains request_id, file, content, retention (normal or pinned), and
source. Update input contains request_id, id, expected_revision, and content.
Use edit show --id to obtain the revision. IDs and timestamps come from the
program. Summary apply input contains file, expected_source_hash, and exactly
three summary strings; folder apply uses folder instead of file.

Search returns a search_id for `explain --search-id ... --id ...`. Search traces
retain matching terms, IDs, revisions and scores, but not full memory bodies.
GC expires old traces and forget removes traces related to the forgotten unit.

See acceptance.md for tested behavior and outstanding release requirements.
