"""Losslessly normalize brand SVGs into a common 24x24 canvas + faded variants.

Vector-only: wraps each source's drawing in <g transform="translate scale"> so
nothing is rasterized and no resolution is lost. Originals are left untouched;
output goes to <resources>/normalized/.
"""
import copy
import re
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

NS = "http://www.w3.org/2000/svg"
ET.register_namespace("", NS)

TARGET = 24.0      # common square canvas (vector units; resolution-independent)
PAD = 1.5          # uniform optical padding inside the canvas
FADE = "0.25"      # opacity for the disabled/faded variant (stronger = more distinct)

TITLES = {
    "claude": "Claude", "anthropic": "Anthropic", "openai-codex": "Codex",
    "opencode-light": "OpenCode", "opencode-dark": "OpenCode",
    "vscode": "Visual Studio Code", "jetbrains": "JetBrains", "pi": "Pi",
}


def parse_len(v):
    if not v:
        return None
    m = re.match(r"\s*([0-9.]+)", v)
    return float(m.group(1)) if m else None


def source_box(root):
    vb = root.get("viewBox")
    if vb:
        n = [float(x) for x in re.split(r"[ ,]+", vb.strip())]
        if len(n) == 4:
            return n
    w, h = parse_len(root.get("width")), parse_len(root.get("height"))
    if w and h:
        return [0.0, 0.0, w, h]
    return None


def normalize(path, title):
    root = ET.parse(path).getroot()
    box = source_box(root)
    if not box:
        return None, "no viewBox and no width/height"
    minx, miny, w, h = box
    content = TARGET - 2 * PAD
    s = content / max(w, h)
    tx = PAD + (content - w * s) / 2 - minx * s
    ty = PAD + (content - h * s) / 2 - miny * s

    svg = ET.Element(f"{{{NS}}}svg", {
        "viewBox": f"0 0 {int(TARGET)} {int(TARGET)}",
        "width": str(int(TARGET)), "height": str(int(TARGET)), "role": "img",
    })
    ET.SubElement(svg, f"{{{NS}}}title").text = title
    g = ET.SubElement(svg, f"{{{NS}}}g",
                      {"transform": f"translate({tx:.4f} {ty:.4f}) scale({s:.6f})"})
    for child in list(root):
        if child.tag.split("}")[-1] == "title":
            continue
        g.append(child)
    return svg, f"src {w:g}x{h:g} -> scale {s:.4f}"


def write(svg, path):
    ET.ElementTree(svg).write(str(path), encoding="unicode", xml_declaration=False)
    path.write_text(path.read_text() + "\n")


def main():
    src = Path(sys.argv[1])
    out = src / "normalized"
    out.mkdir(exist_ok=True)
    for stem, title in TITLES.items():
        p = src / f"{stem}.svg"
        if not p.exists():
            print(f"SKIP {stem}: file missing")
            continue
        try:
            svg, info = normalize(p, title)
        except Exception as e:  # noqa: BLE001
            print(f"FAIL {stem}: {e}")
            continue
        if svg is None:
            print(f"FAIL {stem}: {info}")
            continue
        write(svg, out / f"{stem}.svg")
        faded = copy.deepcopy(svg)
        faded.find(f"{{{NS}}}g").set("opacity", FADE)
        write(faded, out / f"{stem}-off.svg")
        print(f"OK   {stem}.svg + {stem}-off.svg  ({info})")


if __name__ == "__main__":
    main()
