import json
import os

from app.function.common import data_path


def load_point_json():
    json_file_path = os.path.join(data_path, "point.json")
    with open(json_file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def save_point_json(data):
    json_file_path = os.path.join(data_path, "point.json")
    with open(json_file_path, "w", encoding="utf-8") as file:
        json.dump(data, file, ensure_ascii=False, indent=2)


def get_point_data(paiwei_type):
    if paiwei_type in ("A1", "A2", "A3"):
        source_name = "paiwei_1"
    elif paiwei_type in ("B1", "B2", "B3"):
        source_name = "paiwei_5"
    elif paiwei_type == "C":
        source_name = "paiwei_10"
    else:
        return None, None

    point_data = load_point_json()
    for entry in point_data:
        if source_name in entry:
            return entry[source_name], source_name

    return None, source_name


def get_owner_point(owner_point):
    json_file_path = os.path.join(data_path, f"{owner_point}.json")
    with open(json_file_path, "r", encoding="utf-8") as file:
        return json.load(file)


def get_deceased_point(file_key):
    json_file_path = os.path.join(data_path, f"{file_key}.json")
    with open(json_file_path, "r", encoding="utf-8") as file:
        return json.load(file)
