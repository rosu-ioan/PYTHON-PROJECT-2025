from rich import print

def print_error(msg: str):
    """Print an error message with a colored "ERROR" prefix."""

    print("[red]ERROR[/red]: " + msg)

def print_table_color(table: dict[str, str]):
    """Print an aligned table with colored fields."""
    width = len(max(table.keys(), key=len))
    for name, value in table.items():
        print(f"[blue]{name:<{width}}[/blue]: {value}")

