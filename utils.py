import os
import re
import time
import json
import logging
import argparse


def get_logger(output_dir: str):
    logger = logging.getLogger(name="annotation")
    logger.setLevel(logging.INFO)

    # create directory if neccessary
    if not os.path.isdir(output_dir) and len(output_dir) > 0:
        os.makedirs(output_dir)

    log_filename = "default.log"
    file_handler = logging.FileHandler(filename=os.path.join(output_dir, log_filename))
    file_handler.setLevel(logging.INFO)
    formatter = logging.Formatter(fmt="%(asctime)s - %(levelname)s >> %(message)s", datefmt="%Y-%m-%d %H:%M:%S")
    file_handler.setFormatter(formatter)
    stream_handler = logging.StreamHandler()
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)
    logger.addHandler(file_handler)
    logger.addHandler(stream_handler)   # log to file and print to console
    return logger


def save2jsonl(name, data):
    with open(name, "w") as file:
        for dict_obj in data:
            json_str = json.dumps(dict_obj)
            file.write(json_str + "\n")


def readjsonl2list(name):
    data = []
    with open(name, "r") as file:
        for line in file:
            dict_obj = json.loads(line)
            data.append(dict_obj)
    return data
