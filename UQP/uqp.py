# This file contains prototype UQP implementations.
#
# These patterns should be purposed for specific settings.
# As such, they do not contain a @task descriptor.
import os


"""
  UQP 1-aleatoric: aleatoric acyclic coupled UQ

  Runs an initial model, which has an uncertainty caused by 
  probabilistic variability. Each output of the initial model is 
  then analysed, and resulting uncertainties quantified.
"""
def uqp1_aleatoric(model_exec, collation_function, **kwargs):
  pass


"""
  UQP 2-aleatoric: aleatoric acyclic coupled UQ

  Runs an initial model, which has an uncertainty caused by 
  uncertain inputs. Each output of the initial model is 
  then analysed, and resulting uncertainties quantified.
"""
def uqp1_epistemic(input_space, sampling_function, model_exec, collation_function, **kwargs):
  pass


"""
  UQP 2-aleatoric: aleatoric acyclic coupled UQ

  Runs an initial model, which has an uncertainty caused by 
  probabilistic variability. Each output of the initial model is 
  then ported and serves as an input for a second model.

  The translation_function does the porting, and in this case,
  it takes results directly.

  The output of the second model ensemble is then analysed, and
  resulting uncertainties quantified.
"""
def uqp2_aleatoric(model1_exec, translation_function, model2_exec, collation_function, **kwargs):
  pass


"""
  UQP 2-epistemic: epistemic acyclic coupled UQ

  Runs an initial model, which has an uncertainty caused by 
  uncertain inputs. Each output of the initial model is 
  then ported and serves as an input for a second model.

  The translation_function does the porting, and in this case,
  it could take results directly, or perform a resampling.

  The output of the second model ensemble is then analysed, and
  resulting uncertainties quantified.
"""
def uqp2_epistemic(input_space, sampling_function, model1_exec, translation_function, model2_exec, collation_function, **kwargs):
  pass



def ensemble_vvp(results_dirs, sample_testing_function, aggregation_function, **kwargs):
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

    #if a single result_dir is specified, still add it to a list
    if type(results_dirs) == str:
        tmp = []; tmp.append(results_dirs); results_dirs = tmp
        
    for results_dir in results_dirs:    

        scores = []
        
        #use user-specified sample directories if specified, 
        #otherwise look for uq results in all directories in results_dir
        if 'items' in kwargs:
            items = kwargs['items']
        else:
            items = os.listdir("{}".format(results_dir))
        
        for item in items:
            if os.path.isdir(os.path.join(results_dir, item)):
                print(os.path.join(results_dir, item))
                scores.append(sample_testing_function(os.path.join(results_dir, item), **kwargs))
    
        aggregation_function(scores, **kwargs)
