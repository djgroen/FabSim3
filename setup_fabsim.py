from pprint import pprint
import platform
import sys
import getpass
import os
import ruamel.yaml
import subprocess

yaml = ruamel.yaml.YAML()
yaml.allow_duplicate_keys = None
yaml.preserve_quotes = True
# to Prevent long lines getting wrapped in ruamel.yaml
yaml.width = 4096  # or some other big enough value to prevent line-wrap


def get_platform():
    platforms = {
        'linux': 'Linux',
        'linux1': 'Linux',
        'linux2': 'Linux',
        'linux3': 'Linux',
        'darwin': 'OSX',
        'win32': 'Windows'
    }
    try:
        return platforms[sys.platform]
    except:
        print("[%s] Unidentified system !!!" % (sys.platform))
        exit()


class AttributeDict(dict):

    def __getattr__(self, key):
        try:
            return self[key]
        except KeyError:
            # to conform with __getattr__ spec
            raise AttributeError(key)

    def __setattr__(self, key, value):
        self[key] = value

    def __delattr__(self, key):
        del self[key]


def linux_distribution():
    try:
        return platform.linux_distribution()
    except:
        return "N/A"

FS3_env = AttributeDict({
    'OS_system': get_platform(),
    'OS_release': platform.release(),
    'OS_version': platform.version(),
    # os.getcwd() : not working is you call is outside of FabSim3 folder
    'FabSim3_PATH': os.path.dirname(os.path.realpath(__file__)),
    'user_name': getpass.getuser(),
    'machines_yml': None,
    'machines_user_yml': None

})


def config_yml_files():
    # Load and invoke the default non-machine specific config JSON
    # dictionaries.
    FS3_env.machines_yml = yaml.load(
        open(os.path.join(FS3_env.FabSim3_PATH,
                          'deploy',
                          'machines.yml'))
    )

    FS3_env.machines_user_yml = yaml.load(
        open(os.path.join(FS3_env.FabSim3_PATH,
                          'deploy',
                          'machines_user_example.yml'))
    )
    # set localhost execution folder in machines.yml
    FS3_env.machines_yml['localhost']['home_path_template'] = os.path.join(
        FS3_env.FabSim3_PATH, 'localhost_exe')
    FS3_env.machines_yml['default']['home_path_template'] = os.path.join(
        FS3_env.FabSim3_PATH, 'localhost_exe')
    # save machines.yml
    with open(os.path.join(FS3_env.FabSim3_PATH,
                           'deploy', 'machines.yml'), 'w') as yaml_file:
        yaml.dump(FS3_env.machines_yml, yaml_file)

    # setup machines_user.yml
    FS3_env.machines_user_yml['default'][
        'local_results'] = os.path.join(FS3_env.FabSim3_PATH, 'results')
    FS3_env.machines_user_yml['default']['local_configs'] = os.path.join(
        FS3_env.FabSim3_PATH, 'config_files')
    FS3_env.machines_user_yml['default']['username'] = FS3_env.user_name
    FS3_env.machines_user_yml['localhost']['username'] = FS3_env.user_name
    # save machines_user.yml
    with open(os.path.join(FS3_env.FabSim3_PATH,
                           'deploy', 'machines_user.yml'), 'w') as yaml_file:
        yaml.dump(FS3_env.machines_user_yml, yaml_file)

    # create localhost execution folder if it is not exists
    if not os.path.exists(os.path.join(FS3_env.FabSim3_PATH, 'localhost_exe')):
        os.makedirs(os.path.join(FS3_env.FabSim3_PATH, 'localhost_exe'))


def main():

    config_yml_files()

    # run fab localhost setup_fabsim
    assert(subprocess.call(["fab", "localhost", "setup_fabsim"],
                           cwd=FS3_env.FabSim3_PATH) == 0)
    # use ssh-add instead of ssh-copy-id for MacOSX
    if FS3_env.OS_system == 'OSX':
        assert(subprocess.call(["ssh-add", "~/.ssh/id_rsa"]) == 0)

    # setup PATH and PYTHONPATH in bashrc
    if FS3_env.OS_system == 'Linux':
        bash_file_name = os.path.join(os.path.expanduser('~'), '.bashrc')
    elif FS3_env.OS_system == 'OSX':
        bash_file_name = os.path.join(os.path.expanduser('~'), '.bash_profile')

    if os.path.isfile(bash_file_name) is False:
        print("Error : can not find bash file !!!")
        exit()

    FabSim_env_setting = []
    FabSim_env_setting.append('# FabSim Env parameters')
    # check if <FabSim3_PATH>/bin is already in PATH variable or not
    if FS3_env.FabSim3_PATH not in os.environ.get('PATH'):
        FabSim_env_setting.append('export PATH=%s/bin:$PATH'
                                  % (FS3_env.FabSim3_PATH))
    # check if <FabSim3_PATH> is already in PYTHONPATH variable or not
    if FS3_env.FabSim3_PATH not in os.environ.get('PYTHONPATH'):
        FabSim_env_setting.append('export PYTHONPATH=%s:$PYTHONPATH'
                                  % (FS3_env.FabSim3_PATH))

    with open(bash_file_name, 'a+') as out:
        out.write('\n'.join(FabSim_env_setting))


if __name__ == "__main__":
    main()


# https://shreevatsa.wordpress.com/2008/03/30/zshbash-startup-files-loading-order-bashrc-zshrc-etc/
'''

with open("file.txt", "w") as out_file:
    for line in buf:
        if line == "; Include this text\n":
            line = line + "Include below\n"
        out_file.write(line)
'''
