"""Tests for the Textual TUI, driven through Textual's test pilot."""
import asyncio
import json
import unittest
from unittest import mock

from textual.widgets import Static, TextArea

from tui import PasswordApp, RecoverInputScreen, ResultScreen

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


if __name__ == "__main__":
    unittest.main()
