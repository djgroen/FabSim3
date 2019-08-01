# This file contains prototype VVP implementations.
#
# These patterns should be purposed for specific settings.
# As such, they do not contain a @task descriptor.
import os


"""
validate_ensemble_output Validation Pattern.

Purpose: 
1. given an ensemble of validation output directories, it will:
2. operate a validation_function on each direction, and
3. print the outputs to screen, and
4. use an aggregation function to combine all outputs into a compound metric, 
   and
5. print the compound metric.


SPECS of the required validation_function:
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

def validate_ensemble_output(results_dir, validation_function, aggregation_function):
    """
    Goes through all the output directories and calculates the validation
    scores.
    """

    validation_scores = []
    for item in os.listdir("{}/RUNS".format(results_dir)):
        print(item)
        if os.path.isdir(os.path.join(results_dir, "RUNS", item)):
            print(os.path.join(results_dir, "RUNS", item))
            validation_scores.append(validation_function(os.path.join(results_dir, "RUNS", item)))

    print("scores:", validation_scores)
    print("AVERAGED VALIDATION SCORE: {}".format(aggregation_function(validation_scores)))


