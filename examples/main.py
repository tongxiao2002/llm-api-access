import json
from llm_api_access import (
    parse_args,
    run_llm_api,
    llm_inputs_wrapper,
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


@llm_inputs_wrapper
def producer_direct_input_process(inputs: dict, prompt_template: str):
    prompt = prompt_template.format(query=inputs['query'])
    return prompt


def consumer_direct_input_postprocess(inputs: dict, response: str, prompt: str):
    resp_item = {
        "id": inputs['id'],
        "query": prompt,
        "response": response,
    }
    return resp_item


def main(prompt_template: str, cfg_file: str = None):
    arguments = parse_args(cfg_file=cfg_file)
    run_llm_api(
        arguments=arguments,
        prompt_template=prompt_template,
        llm_input_process_func=producer_direct_input_process,
        llm_output_postprocess_func=consumer_direct_input_postprocess,
        data_load_func=load_direct_input_output_jsonl_dataset,
    )


if __name__ == "__main__":
    prompt_template = "{query}"
    # cfg_file = config/config.yaml
    main(prompt_template=prompt_template)
