from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import wait
from concurrent.futures import ALL_COMPLETED
import traceback
import sys
import itertools


class MultiThreadingPool:

    def __init__(self, ncpu=1):
        self.ncpu = ncpu

        self.executor = ThreadPoolExecutor(max_workers=self.ncpu)
        self.thread_tasks = []

    def add_task(self, func, func_args=dict()):
        # Schedule all tasks.
        #   -   We don't want to schedule them all at once, to avoid consuming
        #       excessive amounts of memory.
        try:
            self.thread_tasks.append(
                self.executor.submit(func, (func_args))
            )
        except Exception as exc:
            print(
                '\n{} error_callback from thread {}'
                '\nEXCEPTION TRACE:{}\n{}{}\n'.format(
                    '=' * 30, '=' * 30,
                    type(exc),
                    "".join(traceback.format_tb(exc.__traceback__)),
                    '-' * 90
                )
            )
            self.executor.shutdown()
            sys.exit()

    def wait_for_tasks(self):

        results = []
        print("Waiting for thread tasks to be completed ...")
        # Wait for the future to complete.
        done, _ = wait(self.thread_tasks, return_when=ALL_COMPLETED)

        for finished_task in done:
            try:
                results.append(finished_task.result())
            except Exception as exc:
                print(
                    '\n{} error_callback from thread {}'
                    '\nEXCEPTION TRACE:{}\n{}{}\n'.format(
                        '=' * 30, '=' * 30,
                        type(exc),
                        "".join(traceback.format_tb(exc.__traceback__)),
                        '-' * 90
                    )
                )
                self.executor.shutdown()
                sys.exit()

        print("All thread tasks are finished ...")
        # make thread_tasks empty list
        self.thread_tasks = []

        # Flatten a list of lists
        # source :
        # https://stackoverflow.com/questions/952914/how-to-make-a-flat-list-out-of-list-of-lists
        flatten_results = list(itertools.chain(*results))
        return flatten_results

    def shutdown_threads(self):
        self.executor.shutdown()
