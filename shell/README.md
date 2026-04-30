# Shell scripts

Shell scripts to automate common development and repository maintenance tasks.

## Scripts

| Script | Description |
|---|---|
| `update-repos.sh` | Updates the given branch across all Git repositories inside the current directory. |
| `build-maven-projects.sh` | Runs Maven goals across all Maven projects inside the current directory. |

## Requirements

- Bash
- Git
- Maven

Some scripts may use project-specific wrappers, such as Maven Wrapper, when available.

---

## `update-repos.sh`

Updates a target branch across all Git repositories inside the current directory.

### Usage

```bash
./update-repos.sh -b <branch>
```

### Examples

Update all repositories to `develop`:

```bash
./update-repos.sh -b develop
```

Update all repositories to `main`:

```bash
./update-repos.sh -b main
```

Show available options:

```bash
./update-repos.sh -h
```

### Options

| Option | Description |
|---|---|
| `-b <branch>` | Branch to update. Required. |
| `-h` | Show help message. |

---

## `build-maven-projects.sh`

Runs Maven goals across all Maven projects inside the current directory.

### Usage

```bash
./build-maven-projects.sh [options]
```

### Examples

Run the default Maven build:

```bash
./build-maven-projects.sh
```

Run custom Maven goals:

```bash
./build-maven-projects.sh -g "clean package"
```

Skip tests:

```bash
./build-maven-projects.sh --skip-tests
```

Run in offline mode:

```bash
./build-maven-projects.sh --offline
```

Combine options:

```bash
./build-maven-projects.sh -g "clean verify" --skip-tests
```

Show available options:

```bash
./build-maven-projects.sh -h
```

### Options

| Option | Description |
|---|---|
| `-g <goals>` | Maven goals to run. Default: `"clean install"`. |
| `--skip-tests` | Skip test execution using `-DskipTests`. |
| `--offline` | Run Maven in offline mode using `-o`. |
| `-h`, `--help` | Show help message. |