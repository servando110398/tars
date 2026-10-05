from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from tars.core.settings import APP_NAME, VERSION, config_path, flows_path, get_settings

console = Console()


def welcome():
    console.print(
        Panel.fit(
            f"[bold cyan]Welcome to {APP_NAME}[/]\n"
            f"[dim]v{VERSION} · type [bold yellow]--help[/bold yellow] to get started[/dim]",
            border_style="magenta",
            padding=(1, 4),
        )
    )


def build_connections_table():
    connections_table = Table(title="SQL Server Connections")
    connections_table.add_column("Server",style="magenta")
    connections_table.add_column("Database",justify="right",style="green")
    current_content = get_settings(config_path)
    for connection in current_content.values():
        connections_table.add_row(connection["server"],connection["database"])

    return connections_table


def build_flows_table():
    flows_table = Table(title="Data Ingestion Flows")
    flows_table.add_column("Server",style="#a6e3a1")
    flows_table.add_column("Database",justify="right",style="#a6e3a1")
    flows_table.add_column("Schema",justify="right",style="#a6e3a1")
    flows_table.add_column("Folder",justify="right",style="#a6e3a1")
    flows_table.add_column("File extension",justify="right",style="#a6e3a1")
    flows_table.add_column("Load strategy",justify="right",style="#a6e3a1")
    current_flows = get_settings(flows_path)

    for flow in current_flows.values():
        flows_table.add_row(flow["server"],flow["database"],flow["folder"],flow["file_extension"],flow["table"],flow["schema"],flow["strategy"])

    return flows_table
