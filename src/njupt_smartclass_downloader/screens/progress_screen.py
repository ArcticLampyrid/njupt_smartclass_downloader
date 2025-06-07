from typing import Dict
import typing

from cv2 import exp
from textual.app import ComposeResult
from textual.widgets import Static, ListView, Header, Footer
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.binding import Binding

from njupt_smartclass_downloader.widgets.task_list_item import TaskListItem
from njupt_smartclass_downloader.app import NjuptSmartclassDownloaderApp
from njupt_smartclass_downloader.app_task import TaskStatus


class ProgressScreen(Screen):
    BINDINGS = [
        Binding("b", "back", "Back", show=True),
        Binding("q", "quit", "Quit", show=True),
        Binding("s", "toggle_scroll_lock", "Toggle Scroll Lock", show=True),
    ]

    CSS_PATH = "../styles/progress.tcss"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.task_items: Dict[str, TaskListItem] = {}
        self.auto_scroll_enabled: bool = True

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="progress-container"):
            with Vertical():
                yield Static("Tasks", id="progress-title")
                yield ListView(id="task-list", classes="task-list")
                yield Static("Auto-scroll: ON", id="scroll-status")

        yield Footer()

    def action_quit(self) -> None:
        self.app.exit()

    def action_back(self) -> None:
        self.app.pop_screen()

    def action_toggle_scroll_lock(self) -> None:
        self.auto_scroll_enabled = not self.auto_scroll_enabled
        status = "enabled" if self.auto_scroll_enabled else "disabled"
        self.app.notify(f"Auto-scroll {status}", severity="information")

        # Update status display with detailed task info
        self.update_status_display()

    def update_status_display(self) -> None:
        """Update the status display with task counts and auto-scroll state"""
        app = typing.cast(NjuptSmartclassDownloaderApp, self.app)
        current_tasks = app.task_manager.get_task_info()

        # Count tasks by status using TaskStatus enum values
        queued = sum(1 for task in current_tasks if task.status == TaskStatus.QUEUED)
        running = sum(1 for task in current_tasks if task.status == TaskStatus.RUNNING)
        completed = sum(
            1 for task in current_tasks if task.status == TaskStatus.COMPLETED
        )
        failed = sum(1 for task in current_tasks if task.status == TaskStatus.FAILED)

        scroll_status = "ON" if self.auto_scroll_enabled else "OFF"
        status_text = f"Auto-scroll: {scroll_status}, Queued: {queued}, Running: {running}, Completed: {completed}, Failed: {failed}"

        status_widget = self.query_one("#scroll-status", Static)
        status_widget.update(status_text)

    def on_mount(self) -> None:
        self.set_interval(1.0, self.auto_update)
        self.auto_update()

    def auto_update(self) -> None:
        app = typing.cast(NjuptSmartclassDownloaderApp, self.app)
        task_list = self.query_one("#task-list", ListView)
        current_tasks = app.task_manager.get_task_info()

        # Track if we added any new tasks
        new_tasks_added = False

        for task_info in current_tasks:
            if task_info.id in self.task_items:
                self.task_items[task_info.id].update_task_info(task_info)
            else:
                item = TaskListItem(task_info)
                self.task_items[task_info.id] = item
                task_list.append(item)
                new_tasks_added = True

        # Update status display with current task counts
        self.update_status_display()

        # Auto-scroll to bottom if new tasks were added and auto-scroll is enabled
        if new_tasks_added and self.auto_scroll_enabled:
            if task_list.is_scrollable and task_list.allow_vertical_scroll:
                task_list.action_scroll_end()
