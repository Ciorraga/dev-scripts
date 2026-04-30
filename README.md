# dev-scripts

Personal collection of scripts to automate common development tasks.

This repository contains small scripts and utilities that simplify repetitive development workflows, repository maintenance, local environment tasks, and small CLI operations.

## Scripts

### Shell

| Script | Description |
|---|---|
| [`update-repos.sh`](shell/update-repos.sh) | Updates the given branch across all Git repositories inside the current directory. |
| [`build-maven-projects.sh`](shell/build-maven-projects.sh) | Runs Maven goals across all Maven projects inside the current directory. |

See [`shell/README.md`](shell/README.md) for usage details.

### Python

| Script | Description |
|---|---|
| [`uuid7gen`](python/uuid7gen/) | Generates UUIDv7 identifiers from the command line. |
| [`uuid7_sql_replacer`](python/uuid7_sql_replacer/) | Replaces UUID values in simple SQL `INSERT` and `UPDATE` statements with UUIDv7 identifiers. |

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