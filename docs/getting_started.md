# Getting Started with FabSim3

This page is for you if...

1. If you have just come across FabSim3 for the first time.
2. You are contemplating whether to use FabSim3 for your project.
3. You are not sure how FabSim3 can be useful for you.
4. You are convinced that FabSim3 is for you but are not sure how to use it.

If you fall into any of these categories, then read on...

## What is FabSim3?

It is a tool that provides one-liners to perform pre-processing, execution and post-processing of computer simulations on personal computers as well as high performance computers (HPCs).

## Who should use FabSim3?

If you have a model which is simulated using any programming language of your choice and wish to perform its detailed analysis, you should probably use FabSim3.

Why so?

This is because, you would most probably have to run the simulation multiple times. Maybe because you want to explore its behahiour across a range of parameters; maybe you wish to account for the stochasticity in your model; perhaps you wish to make predictions using your model for a range of complex scenarios; or perhaps you want to perform VVUQ analysis on the model. Whatever be the reason, if an ensemble of runs has to be prepared, run and analysed, FabSim3 would probably be useful for you.

## How will FabSim3 help you simulate?

FabSim3 essentially seperates the essential running the model from other auxillary tasks such as distinguishing between different parameter sets for the model, organising the results into seperate directories and plotting and analysing the results.

FabSim3 then creates a worklow combining the pre-processing, execution and post-processing steps in the required order and creates a shell script accordingly. The shell script is then executed by FabSim3.

How is the shell script created? Using plugins. FabSim3 has a number of plugins which are essentially python scripts that define the workflow for a particular model. The plugins are written in such a way that they can be easily modified to suit your needs.

Essentially, the plugin is the bridge between your model and FabSim3. It is the plugin that tells FabSim3 how to run your model, how to organise the results and how to analyse the results.

## How to create a plugin?

The easiest way to create a plugin is to use the FabDummy plugin as a template. The FabDummy plugin is a minimal plugin that can be used to run a dummy model. It is a good starting point for creating your own plugin.

The FabDummy plugin showcases all the essential API's that are offered by FabSim3. These include submitting single or multiple jobs to local machines and HPCs, copying files to and from machines, running commands on HPCs, etc.

The plugins are writen in python. If you wish to create a plufin from scratch, you can refer to the API documentation for FabSim3.

## The structure of a FabSim3 one-liner

A typical FabSim3 one-liner has the following structure:

```bash
fabsim <machine> <task>:<arg1>=<value1> <arg2>=<value2> ...
```

The `<machine>` argument is the name of the machine on which the essential parts of the task (computationally intensive tasks such as running a simulation) are to be executed. Once installed, FabSim3 comes with a number of pre-defined machines. You can see the list of pre-defined machines by running the following command:

```bash
fabsim -l machines
```

The `<task>` argument is the name of the python function in a plugin to be executed. The `<arg1>`, `<arg2>`, etc. are the arguments to the task. The `<value1>`, `<value2>`, etc. are the values of the arguments. You can see the list of arguments for a task by running the following command:

```bash
fabsim -l tasks
```

## The essential structure of a plugin

A FabSim3 plugin is essentially a python package that resides in the `FabSim3/plugins` directory. The name of the plugin is the name of the python package. For example, the FabDummy plugin is a python package named `FabDummy`.

Inside the plugin is a main module with the same name as the plugin. For example, the FabDummy plugin has a main module named `FabDummy.py`. This module contains the functions that can be accessed by the user using FabSim3.

As an example, let us take a look one of the fuctions in the `FabDummy.py` module of the FabDummy plugin.

```python
@task
def dummy(config, **args):

    update_environment(args)
    with_config(config)
    execute(put_configs, config)
    job(dict(script='dummy', wall_time='0:15:0', memory='2G'), args)

```

As is evident from the code, the `dummy` function is a normal python function with certain certain FabSim3 specific components. 

### The task decorator

The most essential component of these FabSim3 components is the `@task` decorator which enables the function to be directly called from the command line. If you want any function to be callable from the command line, you need to add the `@task` decorator to it. You can refer to the the [fabric documentation](https://docs.fabfile.org/en/1.12.1/usage/tasks.html#the-task-decorator) for more details on the `@task` decorator.

Due to the `@task` decorator, the `dummy` function can be called from the command line as follows:

```bash
fabsim localhost dummy:config=dummy_test
```


The `dummy` function is the task that is called by the user. The `config` argument of the `dummy` function is the name of the configuration file is passed through the `config=dummy_test` argument. Since `config` is a positional argument, it can be passed without the `config=` prefix as follows:

```bash
fabsim localhost dummy:dummy_test
```

### The env variable

The `env` variable is a dictionary that contains the configuration of the plugin. It is automatically populated by FabSim3. The `env` variable is used to access the configuration of the plugin. For example, the `dummy` function uses the `env.localroot` variable to access the local root directory of the plugin.

Arguments can be added to the `env` variable using the `update_environment` function as shown in the first line of the `dummy` function.

By default, the `env` variable comes pre-populated with keys from the configuration files. For more information on the `env` variable, refer to the documentation of [update_environment()](https://fabsim3.readthedocs.io/en/latest/APIs_for_plugin_developers/#update_environmentargs) function.


### The common FabSim3 API's

Following the function definition, the `dummy` function uses a number of FabSim3 API's to perform the task. These are essentially python functions whose documentation can be found [here](https://fabsim3.readthedocs.io/en/latest/APIs_for_plugin_developers/). Please refer to the documentation to create the workflow for your model.