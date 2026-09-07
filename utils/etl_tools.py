import requests
import os 
import pandas as pd
import json
from pathlib import Path

class EtlTools():
    def __init__(self):
        pass

    def extract_data(self , url : str , output_folder : str , format :str):
        """This tool extracts data from the api (url) and stores it in the location (output_folder)

            Args : url(str)  of the api endpoint where the data needs to be fetched
                   output_folder(str) the location where it will be stored

            Also the api i am using is a basic pokemon api just to showcase the process as
            i could not find any such apis
        """

        project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
        output_folder = os.path.join(project_root, output_folder)

        try:
            response = requests.get(url)
            response.raise_for_status()
            data = response.json()

            file_name = os.path.join(output_folder , f"extracted_data.{format}")
            os.makedirs(output_folder , exist_ok = True)

            records = data.get("results", data)
            df = pd.json_normalize(records)

            #a single record normalises to one very wide row, so flip it to
            #field/value rows. multi row responses are already readable.
            if len(df) == 1:
                df = df.T.reset_index()
                df.columns = ["field", "value"]

            if format == "csv":
                df.to_csv(file_name , index=False)
            elif format == "json":
                df.to_json(file_name , orient="records" , lines=True)
            elif format == "parquet":
                df.to_parquet(file_name , index=False)
            else:
                return f"unsupported format"

            return f"Data sucessfully extracted and loaded to {file_name}"

        except requests.exceptions.RequestException as e:
            return f"failed to extract data : {e}"

    def transform_load(self , file_path:str):
        """
        it takes the data transforms it and loads it in output_folder
        """

        file_extension = os.path.splitext(file_path)[1].lower()
        if file_extension == ".csv":
            df = pd.read_csv(file_path)
        elif file_extension == ".json":
            df = pd.read_json(file_path , lines=True)
        elif file_extension == ".parquet":
            df=pd.read_parquet(file_path)
        else:
            return f"Unsupported file extension : {file_extension}"

        top_3_rows = str(df.head(3))
        return top_3_rows

    def execute_load(self , code:str):
        """this tools executes the coded provied and gives a output"""

        try:
            exec(code)
            return "Code executed succesfully"
        except Exception as e:
            return f"error occured while executing the code due to : {e}"

if __name__ == "__main__":
    obj = EtlTools()
    path = "E:\\Coding_Archit\\Ai_Projects\\Data_Agent\\data\\extract\\extracted_data.csv"
    print(obj.transform_load(path))
