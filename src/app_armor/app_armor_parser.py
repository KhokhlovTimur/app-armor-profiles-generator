import subprocess

from src.utils.command_executor_util import run_command

temp_files_path = "../../resources/new_profile.txt"
def check_profile_correctness(profile_as_string):
    __save_as_temp(profile_as_string)
    return run_command(["sudo", "apparmor_parser", "-T", temp_files_path])


def __save_as_temp(profile):
    with open(temp_files_path, "w") as f:
        f.write(profile)
