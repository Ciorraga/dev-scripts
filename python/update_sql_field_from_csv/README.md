# Update SQL Field From CSV

Python command-line utility to update a specific field in simple SQL `INSERT` and `UPDATE` statements using values from a CSV file.

> [!IMPORTANT]
> This script is designed only for simple SQL `INSERT` and `UPDATE` statements.
> It is not a full SQL parser.
>
> It is intended for SQL files containing straightforward statements such as:
>
> ```sql
> INSERT INTO product (id, code, description) VALUES ('123', 'x1', 'Original name');
> UPDATE product SET description = 'Old value' WHERE id = '123';
> ```
>
> Complex SQL files with procedures, triggers, functions, nested statements, vendor-specific syntax, or mixed statement types are not supported.

## Features

- Updates a specific SQL field using values from a CSV file.
- Supports simple `INSERT` and `UPDATE` statements.
- Supports single-row and multi-row `INSERT` statements.
- Matches SQL records using an ID field.
- Uses a CSV column letter, such as `C`, `D`, or `AA`, to select replacement values.
- Treats the first CSV row as a header by default.
- Supports CSV files without headers using `--no-header`.
- Supports custom CSV ID column using `--id-column-letter`.
- Supports custom SQL ID field using `--id-field`.
- Escapes single quotes in SQL string values.
- Supports dry-run mode.
- Does not require external dependencies.

## Requirements

- Python 3.8 or newer

No external dependencies are required.

## Usage

```bash
python3 update_sql_field_from_csv.py --sql-in <input.sql> --csv-in <values.csv> --column-letter <letter> --field <field> --out <output.sql> [options]
```

Or, if executable:

```bash
./update_sql_field_from_csv.py --sql-in <input.sql> --csv-in <values.csv> --column-letter <letter> --field <field> --out <output.sql> [options]
```

## Examples

### Update a field using values from column C

```bash
python3 update_sql_field_from_csv.py \
  --sql-in input.sql \
  --csv-in values.csv \
  --column-letter C \
  --field description \
  --out output.sql
```

### Preview changes without writing the output file

```bash
python3 update_sql_field_from_csv.py \
  --sql-in input.sql \
  --csv-in values.csv \
  --column-letter C \
  --field description \
  --out output.sql \
  --dry-run
```

### Use a different SQL ID field

```bash
python3 update_sql_field_from_csv.py \
  --sql-in input.sql \
  --csv-in values.csv \
  --column-letter C \
  --field description \
  --id-field uuid \
  --out output.sql
```

### Use a different CSV ID column

```bash
python3 update_sql_field_from_csv.py \
  --sql-in input.sql \
  --csv-in values.csv \
  --id-column-letter B \
  --column-letter D \
  --field description \
  --out output.sql
```

### Use a CSV file without header row

```bash
python3 update_sql_field_from_csv.py \
  --sql-in input.sql \
  --csv-in values.csv \
  --no-header \
  --column-letter C \
  --field description \
  --out output.sql
```

### Keep SQL statements unchanged when the ID is missing in the CSV

```bash
python3 update_sql_field_from_csv.py \
  --sql-in input.sql \
  --csv-in values.csv \
  --column-letter C \
  --field description \
  --out output.sql \
  --allow-missing-csv-id
```

### Show help

```bash
python3 update_sql_field_from_csv.py --help
```

## Options

| Option | Description |
|---|---|
| `--sql-in` | Input `.sql` file containing simple `INSERT` or `UPDATE` statements. Required. |
| `--csv-in` | Input `.csv` file. Required. |
| `--column-letter` | CSV column letter containing the new values. Required. |
| `--field` | SQL field name to update. Required. |
| `--out` | Output `.sql` file. Required. |
| `--id-column-letter` | CSV column letter containing the row ID. Default: `A`. |
| `--id-field` | SQL field used to match CSV IDs. Default: `id`. |
| `--no-header` | Use this if the CSV file does not have a header row. |
| `--allow-missing-csv-id` | Keep SQL statements unchanged when their ID is not found in the CSV. |
| `--dry-run` | Show replacements without writing the output file. |
| `--quiet` | Suppress status messages. Replacement lines are still printed. |
| `--verbose` | Show debug information. |
| `--no-color` | Disable colored output. |
| `-h`, `--help` | Show help message. |

## CSV format

By default, the first row is treated as a header.

Example `values.csv`:

```csv
id,code,description,status
123,x1,Updated product description,ACTIVE
124,x2,Another updated description,INACTIVE
125,x3,,PENDING
126,x4,Description with single quote: John's product,ACTIVE
```

With this CSV:

- Column `A` contains the ID used to match SQL records.
- Column `C` contains the new value for the `description` SQL field.
- Column `D` contains the new value for the `status` SQL field.
- Empty CSV values are written as empty SQL strings: `''`.
- Single quotes are escaped automatically.

## SQL input example

Example `input.sql`:

```sql
INSERT INTO product (id, code, description, status)
VALUES ('123', 'x1', 'Original product description', 'DRAFT');

INSERT INTO product (id, code, description, status)
VALUES
('124', 'x2', 'Old description', 'DRAFT'),
('125', 'x3', 'Description to be cleared', 'DRAFT');

UPDATE product
SET description = 'Old update description', status = 'DRAFT'
WHERE id = '126';

UPDATE product
SET description = 'Should stay unchanged', status = 'DRAFT'
WHERE id = '999';
```

To test the script using the examples above:

```bash
python3 update_sql_field_from_csv.py \
  --sql-in input.sql \
  --csv-in values.csv \
  --column-letter C \
  --field description \
  --out output.sql \
  --allow-missing-csv-id
```

The script will generate `output.sql`.

## Supported SQL examples

### Simple `INSERT`

```sql
INSERT INTO product (id, code, description)
VALUES ('123', 'x1', 'Original name');
```

### Multi-row `INSERT`

```sql
INSERT INTO product (id, code, description)
VALUES
('123', 'x1', 'Original name'),
('124', 'x2', 'Old value');
```

### Simple `UPDATE`

```sql
UPDATE product
SET description = 'Old value'
WHERE id = '123';
```

### `UPDATE` with extra conditions

```sql
UPDATE product
SET description = 'Old value'
WHERE id = '123' AND active = true;
```

## Unsupported SQL examples

```sql
SELECT * FROM product;
```

```sql
DELETE FROM product WHERE id = '123';
```

```sql
INSERT INTO product
SELECT id, code, description FROM old_product;
```

```sql
CREATE OR REPLACE FUNCTION refresh_product()
RETURNS void AS $$
BEGIN
  UPDATE product SET description = 'Old value' WHERE id = '123';
END;
$$ LANGUAGE plpgsql;
```

## Output example

```text
✅ Processing 4 SQL statement(s)...
✅ SQL field to update: description
✅ SQL ID field: id
✅ CSV value column: C

Statement #1 | Type: INSERT | ID: 123 | Field: description | Old value: 'Original product description' -> New value: 'Updated product description'
Statement #2 | Type: INSERT | ID: 124 | Field: description | Old value: 'Old description' -> New value: 'Another updated description'
Statement #2 | Type: INSERT | ID: 125 | Field: description | Old value: 'Description to be cleared' -> New value: ''
Statement #3 | Type: UPDATE | ID: 126 | Field: description | Old value: 'Old update description' -> New value: "Description with single quote: John's product"

✅ Output saved to 'output.sql', 4 value(s) updated.
```

## Notes

- The input SQL file is never overwritten.
- The script always writes to the file provided with `--out`.
- Empty CSV values are written as empty SQL strings: `''`.
- CSV values containing single quotes are escaped automatically.
- If a SQL record ID is not found in the CSV, the script fails by default.
- Use `--allow-missing-csv-id` to keep unmatched SQL statements unchanged.
- The script is intentionally conservative and only supports simple SQL statements.