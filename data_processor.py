import os
import json
import numpy as np
from utils import readjsonl2list
from typing import List, Any
from arguments import DataArguments


def empty_data_postprocess_func(data_args: DataArguments, logger=None):
    return


def load_dataset(data_args: DataArguments, logger=None):
    dataset = []
    with open(data_args.dataset_filepath, "r", encoding="utf-8") as fin:
        for idx, line in enumerate(fin):
            dataitem = json.loads(line.strip())
            if "id" not in dataitem:
                dataitem['id'] = idx
            dataset.append(dataitem)

    if os.path.isfile(data_args.output_filepath):
        exist_data = readjsonl2list(data_args.output_filepath)
        exist_data_ids = set([item['id'] for item in exist_data])
        data_remains = [item for item in dataset if item['id'] not in exist_data_ids]
        dataset = data_remains
    return dataset


def load_results_for_number_extraction(data_args: DataArguments, logger=None):
    dataset = readjsonl2list(data_args.output_filepath)

    if os.path.isfile(data_args.number_extraction_output_filepath):
        exist_data = readjsonl2list(data_args.number_extraction_output_filepath)
        exist_data_ids = set([item['id'] for item in exist_data])
        data_remains = [item for item in dataset if item['id'] not in exist_data_ids]
        dataset = data_remains

    return dataset


def number_extraction_data_postprocess(data_args: DataArguments, logger=None):
    printer = logger.info if logger else print

    results = readjsonl2list(data_args.number_extraction_output_filepath)
    # if args.number_extraction:
    # count extraction accuracy
    extract_acc_list = [not item['extract_failed'] for item in results]
    printer(f"Extraction Accuracy: {np.mean(extract_acc_list)}")

    acc_list = [item["acc"] for item in results]
    printer(f"Acc: {np.mean(acc_list)}")
