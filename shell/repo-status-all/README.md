# Repository Status All

Shell script to show the status of all Git repositories inside a target directory.

It is useful when working with multiple repositories and you want a quick overview of their current branch, local changes, upstream status, and synchronization state.

## Features

- Processes all Git repositories inside a target directory.
- Uses the current directory by default.
- Allows selecting a specific path with `-p` or `--path`.
- Shows the current branch for each repository.
- Detects clean or dirty working trees.
- Shows upstream branch information.
- Detects repositories that are:
  - up to date
  - ahead
  - behind
  - diverged
  - without upstream
  - in detached HEAD state
- Optionally runs `git fetch --prune` before checking status.
- Provides a final summary.
- Uses colored output.

## Requirements

- Bash
- Git

## Usage

```bash
./repo-status-all.sh [options]
```

## Examples

### Check repositories in the current directory

```bash
./repo-status-all.sh
```

### Check repositories in a specific path

```bash
./repo-status-all.sh -p ~/workspace/services
```

### Fetch remote changes before checking

```bash
./repo-status-all.sh -p ~/workspace/services --fetch
```

### Show skipped non-Git directories

```bash
./repo-status-all.sh -p ~/workspace/services --show-skipped
```

### Fetch and show skipped directories

```bash
./repo-status-all.sh -p ~/workspace/services --fetch --show-skipped
```

### Disable colored output

```bash
./repo-status-all.sh --no-color
```

### Show help

```bash
./repo-status-all.sh --help
```

## Options

| Option | Description |
|---|---|
| `-p`, `--path <path>` | Path containing Git repositories. Default: current directory. |
| `--fetch` | Run `git fetch --prune` before checking each repository. |
| `--show-skipped` | Show directories that are not Git repositories. |
| `--no-color` | Disable colored output. |
| `-h`, `--help` | Show help message. |

## Output example

```text
Repository                          Branch                    Changes      Sync               Upstream
----------                          ------                    -------      ----               --------
service-users                       develop                   clean        up-to-date         origin/develop
service-orders                      feature/JIRA-123          dirty        ahead 2            origin/feature/JIRA-123
service-billing                     develop                   clean        behind 3           origin/develop
service-notifications               hotfix/fix-timeout        clean        diverged +1/-2     origin/hotfix/fix-timeout
service-legacy                      master                    dirty        no upstream        -
```

## Exit codes

| Exit code | Meaning |
|---|---|
| `0` | All repositories are clean and synchronized. |
| `1` | One or more repositories are dirty, behind, diverged, in detached HEAD state, or had fetch errors. |

## Notes

- By default, the script checks Git repositories inside the current directory.
- Use `-p` or `--path` to check repositories inside a specific directory.
- The selected path must point to a directory containing Git repositories as direct child folders.
- By default, it does not fetch remote changes.
- Use `--fetch` if you want up-to-date ahead/behind information.
- Directories that are not Git repositories are skipped by default.
- Use `--show-skipped` to display skipped directories.