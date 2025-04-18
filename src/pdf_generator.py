import os
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, NextPageTemplate
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors

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

def draw_page_number(canvas, doc):
    """Draws the page number centered at the bottom of the page."""
    page_num = canvas.getPageNumber()
    text = f"Page {page_num}"
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    # Calculate position: Centered horizontally, positioned within bottom margin
    x_position = PAGE_WIDTH / 2
    y_position = 0.5 * inch # Adjust this distance from the bottom edge if needed
    canvas.drawCentredString(x_position, y_position, text)
    canvas.restoreState()

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

    # --- Define Page Templates ---
    # For simplicity now, we'll use one template showing both columns for side-by-side Tables
    # Later, we could add page number drawing etc. here
    main_frame = Frame(OUTSIDE_MARGIN, BOTTOM_MARGIN, # Use outside margin for calculations
                       PAGE_WIDTH - OUTSIDE_MARGIN - GUTTER_MARGIN, # Total usable width
                       PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN,
                       id='main', leftPadding=0, bottomPadding=0,
                       rightPadding=0, topPadding=0)

    doc.addPageTemplates([
        PageTemplate(id='main',
                     frames=[main_frame],
                     onPage=draw_page_number) # Call our function on each page
    ])

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

    # --- Build Story (List of Flowables) ---
    story = []
    print("Processing play structure into PDF flowables...")
    story = []
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