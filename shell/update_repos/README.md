# Update Repositories

Shell script to update a target branch across all Git repositories inside the current directory.

The target branch is mandatory and must be provided using `-b`.

## Features

- Processes all Git repositories inside the current directory.
- Updates the branch provided with `-b`.
- Skips repositories with uncommitted changes.
- Switches to the target branch when possible.
- Pulls changes using fast-forward only.
- Reports updated and failed repositories in a final summary.
- Uses colored output.

## Requirements

- Bash
- Git

## Usage

```bash
./update-repos.sh -b <branch>
```

## Examples

### Update all repositories to `develop`

```bash
./update-repos.sh -b develop
```

### Update all repositories to `main`

```bash
./update-repos.sh -b main
```

### Show help

```bash
./update-repos.sh -h
```

## Options

| Option | Description |
|---|---|
| `-b <branch>` | Branch to update. Required. |
| `-h` | Show help message. |

## Notes

- The script must be executed from a directory containing Git repositories as direct child folders.
- Repositories with uncommitted changes are skipped.
- The script uses `git pull --ff-only` to avoid creating merge commits automatically.
- If a repository cannot be updated safely, it is reported in the final summary.