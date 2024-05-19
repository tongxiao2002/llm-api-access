import time
import requests
from api_keys import api_keys


class APIAdaptor:
    """Support OhMyGPT & GPTGod
    """
    def __init__(self, model: str, logger):
        self.model = model
        self.logger = logger
        self.max_retry_counts = 20
        if self.model.startswith('gpt'):
            # OhMyGPT
            self.logger.info("Use OhMyGPT as backend.")
            if self.model == "gpt-3.5-turbo-instruct":
                self.url = "https://cn2us02.opapi.win/v1/completions"
            else:
                self.url = "https://cn2us02.opapi.win/v1/chat/completions"
            self.headers = {
                "User-Agent": "Apifox/1.0.0 (https://apifox.com)",
                "Authorization": f"Bearer {api_keys['ohmygpt'][0]}",
            }
            self.sleep_time = 0.2
        else:
            # GPTGod
            self.logger.info("Use GPTGod as backend.")
            self.url = "https://api.gptgod.online/v1/chat/completions"
            self.headers = {
                "Authorization": f"Bearer {api_keys['gptgod'][0]}",
                "Content-Type": "application/json",
            }
            if self.model.startswith("mistral"):
                self.sleep_time = 60
            elif self.model.startswith("claude"):
                self.sleep_time = 3
            else:
                # gemini-pro
                self.sleep_time = 5

    def get_payload(self, prompt, temperature=0.0, max_token=1000, n=1, **kwargs):
        if self.model == "gpt-3.5-turbo-instruct":
            payload = {
                "model": self.model,
                "prompt": prompt,
                "temperature": temperature,
                "max_tokens": max_token,
                "n": n,
                **kwargs,
            }
        else:
            payload = {
                "model": self.model,
                "messages": [
                    {"role": "system", "content": "You are a helpful asistant."},
                    {"role": "user", "content": prompt},
                ],
                "temperature": temperature,
                "max_tokens": max_token,
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
        self, prompt, *args, temperature=0.0, max_token=1000, n=1, num_tries=0, **kwargs
    ):
        try:
            payload = self.get_payload(
                prompt=prompt, temperature=temperature, max_token=max_token, n=n, **kwargs,
            )
            response = self.request(method="POST", payload=payload).json()
            # gptgod will return error codes if concurrency is too high
            assert 'code' not in response
            time.sleep(self.sleep_time)
        except Exception as e:
            print(f"Encountered Error {e}, trying for the {num_tries} time.")
            if self.model.startswith("mistral"):
                time.sleep(self.sleep_time)
            else:
                time.sleep(5)
            if num_tries >= self.max_retry_counts:
                raise ConnectionError(f"Retry counts > {self.max_retry_counts}, Abort.")
            else:
                return self.chat_one_turn(
                    prompt,
                    temperature,
                    max_token,
                    n,
                    num_tries=num_tries + 1,
                    **kwargs,
                )
        if self.model != "gpt-3.5-turbo-instruct":
            result = [
                response["choices"][i]["message"]["content"]
                for i in range(len(response["choices"]))
            ]
            result = "\n\n".join(result)
            tokens = None
        else:
            result = [
                response["choices"][i]["text"] for i in range(len(response["choices"]))
            ]
            result = "\n\n".join(result)
            tokens = response["usage"]["completion_tokens"]
        return result, tokens
