
The computing pattern, also called Multiscale Computing Patterns (MCP), are aimed to simplify the implementation of the multiscale application by enhancing the execution of scenarios. From the application’s point of view, a pattern can determine the ordering and composition of single scale models that are coupled within a multiscale application.

## UQP
Uncertainty quantification (UQ) is an increasingly important field in the simulation-based modelling of scientific applications. It can be defined as a bridge between the statistical and probability theory, computer simulation-based techniques with 'the real world'. In other words, by identifying the source of uncertainty in each component of the model, UQ aims to make the results more reliable and have close predictions of the complex physical systems. A typical UQ problem involves one or more mathematical model subjects to some uncertainty of model parameter value.


<figure>
   <img src="images/UQ_pattern_system.png" width="500"> 
   Software architecture of the UQ system
</figure>


Uncertainty Quantification Pattern (UQP) is the term for workflows and algorithms focused on uncertainty quantification and propagation or sensitivity analysis. A general procedure/workflow for UQP can be defined as follows:

* Create an ensemble of simulations, i.e. individual runs of model simulation executions, containing different input or model parameters for each run;
* Execute all ensemble runs;
* Perform post-processing analysis by using statistical techniques, such as the Monte Carlo, Polynomial  Chaos  and  the  Stochastic  Collocation  methods, to measure the error distribution for each input or model parameters (individually);
* Refine and report the previous steps until the confidence in the simulation results is reached, i.e. identifying the source of uncertainty in the model parameters.

## VVP

Verification and validation (V&V) provide a framework for building confidence in computational simulation predictions. The Verification process addresses the quality of the numerical treatment of the model that is used in the predication, and the validation process addresses the quality of the model. The inclusion of V&V is the key to obtain credibility of a proposed model. Given the diversity of applications, there is no doubt that having a V&V pattern increases trustworthiness of the simulation model. 

Within [VECMA](https://www.vecma.eu/) project,  we identified *four* prominent V&V patterns which are most suitable for multiscale computing applications:

1. Stable Intermediate Forms (SIF)
2. Level of Refinement (LoR)
3. Ensemble Output Validation (EoV)
4. Quantity of Interest (QoI)

Within FabSim3, we provide support for these V&V patterns as follow:

### Ensemble Output Validation (EoV)

`ensemble_vvp` function goes through all the output directories and calculates the scores.
```python
def ensemble_vvp(results_dirs, sample_testing_function, aggregation_function, **kwargs)
	...
```

* `results_dirs`: list of result dirs to analyse.
* `sample_testing_function`: analysis/validation/verification function to be performed on each subdirectory of the `results_dirs`.
* `aggregation_function`: function to combine all results.
* `**kwargs`: The optional inputparameter items that can be used to give explicit ordering of the various subdirectories.

The `ensemble_vvp` function returns a `dict` containing the score per each `results_dirs` sub-directory.

#### An example from the FabFlee plugin

=== "Usage Example"

    ``` python
    import VVP.vvp as vvp
    vvp.ensemble_vvp(
        results_dirs="{}/{}/RUNS".format(env.local_results, results_dir),
        sample_testing_function=vvp_validate_results,
        aggregation_function=make_vvp_mean
    )
    ```

=== "sample_testing_function"

    ``` python
	def vvp_validate_results(output_dir="", **kwargs):
	    """ Extract validation results (no dependencies on FabSim env). """

	    flee_location_local = user_config["localhost"].get(
	        "flee_location", user_config["default"].get("flee_location"))

	    local("python3 %s/flee/postprocessing/extract-validation-results.py %s "
	          "> %s/validation_results.yml"
	          % (flee_location_local, output_dir, output_dir))

	    with open("{}/validation_results.yml".format(output_dir), 'r') as val_yaml:
	        validation_results = yaml.load(val_yaml, Loader=yaml.SafeLoader)

	        # TODO: make a proper validation metric using a validation schema.
	        # print(validation_results["totals"]["Error (rescaled)"])
	        print("Validation {}: {}".format(output_dir.split("/")[-1],
	                                         validation_results["totals"][
	                                         "Error (rescaled)"]))
	        return validation_results["totals"]["Error (rescaled)"]

	    print("error: vvp_validate_results failed on {}".format(output_dir))
	    return -1.0
    ```

=== "aggregation_function"

    ``` python
	def make_vvp_mean(np_array, **kwargs):
	    mean_score = np.mean(np_array)
	    print("Mean score: {}".format(mean_score))
	    return mean_score
    ```
