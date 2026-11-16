"""
Terminal UI for the password generation & recovery system.
"""
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Center, Horizontal, Vertical
from textual.screen import Screen
from textual.widgets import Button, Label, Static


class MenuScreen(Screen):
    """Start screen: generate, recover or quit."""

    BINDINGS = [
        Binding("up", "app.focus_previous", "Up", show=False),
        Binding("down", "app.focus_next", "Down", show=False),
    ]

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="menu", classes="panel"):
                yield Static("password system", classes="title")
                yield Static("proof-of-work passwords", classes="subtitle")
                with Horizontal(classes="option"):
                    yield Button("Generate new password", id="generate", classes="mint")
                    yield Label("~15 h", classes="hint")
                with Horizontal(classes="option"):
                    yield Button("Recover from keys", id="recover", classes="violet")
                    yield Label("~15 h", classes="hint")
                with Horizontal(classes="option"):
                    yield Button("Quit", id="quit", classes="peach")
                    yield Label("", classes="hint")
                yield Static("↑↓ move  ·  enter select", classes="footer-hint")

    def on_mount(self) -> None:
        self.query_one("#generate", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "quit":
            self.app.exit(return_code=0)


class PasswordApp(App):
    """The password system TUI."""

    CSS_PATH = "tui.tcss"
    TITLE = "password system"

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())


def run() -> None:
    """Run the TUI."""
    PasswordApp().run()


if __name__ == "__main__":
    run()
