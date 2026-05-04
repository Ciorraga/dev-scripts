# Update Repositories

Shell script to update a target branch across all Git repositories inside a target directory.

The target branch is mandatory and must be provided using `-b`.

By default, the script checks repositories inside the current directory. You can provide a specific path using `-p`.

## Features

- Processes all Git repositories inside a target directory.
- Uses the current directory by default.
- Allows selecting a specific path with `-p`.
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
./update-repos.sh -b <branch> [options]
```

## Examples

### Update all repositories in the current directory to `develop`

```bash
./update-repos.sh -b develop
```

### Update all repositories in a specific path to `develop`

```bash
./update-repos.sh -b develop -p ~/workspace/services
```

### Update all repositories in a specific path to `main`

```bash
./update-repos.sh -b main -p ~/workspace/services
```

### Show help

```bash
./update-repos.sh -h
```

## Options

| Option | Description |
|---|---|
| `-b <branch>` | Branch to update. Required. |
| `-p <path>` | Path containing Git repositories. Default: current directory. |
| `-h` | Show help message. |

## Notes

- By default, the script checks Git repositories inside the current directory.
- Use `-p` to run it against a specific directory containing Git repositories.
- The selected path must contain Git repositories as direct child folders.
- Repositories with uncommitted changes are skipped.
- The script uses `git pull --ff-only` to avoid creating merge commits automatically.
- If a repository cannot be updated safely, it is reported in the final summary.