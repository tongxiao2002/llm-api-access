import os
import logging
from .utils import (
    get_logger,
    llm_inputs_wrapper,
    omit_existing_data_wrapper,
)
from .arguments import (
    DataArguments,
    EntireArguments,
)
from .llm_runner import LLMRunner


class LLMRunnerWrapperBase:
    def __init__(
        self,
        arguments: EntireArguments,
        prompt_template: str,
    ):
        self.arguments = arguments
        self.prompt_template = prompt_template

        if self.arguments.generate_log_file:
            self.logger = get_logger(output_dir=os.path.dirname(self.arguments.output_filepath))
        else:
            self.logger = logging.getLogger(__file__)

    def load_data(self, data_args: DataArguments):
        raise NotImplementedError

    def prepare_llm_inputs(self, inputs: dict, prompt_template: str):
        raise NotImplementedError

    def postprocess_llm_outputs(self, inputs: dict, response: str, prompt: str, *args, **kwargs):
        raise NotImplementedError

    def run_llm_api(self):
        output_filepath = self.arguments.output_filepath

        data_args = DataArguments.from_args(self.arguments)
        dataset = omit_existing_data_wrapper(self.load_data)(data_args)

        if len(dataset) == 0:
            self.logger.info("There is no data need to be run. Experiment finished.")
            return

        self.logger.info(
            f"Model: {self.arguments.llm}, # Data Items: {len(dataset)}"
        )

        # load & run llm
        runner = LLMRunner(
            arguments=self.arguments,
            prompt_template=self.prompt_template,
            producer_process_func=llm_inputs_wrapper(self.prepare_llm_inputs),
            consumer_postprocess_func=self.postprocess_llm_outputs,
            logger=self.logger,
        )
        runner.run(
            data_items=dataset,
            num_threads=self.arguments.num_threads,
            output_filename=output_filepath,
        )
