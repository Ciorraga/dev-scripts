# Branch Cleaner

Shell script to detect and optionally delete local Git branches that are safe candidates for cleanup.

By default, the script does not delete anything. It only shows the branches that could be removed.

## Features

- Detects local branches whose remote tracking branch is gone.
- Detects local branches already merged into a base branch.
- Uses the current branch as the base branch by default.
- Allows selecting a custom base branch.
- Allows running the script against a specific repository path.
- Protects common branches such as `main`, `master`, `develop`, `staging`, and `production`.
- Supports dry-run mode by default.
- Requires `--delete` to remove branches.
- Supports force delete with `--force`.
- Runs `git fetch --prune` by default before checking branches.

## Requirements

- Bash
- Git

## Usage

```bash
./branch-cleaner.sh [options]
```

## Examples

### Analyze the current repository

```bash
./branch-cleaner.sh
```

### Analyze a specific repository

```bash
./branch-cleaner.sh -p ~/workspace/service-users
```

### Use `develop` as the base branch

```bash
./branch-cleaner.sh -p ~/workspace/service-users -b develop
```

### Show only branches whose remote tracking branch is gone

```bash
./branch-cleaner.sh -p ~/workspace/service-users --gone-only
```

### Show only branches merged into `main`

```bash
./branch-cleaner.sh -p ~/workspace/service-users --merged-only -b main
```

### Delete detected branches

```bash
./branch-cleaner.sh -p ~/workspace/service-users --delete -b develop
```

### Delete without confirmation

```bash
./branch-cleaner.sh -p ~/workspace/service-users --delete --yes -b develop
```

### Force delete branches

```bash
./branch-cleaner.sh -p ~/workspace/service-users --delete --force --gone-only
```

### Skip remote pruning

```bash
./branch-cleaner.sh -p ~/workspace/service-users --no-fetch
```

### Show help

```bash
./branch-cleaner.sh --help
```

## Options

| Option | Description |
|---|---|
| `-p`, `--path <path>` | Path to the Git repository. Default: current directory. |
| `-b`, `--base <branch>` | Base branch used to detect merged branches. Default: current branch. |
| `--delete` | Delete detected branches. Without this option, the script only shows candidates. |
| `--force` | Force delete branches using `git branch -D`. By default, `git branch -d` is used. |
| `--yes` | Do not ask for confirmation when deleting. |
| `--gone-only` | Only show/delete branches whose remote tracking branch is gone. |
| `--merged-only` | Only show/delete branches already merged into the base branch. |
| `--no-fetch` | Do not run `git fetch --prune` before checking branches. |
| `--no-color` | Disable colored output. |
| `-h`, `--help` | Show help message. |

## Protected branches

The script never deletes these branches:

```text
main
master
develop
development
staging
release
production
```

It also never deletes the current branch.

## Notes

- By default, the script runs against the current directory.
- Use `-p` or `--path` to run it against a specific Git repository.
- The path must point to a Git repository, not to a folder containing multiple repositories.
- By default, it runs `git fetch --prune` to remove stale remote tracking references before checking local branches.
- Branches are only deleted when `--delete` is explicitly provided.
- Without `--force`, Git may refuse to delete branches that are not fully merged.
- Use `--force` carefully.