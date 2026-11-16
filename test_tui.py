"""Tests for the Textual TUI, driven through Textual's test pilot."""
import unittest

from tui import PasswordApp

SIZE = (100, 32)


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


if __name__ == "__main__":
    unittest.main()
