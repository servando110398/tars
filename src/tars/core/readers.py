import dlt
import pandas as pd


@dlt.transformer
def read_excel(file_obj):
        with file_obj.open() as file:
            # Read from the Excel file and yield its content as dictionary records.
            yield pd.read_excel(file).to_dict(orient="records")
