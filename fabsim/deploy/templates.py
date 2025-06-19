import errno
import os
import re
import sys
from string import Template
from typing import Any, Dict, FrozenSet, Set, Tuple

from beartype import beartype
from beartype.typing import Optional

from fabsim.base.env import env

# Template cache to store loaded raw templates
_template_cache: Dict[str, str] = {}
# Cache for processed templates - keys are (template_name, relevant_env_vars)
_processed_template_cache: Dict[Tuple[str, FrozenSet[Tuple[str, str]]],
                                str] = {}
# Cache for template variable patterns (optimization for large-scale jobs)
_template_vars_cache: Dict[str, Set[str]] = {}

# Configuration for cache management (can be overridden via environment
# or machines_user.yml)
MAX_PROCESSED_CACHE_SIZE = int(os.environ.get(
    'template_cache_size',
    '2000'
))
# Flag to show cache status message only once per session
_cache_status_shown = False


def _get_cache_setting():
    """Get caching setting from environment, machines config, or default."""
    # Environment variable (for quick testing/CI)
    env_setting = os.environ.get('ENABLE_TEMPLATE_CACHE', '').lower()
    if env_setting in ('true', '1', 'yes', 'on'):
        return True
    elif env_setting in ('false', '0', 'no', 'off'):
        return False

    # env configuration (from machines_user.yml)
    if hasattr(env, 'enable_template_cache'):
        cache_setting = getattr(env, 'enable_template_cache', True)
        if isinstance(cache_setting, bool):
            return cache_setting
        elif isinstance(cache_setting, str):
            return cache_setting.lower() in ('true', '1', 'yes', 'on')

    # Default to enabled
    return True


ENABLE_TEMPLATE_CACHE = _get_cache_setting()


def script_templates(*names, **options):
    # Show template cache status once per session (only in main process)
    global _cache_status_shown
    if not _cache_status_shown:
        _cache_status_shown = True
        # Only show notification in the main process to avoid
        # multiprocessing spam
        try:
            from multiprocessing import current_process
            if current_process().name == 'MainProcess':
                cache_enabled = _get_cache_setting()
                status = "ENABLED" if cache_enabled else "DISABLED"
                print(f"Template cache: {status}")
        except ImportError:
            # Fallback if multiprocessing not available
            cache_enabled = _get_cache_setting()
            status = "ENABLED" if cache_enabled else "DISABLED"
            print(f"Template cache: {status}")

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
    Can be disabled via enable_template_cache setting.
    """
    # Check cache setting dynamically
    cache_enabled = _get_cache_setting()

    # If caching is disabled, always load and process template fresh
    if not cache_enabled:
        return _load_and_process_template_uncached(template_name)

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

    # Optimized: Check if we've already analyzed this template's variables
    if template_name not in _template_vars_cache:
        # One-time analysis using regex (more efficient than string search)
        var_pattern = re.compile(r'\$\{?([A-Za-z_][A-Za-z0-9_]*)\}?')
        env_vars_in_template = set(var_pattern.findall(raw_template))
        _template_vars_cache[template_name] = env_vars_in_template
    else:
        # Use cached variable analysis
        env_vars_in_template = _template_vars_cache[template_name]

    # Filter to only variables that exist in current env
    relevant_vars = {var for var in env_vars_in_template if var in env}

    # Create a cache key from template name and relevant env vars
    cache_key = (template_name,
                 frozenset((k, str(env.get(k, ''))) for k in relevant_vars))

    # If we have a cached processed template for this exact environment, use it
    if cache_key in _processed_template_cache:
        return _processed_template_cache[cache_key]

    # Process the template and cache the result
    processed_template = template(raw_template)

    # Safe cache size management to prevent unbounded growth
    if len(_processed_template_cache) >= MAX_PROCESSED_CACHE_SIZE:
        # Remove oldest 10% of entries (simple FIFO cleanup)
        cleanup_count = max(1, MAX_PROCESSED_CACHE_SIZE // 10)
        for _ in range(cleanup_count):
            if _processed_template_cache:
                oldest_key = next(iter(_processed_template_cache))
                _processed_template_cache.pop(oldest_key)

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
        dict: Statistics about cache usage and configuration
    """
    # Determine configuration source
    config_source = "default"
    if 'ENABLE_TEMPLATE_CACHE' in os.environ:
        env_val = os.environ['ENABLE_TEMPLATE_CACHE']
        config_source = f"environment (ENABLE_TEMPLATE_CACHE={env_val})"
    elif hasattr(env, 'enable_template_cache'):
        cache_val = getattr(env, 'enable_template_cache')
        config_source = (f"machines_user.yml "
                         f"(enable_template_cache={cache_val})")

    # Calculate cache hit ratio
    if _get_cache_setting():
        ratio = (len(_processed_template_cache) /
                 max(1, len(_template_cache))) * 100
        hit_ratio = f"{ratio:.1f}%"
    else:
        hit_ratio = "N/A (caching disabled)"

    return {
        "caching_enabled": _get_cache_setting(),
        "config_source": config_source,
        "max_cache_size": MAX_PROCESSED_CACHE_SIZE,
        "raw_templates_cached": len(_template_cache),
        "processed_templates_cached": len(_processed_template_cache),
        "template_vars_analyzed": len(_template_vars_cache),
        "raw_templates": list(_template_cache.keys()),
        "memory_usage_estimate": (
            sum(len(t) for t in _template_cache.values()) +
            sum(len(pt) for pt in _processed_template_cache.values())
        ),
        "cache_hit_ratio": hit_ratio,
    }


def clear_template_cache():
    """
    Clear the template cache completely.
    Useful for testing or if memory usage becomes a concern.
    """
    _template_cache.clear()
    _processed_template_cache.clear()
    _template_vars_cache.clear()

    return {"status": "Template cache cleared"}


@beartype
def _load_and_process_template_uncached(template_name: str) -> str:
    """
    Load and process a template without any caching.
    Used when ENABLE_TEMPLATE_CACHE is disabled for benchmarking.
    """
    # Find and read template file fresh every time
    found = False
    raw_template = ""

    for p in env.local_templates_path:
        template_file_path = os.path.join(p, template_name)
        if os.path.exists(template_file_path):
            with open(template_file_path) as source:
                raw_template = source.read()
            found = True
            break

    if not found:
        raise UnboundLocalError(
            "FabSim Error: could not find template file {} . \
            FabSim looked for it in the following directories: {}".format(
                template_name, env.local_templates_path
            )
        )

    # Process template fresh every time (no caching)
    return template(raw_template)


def set_template_caching(enabled: bool, update_env: bool = True):
    """
    Enable or disable template caching programmatically.

    Args:
        enabled (bool): True to enable caching, False to disable
        update_env (bool): Whether to update the FabSim3 env as well

    Returns:
        dict: Status message and previous state
    """
    previous_state = _get_cache_setting()

    # Update the env setting (this is what _get_cache_setting() reads)
    if update_env:
        env.enable_template_cache = enabled

    status_msg = f"Template caching {'enabled' if enabled else 'disabled'}"
    if not enabled:
        # Clear cache when disabling for clean benchmarking
        clear_template_cache()
        status_msg += " (cache cleared)"

    return {
        "status": status_msg,
        "previous_state": previous_state,
        "current_state": enabled,
        "env_updated": update_env
    }


def benchmark_template_performance(template_name: str, iterations: int = 100):
    """
    Benchmark template processing with and without caching.
    Useful for performance analysis and publications.

    Args:
        template_name (str): Name of template to benchmark
        iterations (int): Number of iterations to run

    Returns:
        dict: Benchmark results
    """
    import time

    # Ensure template exists first
    if not any(os.path.exists(os.path.join(p, template_name))
               for p in env.local_templates_path):
        return {"error": f"Template {template_name} not found"}

    # Benchmark without caching
    clear_template_cache()
    original_cache_setting = _get_cache_setting()
    set_template_caching(False)

    start_time = time.time()
    for _ in range(iterations):
        script_template_content(template_name)
    uncached_time = time.time() - start_time

    # Benchmark with caching
    set_template_caching(True)
    clear_template_cache()  # Start fresh

    start_time = time.time()
    for _ in range(iterations):
        script_template_content(template_name)
    cached_time = time.time() - start_time

    # Restore original setting
    set_template_caching(original_cache_setting)

    speedup = uncached_time / cached_time if cached_time > 0 else float('inf')

    return {
        "template": template_name,
        "iterations": iterations,
        "uncached_time_seconds": round(uncached_time, 4),
        "cached_time_seconds": round(cached_time, 4),
        "speedup_factor": round(speedup, 2),
        "cache_efficiency": (
            f"{((uncached_time - cached_time) / uncached_time * 100):.1f}%"
        )
    }


def refresh_cache_setting():
    """
    Refresh the cache setting from current environment.
    Useful when env is updated during runtime.
    """
    global ENABLE_TEMPLATE_CACHE
    ENABLE_TEMPLATE_CACHE = _get_cache_setting()
    return ENABLE_TEMPLATE_CACHE
