"""Execute the locked graph renderer: themes change presentation, not design data."""

import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest

TEMPLATE = Path(__file__).resolve().parents[1] / "skills/S1_design_system/references/dependency_graph_template.html"
NODE = shutil.which("node")


@pytest.fixture(scope="module")
def rendered():
    if NODE is None:
        pytest.skip("Node is needed only to exercise the HTML template's renderer")
    html = TEMPLATE.read_text(encoding="utf-8")
    data = {
        "manifest": {"id": "fixture", "name": "Theme example", "cycle": "01_demo",
                     "gt": {"strs": ".codeanvil/GT/StRS.md", "syrs": ".codeanvil/GT/SyRS.md"}},
        "subsystems": [
            {"id": "SUB-A", "label": "Acquisition", "modules": [
                {"id": "source", "label": "Source", "color": "#72c7ca"},
                {"id": "dsp", "label": "DSP", "color": "#83c99b"}]},
            {"id": "SUB-B", "label": "Display", "modules": [
                {"id": "source", "label": "View", "color": "#a5b4c1"}]},
            {"id": "SUB-C", "label": "Storage", "modules": []},
        ],
        "hardware": [{"id": "HWC-001", "label": "Device", "to": ["SUB-A/source", "SUB-B/source"]}],
        "subsystemContracts": [{"id": "samples.v1", "from": ["SUB-A"], "to": ["SUB-B", "SUB-C"]}],
    }
    replacement = "const theme = 'dark';\n" + "\n".join(
        f"const {key} = {json.dumps(value)};" for key, value in data.items()
    )
    html = re.sub(r"// === DATA.*?\n// ={5,}\n", lambda _: replacement + "\n", html, flags=re.DOTALL)
    source = re.findall(r"<script>(.*?)</script>", html, flags=re.DOTALL)[0]
    harness = r"""
const fs = require('node:fs');
const vm = require('node:vm');
const source = JSON.parse(fs.readFileSync(0, 'utf8'));
const results = {};
for (const theme of ['dark', 'light']) {
  const elements = Object.fromEntries(['meta', 'legend', 'graph'].map(id => [id, {}]));
  const properties = {};
  const root = {dataset: {}, style: {setProperty(key, value) { properties[key] = value; }}};
  let network;
  const context = {
    document: {documentElement: root, getElementById(id) { return elements[id]; }},
    vis: {Network: function(element, data, options) { network = {data, options}; }},
  };
  vm.runInNewContext(source.replace("const theme = 'dark';", `const theme = '${theme}';`), context);
  results[theme] = {network, properties, theme: root.dataset.theme, meta: elements.meta.textContent};
}
process.stdout.write(JSON.stringify(results));
"""
    result = subprocess.run([NODE, "-e", harness], input=json.dumps(source), text=True,
                            capture_output=True, check=True)
    return json.loads(result.stdout)


def test_both_themes_keep_the_same_spiders_hardware_and_multi_consumer_contract(rendered):
    dark, light = (rendered[theme]["network"] for theme in ("dark", "light"))
    assert [node["id"] for node in dark["data"]["nodes"]] == [
        "SUB-A", "SUB-B", "SUB-C", "SUB-A/source", "SUB-A/dsp", "SUB-B/source", "HWC-001", "c:samples.v1",
    ]
    topology = lambda graph: (
        [(node["id"], node["label"], node["shape"]) for node in graph["data"]["nodes"]],
        [(edge["from"], edge["to"], edge.get("arrows"), edge.get("dashes")) for edge in graph["data"]["edges"]],
    )
    assert topology(dark) == topology(light)
    assert len(dark["data"]["edges"]) == 8
    assert [(edge["from"], edge["to"]) for edge in dark["data"]["edges"][-3:]] == [
        ("SUB-A", "c:samples.v1"), ("c:samples.v1", "SUB-B"), ("c:samples.v1", "SUB-C"),
    ]
    assert dark["options"]["layout"] == light["options"]["layout"] == {"randomSeed": 1}
    assert rendered["dark"]["meta"] == rendered["light"]["meta"]


def contrast(first, second):
    def luminance(color):
        channels = [int(color[index:index + 2], 16) / 255 for index in (1, 3, 5)]
        linear = [value / 12.92 if value <= .04045 else ((value + .055) / 1.055) ** 2.4 for value in channels]
        return sum(value * weight for value, weight in zip(linear, (.2126, .7152, .0722)))
    high, low = sorted((luminance(first), luminance(second)), reverse=True)
    return (high + .05) / (low + .05)


def test_both_themes_use_forge_surfaces_with_readable_nodes_and_distinct_layers(rendered):
    for theme, background, surface in (("dark", "#111417", "#171b1f"), ("light", "#e9eceb", "#f7f8f7")):
        result = rendered[theme]
        assert result["theme"] == theme
        assert result["properties"]["--bg"] == background
        assert result["properties"]["--surface"] == surface
        nodes = result["network"]["data"]["nodes"]
        for node in nodes:
            assert node["color"]["background"] == surface
            assert contrast(node["font"]["color"], surface) >= 4.5
            assert contrast(node["color"]["border"], background) >= 3
        module_borders = [node["color"]["border"] for node in nodes if node["id"].startswith("SUB-") and "/" in node["id"]]
        assert len(set(module_borders)) == 3
    assert rendered["dark"]["network"]["data"]["nodes"][3]["color"] != rendered["light"]["network"]["data"]["nodes"][3]["color"]
