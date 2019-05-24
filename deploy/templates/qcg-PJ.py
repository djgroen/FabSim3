import zmq

from qcg.appscheduler.api.manager import Manager
from qcg.appscheduler.api.job import Jobs

# switch on debugging (by default in api.log file)
m = Manager(cfg={'log_level': 'DEBUG'})

# get available resources
print("available resources:\n%s\n" % str(m.resources()))


# submit jobs and save their names in 'ids' list
$submitted_jobs_list

# list submited jobs
print("submited jobs:\n%s\n" % str(m.list()))


# wait until all submited jobs finish
# m.wait4all()
