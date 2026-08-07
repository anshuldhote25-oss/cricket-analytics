import sqlglot
import sqlglot.expressions as exp


BLOCKED_KEYWORDS = [
    "INSERT", "UPDATE", "DELETE", "DROP", "ALTER",
    "TRUNCATE", "CREATE", "GRANT", "REVOKE", "EXECUTE",
    "EXEC", "CALL", "COPY", "VACUUM", "REINDEX",
]


class ValidationError(Exception):
    pass


def validate_sql(sql: str) -> str:
    if not sql or not sql.strip():
        raise ValidationError("Empty SQL — nothing to execute.")

    sql = sql.strip().rstrip(";")

    import re
    upper = sql.upper()
    for kw in BLOCKED_KEYWORDS:
        if re.search(rf'\b{kw}\b', upper):
            raise ValidationError(
                f"Blocked keyword '{kw}' detected. "
                f"Only SELECT queries are permitted."
            )

    try:
        parsed = sqlglot.parse(sql, dialect="postgres")
    except Exception as e:
        raise ValidationError(f"SQL parse error: {e}")

    if not parsed:
        raise ValidationError("Could not parse the SQL statement.")

    for statement in parsed:
        if not isinstance(statement, exp.Select):
            raise ValidationError(f"Only SELECT statements are permitted.")

    if len(parsed) > 1:
        raise ValidationError("Multiple SQL statements not permitted.")

    return sql
