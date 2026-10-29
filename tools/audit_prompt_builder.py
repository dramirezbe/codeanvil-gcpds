"""
LLM Validation Prompt Builder
Run:  streamlit run audit_prompt_builder.py
Starting content lives in prompt_inputs.template.json, next to this script.
An agent (or a person) can fill a copy of it into inputs/; load it from the
sidebar, adjust anything in the interface, then save the prompt. See README.md.
"""

import json
import re
from pathlib import Path

import streamlit as st

try:
    from codeanvil.config.time import format_timestamp_machine
except ImportError:  # tool may run in a Streamlit-only env without codeanvil installed
    from datetime import datetime

    def format_timestamp_machine():
        return datetime.now().astimezone().strftime("%Y-%m-%d_%H-%M-%S")

TOOLS_DIR = Path(__file__).resolve().parent
PROMPTS_DIR = TOOLS_DIR / "prompts"
INPUTS_DIR = TOOLS_DIR / "inputs"
TEMPLATE_PATH = TOOLS_DIR / "prompt_inputs.template.json"

st.set_page_config(page_title="LLM Validation Prompt Builder", layout="wide")

# =============================================================================
# EDITABLE DEFAULTS
# =============================================================================

STAGES = [
    ("Decomposition",
     "Split the idea into claims, assumptions, interfaces and dependencies. Number each item so later stages can reference it."),
    ("Novelty and prior-art check",
     "Compare the idea against the known prior work. List what is already solved, what is not, and what cannot be verified without a search."),
    ("Gap matrix",
     "Build a problem x method table. Mark empty cells as candidate gaps and state, for each, why it may be empty or whether it is worth filling."),
    ("Matrix scoring",
     "Score every dimension in the scoring matrix, with evidence and visible arithmetic."),
    ("Failure-mode analysis",
     "List the five most likely failure modes. For each: likelihood, impact, detection method, and mitigation."),
    ("Recommendation",
     "Give a verdict and the smallest next experiment that would most change the score."),
]

SCALES = [3, 4, 5, 10]
DISAGREE_OPTIONS = [
    "report both values and flag for human arbitration",
    "use the lower score and note the gap",
    "use the average and report the spread",
]
FORMATS = ["Markdown", "JSON"]
CONTEXT_KEYS = ["title", "domain", "problem", "idea", "constraints", "assumptions", "prior"]
DIM_KEYS = ["name", "weight", "definition", "low", "mid", "high"]

# =============================================================================
# INPUTS FILE (template / agent-filled JSON)
# =============================================================================

IS_STR = (lambda v: isinstance(v, str), "a string")
IS_BOOL = (lambda v: isinstance(v, bool), "true or false")
IS_WEIGHT = (lambda v: isinstance(v, (int, float)) and not isinstance(v, bool) and 0 <= v <= 10,
             "a number from 0 to 10")
IS_STR_LIST = (lambda v: isinstance(v, list) and all(isinstance(x, str) for x in v), "a list of strings")

def one_of(options):
    return (lambda v: not isinstance(v, bool) and v in options,
            "one of: " + ", ".join(json.dumps(o) for o in options))

def load_template():
    return json.loads(TEMPLATE_PATH.read_text(encoding="utf-8"))

def merge_fields(errors, where, src, dst, spec):
    """Copy src fields into dst, checking each one against spec {field: (check, expectation)}."""
    if not isinstance(src, dict):
        errors.append(f"{where} must be an object.")
        return
    for k, v in src.items():
        if k not in spec:
            errors.append(f"Unknown field: {where}.{k}.")
        elif spec[k][0](v):
            dst[k] = v
        else:
            errors.append(f"{where}.{k} must be {spec[k][1]}.")

def parse_inputs(data):
    """Validate an inputs object and merge it over the template. Returns (inputs, errors)."""
    if not isinstance(data, dict):
        return None, ["The file must contain a JSON object."]
    out, errors = load_template(), []
    sections = {
        "context": {k: IS_STR for k in CONTEXT_KEYS},
        "stages": {label: IS_BOOL for label, _ in STAGES},
        "audit": {"enabled": IS_BOOL, "checks": IS_STR_LIST, "documents": IS_STR},
        "rules": {"two_pass": IS_BOOL, "evidence": IS_BOOL, "disagree": one_of(DISAGREE_OPTIONS)},
        "output": {"format": one_of(FORMATS), "language": IS_STR},
    }
    for key, value in data.items():
        if key.startswith("$"):
            continue
        if key in sections:
            merge_fields(errors, key, value, out[key], sections[key])
        elif key == "scale":
            if one_of(SCALES)[0](value):
                out["scale"] = int(value)
            else:
                errors.append(f"scale must be {one_of(SCALES)[1]}.")
        elif key == "dimensions":
            if not isinstance(value, list):
                errors.append("dimensions must be a list.")
                continue
            dims = []
            for n, d in enumerate(value):
                dim = dict(name="", weight=1.0, definition="", low="", mid="", high="")
                merge_fields(errors, f"dimensions[{n}]", d, dim,
                             {k: IS_WEIGHT if k == "weight" else IS_STR for k in DIM_KEYS})
                dims.append(dim)
            out["dimensions"] = dims
        else:
            errors.append(f"Unknown field: {key}.")
    return (None, errors) if errors else (out, [])

def to_inputs(cfg):
    """Convert the interface state into the inputs JSON format (the template's shape)."""
    return {
        "context": {k: cfg[k] for k in CONTEXT_KEYS},
        "stages": dict(cfg["stages"]),
        "scale": cfg["scale"],
        "dimensions": [{k: d[k] for k in DIM_KEYS} for d in cfg["dims"]],
        "audit": {"enabled": cfg["audit_on"], "checks": [c["text"] for c in cfg["checks"]],
                  "documents": cfg["docs"]},
        "rules": {"two_pass": cfg["two_pass"], "evidence": cfg["evidence"], "disagree": cfg["disagree"]},
        "output": {"format": cfg["fmt"], "language": cfg["lang"]},
    }

# =============================================================================
# STATE HELPERS
# =============================================================================

def next_id():
    st.session_state.next_id += 1
    return st.session_state.next_id

def make_dim(name="New dimension", weight=1.0, definition="", low="", mid="", high=""):
    return dict(id=next_id(), name=name, weight=weight, definition=definition,
                low=low, mid=mid, high=high)

def make_check(text=""):
    return dict(id=next_id(), text=text)

def apply_inputs(inp):
    """Load a parsed inputs object into the widgets' session state."""
    ss = st.session_state
    for k in CONTEXT_KEYS:
        ss[k] = inp["context"][k]
    for i, (label, _) in enumerate(STAGES):
        ss[f"stage_{i}"] = inp["stages"].get(label, True)
    ss.scale = inp["scale"]
    ss.dims = [make_dim(**d) for d in inp["dimensions"]]
    ss.audit_on = inp["audit"]["enabled"]
    ss.checks = [make_check(t) for t in inp["audit"]["checks"]]
    ss.docs = inp["audit"]["documents"]
    ss.two_pass = inp["rules"]["two_pass"]
    ss.evidence = inp["rules"]["evidence"]
    ss.disagree = inp["rules"]["disagree"]
    ss.fmt = inp["output"]["format"]
    ss.lang = inp["output"]["language"]

def load_inputs(raw, source):
    """Parse raw JSON bytes and apply them; the outcome is shown once in the sidebar."""
    try:
        inp, errors = parse_inputs(json.loads(raw))
    except (UnicodeDecodeError, json.JSONDecodeError) as e:
        inp, errors = None, [f"Not valid JSON: {e}"]
    if errors:
        st.session_state.load_msg = ("error", f"Not loaded {source}:\n" + "\n".join(f"- {e}" for e in errors))
    else:
        apply_inputs(inp)
        st.session_state.load_msg = ("success", f"Loaded {source}.")

def on_pick():
    name = st.session_state.pick
    load_inputs((INPUTS_DIR / name).read_bytes(), f"inputs/{name}")

def on_upload():
    f = st.session_state.upload
    if f is not None:
        load_inputs(f.getvalue(), f.name)

if "initialized" not in st.session_state:
    st.session_state.initialized = True
    st.session_state.next_id = 100
    apply_inputs(load_template())

JSON_SCHEMA = """{
  "scores": [{"dimension": "", "score": 0, "weight": 0, "evidence": "", "status": "EVIDENCED or ASSUMED"}],
  "weighted_percent": 0,
  "stages": {"<stage name>": "summary"},
  "findings": [{"id": "", "location": "", "check": 0, "severity": "CRITICAL|MAJOR|MINOR",
                "spans": [], "explanation": "", "fix": ""}],
  "coverage_note": "",
  "verdict": "PROCEED | REVISE | STOP",
  "top_risks": [],
  "human_questions": []
}"""

# =============================================================================
# PROMPT BUILDER
# =============================================================================

def build_prompt(cfg):
    smax = cfg["scale"]
    out = []
    a = out.append

    a("# ROLE")
    a(f"You are an independent senior reviewer in {cfg['domain'] or 'engineering'}. "
      "Evaluate rigorously. Separate evidence from opinion, mark every assumption, "
      "and never invent data. If something is unknown, say so.")
    a("")

    a("# CONTEXT")
    a(f"**Title:** {cfg['title'] or 'Untitled'}")
    for label, key in [
        ("Problem statement", "problem"),
        ("Idea description", "idea"),
        ("Constraints", "constraints"),
        ("Stated assumptions", "assumptions"),
        ("Known prior work and attempts", "prior"),
    ]:
        a(f"\n## {label}\n{cfg[key].strip() or 'Not provided.'}")
    a("")

    a("# TASK")
    active = [(l, d) for l, d in STAGES if cfg["stages"].get(l)]
    if active:
        a("Run the stages below in order. Do not skip one. If a stage lacks information, "
          "write INSUFFICIENT DATA, list exactly what is missing, and continue.")
    else:
        a("No staged analysis is requested. Go directly to the scoring matrix.")
    for n, (label, desc) in enumerate(active, 1):
        a(f"{n}. **{label}.** {desc}")
    a("")

    a("# SCORING MATRIX")
    a(f"Score each dimension from 0 to {smax}, using its anchors. If a case falls between "
      "anchors, choose the lower score and justify it.")
    for d in [d for d in cfg["dims"] if d["name"].strip()]:
        a(f"- **{d['name']}** (weight {d['weight']:g}). {d['definition'].strip()}")
        a(f"  - Lowest: {d['low'].strip() or 'n/a'}")
        a(f"  - Middle: {d['mid'].strip() or 'n/a'}")
        a(f"  - Highest ({smax}): {d['high'].strip() or 'n/a'}")
    a(f"\nWeighted score = sum(score x weight) / ({smax} x sum of weights), as a percentage. "
      "Show the arithmetic and recheck it before finalizing.")
    a("")

    a("## Scoring rules")
    if cfg["evidence"]:
        a("- Every score needs evidence: a quote or reference to the input, or the label ASSUMED.")
    if cfg["two_pass"]:
        a("- Run two passes. Pass A: score all dimensions. Pass B: re-score from the input alone, "
          "as if Pass A did not exist. Compare the two.")
    if cfg["two_pass"]:
        a(f"- If the passes differ by 2 or more points, or any score is ASSUMED: {cfg['disagree']}.")
    elif cfg["evidence"]:
        a("- If any score is ASSUMED, flag it for human review.")
    a("- Never hide disagreement.")
    a("")

    if cfg["audit_on"]:
        checks = [c["text"].strip() for c in cfg["checks"] if c["text"].strip()]
        if checks:
            a("# DOCUMENT AUDIT")
            a("Audit the documents in the DOCUMENTS section against these checks:")
            for n, c in enumerate(checks, 1):
                a(f"{n}. {c}")
            a("For every finding report: ID; location (section, paragraph or line); check number; "
              "severity (CRITICAL / MAJOR / MINOR); the conflicting spans, kept short; how they "
              "conflict; and the smallest edit that resolves it. Do not rewrite the document.")
            a("Finish with a coverage note: which checks found nothing, and which could not be "
              "tested from the text provided.")
            a("")

    a("# OUTPUT FORMAT")
    if cfg["fmt"] == "JSON":
        a("Return a single JSON object matching this schema. Put stage details inside \"stages\".")
        a("```json")
        a(JSON_SCHEMA)
        a("```")
    else:
        a("Use Markdown: one header per stage, tables for scores, bullet lists for findings.")
    a(f"Respond in {cfg['lang']}.")
    a("")

    a("# FINAL SUMMARY")
    a("End with: (1) verdict PROCEED, REVISE or STOP, with one paragraph of reasoning; "
      "(2) the top three risks; (3) the top three unknowns a human must resolve; "
      "(4) the questions whose answers would change the score most.")

    if cfg["audit_on"] and cfg["docs"].strip():
        a("")
        a("# DOCUMENTS")
        a("<documents>")
        a(cfg["docs"].strip())
        a("</documents>")

    return "\n".join(out)

def save_prompt(prompt, title):
    """Write the prompt to tools/prompts/<title-slug>_<timestamp>.txt and return the path."""
    slug = re.sub(r"[^a-z0-9]+", "_", (title or "").lower()).strip("_") or "prompt"
    PROMPTS_DIR.mkdir(parents=True, exist_ok=True)
    path = PROMPTS_DIR / f"{slug}_{format_timestamp_machine()}.txt"
    path.write_text(prompt + "\n", encoding="utf-8")
    return path

# =============================================================================
# UI
# =============================================================================

st.title("LLM Validation Prompt Builder")
st.caption("Fill each area. The (?) icons explain every field. Use + to add items and "
           "Remove to delete them. The prompt at the bottom updates as you type.")

with st.sidebar:
    st.header("Inputs file")
    st.caption("Load a JSON inputs file, then edit any field on the page. "
               "Its format is prompt_inputs.template.json; an agent can fill a copy into tools/inputs/.")
    files = sorted(p.name for p in INPUTS_DIR.glob("*.json")) if INPUTS_DIR.is_dir() else []
    if files:
        st.selectbox("From tools/inputs/", files, key="pick")
        st.button("Load selected file", key="load_pick", on_click=on_pick)
    else:
        st.caption("No .json files in tools/inputs/ yet.")
    st.file_uploader("Or upload a JSON file", type="json", key="upload", on_change=on_upload)
    st.button("Reset to template defaults", key="reset", on_click=lambda: apply_inputs(load_template()))
    msg = st.session_state.pop("load_msg", None)
    if msg:
        getattr(st, msg[0])(msg[1])

cfg = {}

# ---- 1. Context ------------------------------------------------------------
st.header("1. Context")
cfg["title"] = st.text_input(
    "Idea or project title", key="title", placeholder="e.g. Low-cost SDR direction-finding array",
    help="A short name for this evaluation. It appears in the prompt header.")
cfg["domain"] = st.text_input(
    "Domain", key="domain", placeholder="e.g. RF hardware, embedded firmware, mechanical design",
    help="The engineering field. It makes the model apply the right standards and failure modes.")
cfg["problem"] = st.text_area(
    "Problem statement", key="problem", height=100,
    help="What problem exists, who is affected, and what goes wrong today. Be concrete.")
cfg["idea"] = st.text_area(
    "Idea description", key="idea", height=140,
    help="What you propose: main components, interfaces, and how it works. The more specific, the more testable.")
cfg["constraints"] = st.text_area(
    "Constraints", key="constraints", height=100,
    help="Hard limits: budget, schedule, power, size, regulatory requirements, team skills, available hardware.")
cfg["assumptions"] = st.text_area(
    "Stated assumptions", key="assumptions", height=100,
    help="Things you believe but have not proven. Listing them makes the model test them instead of accepting them.")
cfg["prior"] = st.text_area(
    "Known prior work and past attempts", key="prior", height=100,
    help="Existing solutions, past failures, or literature you already know. This stops the model from rediscovering what you know.")

# ---- 2. Stages -------------------------------------------------------------
st.header("2. Validation stages")
st.caption("Untick any stage you do not want the model to run.")
cfg["stages"] = {}
for i, (label, desc) in enumerate(STAGES):
    cfg["stages"][label] = st.checkbox(label, key=f"stage_{i}", help=desc)
    st.caption(desc)

# ---- 3. Matrix -------------------------------------------------------------
st.header("3. Scoring matrix")
cfg["scale"] = st.selectbox(
    "Score scale (top value)", SCALES, key="scale",
    help="5 is a good default: easy to calibrate with anchors. Use 10 only if you write anchors for every level.")
st.caption("Each dimension needs a definition and anchors. Anchors tell scorers, human or LLM, what each level means. "
           "Weights set how much each dimension counts in the final percentage.")

for i, d in enumerate(st.session_state.dims):
    with st.container(border=True):
        c1, c2, c3 = st.columns([4, 1, 1])
        d["name"] = c1.text_input(
            "Dimension name", value=d["name"], key=f"name_{d['id']}",
            help="One word or short phrase, e.g. Feasibility, Risk, Cost.")
        d["weight"] = c2.number_input(
            "Weight", min_value=0.0, max_value=10.0, step=0.5, value=float(d["weight"]),
            key=f"w_{d['id']}", help="Relative importance. 0 keeps the dimension as information only.")
        c3.write("")
        if c3.button("Remove", key=f"rm_{d['id']}"):
            st.session_state.dims.pop(i)
            st.rerun()
        d["definition"] = st.text_area(
            "Definition", value=d["definition"], key=f"def_{d['id']}", height=70,
            help="The question this dimension answers. Make it specific enough that two people would score the same way.")
        a1, a2, a3 = st.columns(3)
        d["low"] = a1.text_area("Anchor: lowest score", value=d["low"], key=f"lo_{d['id']}", height=80,
                                help="What the lowest score looks like, concretely.")
        d["mid"] = a2.text_area("Anchor: middle score", value=d["mid"], key=f"mid_{d['id']}", height=80,
                                help="What a middle score looks like. This anchor reduces scoring drift the most.")
        d["high"] = a3.text_area("Anchor: highest score", value=d["high"], key=f"hi_{d['id']}", height=80,
                                 help="What the top score looks like. Reserve it for cases that meet every criterion.")

if st.button("+ Add dimension"):
    st.session_state.dims.append(make_dim())
    st.rerun()

cfg["dims"] = st.session_state.dims

# ---- 4. Document audit -----------------------------------------------------
st.header("4. Document audit (optional)")
cfg["audit_on"] = st.checkbox(
    "Include the document audit section", key="audit_on",
    help="Adds a consistency audit. Only useful if you paste documents below.")
st.caption("Checks define what the model looks for inside the documents. Each check is a single sentence.")

for i, c in enumerate(st.session_state.checks):
    c1, c2 = st.columns([6, 1])
    c["text"] = c1.text_input(f"Check {i + 1}", value=c["text"], key=f"chk_{c['id']}",
                              help="One audit rule. Make it testable: what would a violation look like?")
    c2.write("")
    if c2.button("Remove", key=f"rmc_{c['id']}"):
        st.session_state.checks.pop(i)
        st.rerun()

if st.button("+ Add check"):
    st.session_state.checks.append(make_check())
    st.rerun()

cfg["checks"] = st.session_state.checks
cfg["docs"] = st.text_area(
    "Documents to audit", key="docs", height=220,
    help="Paste the text, labelled, e.g. [SPEC v2.1] ... [TEST PLAN r3] ... Very long documents "
         "lose accuracy: split them into sections or separate chats.")

# ---- 5. Rules and output ---------------------------------------------------
st.header("5. Scoring rules and output")
cfg["two_pass"] = st.checkbox(
    "Ask for two independent scoring passes", key="two_pass",
    help="The model scores, then re-scores from the input alone. Disagreement exposes unstable judgements.")
cfg["evidence"] = st.checkbox(
    "Require evidence for every score", key="evidence",
    help="Each score must cite the input or be labelled ASSUMED. This makes unsupported scores visible.")
cfg["disagree"] = st.selectbox(
    "When passes disagree", DISAGREE_OPTIONS, key="disagree",
    help="How to treat disagreement. Flagging for a human is safest; the lower score is the conservative option.")
cfg["fmt"] = st.selectbox(
    "Output format", FORMATS, key="fmt",
    help="Markdown is easier to read. JSON is easier to parse into a spreadsheet or database.")
cfg["lang"] = st.text_input(
    "Response language", key="lang",
    help="Language of the model's answer.")

# ---- 6. Generate -----------------------------------------------------------
st.header("6. Generated prompt")
prompt = build_prompt(cfg)
st.caption("Copy with the icon at the top-right of the box, or download it as a text file.")
st.code(prompt, language="markdown")

c1, c2, c3 = st.columns(3)
c1.download_button("Download prompt (.md)", prompt, "validation_prompt.md", "text/markdown")
c2.download_button("Save my inputs (.json)", json.dumps(to_inputs(cfg), indent=2, ensure_ascii=False),
                   "validation_inputs.json", "application/json",
                   help="Same format as prompt_inputs.template.json. Put it in tools/inputs/ or upload it to load it again.")
if c3.button("Save prompt to tools/prompts (.txt)", key="save_txt",
             help="Writes the prompt as a .txt file in the prompts/ folder next to this script."):
    st.success(f"Saved: {save_prompt(prompt, cfg['title'])}")
