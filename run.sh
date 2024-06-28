#!/bin/bash
dataset_name="test"
dataset_filepath="data/test.jsonl"
llm=gpt-3.5-turbo-0125

python main.py \
    --llm ${llm} \
    --prompt_template "{query}" \
    --dataset_name ${dataset_name} \
    --dataset_filepath ${dataset_filepath} \
    --temperature 0.0 \
    --n 1 \
    --max_tokens 1024 \
    --num_threads 16 \
    --endpoint_name "openai" \
    --endpoint_url "https://api.openai.com" \
    --output_filepath "runs/${dataset_name}/${dataset_name}_response.jsonl" \
    --generate_log_file
