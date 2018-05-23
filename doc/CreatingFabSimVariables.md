# FabSim variables.

### Representing FabSim variables

FabSim variables are represented in three different ways:

* in .yml files as a key-value pair, e.g.
```
number_of_cores: 16
```

* within the FabSim Python environment as a member of the env dictionary, e.g.:
```
env.number_of_cores = 16
```
or
```
update_environment({"number_of_cores":16})
```

* within templates as a $ denominated variable, which is to be substituted. For example:
```
$number_of_cores
```
### How variables are obtained or introduced:

Variable are obtained from the following sources:
1. Parsed from .yml files such as machines.yml and machines_user.yml, which are loaded on startup.
2. Explicitly written/created in the Python code environment. This should be implemented such that the third method will still override this method.
3. Overridden or introduced using command-line arguments.

### How variables are applied:
1. Directly, by reading values from env.<variable_name> in the Python code base.
2. Through template substitution, where instances of $<variable_name> are replaced with <variable_value> in the substitution output.

#### Example of applying a variable 

```
@task
def test_sim(config,**args):
    """
    Submit a my_sim job to the remote queue.
    """
    
    env.test_var = 300.0 # test variable is set to a default value in the FabSim environment. 
    # This will override any defaults set in other parts of FabSim (e.g. machines_user.yml)

    update_environment(args) 
    # If a value for test_var is given as a command-line argument, then the default set above will be overridden.

    env.sim_args = "-test-var=%s" % (env.test_var) 
    # Optional example how to use your created variable to create some parameter syntax for your job.

    test_sim(config, **args) # start a fictitious job, with the variable present in your FabSim environment.
```
