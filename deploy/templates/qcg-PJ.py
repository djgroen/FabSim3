from qcg.appscheduler.api.manager import Manager
from qcg.appscheduler.api.job import Jobs
from qcg.appscheduler.api.manager import LocalManager

m = LocalManager(cfg={'log_level': 'DEBUG'}, server_args=['--log', 'debug'])
# m = Manager(cfg={'log_level': 'DEBUG'}, server_args=['--log', 'debug'])

# get available resources
print("available resources:\n%s\n" % str(m.resources()))


# submit jobs and save their names in 'ids' list
ids = m.submit(Jobs().$submitted_jobs_list)


# wait until submited jobs finish
m.wait4(ids)

# get detailed information about submited and finished jobs
print("jobs details:\n%s\n" % str(m.info(ids)))

# m.finish()
# m.stopManager()
# m.cleanup()
