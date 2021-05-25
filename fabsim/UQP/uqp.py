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


def uqp1_epistemic(input_space, sampling_function, model_exec,
                   collation_function, **kwargs):
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


def uqp2_aleatoric(model1_exec, translation_function, model2_exec,
                   collation_function, **kwargs):
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


def uqp2_epistemic(input_space, sampling_function, model1_exec,
                   translation_function, model2_exec,
                   collation_function, **kwargs):
    pass
