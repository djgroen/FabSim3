# This file contains prototype VVP implementations.
#
# These patterns should be purposed for specific settings.
# As such, they do not contain a @task descriptor.
import os
from collections import OrderedDict
from pprint import pprint

import numpy as np

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


def ensemble_vvp_QoI(simulation_result_QoI, uncertainty_result_QoI, QoI_name):
    """

    The current supported similarity measure are:

    * Jensen-Shannon divergence
    * Renyi divergence
    * Cosine distance
    * Euclidean distance
    * Kullback-Leibler divergence

    Args:
        simulation_result_QoI : Experimental QoI data.
        uncertainty_result_QoI : uncertainty QoI results
        QoI_name : the name of QoI


    Returns:
        dic : returns a dictionary with the following structure:
        ```json
        {
            "similarity measure function name":
            {
                "QoI_name" : [similarity_measure_function_result]
            }
        }
        ```



    Author: Hamid Arabnejad
    """
    simulation_result_QoI = np.array(simulation_result_QoI)
    uncertainty_result_QoI = np.array(uncertainty_result_QoI)

    if simulation_result_QoI.shape != uncertainty_result_QoI.shape:
        raise RuntimeError("The dimension of two input array are not equal !")

    if simulation_result_QoI.ndim == 1:
        simulation_result_QoI = np.array([simulation_result_QoI])
    if uncertainty_result_QoI.ndim == 1:
        uncertainty_result_QoI = np.array([uncertainty_result_QoI])

    similarity_measure_results = {}

    for simulation_result, uncertainty_result in zip(
        simulation_result_QoI, uncertainty_result_QoI
    ):
        # calculate Jensen-Shannon Divergence
        measure_name = "Jensen-Shannon Divergence"
        if measure_name not in similarity_measure_results:
            similarity_measure_results.update({measure_name: {}})
            similarity_measure_results[measure_name].update({QoI_name: []})

        res = jensen_shannon_divergence(simulation_result, uncertainty_result)
        similarity_measure_results[measure_name][QoI_name].append(res)

        # calculate Cosine Similarity
        measure_name = "Cosine similarity"
        if measure_name not in similarity_measure_results:
            similarity_measure_results.update({measure_name: {}})
            similarity_measure_results[measure_name].update({QoI_name: []})
        res = cosine_similarity(simulation_result, uncertainty_result)
        similarity_measure_results[measure_name][QoI_name].append(res)

        # calculate KL divergence
        measure_name = "KL divergence"
        if measure_name not in similarity_measure_results:
            similarity_measure_results.update({measure_name: {}})
            similarity_measure_results[measure_name].update({QoI_name: []})
        res = kl_divergence(simulation_result, uncertainty_result)
        similarity_measure_results[measure_name][QoI_name].append(res)

        # calculate Renyi Divergence
        measure_name = "Renyi Divergence"
        if measure_name not in similarity_measure_results:
            similarity_measure_results.update({measure_name: {}})
            similarity_measure_results[measure_name].update({QoI_name: []})
        res = renyi_divergence(simulation_result, uncertainty_result)
        similarity_measure_results[measure_name][QoI_name].append(res)

        # calculate Euclidean Distance
        measure_name = "Euclidean Distance"
        if measure_name not in similarity_measure_results:
            similarity_measure_results.update({measure_name: {}})
            similarity_measure_results[measure_name].update({QoI_name: []})
        res = euclidean_distance(simulation_result, uncertainty_result)
        similarity_measure_results[measure_name][QoI_name].append(res)

    return similarity_measure_results


def ensemble_vvp_LoR(
    results_dirs_PATH, load_QoIs_function, aggregation_function, **kwargs
):
    """

    Arguments:
    ----------
    - `results_dirs_PATH`:
            list of result dirs, one directory for each resolution and
            each one containing the same QoIs stored to disk
    - `load_QoIs_function`:
            a function which loads the QoIs from each subdirectory of
            the results_dirs_PATH.
    - `aggregation_function`:
            function to combine all results
    - `**kwargs`:
            custom parameters. The 'items' parameter must be used to give
            explicit ordering of the various subdirectories, indicating
            the order of the refinement.

    Returns:
        dic: returns the results score in `dic` format.

        The scores dict has this structure
        ```python
        result_dir_1_name:
            order: <polynomial_order>
            runs: <num_runs>
            value:
                vary_param_1: {<sobol_func_name>:<value>}
                ...
                vary_param_X: {<sobol_func_name>:<value>}
        ...
        result_dir_N_name:
              order: <polynomial_order>
              runs: <num_runs>
              value:
                    vary_param_1: {<sobol_func_name>:<value>}
                    ...
                    vary_param_X: {<sobol_func_name>:<value>}
        ```

    !!! tip
        - to see how  input functions should be defined for your app, please
        look at the implemented examples in [FabFlee repo]
        (https://github.com/djgroen/FabFlee/blob/master/VVP/flee_vvp.py#L752)

    Author: Hamid Arabnejad
    """

    results_dirs = [
        dirname
        for dirname in os.listdir(results_dirs_PATH)
        if os.path.isdir(os.path.join(results_dirs_PATH, dirname))
    ]
    if len(results_dirs) == 0:
        raise ValueError(
            "\nThere is not subdirectories in the passed "
            "results_dirs_PATH arguments."
            "\nresults_dirs_PATH = %s" % (results_dirs_PATH)
        )

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
            os.path.join(results_dirs_PATH, result_dir)
        )
        scores.update(
            {result_dir: {"value": value, "runs": num_runs, "order": order}}
        )

    #################################################################
    # sort scores dict based on order value in ascending            #
    # i.e., the last key in scores will have the higher order value #
    # to have Descending order, set reverse=True                    #
    #################################################################
    scores = dict(
        OrderedDict(
            sorted(scores.items(), key=lambda x: x[1]["order"], reverse=False)
        )
    )
    ###########################################################
    # call aggregation_function to compares the sobol indices #
    ###########################################################
    aggregation_function(scores, **kwargs)


def ensemble_vvp(
    results_dirs, sample_testing_function, aggregation_function, **kwargs
):
    """
    Goes through all the output directories and calculates the scores.
    Arguments:
    - `results_dirs`: list of result dirs to analyse.
    - `sample_testing_function`: analysis/validation/verification function to
        be performed on each subdirectory of the results_dirs.
    - `aggregation_function`: function to combine all results
    - `**kwargs` : custom parameters. The `items` parameter can be used to
        give explicit ordering of the various subdirectories.

    Returns:
        dict: ensemble_vvp_results

    Authors: Derek Groen, Wouter Edeling, and Hamid Arabnejad
    """

    ensemble_vvp_results = {}

    # if a single result_dir is specified, still add it to a list
    if isinstance(results_dirs, str):
        tmp = []
        tmp.append(results_dirs)
        results_dirs = tmp

    for results_dir in results_dirs:
        names = []
        scores = []

        # use user-specified sample directories if specified,
        # otherwise look for uq results in all directories in results_dir
        if "items" in kwargs:
            items = kwargs["items"]
        else:
            items = os.listdir("{}".format(results_dir))

        for item in items:
            if os.path.isdir(os.path.join(results_dir, item)):
                print(os.path.join(results_dir, item))
                names.append(item)
                scores.append(
                    sample_testing_function(
                        os.path.join(results_dir, item), **kwargs
                    )
                )

        scores_aggregation = aggregation_function(scores, **kwargs)

        # update return results dict
        ensemble_vvp_results.update({results_dir: {}})

        ensemble_vvp_results[results_dir].update(
            {"names": names, "scores": scores,
                "scores_aggregation": scores_aggregation}
        )

    # print(ensemble_vvp_results)
    return ensemble_vvp_results


def jensen_shannon_divergence(list1, list2):
    """Calculates Jenson-Shannon Distance"""
    import scipy

    # convert the vectors into numpy arrays in case that they aren't
    list1 = np.array(list1)
    list2 = np.array(list2)
    # calculate average
    avg_lists = (list1 + list2) / 2
    # compute Jensen Shannon Divergence
    sim = 1 - 0.5 * (
        scipy.stats.entropy(list1, avg_lists)
        + scipy.stats.entropy(list2, avg_lists)
    )
    if np.isinf(sim):
        # the similarity is -inf if no term in the document is in the
        # vocabulary
        return 0
    return sim


def cosine_similarity(list1, list2):
    """Calculates cosine similarity."""
    import scipy

    if list1 is None or list2 is None:
        return 0
    assert not (np.isnan(list2).any() or np.isinf(list2).any())
    assert not (np.isnan(list1).any() or np.isinf(list1).any())
    sim = 1 - scipy.spatial.distance.cosine(list1, list2)
    if np.isnan(sim):
        # the similarity is nan if no term in the document is in the vocabulary
        return 0
    return sim


def kl_divergence(list1, list2):
    """Calculates Kullback-Leibler divergence."""
    import scipy

    sim = scipy.stats.entropy(list1, list2)
    return sim


def renyi_divergence(list1, list2, alpha=0.99):
    """Calculates Renyi divergence."""
    log_sum = np.sum(
        [
            np.power(p, alpha) / np.power(q, alpha - 1)
            for (p, q) in zip(list1, list2)
        ]
    )
    sim = 1 / (alpha - 1) * np.log(log_sum)
    if np.isinf(sim):
        # the similarity is -inf if no term in the document is in the
        # vocabulary
        return 0
    return sim


def euclidean_distance(list1, list2):
    """Calculates Euclidean distance."""
    sim = np.sqrt(np.sum([np.power(p - q, 2) for (p, q) in zip(list1, list2)]))
    return sim


# VVP 1


def sif_vvp(
    results_dirs,
    sif_dirs,
    sample_testing_function,
    aggregation_function,
    **kwargs
):
    """
    Goes through all the output directories and calculates the scores.
    Arguments:
    - results_dirs: list of result dirs to analyse.
    - sample_testing_function: analysis/validation/verification function to be
    performed on each subdirectory of the results_dirs.
    - aggregation_function: function to combine all results
    - **kwargs: custom parameters. The 'items' parameter can be used to give
    explicit ordering of the various subdirectories.

    return : sif_vvp_results (dict)

    Authors: Derek Groen, Wouter Edeling, and Hamid Arabnejad
    """

    sif_vvp_results = {}

    # if a single result_dir is specified, still add it to a list
    if isinstance(results_dirs, str):
        tmp = []
        tmp.append(results_dirs)
        results_dirs = tmp

    # if a single sif_dir is specified, still add it to a list
    if isinstance(sif_dirs, str):
        tmp = []
        tmp.append(sif_dirs)
        sif_dirs = tmp

    print("SIF_VVP results dirs:", results_dirs, sif_dirs)
    if (len(results_dirs)) == 0:
        print("ERROR: SIF_VVP applied,")
        print("but no results directories of test_subject runs provided.")
        sys.exit()

    for i in range(0, len(results_dirs)):
        ri = results_dirs[i]
        si = sif_dirs[0]

        scores = []

        # use user-specified sample directories if specified,
        # otherwise look for uq results in all directories in results_dir
        if "items" in kwargs:
            items = kwargs["items"]
        else:
            items = os.listdir("{}".format(ri))

        scores.append(sample_testing_function(ri, si, **kwargs))

        for item in items:
            if os.path.isdir(os.path.join(ri, item)):
                if os.path.isdir(os.path.join(sif_dir, item)):
                    print(os.path.join(ri, item))
                    print(os.path.join(si, item))
                    scores.append(
                        sample_testing_function(
                            os.path.join(ri, item),
                            os.path.join(si, item),
                            **kwargs
                        )
                    )
                else:
                    print(
                        "ERROR: SIF dir structure doesn't match "
                        "results dir structure."
                    )

        scores_aggregation = aggregation_function(scores, **kwargs)

        # update return results dict
        sif_vvp_results.update({ri: {}})

        sif_vvp_results[ri].update(
            {"scores": scores, "scores_aggregation": scores_aggregation}
        )

    return sif_vvp_results
