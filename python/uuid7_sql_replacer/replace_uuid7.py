#!/usr/bin/env python3

import argparse
import re
import secrets
import shutil
import sys
import time
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Iterable


# ANSI colors
GREEN = "\033[92m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"

UUID_REGEX = re.compile(
    r"^[0-9a-fA-F]{8}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{4}-"
    r"[0-9a-fA-F]{12}$"
)


@dataclass
class Replacement:
    field: str
    old_value: str
    new_value: str
    statement_index: int


class ScriptError(Exception):
    pass


def generate_uuid7() -> uuid.UUID:
    """
    Generate a UUID version 7 identifier.

    Layout:
      - 48 bits: Unix timestamp in milliseconds
      - 4 bits: version 7
      - 12 bits: random data
      - 2 bits: RFC 4122 variant
      - 62 bits: random data
    """
    timestamp_ms = int(time.time() * 1000) & ((1 << 48) - 1)

    random_a = secrets.randbits(12)
    random_b = secrets.randbits(62)

    uuid_int = (
        (timestamp_ms << 80)
        | (0x7 << 76)
        | (random_a << 64)
        | (0x2 << 62)
        | random_b
    )

    return uuid.UUID(int=uuid_int)


def colorize(message: str, color: str, use_color: bool) -> str:
    if not use_color:
        return message
    return f"{color}{message}{RESET}"


def print_info(message: str, use_color: bool, plain: bool = False) -> None:
    if not plain:
        print(colorize(f"✅ {message}", GREEN, use_color))


def print_warn(message: str, use_color: bool, plain: bool = False) -> None:
    if not plain:
        print(colorize(f"⚠️  {message}", YELLOW, use_color))


def print_error(message: str, use_color: bool) -> None:
    print(colorize(f"❌ {message}", RED, use_color), file=sys.stderr)


def validate_sql_path(path: Path, arg_name: str, must_exist: bool) -> None:
    if path.suffix.lower() != ".sql":
        raise ScriptError(f"The {arg_name} file must have a .sql extension.")

    if must_exist and not path.exists():
        raise ScriptError(f"The {arg_name} file '{path}' does not exist.")

    if must_exist and not path.is_file():
        raise ScriptError(f"The {arg_name} path '{path}' is not a file.")


def parse_fields(raw_fields: str | None) -> list[str]:
    if not raw_fields:
        return ["id"]

    fields = [field.strip().lower() for field in raw_fields.split(",") if field.strip()]

    if not fields:
        raise ScriptError("At least one field must be provided.")

    duplicated = sorted({field for field in fields if fields.count(field) > 1})
    if duplicated:
        raise ScriptError(f"Duplicated field(s): {', '.join(duplicated)}")

    invalid = [field for field in fields if not re.match(r"^[a-zA-Z_][a-zA-Z0-9_]*$", field)]
    if invalid:
        raise ScriptError(f"Invalid field name(s): {', '.join(invalid)}")

    return fields


def split_sql_statements(sql_content: str) -> list[str]:
    """
    Split SQL statements by semicolon, while respecting single quoted strings,
    double quoted strings, line comments and block comments.
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
    Split a string by commas while respecting quotes and nested parentheses.
    Useful for SQL column lists, values lists and update assignments.
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


def normalize_identifier(identifier: str) -> str:
    return identifier.strip().strip('"').strip("`").strip("[").strip("]").lower()


def parse_insert_statement(statement: str) -> tuple[list[str], list[list[str]], tuple[int, int]]:
    """
    Parse a simple INSERT statement with explicit columns.

    Supported:
      INSERT INTO table_name (id, name) VALUES ('...', '...');
      INSERT INTO table_name (id, name) VALUES ('...', '...'), ('...', '...');
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


def parse_update_statement(statement: str) -> tuple[list[str], list[str], tuple[int, int]]:
    """
    Parse a simple UPDATE statement.

    Supported:
      UPDATE table_name SET id = '...', name = '...' WHERE ...;
      UPDATE table_name SET id = '...', name = '...';
    """
    clean_statement = strip_trailing_semicolon(statement)

    set_match = re.search(r"\bset\b", clean_statement, re.IGNORECASE)
    if not set_match:
        raise ScriptError("UPDATE statement must contain a SET clause.")

    where_match = re.search(r"\bwhere\b", clean_statement[set_match.end() :], re.IGNORECASE)
    set_start = set_match.end()

    if where_match:
        set_end = set_match.end() + where_match.start()
    else:
        set_end = len(clean_statement)

    set_clause = clean_statement[set_start:set_end].strip()
    assignments = split_top_level_commas(set_clause)

    fields: list[str] = []

    for assignment in assignments:
        if "=" not in assignment:
            raise ScriptError(f"Invalid UPDATE assignment: {assignment}")

        field_name = assignment.split("=", 1)[0]
        fields.append(normalize_identifier(field_name))

    return fields, assignments, (set_start, set_end)


def validate_uuid_value(value: str, strict_uuid: bool) -> None:
    normalized = value.strip().strip("'").strip('"')

    if strict_uuid and not UUID_REGEX.match(normalized):
        raise ScriptError(f"Value '{normalized}' is not a valid UUID.")


def replace_insert_fields(
    statement: str,
    fields_to_replace: list[str],
    strict_uuid: bool,
    statement_index: int,
) -> tuple[str, list[Replacement]]:
    columns, tuples, values_range = parse_insert_statement(statement)

    missing = [field for field in fields_to_replace if field not in columns]
    if missing:
        raise ScriptError(f"Missing field(s) in INSERT statement: {', '.join(missing)}")

    replacements: list[Replacement] = []
    field_indexes = {field: columns.index(field) for field in fields_to_replace}

    updated_tuples: list[str] = []

    for tuple_values in tuples:
        updated_values = tuple_values[:]

        for field, index in field_indexes.items():
            old_value = tuple_values[index].strip()
            validate_uuid_value(old_value, strict_uuid)

            new_value = str(generate_uuid7())
            updated_values[index] = f"'{new_value}'"

            replacements.append(
                Replacement(
                    field=field,
                    old_value=old_value.strip("'").strip('"'),
                    new_value=new_value,
                    statement_index=statement_index,
                )
            )

        updated_tuples.append(f"({', '.join(updated_values)})")

    start, end = values_range
    clean_statement = strip_trailing_semicolon(statement)
    updated_statement = clean_statement[:start] + ", ".join(updated_tuples) + clean_statement[end:]

    return updated_statement + ";", replacements


def replace_update_fields(
    statement: str,
    fields_to_replace: list[str],
    strict_uuid: bool,
    statement_index: int,
) -> tuple[str, list[Replacement]]:
    fields, assignments, set_range = parse_update_statement(statement)

    missing = [field for field in fields_to_replace if field not in fields]
    if missing:
        raise ScriptError(f"Missing field(s) in UPDATE statement: {', '.join(missing)}")

    replacements: list[Replacement] = []
    updated_assignments: list[str] = []

    for assignment in assignments:
        left, right = assignment.split("=", 1)
        field = normalize_identifier(left)

        if field not in fields_to_replace:
            updated_assignments.append(assignment)
            continue

        old_value = right.strip()
        validate_uuid_value(old_value, strict_uuid)

        new_value = str(generate_uuid7())
        updated_assignments.append(f"{left.strip()} = '{new_value}'")

        replacements.append(
            Replacement(
                field=field,
                old_value=old_value.strip("'").strip('"'),
                new_value=new_value,
                statement_index=statement_index,
            )
        )

    start, end = set_range
    clean_statement = strip_trailing_semicolon(statement)
    updated_statement = clean_statement[:start] + " " + ", ".join(updated_assignments) + " " + clean_statement[end:].lstrip()

    return updated_statement.rstrip() + ";", replacements


def replace_statement(
    statement: str,
    fields_to_replace: list[str],
    strict_uuid: bool,
    statement_index: int,
) -> tuple[str, list[Replacement]]:
    kind = statement_type(statement)

    if kind == "insert":
        return replace_insert_fields(statement, fields_to_replace, strict_uuid, statement_index)

    if kind == "update":
        return replace_update_fields(statement, fields_to_replace, strict_uuid, statement_index)

    raise ScriptError("Only INSERT and UPDATE statements are supported.")


def validate_statements(statements: Iterable[str]) -> None:
    unsupported = []

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


def build_output_path(input_path: Path, output_arg: str | None, in_place: bool, dry_run: bool) -> Path | None:
    if dry_run:
        return None

    if in_place:
        return input_path

    if output_arg:
        return Path(output_arg)

    raise ScriptError("Missing output target. Use -o <file> or --in-place.")


def write_output(output_path: Path, content: str, create_backup: bool) -> None:
    if create_backup:
        backup_path = output_path.with_suffix(output_path.suffix + ".bak")
        shutil.copy2(output_path, backup_path)

    output_path.write_text(content, encoding="utf-8")


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Replace UUID values in SQL INSERT and UPDATE statements with UUIDv7 identifiers.",
        epilog=(
            "Examples:\n"
            "  python3 uuid7_sql_replacer.py -i input.sql -o output.sql\n"
            "  python3 uuid7_sql_replacer.py -i input.sql --in-place\n"
            "  python3 uuid7_sql_replacer.py -i input.sql -o output.sql -f id,session_id\n"
            "  python3 uuid7_sql_replacer.py -i input.sql --dry-run"
        ),
        formatter_class=argparse.RawTextHelpFormatter,
    )

    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Input .sql file containing INSERT/UPDATE statements.",
    )

    parser.add_argument(
        "-o",
        "--output",
        help="Output .sql file. Required unless --in-place or --dry-run is used.",
    )

    parser.add_argument(
        "-f",
        "--fields",
        default="id",
        help="Comma-separated list of fields to replace. Default: id",
    )

    parser.add_argument(
        "--in-place",
        action="store_true",
        help="Overwrite the input file. Must be explicitly enabled.",
    )

    parser.add_argument(
        "--backup",
        action="store_true",
        help="Create a .bak backup before overwriting with --in-place.",
    )

    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show replacements without writing any file.",
    )

    parser.add_argument(
        "--allow-non-uuid",
        action="store_true",
        help="Allow replacing values that are not valid UUIDs.",
    )

    parser.add_argument(
        "--plain",
        action="store_true",
        help="Print only replacement lines without extra status messages.",
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
        input_path = Path(args.input)
        validate_sql_path(input_path, "input", must_exist=True)

        if args.output and args.in_place:
            raise ScriptError("Use either -o <file> or --in-place, not both.")

        if args.backup and not args.in_place:
            raise ScriptError("--backup can only be used together with --in-place.")

        output_path = build_output_path(input_path, args.output, args.in_place, args.dry_run)

        if output_path is not None:
            validate_sql_path(output_path, "output", must_exist=False)

        fields_to_replace = parse_fields(args.fields)
        sql_content = input_path.read_text(encoding="utf-8")

        statements = split_sql_statements(sql_content)

        if not statements:
            raise ScriptError("Input file does not contain any SQL statement.")

        validate_statements(statements)

        strict_uuid = not args.allow_non_uuid

        print_info(f"Processing {len(statements)} SQL statement(s)...", use_color, args.plain)
        print_info(f"Fields to replace: {', '.join(fields_to_replace)}", use_color, args.plain)

        updated_statements: list[str] = []
        all_replacements: list[Replacement] = []

        for index, statement in enumerate(statements, start=1):
            updated_statement, replacements = replace_statement(
                statement=statement,
                fields_to_replace=fields_to_replace,
                strict_uuid=strict_uuid,
                statement_index=index,
            )

            updated_statements.append(updated_statement)
            all_replacements.extend(replacements)

        if not all_replacements:
            print_warn("No UUID values were replaced.", use_color, args.plain)
        else:
            for replacement in all_replacements:
                print(
                    f"Statement #{replacement.statement_index} | "
                    f"Field: {replacement.field} | "
                    f"Previous UUID: {replacement.old_value} -> "
                    f"New UUID: {replacement.new_value}"
                )

        updated_sql = "\n".join(updated_statements) + "\n"

        if args.dry_run:
            print_info("Dry-run enabled. No file was written.", use_color, args.plain)
            return

        if output_path is None:
            raise ScriptError("Output path could not be resolved.")

        write_output(output_path, updated_sql, create_backup=args.backup)

        print_info(f"All UUIDs replaced successfully. Output saved to '{output_path}'.", use_color, args.plain)

        if args.backup:
            backup_path = output_path.with_suffix(output_path.suffix + ".bak")
            print_info(f"Backup created at '{backup_path}'.", use_color, args.plain)

    except ScriptError as error:
        print_error(str(error), use_color)
        sys.exit(1)

    except KeyboardInterrupt:
        print_error("Execution interrupted by user.", use_color)
        sys.exit(130)


if __name__ == "__main__":
    main()