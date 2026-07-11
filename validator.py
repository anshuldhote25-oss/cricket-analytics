import sqlglot
import sqlglot.expressions as exp


# Statements that must never reach the database
BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "TRUNCATE", "CREATE", "GRANT", "REVOKE", "EXECUTE",
    "EXEC", "CALL", "COPY", "VACUUM", "REINDEX",
]


class ValidationError(Exception):
    pass


def validate_sql(sql: str) -> str:
    """
    Validate that sql is a safe, read-only SELECT statement.
    Returns the (possibly whitespace-cleaned) sql if valid.
    Raises ValidationError with a clear message if not.
    """
    if not sql or not sql.strip():
        raise ValidationError("Empty SQL — nothing to execute.")

    sql = sql.strip().rstrip(";")

    # 1. Block any dangerous keywords (case-insensitive)
    upper = sql.upper()
    for kw in BLOCKED_KEYWORDS:
        # Check as a word boundary to avoid false positives
        import re
        if re.search(rf'\b{kw}\b', upper):
            raise ValidationError(
                f"Blocked keyword '{kw}' detected. "
                f"Only SELECT queries are permitted."
            )

    # 2. Parse with sqlglot to confirm it's a valid SELECT
    try:
        parsed = sqlglot.parse(sql, dialect="postgres")
    except Exception as e:
        raise ValidationError(f"SQL parse error: {e}")

    if not parsed:
        raise ValidationError("Could not parse the SQL statement.")

    # Allow only SELECT statements
    for statement in parsed:
        if not isinstance(statement, exp.Select):
            raise ValidationError(
                f"Only SELECT statements are permitted. "
                f"Got: {type(statement).__name__}"
            )

    # 3. Check for multiple statements (e.g. SELECT 1; DROP TABLE)
    if len(parsed) > 1:
        raise ValidationError(
            "Multiple SQL statements detected. "
            "Only a single SELECT is permitted per query."
        )

    return sql
