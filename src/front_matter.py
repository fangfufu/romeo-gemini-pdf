from reportlab.platypus import Paragraph, Spacer, PageBreak
from reportlab.lib.units import inch
from reportlab.lib.styles import ParagraphStyle # For type hinting if needed

def get_front_matter_story(styles, title, subtitle, adapter_name, copyright_holder, current_year):
    """
    Generates the ReportLab Flowables for the Title and Copyright pages.

    Args:
        styles: The StyleSheet object containing defined paragraph styles.
        title (str): The main title of the book.
        subtitle (str): The subtitle (can be empty string).
        adapter_name (str): Your name or the entity credited for adaptation.
        copyright_holder (str): The name to use in the copyright notice.
        current_year (int): The year for the copyright notice.

    Returns:
        list: A list of Flowable objects representing the front matter.
    """
    story = []

    # --- Title Page ---
    # Typically page 3 (recto), assuming blank or half-title before it.
    # We might need to manually ensure it lands on a recto page later if needed,
    # but for now, let's just add the content. Add Spacers for positioning.
    story.append(Spacer(1, 3*inch)) # Space from top
    story.append(Paragraph(title, styles['h1'])) # Use heading style for title
    story.append(Spacer(1, 0.2*inch))
    if subtitle:
        story.append(Paragraph(subtitle, styles['h2'])) # Use heading 2 for subtitle
        story.append(Spacer(1, 0.5*inch))
    else:
        story.append(Spacer(1, 0.5*inch))

    story.append(Paragraph("by William Shakespeare", styles['Normal']))
    story.append(Spacer(1, 0.2*inch))
    story.append(Paragraph(f"Adapted and Translated by {adapter_name}", styles['Normal']))
    story.append(PageBreak()) # End of Title Page, move to Copyright Page (verso)

    # --- Copyright Page ---
    # Typically page 4 (verso)
    story.append(Spacer(1, 1*inch)) # Space from top for copyright info

    # Construct copyright text carefully, using <br/> for line breaks within a single Paragraph
    copyright_text = f"""
    Copyright © {current_year} {copyright_holder}<br/>
    All rights reserved.<br/>
    <br/>
    Based on the public domain work <i>Romeo and Juliet</i> by William Shakespeare.<br/>
    <br/>
    <b>Note on Translation:</b><br/>
    This work is an experimental adaptation of Shakespeare's <i>Romeo and Juliet</i>,
    reimagining the dialogue in a contemporary British urban vernacular for creative
    exploration. The translation was generated with assistance from Google AI models
    (Gemini/Gemma) and subsequently reviewed and edited. It aims to explore language
    and character through a modern lens and is not intended as a literal or scholarly
    translation. Reader discretion regarding language and style is advised.
    """
    story.append(Paragraph(copyright_text, styles['CopyrightStyle']))
    story.append(PageBreak()) # End of Copyright Page

    return story
