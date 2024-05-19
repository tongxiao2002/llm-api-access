import os
import json
import numpy as np
from utils import readjsonl2list
from typing import List, Any
from arguments import DataArguments


def empty_data_postprocess_func(data_args: DataArguments, logger=None):
    return


def load_gpt4_dataset(data_args: DataArguments, logger=None) -> List[Any]:
    dataset = []
    with open(data_args.dataset_filepath, "r", encoding="utf-8") as fin:
        for line in fin:
            dataset.append(json.loads(line.strip()))

    # 通过 id 去重，若数据集中没有 'id' 字段则需要修改
    if os.path.isfile(data_args.output_filepath):
        exist_data = readjsonl2list(data_args.output_filepath)
        exist_data_ids = set([item['id'] for item in exist_data])
        data_remains = [item for item in dataset if item['id'] not in exist_data_ids]
        dataset = data_remains

    return dataset


def load_svamp_dataset(data_args: DataArguments, logger=None):
    dataset = []
    with open(data_args.dataset_filepath, "r", encoding="utf-8") as fin:
        for line in fin:
            item = json.loads(line.strip())
            item['id'] = item['ID']
            item['question'] = item['Body'] + ' ' + item['Question']
            item['answer'] = item['Answer']
            item.pop('Body')
            item.pop('Question')
            item.pop('Answer')
            item.pop('ID')
            dataset.append(item)

    if os.path.isfile(data_args.output_filepath):
        exist_data = readjsonl2list(data_args.output_filepath)
        exist_data_ids = set([item['id'] for item in exist_data])
        data_remains = [item for item in dataset if item['id'] not in exist_data_ids]
        dataset = data_remains

    return dataset


def load_asdiv_dataset(data_args: DataArguments, logger=None):
    dataset = []
    with open(data_args.dataset_filepath, "r", encoding="utf-8") as fin:
        for line in fin:
            dataset.append(json.loads(line.strip()))

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
    results = readjsonl2list(data_args.number_extraction_output_filepath)
    # if args.number_extraction:
    # count extraction accuracy
    extract_acc_list = [not item['extract_failed'] for item in results]
    logger.info(f"Extraction Accuracy: {np.mean(extract_acc_list)}")

    acc_list = [item["acc"] for item in results]
    logger.info(f"Acc: {np.mean(acc_list)}")
