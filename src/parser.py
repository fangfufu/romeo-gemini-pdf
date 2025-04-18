# src/parser.py
import re
import os

def parse_play(filepath):
    """
    Parses a plain text file of a play (like Romeo and Juliet) into a structured list.

    Args:
        filepath (str): The path to the input text file.

    Returns:
        list: A list of dictionaries, where each dictionary represents an element
              (heading, scene_marker, speaker, dialogue, stage_direction, unknown).
    """
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"Input file not found at: {filepath}")

    play_structure = []
    current_speaker = None

    try:
        # Use 'utf-8-sig' to automatically handle/remove the BOM if present
        with open(filepath, 'r', encoding='utf-8-sig') as f:
            for line_num, line in enumerate(f, 1): # Add line number for debugging if needed
                stripped_line = line.strip()

                # Skip empty lines
                if not stripped_line:
                    continue

                # --- Perform necessary checks ONCE per line, UPFRONT ---
                # Calculate these flags/matches for use in the conditional logic below
                stage_direction_keywords = ['Enter ', 'Exit ', 'Exeunt', 'Re-enter ']
                is_bracketed = (stripped_line.startswith('[') and stripped_line.endswith(']')) or \
                               (stripped_line.startswith('(') and stripped_line.endswith(')'))
                starts_with_keyword = any(stripped_line.startswith(keyword) for keyword in stage_direction_keywords)

                # Perform the regex check for potential speakers
                speaker_regex = r'^([A-Z][A-Z\s]{1,})(\.?)$'
                is_likely_speaker = re.match(speaker_regex, stripped_line)
                # --- End upfront checks ---


                # --- Start the main conditional chain to classify the line type ---
                # Order Matters! Check most specific types first.

                # Check for specific known headings first
                if stripped_line == 'THE PROLOGUE': # Specific check is robust
                    play_structure.append({'type': 'heading', 'original': stripped_line, 'translated': None})
                    print(f"L{line_num}: Found Heading: {stripped_line}")
                    current_speaker = None # Reset speaker after a major heading
                    continue

                # Check for Act/Scene markers
                elif stripped_line.startswith("ACT ") or stripped_line.startswith("SCENE "):
                    play_structure.append({'type': 'scene_marker', 'original': stripped_line, 'translated': None})
                    current_speaker = None
                    print(f"L{line_num}: Found Scene Marker: {stripped_line}")
                    continue

                # General Heading Check (e.g., other ALL CAPS lines NOT matching speaker format)
                # Placed BEFORE speaker check now
                elif stripped_line.isupper() and not is_likely_speaker:
                    play_structure.append({'type': 'heading', 'original': stripped_line, 'translated': None})
                    print(f"L{line_num}: Found Heading (General): {stripped_line}") # Debug print
                    current_speaker = None # Reset speaker after a major heading
                    continue

                # Check for stage directions (brackets OR common keywords)
                # Uses checks performed above
                elif is_bracketed or (starts_with_keyword and not is_likely_speaker):
                     play_structure.append({'type': 'stage_direction', 'original': stripped_line, 'translated': ''})
                     print(f"L{line_num}: Found Direction: {stripped_line}")
                     continue

                # Check for speaker names (only if not classified above)
                # Uses checks performed above
                elif is_likely_speaker:
                    # Check if it's identical to the previous speaker to avoid duplicates if format is weird
                    new_speaker_name = is_likely_speaker.group(1).strip()
                    if new_speaker_name != current_speaker:
                        current_speaker = new_speaker_name
                        play_structure.append({'type': 'speaker', 'original': current_speaker, 'translated': None})
                        print(f"L{line_num}: Found Speaker: {current_speaker}")
                    # else: # Optional: Handle case where speaker name might repeat redundantly
                    #    print(f"L{line_num}: Skipping redundant speaker: {new_speaker_name}")
                    continue

                # Assume it's dialogue if a speaker is currently set
                elif current_speaker:
                    play_structure.append({'type': 'dialogue', 'original': stripped_line, 'translated': ''})
                    # print(f"L{line_num}: Found Dialogue: {stripped_line}") # Keep commented unless debugging dialogue
                    continue

                # Handle lines that don't match any known type LAST
                else:
                     play_structure.append({'type': 'unknown', 'original': stripped_line, 'translated': None})
                     print(f"L{line_num}: Found Unknown: {stripped_line}")

                 # --- End the main conditional chain ---

    except Exception as e:
        print(f"Error reading or parsing file on line {line_num if 'line_num' in locals() else 'unknown'}: {e}")
        # Optionally re-raise the exception if you want the program to stop on error
        # raise e
        return [] # Return empty list on error

    return play_structure

# Example usage block for testing the parser directly
if __name__ == '__main__':
    # Construct the path to the data file relative to this script's location
    # Assumes script is in 'src/' and data is in '../data/'
    try:
        script_dir = os.path.dirname(__file__) # Directory of parser.py (src/)
        project_root = os.path.dirname(script_dir) # Parent directory (project root)
        # Handle case where script is run from project root directly
        if not project_root:
             project_root = '.'
             script_dir = os.path.join(project_root, 'src')

        data_file = os.path.join(project_root, 'data', 'romeo_and_juliet.txt')

        if not os.path.exists(data_file):
             # Fallback if running script from within src directory
             data_file = os.path.join('..', 'data', 'romeo_and_juliet.txt')

        print(f"Attempting to parse: {data_file}")
        parsed_play = parse_play(data_file)

        print(f"\nParsing complete. Parsed {len(parsed_play)} elements.")

        # Print first 20 elements for verification
        print("\nFirst 20 parsed elements:")
        for i, element in enumerate(parsed_play[:20]):
             print(f"{i}: {element}")

        # Optional: Print last 10 elements
        # print("\nLast 10 parsed elements:")
        # for i, element in enumerate(parsed_play[-10:], start=len(parsed_play)-10):
        #      print(f"{i}: {element}")

    except FileNotFoundError as fnf_error:
        print(f"\nError: {fnf_error}")
        print("Please ensure 'romeo_and_juliet.txt' is inside the 'data' directory relative to your project root.")
    except Exception as general_error:
        print(f"\nAn unexpected error occurred: {general_error}")