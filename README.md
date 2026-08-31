# Device Tree Editor Lite (qdte-lite)

A focused, lightweight fork of [qualcomm/DTE](https://github.com/qualcomm/DTE)
(the Qualcomm Device Tree Editor). It does one thing well: edit device
trees and assemble/disassemble the Qualcomm config-ELF containers that hold
them (`xbl_config.elf`, `uefi_dtbs.elf`, and similar).

The CLI command and the distribution are both named `qdte-lite`; the import
package is `qdte_lite`.

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
- **Proper packaging** -- a `pyproject.toml` with a `qdte-lite` console script;
  installable with pip/uv/pipx.
- Child interpreters are spawned via `sys.executable`, so a bare `python`
  is not required on the host.

Versioning:

- The version line is this fork's own. `qdte-lite` 2.0.0 follows upstream
  DTE 1.5.x in ancestry only -- the major bump marks the removals and the
  device-tree backend swap listed above. It does not imply parity with, or
  succession to, any DTE 1.x release, and upstream releases are not tracked
  here.

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
$ uv pip install ".[qt]"    # with the GUI
$ uv pip install .          # headless only
```

`pip` works too. The install provides the `qdte-lite` console script;
`python -m qdte_lite` is an equivalent entry point. Install the package
rather than running from a source checkout, so the `qdte-lite` command and
its dependencies resolve correctly.

## Usage

Launch the GUI on a file:

```bash
$ qdte-lite file.dtb
```

Headless, e.g. editing a property inside a config ELF (no GUI toolkit
needed):

```bash
$ qdte-lite --nogui \
    --input_file xbl_config.elf \
    --output_path out --output_file xbl_config.elf \
    --modify "<dtb name>/<node path>/<property>=<value>"
```

A value token may also be read from a file, so a binary blob does not have
to be hex-encoded on the command line. `@list:<path>` is replaced by the
cells listed in `<path>`: whitespace- or comma-separated hexadecimal words,
one per 32-bit cell, without a `0x` prefix. That is the format
cbsp-boot-utilities' `bin-to-hex` writes and its own `@list:` reads, so a
blob converted once feeds either tool and yields identical bytes:

```bash
$ qcom-capsule-tool bin-to-hex root.cer root.inc

$ qdte-lite --nogui \
    --input_file xbl_config.elf \
    --output_path out --output_file xbl_config.elf \
    --modify "<dtb name>/sw/uefi/uefiplat/QcCapsuleRootCert=@list:root.inc"
```

The file supplies the whole value, length prefix included. It composes with
literals, so a value may still mix the two forms.

`--list` prints the DTBs a container holds, one name per line and nothing
else, so the output can be iterated:

```bash
$ qdte-lite --nogui --input_file xbl_config.elf --list
post-ddr-kodiak-1.0.dtb
pre-ddr-kodiak-1.0.dtb
```

Addressing a property also requires knowing which of those DTBs holds it,
and the names are assigned during disassembly rather than being visible in
the container itself. `--find_property` reports the whole target at once:

```bash
$ qdte-lite --nogui --input_file xbl_config.elf --find_property QcCapsuleRootCert
post-ddr-kodiak-1.0.dtb/sw/uefi/uefiplat/QcCapsuleRootCert
```

One line per match, usable as a `--modify` target verbatim, and a non-zero
exit if the property is absent, so a script can locate a property instead of
hardcoding names per platform:

```bash
$ target=$(qdte-lite --nogui --input_file xbl_config.elf --find_property QcCapsuleRootCert)
$ qdte-lite --nogui --input_file xbl_config.elf \
    --output_path out --output_file xbl_config.elf \
    --modify "$target=@list:root.inc"
```

`--allow_unsigned` is accepted and ignored (this tool only produces
unsigned ELFs); it is kept so existing command lines keep working. Run
`qdte-lite --help` for the full flag list.

Troubleshooting (Linux): if the Qt GUI fails to start under Wayland, try
`QT_QPA_PLATFORM=xcb qdte-lite ...`.

The GUI covers browse/edit with undo/redo, save / save-as / DTS export,
find, the raw (hex) view with per-node highlighting, and config-ELF
sessions with unsigned reassembly.

## Code layout

```text
qdte_lite/__main__.py  console entry point (the `qdte-lite` command; `python -m qdte_lite`)
qdte_lite/core/        headless engine: flags, dtwrapper, fdt_backend (the
                  libfdt-based DTB layer), assemble/version_2_assemble,
                  Autocmd, XBLConfig tool scripts.
                  Never imports the GUI; CI enforces this by running the
                  --nogui smoke tests on a PySide6-free interpreter.
qdte_lite/cli/         argument parsing and dispatch; the --nogui path
qdte_lite/gui_qt/      the Qt (PySide6) application: item model over dtwrapper,
                  main window, hex view, config-ELF sessions ("qt" extra)
```

The `--nogui` flow imports only `qdte_lite.core` / `qdte_lite.cli`, so it runs on
minimal sysroots (for example Yocto native tools) with no GUI toolkit
installed.

## Development

A `Makefile` is the single entry point for setup and checks (bash-based, so
it works on Linux and macOS natively and on Windows under Git Bash or WSL):

```bash
$ make init          # install dependencies with uv (base + GUI extra)
$ make run           # launch the GUI
$ make check-all     # run every check (what CI runs)

$ make ascii         # enforce the ASCII-only rule (scripts/check_unicode_symbols.sh)
$ make test          # headless --nogui smoke test against real boot images
                     # (scripts/nogui-smoketest.sh; fixtures download to .test/)
$ make help          # list all targets
```

`make lint`, `make format`, `make format-check` and `make type` are stubs
until that tooling is configured. The GitHub `nogui smoketest` workflow runs
`make test`, so CI and local runs are identical.

See [CONTRIBUTING.md](CONTRIBUTING.md). Contributor and repository
conventions (commit style, package manager, invariants) are documented in
[CLAUDE.md](CLAUDE.md).

## License

Licensed under the
[BSD-3-Clause-Clear License](https://spdx.org/licenses/BSD-3-Clause-Clear.html).
See [LICENSE.txt](LICENSE.txt) for the full text. Forked from
[qualcomm/DTE](https://github.com/qualcomm/DTE).
