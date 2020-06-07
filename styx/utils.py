import ujson
import logging
import uuid
from pathlib import Path


def get_logger():
    FORMAT = "[%(asctime)s][%(levelname)-5.5s] %(message)s"
    logging.basicConfig(format=FORMAT)
    log = logging.getLogger()
    log.setLevel(logging.INFO)
    return log


def get_json_content(file_path):
    file_content = None
    with open(file_path) as file_path_stream:
        file_content = ujson.load(file_path_stream)

    return file_content


def get_file_content(file_path):
    file_stream = open(file_path, "r")
    file_content = file_stream.read()
    file_stream.close()

    return file_content


def find_files(base_path, file_extensions):
    found_files = []
    for file_extension in file_extensions:
        found_files = found_files + list(base_path.rglob("*{}".format(file_extension)))

    return found_files


def get_random_prefix(project_stem):
    return "{}--{}".format(uuid.uuid1(), project_stem)
