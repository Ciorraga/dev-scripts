# dev-scripts

Personal collection of scripts to automate common development tasks.

This repository contains small scripts and utilities that simplify repetitive development workflows, repository maintenance, local environment tasks, and small CLI operations.

## Scripts

### Shell

| Script | Description |
|---|---|
| [`update-repos`](shell/update-repos/) | Updates the given branch across all Git repositories inside the current directory. |
| [`build-maven-projects`](shell/build-maven-projects/) | Runs Maven goals across all Maven projects inside the current directory. |
| [`branch-cleaner`](shell/branch-cleaner/) | Detects and optionally deletes local Git branches that are merged or have a gone remote tracking branch. |
| [`repo-status-all`](shell/repo-status-all/) | Shows branch, local changes, upstream, and sync status for all Git repositories inside the current directory. |

See [`shell/README.md`](shell/README.md) for the Shell scripts index.

### Python

| Script | Description |
|---|---|
| [`uuid7gen`](python/uuid7gen/) | Generates UUIDv7 identifiers from the command line. |
| [`uuid7_sql_replacer`](python/uuid7_sql_replacer/) | Replaces UUID values in simple SQL `INSERT` and `UPDATE` statements with UUIDv7 identifiers. |
| [`update_sql_field_from_csv`](python/update_sql_field_from_csv/) | Updates a SQL field using values from a CSV file. |

See [`python/README.md`](python/README.md) for the Python scripts index.

## Requirements

Requirements depend on each script.

Common tools used by these scripts include:

- Bash
- Git
- Maven
- Python 3

Check each script README for specific requirements and usage instructions.

## Disclaimer

These scripts are mainly built for personal workflows, but feel free to use, adapt, or improve them.