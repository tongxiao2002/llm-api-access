import os
import sys
from gpt_runner import Model
from prompt_generator import PromptGenerator
from utils import (
    get_logger,
)
from arguments import EntireArguments, DataArguments, RunningArguments
from runner_processor import (
    producer_direct_input_process,
    consumer_direct_input_postprocess,
    producer_gpt_solve_process,
    consumer_gpt_solve_postprocess,
    producer_number_extraction_process,
    consumer_number_extraction_postprocess,
)
from data_processor import (
    load_dataset,
    load_direct_input_output_jsonl_dataset,
    load_results_for_number_extraction,
    empty_data_postprocess_func,
    number_extraction_data_postprocess,
)
from transformers import HfArgumentParser
from omegaconf import OmegaConf


def main():
    parser = HfArgumentParser([EntireArguments])
    if len(sys.argv) == 2:
        # If we pass only one argument to the script and it's the path to a json file,
        # let's parse it to get our arguments.
        if sys.argv[1].endswith(".json") or sys.argv[1].endswith(".yaml"):
            arguments: EntireArguments = OmegaConf.load(os.path.abspath(sys.argv[1]))
        else:
            raise ValueError("Config file must be JSON or YAML file.")
    else:
        (arguments,) = parser.parse_args_into_dataclasses()
        arguments: EntireArguments = OmegaConf.structured(arguments)

    print(arguments)
    # decide process functions
    if arguments.is_number_extraction:
        producer_process_func = producer_number_extraction_process
        consumer_postprocess_func = consumer_number_extraction_postprocess

        data_load_and_preprocess_func = load_results_for_number_extraction
        data_postprocess_func = number_extraction_data_postprocess
        output_filepath = arguments.number_extraction_output_filepath
        arguments.llm = "gpt-3.5-turbo-0125"
    else:
        producer_process_func = producer_direct_input_process
        consumer_postprocess_func = consumer_direct_input_postprocess

        data_load_and_preprocess_func = load_dataset
        data_postprocess_func = empty_data_postprocess_func
        output_filepath = arguments.output_filepath

    if arguments.generate_log_file:
        logger = get_logger(output_dir=os.path.dirname(output_filepath))
        printer = logger.info
    else:
        logger = None
        printer = print

    data_args = DataArguments.from_dict(arguments)
    running_args = RunningArguments.from_dict(arguments)
    dataset = data_load_and_preprocess_func(data_args)

    if len(dataset) == 0:
        printer("There is no data need to be run. Experiment finished.")
        data_postprocess_func(data_args, logger=logger)
        return

    printer(
        f"Model: {arguments.llm}, # Data Items: {len(dataset)}"
    )

    prompt_generator = PromptGenerator(data_args, running_args)
    prompt_template = prompt_generator.prompt_template

    # load & run llm
    model = Model(
        llm=arguments.llm,
        logger=logger,
        prompt_template=prompt_template,
        producer_process_func=producer_process_func,
        consumer_postprocess_func=consumer_postprocess_func,
        endpoint_name=arguments.endpoint_name,
        endpoint_url=arguments.endpoint_url,
    )
    model.run(
        data_items=dataset,
        num_threads=arguments.num_threads,
        output_filename=output_filepath,
    )

    data_postprocess_func(data_args, logger=logger)


if __name__ == "__main__":
    main()
