from collections import defaultdict
import fitz
import os
from typing import List, Tuple, Dict
import pandas as pd
import logging
from constants import (
    COLUMNS,
    SUBSECTION,
    SUBSECTION_TEXT,
    TABLE_OF_CONTENTS,
    PYMUPDF_FROM,
    PYMUPDF_PAGE,
    TRUE_PAGE_NUMBER_END,
    TRUE_PAGE_NUMBER_START,
)
from openai_utils import prompt_section_subsection_page_mapping, prompt_subsection_label


def get_text_true_page_mapping(pages: List[fitz.Page]) -> Dict[str, List[int]]:
    """
    Extracts a mapping from text to its corresponding true page numbers from a list of PDF pages.

    Parameters
    ----------
    pages : List[fitz.Page]
        A list of `fitz.Page` objects from which to extract text and page number mappings.

    Returns
    -------
    Dict[str, List[int]]
        A dictionary where each key is a piece of text found within the links of the pages,
        and the value is a list of page numbers where the text is linked.

    Examples
    --------
    >>> pages = [fitz.open('example.pdf')[0]]  # Assuming the PDF has at least one page
    >>> text_page_map = get_text_true_page_mapping(pages)
    >>> print(text_page_map)
    {'Introduction': [1], 'Chapter 1': [2]}
    """
    text_true_page_map = defaultdict(list)
    for page in pages:
        for link in page.get_links():
            if PYMUPDF_FROM not in link or PYMUPDF_PAGE not in link:
                continue
            text = page.get_textbox(link[PYMUPDF_FROM]).strip()
            text_true_page_map[text].append(link[PYMUPDF_PAGE])

    return dict(text_true_page_map)


def find_closest_or_greater(page_numbers: List[int], previous_page: int) -> int:
    """
    Finds the first page number in the list that is greater than or equal to the given page number.
    If no such page exists, returns the closest smaller page number.

    Parameters
    ----------
    page_numbers : List[int]
        A list of integers representing page numbers.
    previous_page : int
        The page number to compare against.

    Returns
    -------
    int
        The closest page number from the list that is greater than or equal to `previous_page`.

    Raises
    ------
    ValueError
        If the input list `page_numbers` is empty.

    Examples
    --------
    >>> find_closest_or_greater([2, 3, 5, 10], 4)
    5
    >>> find_closest_or_greater([1, 2, 3], 6)
    3
    """
    if len(page_numbers) < 1:
        raise ValueError(f"Unexpected value: {page_numbers}.")
    elif len(page_numbers) == 1:
        return page_numbers[0]
    page_numbers.sort()  # Sort the list to make it easier to find the closest value
    closest = page_numbers[0]  # Initialize closest with the first element

    for page_number in page_numbers:
        if page_number >= previous_page:
            # If page_number is greater than or equal to previous_page, it's the closest we need
            return page_number
        else:
            # Update closest if page_number is closer to previous_page than the current closest
            if abs(page_number - previous_page) < abs(closest - previous_page):
                closest = page_number

    return closest


def create_table(
    section_subsection_page_map: Dict[str, Dict[str, str]],
    text_true_page_map: Dict[str, List[int]],
    file_name: str,
) -> List[Tuple[str, str, str, str, int]]:
    """
    Creates a table listing document, sections, subsections, and their corresponding page numbers.

    Parameters
    ----------
    section_subsection_page_map : Dict[str, Dict[str, str]]
        A mapping from section titles to a dictionary of subsection titles and their indicated page numbers.
    text_true_page_map : Dict[str, List[int]]
        A mapping from text to a list of true page numbers where the text appears.
    file_name : str
        The name of the file being processed.

    Returns
    -------
    List[Tuple[str, str, str, str, int]]
        A list of tuples, each containing the file name, section title, subsection title,
        indicated page number (as a string), and the true page number (as an integer).

    Examples
    --------
    >>> section_map = {"Introduction": {"Purpose": "1"}}
    >>> text_page_map = {"1": [1]}
    >>> create_table(section_map, text_page_map, "example.pdf")
    [('example.pdf', 'Introduction', 'Purpose', '1', 1)]
    """
    table = []
    for section in section_subsection_page_map:
        for subsection in section_subsection_page_map[section]:
            page_number = section_subsection_page_map[section][subsection]
            if isinstance(page_number, str) and page_number in text_true_page_map:
                true_page_number = find_closest_or_greater(
                    page_numbers=text_true_page_map[page_number],
                    previous_page=(
                        table[-1][TRUE_PAGE_NUMBER_START] if len(table) > 0 else 0
                    ),
                )
            elif isinstance(subsection, str) and subsection in text_true_page_map:
                true_page_number = find_closest_or_greater(
                    page_numbers=text_true_page_map[subsection],
                    previous_page=(
                        table[-1][TRUE_PAGE_NUMBER_START] if len(table) > 0 else 0
                    ),
                )
            else:
                continue
            table.append(
                (file_name, section, subsection, page_number, true_page_number)
            )
    return table


def add_true_end_page(
    table: List[Tuple[str, str, str, str, int]], document_length: int
) -> List[Tuple[str, str, str, str, int, int]]:
    """
    Adds the true end page number for each entry in the table.

    Parameters
    ----------
    table : List[Tuple[str, str, str, str, int]]
        The table to which the true end page numbers will be added. Each entry contains
        the file name, section, subsection, page number, and start page number.
    document_length : int
        The total number of pages in the document.

    Returns
    -------
    List[Tuple[str, str, str, str, int, int]]
        The updated table with an additional element for each entry indicating the true end page.

    Examples
    --------
    >>> table = [('example.pdf', 'Introduction', 'Purpose', '1', 1)]
    >>> add_true_end_page(table, 10)
    [('example.pdf', 'Introduction', 'Purpose', '1', 1, 9)]
    """
    for index in range(len(table)):
        true_end_page = (
            document_length - 1
            if index == len(table) - 1
            else table[index + 1][TRUE_PAGE_NUMBER_START]
        )
        table[index] = table[index] + (true_end_page,)
    return table


def add_subsection_text(
    table: List[Tuple[str, str, str, str, int, int]], document: fitz.Document
) -> List[Tuple[str, str, str, str, int, int, str]]:
    """
    Appends the text of each subsection to the table entries based on the start and end page numbers.

    Parameters
    ----------
    table : List[Tuple[str, str, str, str, int, int]]
        The table containing the entries for which to add the subsection text.
    document : fitz.Document
        The document from which to extract the subsection text.

    Returns
    -------
    List[Tuple[str, str, str, str, int, int, str]]
        The updated table with an additional element for each entry containing the subsection text.

    Notes
    -----
    This function assumes the `table` list has been properly populated with start and end page numbers
    for each section and subsection.
    """
    for index, row in enumerate(table):
        text_for_pages = get_text_from_range_of_pages(
            document, row[TRUE_PAGE_NUMBER_START], row[TRUE_PAGE_NUMBER_END]
        )
        start_index = text_for_pages.find(row[SUBSECTION])
        if start_index == -1:
            start_index = 0

        if index == len(table) - 1:
            subsection_text = text_for_pages[start_index:].replace(
                TABLE_OF_CONTENTS, ""
            )
            table[index] = table[index] + (subsection_text,)
        else:
            end_index = text_for_pages.find(table[index + 1][SUBSECTION])
            if end_index == -1:
                end_index = len(text_for_pages)
            subsection_text = text_for_pages[start_index:end_index].replace(
                TABLE_OF_CONTENTS, ""
            )
            table[index] = table[index] + (subsection_text,)

    return table


def add_subsection_label(
    table: List[Tuple[str, str, str, str, int, int, str]]
) -> List[Tuple[str, str, str, str, int, int, str, str]]:
    """
    Appends a subsection label to each entry in the table by analyzing the subsection text.

    Parameters
    ----------
    table : List[Tuple[str, str, str, str, int, int, str]]
        The table containing the entries for which to add the subsection labels. Each entry is expected
        to already include the subsection text.

    Returns
    -------
    List[Tuple[str, str, str, str, int, int, str, str]]
        The updated table with an additional element for each entry containing the subsection label.

    Examples
    --------
    # Assuming `table` is populated and `prompt_subsection_label` function is defined:
    >>> table = [('example.pdf', 'Introduction', 'Purpose', '1', 1, 10, 'This section introduces...')]
    >>> labeled_table = add_subsection_label(table)
    >>> print(labeled_table[0][-1])  # Prints the label of the first entry's subsection.
    """
    for index, row in enumerate(table):
        subsection_text = row[SUBSECTION_TEXT]
        label_text = prompt_subsection_label(text=subsection_text)
        table[index] = table[index] + (label_text,)
    return table


def get_text_from_pages(pages: List[fitz.Page]) -> str:
    """
    Concatenates and returns the text from a list of PDF pages.

    Parameters
    ----------
    pages : List[fitz.Page]
        A list of `fitz.Page` objects from which to extract text.

    Returns
    -------
    str
        The concatenated text from all provided pages.

    Examples
    --------
    >>> document = fitz.open('example.pdf')
    >>> pages = [document[0], document[1]]  # Assuming the document has at least two pages
    >>> text = get_text_from_pages(pages)
    >>> print(text[:100])  # Prints the first 100 characters of the combined text
    """
    return "".join(page.get_text() for page in pages)


def get_text_from_range_of_pages(
    document: fitz.Document, start_page: int, end_page: int
) -> str:
    """
    Extracts and concatenates text from a specified range of pages in a PDF document.

    Parameters
    ----------
    document : fitz.Document
        The PDF document from which to extract text.
    start_page : int
        The zero-based index of the first page from which to start extracting text.
    end_page : int
        The zero-based index of the last page from which to extract text.

    Returns
    -------
    str
        The concatenated text from the specified range of pages.

    Examples
    --------
    >>> document = fitz.open('example.pdf')
    >>> text = get_text_from_range_of_pages(document, 0, 1)
    >>> print(text[:100])  # Prints the first 100 characters of the text from pages 1 and 2
    """
    return "".join(document[i].get_text() for i in range(start_page, end_page + 1))


def get_filtered_pages_with_links(
    document: fitz.Document, links_per_page_threshold: int = 5
) -> List[fitz.Page]:
    """
    Filters and returns pages from a PDF document that have more than a specified number of links.

    Parameters
    ----------
    document : fitz.Document
        The PDF document to filter.
    links_per_page_threshold : int, optional
        The minimum number of links a page must have to be included in the returned list, by default 5.

    Returns
    -------
    List[fitz.Page]
        A list of `fitz.Page` objects that meet the link count criteria.

    Examples
    --------
    >>> document = fitz.open('example.pdf')
    >>> filtered_pages = get_filtered_pages_with_links(document, 2)
    >>> print(len(filtered_pages))  # Prints the number of pages with more than 2 links
    """
    return list(
        filter(lambda page: len(page.get_links()) > links_per_page_threshold, document)
    )


def generate_summary(input_file_path: str, output_file_path: str) -> None:
    """
    Generates a summary of a PDF document, including sections, subsections, and their labels, and saves it to a CSV file.

    Parameters
    ----------
    input_file_path : str
        The path to the input PDF document.
    output_file_path : str
        The path where the summary CSV file will be saved.

    Examples
    --------
    >>> input_pdf = 'path/to/document.pdf'
    >>> output_csv = 'path/to/summary.csv'
    >>> generate_summary(input_pdf, output_csv)
    This will read the document at `input_pdf`, generate a summary, and save it to `output_csv`.
    """
    file_name = os.path.basename(input_file_path)
    logging.basicConfig(
        level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
    )
    logging.info(f"Generating Summary for: {file_name:<{50}}")
    with fitz.open(input_file_path) as document:
        filtered_pages = get_filtered_pages_with_links(document=document)
        filtered_text = get_text_from_pages(pages=filtered_pages)
        text_true_page_map = get_text_true_page_mapping(pages=filtered_pages)
        section_subsection_page_map = prompt_section_subsection_page_mapping(
            text=filtered_text
        )
        table = create_table(
            section_subsection_page_map=section_subsection_page_map,
            text_true_page_map=text_true_page_map,
            file_name=file_name,
        )
        table = add_true_end_page(table=table, document_length=len(document))
        table = add_subsection_text(table=table, document=document)
        table = add_subsection_label(table=table)

    summary_df = pd.DataFrame(
        data=table,
        columns=COLUMNS,
    )
    summary_df.to_csv(output_file_path, index=False)
    logging.info(f"Successfully Completed Summary for: {output_file_path:<{50}}")
