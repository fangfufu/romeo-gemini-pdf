import os
import re
from reportlab.platypus import BaseDocTemplate, PageTemplate, Frame, Paragraph, Spacer, Table, TableStyle, NextPageTemplate, PageBreak
from reportlab.lib.units import inch, cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_JUSTIFY
from reportlab.lib import colors
import datetime
from src.front_matter import get_front_matter_story # Ensure this import is correct

# --- Helper for Roman Numerals ---
def int_to_roman(num):
    # (Keep the int_to_roman function as defined previously)
    if not 0 < num < 4000: return str(num)
    val = [1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1]
    syb = ["m", "cm", "d", "cd", "c", "xc", "l", "xl", "x", "ix", "v", "iv", "i"]
    roman_num = ''; i = 0
    while num > 0:
        for _ in range(num // val[i]): roman_num += syb[i]; num -= val[i]
        i += 1
    return roman_num

# --- KDP Constants (8.25x11 Hardback, >151 pages) ---
PAGE_WIDTH = 8.25 * inch
PAGE_HEIGHT = 11 * inch
GUTTER_MARGIN = 0.875 * inch # Verify on KDP
OUTSIDE_MARGIN = 0.5 * inch   # Recommended aesthetic margin
TOP_MARGIN = 0.75 * inch      # Using 0.75 to maximize frame height
BOTTOM_MARGIN = 0.75 * inch     # Using 0.75 to maximize frame height
COLUMN_GAP = 0.25 * inch      # Gap between the two columns

# Recalculate usable width and column width
USABLE_WIDTH = PAGE_WIDTH - GUTTER_MARGIN - OUTSIDE_MARGIN
COLUMN_WIDTH = (USABLE_WIDTH - COLUMN_GAP) / 2
FRAME_HEIGHT = PAGE_HEIGHT - TOP_MARGIN - BOTTOM_MARGIN # Approx 9.5 inches = 684 points

print(f"--- PDF Settings ---")
print(f"Page Size: {PAGE_WIDTH/inch}\" x {PAGE_HEIGHT/inch}\"")
print(f"Margins (In/Out/Top/Bot): {GUTTER_MARGIN/inch}\" / {OUTSIDE_MARGIN/inch}\" / {TOP_MARGIN/inch}\" / {BOTTOM_MARGIN/inch}\"")
print(f"Usable Width: {USABLE_WIDTH/inch}\"")
print(f"Column Width: {COLUMN_WIDTH/inch}\"")
print(f"Frame Height: {FRAME_HEIGHT/inch}\" ({FRAME_HEIGHT} points)")
print(f"--- End PDF Settings ---")


# --- Page Numbering Functions (Unchanged) ---
_main_content_start_page = None

def _draw_page_number_base(canvas, doc, number_format_func):
    page_num = canvas.getPageNumber()
    try: text = number_format_func(page_num)
    except Exception: text = str(page_num)
    canvas.saveState()
    canvas.setFont('Helvetica', 9)
    x_position = PAGE_WIDTH / 2
    y_position = 0.5 * inch
    canvas.drawCentredString(x_position, y_position, text)
    canvas.restoreState()

def draw_roman_page_number(canvas, doc):
    _draw_page_number_base(canvas, doc, int_to_roman)

def draw_arabic_page_number(canvas, doc):
    global _main_content_start_page
    current_abs_page = canvas.getPageNumber()
    if _main_content_start_page is None:
         _main_content_start_page = current_abs_page
    display_page_num = max(1, current_abs_page - _main_content_start_page + 1)
    _draw_page_number_base(canvas, doc, lambda num: str(display_page_num))

# --- Main PDF Creation Function ---
def create_side_by_side_pdf(play_structure, output_filepath):
    print(f"Starting PDF generation: {output_filepath}")
    doc = BaseDocTemplate(output_filepath,
                          pagesize=(PAGE_WIDTH, PAGE_HEIGHT),
                          title="Romeo and Juliet - Vernacular Translation",
                          author="Adapted from Shakespeare",
                          leftMargin=OUTSIDE_MARGIN, rightMargin=GUTTER_MARGIN,
                          topMargin=TOP_MARGIN, bottomMargin=BOTTOM_MARGIN)

    # --- Define Frames ---
    main_frame = Frame(doc.leftMargin, doc.bottomMargin, doc.width, doc.height,
                       id='main', leftPadding=6, bottomPadding=6, rightPadding=6, topPadding=6)

    # --- Define Page Templates ---
    front_matter_template = PageTemplate(id='front_matter', frames=[main_frame], onPage=draw_roman_page_number)
    main_body_template = PageTemplate(id='main_body', frames=[main_frame], onPage=draw_arabic_page_number)
    doc.addPageTemplates([front_matter_template, main_body_template])

    # --- Define Paragraph Styles ---
    styles = getSampleStyleSheet()
    styles.add(ParagraphStyle(name='OriginalText', parent=styles['Normal'], fontSize=10, leading=12, alignment=TA_LEFT, spaceBefore=0, spaceAfter=0))
    styles.add(ParagraphStyle(name='TranslatedText', parent=styles['Normal'], fontSize=10, leading=12, alignment=TA_LEFT, spaceBefore=0, spaceAfter=0))
    styles.add(ParagraphStyle(name='Speaker', parent=styles['Normal'], fontSize=10, leading=12, alignment=TA_CENTER, spaceBefore=4, spaceAfter=2, fontName='Helvetica-Bold'))
    styles.add(ParagraphStyle(name='Heading', parent=styles['h1'], fontSize=14, leading=16, alignment=TA_CENTER, spaceAfter=12, spaceBefore=12))
    styles.add(ParagraphStyle(name='Scenemarker', parent=styles['h2'], fontSize=12, leading=14, alignment=TA_CENTER, spaceAfter=10, spaceBefore=10)) # Corrected name
    styles.add(ParagraphStyle(name='StageDirectionCentered', parent=styles['Normal'], fontSize=9, leading=11, alignment=TA_CENTER, fontName='Helvetica-Oblique', spaceBefore=6, spaceAfter=6))
    styles.add(ParagraphStyle(name='ErrorText', parent=styles['TranslatedText'], textColor=colors.red))
    styles.add(ParagraphStyle(name='CopyrightStyle', parent=styles['Normal'], fontSize=8, leading=10, alignment=TA_LEFT, spaceBefore=6, spaceAfter=6))

    # --- Build Story ---
    story = []
    print("Adding front matter...")
    book_title = "Romeo and Juliet: A Contemporary Vernacular Adaptation"
    book_subtitle = "Side-by-Side Edition"
    adapter_name = "[Your Name Here]" # Replace
    copyright_holder = "[Your Name Here]" # Replace
    current_year = datetime.datetime.now().year
    front_matter_flowables = get_front_matter_story(styles, book_title, book_subtitle, adapter_name, copyright_holder, current_year)
    story.extend(front_matter_flowables)

    # Switch template and force page break
    story.append(NextPageTemplate('main_body'))
    story.append(PageBreak())
    global _main_content_start_page
    _main_content_start_page = None

    print("Processing play structure elements for main body...")
    item_count = 0

    for index, element in enumerate(play_structure):
        el_type = element.get('type')
        original_text = element.get('original', '')
        raw_translated_text = element.get('translated', '') or ""
        trans_style_to_use = styles['ErrorText'] if raw_translated_text.startswith('[Translation') else styles['TranslatedText']

        # --- Handle Different Element Types ---
        if el_type in ['heading', 'scenemarker', 'speaker']: # Corrected 'Scenemarker' name usage
            style_name = el_type.replace('_', '').capitalize()
            if style_name == 'Speaker' and index > 0 and play_structure[index-1].get('type') not in ['heading', 'scenemarker', 'speaker']:
                 story.append(Spacer(1, 0.05*inch))
            story.append(Paragraph(original_text, styles[style_name]))
            if style_name in ['Heading', 'Scenemarker']: story.append(Spacer(1, 0.1*inch))
            item_count += 1
        elif el_type == 'stage_direction':
             cleaned_original_text = original_text.replace('_', '')
             story.append(Spacer(1, 0.08*inch))
             story.append(Paragraph(cleaned_original_text, styles['StageDirectionCentered']))
             story.append(Spacer(1, 0.08*inch))
             item_count += 1
        elif el_type == 'dialogue':
            # --- Using Pre-Splitting into Multi-Row Table Logic ---
            table_data = []
            processed_dialogue = False

            if raw_translated_text == '[Translated as part of previous chunk]':
                p_orig = Paragraph(original_text.replace('\n', '<br/>'), styles['OriginalText'])
                p_trans = Spacer(0, 0)
                table_data = [[p_orig, p_trans]] # Single row
                processed_dialogue = True
            elif raw_translated_text.startswith('[Translation'):
                p_orig = Paragraph(original_text.replace('\n', '<br/>'), styles['OriginalText'])
                p_trans = Paragraph(raw_translated_text, styles['ErrorText'])
                table_data = [[p_orig, p_trans]] # Single row
                processed_dialogue = True
            else:
                # --- Actual Translation: Split into multiple rows based on character count ---
                MAX_CHARS_PER_SUBCHUNK = 1200 # Using a reasonable threshold

                orig_len = len(original_text)
                trans_len = len(raw_translated_text)
                should_split = (orig_len > MAX_CHARS_PER_SUBCHUNK or trans_len > MAX_CHARS_PER_SUBCHUNK)

                if not should_split:
                    # Short enough, treat as single row
                    p_orig = Paragraph(original_text.replace('\n', '<br/>'), styles['OriginalText'])
                    p_trans = Paragraph(raw_translated_text.replace('\n', '<br/>'), trans_style_to_use)
                    table_data = [[p_orig, p_trans]]
                else:
                    # Needs splitting
                    print(f"Info: Splitting dialogue chunk (approx {orig_len}/{trans_len} chars) starting element {index}...")
                    if orig_len > trans_len:
                        longer_text, shorter_text = original_text, raw_translated_text
                        longer_len, shorter_len = orig_len, trans_len
                        longer_style, shorter_style = styles['OriginalText'], styles['TranslatedText']
                        is_orig_longer = True
                    else:
                        longer_text, shorter_text = raw_translated_text, original_text
                        longer_len, shorter_len = trans_len, orig_len
                        longer_style, shorter_style = styles['TranslatedText'], styles['OriginalText']
                        is_orig_longer = False

                    num_splits = max(1, (longer_len + MAX_CHARS_PER_SUBCHUNK - 1) // MAX_CHARS_PER_SUBCHUNK)
                    start_longer_idx, start_shorter_idx = 0, 0

                    for i in range(num_splits):
                        # Calculate proportional endpoints
                        prop_end_longer = int(longer_len * (i + 1) / num_splits)
                        prop_end_shorter = int(shorter_len * (i + 1) / num_splits)

                        # Find simple break points (use proportional end or full length)
                        end_longer_idx = prop_end_longer if i < num_splits - 1 else longer_len
                        end_shorter_idx = prop_end_shorter if i < num_splits - 1 else shorter_len

                        # Extract sub-chunks, replace newlines with <br/> for Paragraph
                        longer_sub_chunk = longer_text[start_longer_idx:end_longer_idx].strip().replace('\n', '<br/>')
                        shorter_sub_chunk = shorter_text[start_shorter_idx:end_shorter_idx].strip().replace('\n', '<br/>')

                        p_longer = Paragraph(longer_sub_chunk, longer_style) if longer_sub_chunk else Spacer(0,0)
                        p_shorter = Paragraph(shorter_sub_chunk, shorter_style) if shorter_sub_chunk else Spacer(0,0)

                        # Add row in correct order
                        if is_orig_longer: table_data.append([p_longer, p_shorter])
                        else: table_data.append([p_shorter, p_longer])

                        start_longer_idx = end_longer_idx
                        start_shorter_idx = end_shorter_idx

                processed_dialogue = True


            # --- Create and append the Table ---
            if processed_dialogue and table_data:
                ts = TableStyle([
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.transparent), # Invisible grid
                    ('LEFTPADDING', (0,0), (-1,-1), 0), ('RIGHTPADDING', (0,0), (-1,-1), 0),
                    ('TOPPADDING', (0,0), (-1,-1), 0), ('BOTTOMPADDING', (0,0), (-1,-1), 1), # Minimal padding
                ])
                # Create the table, ALWAYS allowing splitting BETWEEN rows
                dialogue_table = Table(table_data,
                                     colWidths=[COLUMN_WIDTH, COLUMN_WIDTH],
                                     style=ts,
                                     splitByRow=1) # <<< ALLOW SPLITTING BETWEEN ROWS
                story.append(dialogue_table)
                story.append(Spacer(1, 0.05*inch)) # Spacer AFTER the speech/element
                item_count += 1
            elif not processed_dialogue:
                 print(f"Warning: Dialogue element {index} did not produce table data.")
                 item_count += 1

        # else: ignore 'unknown' type

    print(f"Added {item_count} elements to the PDF story.")

    # --- Build the PDF ---
    print("Building PDF document...")
    try:
        _main_content_start_page = None # Reset before build
        doc.build(story)
        print(f"PDF generated successfully: {output_filepath}")
    except Exception as e:
        print(f"Error building PDF: {e}")
        import traceback
        traceback.print_exc() # Print full traceback