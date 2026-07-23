# CLAUDE.md

Guidance for working in this repository. Follow it exactly; it overrides
default behavior.

## What this project is

Device Tree Editor Lite: a focused fork of
[qualcomm/DTE](https://github.com/qualcomm/DTE) (the Qualcomm Device Tree
Editor). Distribution name and console command are `qdte-lite`; the import
package is `qdte_lite`.

It does one thing well: edit device trees and assemble/disassemble the
Qualcomm config-ELF containers that hold them (`xbl_config.elf`,
`uefi_dtbs.elf`, and similar). Two frontends: a headless CLI
(`qdte-lite --nogui`) and a Qt GUI.

Deliberately out of scope (do not re-add or extend):

- QUTS device programming and the NON-HLOS FAT browser. Removed.
- The tkinter GUI. Removed; PySide6 is the only GUI.
- Sectools signing. Removed; the tool only produces unsigned ELFs. Sign by
  invoking sectools directly on the output if needed. `--allow_unsigned` is
  kept as an accepted no-op so the existing CLI contract (CI, the meta-qcom
  capsule bbclass) keeps working.

Forked from upstream at `7e3e493` under BSD-3-Clause-Clear. Target version
`2.0.0`.

## Layout

```text
qdte_lite/__main__.py  console entry point (the qdte-lite command; python -m qdte_lite)
qdte_lite/core/        headless engine: flags, dtwrapper, fdt_backend (libfdt),
                  assemble/version_2_assemble, Autocmd, dtlogger, strvalues,
                  XBLConfig/ tool scripts. MUST NOT import any GUI toolkit.
qdte_lite/cli/         argparse and dispatch; headless.py is the --nogui path
qdte_lite/gui_qt/      Qt (PySide6) app: DtTreeModel over dtwrapper, mainwindow,
                  hexview, finddialog, elfsession, valueparse  ("qt" extra)
```

## Invariants, do not break these

- Headless never imports a GUI toolkit. `qdte_lite.core` and `qdte_lite.cli` must
  import with no PySide6 present; CI enforces this by running the nogui
  smoke on a PySide6-free interpreter. The GUI enters the process at exactly
  one lazy import in `qdte_lite/cli/main.py:_dispatch`.
- The DTB layer is libfdt (`qdte_lite/core/fdt_backend.py`), not pyfdt: a
  materialized tree plus `FdtSw` sequential-write emission, so output bytes
  are deterministic and undo/redo's SHA-256-of-bytes check holds. Do not
  reintroduce pyfdt.
- Spawn child interpreters via `sys.executable`, never a bare `python` (the
  XBLConfig tool scripts run as subprocesses; bare `python` is often absent
  on the target hosts).

## Build and dev, uv is the package manager

- Use uv for environments and installs: `uv venv`,
  `uv pip install -e ".[qt]"`, `uv build`.
- `pylibfdt` is sdist-only on PyPI, so building it needs swig at build time
  (`uv pip install swig` provides a prebuilt wheel; system swig also works).
  Yocto ships it prebuilt as `python3-dtc`.
- Extras: `qt` (PySide6, the GUI) and `all`. A plain install is
  headless-only.
- Entry points: the `qdte-lite` console script or `python -m qdte_lite`. There is no
  run-from-checkout launcher; install the package.
- (The CI workflow still installs with pip; it may be migrated to uv.)

## Testing

- Headless smoke, as CI runs it:
  `qdte-lite --nogui --input_file <elf> --output_path <dir> --output_file <name>
  --modify "<dtb>/<node>/<prop>=<val>"`, verified with `fdtdump --scan`.
- fdt backend selftest: `python -m qdte_lite.core._fdt_selftest --roundtrip
  <dtb...>`.
- Qt is offscreen-testable:
  `QT_QPA_PLATFORM=offscreen python -m qdte_lite.gui_qt._smoke ...`.
- CI is `.github/workflows/nogui-smoke.yml`: a `nogui-smoke` job (installed
  package, PySide6-free interpreter, real boot-image fixtures) and a
  `qt-offscreen` job (functional GUI exercise under the offscreen plugin).

## Code and documentation rules

- ASCII only. Do not use non-ASCII characters anywhere: source, docs, or
  commit messages. Write `--` not an em dash, `->` not an arrow, straight
  quotes, `...` not an ellipsis character.

## Commit conventions, follow exactly

- Conventional Commits. Prefix every subject with a type: `feat:`, `fix:`,
  `chore:`, `refactor:`, `docs:`, `ci:`, `build:`, `style:`, `test:`.
- Explain why, not what. The diff already shows what changed. The message
  must justify the change: the problem it solves, the constraint it
  satisfies, why this approach. Do not narrate the edits line by line.
- Sign off every commit: `git commit -s` (adds the `Signed-off-by:`
  trailer). No exceptions.
- On the default branch, create a topic branch before committing; push only
  when asked.
