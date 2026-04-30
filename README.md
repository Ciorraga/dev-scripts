# dev-scripts

Personal collection of scripts to automate common development tasks.

This repository contains small scripts and utilities that I use to simplify repetitive development workflows, repository maintenance, and local environment tasks.

## Scripts

| Script | Description |
|---|---|
| `update-repos.sh` | Updates the given branch across all Git repositories inside the current directory. |
| `build-maven-projects.sh` | Runs Maven goals across all Maven projects inside the current directory. |

## Requirements

Most scripts are written in Bash and are intended to run on Unix-like systems such as Linux or macOS.

Depending on the script, you may need some tools installed locally:

- Git
- Maven

Some scripts may use project-specific wrappers, such as Maven Wrapper, when available.

## Usage

### `update-repos.sh`

Updates a target branch across all Git repositories inside the current directory.

The branch is mandatory and must be provided using `-b`.

```bash
./update-repos.sh -b <branch>
```

### `build-maven-projects.sh`

Runs Maven goals across all Maven projects inside the current directory.

#### Usage

```bash
./build-maven-projects.sh [options]
```