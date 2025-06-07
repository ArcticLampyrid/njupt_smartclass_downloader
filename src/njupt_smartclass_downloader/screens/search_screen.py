import os
from typing import Dict, List, Optional
import typing

from textual.app import ComposeResult
from textual.widgets import Static, ListView, Header, Footer
from textual.containers import Container, Vertical
from textual.screen import Screen
from textual.binding import Binding
from sanitize_filename import sanitize

from njupt_smartclass_downloader import app_task
from njupt_smartclass_downloader.njupt_smartclass import (
    NjuptSmartclassVideoSearchCondition,
    NjuptSmartclassVideoSummary,
)
from njupt_smartclass_downloader.screens.progress_screen import ProgressScreen
from njupt_smartclass_downloader.widgets.video_list_item import VideoListItem
from njupt_smartclass_downloader.screens.search_input_modal import SearchInputModal
from njupt_smartclass_downloader.screens.download_options_modal import (
    DownloadOptionsModal,
)
from njupt_smartclass_downloader.app import NjuptSmartclassDownloaderApp


class SearchScreen(Screen):
    BINDINGS = [
        Binding("/", "search", "Search", show=True),
        Binding("space", "toggle_selection", "Toggle Selection", show=True),
        Binding("a", "select_all", "Select All", show=True),
        Binding("n", "select_none", "Select None", show=True),
        Binding("d", "download", "Download", show=True),
        Binding("p", "progress", "Progress", show=True),
        Binding("q", "quit", "Quit", show=True),
    ]

    CSS_PATH = "../styles/search.tcss"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.resources: List[NjuptSmartclassVideoSummary] = []
        self.video_items: Dict[str, VideoListItem] = {}
        self.current_search_term = ""

    def compose(self) -> ComposeResult:
        yield Header()

        with Container(id="search-container"):
            with Vertical():
                yield Static("Search Results", id="results-title")
                yield ListView(id="results-list", classes="results-list")

        yield Footer()

    def action_quit(self) -> None:
        self.app.exit()

    def action_progress(self) -> None:
        app = typing.cast(NjuptSmartclassDownloaderApp, self.app)
        app.push_screen(ProgressScreen())

    def action_search(self) -> None:
        def handle_search_result(search_term: Optional[str]) -> None:
            if search_term is not None:
                self.current_search_term = search_term
                self.perform_search(search_term)

        self.app.push_screen(
            SearchInputModal(self.current_search_term), handle_search_result
        )

    def perform_search(self, search_term: str) -> None:
        # Import here to avoid circular imports
        from njupt_smartclass_downloader.app import NjuptSmartclassDownloaderApp

        app = typing.cast(NjuptSmartclassDownloaderApp, self.app)
        if app.smartclass is None:
            self.app.notify(
                "Internal error: Smartclass not initialized.", severity="error"
            )
            return

        resources = list(
            app.smartclass.search_video_all(
                NjuptSmartclassVideoSearchCondition(title_key=search_term)
            )
        )
        self.load_data(resources)
        if not resources:
            self.app.notify("No resources found.", severity="information")
        else:
            self.app.notify(
                f"Found {len(resources)} resources.", severity="information"
            )

    def load_data(self, new_resources: List[NjuptSmartclassVideoSummary]) -> None:
        self.resources = new_resources
        self.video_items = {}

        results_list = self.query_one("#results-list", ListView)
        results_list.clear()

        for resource in self.resources:
            item = VideoListItem(resource, False)
            self.video_items[resource.id] = item
            results_list.append(item)

    def on_list_view_selected(self, event: ListView.Selected) -> None:
        if event.item and isinstance(event.item, VideoListItem):
            event.item.toggle_selection()

    def action_toggle_selection(self) -> None:
        results_list = self.query_one("#results-list", ListView)
        if results_list.highlighted_child is not None:
            highlighted_item = results_list.highlighted_child
            if isinstance(highlighted_item, VideoListItem):
                highlighted_item.toggle_selection()

    def action_select_all(self) -> None:
        for item in self.video_items.values():
            item.set_selection(True)

    def action_select_none(self) -> None:
        for item in self.video_items.values():
            item.set_selection(False)

    def action_download(self) -> None:
        selected_items = [
            item for item in self.video_items.values() if item.is_selected
        ]
        if not selected_items:
            self.app.notify("No resources selected for download.", severity="warning")
            return

        def handle_download_options(
            options: Optional[app_task.DownloadOptions],
        ) -> None:
            if options is None:
                return  # User cancelled

            if not options.type_filter:
                self.app.notify(
                    "Please select at least one video type to download.",
                    severity="warning",
                )
                return

            app = typing.cast(NjuptSmartclassDownloaderApp, self.app)

            for item in selected_items:
                resource = item.video
                try:
                    if resource.start_time.date() != resource.stop_time.date():
                        sanitized_time_str = (
                            resource.start_time.strftime("%Y%m%d%H%M")
                            + "_"
                            + resource.stop_time.strftime("%Y%m%d%H%M")
                        )
                    else:
                        sanitized_time_str = (
                            resource.start_time.strftime("%Y%m%d %H%M")
                            + "_"
                            + resource.stop_time.strftime("%H%M")
                        )
                    local_path = os.path.join(
                        ".",
                        "SmartclassDownload",
                        sanitize(resource.course_name),
                        sanitized_time_str,
                    )
                    app.task_manager.submit_task(
                        app_task.IndexTask(
                            title=f"{resource.course_name} - {sanitized_time_str}",
                            video_id=resource.id,
                            local_path=local_path,
                            cookies=app.session.cookies.copy(),
                            options=options,
                        )
                    )
                except Exception as e:
                    self.app.notify(
                        f"Failed to add task for {resource.title}: {str(e)}",
                        severity="error",
                    )

            app.push_screen(ProgressScreen())

        # Show download options modal
        self.app.push_screen(DownloadOptionsModal(), handle_download_options)
