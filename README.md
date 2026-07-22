# Device Tree Editor Lite (qdte-lite)

A focused, lightweight fork of [qualcomm/DTE](https://github.com/qualcomm/DTE)
(the Qualcomm Device Tree Editor). It does one thing well: edit device
trees and assemble/disassemble the Qualcomm config-ELF containers that hold
them (`xbl_config.elf`, `uefi_dtbs.elf`, and similar).

The CLI tool is invoked as `qdte`; the distribution is `qdte-lite`.

## Motivation

Over its life the upstream tool accumulated functionality for specialized
workflows -- on-target device programming, image signing -- that most people
editing device trees never use, and that pull in heavyweight, platform- and
hardware-specific machinery. This fork strips the tool back to the job it is
actually reached for, so it installs cleanly, stays small, and is easy to
reason about. The specialized features remain available in upstream DTE for
anyone who needs them.

## What is different from upstream DTE

Removed:

- **On-target device flows (QUTS)** -- reading and writing DTB ELFs off a
  device. These are Windows/QUTS/EDL-hardware bound.
- **NON-HLOS FAT browser** -- and its `fs`/`pyfatfs` dependencies.
- **sectools signing** -- a wrapper around the external `sectools` binary.
  If you need to sign an image, invoke `sectools` directly on the ELF this
  tool produces.
- **The tkinter GUI** -- replaced by a Qt (PySide6) GUI.

Changed:

- **libfdt instead of pyfdt** for the device-tree layer (`pylibfdt`, the
  maintained dtc bindings), replacing the unmaintained 2014 `pyfdt`.
- **Proper packaging** -- a `pyproject.toml` with a `qdte` console script;
  installable with pip/uv/pipx.
- Child interpreters are spawned via `sys.executable`, so a bare `python`
  is not required on the host.

## Requirements

- Python 3
- `pylibfdt` (the dtc project's libfdt bindings). PyPI ships it as a source
  distribution, so a pip/uv install builds it and needs `swig` at build time
  (`uv pip install swig` provides a prebuilt wheel; distro packages work
  too). Yocto ships it prebuilt as `python3-dtc`.
- For the GUI: the `qt` extra (PySide6, pip-installable on all platforms).

## Install

`uv` is the recommended package manager:

```bash
uv pip install ".[qt]"    # with the GUI
uv pip install .          # headless only
```

`pip` works too. The install provides the `qdte` console script; `python -m
qdte` and `python run.py` are equivalent entry points.

## Usage

Launch the GUI on a file:

```bash
qdte file.dtb
```

Headless, e.g. editing a property inside a config ELF (no GUI toolkit
needed):

```bash
qdte --nogui \
    --input_file xbl_config.elf \
    --output_path out --output_file xbl_config.elf \
    --modify "<dtb name>/<node path>/<property>=<value>"
```

`--allow_unsigned` is accepted and ignored (this tool only produces
unsigned ELFs); it is kept so existing command lines keep working. Run
`qdte --help` for the full flag list.

Troubleshooting (Linux): if the Qt GUI fails to start under Wayland, try
`QT_QPA_PLATFORM=xcb qdte ...`.

The GUI covers browse/edit with undo/redo, save / save-as / DTS export,
find, the raw (hex) view with per-node highlighting, and config-ELF
sessions with unsigned reassembly.

## Code layout

```
run.py            thin launcher; calls qdte.cli.main
qdte/core/        headless engine: flags, dtwrapper, fdt_backend (the
                  libfdt-based DTB layer), assemble/version_2_assemble,
                  Autocmd, XBLConfig tool scripts.
                  Never imports the GUI; CI enforces this by running the
                  --nogui smoke tests on a PySide6-free interpreter.
qdte/cli/         argument parsing and dispatch; the --nogui path
qdte/gui_qt/      the Qt (PySide6) application: item model over dtwrapper,
                  main window, hex view, config-ELF sessions ("qt" extra)
```

The `--nogui` flow imports only `qdte.core` / `qdte.cli`, so it runs on
minimal sysroots (for example Yocto native tools) with no GUI toolkit
installed.

## Development

See [CONTRIBUTING.md](CONTRIBUTING.md). Contributor and repository
conventions (commit style, package manager, invariants) are documented in
[CLAUDE.md](CLAUDE.md).

## License

Licensed under the
[BSD-3-Clause-Clear License](https://spdx.org/licenses/BSD-3-Clause-Clear.html).
See [LICENSE.txt](LICENSE.txt) for the full text. Forked from
[qualcomm/DTE](https://github.com/qualcomm/DTE).
