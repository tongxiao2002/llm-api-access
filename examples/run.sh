#!/bin/bash
dataset_name="test"
dataset_filepath="data/test.jsonl"
llm=gpt-4o-mini

python main.py \
    --llm ${llm} \
    --dataset_name ${dataset_name} \
    --dataset_filepath ${dataset_filepath} \
    --temperature 0.0 \
    --n 1 \
    --max_completion_tokens 1024 \
    --num_threads 16 \
    --endpoint_name "openai" \
    --base_url "https://api.openai.com" \
    --output_filepath "runs/${dataset_name}/${dataset_name}_response.jsonl" \
    --generate_log_file \
    --save_as_json
