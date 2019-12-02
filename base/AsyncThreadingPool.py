import os
import concurrent.futures
import traceback

# Asynchronous Threads Pool Class


class ATP:
    def __init__(self, ncpu=1):
        self.ncpu = ncpu
        self.job_executor = concurrent.futures.ThreadPoolExecutor(
            max_workers=self.ncpu)
        self.remote_jobs = {}
        self.jobs_ID = {}
        self.counter = 0

    def run_job(self, jobID, handler, counter=False,
                serial=False, args=(), **kwargs):
        """
        Put a job on a threading queue.
        Args:
            jobID   : string job identifier
            handler : function that will be executed by the job
            counter : Counter that will be associated with a 
                      job and a jobID  ( Could be merged with jobID ...)
            serial  : Serial mode (not implemented yet)
        """
        try:
            fn = self.job_executor.submit(handler, *args, **kwargs)
        except Exception as e:
            print("Caught excepetion in worker thread X")
            traceback.print_exc()
        # self.remote_jobs[jobID] = fn
        self.remote_jobs[self.counter] = fn
        self.jobs_ID[self.counter] = jobID
        self.counter += 1

    def awaitJobResult(self):
        jobs = []
        jobs_id = []

    def awaitJobOver(self):
        """
        Wait for all the jobs to be done.
        """
        # print([self.remote_jobs[jobID] for jobID in range(self.counter)])
        concurrent.futures.wait([self.remote_jobs[jobID] for jobID in range(
            self.counter)], return_when=concurrent.futures.ALL_COMPLETED)
        print("All threads are over")
