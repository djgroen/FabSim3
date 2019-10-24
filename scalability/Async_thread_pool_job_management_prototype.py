import concurrent.futures

import numpy as np 
import os
import time

from fabric.contrib.project import *
from fabric.api import settings
from fabric.operations import *
from fabric.api import env, run, task

class ClassTimeIt():
    """
        Class Timer, very useful to time some functions or more.
    """
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



# Asynchronous Threads Pool Class
class ATP:
    def __init__(self, ncpu=1):
        self.ncpu = ncpu
        self.job_executor = concurrent.futures.ThreadPoolExecutor(max_workers=self.ncpu)
        self.remote_jobs = {}
        self.jobs_ID = {}
        self.counter = 0
    

    def run_job(self, jobID, handler, counter=False, serial=False, args=(), **kwargs):
        """
        Put a job on a threading queue.
        Args:
            jobID   : string job identifier  
            handler : function that will be executed by the job
            counter : Counter that will be associated with a job and a jobID  ( Could be merged with jobID ...)
            serial  : Serial mode (not implemented yet) 
        """
        fn = self.job_executor.submit(handler, *args, **kwargs)
        self.remote_jobs[jobID] = fn
        #self.remote_jobs[self.counter] = fn
        self.jobs_ID[self.counter] = jobID
        self.counter += 1

    def awaitJobResult(self):
        jobs = []
        jobs_id = []
        
            
    def awaitJobOver(self):
        """
        Wait for all the jobs to be done.            
        """
        #print([self.remote_jobs[jobID] for jobID in range(self.counter)])
        concurrent.futures.wait([self.remote_jobs[jobID] for jobID in range(self.counter)], return_when=concurrent.futures.ALL_COMPLETED)
        print("All threads are over")
        


def fake_sleep_job():
    """
    Small job that wait few second
    """
    print("This is a fake sleep job")
    time.sleep(1)

def fabsim3_job(remote_port='', remote_adress='', remote_path='', filepath='', filename=''):
    """
    Job that simulate FabSim3 behaviour.
    Send files and execute few commands to the local and the remote machine.
    Start to send a ~1MB file 
    Args:
        remote_port     : ssh port of the remote machine (eg. 22)
        remote_adress   : adress of the remote machine (eg. nicolasmonnier@adress.of.my.remote.fr)
        remote_path     : result path of the remote machine (eg. /home/nicolas/FS3_scalability_result)
        filepath        : local path of the file to send (eg. /home/nicolas/file_dir)
        filename        : name of the local file to send (eg. sample_1)
    """

    if not os.path.isfile(os.path.join(filepath, filename)):
        raise OSError('Error, file doesnt exist')

    if remote_adress == '':
        raise OSError('Error: remote machine is not defined')

    

    # Transfert file to the remote
    local(
            "rsync -pthrvz  --rsh='ssh  -p %s  ' %s/%s %s:%s" %(remote_port, filepath, filename, remote_adress, remote_path)
        )
    # TODO 
    # To simulate the behavior of FS3, Remotely create a folder specific of the job, then rsync a bash file, copy bash file & the previous file in the folder, Execute the bash file via slurm

    run(
        'mkdir -p /home_nfs_robin_ib/bmonniern/utils/results/d1 && rsync -av --progress /home_nfs_robin_ib/bmonniern/utils/config /home_nfs_robin_ib/bmonniern/utils/results/d1 --exclude SWEEP && cp /home_nfs_robin_ib/bmonniern/utils/script/fask_script.sh /home_nfs_robin_ib/bmonniern/utils/results/d1'
    )
    run(
        ' cp -r /home_nfs_robin_ib/bmonniern/utils/config/d1/* home_nfs_robin_ib/bmonniern/utils/results/d1/'
    )
    run(
        'sbatch /home_nfs_robin_ib/bmonniern/utils/config/d1/fake_script.sh'
    )




if __name__ == '__main__':
    print("Testing worker management protoype")

    Timer = ClassTimeIt(name="Timer")

    
    # Setting variables 
    nb_samples = 10
    current_path = '/home/nicolas/scalab_dev/FabSim3/scalability' 

    # This directories must be created on the cluster by hand
    remote_path_config = '/home_nfs_robin_ib/bmonniern/utils/config'
    remote_path_results = '/home_nfs_robin_ib/bmonniern/utils/results'
    remote_path_script = '/home_nfs_robin_ib/bmonniern/utils/script'
    remote_adress = 'username@adress.fr'
    remote_port = 2222 

    # setting env.* for fabric remote
    env.hosts = ['%s:%s' %(remote_adress, str(remote_port))] 
    env.host_string = '%s:%s' %(remote_adress,str(remote_port))


    # Creation of the SWEEP dir if not exists
    import os
    if not os.path.exists(os.path.join(current_path, 'SWEEP')):
        os.system('mkdir -p %s' %os.path.join(current_path, 'SWEEP'))
    current_path = os.path.join(current_path, 'SWEEP')

    # Creation (if not exist) of the files and dirs to send to the remote 
    for sample in range(nb_samples):
        dirname = 'd' + str(sample)
        if not os.path.isdir(os.path.join(current_path, dirname)):
            os.system('mkdir -p %s' %os.path.join(current_path, dirname))
        with cd("%s/%s" %(current_path, dirname)):
            filename = 'sample_' + str(sample)
            if not os.path.isfile(os.path.join(current_path, filename)):
                os.system('dd if=/dev/urandom of=%s count=2500' %(os.path.join(current_path,filename)))
    
    for directo in os.listdir(current_path):
        print(directo)


    #####################
    # FabSim3 behaviour #
    #####################
    
    # Like FS3, Start to send all the SWEEP dir to the remote --> This perf depends on rsync mechanisms && internet connexion
    local(
            "rsync -pthrvz  --rsh='ssh  -p %s  ' %s %s:%s" %(remote_port, current_path, remote_adress, remote_path_config)
        )
    

    # Creation of the Worker 
    # ncpu correspond to the number of simultaneous thread you want to set
    atp = ATP(ncpu=1)

    for ite, dire in current_dir:
        filename = 'sample_' + str(sample)
        atp.run_job(jobID=filename, handler=fabsim3_job, args=(str(remote_port), remote_adress, remote_path, current_path, filename))


    print("The jobs are running")
    atp.awaitJobOver() # Wait for all jobs to be done
    
    Timer.timeit()
