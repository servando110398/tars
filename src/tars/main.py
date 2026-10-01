import dlt
from dlt.sources.filesystem import filesystem , read_csv
import pandas as pd
import shutil
from datetime import datetime
from pathlib import Path
import typer
import os 
from typing import Annotated
import json
import hashlib
from rich import print
from rich.console import Console
from rich.table import Table
import questionary 
import click 
from dlt.destinations import mssql


APP_NAME = "TARS-de"
app_dir = typer.get_app_dir(APP_NAME)
config_path: Path = Path(app_dir) / "config.json"
flows_path: Path = Path(app_dir) / "flows.json"
    
app = typer.Typer(no_args_is_help=True)
console = Console()


@app.command("init")
def init():
    server = typer.prompt("server: ")
    database = typer.prompt("database: ")
    key = hashlib.sha256(f"{server}:{database}".encode()).digest()

    new_connection = {
        key :{ 
         "server": server , 
         "database": database
        } 
    }
    current_content = get_settings(config_path) 
    return update_json(key,current_content,new_connection,config_path)


@app.command("use")
def setup_connection():

    current_settings = get_settings(config_path)  
    current_settings_table = build_connections_table()
    console.print(current_settings_table)
    console.print("")

    connection_keys = list(current_settings.keys())

    selected_key = questionary.select(
        "Choose a connection profile:",
        choices=connection_keys
    ).ask()

    if selected_key:
        return selected_key
    else:
        console.print("\n[red]No connection selected.[/red]")


@app.command("inspect settings")
def check_current_setup():
    connections = build_connections_table()
    console.print(connections)



def get_settings(path: str)-> dict:
    if os.path.exists(path) and os.path.getsize(path) > 0:
        with open(path, "r") as file:
            current_settings = json.load(file)
    else:
        current_settings = {}
    return current_settings


def build_connections_table():
    app_dir = typer.get_app_dir(APP_NAME)
    config_path: Path = Path(app_dir) / "config.json"
    connections_table = Table(title="SQL Server Connections")
    connections_table.add_column("Server",style="magenta")
    connections_table.add_column("Database",justify="right",style="green")
    
    current_content = get_settings(config_path)  
    
    for connection in current_content.values():
        connections_table.add_row(connection["server"],connection["table"])

    return connections_table

def build_flows_table():
    app_dir = typer.get_app_dir(APP_NAME)
    flows_path: Path = Path(app_dir) / "flows.json"
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




@app.command("load files")
def load_files(
        ctx:typer.Context,
        source_folder:Annotated[str,typer.Argument(help="Path to the folder containing the files to be loaded.")] ,
        file_extension:Annotated[str,typer.Argument(help="File extension used to identify the files to be loaded.")],
        table_name : Annotated[str,typer.Argument(help="Name of the target table where the files will be loaded.")] , 
        schema_name:Annotated[str,typer.Argument(help="Name of the schema where the files will be loaded.")],
        load_strategy:Annotated[str,typer.Argument(help="Loading strategy to be used")] = "append"):
    """
    Load all files with the selected extension from the source folder into the target schema and table using the selected load strategy.
    """
    creds = ctx.obj

    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    pipeline = dlt.pipeline(
            pipeline_name="file_to_mssql_pipeline",
            #destination="mssql",
            destination=mssql(credentials=creds),
            dataset_name=schema_name  # This will map to a schema in SQL Server
        )
    
    files = filesystem(
        bucket_url=source_folder,
        file_glob=("*."+file_extension)  # Filter for specific file types if needed
        )
    
    strategy ={"csv":read_csv, "xls":read_excel , "xlsx":read_excel}

    archive_dir , failed_dir , source  = setup_folders(source_folder=source_folder)

    files_processed = 0 
    failed_files = 0 
    total_rows = 0 

    total_files = len(list(files))
    print(f"Folder: {source_folder}")
    print(f"Extension: {file_extension}")
    print(f"Files found: {total_files}")

    for file in list(files):  # snapshot the folder before moving anything
          file_name = file["file_name"]
          print(f"Processing file : {file_name} ...")
          file_path = source / file["relative_path"]
          new_file_name = f"{file_path.stem}__{timestamp}{file_path.suffix}"
          reader = ([file] | strategy[file_extension]()).with_name(table_name)
          load_info , is_success = try_run_pipeline(pipeline, reader, load_strategy)
          dest_path = archive_dir if is_success else failed_dir
          rows = load_info.metrics['row_counts'][table_name]  
          if is_success:
            files_processed += 1
            total_rows = total_rows + rows
          else:
            failed_files += 1

          shutil.move(file_path, dest_path / new_file_name)

    
    print(f"Processed files: {files_processed}")
    print(f"Total rows ingested: {total_rows}")
    print(f"Failed files: {failed_files}")



  
@app.command("load")
def load_file(ctx:typer.Context,
              file_name: Annotated[str,typer.Argument(help="Name of file to be loaded")],
              table_name: Annotated[str,typer.Argument(help="Name of the target table where the files will be loaded.")], 
              schema_name:Annotated[str,typer.Argument(help="Name of the schema where the file will be loaded.")],
              load_strategy:Annotated[str,typer.Argument(help="Loading strategy to be used")] = "append"):
    """
    Load file into the specified target schema and table using the selected load strategy.
    """

    print(f"Processing file : {file_name} ...")

    creds = ctx.obj
    timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
    pipeline = dlt.pipeline(
            pipeline_name="file_to_mssql_pipeline",
            #destination="mssql",
            destination=mssql(credentials=creds),
            dataset_name=schema_name  # This will map to a schema in SQL Server
        )    
    current_dir = str(Path.cwd() / "")
    archive_dir , failed_dir , source  = setup_folders(source_folder=current_dir)

    file_source = filesystem(
    bucket_url=current_dir,  # Path to the parent folder
    file_glob=f"{file_name}*"# Add * to match the exact single file
    )

    file_path = source / file_source["relative_path"]
    new_file_name = f"{file_path.stem}__{timestamp}{file_path.suffix}"
      
    reader = (file_source | read_csv()).with_name(table_name)

    load_info , is_success = try_run_pipeline(pipeline, reader, load_strategy)
    
    dest_path = archive_dir if is_success else failed_dir
    shutil.move(file_path, dest_path / new_file_name)
    generate_message(load_info , is_success,pipeline,file_name)



def generate_message(info , status_is_succes , pipeline , file_name,table_name):    
    if status_is_succes:
        total_rows = info.metrics['row_counts'][table_name]
        trace = pipeline.last_trace
        duration = trace.finished_at - trace.started_at
        seconds = duration.total_seconds()
        print(f"[green]:white_check_mark: Done. File {file_name} has been processed. \n{total_rows} rows ingested in {seconds:.2f} seconds[/green]")
    else:
        print("[red]:x: load failed![/red]")


@dlt.transformer
def read_excel(file_obj):
        with file_obj.open() as file:
            # Read from the Excel file and yield its content as dictionary records.
            yield pd.read_excel(file).to_dict(orient="records")

def setup_folders(source_folder):
    source = Path(source_folder)
    archive_dir = source / "Archive"
    failed_dir = source / "Failed"
    archive_dir.mkdir(exist_ok=True)
    failed_dir.mkdir(exist_ok=True)

    return archive_dir , failed_dir , source 


def try_run_pipeline(pipeline, reader, load_strategy) -> bool:
    try:
        load_info = pipeline.run(reader, write_disposition=load_strategy)
        return load_info , True
    except Exception as e:
        return load_info , False

def update_json(new_entry_key:str , configs:dict , new_entry:dict,configs_path)->str:
    if new_entry_key in configs :
        print("Those settings already exists")
        raise typer.Exit()
    else:
        configs.update(new_entry)
        with open(configs_path,"w") as file:
                json.dump(configs,file,indent=4)
        print("New connection setttings added successfully")
        return new_entry_key     


@app.callback("flow")
def flow(ctx:typer.Context):

    if not get_settings():
        print("You need to configure connection settings first")
        key = init()
    else:
        key = setup_connection()

    settings = get_settings()
    current_setting = settings[key]
    server = current_setting["server"]
    database = current_setting["database"]
    folder = typer.prompt("folder: ")
    file_extension = typer.prompt("file extension: ")    
    table = typer.prompt("table": ")  
    schema = typer.prompt("schema: ")
    strategy = typer.prompt("load strategy: ")       

    flow_key = hashlib.sha256(f"{server}:{database}:{schema}:{table}:{folder}:{file_extension}:{strategy}".encode()).digest()
    

    flow_config = { 
                    flow_key:{
                    "connection_key": key,
                    "server": server, 
                    "database": database,
                    "folder": folder,
                    "file_extension": file_extension,
                    "table": table,
                    "schema": schema,
                    "strategy": strategy,
                    }
    }

    creds = {
       "host": server,
      "database": database,
      "username": "",
      "password": "",
      "driver": "ODBC Driver 18 for SQL Server",
    } 

    ctx.obj = creds

    load_files(folder,file_extension,table,schema,strategy)

    


    """prompt user if wants to save flow  """
    response = typer.prompt("Would you like to save this flow?")
    if response == "Y":
        current_flow_config = get_settings(flows_path)
        return update_json(flow_key,current_flow_config,flow_config,flows_path)
    else:
        pass
        typer.exit()

app.command("run flow")
def run_existing_flow():
    flows = build_flows_table()
    console.print(flows)
    console.print("")
    

    current_flows = get_settings(flows_path)

    flows_keys = list(current_flows.keys())

    selected_key = questionary.select(
        "Choose a flow:",
        choices=flows_keys
    ).ask()

    if selected_key:
        "run flow"
        current_flows[selected_keys]
        

    else:
        "retry mechanism"
        console.print("\n[red]No connection selected.[/red]")






    "add a method to run available flows , print table and choose with arrows "

    












if __name__ == "__main__":
    app()
    

    