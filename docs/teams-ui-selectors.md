# Teams UI selector maintenance

Microsoft Teams can change its DOM without changing what the exporter is meant to do. This project therefore separates **UI location knowledge** from **export behavior**.

## Decision rule

If the exporter logic is still correct but Teams moved or renamed DOM elements, change the selector configuration under `config/`.

Change `src/main.py` only when the exporter behavior itself must change: for example how chats are detected, how messages are collected, how images are captured, or how exports are written.

## How configuration selection works

`src/main.py` searches the dated `config/*.ini` files newest-first. For each file it reads `app_shell_selector`; the first configuration whose selector exists in the current Teams page becomes the active configuration.

This means older configuration files can remain as understandable fallbacks while a newer dated file describes a newer Teams UI.

## Updating selectors

1. Inspect the current Teams DOM in browser developer tools.
2. Prefer stable attributes such as `data-tid` or `data-testid` over fragile visual structure.
3. Copy the newest configuration to a new dated file rather than rewriting history when the UI generation has materially changed.
4. Change only selectors that are actually affected.
5. Run the exporter with `--debug`, navigate to a chat, and confirm that it reports the expected configuration and can detect/export messages.

## Where to look in code

The two most relevant places in `src/main.py` are:

- `Config`, which maps the `[Selectors]` values into runtime attributes;
- `find_and_load_config`, which scans configuration files and selects the first one matching the current Teams DOM.

For deeper implementation history and architectural rationale, read `CONTRIBUTING.md` if needed.
