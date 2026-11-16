"""
Terminal UI for the password generation & recovery system.
"""
import shutil
import subprocess
from datetime import datetime
from typing import Literal, Optional

from textual import work
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.color import Gradient
from textual.containers import Center, Horizontal, Vertical
from textual.screen import ModalScreen, Screen
from textual.widgets import Button, Label, ProgressBar, Static, TextArea
from textual.worker import get_current_worker

import config
from background import compute_password
from password_generator import generate_random_seed
from password_recovery import ComputationCancelled
from progress import progress_stats
from utils import format_keys, parse_keys, validate_keys

MINT = "#7ee8b5"
VIOLET = "#b39cf5"
PINK = "#f59ac0"
PEACH = "#f9b98a"

KEYS_ERROR = (
    "Those don't look like recovery keys. Paste the whole JSON block "
    "with \"seed\" and \"iterations\"."
)


def copy_text(app: App, text: str) -> None:
    """Copy text to the clipboard: pbcopy on macOS, else the terminal (OSC 52)."""
    if shutil.which("pbcopy"):
        subprocess.run(["pbcopy"], input=text, text=True, check=False)
    else:
        app.copy_to_clipboard(text)
    app.notify("Copied to clipboard")


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
        if event.button.id == "generate":
            self.app.switch_screen(ComputingScreen("generate"))
        elif event.button.id == "recover":
            self.app.switch_screen(RecoverInputScreen())
        elif event.button.id == "quit":
            self.app.exit(return_code=0)


class RecoverInputScreen(Screen):
    """Paste recovery keys to start a recovery."""

    BINDINGS = [Binding("escape", "back", "Back", show=False)]

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="recover-panel", classes="panel"):
                yield Static("recover from keys", classes="title violet-text")
                yield Static("paste the JSON block you saved when generating", classes="subtitle")
                yield TextArea(id="keys", soft_wrap=True)
                yield Static("", id="error")
                with Horizontal(classes="actions"):
                    yield Button("Back", id="back")
                    yield Button("Start recovery", id="start", classes="violet")
                yield Static("esc back", classes="footer-hint")

    def on_mount(self) -> None:
        self.query_one("#keys", TextArea).focus()

    def action_back(self) -> None:
        self.app.switch_screen(MenuScreen())

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.action_back()
        elif event.button.id == "start":
            self.start_recovery()

    def start_recovery(self) -> None:
        keys = parse_keys(self.query_one("#keys", TextArea).text.strip())
        if not keys or not validate_keys(keys) or not _is_hex(keys["seed"]):
            self.query_one("#error", Static).update(KEYS_ERROR)
            return
        self.app.switch_screen(ComputingScreen("recover", keys["seed"], keys["iterations"]))


def _is_hex(value: str) -> bool:
    try:
        bytes.fromhex(value)
    except ValueError:
        return False
    return True


UNSAVED_KEYS_WARNING = (
    "The recovery keys haven't been copied. Without them this password "
    "can't be recovered."
)


class ConfirmQuitScreen(ModalScreen[bool]):
    """Asks before throwing away a computation or its result."""

    BINDINGS = [Binding("escape", "dismiss(False)", "Cancel", show=False)]

    def __init__(
        self,
        title: str = "quit now?",
        message: str = "The computation will stop and its progress will be lost.",
        confirm_label: str = "Quit",
        cancel_label: str = "Keep going",
    ) -> None:
        super().__init__()
        self.title_text = title
        self.message = message
        self.confirm_label = confirm_label
        self.cancel_label = cancel_label

    def compose(self) -> ComposeResult:
        with Vertical(id="confirm-panel", classes="panel"):
            yield Static(self.title_text, classes="title peach-text")
            yield Static(self.message, classes="subtitle")
            with Horizontal(classes="actions"):
                yield Button(self.cancel_label, id="no", classes="mint")
                yield Button(self.confirm_label, id="yes", classes="pink")

    def on_mount(self) -> None:
        self.query_one("#no", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        self.dismiss(event.button.id == "yes")


class ComputingScreen(Screen):
    """Live progress while the proof-of-work hashing runs."""

    BINDINGS = [Binding("q", "confirm_quit", "Quit")]

    def __init__(
        self,
        mode: Literal["generate", "recover"],
        seed: Optional[str] = None,
        iterations: Optional[int] = None,
    ) -> None:
        super().__init__()
        self.mode = mode
        self.seed = seed
        self.iterations = iterations

    def compose(self) -> ComposeResult:
        title = "generating password" if self.mode == "generate" else "recovering password"
        status = "calibrating speed…" if self.mode == "generate" else "starting…"
        with Center():
            with Vertical(id="computing-panel", classes="panel"):
                yield Static(title, classes="title")
                yield Static(status, id="status", classes="subtitle")
                yield ProgressBar(
                    id="progress",
                    total=100,
                    show_eta=False,
                    show_percentage=False,
                    gradient=Gradient.from_colors(MINT, VIOLET, PINK, PEACH),
                )
                yield Static("0.000%", id="percent")
                for stat_id, name in (
                    ("speed", "speed"),
                    ("elapsed", "elapsed"),
                    ("left", "time left"),
                    ("finish", "done around"),
                ):
                    with Horizontal(classes="stat"):
                        yield Label(name, classes="stat-name")
                        yield Static("—", id=stat_id, classes="stat-value")
                yield Static("q quit", classes="footer-hint")

    def on_mount(self) -> None:
        self.compute()

    def action_confirm_quit(self) -> None:
        def quit_if_confirmed(confirmed: Optional[bool]) -> None:
            if confirmed:
                # The worker sees the cancellation within 0.1 s and stops the hashing process
                self.workers.cancel_all()
                self.app.exit(return_code=0)

        self.app.push_screen(ConfirmQuitScreen(), quit_if_confirmed)

    @work(thread=True, exclusive=True)
    def compute(self) -> None:
        # This thread only waits on the hashing process, so it barely
        # competes with the UI; the hashing itself runs in another process.
        worker = get_current_worker()

        def on_progress(done: int, total: int, elapsed: float) -> None:
            self.app.call_from_thread(self.show_progress, done, total, elapsed)

        try:
            if self.mode == "generate":
                # Same steps as password_generator.create_password_with_keys
                seed = generate_random_seed()
                iterations = config.calibrate_iterations(verbose=False)
                keys_json: Optional[str] = format_keys(seed, iterations)
            else:
                seed, iterations, keys_json = self.seed, self.iterations, None
            password: Optional[str] = compute_password(
                seed, iterations, on_progress, lambda: worker.is_cancelled
            )
        except ComputationCancelled:
            return
        except RuntimeError:
            password = None
        if not worker.is_cancelled:
            self.app.call_from_thread(self.finish, password, keys_json)

    def show_progress(self, done: int, total: int, elapsed: float) -> None:
        stats = progress_stats(done, total, elapsed, datetime.now())
        self.query_one("#status", Static).update("hashing")
        self.query_one("#progress", ProgressBar).update(progress=stats.fraction * 100)
        self.query_one("#percent", Static).update(stats.percent)
        self.query_one("#speed", Static).update(stats.speed)
        self.query_one("#elapsed", Static).update(stats.elapsed)
        self.query_one("#left", Static).update(stats.left)
        self.query_one("#finish", Static).update(stats.finish)

    def finish(self, password: Optional[str], keys_json: Optional[str]) -> None:
        if password is None:
            self.app.notify("The computation failed unexpectedly.", severity="error")
            self.app.switch_screen(MenuScreen())
            return
        self.app.switch_screen(ResultScreen(password, keys_json))


class ResultScreen(Screen):
    """The finished password, plus recovery keys after generation."""

    def __init__(self, password: str, keys_json: Optional[str] = None) -> None:
        super().__init__()
        self.password = password
        self.keys_json = keys_json
        self.keys_copied = False

    def compose(self) -> ComposeResult:
        with Center():
            with Vertical(id="result-panel", classes="panel"):
                yield Static("✓ password ready", classes="title")
                yield Static("your password", classes="label")
                with Horizontal(classes="secret-row"):
                    yield Static(self.password, id="password", classes="secret")
                    yield Button("Copy", id="copy-password", classes="mint")
                if self.keys_json is not None:
                    yield Static("recovery keys", classes="label")
                    with Horizontal(classes="secret-row"):
                        yield Static(self.keys_json, id="keys-json", classes="secret keys")
                        yield Button("Copy", id="copy-keys", classes="violet")
                    yield Static(
                        "Save these keys somewhere safe. Without them this "
                        "password can't be recovered.",
                        classes="warning",
                    )
                with Horizontal(classes="actions"):
                    yield Button("Back to menu", id="menu", classes="peach")

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "copy-password":
            copy_text(self.app, self.password)
        elif event.button.id == "copy-keys" and self.keys_json is not None:
            copy_text(self.app, self.keys_json)
            self.keys_copied = True
        elif event.button.id == "menu":
            self.back_to_menu()

    def has_unsaved_keys(self) -> bool:
        return self.keys_json is not None and not self.keys_copied

    def back_to_menu(self) -> None:
        if not self.has_unsaved_keys():
            self.app.switch_screen(MenuScreen())
            return

        def leave_if_confirmed(confirmed: Optional[bool]) -> None:
            if confirmed:
                self.app.switch_screen(MenuScreen())

        self.app.push_screen(
            ConfirmQuitScreen("leave without the keys?", UNSAVED_KEYS_WARNING, "Leave", "Stay"),
            leave_if_confirmed,
        )

    def action_confirm_quit(self) -> None:
        if not self.has_unsaved_keys():
            self.app.exit(return_code=0)
            return

        def quit_if_confirmed(confirmed: Optional[bool]) -> None:
            if confirmed:
                self.app.exit(return_code=0)

        self.app.push_screen(
            ConfirmQuitScreen("quit without the keys?", UNSAVED_KEYS_WARNING, "Quit", "Stay"),
            quit_if_confirmed,
        )


class PasswordApp(App):
    """The password system TUI."""

    CSS_PATH = "tui.tcss"
    TITLE = "password system"

    def on_mount(self) -> None:
        self.push_screen(MenuScreen())

    async def action_quit(self) -> None:
        """ctrl+q and the command palette's Quit: ask first where work could be lost."""
        if isinstance(self.screen, ConfirmQuitScreen):
            return  # already asking
        confirm_quit = getattr(self.screen, "action_confirm_quit", None)
        if confirm_quit is not None:
            confirm_quit()
        else:
            self.exit(return_code=0)


def run() -> None:
    """Run the TUI."""
    PasswordApp().run()


if __name__ == "__main__":
    run()
