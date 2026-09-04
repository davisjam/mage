"""SVG parsing helpers, extracted from the MAGE book build.

Exactly the five functions ``lint_figure_font_band`` needs, lifted verbatim from
``tests/svg_fit.py`` in the MAGE repository. The full module is 1279 lines and
depends on the book's test harness (``tests.common`` -> ``catalog.ROOT``); these
five are pure SVG parsing with no such coupling, so they carry cleanly.

Source: repos/model-based-agentic-software-engineering/tests/svg_fit.py
"""

from __future__ import annotations

import re
import xml.etree.ElementTree as ET


def _local(tag: str) -> str:
    """Strip the `{namespace}` prefix ElementTree prepends, so `{...}text` -> `text`."""
    return tag.rsplit("}", 1)[-1]

def _num(v: str | None) -> float | None:
    if v is None:
        return None
    m = re.match(r"(-?[0-9.]+)", v)
    return float(m.group(1)) if m else None

def _parse_style_font_sizes(root: ET.Element) -> dict[str, tuple[float, bool]]:
    """Map each CSS class in a `<style>` block to (font_size_px, is_bold).

    Figures declare font sizing two ways: a `font-size` attribute on the `<text>`, or a CSS class whose
    rule lives in an SVG `<style>` block (e.g. `.btitle { font-size:32px; font-weight:700; }`). Parse the
    class rules so a class-styled label resolves its size the same as an attribute-styled one.
    """
    classes: dict[str, tuple[float, bool]] = {}
    for el in root.iter():
        if _local(el.tag) != "style" or not el.text:
            continue
        # Each rule: `.name { ...decls... }`. Pull font-size + font-weight out of the decl block.
        for cls, body in re.findall(r"\.([A-Za-z0-9_-]+)\s*\{([^}]*)\}", el.text):
            m = re.search(r"font-size\s*:\s*([0-9.]+)", body)
            if not m:
                continue
            size = float(m.group(1))
            bold = bool(re.search(r"font-weight\s*:\s*(bold|[6-9]00)", body))
            classes[cls] = (size, bold)
    return classes

def _text_content(el: ET.Element) -> str:
    """Flatten a `<text>` (and any `<tspan>` children) to its visible string."""
    return "".join(el.itertext()).strip()

def _viewbox_width(root: ET.Element) -> float | None:
    vb = root.get("viewBox")
    if vb:
        parts = re.split(r"[\s,]+", vb.strip())
        if len(parts) == 4:
            return float(parts[2])
    return _num(root.get("width"))
