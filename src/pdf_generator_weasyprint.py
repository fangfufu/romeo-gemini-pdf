import os
import weasyprint
import datetime
import html # For escaping
import sys

# Ensure the front_matter helper can be found
try:
    from src.front_matter_html import get_front_matter_html
except ImportError:
    project_root_for_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if project_root_for_path not in sys.path:
        sys.path.insert(0, project_root_for_path)
    from src.front_matter_html import get_front_matter_html

# --- KDP Constants (8.25x11) ---
# Defined for reference, actual control is via CSS
PAGE_WIDTH_IN = 8.25
PAGE_HEIGHT_IN = 11
GUTTER_MARGIN_IN = 0.875 # Inside
OUTSIDE_MARGIN_IN = 0.5
TOP_MARGIN_IN = 0.75
BOTTOM_MARGIN_IN = 0.75

# --- Main PDF Creation Function ---
def create_pdf_weasyprint(play_structure, output_filepath, css_filepath):
    """
    Generates a side-by-side PDF using WeasyPrint from HTML/CSS.

    Args:
        play_structure (list): List of dictionaries representing the play.
        output_filepath (str): Path to save the generated PDF.
        css_filepath (str): Path to the CSS file for styling.
    """
    print(f"Starting PDF generation with WeasyPrint: {output_filepath}")
    project_root = os.path.dirname(os.path.dirname(css_filepath)) # Infer project root from CSS path

    # --- Generate HTML Content ---
    print("Generating HTML content...")
    html_parts = []

    # 1. Add HTML Head / Basic Structure
    # Reference CSS relative to HTML base_url (project root)
    relative_css_path = os.path.relpath(css_filepath, project_root).replace('\\', '/')
    html_parts.append(f"""<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>Romeo and Juliet - Vernacular Adaptation</title>
    <link rel="stylesheet" href="{relative_css_path}">
</head>
<body>
""")

    # 2. Add Front Matter HTML
    print("Adding front matter HTML...")
    book_title = "Romeo and Juliet: A Contemporary Vernacular Adaptation"
    book_subtitle = "Side-by-Side Edition"
    adapter_name = "[Your Name Here]" # Replace
    copyright_holder = "[Your Name Here]" # Replace
    current_year = datetime.datetime.now().year
    try:
        front_matter_html_content = get_front_matter_html(
            title=book_title,
            subtitle=book_subtitle,
            adapter_name=adapter_name,
            copyright_holder=copyright_holder,
            current_year=current_year
        )
        html_parts.append(front_matter_html_content)
    except NameError:
         print("Warning: src.front_matter_html.get_front_matter_html not found or not imported correctly.")
    except Exception as fm_e:
         print(f"Warning: Error generating front matter HTML: {fm_e}")


    # 3. Add Main Play Content HTML
    print("Processing play structure elements for main body HTML...")
    html_parts.append('<div class="main-content">') # Div for main content

    item_count = 0 # Optional: only for final count printout
    for index, element in enumerate(play_structure):
        el_type = element.get('type')
        original_text = element.get('original', '')
        if el_type == 'stage_direction':
             original_text = original_text.replace('_', '') # Clean underscores

        # Convert newlines to <br> for HTML paragraphs WITHIN a single P tag method
        # original_html = original_text.replace('\n', '<br/>') # Use this if reverting to single P tag per chunk

        # Handle translation similarly
        raw_translated_text = element.get('translated', '') or ""
        # translated_html = raw_translated_text.replace('\n', '<br/>') # Use this if reverting
        is_error_translation = raw_translated_text.startswith('[Translation')
        is_placeholder_translation = raw_translated_text == '[Translated as part of previous chunk]'

        # --- Append HTML based on element type ---
        if el_type == 'heading':
            html_parts.append(f'<h1 class="heading">{html.escape(original_text)}</h1>\n')
            item_count+=1
        elif el_type == 'scene_marker':
            html_parts.append(f'<h2 class="scenemarker">{html.escape(original_text)}</h2>\n')
            item_count+=1
        elif el_type == 'speaker':
             html_parts.append(f'<p class="speaker">{html.escape(original_text)}</p>\n')
             item_count+=1
        elif el_type == 'stage_direction':
             html_parts.append(f'<p class="direction">{html.escape(original_text)}</p>\n') # Use cleaned text
             item_count+=1
        elif el_type == 'dialogue':
             # Container for the side-by-side pair
             html_parts.append('<div class="dialogue-pair">\n')

             # --- Left Column (Original Text - Multiple <p> tags) ---
             html_parts.append('  <div class="col-left">\n')
             original_lines = original_text.split('\n')
             for line in original_lines:
                 stripped_line = line.strip()
                 if stripped_line:
                      safe_line = html.escape(stripped_line)
                      html_parts.append(f'    <p>{safe_line}</p>\n')
                 elif len(original_lines) > 1: # Preserve blank lines between lines
                      html_parts.append('    <p>&nbsp;</p>\n')
             html_parts.append('  </div>\n') # End col-left

             # --- Right Column (Translated Text - Multiple <p> tags) ---
             html_parts.append('  <div class="col-right">\n')
             if is_placeholder_translation:
                 html_parts.append('    <p class="placeholder">&nbsp;</p>\n')
             elif is_error_translation:
                 safe_error = html.escape(raw_translated_text)
                 html_parts.append(f'    <p class="error">{safe_error}</p>\n')
             else:
                 translated_lines = raw_translated_text.split('\n')
                 for line in translated_lines:
                     stripped_line = line.strip()
                     if stripped_line:
                         safe_line = html.escape(stripped_line)
                         html_parts.append(f'    <p>{safe_line}</p>\n')
                     elif len(translated_lines) > 1: # Preserve blank lines
                         html_parts.append('    <p>&nbsp;</p>\n')
             html_parts.append('  </div>\n') # End col-right

             html_parts.append('</div>\n') # end dialogue-pair
             item_count += 1
        # else: ignore 'unknown' type

    html_parts.append('</div>\n') # end main-content
    html_parts.append("</body></html>")
    final_html = "".join(html_parts)
    print(f"Generated HTML for {item_count} elements.")

    # --- Generate PDF using WeasyPrint ---
    print("Rendering PDF with WeasyPrint...")
    try:
        # Ensure output directory exists
        output_dir = os.path.dirname(output_filepath)
        os.makedirs(output_dir, exist_ok=True)

        # Use a different variable name for the WeasyPrint HTML object
        html_doc = weasyprint.HTML(string=final_html, base_url=project_root) # Use project root as base URL
        css = weasyprint.CSS(filename=css_filepath)

        # Use the renamed variable here
        html_doc.write_pdf(output_filepath, stylesheets=[css])
        print(f"PDF generated successfully: {output_filepath}")

    except FileNotFoundError:
         print(f"Error: CSS file not found at {css_filepath}")
         print("Please ensure the CSS file exists.")
    except Exception as e:
        print(f"Error building PDF with WeasyPrint: {e}")
        import traceback
        traceback.print_exc()


# Example usage block for testing the generator directly
if __name__ == '__main__':
    print("Testing WeasyPrint generator structure (requires dummy data and CSS)...")
    # Construct paths relative to this script file
    try:
        script_dir = os.path.dirname(__file__)
        project_root_test = os.path.dirname(script_dir)
        if not project_root_test: project_root_test = '.'

        test_output_dir = os.path.join(project_root_test, 'output')
        os.makedirs(test_output_dir, exist_ok=True)
        test_pdf_filepath = os.path.join(test_output_dir, 'test_weasyprint_output.pdf')
        test_css_filepath = os.path.join(project_root_test, 'config', 'style_weasy.css')

        # Create minimal dummy data and structure
        dummy_play_structure = [
             {'type': 'heading', 'original': 'TEST TITLE', 'translated': None},
             {'type': 'speaker', 'original': 'SPEAKER', 'translated': None},
             {'type': 'dialogue', 'original': 'Line one.\nLine two.', 'translated': 'Trans line one.\nTrans line two is maybe longer.'},
             {'type': 'stage_direction', 'original': '[_Test Exit_]', 'translated': '[Test Exit.]'}, # Test underscore removal
        ]
        dummy_front_matter_path = os.path.join(project_root_test, 'src', 'front_matter_html.py')
        if not os.path.exists(dummy_front_matter_path):
             print(f"Warning: Front matter helper {dummy_front_matter_path} not found, skipping.")
             # Define dummy function if needed for testing
             def get_front_matter_html(*args, **kwargs): return "<div>Dummy Front Matter</div>"
             # Assign dummy function globally ONLY if needed for test scope
             # Be careful with global scope modification in real applications
             if 'src.front_matter_html' not in sys.modules:
                 # Mock the module if it wasn't importable
                 class MockFrontMatter:
                     get_front_matter_html = staticmethod(get_front_matter_html)
                 sys.modules['src.front_matter_html'] = MockFrontMatter()
             else: # If module exists, patch function? Or just rely on try/except in main call.
                 pass


        if not os.path.exists(test_css_filepath):
             print(f"Error: Cannot run test. CSS file not found at {test_css_filepath}")
        else:
             create_pdf_weasyprint(dummy_play_structure, test_pdf_filepath, test_css_filepath)

    except Exception as test_e:
        print(f"Error during test execution: {test_e}")