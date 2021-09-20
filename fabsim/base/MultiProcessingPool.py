import itertools
import os
import signal
import sys
import traceback
from multiprocessing import (
    Manager,
    Pool,
    Process,
    cpu_count,
    current_process,
    set_start_method,
)

parent_id = os.getpid()


def start_process(PoolSize):
    """
    the initializer function for multiprocessing Pool
    """
    print(
        "[MultiProcessingPool] Starting Process child "
        ": Name = {} {} , PID = {},  parentPID = {} "
        "Max PoolSize = {} requested PoolSize = {}".format(
            current_process().name,
            Process().name,
            os.getpid(),
            parent_id,
            cpu_count() - 1,
            PoolSize,
        )
    )
    signal.signal(signal.SIGINT, signal.SIG_IGN)


def error_callback(e):
    """
    the error callback function attached to each process to check show the
    error message in case if the process call failed.
    """
    print(
        "{} error_callback from process {}:{} {}"
        "\nEXCEPTION TRACE:{}\n{}\n".format(
            "=" * 10,
            current_process().name,
            Process().name,
            "=" * 10,
            type(e),
            "".join(traceback.format_tb(e.__traceback__)),
        )
    )


class MultiProcessingPool:
    """
    the based Multi Processing Pool Class to be used for lunching FabSim3
    tasks.
    """

    def __init__(self, PoolSize=1):
        try:
            set_start_method("fork")
        except RuntimeError:
            pass
        # to be a little more stable : use one less process maximum
        self.PoolSize = PoolSize if PoolSize < cpu_count() else cpu_count() - 1
        self.Pool = Pool(
            processes=self.PoolSize,
            initializer=start_process,
            initargs=(self.PoolSize,),
        )
        self.Pool_tasks = []

    def add_task(self, func, func_args=dict(), callback_func=None):
        """
        adds the task to create Pool process for execution
        """
        # TODO: it would be better to collect the output results of
        #     each task within a callback function, instead of
        #     iterating over the Pool_tasks
        try:
            self.Pool_tasks.append(
                self.Pool.apply_async(
                    func=func,
                    args=(func_args,),
                    callback=callback_func,
                    error_callback=error_callback,
                )
            )
        except Exception as e:
            self.Pool.close()
            self.Pool.terminate()
            self.Pool.join()
            error_callback(e)
            sys.exit(1)

    def wait_for_tasks(self):
        """
        wait until all tasks in the Pool are finished, then collect the output
        tasks and return the outputs
        """
        results = []
        print("Waiting for tasks to be completed ...")
        # tells the pool not to accept any new job
        self.Pool.close()
        # tells the pool to wait until all jobs finished then exit,
        # effectively cleaning up the pool
        self.Pool.join()

        print("All tasks are finished ...")

        results = [task.get() for task in self.Pool_tasks]

        # make Pool_tasks empty list
        self.Pool_tasks = []

        # Flatten a list of lists
        # source :
        # https://stackoverflow.com/questions/952914/how-to-make-a-flat-list-out-of-list-of-lists
        flatten_results = list(itertools.chain(*results))
        return flatten_results


"""
####################################################################################################################
Among all 6 different kinds of pools and both workload types,
the multiprocessing process pool is the overall winner.
https://github.com/JohnStarich/python-pool-performance/tree/5a8428ca95240932e0b1b0d7064bf8020e0b1f2e#overall-ranks
####################################################################################################################

Pool class:
1- Synchronous execution :
                          A synchronous execution is one the processes are
                          completed in the same order in which it was started.
                          This is achieved by locking the main program until
                          the respective processes are finished

       > Pool.map() and Pool.starmap()
       > Pool.apply()

1- Asynchronous execution :
                         Asynchronous, on the other hand, doesn’t involve
                         locking. As a result, the order of results can get
                         mixed up but usually gets done quicker.

       > Pool.map_async() and Pool.starmap_async()
       > Pool.apply_async()

-------------------------------------------------------------------------
                  | Multi-args   Concurrence    Blocking  Ordered-results
-------------------------------------------------------------------------
Pool.map          | no           yes            yes          yes
Pool.map_async    | no           yes            no           yes
Pool.apply        | yes          no             yes          no
Pool.apply_async  | yes          yes            no           no
Pool.starmap      | yes          yes            yes          yes
Pool.starmap_async| yes          yes            no           no
-------------------------------------------------------------------------


"""
