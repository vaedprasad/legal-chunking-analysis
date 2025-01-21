import time
import multiprocessing
import logging
from typing import List, Tuple
from io_utils import get_output_file_path, get_pdf_file_paths_from_directory
from processor import generate_summary


def generate_summary_for_directory(
    input_directory_path: str, output_directory_path: str
) -> None:
    """
    Generates summaries for all PDF files in a specified input directory
    and saves them to an output directory, processing each file sequentially.

    Parameters
    ----------
    input_directory_path : str
        The path to the directory containing input PDF files.
    output_directory_path : str
        The path to the directory where output summary CSV files will be saved.

    Notes
    -----
    This function processes files sequentially and reports the total elapsed time
    to complete the summaries for all files.
    """
    start_time = time.time()
    input_file_paths: List[str] = get_pdf_file_paths_from_directory(
        directory_path=input_directory_path
    )
    for input_file_path in input_file_paths:
        output_file_path = get_output_file_path(
            input_file_path=input_file_path, output_directory_path=output_directory_path
        )
        generate_summary(
            input_file_path=input_file_path, output_file_path=output_file_path
        )
    end_time = time.time()
    print("Elapsed Time (Single):", end_time - start_time)


def _generate_summary_worker(args: Tuple[str, str]) -> None:
    """
    Worker function to generate a summary for a single PDF file. This function is
    intended to be called by multiprocessing.Pool.map().

    Parameters
    ----------
    args : Tuple[str, str]
        A tuple containing two elements: the path to the input PDF file and the path
        to the output CSV file where the summary should be saved.
    """
    input_file_path, output_file_path = args
    generate_summary(input_file_path, output_file_path)


def generate_summary_for_directory_parallel(
    input_directory_path: str, output_directory_path: str
) -> None:
    """
    Generates summaries for all PDF files in a specified input directory
    and saves them to an output directory, processing the files in parallel.

    Parameters
    ----------
    input_directory_path : str
        The path to the directory containing input PDF files.
    output_directory_path : str
        The path to the directory where output summary CSV files will be saved.

    Notes
    -----
    This function utilizes multiprocessing to process files in parallel,
    significantly reducing the total time required to generate summaries for all files.
    The number of processes spawned will default to the number of CPUs available.
    """
    start_time = time.time()

    input_file_paths = get_pdf_file_paths_from_directory(
        directory_path=input_directory_path
    )
    args_list = [
        (input_file_path, get_output_file_path(input_file_path, output_directory_path))
        for input_file_path in input_file_paths
    ]

    with multiprocessing.Pool() as pool:
        pool.map(_generate_summary_worker, args_list)

    end_time = time.time()
    print("Elapsed Time (Parallel):", end_time - start_time)


if __name__ == "__main__":
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    generate_summary_for_directory_parallel(
        input_directory_path="data", output_directory_path="chunks"
    )
