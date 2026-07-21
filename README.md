# DTE (Device Tree Editor)

*Welcome to the DTE project*

DTE is a graphical user interface application for editing Device Trees and modifying DTB (Device Tree Blob) and ELF files. It runs on host machines (Linux/Windows) and is designed to work with Qualcomm® platforms.

## Branches

**main**: Primary development branch. Contributors should develop submissions based on this branch, and submit pull requests to this branch.

## Requirements

To run this project, you need:

* Python 3
* For the Qt GUI: the `qt` extra (PySide6, pip-installable everywhere)
* For the legacy tkinter GUI: Tkinter (usually included with Python;
  on Debian/Ubuntu install `python3-tk`, on Fedora/Yocto `python3-tkinter`)
* Dependencies listed in `requirements.txt`

## Installation Instructions

1. Clone the repository:

   ```bash
   git clone https://github.com/qualcomm/DTE.git
   cd DTE
   ```
2. Install the required Python packages:

   ```bash
   pip install -r requirements.txt
   ```

## Usage

To launch the application, run the `run.py` script:

```bash
python3 run.py
```

You can also pass a file to open directly:

```bash
python3 run.py <filename>.dtb
```

For a list of available options and flags:

```bash
python3 run.py --help
```

Headless (no GUI, no Tcl/Tk needed), e.g. editing a property inside a
config ELF:

```bash
python3 run.py --nogui --allow_unsigned \
    --input_file xbl_config.elf \
    --output_path out --output_file xbl_config.elf \
    --modify "<dtb name>/<node path>/<property>=<value>"
```

`python3 -m qdte` is equivalent to `run.py`, and installing the package
(`pip install .`) provides a `qdte` console script.

### GUI flavours

```bash
pip install "qdte-lite[qt]"     # Qt (PySide6) GUI - the default when installed
pip install "qdte-lite[gui]"    # tkinter GUI extras (NON-HLOS FAT browser)
pip install "qdte-lite[all]"    # everything

qdte file.dtb                 # Qt if PySide6 is importable, tkinter otherwise
qdte --tk file.dtb            # force the legacy tkinter GUI
```

The Qt frontend currently covers the core editing loop (browse, edit,
undo/redo, save, unsigned config-ELF reassembly); device operations, the
NON-HLOS browser and signing dialogs still live in the tkinter GUI, one
`--tk` away.

Troubleshooting (Linux): if the Qt GUI fails to start under Wayland, try
`QT_QPA_PLATFORM=xcb qdte ...`.

## Code layout

```
run.py            thin launcher (kept for compatibility; calls qdte.cli.main)
qdte/core/        headless engine: flags, dtwrapper, assemble/version_2_assemble,
                  sign, Autocmd, XBLConfig tool scripts.
                  Must never import qdte.gui or tkinter -- CI enforces this by
                  running the --nogui smoke tests with a poisoned tkinter.
qdte/cli/         argument parsing and dispatch; the --nogui path
qdte/gui_qt/      the Qt (PySide6) application: item model over dtwrapper,
                  main window, config-ELF sessions ("qt" extra)
qdte/gui/         the tkinter application: controller, views, settings,
                  XBLConfig integration, NON-HLOS FAT browser
QutsAtom/         vendored QUTS Atom glue, loaded only when a QUTS
                  installation is present (GUI device operations)
```

The `--nogui` flow imports only `qdte.core`/`qdte.cli`, so it runs on
minimal sysroots (e.g. Yocto native tools) without Tcl/Tk or the GUI's
fs/pyfatfs dependencies.

## Development

For information on how to contribute to this project, please refer to the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## Getting in Contact

* [Report an Issue on GitHub](../../issues)
* [Open a Discussion on GitHub](../../discussions)

## License

DTGUI is licensed under the [BSD-3-clause License](https://spdx.org/licenses/BSD-3-Clause.html). See [LICENSE.txt](LICENSE.txt) for the full license text.
