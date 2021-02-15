# This file contains prototype VVP implementations.
#
# These patterns should be purposed for specific settings.
# As such, they do not contain a @task descriptor.
import os
from collections import OrderedDict
from pprint import pprint

"""
validate_ensemble_output Validation Pattern.

Purpose:
1. given an ensemble of validation/verification output directories, it will:
2. operate a sample  testing function on each directory, and
3. print the outputs to screen, and
4. use an aggregation function to combine all outputs into a compound metric.
        (printing needs to be done within the testing and
        aggregation functions themselves).


SPECS of the required sample_testing_function:
- Should operate with a single argument (the simulation output directory).
- ASSUMPTION: There is no explicit argument to indicate where the validation
  data resides (currently assumed to be packaged with the simulation output
  and known by the function). -> we could choose to make this explicit.
- The validation function should return a set of metrics.

SPECS of the aggregation_function:
- Receives a Python list with the output of validation_function in each
  element.
- Returns a data type that represents the compound validation outcome
  (.e.g, one or more error scores).
"""


def ensemble_vvp_LoR(results_dirs_PATH, load_QoIs_function,
                     aggregation_function,
                     **kwargs):
    """

    Arguments:
    ----------
    - results_dirs_PATH:
            list of result dirs, one directory for each resolution and
            each one containing the same QoIs stored to disk
    - load_QoIs_function:
            a function which loads the QoIs from each subdirectory of
            the results_dirs_PATH.
    - aggregation_function:
            function to combine all results
    - **kwargs:
            custom parameters. The 'items' parameter must be used to give
            explicit ordering of the various subdirectories, indicating
            the order of the refinement.

    NOTE:
        - to see how  input functions should be defined for your app, please
        look at the implemented examples in FabFlee repo

    Author: Hamid Arabnejad
    """

    results_dirs = [dirname for dirname in os.listdir(results_dirs_PATH)
                    if os.path.isdir(os.path.join(results_dirs_PATH, dirname))]
    if len(results_dirs) == 0:
        raise ValueError('\nThere is not subdirectories in the passed '
                         'results_dirs_PATH arguments.'
                         '\nresults_dirs_PATH = %s' % (results_dirs_PATH))

    #########################################################
    # the scores dict has this structure:                   #
    # result_dir_1_name:                                    #
    #       order: <polynomial_order>                       #
    #       runs: <num_runs>                                #
    #       value:                                          #
    #             vary_param_1: {<sobol_func_name>:<value>} #
    #             ...                                       #
    #             vary_param_X: {<sobol_func_name>:<value>} #
    # ...                                                   #
    # result_dir_N_name:                                    #
    #       order: <polynomial_order>                       #
    #       runs: <num_runs>                                #
    #       value:                                          #
    #             vary_param_1: {<sobol_func_name>:<value>} #
    #             ...                                       #
    #             vary_param_X: {<sobol_func_name>:<value>} #
    #########################################################
    scores = {}
    for result_dir in results_dirs:
        value, order, num_runs = load_QoIs_function(
            os.path.join(results_dirs_PATH, result_dir))
        scores.update({
            result_dir: {
                'value': value,
                'runs': num_runs,
                'order': order
            }
        })

    #################################################################
    # sort scores dict based on order value in ascending            #
    # i.e., the last key in scores will have the higher order value #
    # to have Descending order, set reverse=True                    #
    #################################################################
    scores = dict(OrderedDict(sorted(scores.items(),
                                     key=lambda x: x[1]['order'],
                                     reverse=False)
                              ))
    ###########################################################
    # call aggregation_function to compares the sobol indices #
    ###########################################################
    aggregation_function(scores, **kwargs)


def ensemble_vvp(results_dirs, sample_testing_function,
                 aggregation_function, **kwargs):
    """
    Goes through all the output directories and calculates the scores.
    Arguments:
    - results_dirs: list of result dirs to analyse.
    - sample_testing_function: analysis/validation/verification function to be
    performed on each subdirectory of the results_dirs.
    - aggregation_function: function to combine all results
    - **kwargs: custom parameters. The 'items' parameter can be used to give
    explicit ordering of the various subdirectories.

    return : ensemble_vvp_results (dict)      

    Authors: Derek Groen, Wouter Edeling, and Hamid Arabnejad
    """

    ensemble_vvp_results = {}

    # if a single result_dir is specified, still add it to a list
    if type(results_dirs) == str:
        tmp = []
        tmp.append(results_dirs)
        results_dirs = tmp

    for results_dir in results_dirs:

        scores = []

        # use user-specified sample directories if specified,
        # otherwise look for uq results in all directories in results_dir
        if 'items' in kwargs:
            items = kwargs['items']
        else:
            items = os.listdir("{}".format(results_dir))

        for item in items:
            if os.path.isdir(os.path.join(results_dir, item)):
                print(os.path.join(results_dir, item))
                scores.append(sample_testing_function(
                    os.path.join(results_dir, item), **kwargs))

        scores_aggregation = aggregation_function(scores, **kwargs)

        # update return results dict
        ensemble_vvp_results.update({results_dir: {}})

        ensemble_vvp_results[results_dir].update({
            'scores': scores,
            'scores_aggregation': scores_aggregation
        })

    return ensemble_vvp_results
