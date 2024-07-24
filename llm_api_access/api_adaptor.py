import os
import time
import requests
from .api_keys import api_keys


class APIAdaptor:
    def __init__(self, model: str, logger, endpoint_name: str = None, endpoint_url: str = None):
        self.model = model
        self.logger = logger
        self.endpoint_name = endpoint_name
        self.endpoint_url = endpoint_url
        self.max_retry_counts = 10
        self.api_key_idx = 0

        self.logger.info(f"Use {endpoint_name} as backend.")
        keys = api_keys[endpoint_name]
        self.url = os.path.join(endpoint_url, "v1/chat/completions")
        self.headers = {
            "Authorization": f"Bearer {keys[0]}",
            "Content-Type": "application/json",
        }
        self.sleep_time = 0.2

    def update_api_key(self):
        self.api_key_idx += 1
        if self.api_key_idx >= len(api_keys[self.endpoint_name]):
            raise RuntimeError("All API_KEY quota exceeded.")
        self.headers = {
            "Authorization": f"Bearer {api_keys[self.endpoint_name][self.api_key_idx]}",
            "Content-Type": "application/json",
        }

    def get_payload(self, prompt, temperature=0.0, max_tokens=1000, n=1, **kwargs):
        if self.model == "gpt-3.5-turbo-instruct":
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_tokens,
                "n": n,
                **kwargs,
            }
        else:
            if "image_url" not in kwargs:
                contents = prompt
            else:
                # add image
                contents = [
                    {"type": "text", "text": prompt},
                    {"type": "image_url", "image_url": kwargs['image_url']},
                ]
            payload = {
                "model": self.model,
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

    def request(self, method, payload):
        return requests.request(
            method=method,
            url=self.url,
            headers=self.headers,
            json=payload,
            timeout=60,
        )

    def chat_one_turn(
        self, prompt, *args, temperature=0.0, max_tokens=1000, n=1, num_tries=0, **kwargs
    ):
        err_msg = ""
        try:
            payload = self.get_payload(
                prompt=prompt, temperature=temperature, max_tokens=max_tokens, n=n, **kwargs,
            )
            response = self.request(method="POST", payload=payload).json()
            # gptgod will return error codes if concurrency is too high
            assert 'error' not in response, f"Response format error: {response}"

            if self.model != "gpt-3.5-turbo-instruct":
                result = [
                    response["choices"][i]["message"]["content"]
                    for i in range(len(response["choices"]))
                ]
                result = "\n\n".join(result)
            else:
                result = [
                    response["choices"][i]["text"] for i in range(len(response["choices"]))
                ]
                result = "\n\n".join(result)

            time.sleep(self.sleep_time)
        except Exception as e:
            print(f"Encountered Error {e}, trying for the {num_tries} time.")
            if response['error']['code'] == "content_policy_violation":
                return None, "content_policy_violation"
            elif response['error']['code'] == "insufficient_quota":
                self.logger.info(f"Updating api_key_idx to {self.api_key_idx}")
                try:
                    self.update_api_key()
                except Exception:
                    raise

                return self.chat_one_turn(
                    prompt,
                    temperature,
                    max_tokens,
                    n,
                    num_tries=num_tries + 1,
                    **kwargs,
                )

            time.sleep(5)
            if num_tries >= self.max_retry_counts:
                raise ConnectionError(f"Retry counts > {self.max_retry_counts}, Abort.")
            else:
                return self.chat_one_turn(
                    prompt,
                    temperature,
                    max_tokens,
                    n,
                    num_tries=num_tries + 1,
                    **kwargs,
                )

        return result, err_msg
