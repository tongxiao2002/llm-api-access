import os
import openai
from .api_keys import api_keys
from .arguments import EntireArguments
from openai.types.chat import ChatCompletion


class LLMRequester(object):
    def __init__(
        self,
        arguments: EntireArguments,
        logger,
        *args,
        **kwargs,
    ):
        self.arguments = arguments
        self.llm = self.arguments.llm
        self.logger = logger
        self.endpoint_name = self.arguments.endpoint_name
        self.endpoint_url = self.arguments.endpoint_url
        self.api_key_idx = 0
        self.max_retries = 10 if "max_retries" not in kwargs else kwargs["max_retries"]

        self.logger.info(f"Use {self.endpoint_name} as backend.")
        keys = api_keys[self.endpoint_name]
        self.openai_client = openai.OpenAI(
            api_key=keys[0],
            base_url=os.path.join(self.endpoint_url, "v1"),
            max_retries=self.max_retries,
        )

    def update_api_key(self):
        self.api_key_idx += 1
        if self.api_key_idx >= len(api_keys[self.endpoint_name]):
            raise RuntimeError("All API_KEY quota exceeded.")
        self.openai_client.api_key = api_keys[self.endpoint_name][self.api_key_idx]

    def get_payload(self, prompt, temperature=0.0, max_tokens=1000, n=1, **kwargs):
        if "image_url" not in kwargs:
            contents = prompt
        else:
            # add image
            contents = [
                {"type": "text", "text": prompt},
                {
                    "type": "image_url",
                    "image_url": {
                        "url": kwargs['image_url'],
                        "detail": self.arguments.image_detail,
                    },
                }
            ]
        payload = {
            "model": self.llm,
            "messages": [
                {"role": "system", "content": "You are a helpful asistant."},
                {"role": "user", "content": contents},
            ],
            "temperature": temperature,
            "max_tokens": max_tokens,
            "n": n,
            **kwargs,
        }
        return payload

    def request(self, payload) -> ChatCompletion:
        completion = self.openai_client.chat.completions.create(**payload)
        return completion

    def chat_one_turn(
        self, prompt, *args, temperature=0.0, max_tokens=1000, n=1, **kwargs
    ):
        err_msg = ""
        try:
            payload = self.get_payload(
                prompt=prompt, temperature=temperature, max_tokens=max_tokens, n=n, **kwargs,
            )
            completion = self.request(payload=payload)
            # assert 'error' not in response, f"Response format error: {response}"

            result = [
                completion.choices[i].message.content
                for i in range(len(completion.choices))
            ]
            result = "\n\n".join(result)
        except Exception as e:
            # error handling
            # if completion['error']['code'] == "content_policy_violation":
            #     return None, "content_policy_violation"
            # elif completion['error']['code'] == "insufficient_quota":
            #     self.logger.info(f"Updating api_key_idx to {self.api_key_idx}")
            #     try:
            #         self.update_api_key()
            #     except Exception:
            #         raise
            err_msg = str(e)

        return result, err_msg
