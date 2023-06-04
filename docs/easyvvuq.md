# Sensitivity analysis using FabSim3 and EasyVVUQ

FabSim3 is very useful when submitting a large number of jobs at together. One of the cases where this becomes especially useful is for sensitivity analysis. Sensitivity analysis can be breifly described as the process of evaluating the extent to which various input parameters affect the output of a simulation. One of the popular ways of quantifying this effect of parameters on the simulations is throgh Sobol Indices. Computation of Sobol Indices involves running the simulation for a large number of parameter sets and then comuting the variances among the various subsets of results obtained. Given the large number of computations required, this becomes a suitable candidate for simplification using FabSim3.

In this tutorial, we showcase how to conduct sensitivity analysis using FabSim3 and the python packages EasyVVUQ and QCG-PilotJob. Theb tutorial will use a simple plugin called `FabDynamics` which has been tailored for this purpose.

## Brief introduction of Dynamics and FabDynamics

At the core of this tutorial is the `Dynamics` software which numerically solves a system of differential equations for a fixed amount of time. By default, if no arguments are provided, the program solves the FitzHugh-Nagumo system of differential equations:

$$ \dfrac{dx}{dt} = \dfrac{x^3}{3} - x + \dfrac{1}{2} $$

$$ \dfrac{dy}{dt} = \dfrac{x + a - by}{c} $$

where $a$, $b$ and $c$ are three real-valued parameters that determine the time-evolution of dynamical variables $x$ and $y$.

In order to use FabSim3 with the `Dynamics` software, we use the `FabDynamics` plugin. This plugin would help us submit large ensembles of simulation runs and perform sensitivity analysis. We discuss this aspect of the plugin in the following sections of the tutorial.

## Installing Dynamics

In order to install the `Dynamics` software:

1. Clone the software repository in a directory of your choice:

    ```sh
    git clone https://github.com/arindamsaha1507/dynamics.git
    ```
2. Enter the newly created directory:
    ```sh
    cd dynamics
    ```

3. Install the required dependencies:
    ```sh
    pip install -r requirements.txt
    ```

4. This should complete the installation process. Check that the software works properly by issuing the command:
    ```sh
    python run.py
    ```
    This should create a new file called `timeseries.csv` which contains the time-evolution of variables $x$ and $y$.

5. To check that the results are as expected, you can plot the results using:
    ```sh
    python plotter.py
    ```
    This should result in a plot similar to the one shown below.

<figure>
    <img src="../images/fhn_plot.png" width="600"> 
</figure>

## Installing FabDynamics

Now, with the `Dynamics` software installed, we must install the `FabDynamics` plugin so that we can use it with FabSim3:

1. With FabSim3 installed properly, issue the following command:
    ```sh
    fabsim localhost install_plugin:FabDynamics
    ```
    This should create a `FabDynamics` subdirectory in the `FabSim3/plugins` directory.

2. Change to the newly created directory:
    ```sh
    cd <path to FabSim3 directory>/plugins/FabDynamics
    ```

3. Copy the contents of the `machines_FabDynamics_user_example.yml` file into a new file `machines_FabDynamics_user.yml`:
    ```sh
    cp machines_FabDynamics_user.yml machines_FabDynamics_user_example.yml
    ```

4. Now edit the the last line of the `machines_FabDynamics_user.yml` file with the location where dynamics software is installed:

    ```yaml
    default:

    dynamics_args:

        outfile: 'timeseries.csv'

    localhost:

    # location of dynamics in your local PC
    dynamics_location: "<path/to/dynamics/software>"
    ```

## Perfoming sensitivity analysis and computing Sobol Indices

The `FabDynamics` plugin comes pre-configured for sensitivity analysis. In order to start sensitivity analysis with default settings, simply issue the command:

```sh
fabsim localhost dyn_init_SA:config=fhn
```

Based on the pre-set configuration, issuing this command selects 64 points in the three-dimensional parameter space defined by parameters $a$, $b$ and $c$. It then submits one simulation run for each parameter set to the localhost.

After all the simulation runs have successfully run, the results of the simulations can be collected and analysed using a single command:

```sh
fabsim localhost dyn_analyse_SA:config=fhn
```

Issuing this command also computes the Sobol indices at each point in the timeseries. The results of this analysis are stored in the directory: 

```
<path to FabSim3 directory>/plugins/FabDynamics/SA/dyn_SA_SCSampler
```

In this directory
- The first order Sobol indices are stored in `sobols.yml`. The contents of this file should look like:

    ```yaml
    campaign_info:
    name: "dyn_SA_SCSampler"
    work_dir: "/home/arindam/FabSim3/plugins/FabDynamics"
    num_runs: 64
    output_column: "x"
    polynomial_order: 3
    sampler: "SCSampler"
    distribution_type: "Uniform"
    sparse: "False"
    growth: "False"
    quadrature_rule: "G"
    midpoint_level1: "False"
    dimension_adaptive: "False"
    a:
    # arithmetic mean i.e., (x1 + x2 + … + xn)/n
    sobols_first_mean: 0.435
    # geometric mean, i.e., n-th root of (x1 * x2 * … * xn)
    sobols_first_gmean: 0.4329
    sobols_first: [0.5201, 0.5201, 0.5201, 0.5201, 0.52, 0.52, 0.52, 0.5199, 0.5199,  0.3959, 0.3956, 0.3953, 0.395, 0.3947, 0.3945, 0.3942, 0.3938, 0.3935]
    b:
    # arithmetic mean i.e., (x1 + x2 + … + xn)/n
    sobols_first_mean: 0.011
    # geometric mean, i.e., n-th root of (x1 * x2 * … * xn)
    sobols_first_gmean: 0.0085
    sobols_first: [0.0042, 0.0042, 0.0041, 0.0041, 0.004, 0.004, 0.004, 0.0039, 0.0039, 0.0039, 0.0038, 0.0038, 0.0037, 0.0037, 0.0037, 0.0036, 0.0036, 0.0036, 0.0036, 0.0035, ... 0.0069, 0.007, 0.007, 0.007, 0.0071, 0.0071, 0.0072, 0.0072, 0.0073, 0.0073]
    c:
    # arithmetic mean i.e., (x1 + x2 + … + xn)/n
    sobols_first_mean: 0.0382
    # geometric mean, i.e., n-th root of (x1 * x2 * … * xn)
    sobols_first_gmean: 0.0288
    sobols_first: [0.0097, 0.0098, 0.0099, 0.01, 0.0101, 0.0102, 0.0103, 0.0104, 0.0105, 0.0106, 0.0107, ... 0.0197, 0.0195, 0.0194, 0.0192, 0.0191, 0.0189, 0.0188, 0.0186, 0.0185, 0.0183, 0.0182]
    ```

    As evident from the contents of the file, the first order Sobol indices for each parameter is computed separately.

- The plot of the first-order Sobol indices is stored in `plot_sobols_first[x].png`. The plot should look similar to:

<figure>
    <img src="../images/fhn_plot.png" width="600"> 
</figure>

- Similar plot showing all Sobol indices (inclding the higher order indices) is stored in `plot_all_sobol[x].png`. The plot should look similar to:

<figure>
    <img src="../images/fhn_plot.png" width="600"> 
</figure>

- The command also creates other plots not directly related to the Sobol indices, namely `raw[x].png` and `plot_statistical_moments[x].png`.