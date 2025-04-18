# src/main.py

import os
import sys

# --- Add project root to sys.path ---
# This ensures Python can find the 'src' package when running main.py directly
# Calculates the project root directory (the parent of 'src')
PROJECT_ROOT_FOR_PATH = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if PROJECT_ROOT_FOR_PATH not in sys.path:
    sys.path.insert(0, PROJECT_ROOT_FOR_PATH)
# --- End sys.path modification ---

import google.generativeai as genai
from dotenv import load_dotenv
import time
import pickle
import sys
from src.pdf_generator import create_side_by_side_pdf

# Ensure the parser can be found (if running main.py from project root)
# If 'src' is not in the Python path, this helps find the parser module
try:
    from src.parser import parse_play
except ImportError:
    # If run with 'python src/main.py', src might not be in path directly
    # Add project root to path to allow 'from src.parser import ...'
    project_root_for_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root_for_path not in sys.path:
        sys.path.insert(0, project_root_for_path)
    from src.parser import parse_play

# --- Configuration ---
# Define file paths relative to the project root
try:
    PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if not PROJECT_ROOT: # Handle potential issues finding root
       PROJECT_ROOT = os.path.abspath('.')
except NameError:
    # If __file__ is not defined (e.g. in some interactive environments)
    PROJECT_ROOT = os.path.abspath('.')

DATA_FILE = os.path.join(PROJECT_ROOT, 'data', 'romeo_and_juliet.txt')
CHECKPOINT_DIR = os.path.join(PROJECT_ROOT, 'checkpoints')
CHECKPOINT_FILE = os.path.join(CHECKPOINT_DIR, 'translation_progress.pkl')
OUTPUT_DIR = os.path.join(PROJECT_ROOT, 'output') # Define for later PDF output

# --- Helper Functions ---

def load_api_key():
    """Loads the Gemini API key from .env file."""
    load_dotenv(dotenv_path=os.path.join(PROJECT_ROOT, '.env')) # Specify path to .env
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("Gemini API Key not found. Make sure it's set in your .env file in the project root.")
    return api_key

def load_checkpoint(filepath):
    """Loads the play structure from a checkpoint file if it exists."""
    if os.path.exists(filepath):
        print(f"Loading checkpoint from: {filepath}")
        try:
            with open(filepath, 'rb') as f:
                return pickle.load(f)
        except (pickle.UnpicklingError, EOFError, FileNotFoundError, Exception) as e:
            print(f"Warning: Error loading checkpoint ({e}). Starting fresh parse.")
            # Optionally delete corrupted checkpoint: os.remove(filepath)
            return None
    return None

def save_checkpoint(data, filepath):
    """Saves the play structure to a checkpoint file."""
    try:
        os.makedirs(os.path.dirname(filepath), exist_ok=True) # Ensure dir exists
        with open(filepath, 'wb') as f:
            pickle.dump(data, f)
        # print(f"Checkpoint saved to: {filepath}") # Make less verbose during loop
    except Exception as e:
        print(f"Error saving checkpoint: {e}")

# --- Main Execution Logic ---

def main():
    """Main function to parse, translate, and eventually generate PDF."""
    print("--- Starting Romeo & Juliet Translation Project ---")
    start_time = time.time()

    # 1. Load API Key and Configure Gemini
    try:
        api_key = load_api_key()
        genai.configure(api_key=api_key)
        # Specify model - check available models, 'gemini-pro' is common
        model = genai.GenerativeModel('gemma-3-27b-it')
        print("Gemini API configured successfully.")
    except ValueError as e:
        print(f"Configuration Error: {e}")
        return # Exit if API key is missing
    except Exception as e:
        print(f"Error configuring Gemini API: {e}")
        return

    # 2. Load or Parse Play Structure
    play_structure = load_checkpoint(CHECKPOINT_FILE)
    if play_structure is None:
        print(f"No valid checkpoint found. Parsing source file: {DATA_FILE}")
        try:
            play_structure = parse_play(DATA_FILE)
            if not play_structure:
                print("Parsing failed or returned empty structure. Exiting.")
                return
            print(f"Parsing complete. Found {len(play_structure)} elements.")
            # Save initial parsed structure as first checkpoint
            save_checkpoint(play_structure, CHECKPOINT_FILE)
            print(f"Initial checkpoint saved to {CHECKPOINT_FILE}")
        except FileNotFoundError as e:
            print(f"Error: Source file not found at {DATA_FILE}")
            print("Please ensure 'romeo_and_juliet.txt' is in the 'data' directory.")
            return
        except Exception as e:
            print(f"An unexpected error occurred during parsing: {e}")
            return
    else:
         already_translated_count = sum(1 for element in play_structure if element.get('translated'))
         print(f"Resumed from checkpoint. {len(play_structure)} elements loaded, {already_translated_count} previously translated.")

    # 3. Translation Loop (Placeholder - To be implemented next)
    # 3. Translation Loop
    print("\n--- Translation Phase ---")
    translated_in_session = 0
    api_errors = 0
    CHECKPOINT_INTERVAL = 20  # Save progress every N translations
    TRANSLATION_DELAY = 2 # Seconds between API calls to avoid rate limits

    # Keep track of the current speaker for context
    loop_current_speaker = None

    total_elements = len(play_structure)
    for index, element in enumerate(play_structure):

        # Update current speaker when encountered
        if element['type'] == 'speaker':
            loop_current_speaker = element['original']
            continue # Speakers don't need translation

        # Check if element is translatable and not already translated
        if element['type'] in ['dialogue', 'stage_direction'] and not element.get('translated'):

            original_text = element['original']
            element_type = element['type']
            print(f"\nTranslating element {index + 1}/{total_elements} ({element_type}): {original_text[:80]}...") # Print start of text

            # --- Construct the Prompt ---
            # Customize this prompt to refine the style!
            style_instruction = "British 'Chav' style, but prioritize character voice over heavy caricature"
            context = f" The speaker is {loop_current_speaker}." if element_type == 'dialogue' and loop_current_speaker else ""

            # Make the instruction more direct and add a negative constraint
            prompt_text = f"""Directly translate the following Shakespearean text into {style_instruction}. {context} 
Do not provide commentary, explanations, or multiple options. Only provide the single best translation in the requested style.
Original: "{original_text}"
Translation:"""

            try:
                # --- Call Gemini API ---
                # Note: Adjust generation_config if needed (temperature, etc.)
                response = model.generate_content(prompt_text)

                # --- Process Response ---
                # Check for safety blocks or empty response before accessing text
                if response.parts:
                     translation = response.text.strip()
                     element['translated'] = translation
                     translated_in_session += 1
                     print(f"-> Translation: {translation[:80]}...") # Print start of translation
                elif response.prompt_feedback.block_reason:
                     print(f"-> Blocked. Reason: {response.prompt_feedback.block_reason}")
                     element['translated'] = f"[Translation Blocked: {response.prompt_feedback.block_reason}]" # Mark as blocked
                     api_errors += 1 # Count blocks as errors for summary
                else:
                     # Handle cases where response might be empty but not explicitly blocked
                     print("-> Received empty response from API.")
                     element['translated'] = "[Translation Error: Empty Response]"
                     api_errors += 1

            except Exception as e:
                # Catch potential API errors (rate limits, connection issues, etc.)
                print(f"-> API Error: {e}")
                api_errors += 1
                # Optional: could add logic here to retry after a longer delay
                # For now, we just mark it and continue
                element['translated'] = f"[Translation Error: {type(e).__name__}]"


            # --- Rate Limiting ---
            # Pause *after* every attempt (success or failure) that hit the API
            # print(f"Waiting {TRANSLATION_DELAY}s...") # Optional verbose wait message
            time.sleep(TRANSLATION_DELAY)

            # --- Save Checkpoint Periodically ---
            if translated_in_session > 0 and translated_in_session % CHECKPOINT_INTERVAL == 0:
                print(f"\n--- Saving checkpoint after {translated_in_session} translations in this session ---")
                save_checkpoint(play_structure, CHECKPOINT_FILE)

    # --- End of Loop ---

    print("\n--- Translation Phase Complete ---")
    # Save final state
    if translated_in_session > 0: # Only save if work was done
         print("Saving final translation progress...")
         save_checkpoint(play_structure, CHECKPOINT_FILE)

    final_translated_count = sum(1 for element in play_structure if element.get('translated') and not element.get('translated','').startswith('[')) # Count successful non-error translations
    total_translatable = sum(1 for element in play_structure if element['type'] in ['dialogue', 'stage_direction'])
    print(f"Translation Summary:")
    print(f"- Translated in this session: {translated_in_session}")
    print(f"- Total successfully translated: {final_translated_count} / {total_translatable}")
    print(f"- API Errors/Blocks encountered: {api_errors}")

    # Example of how to check progress after loop (we'll build the loop next):
    final_translated_count = sum(1 for element in play_structure if element.get('translated'))
    total_translatable = sum(1 for element in play_structure if element['type'] in ['dialogue', 'stage_direction'])
    print(f"Translation status: {final_translated_count} / {total_translatable} elements potentially translated.")


    # 4. PDF Generation
    print("\n--- PDF Generation Phase ---")
    if play_structure: # Only generate if we have data
        pdf_output_filepath = os.path.join(OUTPUT_DIR, 'romeo_vernacular_side_by_side.pdf')
        try:
            # Ensure output directory exists
            os.makedirs(OUTPUT_DIR, exist_ok=True)
            create_side_by_side_pdf(play_structure, pdf_output_filepath)
        except Exception as e:
            print(f"An error occurred during PDF generation: {e}")
    else:
        print("Skipping PDF generation because play structure is empty.")


    end_time = time.time()
    print(f"\n--- Project execution finished in {end_time - start_time:.2f} seconds ---")


if __name__ == "__main__":
    main()