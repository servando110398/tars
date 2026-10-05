"""
@app.command("flow")
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


     creds = ctx.obj["creds"]

    load_files(folder,file_extension,table,schema,strategy)



    response = typer.prompt("Would you like to save this flow?")
    if response == "Y":
        current_flow_config = get_settings(flows_path)
        return update_json(flow_key,current_flow_config,flow_config,flows_path)
    else:
        pass
        typer.exit()


@app.command("run-flow")
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


"""
