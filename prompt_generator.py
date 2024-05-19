'''
@Author: tongxiao
@FileName: prompt.py
@CreateTime: 2024-03-07 23:33:54
@Description:

'''

import os
from arguments import DataArguments, RunningArguments


instructions = {
    "zero-shot-cot": "Let's think step by step.",
    "ps": (
        "Let's first understand the problem and devise a plan to solve the problem. "
        "Then, let's carry out the plan to solve the problem step by step."
    ),
    "ps+": (
        "Let's first understand the problem, extract relevant variables and their corresponding numerals, "
        "and devise a plan. Then, let's carry out the plan, calculate intermediate variables (pay attention to "
        "correct numeral calculation and commonsense), solve the problem step by step, and show the answer."
    ),
    "number-extraction": (
        "Given the the 'Quesion' and 'Answer', "
        "your goal is to extract the final numerical result from the 'Answer' part, "
        "and put the numerical result after the 'Result' part. You should give me only the numerical answer."
    )
}

templates = {
    "number-extraction": "Quesion: {question}\nAnswer: {answer}\nResult: ",
    "qa": "Q: {question}\nA: "
}


core_instruction = (
    "Let's first understand the problem, "
    "then list all the known conditions which are formed by numbers or "
    "quantitative relationships along with their contexts from problem text, "
    "and identify the final goal of the problem.\n"
)

zero_shot_cot_core = (
    "Let's first understand the problem, "
    "then list all the known conditions which are formed by numbers or "
    "quantitative relationships along with their contexts from problem text, "
    "and identify the final goal of the problem. Then let's solve the problem step by step.\n"
)

ps_core = (
    "Let's first understand the problem, "
    "then list all the known conditions which are formed by numbers or "
    "quantitative relationships along with their contexts from problem text, "
    "and identify the final goal of the problem. "
    "Then let's understand the problem and devise a plan to solve the problem. "
    "Let's carry out the plan to solve the problem step by step."
)


class PromptGenerator:
    def __init__(self, data_args: DataArguments, running_args: RunningArguments):
        self.data_args = data_args
        self.running_args = running_args
        self.prompt = data_args.prompt_template

    @property
    def prompt_template(self):
        if self.prompt:
            return self.prompt
        try:
            # instruction
            instruction = instructions[self.data_args.prompt_name]
            if self.data_args.use_core_instruction and not self.running_args.is_number_extraction:
                if self.data_args.prompt_name == "zero-shot-cot":
                    instruction = zero_shot_cot_core
                elif self.data_args.prompt_name == "ps":
                    instruction = ps_core
                else:
                    instruction = core_instruction + instruction
            if self.running_args.is_number_extraction:
                instruction = instructions['number-extraction']

            # template
            if self.running_args.is_number_extraction:
                qa_template = templates["number-extraction"]
            else:
                qa_template = templates['qa']
        except Exception:
            raise

        return "\n\n".join([item for item in [qa_template, instruction] if len(item) > 0])
