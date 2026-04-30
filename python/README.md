# Python scripts

Small Python command-line utilities.

## Scripts

| Script | Description |
|---|---|
| `uuid7gen.py` | Generates UUID version 7 identifiers. |

---

## `uuid7gen.py`

Generate UUID version 7 identifiers from the command line.

UUIDv7 is a time-ordered UUID format based on a Unix timestamp in milliseconds plus random data. It is useful for systems where sortable identifiers are preferred, such as databases, logs, distributed systems, or event-driven applications.

### Requirements

- Python 3.8 or newer

No external dependencies are required.

### Usage

```bash
python3 uuid7gen.py [options]
```

Or, if executable:

```bash
./uuid7gen.py [options]
```

### Examples

Generate one UUIDv7:

```bash
python3 uuid7gen.py
```

Generate multiple UUIDv7 identifiers:

```bash
python3 uuid7gen.py -n 10
```

Generate only the UUID values, without extra messages:

```bash
python3 uuid7gen.py -n 10 --plain
```

Disable colored output:

```bash
python3 uuid7gen.py --no-color
```

Show help:

```bash
python3 uuid7gen.py --help
```

### Options

| Option | Description |
|---|---|
| `-n`, `--number` | Number of UUIDv7 identifiers to generate. Default: `1`. |
| `--plain` | Print only UUID values, without extra messages. |
| `--no-color` | Disable colored output. |
| `-h`, `--help` | Show help message. |

### Example output

```text
$ python3 uuid7gen.py -n 3 --plain
0196f7e9-9c5e-772f-83b5-f54f9e47c78d
0196f7e9-9c5e-773a-8c1d-369bf0df6e0c
0196f7e9-9c5e-7a27-a972-9c93fdd6cf5e
```

### Notes

- UUIDv7 identifiers are time-ordered.
- The first 48 bits contain the Unix timestamp in milliseconds.
- The remaining bits contain version, variant, and random data.
- This script does not require external Python packages.