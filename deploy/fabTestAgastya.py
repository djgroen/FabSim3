import numpy as np

@task
def dir_structure(prefix, archive_location):
    """ Cleans results directories of core dumps and moves results to archive locations. """

    if len(prefix)<1:
      print "error: no prefix defined."
      sys.exit()

    print "LOCAL %s %s %s*" % (env.local_results, prefix, archive_location)
    local("rm -f %s/*/core" % (env.local_results))
    local("mv -i %s/%s* %s/" % (env.local_results, prefix, archive_location))


    parent_path = os.sep.join(env.results_path.split(os.sep)[:-1])

    print "REMOTE MOVE: mv %s/%s %s/Backup" % (env.results_path, prefix, parent_path)
    run("mkdir -p %s/Backup" % (parent_path))
    run("mv -i %s/%s* %s/Backup/" % (env.results_path, prefix, parent_path))

