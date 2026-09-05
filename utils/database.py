import psycopg2
import os
import logging

class DataUtils:
    def __init__(self , db_config):
        self.db_config = db_config
        try:
            self.connect = psycopg2.connect(**db_config)
            print(f"connection successful")
            logging.info("connection successful in log")

        except Exception as e:
            print(f"error occured while connecting to database due to: {e}")
            self.connect = None

    def schema_details(self, schema_name):
        schema_info_context = ""

        connect = self.connect
        cursor = connect.cursor()

        schema_info_context = f"Data Schema: {schema_name}\n"

        try:
            cursor.execute("SELECT table_name from information_schema.tables where table_schema = %s;" , (schema_name))
            tables_list = cursor.fetchall()

            #Adding Table list
            for table in tables_list:
                table_name = table[0]
                schema_info_context = f"{schema_info_context}\n {table_name}\n"

                #Adding Column list
                cursor.execute("SELECT column_name, data_type FROM information_schema.columns WHERE table_name = %s;", (table_name))
                column_list = cursor.fetchall()

                for column in column_list:
                    column_name = column[0]
                    data_types = column[1]

                    schema_info_context = f"{schema_info_context} Column : {column_name} Data types : {data_types}"

                #Adding sample data
                cursor.execute(f"SELECT * FROM {schema_name}.{table_name} LIMIT 5;")
                sample_data = cursor.fetchall()

                schema_info_context = f"{schema_info_context} Sample Data\n"

                for row in sample_data:
                    schema_info_context = f"{schema_info_context} {row}\n"

        except Exception as e:
            print(f"Error occured while quering data due to : {e}")
            schema_info_context = f" error occured in schema_info_context due to : {e}"

        finally:
            if cursor:
                cursor.close()
            if connect:
                connect.close()
        return schema_info_context

    def execute_sql(self ,query):
        try:
            connect =self.connect
            cursor = connect.cursor()
            cursor.execute(query)
            result = cursor.fetchall()
            connect.commit()
        except Exception as e:
            print(f"Error occured when executing query : {e}")

        finally:
            if cursor:
                cursor.close()
            if connect:
                connect.close()

obj = DataUtils({
    "dbname" : os.getenv("dbname"),
    "host" : os.getenv("host"),
    "user" : os.getenv("user"),
    "password" : os.getenv("password"),
    "port" : os.getenv("port"),
}) 

result = obj.schema_details("public")

with open("test_schema_text" , "w") as f:
    f.write(result)