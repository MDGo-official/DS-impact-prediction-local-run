import pandas as pd
import numpy as np

def rawData_to_df(raw_data_json):
    df = pd.DataFrame()

    x = raw_data_json['Acc_X']['Data']
    df["Time axis"] = range(0, len(x), 1)

    for sensor in raw_data_json["Sensors"]:
        title = str(sensor["Title"])
        if title.startswith("Gyro_") or title.startswith("Button"):
            df[title] = sensor["Data"]

    df["Acc_X"] = x
    df["Acc_Y"] = raw_data_json['Acc_Y']['Data']
    df["Acc_Z"] = raw_data_json['Acc_Z']['Data']

    return raw_data_json, df

def df_to_json(data_df):
    # converting columns names to keys and columns values to list for each column key
    return data_df.to_dict('list')

def json_to_df(data_json):
    # converting dict keys to columns names and dict values to columns values for each dict key
    data_df = pd.DataFrame.from_dict(data_json)
    return data_json, data_df
