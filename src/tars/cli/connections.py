import typer
from rich.prompt import IntPrompt

from tars.core.settings import add_connection
from tars.ui.display import build_connections_table, console


def init():
    "Enter a new server and database connection"
    server = typer.prompt("server ")
    database = typer.prompt("database ")
    add_connection(server,database)


def setup_connection():
    "Choose a connection from saved configurations"
    current_settings_table = build_connections_table()
    console.print(current_settings_table)
    console.print("")
    rows = list(zip(*(col.cells for col in current_settings_table.columns)))

    choice = IntPrompt.ask("Select a row",
                           choices=[str(i) for i in range(1, current_settings_table.row_count + 1)],
                           )
    row = rows[choice - 1]

    server = row[0]
    database = row[1]

    if choice:
        return server , database
    else:
        console.print("\n[red]No connection selected.[/red]")


def check_current_setup():
    "See available saved database connections"
    connections = build_connections_table()
    console.print(connections)
