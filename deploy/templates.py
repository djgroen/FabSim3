# -*- coding: utf-8 -*-
#
# This source file is part of the FabSim software toolkit, which is distributed under the BSD 3-Clause license.
# Please refer to LICENSE for detailed information regarding the licensing.
#
# Use python standard library templates to allow strings to include $foo syntax to interpolate elements from the
# Fabric environment dictionary, and to generate job queue submission scripts therefrom.
#
# Job-queue submission scripts should be stored in deploy/templates, with filenames like legion-hemelb (for a script used to
# launch hemelb jobs on legion, or hector-unittest, for a script used to launch unit-testing jobs on hector.)

from fabric.api import *
from string import Template
import os
import sys

def script_templates(*names,**options):
  commands=options.get('commands',[])
  result= "\n".join([script_template_content(name) for name in names]+commands)
  return script_template_save_temporary(result)

def script_template_content(template_name):
  for p in env.local_templates_path:
    template_file_path = os.path.join(p, template_name)
    if os.path.exists(template_file_path):
      source=open(template_file_path)

  if source:
    return template(source.read())
  else:
    print("FabSim Error: could not find template file. FabSim looked for it in the following directories: ", env.local_templates_path)

def script_template_save_temporary(content):
  destname=os.path.join(env.localroot,'deploy','.jobscripts',env['name']+'.sh')

  # Support for multi-level directories in the configuration files.
  if not os.path.exists(os.path.dirname(destname)):
    try:
      os.makedirs(os.path.dirname(destname))
    except OSError as exc: # Guard against race condition
      if exc.errno != errno.EEXIST:
        raise

  target=open(destname,'w')
  target.write(content)
  return destname

def script_template(template_name):
  """
  Load a template of the given name, and fill it in based on the Fabric environment dictionary,
  storing the result in deploy/.scripts/job-name.sh
  job-name is loaded from the environment dictionary.
  Return value is the path of the generated script.
  """
  result=script_template_content(template_name)
  return script_template_save_temporary(result)

def template(pattern, number_of_iterations=1):
  """
  Low-level templating function, insert env variables into any string pattern.
  - number_of_iterations can be adjusted to allow recurring templating using a single function call.
  """
  try:
    for i in range(0, number_of_iterations):
      template = Template(pattern).substitute(env)
      pattern = template
    return template
  except KeyError as err:
    print("ORIGINAL PATTERN:\n\n%s" % (pattern))
    print("SAFELY SUBSTITUTED PATTERN:\n\n%s" % (Template(pattern).safe_substitute(env)))
    print("ERROR: FABSIM_TEMPLATE_KEYERROR")
    print("Template variables were not found in FabSim env dictionary: These variables need to be added, with a default value set.")
    print("FabSim performed a 'safe_substite' and print the original template and the partially substituted one (both are given above this message). Variables that are missing in the env dictionary will be displayed unsubstituted in the output text. FabSim will now terminate as these errors would result in unpredictable behavior otherwise.")
    sys.exit()

