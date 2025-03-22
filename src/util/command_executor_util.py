import subprocess

from src.app_armor.credentials_holder import CredentialsHolder


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
                input=f'{CredentialsHolder().get_pswd()}\n',
                capture_output=True,
                text=True)
    except Exception as e:
        return subprocess.CompletedProcess(args=command, returncode=1, stdout='', stderr=str(e))