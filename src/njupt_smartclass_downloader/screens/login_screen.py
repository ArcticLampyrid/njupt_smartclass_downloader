import typing
import textual
from textual.app import ComposeResult
from textual.widgets import Button, Input, Label, Header, Footer
from textual.containers import Container, Horizontal, Vertical
from textual.screen import Screen
from textual.binding import Binding

from njupt_smartclass_downloader.njupt_smartclass import NjuptSmartclass
from njupt_smartclass_downloader.njupt_sso import NjuptSso
from njupt_smartclass_downloader.screens.search_screen import SearchScreen
from njupt_smartclass_downloader.app import NjuptSmartclassDownloaderApp


class LoginScreen(Screen):
    BINDINGS = [
        Binding("escape", "quit", "Quit", show=True),
    ]

    CSS_PATH = "../styles/login.tcss"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.username = ""
        self.password = ""

    def compose(self) -> ComposeResult:
        yield Header()
        with Container(id="login-container"):
            with Vertical(id="login-form"):
                yield Label("Username:", classes="form-label")
                yield Input(
                    placeholder="Enter your username",
                    id="username-input",
                    classes="form-input",
                )
                yield Label("Password:", classes="form-label")
                yield Input(
                    placeholder="Enter your password",
                    password=True,
                    id="password-input",
                    classes="form-input",
                )
                with Horizontal(id="login-buttons"):
                    yield Button("Login", variant="primary", id="login-btn")
                    yield Button("Quit", variant="error", id="quit-btn")
        yield Footer()

    @textual.on(Input.Submitted, "#username-input")
    def focus_password_input(self) -> None:
        self.query_one("#password-input", Input).focus()

    @textual.on(Button.Pressed, "#login-btn")
    @textual.on(Input.Submitted, "#password-input")
    def action_login(self) -> None:
        username = self.query_one("#username-input", Input).value
        password = self.query_one("#password-input", Input).value

        if not username or not password:
            self.app.notify(
                "Please enter both username and password.", severity="error"
            )
            return

        app = typing.cast(NjuptSmartclassDownloaderApp, self.app)
        sso = NjuptSso(app.session)
        try:
            app.session.cookies.clear()
            sso.login(username, password)
            sso.grant_service("https://njupt.smartclass.cn/SystemSpace/Redirect.aspx")
            app.smartclass = NjuptSmartclass(app.session)
        except Exception as e:
            self.app.notify(f"Login failed: {str(e)}", severity="error")
            return
        app.switch_screen(SearchScreen())

    @textual.on(Button.Pressed, "#quit-btn")
    def action_quit(self) -> None:
        self.app.exit()
