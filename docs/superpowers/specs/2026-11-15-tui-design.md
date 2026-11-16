# TUI for Password System — design

## Intent
Replace the plain `input()`/`print()` menu with a terminal UI the owner enjoys
using: simple, aesthetic, colorful, roomy. No new features beyond what makes the
existing flows nicer — except copy buttons, because a generated password was
previously lost when its terminal output disappeared.

## Goals
- Same three flows: generate, recover from keys, quit.
- The computing screen (~15 h of waiting) is the centerpiece: big progress bar,
  speed, elapsed, time left, expected finish clock time.
- Colorful but coherent; generous spacing (nothing cramped, especially the
  computing screen).
- Result screen shows password and recovery keys with copy-to-clipboard buttons.

## Non-goals / anti-goals
- Must NOT change password derivation. Existing recovery keys must produce the
  same passwords (guarded by `test_passwords.py`).
- No measurable slowdown of hashing from the UI.
- No storing passwords or keys on disk.
- Nothing fancy beyond that (no themes menu, no settings, no history).

## Approaches
- **Textual (picked):** full terminal app framework — screens, real text area for
  pasting keys, buttons, mouse, smooth live updates. One dependency.
- Rich: prettier printing and live progress, but key pasting stays clunky.
- curses: no dependency, but far more code for a worse look.

## Design
- New `tui.py` (Textual app) becomes the entry point; `main.py` launches it.
  The old prompt-based CLI stays reachable as a fallback (`main.py --plain`).
- Screens: Menu → (Generate | Recover-input) → Computing → Result.
- Look: dark background; mint green primary (the app's existing accent) with
  violet/pink and peach secondary accents; rounded panels; centered content
  with wide padding and blank lines between stat rows.
- Computing: gradient progress bar; stats on separate spaced rows: speed,
  elapsed, ~time left, "done around HH:MM". Quit asks for confirmation.
- Hashing runs in a background worker using the existing chunked
  `hash_chain` loop; progress is posted to the UI between chunks.
- Result: password and keys in panels, each with a Copy button (macOS `pbcopy`
  via Textual's clipboard support), plus the existing "save your keys" warning.
- Recover-input: multiline box for the JSON keys, validated with the existing
  `parse_keys`/`validate_keys`; errors shown inline.

## Left to the builder
Exact hex colors, widget choices, key bindings, layout sizes.
