from src.ui.create_profile.profile_add import CreateProfilePage


class ProfileFromLogsGenerator(CreateProfilePage):
    def __init__(self, profile: AppArmorProfile, parent):
        super().__init__(profile)
        self.setWindowTitle("Edit Profile")
        self.profile = profile
        self.edit_profile_text = None
        self.parent = parent
        self.profile_code = read_apparmor_profile_by_name(self.profile.name)
        self.template_edit.setPlainText(self.profile_code)