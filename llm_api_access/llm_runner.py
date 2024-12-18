import os
import json
import time
import signal
import logging
import argparse
from typing import Callable
from functools import partial
from .arguments import EntireArguments, GenerationArguments
from .llm_requester import LLMRequester
from rich.progress import Progress, TimeElapsedColumn, MofNCompleteColumn
from multiprocessing import Queue
from multiprocessing.pool import ThreadPool


class LLMRunner(object):
    def __init__(
        self,
        arguments: EntireArguments,
        prompt_template: str,
        producer_process_func: Callable,
        consumer_postprocess_func: Callable,
        logger: logging.Logger = None,
        *args,
        **kwargs,
    ):
        self.arguments = arguments
        self.logger = logger

        self.prompt_template = prompt_template
        self.logger.info(f"Prompt Template: {self.prompt_template}")
        self.logger.info(f"Use '{self.arguments.base_url}' as backend.")

        self.producer_process_func = producer_process_func
        self.consumer_postprocess_func = consumer_postprocess_func

        self.gen_kwargs = GenerationArguments.from_args(self.arguments).to_dict()

        self.args = args
        self.kwargs = kwargs

    def dict2namespace(self, config):
        namespace = argparse.Namespace()
        for key, value in config.items():
            if isinstance(value, dict):
                new_value = self.dict2namespace(value)
            else:
                new_value = value
            setattr(namespace, key, new_value)
        return namespace

    def predict_batch(
        self,
        data_queue: Queue,
        queue: Queue,
        *args,
        **kwargs
    ):
        llm_requester = LLMRequester(arguments=self.arguments)
        chat_one_turn_func = partial(llm_requester.chat_one_turn, **self.gen_kwargs)

        while not data_queue.empty():
            try:
                item = data_queue.get(timeout=5)
            except Exception:
                break

            try:
                prompt, response, err_msg = self.producer_process_func(item, self.prompt_template, chat_one_turn_func)
                assert err_msg is None or len(err_msg) == 0, err_msg

                queue.put([item, prompt, response])
            except Exception as e:
                self.logger.error(f"\033[91mProducer: Solving failed because:\n{e}\033[0m\n\nData item: {item}")
                data_queue.put(item)
                time.sleep(2.5)
                continue
        queue.put(signal.SIGTERM)

    def run(
        self,
        data_items: list,
        num_threads: int,
        output_filename: str,
        *args,
        **kwargs
    ):
        queue = Queue()
        producer = Producer(
            task=self.predict_batch,
            queue=queue,
            num_threads=num_threads,
            logger=self.logger,
            *args,
            **kwargs,
        )
        consumer = Consumer(
            queue=queue,
            num_producers=num_threads,
            num_dataitems=len(data_items),
            output_filename=output_filename,
            logger=self.logger,
            postprocess_func=self.consumer_postprocess_func,
            save_as_json=self.arguments.save_as_json,
            *args,
            **kwargs,
        )

        consumer.run()
        producer.run(data=data_items)

        producer.join()
        consumer.join()


class Producer():
    def __init__(self, task, queue: Queue, num_threads: int, logger, *args, **kwargs):
        self.task = task
        self.queue = queue
        self.num_threads = num_threads
        self.logger = logger
        self.args = args
        self.kwargs = kwargs
        self.thread_pool = ThreadPool(processes=self.num_threads)

    def run(self, data: list):
        data_queue = Queue()
        for item in data:
            try:
                data_queue.put(item, timeout=1)
            except Exception:
                self.logger.error("Putting data items to data_queue failed.")
                return

        for thread_idx in range(self.num_threads):
            self.thread_pool.apply_async(
                func=self.task,
                kwds={
                    "data_queue": data_queue,
                    "queue": self.queue,
                    **self.kwargs,
                },
                error_callback=self.error_callback,
            )
        self.thread_pool.close()

    def join(self):
        self.thread_pool.join()

    def error_callback(self, exception):
        self.logger.error(f"Producer failed because: {exception}")
        self.queue.put(signal.SIGTERM)


class Consumer():
    def __init__(
        self,
        queue: Queue,
        num_producers: int,
        num_dataitems: int,
        output_filename: str,
        save_as_json: bool,
        logger,
        *args,
        **kwargs
    ):
        self.queue = queue
        self.num_producers = num_producers
        self.num_dataitems = num_dataitems
        self.output_filename = output_filename
        self.save_as_json = save_as_json
        self.logger = logger

        self.args = args
        self.kwargs = kwargs
        self.thread_pool = ThreadPool(processes=1)

        progress_columns = Progress.get_default_columns() + (TimeElapsedColumn(), MofNCompleteColumn())
        self.progress = Progress(*progress_columns, refresh_per_second=1)

    def run(self):
        self.progress.start()
        self.thread_pool.apply_async(
            func=self.consumer_task,
            kwds={
                "queue": self.queue,
                "progress": self.progress,
                "num_dataitems": self.num_dataitems,
                "num_producers": self.num_producers,
                "output_filename": self.output_filename,
                **self.kwargs
            },
            error_callback=self.error_callback,
        )
        self.thread_pool.close()

    def join(self):
        self.thread_pool.join()
        self.progress.stop()

    def error_callback(self, exception):
        self.logger.error(f"\033[91mConsumer failed because:\n{exception}\033[0m")

    def write_results_to_file(self, data: list, output_filename: str, sort_by_id: bool = False):
        def _sort_by_id(data):
            try:
                _ = int(data[0]['id'])
                is_integer_id = True
            except Exception:
                is_integer_id = False
                pass
            if is_integer_id:
                data = sorted(data, key=lambda x: int(x["id"]))
            else:
                data = sorted(data, key=lambda x: x["id"])
            return data

        if self.save_as_json:
            if os.path.isfile(output_filename):
                with open(output_filename, "r", encoding="utf-8") as fin:
                    existing_data = json.load(fin)
            else:
                existing_data = []
            data = existing_data + data
            if sort_by_id:
                data = _sort_by_id(data)
            with open(output_filename, "w", encoding="utf-8") as fout:
                json.dump(data, fout, ensure_ascii=False, indent=4)
        else:
            if sort_by_id:
                if os.path.isfile(output_filename):
                    with open(output_filename, "r", encoding="utf-8") as fin:
                        existing_data = []
                        for line in fin:
                            existing_data.append(json.loads(line.strip()))
                else:
                    existing_data = []
                data = existing_data + data
                data = _sort_by_id(data)
                with open(output_filename, "w", encoding="utf-8") as fout:
                    for item in data:
                        fout.write(json.dumps(item, ensure_ascii=False) + "\n")
            else:
                # save as jsonl, just append
                with open(output_filename, "a", encoding="utf-8") as fout:
                    for item in data:
                        fout.write(json.dumps(item, ensure_ascii=False) + "\n")

    def consumer_task(
        self,
        queue: Queue,
        progress: Progress,
        num_dataitems: int,
        num_producers: int,
        output_filename: str,
        postprocess_func,
        *args,
        **kwargs
    ):
        task_id = progress.add_task(description="Number of Accomplished Items", total=num_dataitems)
        data_received = 0
        receive_buffer = []
        num_producers_remain = num_producers
        while num_producers_remain > 0:
            while not queue.empty():
                dataitem = queue.get()
                if dataitem == signal.SIGTERM:
                    num_producers_remain -= 1
                    continue
                else:
                    inputs, prompt, response = dataitem
                    try:
                        result = postprocess_func(inputs, response, *args, **prompt, **kwargs)
                    except Exception as e:
                        self.logger.error(f"\033[91mConsumer: postprocessed failed because:\n{e}\033[0m\n\nData item: {inputs}")
                        continue
                    receive_buffer.append(result)
                    data_received += 1
                    self.progress.update(task_id=task_id, advance=1)
            if len(receive_buffer) > 20:
                self.write_results_to_file(data=receive_buffer, output_filename=output_filename)
                receive_buffer = []
            time.sleep(5)
        self.write_results_to_file(data=receive_buffer, output_filename=output_filename, sort_by_id=True)
        receive_buffer = []
