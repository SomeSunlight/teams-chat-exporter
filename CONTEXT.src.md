# Teams Chat Exporter — Local Context Source
<!-- ctx:node id="433a61e0-a960-412c-91f9-d95f9ad35af3" version="0.1.0-experiment" adapters="agents,goose" -->

> [!IMPORTANT]
> This is the human-edited ContextCanon source for the experiment branch.
> Generated `CONTEXT.md`, `CONTEXT/`, `.context/`, `AGENTS.md`, and `.goosehints` do not belong here yet: the first test is to let the compiler create them.

## Rules

### Architecture

- **Keep Teams UI selectors in configuration:** CSS/selectors that describe the current Teams DOM belong in dated files under `config/`; do not hard-code a UI selector in `src/main.py` when the change is only a Teams markup change.
  Why: Teams changes its UI independently of exporter behavior; dated selector files let UI maintenance remain data-driven and keep working configurations understandable.
  <!-- ctx:rule id="TCE-001" -->

### Privacy

- **Keep private runtime data out of the repository:** Exported chats and persistent browser-session data must remain outside version control.
  Why: They can contain personal conversations, authentication state, cookies, and other sensitive data that are not project source.
  <!-- ctx:rule id="TCE-002" -->

## Topics

### Teams UI selector maintenance

When Teams changes its page structure, chat detection fails, messages can no longer be located, or CSS/selectors need maintenance:

Required:
- Resource: `docs/teams-ui-selectors.md`
- Resource: `config/teams_2025-09-26.ini`

Optional:
- Resource: `CONTRIBUTING.md`
<!-- ctx:topic id="TCE-TOPIC-SELECTORS" -->
