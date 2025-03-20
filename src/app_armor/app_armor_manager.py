from src.utils.command_executor_util import run_command


class AppArmorManager:
    def __init__(self):
        self.sudo_password = None
        pass

    def check_status(self):
        return run_command(["sudo", "aa-status"])

    def enforce_profile(self, profile_name):
        return run_command(["sudo", "aa-enforce", profile_name])

    def complain_profile(self, profile_name):
        return run_command(["sudo", "aa-complain", profile_name])

    def load_profile(self, profile_path):
        return run_command(["sudo", "apparmor_parser", "-r", profile_path])

    def remove_profile(self, profile_name):
        return run_command(["sudo", "apparmor_parser", "-R", f"/etc/apparmor.d/{profile_name}"])

    def list_profiles(self):
        return run_command(["sudo", "ls", "/etc/apparmor.d/"])

    def get_profiles_data(self):
        try:
            lines = run_command(['sudo', '-S', 'aa-status']).stdout.split('\n')
            profiles = []
            current_mode = None

            for line in lines:
                line = line.strip()

                if "profiles are in enforce mode" in line:
                    current_mode = "enforced"
                    continue
                elif "profiles are in complain mode" in line:
                    current_mode = "complain"
                    continue
                elif "profiles are in unconfined mode" in line:
                    current_mode = "unconfined"
                    continue
                elif "profiles are in prompt mode" in line:
                    current_mode = "prompt"
                    continue
                elif "profiles are in kill mode" in line:
                    current_mode = "kill"
                    continue
                elif "is loaded" in line or "are loaded" in line or "in mixed mode" in line or len(line.strip()) == 0:
                    continue

                profiles.append({
                    'name': line,
                    'mode': current_mode,
                    'path': line
                })

            return profiles
        except Exception as e:
            print(f"Ошибка: {e}")
            return []
