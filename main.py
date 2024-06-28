import json
from llm_api_access import (
    parse_args,
    run_llm_api,
    omit_existing_data_wrapper,
    DataArguments
)


@omit_existing_data_wrapper
def load_direct_input_output_jsonl_dataset(data_args: DataArguments, logger=None):
    dataset = []
    with open(data_args.dataset_filepath, "r", encoding="utf-8") as fin:
        for idx, line in enumerate(fin):
            dataitem = json.loads(line.strip())
            dataset.append(dataitem)
    return dataset


def producer_direct_input_process(inputs: dict, prompt_template: str, chat_one_turn_func):
    prompt = prompt_template.format(query=inputs['query'])
    result, err_msg = chat_one_turn_func(prompt)
    return prompt, result, err_msg


def consumer_direct_input_postprocess(inputs: dict, response: str, prompt: str, *args, **kwargs):
    resp_item = {
        "id": inputs['id'],
        "query": prompt,
        "response": response,
    }
    return resp_item


def main():
    arguments = parse_args()
    run_llm_api(
        arguments=arguments,
        llm_input_process_func=producer_direct_input_process,
        llm_output_postprocess_func=consumer_direct_input_postprocess,
        data_load_func=load_direct_input_output_jsonl_dataset,
    )


if __name__ == "__main__":
    main()
