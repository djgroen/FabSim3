# This file contains prototype VVP implementations.
#
# These patterns should be purposed for specific settings.
# As such, they do not contain a @task descriptor.
import os


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
    Authors: Derek Groen and Wouter Edeling
    """

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

        aggregation_function(scores, **kwargs)
