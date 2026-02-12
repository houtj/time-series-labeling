#!/usr/bin/env -S uv run --script
# /// script
# requires-python = ">=3.9"
# dependencies = [
#     "markdown>=3.5",
#     "weasyprint>=60.0",
# ]
# ///
"""
Script to generate PDF from USER_MANUAL.md using uv
Automatically installs dependencies when run with: uv run generate_pdf.py

No manual installation needed!
"""

import os
import sys
from pathlib import Path

import markdown
from weasyprint import HTML, CSS


def generate_pdf(input_file: Path, output_file: Path):
    """Generate PDF from markdown file."""

    print("=" * 50)
    print("Hill Sequence Manual PDF Generator")
    print("=" * 50)
    print()

    # Check if input file exists
    if not input_file.exists():
        print(f"ERROR: Input file not found: {input_file}")
        sys.exit(1)

    print(f"Input:  {input_file}")
    print(f"Output: {output_file}")
    print()
    print("Reading markdown file...")

    # Read markdown content
    with open(input_file, 'r', encoding='utf-8') as f:
        md_content = f.read()

    print("Converting markdown to HTML...")

    # Convert markdown to HTML with extensions
    html_content = markdown.markdown(
        md_content,
        extensions=[
            'extra',           # Extra features like tables, footnotes
            'codehilite',      # Code syntax highlighting
            'toc',             # Table of contents
            'sane_lists',      # Better list handling
            'smarty',          # Smart quotes
        ]
    )

    # Wrap HTML with proper structure and CSS
    full_html = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <meta charset="UTF-8">
        <title>Hill Sequence Labeling Tool - User Manual</title>
        <style>
            @page {{
                size: A4;
                margin: 2.5cm;
                @bottom-right {{
                    content: "Page " counter(page) " of " counter(pages);
                    font-size: 9pt;
                    color: #666;
                }}
            }}
            body {{
                font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Helvetica, Arial, sans-serif;
                font-size: 11pt;
                line-height: 1.6;
                color: #333;
                max-width: 100%;
            }}
            h1 {{
                font-size: 24pt;
                color: #2c3e50;
                border-bottom: 3px solid #3498db;
                padding-bottom: 10px;
                margin-top: 30px;
                page-break-after: avoid;
            }}
            h2 {{
                font-size: 18pt;
                color: #34495e;
                border-bottom: 2px solid #95a5a6;
                padding-bottom: 8px;
                margin-top: 25px;
                page-break-after: avoid;
            }}
            h3 {{
                font-size: 14pt;
                color: #555;
                margin-top: 20px;
                page-break-after: avoid;
            }}
            h4 {{
                font-size: 12pt;
                color: #666;
                margin-top: 15px;
            }}
            code {{
                background-color: #f4f4f4;
                padding: 2px 6px;
                border-radius: 3px;
                font-family: "Courier New", monospace;
                font-size: 10pt;
                color: #d63031;
            }}
            pre {{
                background-color: #f8f8f8;
                border: 1px solid #ddd;
                border-radius: 5px;
                padding: 12px;
                overflow-x: auto;
                page-break-inside: avoid;
                margin: 15px 0;
            }}
            pre code {{
                background-color: transparent;
                padding: 0;
                color: inherit;
            }}
            ul, ol {{
                margin-left: 20px;
                margin-bottom: 15px;
            }}
            li {{
                margin-bottom: 5px;
            }}
            strong {{
                color: #2c3e50;
                font-weight: 600;
            }}
            a {{
                color: #3498db;
                text-decoration: none;
            }}
            img {{
                max-width: 100%;
                height: auto;
                display: block;
                margin: 15px auto;
                border: 1px solid #ddd;
                border-radius: 5px;
                page-break-inside: avoid;
            }}
            blockquote {{
                border-left: 4px solid #3498db;
                margin-left: 0;
                padding-left: 20px;
                color: #555;
                font-style: italic;
            }}
            table {{
                border-collapse: collapse;
                width: 100%;
                margin: 15px 0;
                page-break-inside: avoid;
                font-size: 10pt;
            }}
            th, td {{
                border: 1px solid #ddd;
                padding: 8px;
                text-align: left;
            }}
            th {{
                background-color: #3498db;
                color: white;
                font-weight: bold;
            }}
            tr:nth-child(even) {{
                background-color: #f8f9fa;
            }}
            hr {{
                border: none;
                border-top: 1px solid #ddd;
                margin: 30px 0;
            }}
        </style>
    </head>
    <body>
        {html_content}
    </body>
    </html>
    """

    print("Generating PDF...")

    # Convert HTML to PDF
    try:
        HTML(
            string=full_html,
            base_url=str(input_file.parent)
        ).write_pdf(
            output_file,
            stylesheets=[CSS(string='@page { size: A4; margin: 2.5cm; }')]
        )

        print()
        print("✓ PDF generated successfully!")
        print(f"  Location: {output_file}")

        # Get file size
        size_bytes = output_file.stat().st_size
        size_mb = size_bytes / (1024 * 1024)
        if size_mb >= 1:
            print(f"  Size: {size_mb:.2f} MB")
        else:
            size_kb = size_bytes / 1024
            print(f"  Size: {size_kb:.2f} KB")

    except Exception as e:
        print()
        print(f"✗ PDF generation failed: {e}")
        print()
        print("Note: WeasyPrint requires system dependencies:")
        print("  Ubuntu/Debian: sudo apt-get install python3-cffi python3-brotli libpango-1.0-0 libpangoft2-1.0-0")
        print("  macOS: brew install cairo pango gdk-pixbuf libffi")
        sys.exit(1)


if __name__ == "__main__":
    script_dir = Path(__file__).parent
    input_file = script_dir / "USER_MANUAL.md"
    output_file = script_dir / "USER_MANUAL.pdf"

    generate_pdf(input_file, output_file)
