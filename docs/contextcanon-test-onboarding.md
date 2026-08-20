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

To refresh the installed tool after the ContextCanon branch changes, run the `uv tool install` command again.

## 2. Check out the experiment branch

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

## 9. First LLM comparison

After restoring a clean compiled state, use the project through a real agent harness.

### Ordinary task

Ask something unrelated to Teams UI selectors, for example:

> Where is the default output directory defined? Analyze only; do not change anything.

The selector Topic should not be needed.

### Topic-triggering task

Then ask:

> After a Teams update, a chat is no longer detected. Where should I first look for an adjustment? Analyze only; do not change anything. At the end, briefly state which additional ContextCanon targets you used.

Expected behavior: the agent should use the selector-maintenance Topic and distinguish a selector-only Teams UI change from a change that genuinely requires Python logic changes.

## 10. What to evaluate

The experiment is successful only if it improves the real working experience. Pay particular attention to:

- whether `CONTEXT.src.md` is pleasant to read and maintain;
- whether `CONTEXT.md` contains the right amount of always-loaded information;
- whether Topic resources appear only when relevant;
- whether `CONTEXT/` is understandable rather than clutter;
- whether `.context/` can remain safely ignorable during normal work;
- whether the LLM becomes more targeted without receiving unnecessary project material.

Record confusing or unnecessary behavior rather than working around it. The point of this experiment is to let the real project shape the next ContextCanon iteration.
