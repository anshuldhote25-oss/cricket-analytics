import sys
from tabulate import tabulate
from colorama import init, Fore, Style
from config import validate
from database import test_connection, run_query
from agent import CricketAgent

init(autoreset=True) 


def print_header():
    print(Fore.CYAN + Style.BRIGHT + """
╔══════════════════════════════════════════════════════════════╗
║               Cricket Analytics v1.0                         ║
╚══════════════════════════════════════════════════════════════╝""")
    print(Fore.WHITE + "  Type a question, 'help' for examples, or 'quit' to exit.\n")


def print_help():
    examples = [
        "Show me the top 10 T20 batters by strike rate (min 30 balls)",
        "Which bowlers have the best economy in the powerplay?",
        "Top U19 female batters by total runs this season",
        "Best leg-spin bowlers in SMAT by wickets taken",
        "Top-order batters (positions 1-3) with boundary % over 20 in T20",
        "Which all-rounders have strike rate above 130 and economy below 8?",
        "Compare batting strike rates by phase for senior male T20",
        "Best death-over bowlers by dot ball percentage",
        "Top 5 wicket-keepers by runs scored",
        "Which districts produce the most runs in domestic cricket?",
    ]
    print(Fore.YELLOW + "\n  Example questions:")
    for i, ex in enumerate(examples, 1):
        print(f"    {i:2}. {ex}")
    print()


def print_results(rows: list, columns: list, explanation: str,
                  assumptions: str, sql: str, show_sql: bool):
    # Explanation
    print(Fore.GREEN + f"\n  ✓ {explanation}")
    if assumptions:
        print(Fore.YELLOW + f"  ℹ  {assumptions}")

    # SQL (optional)
    if show_sql and sql:
        print(Fore.BLUE + "\n  Generated SQL:")
        print(Fore.BLUE + "  " + "─" * 60)
        for line in sql.split("\n"):
            print(Fore.BLUE + f"    {line}")
        print(Fore.BLUE + "  " + "─" * 60)

    # Results
    if not rows:
        print(Fore.YELLOW + "\n  No results found for this query.")
        print(Fore.YELLOW + "  Try relaxing the filters or checking the tournament name.\n")
        return

    print(Fore.WHITE + f"\n  Results ({len(rows)} row{'s' if len(rows) != 1 else ''}):\n")

    # Formatting
    formatted = []
    for row in rows:
        formatted_row = {}
        for k, v in row.items():
            if isinstance(v, float):
                formatted_row[k] = f"{v:.2f}"
            elif v is None:
                formatted_row[k] = "—"
            else:
                formatted_row[k] = v
        formatted.append(formatted_row)

    print(tabulate(
        [list(r.values()) for r in formatted],
        headers=columns,
        tablefmt="rounded_outline",
        stralign="left",
        numalign="right",
        maxcolwidths=30,
    ))
    print()


def print_error(message: str):
    print(Fore.RED + f"\n  ✗ {message}\n")


def print_info(message: str):
    print(Fore.YELLOW + f"\n  ℹ  {message}\n")


# Main

def main():
    print_header()

    try:
        validate()
    except EnvironmentError as e:
        print_error(str(e))
        sys.exit(1)

    print(Fore.WHITE + "  Connecting to database...", end=" ")
    if not test_connection():
        print_error("Cannot connect to the database. Check your .env settings.")
        sys.exit(1)
    print(Fore.GREEN + "connected ✓")

    print(Fore.WHITE + "  Loading AI agent...", end=" ")
    try:
        agent = CricketAgent()
        print(Fore.GREEN + "ready ✓\n")
    except Exception as e:
        print_error(f"Failed to initialize AI agent: {e}")
        sys.exit(1)

    show_sql = False  

    while True:
        try:
            question = input(Fore.CYAN + "  Ask > " + Style.RESET_ALL).strip()
        except (KeyboardInterrupt, EOFError):
            print(Fore.WHITE + "\n\n  Goodbye!\n")
            break

        if not question:
            continue

        if question.lower() in ("quit", "exit", "q"):
            print(Fore.WHITE + "\n  Goodbye!\n")
            break

        if question.lower() == "help":
            print_help()
            continue

        if question.lower() == "sql":
            show_sql = not show_sql
            state = "ON" if show_sql else "OFF"
            print_info(f"SQL display turned {state}.")
            continue

        print(Fore.WHITE + "  Thinking...", end="\r")

        result = agent.ask(question)

        if result["intent"] in ("out_of_scope", "external", "unanswerable"):
            print_info(result["explanation"])
            continue

        if result["intent"] == "error":
            print_error(result.get("error") or result.get("explanation") or "Unknown error")
            continue

        if result["intent"] == "validation_error":
            print_error(f"SQL validation failed: {result['error']}")
            print_info("The AI generated an unsafe query. Please rephrase your question.")
            continue

        try:
            rows, columns = run_query(result["sql"])
            print(" " * 20, end="\r")  
            print_results(
                rows, columns,
                result["explanation"],
                result["assumptions"],
                result["sql"],
                show_sql,
            )
        except Exception as e:
            print_error(f"Query execution failed: {e}")
            if show_sql and result["sql"]:
                print_info(f"Failed SQL:\n{result['sql']}")


if __name__ == "__main__":
    main()
