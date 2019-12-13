.. _fabsim3qcg:

FabSim3: Remote job management command
======================================
This document explains how users should set and use remote machine functionality.

.. note:: In this tutorial, all parameters are set based on our tested target machine  (the Eagle cluster at PSNC), which uses `QCG Middleware <http://apps.man.poznan.pl/trac/qcg>`_ for resource management. For the local testing, you need to change them based your remote machine configuration and usage software.

Machine configuration
---------------------
To execute jobs through remote resource schedulers, some **essential** machine-specific configurations are required to be set and stored. These parameters will be applied to all applications run on that remote machine. 

First, you need to add your **username** for remote machine in ``/deploy/machines_user.yml`` file as::

    qcg: # machine name
         username: "plg..." 

Then, set up configuration for remote machine in ``/deploy/machines.yml`` file. Here is a simple example::

    qcg: # machine name
         remote: 'eagle.man.poznan.pl'
         home_path_template: '/home/plgrid/$username'
         manual_ssh: true
         dispatch_jobs_on_localhost: true
         job_dispatch : 'qcg-sub'
         batch_header: qcg-eagle
         stat: 'qcg-list -Q -s all -F "%-22I %-16S %-8H" | awk "{if(NR>2)print}"'
         job_dispatch: 'qcg-sub'
         cancel_job_command: 'qcg-cancel $jobID'
         job_info_command : 'qcg-info -Q $jobID'

* ``qcg``: the name of target remote machine machine , it will use by FabSim3 as ``fab qcg <command>``. Internally, FabSim3 uses ``<$user_name>@<$remote>`` to connect to the remote machine.
* ``remote``: the remote machine address. FabSim3 uses ``<$user_name>@<$remote>`` template internally all connection. The ``user_name`` parameter is taken from ``/deploy/machines.yml`` file.

* ``home_path_template``: used to the storage space to checkout and build on the remote machine.

* ``manual_ssh``: when enabled, FabSim3 will connect directly using an ssh client instead of using the paramiko api.

* ``dispatch_jobs_on_localhost``: if it is set to **true**, job dispatch is done locally. Otherwise, FabSim3 executes commands directly inside the remote machine by **ssh** connection. To dispatch job locally, the command-line interface for job management should be installed in your local machine.

* ``batch_header``: it can be used to add some predefined templates to the submitted job script. The template file should be store at ``/deploy/templates``.

* ``stat``: filled by the command-line that displays report on the submitted jobs. In this example, according to our grid broker, ``qcg-list`` command displays table with information about tasks. 

It should be set in the way that only return jobID, job status, and host in the output (without column header). For example, the template output should be similar to::

      =======   =========   ===========
      jobID1    FINISHED    eagle
      jobID2    FAILED      tryton
      jobID3    CANCELED    prometheus  
      =======   =========   ===========

* ``job_dispatch``: the command to submit the task to be processed by remote machine.

* ``cancel_job_command``: the command to cancel the submitted task based on input **$jobID**. the **$jobID** variable will be set during the execution, keep the format as **$jobID** in the parameters list.

* ``job_info_command``: the command to display a comprehensive information of a specific **jobID**. Please set this parameters based on the workload manager of target remote machine, i.e : ``<command> <parameters> $jobID``. The **$jobID** variable will be set during the execution, keep the format as **$jobID** in the parameters list.

Job Executing, Monitoring, and Fetching results on a remote host
----------------------------------------------------------------
Job Submisson 
~~~~~~~~~~~~~
* To submit a job on the remote mahcine, type::

    fab <machine name> install_plugin:<plug_name>
    
This does the following: 
* Copy your job input to the remote machine location specified in the variable. 
* By each job submssion, the associated jobID will be stored in the jobs database in ``/deploy/.jobsDB``  at your local machine.

Job Monitoring
~~~~~~~~~~~~~~
* ``job_stat``: returns a report for all submitted jobs or a one in Particular. By default ``fab <machine> job_stat`` reports the status of jobs saved in the local jobs database. 

    $ fab <machine> job_stat
    
      ======================   ================     ===========
      JobID                    Job Status           Host
      ----------------------   ----------------     -----------
      J1550579738985__5903     FINISHED             eagle
      J1550579822765__3295     FAILED               eagle
      J1551348984148__7461     CANCELED             eagle
      ======================   ================     ===========

To return task information for all submitted jobs, you can use ``fab <machine> job_stat:period=all``. Also, to return the status for a specific task, type::

    fab <machine> job_stat:jobID=...

* ``job_stat_update``: updates the job status in the local database file

    $ fab <machine> job_stat_update

      ======================   ================     ================
      JobID                    current Status       New Status
      ----------------------   ----------------     ----------------
      J1550579738985__5925     FAILED               --
      J1550579822765__9151     PREPROCESSING        PENDING
      J1551348984148__8504     PENDING              FINISHED
      ======================   ================     ================

 * ``job_info``: returns an extened reports on for a specefic job, ``fab <machine> job_info:<jobID>``
 * ``cancel_job``: will cancel a remote job, ``fab <machine> cancel_job:<jobID>``
   
Fetaching results
~~~~~~~~~~~~~~~~~
* You can fetch the remote data using 
    
    fab <machine> fetch_results
