#!/usr/bin/env python3

import argparse
import csv
import re
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"


@dataclass
class CsvConfig:
    id_column_index: int
    value_column_index: int
    has_header: bool


@dataclass
class Replacement:
    statement_index: int
    row_id: str
    field: str
    old_value: str
    new_value: str
    statement_type: str


class ScriptError(Exception):
    pass


def colorize(message: str, color: str, use_color: bool) -> str:
    if not use_color:
        return message
    return f"{color}{message}{RESET}"


def print_info(message: str, use_color: bool, quiet: bool = False) -> None:
    if not quiet:
        print(colorize(f"✅ {message}", GREEN, use_color))


def print_warn(message: str, use_color: bool, quiet: bool = False) -> None:
    if not quiet:
        print(colorize(f"⚠️  {message}", YELLOW, use_color))


def print_error(message: str, use_color: bool) -> None:
    print(colorize(f"❌ {message}", RED, use_color), file=sys.stderr)


def print_verbose(message: str, verbose: bool, use_color: bool) -> None:
    if verbose:
        print(colorize(f"DEBUG: {message}", YELLOW, use_color))


def validate_file_path(path: Path, label: str, expected_suffix: str, must_exist: bool) -> None:
    if path.suffix.lower() != expected_suffix:
        raise ScriptError(f"The {label} file must have a {expected_suffix} extension.")

    if must_exist and not path.exists():
        raise ScriptError(f"The {label} file '{path}' does not exist.")

    if must_exist and not path.is_file():
        raise ScriptError(f"The {label} path '{path}' is not a file.")


def validate_field_name(field: str, label: str) -> str:
    normalized = field.strip()

    if not normalized:
        raise ScriptError(f"{label} cannot be empty.")

    if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", normalized):
        raise ScriptError(f"Invalid {label}: '{field}'.")

    return normalized


def column_letter_to_index(letter: str) -> int:
    normalized = letter.strip().upper()

    if not re.match(r"^[A-Z]+$", normalized):
        raise ScriptError(f"Invalid column letter: '{letter}'.")

    index = 0
    for char in normalized:
        index = index * 26 + (ord(char) - ord("A") + 1)

    return index - 1


def escape_sql_string(value: str) -> str:
    return value.replace("'", "''")


def strip_sql_quotes(value: str) -> str:
    value = value.strip()

    if len(value) >= 2 and value[0] == "'" and value[-1] == "'":
        return value[1:-1].replace("''", "'")

    if len(value) >= 2 and value[0] == '"' and value[-1] == '"':
        return value[1:-1].replace('""', '"')

    return value


def normalize_identifier(identifier: str) -> str:
    return identifier.strip().strip('"').strip("`").strip("[").strip("]").lower()


def split_sql_statements(sql_content: str) -> list[str]:
    """
    Split SQL statements by semicolon while respecting quoted strings and comments.
    This is not a full SQL parser, but it is safer than a plain split(';').
    """
    statements: list[str] = []
    current: list[str] = []

    in_single_quote = False
    in_double_quote = False
    in_line_comment = False
    in_block_comment = False

    i = 0
    while i < len(sql_content):
        char = sql_content[i]
        next_char = sql_content[i + 1] if i + 1 < len(sql_content) else ""

        current.append(char)

        if in_line_comment:
            if char == "\n":
                in_line_comment = False
            i += 1
            continue

        if in_block_comment:
            if char == "*" and next_char == "/":
                current.append(next_char)
                in_block_comment = False
                i += 2
                continue
            i += 1
            continue

        if not in_single_quote and not in_double_quote:
            if char == "-" and next_char == "-":
                current.append(next_char)
                in_line_comment = True
                i += 2
                continue

            if char == "/" and next_char == "*":
                current.append(next_char)
                in_block_comment = True
                i += 2
                continue

        if char == "'" and not in_double_quote:
            if in_single_quote and next_char == "'":
                current.append(next_char)
                i += 2
                continue
            in_single_quote = not in_single_quote

        elif char == '"' and not in_single_quote:
            if in_double_quote and next_char == '"':
                current.append(next_char)
                i += 2
                continue
            in_double_quote = not in_double_quote

        elif char == ";" and not in_single_quote and not in_double_quote:
            statement = "".join(current).strip()
            if statement:
                statements.append(statement)
            current = []

        i += 1

    trailing = "".join(current).strip()
    if trailing:
        statements.append(trailing)

    return statements


def strip_trailing_semicolon(statement: str) -> str:
    stripped = statement.rstrip()
    if stripped.endswith(";"):
        return stripped[:-1].rstrip()
    return stripped


def statement_type(statement: str) -> str:
    normalized = statement.lstrip().lower()

    if normalized.startswith("insert"):
        return "insert"

    if normalized.startswith("update"):
        return "update"

    return "unsupported"


def split_top_level_commas(value: str) -> list[str]:
    """
    Split by commas while respecting quotes and nested parentheses.
    """
    parts: list[str] = []
    current: list[str] = []

    in_single_quote = False
    in_double_quote = False
    paren_depth = 0

    i = 0
    while i < len(value):
        char = value[i]
        next_char = value[i + 1] if i + 1 < len(value) else ""

        if char == "'" and not in_double_quote:
            current.append(char)
            if in_single_quote and next_char == "'":
                current.append(next_char)
                i += 2
                continue
            in_single_quote = not in_single_quote
            i += 1
            continue

        if char == '"' and not in_single_quote:
            current.append(char)
            if in_double_quote and next_char == '"':
                current.append(next_char)
                i += 2
                continue
            in_double_quote = not in_double_quote
            i += 1
            continue

        if not in_single_quote and not in_double_quote:
            if char == "(":
                paren_depth += 1
            elif char == ")":
                paren_depth -= 1

            if char == "," and paren_depth == 0:
                parts.append("".join(current).strip())
                current = []
                i += 1
                continue

        current.append(char)
        i += 1

    parts.append("".join(current).strip())
    return parts


def find_matching_parenthesis(text: str, opening_index: int) -> int:
    depth = 0
    in_single_quote = False
    in_double_quote = False

    i = opening_index
    while i < len(text):
        char = text[i]
        next_char = text[i + 1] if i + 1 < len(text) else ""

        if char == "'" and not in_double_quote:
            if in_single_quote and next_char == "'":
                i += 2
                continue
            in_single_quote = not in_single_quote

        elif char == '"' and not in_single_quote:
            if in_double_quote and next_char == '"':
                i += 2
                continue
            in_double_quote = not in_double_quote

        elif not in_single_quote and not in_double_quote:
            if char == "(":
                depth += 1
            elif char == ")":
                depth -= 1
                if depth == 0:
                    return i

        i += 1

    raise ScriptError("Could not find matching closing parenthesis.")


def read_csv_values(csv_path: Path, config: CsvConfig, verbose: bool, use_color: bool) -> dict[str, str]:
    values_by_id: dict[str, str] = {}

    with csv_path.open("r", encoding="utf-8", newline="") as file:
        reader = csv.reader(file)
        rows = list(reader)

    if not rows:
        raise ScriptError("CSV file is empty.")

    max_required_index = max(config.id_column_index, config.value_column_index)

    for row_number, row in enumerate(rows, start=1):
        if config.has_header and row_number == 1:
            print_verbose(f"CSV header: {row}", verbose, use_color)
            continue

        if len(row) <= max_required_index:
            raise ScriptError(
                f"CSV row {row_number} does not contain the required column. "
                f"Expected at least {max_required_index + 1} column(s)."
            )

        row_id = row[config.id_column_index].strip()
        new_value = row[config.value_column_index].strip()

        if not row_id:
            raise ScriptError(f"CSV row {row_number} has an empty ID value.")

        if row_id in values_by_id:
            raise ScriptError(f"Duplicated CSV ID found: '{row_id}'.")

        values_by_id[row_id] = new_value

    if not values_by_id:
        raise ScriptError("CSV file does not contain any data rows.")

    first_id = next(iter(values_by_id))
    first_value = values_by_id[first_id]

    if first_value == "":
        raise ScriptError("First data row in the selected CSV column is empty.")

    print_verbose(f"Loaded {len(values_by_id)} CSV row(s).", verbose, use_color)
    print_verbose(f"First CSV ID: {first_id}", verbose, use_color)

    return values_by_id


def parse_insert_statement(statement: str) -> tuple[list[str], list[list[str]], tuple[int, int]]:
    """
    Parse simple INSERT statements with explicit columns.

    Supported:
      INSERT INTO table_name (id, name) VALUES ('1', 'Name');
      INSERT INTO table_name (id, name) VALUES ('1', 'Name'), ('2', 'Other');
    """
    clean_statement = strip_trailing_semicolon(statement)

    columns_match = re.search(
        r"\binsert\s+into\s+[\w.\"`\[\]-]+\s*\(",
        clean_statement,
        re.IGNORECASE | re.DOTALL,
    )

    if not columns_match:
        raise ScriptError("INSERT statements must include an explicit column list.")

    columns_open = clean_statement.find("(", columns_match.start())
    columns_close = find_matching_parenthesis(clean_statement, columns_open)

    raw_columns = clean_statement[columns_open + 1 : columns_close]
    columns = [normalize_identifier(column) for column in split_top_level_commas(raw_columns)]

    if not columns:
        raise ScriptError("INSERT statement has an empty column list.")

    values_match = re.search(r"\bvalues\b", clean_statement[columns_close + 1 :], re.IGNORECASE)
    if not values_match:
        raise ScriptError("INSERT statement must contain a VALUES clause.")

    values_start = columns_close + 1 + values_match.end()
    values_part = clean_statement[values_start:].strip()

    if not values_part.startswith("("):
        raise ScriptError("INSERT VALUES clause must contain parenthesized values.")

    tuples: list[list[str]] = []
    tuple_start_in_values = 0
    cursor = 0

    while cursor < len(values_part):
        while cursor < len(values_part) and values_part[cursor].isspace():
            cursor += 1

        if cursor >= len(values_part):
            break

        if values_part[cursor] == ",":
            cursor += 1
            continue

        if values_part[cursor] != "(":
            raise ScriptError("Unsupported INSERT VALUES format.")

        if not tuples:
            tuple_start_in_values = cursor

        tuple_end = find_matching_parenthesis(values_part, cursor)
        tuple_body = values_part[cursor + 1 : tuple_end]
        tuple_values = split_top_level_commas(tuple_body)

        if len(tuple_values) != len(columns):
            raise ScriptError(
                f"INSERT values count ({len(tuple_values)}) does not match columns count ({len(columns)})."
            )

        tuples.append(tuple_values)
        cursor = tuple_end + 1

    if not tuples:
        raise ScriptError("INSERT statement does not contain values.")

    values_absolute_start = values_start + tuple_start_in_values
    values_absolute_end = len(clean_statement)

    return columns, tuples, (values_absolute_start, values_absolute_end)


def parse_update_statement(statement: str) -> tuple[list[str], list[str], str, tuple[int, int]]:
    """
    Parse simple UPDATE statements.

    Supported:
      UPDATE table_name SET field = 'value' WHERE id = '1';
      UPDATE table_name SET field = 'value' WHERE id='1' AND active = true;
    """
    clean_statement = strip_trailing_semicolon(statement)

    set_match = re.search(r"\bset\b", clean_statement, re.IGNORECASE)
    if not set_match:
        raise ScriptError("UPDATE statement must contain a SET clause.")

    where_match = re.search(r"\bwhere\b", clean_statement[set_match.end() :], re.IGNORECASE)
    if not where_match:
        raise ScriptError("UPDATE statements must contain a WHERE clause.")

    set_start = set_match.end()
    set_end = set_match.end() + where_match.start()

    set_clause = clean_statement[set_start:set_end].strip()
    where_clause = clean_statement[set_end:].strip()

    assignments = split_top_level_commas(set_clause)

    fields: list[str] = []
    for assignment in assignments:
        if "=" not in assignment:
            raise ScriptError(f"Invalid UPDATE assignment: {assignment}")

        field_name = assignment.split("=", 1)[0]
        fields.append(normalize_identifier(field_name))

    return fields, assignments, where_clause, (set_start, set_end)


def extract_row_id_from_where(where_clause: str, id_field: str) -> str:
    normalized_id_field = re.escape(id_field)

    pattern = re.compile(
        rf"\b{normalized_id_field}\b\s*=\s*('([^']*)'|\"([^\"]*)\"|([^\s,)]+))",
        re.IGNORECASE,
    )

    match = pattern.search(where_clause)
    if not match:
        raise ScriptError(f"Could not find ID field '{id_field}' in UPDATE WHERE clause.")

    return match.group(2) or match.group(3) or match.group(4)


def replace_insert_statement(
    statement: str,
    values_by_id: dict[str, str],
    target_field: str,
    id_field: str,
    statement_index: int,
    fail_on_missing_csv_id: bool,
) -> tuple[str, list[Replacement]]:
    columns, tuples, values_range = parse_insert_statement(statement)

    normalized_target_field = normalize_identifier(target_field)
    normalized_id_field = normalize_identifier(id_field)

    if normalized_id_field not in columns:
        raise ScriptError(f"Missing ID field '{id_field}' in INSERT statement.")

    if normalized_target_field not in columns:
        raise ScriptError(f"Missing target field '{target_field}' in INSERT statement.")

    id_index = columns.index(normalized_id_field)
    target_index = columns.index(normalized_target_field)

    updated_tuples: list[str] = []
    replacements: list[Replacement] = []

    for tuple_values in tuples:
        row_id = strip_sql_quotes(tuple_values[id_index])

        if row_id not in values_by_id:
            if fail_on_missing_csv_id:
                raise ScriptError(f"ID '{row_id}' from INSERT statement was not found in CSV.")
            updated_tuples.append(f"({', '.join(tuple_values)})")
            continue

        old_value = tuple_values[target_index].strip()
        new_value = values_by_id[row_id]
        new_sql_value = escape_sql_string(new_value)

        updated_values = tuple_values[:]
        updated_values[target_index] = f"'{new_sql_value}'"

        replacements.append(
            Replacement(
                statement_index=statement_index,
                row_id=row_id,
                field=target_field,
                old_value=strip_sql_quotes(old_value),
                new_value=new_value,
                statement_type="INSERT",
            )
        )

        updated_tuples.append(f"({', '.join(updated_values)})")

    start, end = values_range
    clean_statement = strip_trailing_semicolon(statement)
    updated_statement = clean_statement[:start] + ", ".join(updated_tuples) + clean_statement[end:]

    return updated_statement + ";", replacements


def replace_update_statement(
    statement: str,
    values_by_id: dict[str, str],
    target_field: str,
    id_field: str,
    statement_index: int,
    fail_on_missing_csv_id: bool,
) -> tuple[str, list[Replacement]]:
    fields, assignments, where_clause, set_range = parse_update_statement(statement)

    normalized_target_field = normalize_identifier(target_field)
    normalized_id_field = normalize_identifier(id_field)

    if normalized_target_field not in fields:
        raise ScriptError(f"Missing target field '{target_field}' in UPDATE statement.")

    row_id = extract_row_id_from_where(where_clause, normalized_id_field)

    if row_id not in values_by_id:
        if fail_on_missing_csv_id:
            raise ScriptError(f"ID '{row_id}' from UPDATE statement was not found in CSV.")
        return strip_trailing_semicolon(statement) + ";", []

    new_value = values_by_id[row_id]
    new_sql_value = escape_sql_string(new_value)

    updated_assignments: list[str] = []
    replacements: list[Replacement] = []

    for assignment in assignments:
        left, right = assignment.split("=", 1)
        field = normalize_identifier(left)

        if field != normalized_target_field:
            updated_assignments.append(assignment)
            continue

        old_value = right.strip()
        updated_assignments.append(f"{left.strip()} = '{new_sql_value}'")

        replacements.append(
            Replacement(
                statement_index=statement_index,
                row_id=row_id,
                field=target_field,
                old_value=strip_sql_quotes(old_value),
                new_value=new_value,
                statement_type="UPDATE",
            )
        )

    start, end = set_range
    clean_statement = strip_trailing_semicolon(statement)
    updated_statement = (
        clean_statement[:start]
        + " "
        + ", ".join(updated_assignments)
        + " "
        + clean_statement[end:].lstrip()
    )

    return updated_statement.rstrip() + ";", replacements


def replace_statement(
    statement: str,
    values_by_id: dict[str, str],
    target_field: str,
    id_field: str,
    statement_index: int,
    fail_on_missing_csv_id: bool,
) -> tuple[str, list[Replacement]]:
    kind = statement_type(statement)

    if kind == "insert":
        return replace_insert_statement(
            statement=statement,
            values_by_id=values_by_id,
            target_field=target_field,
            id_field=id_field,
            statement_index=statement_index,
            fail_on_missing_csv_id=fail_on_missing_csv_id,
        )

    if kind == "update":
        return replace_update_statement(
            statement=statement,
            values_by_id=values_by_id,
            target_field=target_field,
            id_field=id_field,
            statement_index=statement_index,
            fail_on_missing_csv_id=fail_on_missing_csv_id,
        )

    raise ScriptError("Only INSERT and UPDATE statements are supported.")


def validate_statements(statements: Iterable[str]) -> None:
    unsupported: list[str] = []

    for index, statement in enumerate(statements, start=1):
        kind = statement_type(statement)

        if kind == "unsupported":
            first_line = statement.strip().splitlines()[0][:80]
            unsupported.append(f"statement #{index}: {first_line}")

    if unsupported:
        raise ScriptError(
            "Unsupported SQL statement(s) found. Only INSERT and UPDATE are allowed:\n"
            + "\n".join(f"- {item}" for item in unsupported)
        )


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        prog="update_sql_field_from_csv.py",
        description="Update a field in simple SQL INSERT/UPDATE statements using values from a CSV file.",
        epilog=(
            "Examples:\n"
            "  python3 update_sql_field_from_csv.py --sql-in input.sql --csv-in values.csv "
            "--column-letter C --field description --out output.sql\n"
            "  python3 update_sql_field_from_csv.py --sql-in input.sql --csv-in values.csv "
            "--column-letter C --field description --out output.sql --dry-run\n"
            "  python3 update_sql_field_from_csv.py --sql-in input.sql --csv-in values.csv "
            "--column-letter C --field description --id-field uuid --out output.sql"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "--sql-in",
        required=True,
        help="Input .sql file containing simple INSERT/UPDATE statements.",
    )

    parser.add_argument(
        "--csv-in",
        required=True,
        help="Input .csv file. By default, the first row is treated as a header.",
    )

    parser.add_argument(
        "--column-letter",
        required=True,
        help="CSV column letter containing the new values. Example: C",
    )

    parser.add_argument(
        "--field",
        required=True,
        help="SQL field name to update.",
    )

    parser.add_argument(
        "--out",
        required=True,
        help="Output .sql file.",
    )

    parser.add_argument(
        "--id-column-letter",
        default="A",
        help="CSV column letter containing the row ID. Default: A",
    )

    parser.add_argument(
        "--id-field",
        default="id",
        help="SQL field used to match CSV IDs. Default: id",
    )

    parser.add_argument(
        "--no-header",
        action="store_true",
        help="Use this if the CSV file does not have a header row.",
    )

    parser.add_argument(
        "--allow-missing-csv-id",
        action="store_true",
        help="Keep SQL statements unchanged when their ID is not found in the CSV.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show replacements without writing the output file.",
    )

    parser.add_argument(
        "--quiet",
        action="store_true",
        help="Suppress status messages. Replacement lines are still printed.",
    )

    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Show debug information.",
    )

    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable colored output.",
    )

    return parser.parse_args()


def main() -> None:
    args = parse_args()
    use_color = not args.no_color

    try:
        sql_input_path = Path(args.sql_in)
        csv_input_path = Path(args.csv_in)
        output_path = Path(args.out)

        validate_file_path(sql_input_path, "SQL input", ".sql", must_exist=True)
        validate_file_path(csv_input_path, "CSV input", ".csv", must_exist=True)
        validate_file_path(output_path, "SQL output", ".sql", must_exist=False)

        target_field = validate_field_name(args.field, "field")
        id_field = validate_field_name(args.id_field, "ID field")

        id_column_index = column_letter_to_index(args.id_column_letter)
        value_column_index = column_letter_to_index(args.column_letter)

        if id_column_index == value_column_index:
            raise ScriptError("ID column and value column cannot be the same.")

        csv_config = CsvConfig(
            id_column_index=id_column_index,
            value_column_index=value_column_index,
            has_header=not args.no_header,
        )

        values_by_id = read_csv_values(csv_input_path, csv_config, args.verbose, use_color)

        sql_content = sql_input_path.read_text(encoding="utf-8")
        statements = split_sql_statements(sql_content)

        if not statements:
            raise ScriptError("Input SQL file does not contain any SQL statement.")

        validate_statements(statements)

        print_info(f"Processing {len(statements)} SQL statement(s)...", use_color, args.quiet)
        print_info(f"SQL field to update: {target_field}", use_color, args.quiet)
        print_info(f"SQL ID field: {id_field}", use_color, args.quiet)
        print_info(f"CSV value column: {args.column_letter.upper()}", use_color, args.quiet)

        updated_statements: list[str] = []
        all_replacements: list[Replacement] = []

        for index, statement in enumerate(statements, start=1):
            updated_statement, replacements = replace_statement(
                statement=statement,
                values_by_id=values_by_id,
                target_field=target_field,
                id_field=id_field,
                statement_index=index,
                fail_on_missing_csv_id=not args.allow_missing_csv_id,
            )

            updated_statements.append(updated_statement)
            all_replacements.extend(replacements)

        if not all_replacements:
            print_warn("No SQL values were updated.", use_color, args.quiet)
        else:
            for replacement in all_replacements:
                print(
                    f"Statement #{replacement.statement_index} | "
                    f"Type: {replacement.statement_type} | "
                    f"ID: {replacement.row_id} | "
                    f"Field: {replacement.field} | "
                    f"Old value: {replacement.old_value!r} -> "
                    f"New value: {replacement.new_value!r}"
                )

        updated_sql = "\n".join(updated_statements) + "\n"

        if args.dry_run:
            print_info("Dry-run enabled. No file was written.", use_color, args.quiet)
            return

        output_path.write_text(updated_sql, encoding="utf-8")

        print_info(
            f"Output saved to '{output_path}', {len(all_replacements)} value(s) updated.",
            use_color,
            args.quiet,
        )

    except ScriptError as error:
        print_error(str(error), use_color)
        sys.exit(1)

    except KeyboardInterrupt:
        print_error("Execution interrupted by user.", use_color)
        sys.exit(130)


if __name__ == "__main__":
    main()