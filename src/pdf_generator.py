import os
from reportlab.platypus import (
    BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle,
    NextPageTemplate, PageBreak
)
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
from src.front_matter import get_front_matter_story # Add this import
import datetime # Needed to get the current year

# --- KDP Constants (6x9 Hardback, >151 pages) ---
PAGE_WIDTH = 6 * inch
PAGE_HEIGHT = 9 * inch
GUTTER_MARGIN = 0.875 * inch # Inside margin
OUTSIDE_MARGIN = 0.5 * inch
TOP_MARGIN = 0.75 * inch
BOTTOM_MARGIN = 0.75 * inch
COLUMN_GAP = 0.25 * inch

# Calculate usable width and column width
USABLE_WIDTH = PAGE_WIDTH - GUTTER_MARGIN - OUTSIDE_MARGIN
COLUMN_WIDTH = (USABLE_WIDTH - COLUMN_GAP) / 2

def int_to_roman(num):
    """Converts an integer to a lowercase Roman numeral string."""
    if not 0 < num < 4000: # Basic range check
        return str(num) # Return as string if out of typical range
    val = [
        1000, 900, 500, 400,
        100, 90, 50, 40,
        10, 9, 5, 4,
        1
        ]
    syb = [
        "m", "cm", "d", "cd",
        "c", "xc", "l", "xl",
        "x", "ix", "v", "iv",
        "i"
        ]
    roman_num = ''
    i = 0
    while num > 0:
        for _ in range(num // val[i]):
            roman_num += syb[i]
            num -= val[i]
        i += 1
    return roman_num

# We'll rename this slightly and create two versions
def _draw_page_number_base(canvas, doc, number_format_func):
    """Base function to draw page number, using a formatting function."""
    page_num = canvas.getPageNumber()
    #Often, page numbers are omitted on the very first few pages (like title page)
    # Let's skip numbering for page 1 and 2 for now (adjust if needed)
    if page_num <= 3:
         return

    try:
        text = number_format_func(page_num) # Apply formatting
    except Exception:
        text = str(page_num) # Fallback

    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    x_position = PAGE_WIDTH / 2
    y_position = 0.5 * inch # Adjust this distance from the bottom edge if needed
    canvas.drawCentredString(x_position, y_position, text)
    canvas.restoreState()

def draw_roman_page_number(canvas, doc):
    """Draws page number as lowercase Roman numeral."""
    _draw_page_number_base(canvas, doc, int_to_roman)

# This needs modification to handle restarting the count
_main_content_start_page = None # Module-level variable to track start page

def draw_arabic_page_number(canvas, doc):
    """Draws page number as Arabic numeral, restarting from 1 for main content."""
    global _main_content_start_page
    current_abs_page = canvas.getPageNumber()

    # If this is the first time we're drawing an Arabic number, record the page
    if _main_content_start_page is None:
         # We assume this function is ONLY called for the main content template
         # If front matter had exactly N pages, this function is first called
         # when canvas.getPageNumber() is N+1.
         _main_content_start_page = current_abs_page

    # Calculate the displayed page number
    display_page_num = current_abs_page - _main_content_start_page + 1

    # Reuse the base drawing function, passing a simple string conversion
    _draw_page_number_base(canvas, doc, lambda num: str(display_page_num)) # Format using calculated num

def create_side_by_side_pdf(play_structure, output_filepath):
    """
    Generates a side-by-side PDF from the parsed play structure.

    Args:
        play_structure (list): List of dictionaries representing the play.
        output_filepath (str): Path to save the generated PDF.
    """
    print(f"Starting PDF generation: {output_filepath}")
    doc = BaseDocTemplate(output_filepath,
                          pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
                          title="Romeo and Juliet - Vernacular Translation",
                          author="Adapted from Shakespeare")

    # --- Define Frames for Mirrored Margins ---
    # Odd pages (gutter on left)
    frame_l_odd = Frame(OUTSIDE_MARGIN, BOTTOM_MARGIN,
                        COLUMN_WIDTH, PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN,
                        id='col_l_odd', leftPadding=0, bottomPadding=0,
                        rightPadding=0, topPadding=0)
    frame_r_odd = Frame(OUTSIDE_MARGIN + COLUMN_WIDTH + COLUMN_GAP, BOTTOM_MARGIN,
                        COLUMN_WIDTH, PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN,
                        id='col_r_odd', leftPadding=0, bottomPadding=0,
                        rightPadding=0, topPadding=0)

    # Even pages (gutter on right)
    frame_l_even = Frame(GUTTER_MARGIN, BOTTOM_MARGIN, # Starts after gutter margin
                         COLUMN_WIDTH, PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN,
                         id='col_l_even', leftPadding=0, bottomPadding=0,
                         rightPadding=0, topPadding=0)
    frame_r_even = Frame(GUTTER_MARGIN + COLUMN_WIDTH + COLUMN_GAP, BOTTOM_MARGIN,
                         COLUMN_WIDTH, PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN,
                         id='col_r_even', leftPadding=0, bottomPadding=0,
                         rightPadding=0, topPadding=0)
    
    # --- Define Frames ---
    main_frame = Frame(OUTSIDE_MARGIN, BOTTOM_MARGIN, # Use outside margin for calculations
                       PAGE_WIDTH - OUTSIDE_MARGIN - GUTTER_MARGIN, # Total usable width
                       PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN,
                       id='main', leftPadding=0, bottomPadding=0,
                       rightPadding=0, topPadding=0)

    # --- Define Page Templates (NOW WE NEED TWO) ---
    front_matter_template = PageTemplate(id='front_matter',
                                         frames=[main_frame],
                                         onPage=draw_roman_page_number) # Use Roman numeral drawer

    main_body_template = PageTemplate(id='main_body',
                                      frames=[main_frame],
                                      onPage=draw_arabic_page_number) # Use Arabic numeral drawer

    # Add BOTH templates to the document
    doc.addPageTemplates([front_matter_template, main_body_template])

    # --- Define Paragraph Styles ---
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='OriginalText', parent=styles['Normal'], fontSize=10, leading=12, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='TranslatedText', parent=styles['Normal'], fontSize=10, leading=12, alignment=TA_LEFT))
    styles.add(ParagraphStyle(name='Speaker', parent=styles['Normal'], fontSize=10, leading=12, alignment=TA_CENTER, spaceAfter=6, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='Heading', parent=styles['h1'], fontSize=14, leading=16, alignment=TA_CENTER, spaceAfter=12, spaceBefore=12))
    styles.add(ParagraphStyle(name='SceneMarker', parent=styles['h2'], fontSize=12, leading=14, alignment=TA_CENTER, spaceAfter=10, spaceBefore=10))
    styles.add(ParagraphStyle(name='StageDirection', parent=styles['Normal'], fontSize=9, leading=11, alignment=TA_LEFT, fontName='Helvetica-Oblique', leftIndent=0.5*inch, rightIndent=0.5*inch))
    styles.add(ParagraphStyle(name='StageDirectionCentered', parent=styles['Normal'], fontSize=9, leading=11, alignment=TA_CENTER, fontName='Helvetica-Oblique', spaceBefore=6, spaceAfter=6))
    styles.add(ParagraphStyle(name='StageDirectionTranslated', parent=styles['StageDirection'])) # Same style for translated directions for now
    styles.add(ParagraphStyle(name='ErrorText', parent=styles['TranslatedText'], textColor=colors.red))
    styles.add(ParagraphStyle(name='CopyrightStyle', parent=styles['Normal'], fontSize=8, leading=10, alignment=TA_LEFT, spaceBefore=6, spaceAfter=6))

    # --- Build Story (List of Flowables) ---   
    print("Processing play structure into PDF flowables...")
    story = []

    print("Adding front matter...")
    book_title = "Romeo and Juliet: A Contemporary Vernacular Adaptation"
    book_subtitle = "Side-by-Side Edition" # Or "" if no subtitle
    adapter_name = "Fufu Fang" # Replace with your name/entity
    copyright_holder = "Fufu Fang" # Replace with your name/entity
    current_year = datetime.datetime.now().year

    front_matter_flowables = get_front_matter_story(
        styles=styles,
        title=book_title,
        subtitle=book_subtitle,
        adapter_name=adapter_name,
        copyright_holder=copyright_holder,
        current_year=current_year
    )
    story.extend(front_matter_flowables) # Add the front matter pages to the story
    
    # After adding ALL front matter, tell ReportLab to switch to the main_body template
    # for the *next* page that begins *after* this point in the story.
    story.append(NextPageTemplate('main_body'))
    # Explicitly reset the global tracker when switching templates
    global _main_content_start_page
    _main_content_start_page = None # Reset before build
    
    story.append(PageBreak())

    # --- Now process the main play structure ---
    print("Processing play structure elements for main body...")
    # The loop starts here, the first element (Prologue heading) will now be on a new page
    # using the main_body_template
    
    item_count = 0 # Counter for actual items added to story

    for index, element in enumerate(play_structure):
        el_type = element.get('type')
        original_text = element.get('original', '')
        translated_text = element.get('translated', '') or "" # Ensure it's a string

        # Choose style for translated text (use ErrorText if it looks like an error)
        trans_style = styles['ErrorText'] if translated_text.startswith('[Translation') else styles['TranslatedText']
        dir_trans_style = styles['ErrorText'] if translated_text.startswith('[Translation') else styles['StageDirectionTranslated']

        if el_type == 'heading':
            story.append(Paragraph(original_text, styles['Heading']))
            story.append(Spacer(1, 0.2*inch))
            item_count += 1
        elif el_type == 'scene_marker':
            story.append(Paragraph(original_text, styles['SceneMarker']))
            story.append(Spacer(1, 0.15*inch))
            item_count += 1
        elif el_type == 'speaker':
            # Add space before speaker for clarity
            if index > 0 and play_structure[index-1].get('type') not in ['heading', 'scene_marker', 'speaker']:
                 story.append(Spacer(1, 0.1*inch))
            story.append(Paragraph(original_text, styles['Speaker']))
            # No space after speaker, space comes from table below
            item_count += 1
        elif el_type == 'dialogue':
            # Create paragraphs for original and translated text
            p_orig = Paragraph(original_text, styles['OriginalText'])
            p_trans = Paragraph(translated_text, trans_style)
            # Create a table with two columns for side-by-side layout
            table_data = [[p_orig, p_trans]]
            # TableStyle: VALIGN TOP, no borders (GRID set to transparent)
            ts = TableStyle([
                ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ('GRID', (0,0), (-1,-1), 0.5, colors.transparent),
                # Optional: Add padding if needed
                # ('LEFTPADDING', (0,0), (-1,-1), 0),
                # ('RIGHTPADDING', (0,0), (-1,-1), 0),
            ])
            # Create the table, specifying column widths
            dialogue_table = Table(table_data, colWidths=[COLUMN_WIDTH, COLUMN_WIDTH], style=ts)
            story.append(dialogue_table)
            story.append(Spacer(1, 0.05*inch)) # Small space after dialogue lines
            item_count += 1
        elif el_type == 'stage_direction':
             original_text = element.get('original', '') # Get the original text
             cleaned_original_text = original_text.replace('_', '')
             story.append(Spacer(1, 0.1*inch)) # Space before direction
             # Use the CLEANED text in the Paragraph
             story.append(Paragraph(cleaned_original_text, styles['StageDirectionCentered']))
             story.append(Spacer(1, 0.1*inch)) # Space after direction
             item_count += 1
        # else: ignore 'unknown' type for now

    print(f"Added {item_count} elements to the PDF story.")


    # --- Build the PDF ---
    print("Building PDF document...")
    try:
        # Reset page number tracker before building
        _main_content_start_page = None
        doc.build(story)
        print(f"PDF generated successfully: {output_filepath}")
    except Exception as e:
        print(f"Error building PDF: {e}")

# Example usage (if run directly, for testing)
if __name__ == '__main__':
    # Create some dummy data matching the play_structure format
    dummy_play = [
        {'type': 'heading', 'original': 'THE PROLOGUE', 'translated': None},
        {'type': 'stage_direction', 'original': 'Enter Chorus.', 'translated': 'Chorus comes on.'},
        {'type': 'speaker', 'original': 'CHORUS', 'translated': None},
        {'type': 'dialogue', 'original': 'Two households, both alike in dignity,', 'translated': 'Two crews, yeah, both proper big families,'},
        {'type': 'dialogue', 'original': 'In fair Verona, where we lay our scene,', 'translated': "Right here in Verona, where this story's set,"},
        {'type': 'stage_direction', 'original': '[_Exit._]', 'translated': '[He leaves.]'},
        {'type': 'scene_marker', 'original': 'ACT I', 'translated': None},
        {'type': 'scene_marker', 'original': 'SCENE I. A public place.', 'translated': None},
         {'type': 'dialogue', 'original': 'This is a much longer line to test how wrapping works within the column when generating the PDF output.', 'translated': 'This here is the translated version, innit? Gotta check if the words wrap around alright when they go in the PDF column.'},

    ]
    test_output_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'output')
    os.makedirs(test_output_dir, exist_ok=True)
    test_filepath = os.path.join(test_output_dir, 'test_pdf_generation.pdf')
    create_side_by_side_pdf(dummy_play, test_filepath)