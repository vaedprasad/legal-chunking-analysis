from enum import Enum


class SectionLabel(Enum):
    Termination = "Termination"
    Indemnification = "Indemnification"
    Confidentiality = "Confidentiality"
    Unknown = "Unknown"


TABLE_OF_CONTENTS = "TABLE OF CONTENTS"
PYMUPDF_PAGE = "page"
PYMUPDF_FROM = "from"

OPENAI_SECRET_NAME = "OPENAI_API_KEY"
DEFAULT_OPENAI_PARAMS = dict(model="gpt-4-0125-preview", temperature=0)
OPENAI_PARAMS_SECTION_LABEL = dict(
    model="gpt-4-0125-preview", temperature=0, max_tokens=2
)
OPENAI_PARAMS_TOC_JSON = dict(
    model="gpt-4-0125-preview", temperature=0, response_format={"type": "json_object"}
)
MODEL_KEY = "model"
USER = "user"

# General estimation is 1 token ~= 4 characters in English.
# The context window for gpt-4-0125-preview is 128,000.
# Set the maximum input characters to 128,000 * 3 = 384,000 to allow room for the prompt.
MAX_INPUT_CHARS = 384_000

DOCUMENT = 0
SECTION = 1
SUBSECTION = 2
PAGE_NUMBER_START = 3
TRUE_PAGE_NUMBER_START = 4
TRUE_PAGE_NUMBER_END = 5
SUBSECTION_TEXT = 6

COLUMNS = [
    "Document Name",
    "Section Header",
    "Subsection Header",
    "Page Number Start",
    "True Page Number Start",
    "True Page Number End",
    "Subsection Text",
    "Subsection Label",
]


TABLE_OF_CONTENTS_PROMPT = """
Given the raw text extracted from a PDF document, please analyze the content and identify the table of contents, including all main sections and any appendixes. Once identified, create a JSON object where each key represents the name of a top-level section or appendix as mentioned in the table of contents, and its corresponding value is a dictionary containing any subsections for that top-level section as a key and the corresponding page number as a value. The top-level section names are always in all capital letters, and the page numbers could be in numerical format or follow a pattern such as A-1, B-2 for appendixes and other special sections.

Note: All top-level sections are capitalized. Ensure that sections and subsections in the response are represented literally as it appears. If sections or subsections are on multiple lines, combine them on the same line replacing the \\n sequence with a space. If any ambiguities or unclear mappings arise, please provide your best guess. Include the top-level section as a subsection in the sub-dictionary. Subsections for appendixes may appear later in the document, include these subsections. Ensure that all property names are enclosed by double quotes.

Example of Expected Output:

If you identify the following sections and page numbers in the table of contents - "SUMMARY" on page 3, "Prologue" as a subsection on page 4, "CHAPTER 1: INTRODUCTION" on page 7, and "ADDITIONAL RESOURCES" on page A-1, then format the output as follows:

{
  "SUMMARY": {
      "SUMMARY": "3",
      "Prologue": "4",
  },
  "CHAPTER 1: INTRODUCTION": {
      "CHAPTER 1: INTRODUCTION": "7",
  },
  "ADDITIONAL RESOURCES": {
      "ADDITIONAL RESOURCES": "A-1",
  },
}

Document:

"""

SECTION_CLASSIFICATION_PROMPT = """
Analyze the following section extracted from a document and determine if the section relates to Termination, Indemnification, Confidentiality, or other. Provide a single label as the response, indicating the category that best describes the content of the text.

Section:

"""
