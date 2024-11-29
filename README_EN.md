# llm-api-access
[中文](./README.md) | English

A personal codebase for accessing LLM APIs. Essentially, it implements a simple producer-consumer framework for parallel access to LLM APIs, specifically implemented in `llm_api_access/llm_runner.py`.

## Installation

First, clone this repository:

```bash
git clone https://github.com/tongxiao2002/llm-api-access
```

Then, navigate into the repository folder and install locally using pip:
```bash
cd llm-api-access
pip install .
```

## Usage

Currently, this repository only supports OpenAI’s chat/completions interface. If you have other requirements (such as embeddings), you can add them yourself in `llm_api_access/api_adaptor.py`.

### API_KEY

To start using, you need to add your `API_KEY`. Add your `API_KEY` in `llm_api_access/api_keys.py`. After adding, the api_keys dictionary should look like this:

```python
from llm_api_access.api_keys import api_keys

api_keys = {
    "openai": [
        "sk-xxxxxxxxxxx",
    ],
}
```

The key should be the API endpoint name, and the value should be a list of `API_KEY`s. The API endpoint name should match at least one of the `endpoint_name` command line parameters explained below.

### Interface

The `llm_api_access.base_wrapper` module provides a class `LLMRunnerWrapperBase` as the interface. Specifically, you should inherit from the `LLMRunnerWrapperBase` class and implement three methods: `load_data`, `prepare_llm_inputs`, and `postprocess_llm_outputs`:

- `load_data`: Accepts a `DataArguments` (see `llm_api_access.arguments`) as a parameter and needs to implement data loading functionality. The returned data format should be a list of dictionaries, where each dictionary must contain an `id` field. For example:
  ```json
  [{"id": "0", "key1": "val1"}, {"id": "0", "key1": "val2"}, ...]
  ```
- `prepare_llm_inputs`: Accepts two parameters, a dictionary data sample ({"id": "0", "key1": "val1"}) and a prompt template. This function formats the text data from the dictionary into the prompt template to create the final prompt for the OpenAI models. For example:
  ```python
  def prepare_llm_inputs(self, inputs: dict, prompt_template):
      return prompt_template.format(question=inputs['question'])
  ```
  The result can be plain text (as shown above). If you need to access multimodal models with images, organize the result into fields, placing text and images into `prompt` and `image_url` fields, respectively. Images should be encoded in `base64` format:
  ```python
  def prepare_llm_inputs(self, inputs: dict, prompt_template):
      return {
          "prompt": prompt_template.format(question=inputs['question']),
          "image_url": inputs['image'],     # "data:image/......"
      }
  ```
- `postprocess_llm_outputs`: This function determines what content to save in the result file. The return value (must be a dictionary) will be saved directly to the result file. It primarily accepts three parameters: a single dictionary data sample from `load_data`, the final prompt (plain text) from `prepare_llm_inputs`, and the response from the OpenAI models. If `prepare_llm_inputs` provided a dictionary format prompt, additional fields (such as `image_url`) can be found in `kwargs`:

After implementing these three methods, you can directly call the class method `llm_run_api` to run this framework. See `examples/main.py` for a specific example.

### Command Line Arguments Explanation

The command line arguments for this framework match the parameters in `llm_api_access.arguments.EntireArguments`. They can be categorized as follows:

- `DataArguments`: Data loading parameters.
  - `dataset_name` (optional): Doesn’t affect the framework’s operation, just helps users identify the run.
  - `dataset_filepath`: Path to the data to be loaded, can be a file or directory. The specific loading logic is implemented by the user in load_data, so there are no special restrictions.
  - `output_filepath`: Path to save the results. This must be a file path and can be a non-existent path. The framework will automatically create the necessary directories.
  - `regenerate` (optional): Whether to delete the existing results and re-access all data from OpenAI. Default is `False`.
- `LLMArguments`: Parameters related to selecting the large language model.
  - `llm`: The name of the large language model to access, must be a model supported by OpenAI.
  - `image_detail` (optional): Used only for multimodal models. Selects the image quality, can be chosen from `["auto", "low", "high"]`. See OpenAI official documentation for details.
  - `endpoint_name`: API endpoint name. Considering that accessing OpenAI from within China often requires a proxy, this field is used to specify the proxy name. This field does not affect the framework’s operation, users just need to ensure that the endpoint name exists in the `api_keys` field in `llm_api_access.api_keys`.
  - `base_url`: The URL of the API endpoint corresponding to `endpoint_name`, e.g., `https://api.openai.com`, without the `/v1/chat/completions` suffix.
- GenerationArguments: Parameters related to LLM generation, consistent with [OpenAI official documentation](https://platform.openai.com/docs/api-reference/chat/create).
  - `temperature`
  - `top_p`
  - `n`
  - `max_completion_tokens`
- RunningArguments: Parameters specific to this run.
  - num_threads: The number of threads to use for parallel access in this run.
  - generate_log_file (optional): Whether to generate a log for this run. Default is `True`, recommended to set to `True`.

## Advanced Modifications and Usage

Coming soon.
