from PyQt5.QtWidgets import QStackedWidget

from src.app_armor.apparmor_manager import AppArmorManager


class PagesHolder:
    _instance = None

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(PagesHolder, cls).__new__(cls)
            cls._instance.content_area = None
        return cls._instance

    def get_content_area(self) -> QStackedWidget:
        return self.content_area



