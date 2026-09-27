"""
Standalone HTML table viewer rendering module.
Assembles HTML, CSS, JavaScript, and embedded datasets into a single self-contained file.
"""

import json
import os
from typing import Dict, Any, List, Optional

from .config import (
    PAIRS,
    PAIR_METADATA,
    EVENT_FAMILIES,
    OUTPUT_HTML_PATH,
    CODEX_DISPLAY_APPROVED
)
from .cpi_ledger import (
    load_cpi_ledger_data,
    prepare_cpi_presentation_data,
    render_cpi_section
)

TEMPLATE_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")


def build_html(
    episodes_data: List[Dict[str, Any]],
    codex_display_approved: bool = CODEX_DISPLAY_APPROVED,
    ledger_data: Optional[Dict[str, Any]] = None,
    output_path: str = OUTPUT_HTML_PATH
) -> str:
    """Generates the clean Light Mode standalone HTML table viewer."""
    print("Generating HTML table viewer...")

    # Load dynamic CPI simulation ledger data and prepare presentation strings
    cpi_ledger_data = load_cpi_ledger_data(ledger_data)
    cpi_pres = prepare_cpi_presentation_data(cpi_ledger_data)
    cpi_section_html = render_cpi_section(cpi_pres, codex_display_approved)

    # Compact JSON data
    data_json = json.dumps({
        "pairs": PAIRS,
        "pair_meta": PAIR_METADATA,
        "families": EVENT_FAMILIES,
        "episodes": episodes_data
    })

    # Read templates
    with open(os.path.join(TEMPLATE_DIR, "styles.css"), "r", encoding="utf-8") as f:
        css_content = f.read()

    with open(os.path.join(TEMPLATE_DIR, "app.js"), "r", encoding="utf-8") as f:
        js_template = f.read()

    with open(os.path.join(TEMPLATE_DIR, "template.html"), "r", encoding="utf-8") as f:
        html_template = f.read()

    # Embed data into JS
    js_content = js_template.replace("__DATA_JSON__", data_json)

    # Assemble HTML
    html_content = html_template.replace("__CSS__", css_content)
    html_content = html_content.replace("__CPI_SECTION__", cpi_section_html)
    html_content = html_content.replace("__JS__", js_content)

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html_content)

    print(f"Generated standalone HTML table viewer successfully at: {output_path}")
    print(f"HTML File Size: {os.path.getsize(output_path) / 1024:.1f} KB")
    return html_content
