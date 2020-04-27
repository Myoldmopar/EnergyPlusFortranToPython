from pathlib import Path


def path_to_bin_ep_macro() -> Path:
    this_file_directory = Path(__file__).parent.absolute()
    return this_file_directory / 'bin' / 'EPMacro'
