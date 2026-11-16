"""Tests for the Textual TUI, driven through Textual's test pilot."""
import asyncio
import json
import time
import unittest
from unittest import mock

from textual.widgets import ProgressBar, Static, TextArea
from textual.widgets._progress_bar import Bar

from tui import (
    ComputingScreen,
    ConfirmQuitScreen,
    MenuScreen,
    PasswordApp,
    RecoverInputScreen,
    ResultScreen,
)

SIZE = (100, 32)
KNOWN_KEYS = json.dumps({"seed": "ab" * 32, "iterations": 1000}, indent=2)


async def wait_for_screen(pilot, screen_type, timeout=10.0):
    """Let the app run until its active screen is of screen_type."""
    async def poll():
        while not isinstance(pilot.app.screen, screen_type):
            await pilot.pause(0.05)
        return pilot.app.screen

    return await asyncio.wait_for(poll(), timeout)


def text_of(screen, selector):
    return str(screen.query_one(selector, Static).content)


async def open_recover_and_submit(pilot, keys_text):
    await pilot.click("#recover")
    screen = await wait_for_screen(pilot, RecoverInputScreen)
    screen.query_one("#keys", TextArea).text = keys_text
    await pilot.click("#start")
    await pilot.pause()
    return screen


class MenuTest(unittest.IsolatedAsyncioTestCase):
    async def test_menu_shows_options(self):
        app = PasswordApp()
        async with app.run_test(size=SIZE) as pilot:
            screen = pilot.app.screen
            for button_id in ("#generate", "#recover", "#quit"):
                self.assertIsNotNone(screen.query_one(button_id))

    async def test_quit_from_menu_exits(self):
        app = PasswordApp()
        async with app.run_test(size=SIZE) as pilot:
            await pilot.click("#quit")
            await pilot.pause()
        self.assertEqual(app.return_code, 0)
        self.assertFalse(app.is_running)


class RecoverFlowTest(unittest.IsolatedAsyncioTestCase):
    async def test_recover_known_key(self):
        async with PasswordApp().run_test(size=SIZE) as pilot:
            await open_recover_and_submit(pilot, KNOWN_KEYS)
            result = await wait_for_screen(pilot, ResultScreen)
            self.assertIn("f8442cf378e8c06", text_of(result, "#password"))

    async def test_keys_with_whitespace_accepted(self):
        async with PasswordApp().run_test(size=SIZE) as pilot:
            await open_recover_and_submit(pilot, "\n  " + KNOWN_KEYS + "  \n\n")
            result = await wait_for_screen(pilot, ResultScreen)
            self.assertIn("f8442cf378e8c06", text_of(result, "#password"))

    async def test_invalid_keys_show_error(self):
        async with PasswordApp().run_test(size=SIZE) as pilot:
            screen = await open_recover_and_submit(pilot, "not json")
            self.assertIs(pilot.app.screen, screen)
            self.assertNotEqual(text_of(screen, "#error").strip(), "")


class GenerateFlowTest(unittest.IsolatedAsyncioTestCase):
    async def test_generate_flow(self):
        with mock.patch("config.calibrate_iterations", return_value=1000):
            async with PasswordApp().run_test(size=SIZE) as pilot:
                await pilot.click("#generate")
                result = await wait_for_screen(pilot, ResultScreen)
                self.assertRegex(text_of(result, "#password"), r"\b[0-9a-f]{15}\b")
                self.assertIn('"iterations": 1000', text_of(result, "#keys-json"))


class CopyTest(unittest.IsolatedAsyncioTestCase):
    async def test_copy_falls_back_without_pbcopy(self):
        with mock.patch("tui.shutil.which", return_value=None), mock.patch.object(
            PasswordApp, "copy_to_clipboard"
        ) as copy:
            async with PasswordApp().run_test(size=SIZE) as pilot:
                await open_recover_and_submit(pilot, KNOWN_KEYS)
                await wait_for_screen(pilot, ResultScreen)
                await pilot.click("#copy-password")
                await pilot.pause()
        copy.assert_called_once_with("f8442cf378e8c06")


class QuitTest(unittest.IsolatedAsyncioTestCase):
    async def start_long_recovery(self, pilot):
        keys = json.dumps({"seed": "ab" * 32, "iterations": 2_000_000_000})
        await open_recover_and_submit(pilot, keys)
        screen = await wait_for_screen(pilot, ComputingScreen)

        async def first_update():
            while text_of(screen, "#percent") == "0.000%":
                await pilot.pause(0.05)

        await asyncio.wait_for(first_update(), 10)
        return screen

    async def test_quit_mid_computation_cancels(self):
        app = PasswordApp()

        async def run():
            async with app.run_test(size=SIZE) as pilot:
                await self.start_long_recovery(pilot)
                await pilot.press("q")
                await wait_for_screen(pilot, ConfirmQuitScreen)
                await pilot.click("#yes")
                await pilot.pause()

        await asyncio.wait_for(run(), 20)
        self.assertFalse(app.is_running)

    async def test_ui_stays_responsive_while_hashing(self):
        async with PasswordApp().run_test(size=SIZE) as pilot:
            await self.start_long_recovery(pilot)
            started = time.perf_counter()
            await pilot.press("q")
            await wait_for_screen(pilot, ConfirmQuitScreen)
            self.assertLess(time.perf_counter() - started, 0.5)
            await pilot.click("#yes")

    async def test_quit_declined_keeps_computing(self):
        async with PasswordApp().run_test(size=SIZE) as pilot:
            screen = await self.start_long_recovery(pilot)
            await pilot.press("q")
            await wait_for_screen(pilot, ConfirmQuitScreen)
            await pilot.click("#no")
            await wait_for_screen(pilot, ComputingScreen)
            self.assertIs(pilot.app.screen, screen)
            before = text_of(screen, "#percent")

            async def advanced():
                while text_of(screen, "#percent") == before:
                    await pilot.pause(0.1)

            await asyncio.wait_for(advanced(), 10)
            pilot.app.exit()


class LayoutTest(unittest.IsolatedAsyncioTestCase):
    async def test_progress_bar_track_is_visible(self):
        with mock.patch.object(ComputingScreen, "compute"):
            async with PasswordApp().run_test(size=SIZE) as pilot:
                await pilot.app.push_screen(ComputingScreen("recover", "ab" * 32, 1000))
                await pilot.pause()
                progress = pilot.app.screen.query_one(ProgressBar)
                track = progress.query_one(Bar)
                self.assertTrue(progress.region.contains_region(track.region))
                self.assertGreater(track.region.width, 0)

    async def test_every_panel_fits_80x24(self):
        screens = [
            MenuScreen(),
            RecoverInputScreen(),
            ComputingScreen("recover", "ab" * 32, 1000),
            ResultScreen("f8442cf378e8c06", '{"seed": "' + "ab" * 32 + '", "iterations": 1000}'),
        ]
        with mock.patch.object(ComputingScreen, "compute"):
            async with PasswordApp().run_test(size=(80, 24)) as pilot:
                for screen in screens:
                    await pilot.app.switch_screen(screen)
                    await pilot.pause()
                    panel = screen.query_one(".panel")
                    with self.subTest(screen=type(screen).__name__):
                        self.assertEqual(panel.max_scroll_y, 0)
                await pilot.app.push_screen(ConfirmQuitScreen())
                await pilot.pause()
                self.assertEqual(pilot.app.screen.query_one(".panel").max_scroll_y, 0)


if __name__ == "__main__":
    unittest.main()
