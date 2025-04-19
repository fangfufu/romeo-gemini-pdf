import html

def get_front_matter_html(title, subtitle, adapter_name, copyright_holder, current_year):
    """
    Generates the HTML string for the Title and Copyright pages.

    Args:
        title (str): The main title of the book.
        subtitle (str): The subtitle (can be empty string).
        adapter_name (str): Your name or the entity credited for adaptation.
        copyright_holder (str): The name to use in the copyright notice.
        current_year (int): The year for the copyright notice.

    Returns:
        str: An HTML string representing the front matter pages.
    """
    # Escape potentially problematic characters in user-provided strings
    safe_title = html.escape(title)
    safe_subtitle = html.escape(subtitle) if subtitle else ""
    safe_adapter = html.escape(adapter_name)
    safe_holder = html.escape(copyright_holder)

    # --- Title Page HTML ---
    # Use divs with classes for styling and page breaks
    title_page_html = f"""
<div class="title-page">
    <div class="title-content">
        <h1>{safe_title}</h1>
        {'<h2>' + safe_subtitle + '</h2>' if safe_subtitle else ''}
        <p class="author">by William Shakespeare</p>
        <p class="adapter">Adapted and Translated by {safe_adapter}</p>
    </div>
</div>
""" # CSS will handle page break after this div

    # --- Copyright Page HTML ---
    # Using <p> tags and relying on CSS for small font size and spacing
    copyright_page_html = f"""
<div class="copyright-page">
    <p>Copyright &copy; {current_year} {safe_holder}<br/>
    All rights reserved.</p>
    <br/>
    <p>Based on the public domain work <i>Romeo and Juliet</i> by William Shakespeare.</p>
    <br/>
    <p>ISBN: [KDP Will Provide - Add Later if Needed]</p>
    <br/>
    <p><b>Note on Translation:</b><br/>
    This work is an experimental adaptation of Shakespeare's <i>Romeo and Juliet</i>,
    reimagining the dialogue in a contemporary British urban vernacular for creative
    exploration. The translation was generated with assistance from Google AI models
    (Gemini/Gemma) and subsequently reviewed and edited. It aims to explore language
    and character through a modern lens and is not intended as a literal or scholarly
    translation. Reader discretion regarding language and style is advised.</p>
</div>
""" # CSS will handle page break after this div (or let main content start)

    # --- Optional Blank Page After Copyright (if needed for Prologue on recto) ---
    # Depending on CSS and flow, might not be necessary. Add if required.
    # blank_page_html = '<div class="blank-page"></div>'

    # Combine the parts
    # return title_page_html + copyright_page_html + blank_page_html
    return title_page_html + copyright_page_html