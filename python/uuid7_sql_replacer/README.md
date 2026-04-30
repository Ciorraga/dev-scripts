# UUIDv7 SQL Replacer

Python command-line utility to replace UUID values in simple SQL `INSERT` and `UPDATE` statements with freshly generated UUID version 7 identifiers.

> [!IMPORTANT]
> This script is designed only for simple SQL `INSERT` and `UPDATE` statements.
> It is not a full SQL parser.
>
> It is intended for SQL files containing straightforward statements such as:
>
> ```sql
> INSERT INTO users (id, name) VALUES ('550e8400-e29b-41d4-a716-446655440000', 'John');
> UPDATE users SET id = '550e8400-e29b-41d4-a716-446655440000' WHERE username = 'john';
> ```
>
> Complex SQL files with procedures, triggers, functions, nested statements, vendor-specific syntax, or mixed statement types are not supported.

## Features

- Replaces UUID values in SQL `INSERT` and `UPDATE` statements.
- Supports replacing one or multiple fields.
- Uses UUIDv7 identifiers.
- Supports single-row and multi-row `INSERT` statements.
- Validates that all selected fields exist in each statement.
- Validates UUID values by default before replacing them.
- Allows non-UUID values with `--allow-non-uuid`.
- Supports dry-run mode.
- Supports explicit in-place replacement.
- Supports backup creation before overwriting files.
- Supports colored output.
- Allows disabling colors for logs or CI environments.

## Requirements

- Python 3.8 or newer

No external dependencies are required.

## Usage

```bash
python3 uuid7_sql_replacer.py -i <input.sql> -o <output.sql> [options]
```

Or, if executable:

```bash
./uuid7_sql_replacer.py -i <input.sql> -o <output.sql> [options]
```

## Examples

### Replace the default `id` field and write to a new file

```bash
python3 uuid7_sql_replacer.py -i input.sql -o output.sql
```

### Replace multiple fields

```bash
python3 uuid7_sql_replacer.py -i input.sql -o output.sql -f id,session_id
```

### Overwrite the input file explicitly

```bash
python3 uuid7_sql_replacer.py -i input.sql --in-place
```

### Overwrite the input file and create a backup

```bash
python3 uuid7_sql_replacer.py -i input.sql --in-place --backup
```

This creates a backup file next to the original one:

```text
input.sql.bak
```

### Preview replacements without writing any file

```bash
python3 uuid7_sql_replacer.py -i input.sql -f id,session_id --dry-run
```

### Allow replacing values that are not valid UUIDs

```bash
python3 uuid7_sql_replacer.py -i input.sql -o output.sql --allow-non-uuid
```

### Disable colored output

```bash
python3 uuid7_sql_replacer.py -i input.sql -o output.sql --no-color
```

### Show help

```bash
python3 uuid7_sql_replacer.py --help
```

## Options

| Option | Description |
|---|---|
| `-i`, `--input` | Input `.sql` file containing simple `INSERT` or `UPDATE` statements. Required. |
| `-o`, `--output` | Output `.sql` file. Required unless `--in-place` or `--dry-run` is used. |
| `-f`, `--fields` | Comma-separated list of fields to replace. Default: `id`. |
| `--in-place` | Overwrite the input file. Must be explicitly enabled. |
| `--backup` | Create a `.bak` backup before overwriting. Only valid with `--in-place`. |
| `--dry-run` | Show replacements without writing any file. |
| `--allow-non-uuid` | Allow replacing values that are not valid UUIDs. |
| `--plain` | Print only replacement lines without extra status messages. |
| `--no-color` | Disable colored output. |
| `-h`, `--help` | Show help message. |

## Supported SQL examples

### Simple `INSERT`

```sql
INSERT INTO users (id, name) VALUES ('550e8400-e29b-41d4-a716-446655440000', 'John');
```

### Multi-row `INSERT`

```sql
INSERT INTO users (id, name) VALUES
('550e8400-e29b-41d4-a716-446655440000', 'John'),
('550e8400-e29b-41d4-a716-446655440001', 'Jane');
```

### Simple `UPDATE`

```sql
UPDATE users
SET id = '550e8400-e29b-41d4-a716-446655440000'
WHERE username = 'john';
```

### Multiple fields

```sql
INSERT INTO user_sessions (id, session_id, username)
VALUES (
  '550e8400-e29b-41d4-a716-446655440000',
  '550e8400-e29b-41d4-a716-446655440001',
  'john'
);
```

Run:

```bash
python3 uuid7_sql_replacer.py -i input.sql -o output.sql -f id,session_id
```

## Unsupported SQL examples

This script does not support complex SQL structures such as:

```sql
SELECT * FROM users;
```

```sql
DELETE FROM users WHERE id = '550e8400-e29b-41d4-a716-446655440000';
```

```sql
CREATE OR REPLACE FUNCTION refresh_data()
RETURNS void AS $$
BEGIN
  UPDATE users SET id = '550e8400-e29b-41d4-a716-446655440000';
END;
$$ LANGUAGE plpgsql;
```

```sql
INSERT INTO users
SELECT id, name FROM old_users;
```

## Output example

```text
✅ Processing 2 SQL statement(s)...
✅ Fields to replace: id,session_id

Statement #1 | Field: id | Previous UUID: 550e8400-e29b-41d4-a716-446655440000 -> New UUID: 0196f863-6f42-75ef-9e7c-a8a87f508c55
Statement #1 | Field: session_id | Previous UUID: 550e8400-e29b-41d4-a716-446655440001 -> New UUID: 0196f863-6f42-7f17-908a-feb4dd6953b5

✅ All UUIDs replaced successfully. Output saved to 'output.sql'.
```

## Notes

- By default, the script replaces only the `id` field.
- Use `-f` or `--fields` to replace multiple fields.
- By default, values must be valid UUIDs.
- Use `--allow-non-uuid` if you intentionally want to replace non-UUID values.
- The input file is never overwritten unless `--in-place` is explicitly used.
- Use `--backup` with `--in-place` to keep a copy of the original file.

## License

MIT License — use it, modify it, share it.