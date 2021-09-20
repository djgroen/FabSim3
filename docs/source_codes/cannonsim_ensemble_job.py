from fabsim.base.fab import *
# Add local script and template path for FabSim3
add_local_paths("FabCannonsim")


@task
@load_plugin_env_vars("FabCannonsim")
def Cannonsim(app, **args):
    ...
    ...
    ...


@task
@load_plugin_env_vars("FabCannonsim")
def Cannonsim_ensemble(app, **args):
    """
    Submit an ensemble of canon_app jobs
        >_ fabsim <remote_machine> Cannonsim_ensemble:cannon_app
        >_ fabsim localhost Cannonsim_ensemble:cannon_app
    """
    update_environment(args)
    with_config(app)
    sweep_dir = find_config_file_path(app) + "/SWEEP"
    env.script = "cannonsim"
    run_ensemble(app, sweep_dir, **args)
