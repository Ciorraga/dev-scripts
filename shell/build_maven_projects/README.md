# Build Maven Projects

Shell script to run Maven goals across all Maven projects inside a target directory.

By default, it checks Maven projects inside the current directory. You can provide a specific path using `-p` or `--path`.

By default, it runs:

```bash
mvn clean install
```

If a project contains Maven Wrapper, the script uses it automatically:

```bash
./mvnw clean install
```

## Features

- Processes all Maven projects inside a target directory.
- Uses the current directory by default.
- Allows selecting a specific path with `-p` or `--path`.
- Detects Maven projects by checking for `pom.xml`.
- Uses Maven Wrapper when available.
- Falls back to local `mvn` when Maven Wrapper is not available.
- Supports custom Maven goals.
- Supports skipping tests.
- Supports offline mode.
- Reports successful and failed builds in a final summary.
- Uses colored output.

## Requirements

- Bash
- Maven

Maven is not required globally if each project contains Maven Wrapper.

## Usage

```bash
./build-maven-projects.sh [options]
```

## Examples

### Run the default Maven build in the current directory

```bash
./build-maven-projects.sh
```

### Run the default Maven build in a specific path

```bash
./build-maven-projects.sh -p ~/workspace/services
```

### Run custom Maven goals

```bash
./build-maven-projects.sh -g "clean package"
```

### Run custom Maven goals in a specific path

```bash
./build-maven-projects.sh -p ~/workspace/services -g "clean package"
```

### Skip tests

```bash
./build-maven-projects.sh --skip-tests
```

### Skip tests in a specific path

```bash
./build-maven-projects.sh -p ~/workspace/services --skip-tests
```

### Run in offline mode

```bash
./build-maven-projects.sh --offline
```

### Combine options

```bash
./build-maven-projects.sh -p ~/workspace/services -g "clean verify" --skip-tests
```

### Show help

```bash
./build-maven-projects.sh -h
```

## Options

| Option | Description |
|---|---|
| `-p`, `--path <path>` | Path containing Maven projects. Default: current directory. |
| `-g <goals>` | Maven goals to run. Default: `"clean install"`. |
| `--skip-tests` | Skip test execution using `-DskipTests`. |
| `--offline` | Run Maven in offline mode using `-o`. |
| `-h`, `--help` | Show help message. |

## Notes

- By default, the script checks Maven projects inside the current directory.
- Use `-p` or `--path` to run it against a specific directory containing Maven projects.
- The selected path must contain Maven projects as direct child folders.
- Directories without a `pom.xml` are skipped.
- If one project fails, the script continues with the remaining projects.
- If at least one build fails, the script exits with status code `1`.