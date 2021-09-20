from fabsim.base.fab import *
# Add local script and template path for FabSim3
add_local_paths("FabCannonsim")


@task
@load_plugin_env_vars("FabCannonsim")
def Cannonsim(app, **args):
    """
    Submit a single job of Cannon_app

          >_ fabsim <remote_machine> Cannonsim:cannon_app
    e.g., >_ fabsim localhost Cannonsim:cannon_app
    """
    update_environment(args)
    with_config(app)
    execute(put_configs, app)
    env.script = "cannonsim"
    job(args)
