# llm-api-access
中文 | [English](./README_EN.md)

自用 llm api 访问 codebase。本质上是实现了一个简单的 producer-consumer 框架用于并行访问 llm api，具体在 `llm_api_access/llm_runner.py` 中实现。

## 安装

首先 clone 本仓库：
```bash
git clone https://github.com/tongxiao2002/llm-api-access
```

然后进入本仓库文件夹后使用 pip 本地安装：
```bash
cd llm-api-access
pip install .
```

## 使用说明

本仓库目前仅支持 OpenAI 的 `chat/completions` 接口，若有其他需求（如 `embeddings`）可以自行在 `llm_api_access/api_adaptor.py` 中添加。

### API_KEY

开始使用时首先需要添加 `API_KEY`，在 `llm_api_access/api_keys.py` 中添加 `API_KEY`，添加完之后 `api_keys` 字典应当像下面这样：

```python
from llm_api_access.api_keys import api_keys


api_keys = {
    "openai": [
        "sk-xxxxxxxxxxx",
    ],
}
```

即以 API 端点名为 key，value 为 `API_KEY` 的列表。这里 API 端点名应当至少有一个与下面将要解释的命令行参数中 `endpoint_name` 保持一致。

### 调用接口

`llm_api_access.base_wrapper` 中提供了一个类 `LLMRunnerWrapperBase` 作为调用接口。具体而言，使用时应当继承 `LLMRunnerWrapperBase` 类并实现 3 个方法：`load_data`, `prepare_llm_inputs` 以及 `postprocess_llm_outputs`：
- `load_data`：接受一个 `DataArguments` (见 `llm_api_access.arguments`) 作为参数，需要实现数据加载功能。返回的数据格式应当为字典列表，其中每一个字典都必须包含 `id` 字段，其他随意，如：
  ```json
  [{"id": "0", "key1": "val1"}, {"id": "0", "key1": "val2"}, ...]
  ```
- `prepare_llm_inputs`：接受两个参数，分别是一个字典数据样本（`{"id": "0", "key1": "val1"}`）以及一个 prompt 模版。该函数的作用是根据用户的需求将字典中的文本数据填入到 prompt 模版中，形成最终给到 OpenAI models 的 prompt。如：
  ```python
  def prepare_llm_inputs(self, inputs: dict, prompt_template):
      return prompt_template.format(question=inputs['question'])
  ```
  返回结果可以是纯文本（如上例所示），若有图片要访问多模态模型，则需要将返回结果组织成字段形式，并分别将文本和图片放入到 `prompt` 和 `image_url` 字段中，图片需要编码为 `base64` 格式：
  ```python
  def prepare_llm_inputs(self, inputs: dict, prompt_template):
      return {
          "prompt": prompt_template.format(question=inputs['question']),
          "image_url": inputs['image'],     # "data:image/......"
      }
  ```
- `postprocess_llm_outputs`: 该函数用于决定用户将什么内容保存到结果文件中，该函数的返回结果（必须为字典形式）将被直接保存到结果文件。该函数主要接受三个参数，分别为 `load_data` 中的单个字典数据样本，`prepare_llm_inputs` 中的最终 prompt（纯文本），以及 OpenAI models 的返回结果。若 `prepare_llm_inputs` 提供了字典格式的 prompt，则除 `prompt` 字段外的字段内容（如 `image_url`）可以在 `kwargs` 中找到：
  ```python
  def postprocess_llm_outputs(self, inputs: dict, response: str, prompt: str, *args, **kwargs):
      return {
          "id": inputs['id'],
          "response": response,
          "question": inputs['question'],
          "prompt": prompt,
          # "image_url": kwargs["image_url"],
      }
  ```

在实现了这 3 个方法之后，就可以直接调用类方法 `llm_run_api`，即可运行本框架，具体实例见 `examples/main.py`。

### 命令行参数解释

本框架命令行参数与 `llm_api_access.arguments` 中 `EntireArguments` 的参数完全一致，具体可分为以下几类：
- `DataArguments`：数据加载参数。
  - `dataset_name` (option)：对框架运行没有任何实际作用，只是方便用户对本次运行进行辨识。
  - `dataset_filepath`：需要加载的数据所在位置，可以为文件也可以为文件夹路径，具体加载逻辑都在 `load_data` 中由用户自己实现，因此并没有特殊限制。
  - `output_filepath`：结果保存路径，该参数必须为文件路径，可以为当前文件夹不存在的路径，本框架会自动创建必需的文件夹。
  - `regenerate` (option)：是否删除已经得到的结果并对所有数据都重新访问 OpenAI 一遍，默认为 `False`。
- `LLMArguments`：大模型选择相关参数。
  - `llm`：需要访问的大模型名称，必须为 OpenAI 支持的 models。
  - `image_detail` (option)：仅用于多模态大模型。用于选择图片的清晰程度，可以从 `["auto", "low", "high"]` 中选择，具体含义请见 OpenAI 官方文档。
  - `endpoint_name`：API 站点名称。考虑到国内访问 OpenAI 基本上都需要一些中转站，该字段用于写入中转站名称。该字段对于框架运行并没有任何实际作用，用户只需要确保该站点名称在 `llm_api_access.api_keys` 中的 `api_keys` 字段中存在即可。
  - `endpoint_url`：与 `endpoint_name` 站点对应的 API 端口 URL。如 `https://api.openai.com`，不需要后缀 `/v1/chat/completions`。
- `GenerationArguments`：LLM 生成相关参数，与 [OpenAI 官网](https://platform.openai.com/docs/api-reference/chat/create)参数一致。
  - `temperature`
  - `top_p`
  - `n`
  - `max_completion_tokens`
- `RunningArguments`：本次运行特制的相关参数。
  - `num_threads`：本次运行需要使用多少个线程并行访问。
  - `generate_log_file` (option)：本次运行是否生成 log，默认为 `True`，建议设置为 `True`。

## 进阶修改与使用

Coming soon.
