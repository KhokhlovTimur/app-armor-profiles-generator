import subprocess

from src.app_armor.data_holder import DataHolder


def run_command(command):
    try:
        if 'sudo' not in command:
            return subprocess.run(
                command,
                capture_output=True,
                text=True)
        else:
            return subprocess.run(
                command,
                input=f'{DataHolder().get_pswd()}\n',
                capture_output=True,
                text=True)
    except:
        pass