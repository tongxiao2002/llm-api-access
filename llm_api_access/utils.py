import os
import json
import logging
from .arguments import DataArguments


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


def omit_existing_data_wrapper(data_processor_func):
    def data_processor(data_args: DataArguments, logger=None):
        dataset = data_processor_func(data_args, logger=None)

        if os.path.isfile(data_args.output_filepath) and not data_args.regenerate:
            exist_data = readjsonl2list(data_args.output_filepath)
            exist_data_ids = set([item['id'] for item in exist_data])
            data_remains = [item for item in dataset if item['id'] not in exist_data_ids]
            dataset = data_remains
        else:
            with open(data_args.output_filepath, "w", encoding="utf-8"):
                # wipe all existing data
                pass
        return dataset

    return data_processor
