# ContextCanon test onboarding

This temporary guide is the shared reference for the first external ContextCanon experiment in this repository. It can be removed after the workflow becomes routine.

## 1. Install the current ContextCanon compiler with uv

ContextCanon is a command-line tool, so install it as an isolated uv tool rather than into this project's Python environment:

```powershell
uv tool install "git+https://github.com/SomeSunlight/context-canon.git@agent/compiler-walking-skeleton"
```

Verify that the command is available:

```powershell
contextcanon --help
```

If uv reports that its tool bin directory is not on `PATH`, run:

```powershell
uv tool update-shell
```

and open a new terminal.

The compiler branch is changing during this experiment. To refresh the installed tool after that branch changes, run the same `uv tool install` command again. uv replaces the existing isolated tool installation.

## 2. Check out the experiment branch

First change to the local checkout of this repository, then run:

```powershell
git fetch
git switch agent/contextcanon-hello-world
git status
```

Before the first build, the experiment intentionally contains only human-authored ContextCanon input:

- `CONTEXT.src.md`
- `docs/teams-ui-selectors.md`
- this temporary onboarding guide

Generated ContextCanon output is deliberately not committed yet.

## 3. Confirm the expected pre-build failure

Run:

```powershell
contextcanon check .
```

Expected result: the command exits non-zero and reports missing generated files. This is intentional: the source exists, but the Official Context Package has not been built yet.

## 4. Build the Official Context Package

```powershell
contextcanon build .
```

Then inspect:

```powershell
git status
git diff
```

The compiler should create derived files such as:

```text
CONTEXT.md
CONTEXT/
.context/context.yaml
AGENTS.md
.goosehints
.github/copilot-instructions.md
```

Do not edit these generated files as source. The human-editable truth remains `CONTEXT.src.md` plus its referenced project resources.

## 5. Verify determinism

```powershell
contextcanon check .
contextcanon build .
```

Expected result:

- `check` reports the Node as clean;
- the second `build` reports no changes.

## 6. Inspect progressive disclosure

Compare:

```text
CONTEXT.src.md
CONTEXT.md
CONTEXT/
.context/context.yaml
```

`CONTEXT.md` is intentionally self-describing. It should make these mechanics clear without relying on harness-specific knowledge:

- Rules apply to every task in the Node.
- For the current task, evaluate each Topic condition.
- When a Topic matches, load every Required target before continuing.
- Load Optional targets only when useful.

For the Topic **Teams UI selector maintenance**, the important relationship is:

```text
ordinary task
    -> compact CONTEXT.md only

Teams selector task
    -> docs/teams-ui-selectors.md
    -> config/teams_2025-09-26.ini
    -> optionally CONTRIBUTING.md
```

The `.ini` file is deliberately a real non-Markdown Context resource. It should not be loaded for unrelated work.

## 7. Test drift detection

Temporarily edit the generated `CONTEXT.md` directly and then run:

```powershell
contextcanon check .
```

Expected result: ContextCanon reports `CONTEXT.md` as changed.

Restore the deterministic result with:

```powershell
contextcanon build .
contextcanon check .
```

## 8. Test an authored Context change

Make a small wording change to one Rule in `CONTEXT.src.md`, then run:

```powershell
contextcanon build .
git diff
```

Confirm that the derived Official Context and machine-state digest change while `CONTEXT.src.md` remains the authored source.

## 9. First LLM comparison with GitHub Copilot in PyCharm

### Refresh the compiler first

If ContextCanon was installed before Copilot adapter support was added, refresh the tool and rebuild:

```powershell
uv tool install "git+https://github.com/SomeSunlight/context-canon.git@agent/compiler-walking-skeleton"
contextcanon build .
contextcanon check .
```

Confirm that this file now exists:

```text
.github/copilot-instructions.md
```

GitHub Copilot Chat in JetBrains automatically uses this repository-wide instruction file. It is a thin generated adapter that points Copilot to `CONTEXT.md`; the project context itself remains harness-neutral.

When Copilot answers, inspect the response's **References** list. `.github/copilot-instructions.md` should appear there when JetBrains applied the repository instructions.

### Ordinary task

Ask something unrelated to Teams UI selectors, for example:

> Where is the default output directory defined? Analyze only; do not change anything.

Expected behavior:

- Copilot enters through `.github/copilot-instructions.md` and reads `CONTEXT.md`.
- Both always-on Rules apply.
- The selector-maintenance Topic does not match, so its Required selector resources should not be needed.

### Topic-triggering task

Then ask:

> After a Teams update, a chat is no longer detected. Where should I first look for an adjustment? Analyze only; do not change anything. At the end, briefly state which additional ContextCanon targets you used.

Expected behavior:

- Copilot evaluates the Topic conditions in `CONTEXT.md`.
- **Teams UI selector maintenance** matches.
- It reads the Required selector-maintenance guide and current `.ini` configuration before concluding what should change.
- It distinguishes a selector-only Teams UI change from a change that genuinely requires Python logic changes.
- `CONTRIBUTING.md` remains Optional and should be read only if deeper architectural/history context is useful.

## 10. What to evaluate

The experiment is successful only if it improves the real working experience. Pay particular attention to:

- whether `CONTEXT.src.md` is pleasant to read and maintain;
- whether `CONTEXT.md` contains the right amount of always-loaded information;
- whether the loading semantics are understandable directly from `CONTEXT.md`;
- whether Topic resources appear only when relevant;
- whether `CONTEXT/` is understandable rather than clutter;
- whether `.context/` can remain safely ignorable during normal work;
- whether the Copilot adapter reliably enters ContextCanon without duplicating project context;
- whether the LLM becomes more targeted without receiving unnecessary project material.

Record confusing or unnecessary behavior rather than working around it. The point of this experiment is to let the real project shape the next ContextCanon iteration.
