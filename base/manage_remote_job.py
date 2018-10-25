from deploy.templates import *
from deploy.machines import *
from fabric.contrib.project import *
import time

@task
def stat():
    """Check the remote message queue status"""
    #TODO: Respect varying remote machine queue systems.
    if not env.get('stat_postfix'):
        return run(template("$stat -u $username"))
    return run(template("$stat -u $username $stat_postfix"))

@task
def monitor():
    """Report on the queue status, ctrl-C to interrupt"""
    while True:
        execute(stat)
        time.sleep(120)


def check_complete():
  """Return true if the user has no queued jobs"""
  return stat()==""

@task
def wait_complete():
  """Wait until all jobs currently qsubbed are complete, then return"""
  # time.sleep(120)
  while not check_complete():
        time.sleep(120)
