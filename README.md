# Romeo & Juliet - Vernacular Translation & KDP PDF Generator

This project takes William Shakespeare's classic play, *Romeo and Juliet*, translates it into contemporary British urban vernacular (inspired by the user's exploration of "Chav style"), and generates a print-ready PDF formatted for Kindle Direct Publishing (KDP) hardback publication. The final PDF features a side-by-side layout with the original Shakespearean text and the modern translation.

**Disclaimer:** This is an experimental project exploring stylistic translation using AI. The vernacular style used is a specific adaptation and may contain language reflecting certain stereotypes; it aims for a particular creative effect rather than linguistic accuracy.

## Features

* **Text Parsing:** Parses a plain text version of the play, identifying acts, scenes, speakers, dialogue, headings, and stage directions.
* **AI Translation:** Utilizes the Google Gemini API (or compatible models like Gemma accessed via the API) to translate dialogue and stage directions line-by-line or chunk-by-chunk into the target vernacular.
* **Checkpointing:** Saves translation progress periodically, allowing the script to be stopped and resumed without losing completed work or re-using API calls unnecessarily.
* **PDF Generation:** Uses the ReportLab library to create a PDF document.
* **KDP Formatting:** Specifically formats the PDF for a 6" x 9" hardback trim size with appropriate mirrored margins for printing via KDP.
* **Side-by-Side Layout:** Presents the original Shakespearean text and the generated translation in parallel columns on each page.
* **Custom Styling:** Applies basic text styling (fonts, sizes, italics, bolding, centering) for different elements within the PDF.
* **Page Numbering:** Automatically adds page numbers to the generated PDF.
## Technology Stack

* **Language:** Python 3.x
* **AI Model:** Google Gemini API (e.g., `gemini-1.5-flash-latest`, `gemini-pro`) or compatible models (e.g., Gemma via API). Model configured in `src/main.py`.
* **Core Libraries:**
    * `google-generativeai`: For interacting with the Gemini API.
    * `reportlab`: For generating the PDF document.
    * `python-dotenv`: For securely managing the API key.
* **Environment:** Managed using `venv`. Dependencies listed in `requirements.txt`.

## Project Structure

romeo-gemini-pdf/
│
├── .env                    # Stores API key (!!! IMPORTANT: MUST be in .gitignore !!!)
├── .gitignore              # Specifies intentionally untracked files by Git
├── LICENSE                 # Project license file (if applicable)
├── README.md               # This file
├── requirements.txt        # Python dependencies
│
├── checkpoints/            # Stores translation progress (ignored by Git)
│   └── translation_progress.pkl
│
├── config/                 # Optional: For non-secret configuration
│   └── constants.py        # (Example, not fully implemented in provided code)
│
├── data/                   # Input data
│   └── romeo_and_juliet.txt # Plain text source file of the play
│
├── output/                 # Generated output (ignored by Git)
│   └── romeo_vernacular_side_by_side.pdf
│
├── src/                    # Source code
│   ├── init.py         # Makes src a package (can be empty)
│   ├── main.py             # Main orchestration script
│   ├── parser.py           # Logic for parsing the input text file
│   └── pdf_generator.py    # Logic for creating the PDF output
│
└── venv/                   # Python virtual environment (ignored by Git)

## Setup Instructions

1.  **Clone the Repository:**
    ```bash
    git clone <your-repository-url> # Or just navigate to your existing local folder
    cd romeo-gemini-pdf
    ```

2.  **Create and Activate Virtual Environment:**
    ```bash
    python3 -m venv venv
    # On Linux/macOS:
    source venv/bin/activate
    # On Windows:
    # venv\Scripts\activate
    ```

3.  **Install Dependencies:**
    ```bash
    pip install -r requirements.txt
    ```

4.  **Set Up API Key:**
    * Create a file named `.env` in the project root directory (`romeo-gemini-pdf/`).
    * Add your Google Gemini API key to this file in the following format:
        ```dotenv
        GEMINI_API_KEY=YOUR_ACTUAL_API_KEY_HERE
        ```
    * **Ensure `.env` is listed in your `.gitignore` file.**

5.  **Add Source Text:**
    * Download a plain text (`.txt`) version of *Romeo and Juliet*. Project Gutenberg (e.g., [Ebook #1513](https://www.gutenberg.org/ebooks/1513.txt.utf-8)) is a good source.
    * Save the file as `romeo_and_juliet.txt` inside the `data/` directory.

## Usage

Run the main script from the project's root directory (`romeo-gemini-pdf/`):

```bash
python src/main.py
```

The script will perform the following phases:

1.  **Initialization:** Load API key, configure Gemini client.
2.  **Load/Parse Data:** Attempt to load translation progress from checkpoints/translation_progress.pkl. If not found or invalid, it will parse data/romeo_and_juliet.txt using src/parser.py and save an initial checkpoint.
3.  **Translation:** Iterate through the parsed play structure. For dialogue and stage directions not already translated (from checkpoint), it will call the Gemini API. Progress is saved to the checkpoint file periodically. This phase is skipped if all translations are already present in the checkpoint.
4. ""PDF Generation:"" Once the play structure (with translations) is ready, it calls src/pdf_generator.py to create the final side-by-side PDF (output/romeo_vernacular_side_by_side.pdf).

You can stop the script during the translation phase (Ctrl+C) and restart it later; it will resume from the last saved checkpoint.

## Configuration Points

* **API Key:** Set in the `.env` file in the project root.
* **AI Model:** Specified in `src/main.py` (e.g., `model = genai.GenerativeModel('gemini-1.5-flash-latest')`).
* **Translation Style Prompt:** Defined within the translation loop in `src/main.py`. Modify the `style_instruction` variable and prompt structure to refine the output.
* **Rate Limit Delay:** `TRANSLATION_DELAY` constant in `src/main.py`.
* **PDF/KDP Specs:** Page size, margins, column gap defined as constants at the top of `src/pdf_generator.py`.
* **PDF Styles:** Paragraph styles defined using ReportLab's `ParagraphStyle` in `src/pdf_generator.py`.

## Current Status & Next Steps

* [X] Parsing of source text implemented.
* [X] Translation loop with Gemini API/Gemma implemented.
* [X] Checkpointing for translation progress implemented.
* [X] PDF generation with side-by-side layout and KDP specs implemented.
* [X] Page numbering added.
* [X] Stage direction formatting adjusted (original only, centered, underscores removed).
* [ ] **Content Review:** Thoroughly review the generated translation for accuracy, consistency, and quality. Manual editing likely required.
* [ ] **Add Front/Back Matter:** Implement Title Page, Copyright Page (with disclaimer), etc., in the PDF generation.
* [ ] **Final PDF Polish:** Proofread the entire PDF for typos and formatting issues after content review and front matter addition.
* [ ] **KDP Preparation:** Cover design, ISBN acquisition (if needed).

## License

    romeo-gemini-pdf: Translate Romeo and Juliet to modern English with AI
    Copyright (C) 2025 Fufu Fang

    This program is free software: you can redistribute it and/or modify
    it under the terms of the GNU General Public License as published by
    the Free Software Foundation, either version 3 of the License, or
    (at your option) any later version.

    This program is distributed in the hope that it will be useful,
    but WITHOUT ANY WARRANTY; without even the implied warranty of
    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
    GNU General Public License for more details.

    You should have received a copy of the GNU General Public License
    along with this program.  If not, see <https://www.gnu.org/licenses/>.