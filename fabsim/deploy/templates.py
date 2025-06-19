import os
import sys
import errno
from string import Template
from typing import Dict, Tuple, FrozenSet, Any

from beartype import beartype
from beartype.typing import Optional

from fabsim.base.env import env

# Template cache to store loaded raw templates
_template_cache: Dict[str, str] = {}
# Cache for processed templates - keys are (template_name, relevant_env_vars)
_processed_template_cache: Dict[Tuple[str, FrozenSet[Tuple[str, str]]], str] = {}


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
    """
    Load a template file and process it with environment variables.
    Uses caching to avoid redundant file reads and processing.
    """
    # First, try to get the raw template from cache
    if template_name not in _template_cache:
        found = False
        for p in env.local_templates_path:
            template_file_path = os.path.join(p, template_name)
            if os.path.exists(template_file_path):
                with open(template_file_path) as source:
                    _template_cache[template_name] = source.read()
                found = True
                break
        
        if not found:
            raise UnboundLocalError(
                "FabSim Error: could not find template file {} . \
                FabSim looked for it in the following directories: {}".format(
                    template_name, env.local_templates_path
                )
            )

    # Get template from cache
    raw_template = _template_cache[template_name]
    
    # For cache key, identify env variables used in this template
    env_vars_in_template = set()
    for var in env.keys():
        if f"${var}" in raw_template or f"${{{var}}}" in raw_template:
            env_vars_in_template.add(var)
    
    # Create a cache key from template name and relevant env vars
    cache_key = (template_name, frozenset((k, str(env.get(k, ''))) for k in env_vars_in_template))
    
    # If we have a cached processed template for this exact environment, use it
    if cache_key in _processed_template_cache:
        return _processed_template_cache[cache_key]
    
    # Process the template and cache the result
    processed_template = template(raw_template)
    _processed_template_cache[cache_key] = processed_template
    
    return processed_template


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
            # template = Template(pattern).substitute(env)
            template = Template(pattern).safe_substitute(env)
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


def get_template_cache_stats():
    """
    Return statistics about the template cache for debugging and monitoring.
    
    Returns:
        dict: Statistics about cache usage
    """
    return {
        "raw_templates_cached": len(_template_cache),
        "processed_templates_cached": len(_processed_template_cache),
        "raw_templates": list(_template_cache.keys()),
        "memory_usage_estimate": sum(len(t) for t in _template_cache.values()) +
                                 sum(len(pt) for pt in _processed_template_cache.values())
    }


def clear_template_cache():
    """
    Clear the template cache completely.
    Useful for testing or if memory usage becomes a concern.
    """
    _template_cache.clear()
    _processed_template_cache.clear()
    return {"status": "Template cache cleared"}
