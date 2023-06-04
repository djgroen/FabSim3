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
