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
from src.pdf_generator_weasyprint import create_pdf_weasyprint

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

    # 3. Translation Loop
     # 3. Translation Loop (with Dialogue Chunking)
    print("\n--- Translation Phase (Chunking Dialogue) ---")
    translated_chunks_in_session = 0 # Count chunks translated
    api_errors = 0
    CHECKPOINT_INTERVAL = 10  # Save progress every N CHUNKS translated
    TRANSLATION_DELAY = 2 # Seconds between API calls

    total_elements = len(play_structure)
    index = 0
    while index < total_elements:
        element = play_structure[index]
        element_type = element.get('type')

        # --- Find speaker for context ---
        # Find the most recent speaker BEFORE the current index
        loop_current_speaker = None
        for i in range(index - 1, -1, -1):
            if play_structure[i].get('type') == 'speaker':
                loop_current_speaker = play_structure[i].get('original')
                break

        # --- Check if element needs translation ---
        needs_translation = False
        if element_type in ['dialogue', 'stage_direction'] and not element.get('translated'):
            needs_translation = True

        if not needs_translation:
            index += 1
            continue # Move to the next element

        # --- Process Translation ---
        original_texts_chunk = []
        indices_in_chunk = []
        context_speaker = loop_current_speaker # Speaker context for this chunk

        # If it's dialogue, try to chunk consecutive lines from the same speaker
        if element_type == 'dialogue':
            chunk_speaker = loop_current_speaker
            # Look ahead to gather consecutive dialogue from the same speaker
            j = index
            while j < total_elements:
                next_element = play_structure[j]
                # Find speaker for next element if needed (only matters for dialogue)
                next_speaker = None
                if next_element.get('type') == 'dialogue':
                     for i in range(j - 1, -1, -1):
                        if play_structure[i].get('type') == 'speaker':
                            next_speaker = play_structure[i].get('original')
                            break

                # Conditions to continue chunk: same type, same speaker, not already translated
                if (next_element.get('type') == 'dialogue' and
                        next_speaker == chunk_speaker and
                        not next_element.get('translated')):
                    original_texts_chunk.append(next_element['original'])
                    indices_in_chunk.append(j)
                    j += 1
                else:
                    break # End of chunk
            # Update outer loop index to skip processed elements
            next_index_after_chunk = j
        else:
            # Stage direction - process individually
            original_texts_chunk.append(element['original'])
            indices_in_chunk.append(index)
            next_index_after_chunk = index + 1
            context_speaker = None # No speaker context for directions


        # --- Translate the gathered chunk ---
        if original_texts_chunk:
            full_original_text = "\n".join(original_texts_chunk)
            print(f"\nTranslating chunk starting element {indices_in_chunk[0] + 1}/{total_elements} ({element_type}, {len(indices_in_chunk)} lines)...")
            print(f"Original: {full_original_text[:150]}...")

            # Construct the prompt
            style_instruction = "contemporary British urban vernacular (similar to the 'Chav' style previously discussed, focus on informal language, slang, potentially dropping 'h's or 'g's subtly where natural, but prioritize clarity and character voice over heavy caricature)"
            context = f" The speaker is {context_speaker}." if context_speaker and element_type == 'dialogue' else ""
            prompt_text = f"""Directly translate the following Shakespearean text chunk into {style_instruction}.{context} Maintain line breaks roughly where they occur in the original if possible, but prioritize natural flow in the target vernacular.
Do not provide commentary, explanations, or multiple options. Only provide the single best translation in the requested style.

Original Chunk:
"{full_original_text}"

Translated Chunk:"""

            translation_successful = False
            try:
                # --- Call Gemini API ---
                response = model.generate_content(prompt_text)

                # --- Process Response ---
                if response.parts:
                     full_translation = response.text.strip()
                     # Store full translation on the *first* element of the chunk
                     play_structure[indices_in_chunk[0]]['translated'] = full_translation
                     # Mark subsequent elements in the chunk
                     for k in indices_in_chunk[1:]:
                         play_structure[k]['translated'] = '[Translated as part of previous chunk]'
                     translated_chunks_in_session += 1
                     translation_successful = True
                     print(f"-> Translation: {full_translation[:150]}...")
                elif response.prompt_feedback.block_reason:
                     print(f"-> Blocked. Reason: {response.prompt_feedback.block_reason}")
                     error_message = f"[Translation Blocked: {response.prompt_feedback.block_reason}]"
                     api_errors += 1
                else:
                     print("-> Received empty response from API.")
                     error_message = "[Translation Error: Empty Response]"
                     api_errors += 1

            except Exception as e:
                print(f"-> API Error: {e}")
                error_message = f"[Translation Error: {type(e).__name__}]"
                api_errors += 1

            # If translation failed, mark all elements in chunk with error
            if not translation_successful:
                for k in indices_in_chunk:
                    play_structure[k]['translated'] = error_message

            # --- Rate Limiting ---
            time.sleep(TRANSLATION_DELAY)

            # --- Save Checkpoint Periodically (based on chunks) ---
            if translated_chunks_in_session > 0 and translated_chunks_in_session % CHECKPOINT_INTERVAL == 0:
                print(f"\n--- Saving checkpoint after {translated_chunks_in_session} chunks translated in this session ---")
                save_checkpoint(play_structure, CHECKPOINT_FILE)

        # Advance outer loop index
        index = next_index_after_chunk

    # --- End of Loop ---

    print("\n--- Translation Phase Complete ---")
    # Save final state
    if translated_chunks_in_session > 0: # Only save if work was done
         print("Saving final translation progress...")
         save_checkpoint(play_structure, CHECKPOINT_FILE)

    # Recalculate final counts
    final_translated_count = sum(1 for element in play_structure if element.get('translated') and not element.get('translated','').startswith('[')) # Count successful non-error/placeholder translations
    total_translatable = sum(1 for element in play_structure if element['type'] in ['dialogue', 'stage_direction'])
    print(f"Translation Summary:")
    print(f"- Chunks translated in this session: {translated_chunks_in_session}")
    # The 'final_translated_count' might be misleading now as it counts only first lines of chunks
    # print(f"- Total successfully translated elements: {final_translated_count} / {total_translatable}") # This is less meaningful now
    print(f"- API Errors/Blocks encountered: {api_errors}")
    
    # Example of how to check progress after loop (we'll build the loop next):
    final_translated_count = sum(1 for element in play_structure if element.get('translated'))
    total_translatable = sum(1 for element in play_structure if element['type'] in ['dialogue', 'stage_direction'])
    print(f"Translation status: {final_translated_count} / {total_translatable} elements potentially translated.")


    # 4. PDF Generation
    print("\n--- PDF Generation Phase (WeasyPrint) ---")
    if play_structure:
        pdf_output_filepath = os.path.join(OUTPUT_DIR, 'romeo_weasyprint_side_by_side.pdf') # New name
        css_filepath = os.path.join(PROJECT_ROOT, 'config', 'style_weasy.css') # Path to CSS
        try:
            os.makedirs(OUTPUT_DIR, exist_ok=True) # Ensure output dir exists
            # NOTE: Need to create/update front_matter_html helper first!
            # For now, just call with main structure
            create_pdf_weasyprint(play_structure, pdf_output_filepath, css_filepath)
        except Exception as e:
            print(f"An error occurred during WeasyPrint PDF generation: {e}")
    else:
        print("Skipping PDF generation because play structure is empty.")

if __name__ == "__main__":
    main()