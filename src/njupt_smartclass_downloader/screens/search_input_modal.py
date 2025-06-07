from pydoc import text
from typing import Optional

import textual
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label
from textual.containers import Container, Horizontal
from textual.screen import ModalScreen
from textual.binding import Binding


class SearchInputModal(ModalScreen):
    BINDINGS = [
        Binding("escape", "cancel", "Cancel", show=True),
    ]

    CSS_PATH = "../styles/search-input-modal.tcss"

    def __init__(self, current_search: str = "", *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.current_search = current_search

    def compose(self) -> ComposeResult:
        with Container(id="search-modal-container"):
            yield Label("Enter search keywords:", classes="modal-label")
            yield Input(
                placeholder="Enter search keywords...",
                value=self.current_search,
                id="modal-search-input",
                classes="modal-input",
            )
            with Horizontal(id="modal-buttons"):
                yield Button("Search", variant="primary", id="modal-search-btn")
                yield Button("Cancel", variant="default", id="modal-cancel-btn")

    def on_mount(self) -> None:
        self.query_one("#modal-search-input", Input).focus()

    @textual.on(Button.Pressed, "#modal-search-btn")
    @textual.on(Input.Submitted, "#modal-search-input")
    def action_submit(self) -> None:
        search_term = self.query_one("#modal-search-input", Input).value
        self.dismiss(search_term)

    @textual.on(Button.Pressed, "#modal-cancel-btn")
    def action_cancel(self) -> None:
        self.dismiss(None)
