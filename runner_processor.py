import re
import math


def producer_direct_input_process(inputs: dict, prompt_template: str, chat_one_turn_func):
    prompt = prompt_template.format(query=inputs['query'])
    result, err_msg = chat_one_turn_func(prompt)
    return prompt, result, err_msg


def consumer_direct_input_postprocess(inputs: dict, response: str, prompt: str, *args, **kwargs):
    resp_item = {
        "id": inputs['id'],
        "query": inputs['query'],
        "response": response
    }
    return resp_item


def producer_gpt_solve_process(inputs: dict, prompt_template: str, chat_one_turn_func):
    prompt = prompt_template.format(question=inputs['question'])
    result, err_msg = chat_one_turn_func(prompt)
    return prompt, result, err_msg


def producer_geo_gpt_solve_process(inputs: dict, prompt_template: str, chat_one_turn_func):
    prompt = prompt_template.format(question=inputs['question'])
    result, err_msg = chat_one_turn_func(prompt, image_url=inputs['image_url'])
    return prompt, result, err_msg


def consumer_gpt_solve_postprocess(inputs: dict, response: str, prompt: str, *args, **kwargs):
    """
    inputs: input dict from raw data
    response: gpt response
    """
    # experimental_arguments = args[0]
    # answer = answer_cleansing(experimental_arguments, response)
    resp_item = {
        "id": inputs['id'],
        "acc": False,
        "question": inputs['question'],
        "answer": None,
        "ground-truth": inputs['answer'],
        "response": response,
        "prompt": prompt,
    }
    return resp_item


def producer_number_extraction_process(inputs: dict, prompt_template: str, chat_one_turn_func):
    prompt = prompt_template.format(
        question=inputs['question'],
        answer=inputs['response'],
    )
    result, err_msg = chat_one_turn_func(prompt)
    return prompt, result, err_msg


def consumer_number_extraction_postprocess(inputs: dict, response: str, prompt: str, *args, **kwargs):
    number_pattern = re.compile(r"-?\d+(\.\d{1,})?")
    # get rid of ',' in integers
    response = response.replace(',', '')

    if isinstance(inputs['ground-truth'], str):
        try:
            ground_truth = float(inputs['ground-truth'].replace(',', ''))
        except Exception:
            ground_truth = -100
    else:
        ground_truth = inputs['ground-truth']

    numerical_match = list(re.finditer(pattern=number_pattern, string=response))
    extract_failed = False
    if len(numerical_match) > 0:
        numerical_match = numerical_match[-1]
        numerical_result = float(numerical_match.group(0))
    else:
        numerical_result = -114514
        extract_failed = True
    resp_item = {
        "id": inputs['id'],
        "extract_failed": extract_failed,
        "acc": math.fabs(numerical_result - ground_truth) < 1e-3,
        "answer": numerical_result,
        "ground-truth": ground_truth,
        "response": response,
    }
    return resp_item
