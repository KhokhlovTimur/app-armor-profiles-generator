import subprocess
import getpass

from src.app_armor.data_holder import DataHolder


class AppArmorManager:
    def __init__(self):
        self.sudo_password = None
        pass

    def run_command(self, command):
        try:
            full_command = command
            process = subprocess.run(full_command, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)

            if process.returncode == 0:
                return process.stdout
            else:
                return f"Ошибка: {process.stderr}"
        except Exception as e:
            return f"Ошибка при выполнении команды: {str(e)}"

    def check_status(self):
        """
        Проверяет статус AppArmor.
        """
        return self.run_command(["sudo", "aa-status"])

    def enforce_profile(self, profile_name):
        """
        Применяет режим enforce для профиля.

        Args:
            profile_name (str): Название профиля.
        """
        return self.run_command(["sudo", "aa-enforce", profile_name])

    def complain_profile(self, profile_name):
        """
        Применяет режим complain для профиля.

        Args:
            profile_name (str): Название профиля.
        """
        return self.run_command(["sudo", "aa-complain", profile_name])

    def load_profile(self, profile_path):
        """
        Загружает профиль AppArmor из указанного файла.

        Args:
            profile_path (str): Путь к файлу профиля.
        """
        return self.run_command(["sudo", "apparmor_parser", "-r", profile_path])

    def remove_profile(self, profile_name):
        """
        Удаляет профиль AppArmor.

        Args:
            profile_name (str): Название профиля.
        """
        return self.run_command(["sudo", "apparmor_parser", "-R", f"/etc/apparmor.d/{profile_name}"])

    def list_profiles(self):
        """
        Возвращает список всех доступных профилей AppArmor.
        """
        return self.run_command(["sudo", "ls", "/etc/apparmor.d/"])

    def get_profiles_data(self):
        try:
            result = subprocess.run(
                ['sudo', '-S', 'aa-status'],
                input=f'{DataHolder().get_pswd()}\n',
                capture_output=True,
                text=True
            )
            if result.returncode != 0:
                print(f"Ошибка при выполнении команды: {result.stderr}")
                return []

            lines = result.stdout.split('\n')
            profiles = []
            current_mode = None

            for line in lines:
                line = line.strip()

                # Определяем режим работы профилей
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

                # # Если строка начинается с символа '/', 'snap.', или что-то похожее на путь
                # elif line.startswith('/') or line.startswith('snap.') or line.startswith('tcpdump') or line.startswith(
                #         'ubuntu_pro'):
                profiles.append({
                    'name': line,
                    'mode': current_mode,
                    'path': line
                })

            return profiles
        except Exception as e:
            print(f"Ошибка: {e}")
            return []
