import os
import json
import logging
from typing import Callable
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


def readjson2list(name):
    data = []
    with open(name, "r", encoding="utf-8") as file:
        try:
            data = json.load(file)
        except Exception:
            for line in file:
                dict_obj = json.loads(line.strip())
                data.append(dict_obj)
    return data


def omit_existing_data_wrapper(data_processor_func: Callable):
    def data_processor(data_args: DataArguments):
        dataset = data_processor_func(data_args)

        if os.path.isfile(data_args.output_filepath) and not data_args.regenerate:
            is_empty_file = False
            with open(data_args.output_filepath) as fin:
                if len(fin.read().strip()) == 0:
                    os.remove(data_args.output_filepath)
                    is_empty_file = True

            exist_data = readjson2list(data_args.output_filepath) if not is_empty_file else []
            exist_data_ids = set([item['id'] for item in exist_data])
            data_remains = [item for item in dataset if item['id'] not in exist_data_ids]
            dataset = data_remains
        else:
            if os.path.isfile(data_args.output_filepath):
                os.remove(data_args.output_filepath)
        return dataset

    return data_processor


def llm_inputs_wrapper(llm_inputs_func: Callable):
    def llm_inputs_processor(inputs: dict, prompt_template: str, chat_one_turn_func):
        prompt = llm_inputs_func(inputs, prompt_template)
        if isinstance(prompt, str):
            prompt = {"prompt": prompt}
        result, err_msg = chat_one_turn_func(**prompt)
        return prompt, result, err_msg

    return llm_inputs_processor
