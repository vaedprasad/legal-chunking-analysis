import os
from pathlib import Path
from typing import List


def get_pdf_file_paths_from_directory(directory_path: str) -> List[str]:
    """
    Retrieves a list of full paths to all PDF files located in the specified directory.

    Parameters
    ----------
    directory_path : str
        The path to the directory from which to retrieve PDF file paths.

    Returns
    -------
    List[str]
        A list containing the full paths to each PDF file found in the specified directory.
        Returns an empty list if no PDF files are found.
    """
    entries = os.listdir(directory_path)
    pdf_files = [
        os.path.join(directory_path, entry)
        for entry in entries
        if os.path.isfile(os.path.join(directory_path, entry))
        and entry.lower().endswith(".pdf")
    ]
    return pdf_files


def get_filename_without_extension(file_path: str) -> str:
    """
    Extracts and returns the filename without its extension from the given file path.

    Parameters
    ----------
    file_path : str
        The full path to the file from which to extract the filename.

    Returns
    -------
    str
        The filename without its extension.
    """
    file_name = Path(file_path).stem
    return file_name


def get_output_file_path(input_file_path: str, output_directory_path: str) -> str:
    """
    Constructs and returns the full path for the output file based on the input file path and output directory.

    The output file will have the same name as the input file but with a '.csv' extension.

    Parameters
    ----------
    input_file_path : str
        The full path to the input file.
    output_directory_path : str
        The path to the output directory where the output file will be saved.

    Returns
    -------
    str
        The full path to the output file with a '.csv' extension.
    """
    filename = os.path.basename(input_file_path)
    name, _ = os.path.splitext(filename)
    output_filename = f"{name}.csv"
    output_path = os.path.join(output_directory_path, output_filename)
    return output_path
