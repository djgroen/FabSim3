from string import Template
import os
import sys
from beartype import beartype
from fabsim.base.env import env
from typing import Optional


def script_templates(*names, **options):
    commands = options.get("commands", [])
    result = "\n".join(
        [script_template_content(name) for name in names] + commands
    )
    return script_template_save_temporary(
        result,
    )


@beartype
def script_template_content(template_name: str):
    for p in env.local_templates_path:
        template_file_path = os.path.join(p, template_name)
        if os.path.exists(template_file_path):
            source = open(template_file_path)

    try:
        return template(source.read())
    except UnboundLocalError:
        raise UnboundLocalError(
            "FabSim Error: could not find template file {} . \
            FabSim looked for it in the following directories: {}".format(
                template_name, env.local_templates_path)
        )


@beartype
def script_template_save_temporary(content: str) -> str:
    destname = os.path.join(
        env.fabsim_root, "deploy", ".jobscripts", env["name"]
    )

    if hasattr(env, "label") and len(env.label) > 0:
        destname += "_" + env.label

    destname += ".sh"

    # Support for multi-level directories in the configuration files.
    if not os.path.exists(os.path.dirname(destname)):
        try:
            os.makedirs(os.path.dirname(destname))
        except OSError as exc:  # Guard against race condition
            if exc.errno != errno.EEXIST:
                raise
    target = open(destname, "w")
    target.write(content)
    return destname


@beartype
def script_template(template_name: str) -> str:
    """
    Load a template of the given name, and fill it in based on the Fabric
    environment dictionary, storing the result in deploy/.scripts/job-name.sh
    job-name is loaded from the environment dictionary.
    Return value is the path of the generated script.
    """
    result = script_template_content(template_name)
    return script_template_save_temporary(result)


@beartype
def template(pattern: str, number_of_iterations: Optional[int] = 1) -> str:
    """
    Low-level templating function, insert env variables into any string pattern
        - number_of_iterations can be adjusted to allow recurring
                templating using a single function call.
    """
    # print(env.flee_location)
    try:
        for i in range(0, number_of_iterations):
            template = Template(pattern).substitute(env)
            pattern = template

        return template
    except KeyError as err:
        print("ORIGINAL PATTERN:\n\n{}".format(pattern))
        print(
            "SAFELY SUBSTITUTED PATTERN:\n\n{}".format(
                Template(pattern).safe_substitute(env)
            )
        )
        print("ERROR: FABSIM_TEMPLATE_KEYERROR")
        print(
            "Template variables were not found in FabSim env dictionary: \
            These variables need to be added, with a default value set."
        )
        print(
            "FabSim performed a 'safe_substite' and print the original \
            template and the partially substituted one (both are given above \
            this message). Variables that are missing in the env dictionary \
            will be displayed unsubstituted in the output text. FabSim will \
            now terminate as these errors would result in unpredictable \
            behavior otherwise."
        )

        sys.tracebacklimit = 0
        raise KeyError
        # sys.exit()
