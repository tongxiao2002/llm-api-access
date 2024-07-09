import os
import logging
from typing import Callable
from .utils import get_logger, llm_inputs_wrapper, omit_existing_data_wrapper
from .llm_runner import LLMRunner
from .arguments import (
    parse_args,
    EntireArguments,
    LLMArguments,
    GenerationArguments,
    DataArguments,
    RunningArguments,
)

__all__ = [
    'parse_args',
    'run_llm_api',
    'llm_inputs_wrapper',
    'omit_existing_data_wrapper',
    'EntireArguments',
    'LLMArguments',
    'GenerationArguments',
    'RunningArguments',
    'LLMRunner',
]


def run_llm_api(
    arguments: EntireArguments,
    prompt_template: str,
    llm_input_process_func: Callable,
    llm_output_postprocess_func: Callable,
    data_load_func: Callable,
):
    output_filepath = arguments.output_filepath

    if arguments.generate_log_file:
        logger = get_logger(output_dir=os.path.dirname(output_filepath))
    else:
        logger = logging.getLogger(__file__)

    data_args = DataArguments.from_args(arguments)
    dataset = data_load_func(data_args)

    if len(dataset) == 0:
        logger.info("There is no data need to be run. Experiment finished.")
        return

    logger.info(
        f"Model: {arguments.llm}, # Data Items: {len(dataset)}"
    )

    # load & run llm
    runner = LLMRunner(
        arguments=arguments,
        prompt_template=prompt_template,
        producer_process_func=llm_input_process_func,
        consumer_postprocess_func=llm_output_postprocess_func,
        logger=logger,
    )
    runner.run(
        data_items=dataset,
        num_threads=arguments.num_threads,
        output_filename=output_filepath,
    )
