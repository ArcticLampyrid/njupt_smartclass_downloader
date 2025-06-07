from typing import Optional

import requests
from textual.app import App

from njupt_smartclass_downloader import app_task
from njupt_smartclass_downloader.njupt_smartclass import NjuptSmartclass


class NjuptSmartclassDownloaderApp(App):
    CSS_PATH = "styles/app.tcss"
    TITLE = "NJUPT Smartclass Downloader"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.session = requests.Session()
        self.smartclass: Optional[NjuptSmartclass] = None
        self.task_manager = app_task.TaskManager()

    def on_mount(self) -> None:
        # Avoid circular import issues
        from njupt_smartclass_downloader.screens.login_screen import LoginScreen

        self.push_screen(LoginScreen())
