from typing import Optional, List, Tuple

import textual
from textual.app import ComposeResult
from textual.widgets import Button, Label, SelectionList
from textual.widgets.selection_list import Selection
from textual.containers import Container, Horizontal, Vertical, ScrollableContainer
from textual.screen import ModalScreen
from textual.binding import Binding

from njupt_smartclass_downloader.app_task import DownloadOptions


class DownloadOptionsModal(ModalScreen):
    BINDINGS = [
        Binding("enter", "submit", "Download", show=True),
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    CSS_PATH = "../styles/download-options-modal.tcss"

    def __init__(
        self, current_options: Optional[DownloadOptions] = None, *args, **kwargs
    ):
        super().__init__(*args, **kwargs)
        if current_options is None:
            current_options = DownloadOptions()
        self.current_options = current_options

    def compose(self) -> ComposeResult:
        with Container(id="download-options-modal-container"):
            yield Label("Download Options", classes="modal-title")

            all_options = [
                Selection(
                    "VGA (Screen Recording)",
                    "VGA",
                    "VGA" in self.current_options.type_filter,
                ),
                Selection(
                    "Video 1", "Video1", "Video1" in self.current_options.type_filter
                ),
                Selection(
                    "Video 2", "Video2", "Video2" in self.current_options.type_filter
                ),
                Selection(
                    "Video 3", "Video3", "Video3" in self.current_options.type_filter
                ),
                Selection(
                    "Extract Slides from VGA",
                    "extract-slides",
                    self.current_options.extract_slides,
                ),
            ]

            yield SelectionList[str](*all_options, id="download-options-selection")

            with Horizontal(id="modal-buttons"):
                yield Button("Download", variant="primary", id="modal-download-btn")
                yield Button("Cancel", variant="default", id="modal-cancel-btn")

    def on_mount(self) -> None:
        self.query_one("#modal-download-btn").focus()

    @textual.on(Button.Pressed, "#modal-download-btn")
    def action_submit(self) -> None:
        options = self._collect_options()
        self.dismiss(options)

    @textual.on(Button.Pressed, "#modal-cancel-btn")
    def action_cancel(self) -> None:
        self.dismiss(None)

    def _collect_options(self) -> DownloadOptions:
        # Get selected options from SelectionList
        selection = self.query_one("#download-options-selection", SelectionList)
        selected_values = list(selection.selected)

        # Separate video types from extract slides option
        type_filter = [
            value
            for value in selected_values
            if value in ["VGA", "Video1", "Video2", "Video3"]
        ]
        extract_slides = "extract-slides" in selected_values

        return DownloadOptions(type_filter=type_filter, extract_slides=extract_slides)
