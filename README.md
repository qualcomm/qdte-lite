# DTGUI (Device Tree Editor)

*Welcome to the DT GUI project*

DTGUI is a graphical user interface application for editing Device Trees and modifying DTB (Device Tree Blob) and ELF files. It runs on host machines (Linux/Windows) and is designed to work with Qualcomm® platforms.

## Branches

**main**: Primary development branch. Contributors should develop submissions based on this branch, and submit pull requests to this branch.

## Requirements

To run this project, you need:

*   Python 3
*   Tkinter (usually included with Python)
*   Dependencies listed in `requirements.txt`

## Installation Instructions

1.  Clone the repository:
    ```bash
    git clone https://github.com/qualcomm/DTGUI-for-Qualcomm-DTB-ELF-Modification.git
    cd DTGUI-for-Qualcomm-DTB-ELF-Modification
    ```

2.  Install the required Python packages:
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
python3 run.py lahaina.dtb
```

For a list of available options and flags:

```bash
python3 run.py --help
```

## Development

For information on how to contribute to this project, please refer to the [CONTRIBUTING.md](CONTRIBUTING.md) file.

## Getting in Contact

*   [Report an Issue on GitHub](../../issues)
*   [Open a Discussion on GitHub](../../discussions)

## License

DTGUI is licensed under the [BSD-3-clause License](https://spdx.org/licenses/BSD-3-Clause.html). See [LICENSE.txt](LICENSE.txt) for the full license text.
