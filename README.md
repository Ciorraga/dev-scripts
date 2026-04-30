# dev-scripts

Personal collection of scripts to automate common development tasks.

This repository contains small scripts and utilities that I use to simplify repetitive development workflows, repository maintenance, local environment tasks, and small CLI utilities.

## Scripts

### Shell scripts

| Script | Description |
|---|---|
| [`update-repos.sh`](shell/update-repos.sh) | Updates the given branch across all Git repositories inside the current directory. |
| [`build-maven-projects.sh`](shell/build-maven-projects.sh) | Runs Maven goals across all Maven projects inside the current directory. |

See [`shell/README.md`](shell/README.md) for usage details.

### Python scripts

| Script | Description |
|---|---|
| [`uuid7gen.py`](python/uuid7gen.py) | Generates UUIDv7 identifiers from the command line. |

See [`python/README.md`](python/README.md) for usage details.

## Requirements

Requirements depend on each script.

Common tools used by these scripts include:

- Bash
- Git
- Maven
- Python 3

Check each script section for specific requirements and usage examples.

## Disclaimer

These scripts are mainly built for personal workflows, but feel free to use, adapt, or improve them.