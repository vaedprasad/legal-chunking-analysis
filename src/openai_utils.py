import json
from typing import Dict, Literal
from difflib import get_close_matches

from constants import (
    MAX_INPUT_CHARS,
    OPENAI_PARAMS_SECTION_LABEL,
    OPENAI_PARAMS_TOC_JSON,
    SECTION_CLASSIFICATION_PROMPT,
    TABLE_OF_CONTENTS_PROMPT,
    SectionLabel,
)
from openai_prompt_service import OpenAIPromptService


def prompt_section_subsection_page_mapping(text: str) -> Dict[str, Dict[str, str]]:
    """
    Generates a mapping of section to subsections and their corresponding page numbers from a given text.

    Parameters
    ----------
    text : str
        The input text from which to generate the section-subsection-page mapping.

    Returns
    -------
    Dict[str, Dict[str, str]]
        A dictionary mapping each section to another dictionary, which maps subsections to their page numbers.

    Raises
    ------
    json.JSONDecodeError
        If the output from the prompt service cannot be decoded into JSON.
    """
    prompt_service = OpenAIPromptService()
    output = prompt_service.run_prompt(
        prompt=TABLE_OF_CONTENTS_PROMPT + text[:MAX_INPUT_CHARS],
        model_config=OPENAI_PARAMS_TOC_JSON,
    )
    try:
        section_subsection_page_map = json.loads(output)
    except json.JSONDecodeError:
        return {}
    return section_subsection_page_map


def prompt_subsection_label(
    text: str,
) -> Literal["Termination", "Indemnification", "Confidentiality", "Unknown"]:
    """
    Determines the label for a subsection based on its content using an AI prompt service.

    Parameters
    ----------
    text : str
        The text content of the subsection to classify.

    Returns
    -------
    Literal["Termination", "Indemnification", "Confidentiality", "Unknown"]
        The classification label of the subsection.
    """
    prompt_service = OpenAIPromptService()
    output = prompt_service.run_prompt(
        prompt=SECTION_CLASSIFICATION_PROMPT + text[:MAX_INPUT_CHARS],
        model_config=OPENAI_PARAMS_SECTION_LABEL,
    )
    label = map_output_to_label(output=output)
    return label.value


def map_output_to_label(output: str) -> SectionLabel:
    """
    Maps the output of the classification prompt to a SectionLabel enum.

    Parameters
    ----------
    output : str
        The raw output string from the AI prompt service.

    Returns
    -------
    SectionLabel
        The corresponding SectionLabel enum for the classification result.

    Notes
    -----
    If no close match is found, defaults to SectionLabel.Unknown.
    """
    clean_output = output.strip().lower()
    clean_labels = {label.value.strip().lower(): label for label in SectionLabel}
    matches = get_close_matches(clean_output, clean_labels, n=1)
    if not matches:
        return SectionLabel.Unknown
    return clean_labels[matches[0]]
