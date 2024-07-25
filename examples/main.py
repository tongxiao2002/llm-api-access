import json
from llm_api_access import (
    parse_args,
    DataArguments,
    LLMRunnerWrapperBase
)


class Runner(LLMRunnerWrapperBase):
    def load_data(data_args: DataArguments):
        dataset = []
        with open(data_args.dataset_filepath, "r", encoding="utf-8") as fin:
            for idx, line in enumerate(fin):
                dataitem = json.loads(line.strip())
                dataset.append(dataitem)
        return dataset

    def prepare_llm_inputs(inputs: dict, prompt_template: str):
        prompt = prompt_template.format(query=inputs['query'])
        return prompt

    def postprocess_llm_outputs(inputs: dict, response: str, prompt: str, *args, **kwargs):
        resp_item = {
            "id": inputs['id'],
            "query": prompt,
            "response": response,
        }
        return resp_item


if __name__ == "__main__":
    prompt_template = "{query}"
    # cfg_file = config/config.yaml
    arguments = parse_args()
    runner = Runner(arguments=arguments, prompt_template=prompt_template)

    runner.run_llm_api()
