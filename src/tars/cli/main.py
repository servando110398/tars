import typer

from tars.cli.connections import check_current_setup, init, setup_connection
from tars.cli.load import load_file, load_files
from tars.core.settings import add_connection, config_path, ensure_files, flows_path, get_settings
from tars.ui.display import welcome

app = typer.Typer()

app.command("init")(init)
app.command("use")(setup_connection)
app.command("inspect-connections")(check_current_setup)
app.command("load-files")(load_files)
app.command("load")(load_file)


@app.callback(invoke_without_command=True)
def main(ctx:typer.Context):
    welcome()
    ensure_files()

    configs = get_settings(config_path)
    flows = get_settings(flows_path)

    ctx.obj = {
                "configs":configs,
                "flows":flows,
                "creds":""
                }

    if configs:
        "extract server an db from here"
        server , database = setup_connection()
    else:
        server = typer.prompt("server ")
        database = typer.prompt("database ")

    mssql_credentials = {
                        "drivername": "mssql+pyodbc",
                        "host": server,
                        "database": database,
                        "username": "",  # Set as empty string to pass dlt validation
                        "password": "",  # Set as empty string to pass dlt validation
                        "port": 1433,
                        "driver": "ODBC Driver 18 for SQL Server",
                        "query": {
                                "Trusted_Connection": "yes",
                                 "TrustServerCertificate": "yes"
                                }
                        }

    ctx.obj["creds"] = mssql_credentials

    add_connection(server,database)


if __name__ == "__main__":
    app()
