import concurrent.futures

import numpy as np 
import os
import time

from fabric.contrib.project import *
from fabric.api import settings
from fabric.operations import *

class ClassTimeIt():
    def __init__(self, name=""):
        self.t0 = time.time()
        self.IsEnable = True
        if name == "":
            self.name = name
        else:
            self.name = name + ": "
        self.IsEnableIncr = False
        self.Counter = ""

    def reinit(self):
        self.t0 = time.time()

    def timestr(self, hms=False):
        t1 = time.time()
        dt = t1 - self.t0
        self.t0 = t1
        return "%7.5f" %dt


    def timeit(self, stri= " Time", hms = False):
        ts = self.timestr(hms=hms)
        Sout = " * %s%s %s : %s" %(self.name, stri, str(self.Counter), ts)
        print(Sout)




class ATP:
    def __init__(self, ncpu=1):
        self.ncpu = ncpu
        self.job_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.ncpu)
        self.remote_jobs = {}
    

    def run_job(self, jobID, handler, counter=False, serial=False, args=(), **kwargs):
        fn = self.job_executor.submit(handler, *args, **kwargs)
        self.remote_jobs[jobID] = fn  

    def awaitJobResult(self):
        jobs = []
        jobs_id = []


def fake_sleep_job():
    print("This is a fake sleep job")
    time.sleep(1)

def rsync_job(remote_adress='', remote_path='', filepath='', filename=''):
    if not os.path.isfile(os.path.join(filepath, filename)):
        raise OSError('Error, file doesnt exist')

    if remote_adress == '':
        raise OSError('Error: remote machine is not defined')

    # Transfert file to the remote
    local(
            "rsync -pthrvz  --rsh='ssh  -p 8522  ' %s/%s %s%s" %(filepath, filename, remote_adress, remote_path)
        )


if __name__ == '__main__':
    print("Testing worker management protoype")

    nb_samples = 10
    current_path = '/home/nicolas/scalab_dev/FabSim3/scalability' 
    remote_result_path = '/home_nfs_robin_ib/bmonniern/utils/'
    remote_adress = 'bmonniern@castle.frec.bull.fr:'
   
    local( "ls") 

    #rsync_job(remote_adress = remote_adress, remote_path=remote_result_path, filepath=current_path, filename='sample_1')
    # Creation (if not exist) of the files to send to the remote 
    for sample in range(nb_samples):
        filename = 'sample_' + str(sample)
        if not os.path.isfile(os.path.join(current_path, filename)):
            os.system('dd if=/dev/urandom of=%s count=2500' %(os.path.join(current_path,filename)))
            #f = open(os.path.join(current_path, filename), 'w')
            #f.write("Im the sample number %d"%sample)            
            #f.close()
    

    # Creation of the Worker 
    atp = ATP(ncpu=6)
    for it in range(6):
        print("Worker nb %d"%it)
        atp.run_job(jobID=1, handler=fake_sleep_job)


    print("The jobs are running")

#rsync ./cycler-0.10.0.tar.gz  bmonniern@castle.frec.bull.fr:9922:/home_nfs_robin_ib/bmonniern/utils/
