"""
Agentic AI Testing Architecture — Clean, Simple PowerPoint
17 slides, white background, professional, interview-ready
"""

from pptx import Presentation
from pptx.util import Inches, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ── Simple Colors ──────────────────────────────────────────
WHITE      = RGBColor(0xFF, 0xFF, 0xFF)
BLACK      = RGBColor(0x33, 0x33, 0x33)
DARK       = RGBColor(0x22, 0x22, 0x22)
GRAY       = RGBColor(0x66, 0x66, 0x66)
LIGHT_GRAY = RGBColor(0xE8, 0xE8, 0xE8)
BLUE       = RGBColor(0x1F, 0x4E, 0x79)
LIGHT_BLUE = RGBColor(0xD6, 0xE4, 0xF0)
TABLE_HEAD = RGBColor(0x1F, 0x4E, 0x79)
TABLE_ROW1 = RGBColor(0xF2, 0xF2, 0xF2)
TABLE_ROW2 = WHITE

prs = Presentation()
prs.slide_width  = Inches(13.333)
prs.slide_height = Inches(7.5)


def new_slide():
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    bg = slide.background.fill
    bg.solid()
    bg.fore_color.rgb = WHITE
    return slide


def add_title(slide, text, top=Inches(0.3)):
    tb = slide.shapes.add_textbox(Inches(0.6), top, Inches(12), Inches(0.7))
    p = tb.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(30)
    p.font.color.rgb = BLUE
    p.font.bold = True
    p.font.name = "Calibri"
    # Underline bar
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), top + Inches(0.65), Inches(2.5), Inches(0.04))
    shape.fill.solid()
    shape.fill.fore_color.rgb = BLUE
    shape.line.fill.background()


def add_subtitle(slide, text, top=Inches(1.05)):
    tb = slide.shapes.add_textbox(Inches(0.6), top, Inches(12), Inches(0.5))
    p = tb.text_frame.paragraphs[0]
    p.text = text
    p.font.size = Pt(16)
    p.font.color.rgb = GRAY
    p.font.name = "Calibri"
    p.font.italic = True


def text_box(slide, left, top, width, height, text, size=16, color=BLACK,
             bold=False, align=PP_ALIGN.LEFT, italic=False):
    tb = slide.shapes.add_textbox(left, top, width, height)
    tf = tb.text_frame
    tf.word_wrap = True
    p = tf.paragraphs[0]
    p.text = text
    p.font.size = Pt(size)
    p.font.color.rgb = color
    p.font.bold = bold
    p.font.name = "Calibri"
    p.alignment = align
    p.font.italic = italic
    return tb


def bullet_list(slide, left, top, width, items, size=15, color=BLACK, spacing=4):
    tb = slide.shapes.add_textbox(left, top, width, Inches(len(items) * 0.35))
    tf = tb.text_frame
    tf.word_wrap = True
    for i, item in enumerate(items):
        p = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        p.space_before = Pt(spacing)
        p.space_after = Pt(spacing)
        
        if " -- " in item:
            # Bold prefix
            parts = item.split(" -- ", 1)
            r1 = p.add_run()
            r1.text = "  " + parts[0] + " -- "
            r1.font.size = Pt(size)
            r1.font.color.rgb = color
            r1.font.bold = True
            r1.font.name = "Calibri"
            r2 = p.add_run()
            r2.text = parts[1]
            r2.font.size = Pt(size)
            r2.font.color.rgb = color
            r2.font.name = "Calibri"
        else:
            r = p.add_run()
            r.text = "  " + item
            r.font.size = Pt(size)
            r.font.color.rgb = color
            r.font.name = "Calibri"

        # Bullet character
        from pptx.oxml.ns import qn
        pPr = p._p.get_or_add_pPr()
        for bn in pPr.findall(qn('a:buNone')):
            pPr.remove(bn)
        buChar = pPr.makeelement(qn('a:buChar'), {'char': '\u2022'})
        pPr.append(buChar)

    return tb


def add_table(slide, left, top, width, row_height, headers, rows, font_size=12):
    cols = len(headers)
    total_rows = len(rows) + 1
    table_shape = slide.shapes.add_table(total_rows, cols, left, top, width,
                                         Inches(row_height * total_rows))
    table = table_shape.table
    col_w = int(width / cols)
    for i in range(cols):
        table.columns[i].width = col_w

    for i, h in enumerate(headers):
        cell = table.cell(0, i)
        cell.text = h
        cell.fill.solid()
        cell.fill.fore_color.rgb = TABLE_HEAD
        p = cell.text_frame.paragraphs[0]
        p.font.size = Pt(font_size)
        p.font.color.rgb = WHITE
        p.font.bold = True
        p.font.name = "Calibri"
        p.alignment = PP_ALIGN.LEFT
        cell.vertical_anchor = MSO_ANCHOR.MIDDLE

    for r, row in enumerate(rows):
        for c, val in enumerate(row):
            cell = table.cell(r + 1, c)
            cell.text = str(val)
            cell.fill.solid()
            cell.fill.fore_color.rgb = TABLE_ROW1 if r % 2 == 0 else TABLE_ROW2
            p = cell.text_frame.paragraphs[0]
            p.font.size = Pt(font_size)
            p.font.color.rgb = BLACK
            p.font.name = "Calibri"
            cell.vertical_anchor = MSO_ANCHOR.MIDDLE

    return table_shape


def section_box(slide, left, top, width, height, title, items, title_size=16):
    shape = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, left, top, width, height)
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0xF7, 0xF9, 0xFC)
    shape.line.color.rgb = LIGHT_GRAY
    shape.line.width = Pt(1)

    text_box(slide, left + Inches(0.15), top + Inches(0.08), width - Inches(0.3), Inches(0.35),
             title, size=title_size, color=BLUE, bold=True)
    bullet_list(slide, left + Inches(0.15), top + Inches(0.45), width - Inches(0.3),
                items, size=13, color=DARK)


def slide_num(slide, num):
    text_box(slide, Inches(12.3), Inches(7.05), Inches(0.8), Inches(0.3),
             str(num), size=10, color=GRAY, align=PP_ALIGN.RIGHT)


# ══════════════════════════════════════════════════════════════
# SLIDE 1 — TITLE
# ══════════════════════════════════════════════════════════════
s = new_slide()
# Top blue bar
shape = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(0.08))
shape.fill.solid(); shape.fill.fore_color.rgb = BLUE; shape.line.fill.background()

text_box(s, Inches(0.8), Inches(1.8), Inches(11), Inches(1.0),
         "Agentic AI Testing Architecture", size=40, color=BLUE, bold=True)
text_box(s, Inches(0.8), Inches(2.8), Inches(11), Inches(0.6),
         "for Automated Tool Validation", size=28, color=DARK)

# Divider
shape = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.8), Inches(3.6), Inches(2.5), Inches(0.04))
shape.fill.solid(); shape.fill.fore_color.rgb = BLUE; shape.line.fill.background()

text_box(s, Inches(0.8), Inches(3.9), Inches(11), Inches(0.5),
         "A Meta-Testing Platform -- It tests applications AND it tests itself.", size=18, color=GRAY)

bullet_list(s, Inches(0.8), Inches(4.7), Inches(10), [
    "Accuracy -- AI quality is measured, not assumed",
    "Autonomy -- Minimal human intervention for routine testing",
    "Trust -- Every AI decision is auditable and traceable",
], size=18, color=DARK, spacing=8)

text_box(s, Inches(0.8), Inches(6.3), Inches(6), Inches(0.3),
         "Testing Architect Presentation  |  February 2026", size=12, color=GRAY)
slide_num(s, 1)


# ══════════════════════════════════════════════════════════════
# SLIDE 2 — PROBLEM STATEMENT
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Problem Statement")
add_subtitle(s, "Why we need an Agentic AI Testing Platform")

add_table(s, Inches(0.6), Inches(1.5), Inches(12), 0.45,
    ["Challenge", "Impact on Testing"],
    [
        ["Manual test design doesn't scale", "QA becomes the bottleneck as sprints accelerate; coverage gaps widen silently"],
        ["Jira stories are ambiguous", "35% have missing acceptance criteria; 60% miss negative/edge scenarios"],
        ["Automation scripts break frequently", "42% of failures are just broken locators; teams spend more time fixing than writing tests"],
        ["No confidence in AI-generated tests", "No framework to measure hallucination, coverage, or format consistency"],
    ])

text_box(s, Inches(0.6), Inches(4.2), Inches(12), Inches(0.4),
         "The Goal:", size=18, color=BLUE, bold=True)

bullet_list(s, Inches(0.6), Inches(4.6), Inches(11), [
    "Scale test design without scaling the team",
    "Detect and flag ambiguous requirements automatically",
    "Self-heal broken automation scripts when UI changes",
    "Measure AI quality with empirical metrics (golden datasets, hallucination rate, coverage scores)",
    "Build a feedback loop so the system improves with every cycle",
], size=15)
slide_num(s, 2)


# ══════════════════════════════════════════════════════════════
# SLIDE 3 — HIGH-LEVEL ARCHITECTURE
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "High-Level Architecture")
add_subtitle(s, "5 independent, testable layers")

layers = [
    ("Layer 5: Control Plane", "Supervisor Agent -- Coordinates all agents, makes decisions, triggers retries/escalations"),
    ("Layer 4: Analysis & Metrics", "AI Metrics + Execution Metrics -- Measures accuracy, coverage, hallucination, pass rate, flakiness"),
    ("Layer 3: Automation & Execution", "Script Agent + Execution Engine + RCA Agent -- Generates code, runs tests, analyzes failures"),
    ("Layer 2: Agentic AI", "Requirement Agent + Test Case Agent + Feedback Loop -- Understands stories, generates test cases, learns"),
    ("Layer 1: Input", "Jira Connector + Parser + Validator + Normalizer -- Fetches, validates, standardizes input data"),
]

y = Inches(1.6)
for name, desc in layers:
    shape = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), y, Inches(12), Inches(0.8))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0xF7, 0xF9, 0xFC)
    shape.line.color.rgb = LIGHT_GRAY
    shape.line.width = Pt(1)
    # Left accent
    bar = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), y, Inches(0.06), Inches(0.8))
    bar.fill.solid(); bar.fill.fore_color.rgb = BLUE; bar.line.fill.background()

    text_box(s, Inches(0.85), y + Inches(0.05), Inches(3.5), Inches(0.35),
             name, size=15, color=BLUE, bold=True)
    text_box(s, Inches(0.85), y + Inches(0.38), Inches(11.5), Inches(0.35),
             desc, size=13, color=DARK)
    y += Inches(0.92)

text_box(s, Inches(0.6), Inches(6.3), Inches(12), Inches(0.4),
         "Each layer is independently testable. Data flows down, feedback flows up. Integration boundaries are explicit contract test points.",
         size=13, color=GRAY, italic=True)
slide_num(s, 3)


# ══════════════════════════════════════════════════════════════
# SLIDE 4 — AGENTIC AI DESIGN PHILOSOPHY
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Agentic AI Design Philosophy")
add_subtitle(s, "Multiple specialized agents coordinated by a supervisor agent")

section_box(s, Inches(0.6), Inches(1.6), Inches(3.7), Inches(2.5),
    "Autonomous Execution", [
        "Agents act without step-by-step human instructions",
        "Goal-driven, not rule-driven",
        "Pipeline runs end-to-end on its own",
        "Each agent has authority to proceed, retry, or escalate",
    ])

section_box(s, Inches(4.6), Inches(1.6), Inches(3.7), Inches(2.5),
    "Decision-Making Capability", [
        "Each agent decides and logs its choices",
        "Confidence scores enable smart routing",
        "Decisions are explainable and reversible",
        "Bounded autonomy -- agents can't do catastrophic things",
    ])

section_box(s, Inches(8.6), Inches(1.6), Inches(3.7), Inches(2.5),
    "Feedback-Driven Improvement", [
        "Execution results feed back into prompts",
        "Thresholds adjust based on real outcomes",
        "System measurably improves each cycle",
        "Prompt regression tests prevent degradation",
    ])

text_box(s, Inches(0.6), Inches(4.5), Inches(12), Inches(0.4),
         "Why Multi-Agent (not Monolithic)?", size=18, color=BLUE, bold=True)

bullet_list(s, Inches(0.6), Inches(4.9), Inches(11), [
    "Each agent fails independently -- no single point of failure for the whole system",
    "Each agent is testable in isolation with its own golden dataset and metrics",
    "Agents can scale independently (e.g., 5 execution workers but only 1 RCA agent)",
    "Clear responsibility boundaries make debugging and auditing straightforward",
], size=14)
slide_num(s, 4)


# ══════════════════════════════════════════════════════════════
# SLIDE 5 — MODULE 1: JIRA INGESTION
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Module 1: Jira Ingestion & Validation")
add_subtitle(s, "The entry point -- if garbage enters here, every downstream agent produces garbage")

section_box(s, Inches(0.6), Inches(1.6), Inches(5.7), Inches(2.5),
    "Responsibilities", [
        "Connect to Jira via OAuth / API Token",
        "Fetch stories, bugs, tasks by ID or batch by project",
        "Validate structure -- required fields, supported formats",
        "Normalize content -- strip HTML, resolve macros, fix encoding",
        "Output canonical JSON for all downstream agents",
    ])

section_box(s, Inches(6.7), Inches(1.6), Inches(5.7), Inches(2.5),
    "Testing Focus", [
        "Empty / malformed stories -- flag as incomplete, don't pass downstream",
        "Expired tokens / wrong project -- return clear auth errors (401, 403)",
        "Rate limits (429) -- backoff and retry with Retry-After header",
        "XSS payloads in story text -- sanitize, never render raw",
        "Bulk fetch 100+ stories -- pagination, no timeout, no data mixing",
    ])

add_table(s, Inches(0.6), Inches(4.5), Inches(12), 0.4,
    ["Metric", "Target", "Alert Threshold", "Why It Matters"],
    [
        ["Ingestion Success Rate", ">= 98%", "< 95%", "Failed fetches block the entire pipeline"],
        ["Parsing Error Rate", "< 2%", "> 5%", "Malformed data corrupts downstream AI output"],
        ["Validation Pass Rate", ">= 90%", "< 85%", "Low pass rate may indicate Jira content quality issues"],
        ["Avg Ingestion Latency", "< 2 seconds", "> 5 seconds", "Slow ingestion delays the full pipeline"],
    ])
slide_num(s, 5)


# ══════════════════════════════════════════════════════════════
# SLIDE 6 — MODULE 2: REQUIREMENT UNDERSTANDING
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Module 2: Requirement Understanding Agent")
add_subtitle(s, "Turning Jira stories into structured, testable knowledge")

section_box(s, Inches(0.6), Inches(1.6), Inches(3.7), Inches(2.6),
    "What It Does", [
        "Extract acceptance criteria from",
        "  story body (Gherkin, bullets, prose)",
        "Identify implicit business rules",
        "  (e.g., 'login' implies auth needed)",
        "Detect ambiguity and flag vague",
        "  requirements for human review",
    ])

section_box(s, Inches(4.6), Inches(1.6), Inches(3.7), Inches(2.6),
    "Testing Strategy", [
        "Golden Story Comparison -- 50-100",
        "  stories with human-verified output",
        "Hallucination Detection -- agent must",
        "  NOT invent criteria not in the story",
        "Ambiguity Flag Accuracy -- vague",
        "  phrases flagged, clear ones passed",
    ])

section_box(s, Inches(8.6), Inches(1.6), Inches(3.7), Inches(2.6),
    "Ambiguity Examples", [
        'BAD: "should work correctly"',
        'BAD: "handle errors appropriately"',
        'BAD: "response time acceptable"',
        'GOOD: "login with email & password"',
        'GOOD: "display name on dashboard"',
        "Agent flags BAD, passes GOOD",
    ])

add_table(s, Inches(0.6), Inches(4.6), Inches(12), 0.4,
    ["Metric", "Target", "How We Measure"],
    [
        ["Requirement Interpretation Accuracy", ">= 85%", "Compare agent output vs golden dataset (human-verified extractions)"],
        ["Hallucination Rate", "< 5%", "Count AI-generated items with no source mapping in the original story"],
        ["Ambiguity Detection F1 Score", ">= 80%", "Precision and recall of flagging vague vs clear requirements"],
        ["Business Rule Detection Rate", ">= 75%", "Compare detected implicit rules vs expert-identified rules"],
    ])
slide_num(s, 6)


# ══════════════════════════════════════════════════════════════
# SLIDE 7 — MODULE 3: TEST CASE DESIGN
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Module 3: Test Case Design Agent")
add_subtitle(s, "Generating comprehensive, traceable test cases from structured requirements")

section_box(s, Inches(0.6), Inches(1.6), Inches(5.7), Inches(2.3),
    "What It Generates", [
        "Positive path tests -- happy flow for each acceptance criterion",
        "Negative path tests -- invalid inputs, unauthorized access, timeouts",
        "Edge cases -- boundary values, empty inputs, max lengths, special characters",
        "Risk-based priority assignment (P0-P3) per test case",
        "Full Jira traceability -- every TC links back to Story ID + AC ID",
    ])

section_box(s, Inches(6.7), Inches(1.6), Inches(5.7), Inches(2.3),
    "Testing Strategy", [
        "Coverage completeness -- every AC has positive + negative + edge tests",
        "Duplicate detection -- semantic similarity check (cosine > 0.85 = duplicate)",
        "Golden dataset comparison -- generated TCs vs expert-written TCs (>= 85%)",
        "Consistency -- same input 5 times produces same TC count and coverage",
        "Hallucination check -- no TCs for features not mentioned in the story",
    ])

add_table(s, Inches(0.6), Inches(4.3), Inches(12), 0.4,
    ["Coverage Dimension", "What We Check", "Target"],
    [
        ["AC Coverage", "Every acceptance criterion has at least 1 test case", "100%"],
        ["Positive Path", "Each AC has a happy-path test case", "100%"],
        ["Negative Path", "Each AC has at least 1 failure-mode test case", ">= 90%"],
        ["Edge Cases", "Boundary values, empty inputs, max lengths", ">= 80%"],
        ["Business Rules", "Each identified business rule has violation scenarios", ">= 85%"],
    ])

text_box(s, Inches(0.6), Inches(6.5), Inches(12), Inches(0.3),
         "Output: Structured JSON test cases with ID, title, steps, expected result, priority, confidence score, and Jira traceability.",
         size=13, color=GRAY, italic=True)
slide_num(s, 7)


# ══════════════════════════════════════════════════════════════
# SLIDE 8 — MODULE 4: AUTOMATION SCRIPT AGENT
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Module 4: Automation Script Agent")
add_subtitle(s, "Converting approved test cases into production-quality executable code")

section_box(s, Inches(0.6), Inches(1.6), Inches(3.7), Inches(2.8),
    "Code Generation", [
        "UI tests: Playwright / Selenium",
        "API tests: REST Assured / Supertest",
        "DB tests: Parameterized SQL queries",
        "Follows Page Object Model (POM)",
        "Uses stable locators (data-testid)",
        "Explicit waits, no hard-coded sleeps",
        "Parameterized test data, not embedded",
    ])

section_box(s, Inches(4.6), Inches(1.6), Inches(3.7), Inches(2.8),
    "Quality Validation", [
        "Syntax check -- must compile clean",
        "Locators -- robustness score >= 7/10",
        "Assertions match every expected result",
        "POM structure compliance check",
        "No hard-coded waits (sleep/timeout)",
        "ESLint / static analysis passes",
        "Test data is externalized",
    ])

section_box(s, Inches(8.6), Inches(1.6), Inches(3.7), Inches(2.8),
    "Self-Healing Capability", [
        "Broken locator: find by text/role/label",
        "App flow changed: regenerate script",
        "Confidence > 0.8: auto-apply fix",
        "Confidence < 0.8: flag for human",
        "Traditional recovery: hours to days",
        "Self-healing recovery: seconds to min",
        "Reduces maintenance effort by 70%",
    ])

add_table(s, Inches(0.6), Inches(4.8), Inches(12), 0.4,
    ["Metric", "Target", "What It Validates"],
    [
        ["Script Compilation Success Rate", ">= 95%", "Generated code must actually compile and run"],
        ["Locator Robustness Score (avg)", ">= 7/10", "data-testid=10, id=8, CSS=5, XPath=2 -- higher is more stable"],
        ["POM Compliance Rate", ">= 95%", "Page classes separate from tests, locators as properties, methods for actions"],
        ["Auto-Heal Success Rate", ">= 70%", "Broken locators/flows auto-repaired without human intervention"],
    ])
slide_num(s, 8)


# ══════════════════════════════════════════════════════════════
# SLIDE 9 — MODULE 5: EXECUTION ENGINE
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Module 5: Execution Engine")
add_subtitle(s, "Running tests at scale, reliably, across environments")

section_box(s, Inches(0.6), Inches(1.6), Inches(3.7), Inches(2.5),
    "What It Does", [
        "Execute across Chrome, Firefox, Edge",
        "Parallel execution (10 workers = 10x)",
        "Environment mgmt (QA, Staging, Prod)",
        "CI/CD integration (Jenkins, GH Actions)",
        "Capture screenshots, logs, videos",
    ])

section_box(s, Inches(4.6), Inches(1.6), Inches(3.7), Inches(2.5),
    "Retry Policy", [
        "Element not found: retry 2x, extend wait",
        "Network timeout: retry 3x, exp. backoff",
        "Browser crash: restart browser, retry 2x",
        "Auth expired: refresh token, retry 1x",
        "Assertion failure: NO retry (real bug!)",
    ])

section_box(s, Inches(8.6), Inches(1.6), Inches(3.7), Inches(2.5),
    "Chaos Testing", [
        "Kill browser mid-test: partial results saved",
        "Network disconnect: retry + clear error log",
        "Disk full: graceful error, no silent loss",
        "Memory pressure: clean shutdown + alert",
        "Grid node removed: redistribute to others",
    ])

add_table(s, Inches(0.6), Inches(4.5), Inches(12), 0.4,
    ["Metric", "Target", "Alert", "What It Means"],
    [
        ["Execution Success Rate", ">= 90%", "< 85%", "Percentage of tests that pass"],
        ["Flakiness %", "< 5%", "> 10%", "Tests that flip pass/fail on same code"],
        ["Retry Recovery Rate", ">= 60%", "< 40%", "Tests that pass on retry (transient failures)"],
        ["Parallel Efficiency", ">= 70%", "< 50%", "Actual speedup vs theoretical max"],
        ["Avg Execution Time", "< 45 sec", "> 90 sec", "Mean duration per test script"],
    ])
slide_num(s, 9)


# ══════════════════════════════════════════════════════════════
# SLIDE 10 — MODULE 6: RESULTS & RCA
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Module 6: Results & RCA Agent")
add_subtitle(s, "From test failures to root causes to Jira defects -- closing the loop")

section_box(s, Inches(0.6), Inches(1.6), Inches(3.7), Inches(2.5),
    "Evidence Capture", [
        "Console logs (browser + server)",
        "Screenshot at exact failure point",
        "Video recording of full test run",
        "Network HAR trace",
        "DOM snapshot at failure moment",
    ])

section_box(s, Inches(4.6), Inches(1.6), Inches(3.7), Inches(2.5),
    "Root Cause Classification", [
        "Assertion mismatch --> App Bug",
        "Element not found --> Locator Issue",
        "HTTP 500 in logs --> Backend Bug",
        "Timeout, no response --> Infra Issue",
        "Script syntax error --> Script Bug",
    ])

section_box(s, Inches(8.6), Inches(1.6), Inches(3.7), Inches(2.5),
    "Auto Jira Defect Creation", [
        "Title + steps to reproduce from TC",
        "Evidence attached (screenshot, video)",
        "Severity mapped from test priority",
        "Linked to original Jira story",
        "Duplicate detection (fingerprinting)",
    ])

text_box(s, Inches(0.6), Inches(4.4), Inches(12), Inches(0.4),
         "Critical: False Positive Filtering", size=16, color=BLUE, bold=True)
bullet_list(s, Inches(0.6), Inches(4.75), Inches(11), [
    "Infra failures are NOT filed as app bugs -- saves developer time",
    "Flaky tests (pass on retry) are NOT filed as bugs -- reduces noise",
    "Environment config issues are classified separately -- prevents false alarms",
    "Only confirmed application bugs create Jira defects -- keeps backlog clean",
], size=14)

add_table(s, Inches(0.6), Inches(6.05), Inches(8), 0.35,
    ["Metric", "Target"],
    [
        ["RCA Accuracy %", ">= 80% (validated against golden failure dataset)"],
        ["False Positive Rate", "< 10% of auto-created defects"],
    ])
slide_num(s, 10)


# ══════════════════════════════════════════════════════════════
# SLIDE 11 — AI METRICS FRAMEWORK
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Module 7: AI Metrics Framework")
add_subtitle(s, "AI quality is measured, not assumed -- every AI decision has a quality score")

add_table(s, Inches(0.6), Inches(1.6), Inches(12), 0.5,
    ["AI Metric", "What It Measures", "How We Measure", "Target"],
    [
        ["Requirement Accuracy", "How well the agent extracts acceptance criteria", "Compare output vs human-verified golden dataset", ">= 85%"],
        ["Test Coverage Score", "How thoroughly TCs cover all scenarios", "Weighted: positive (40%) + negative (35%) + edge (25%)", ">= 85%"],
        ["Hallucination Rate", "AI content with no basis in input data", "Trace every output item to source; no mapping = hallucination", "< 5%"],
        ["Decision Confidence", "Agent's self-reported certainty", "Score 0.0-1.0 emitted with every output", ">= 0.85 avg"],
    ])

text_box(s, Inches(0.6), Inches(3.9), Inches(12), Inches(0.4),
         "Confidence-Based Routing (How the system uses these metrics):", size=16, color=BLUE, bold=True)

add_table(s, Inches(0.6), Inches(4.35), Inches(12), 0.4,
    ["Confidence Score", "What Happens", "Human Involvement"],
    [
        [">= 0.85", "Auto-proceed to next agent -- no delay", "None required"],
        ["0.70 - 0.84", "Proceed but flag for optional review", "Optional -- QA can review if available"],
        ["< 0.70", "BLOCK pipeline -- require human approval before continuing", "Mandatory -- must approve or reject"],
    ])

text_box(s, Inches(0.6), Inches(5.65), Inches(12), Inches(0.4),
         "Why this matters:", size=16, color=BLUE, bold=True)

bullet_list(s, Inches(0.6), Inches(5.95), Inches(11), [
    "Without this framework, we're trusting AI blindly -- no way to know if quality is improving or degrading",
    "Golden datasets provide ground truth -- not opinions, but empirical data",
    "Trends over time prove the feedback loop is working (or expose when it isn't)",
    "Enables compliance: every AI decision has a measurable quality score in the audit trail",
], size=14)
slide_num(s, 11)


# ══════════════════════════════════════════════════════════════
# SLIDE 12 — EXECUTION METRICS
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Automation Execution Metrics")
add_subtitle(s, "AI metrics tell us: are we generating the right tests?  Execution metrics tell us: are they running reliably?")

section_box(s, Inches(0.6), Inches(1.6), Inches(5.7), Inches(2.2),
    "Execution Metrics", [
        "Pass / Fail Rate -- target >= 90% (with failure classification)",
        "Retry Recovery Rate -- target >= 60% (transient vs real failures)",
        "Avg Execution Time per Test -- target < 45 seconds",
        "Parallel Efficiency -- target >= 70% of theoretical speedup",
        "Suite Completion Rate -- target >= 98%",
    ])

section_box(s, Inches(6.7), Inches(1.6), Inches(5.7), Inches(2.2),
    "Stability Metrics", [
        "Flaky Test Rate -- target < 5% (root: timing 45%, data 25%, env 20%)",
        "Auto-Heal Success -- target >= 70% of broken locators fixed",
        "Script Regen Success -- target >= 80% when app flow changes",
        "Reduce flakiness by 20% each month until < 2%",
        "Track per-test flakiness history over last 10 runs",
    ])

text_box(s, Inches(0.6), Inches(4.2), Inches(12), Inches(0.4),
         "Correlation Analysis (the real insight):", size=16, color=BLUE, bold=True)

add_table(s, Inches(0.6), Inches(4.6), Inches(12), 0.45,
    ["AI Quality", "Execution Quality", "What This Means", "Action to Take"],
    [
        ["High accuracy", "Low pass rate", "Environment / infrastructure problem", "Fix infra, not the tests"],
        ["Low accuracy", "High pass rate", "Coverage gap -- tests pass but miss real bugs", "Improve AI prompts and golden datasets"],
        ["High hallucination", "High pass rate", "False confidence -- invented tests happen to pass", "Audit test cases against actual requirements"],
        ["Low confidence", "Low pass rate", "Expected -- agent knew it was uncertain", "Route low-confidence items to human review"],
    ])
slide_num(s, 12)


# ══════════════════════════════════════════════════════════════
# SLIDE 13 — SUPERVISOR AGENT
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Supervisor / Orchestrator Agent")
add_subtitle(s, "This agent makes the system truly autonomous")

section_box(s, Inches(0.6), Inches(1.6), Inches(3.7), Inches(2.7),
    "Coordinates All Agents", [
        "Agent A finishes --> trigger Agent B",
        "Pass outputs between agents correctly",
        "Manage dependencies and ordering",
        "Handle concurrent pipelines (20+ stories)",
        "Persist state for crash recovery",
    ])

section_box(s, Inches(4.6), Inches(1.6), Inches(3.7), Inches(2.7),
    "Makes System-Level Decisions", [
        "Confidence >= 0.85: auto-proceed",
        "Confidence 0.70-0.84: proceed + flag",
        "Confidence < 0.70: block, escalate",
        "Timeout: retry with backoff (max 3)",
        "Fatal error: skip + alert operator",
    ])

section_box(s, Inches(8.6), Inches(1.6), Inches(3.7), Inches(2.7),
    "Human-in-Loop Escalation", [
        "Low confidence on P0/critical story",
        "3+ consecutive agent failures",
        "Hallucination rate spikes above 10%",
        "Auto-created Blocker severity defect",
        "Channels: Slack, email, Jira, PagerDuty",
    ])

text_box(s, Inches(0.6), Inches(4.7), Inches(12), Inches(0.4),
         "Pipeline States:", size=16, color=BLUE, bold=True)
text_box(s, Inches(0.6), Inches(5.1), Inches(12), Inches(0.5),
         "INGESTING  -->  INTERPRETING  -->  DESIGNING  -->  SCRIPTING  -->  EXECUTING  -->  ANALYZING  -->  REPORTING  -->  COMPLETE",
         size=16, color=DARK, bold=True, align=PP_ALIGN.CENTER)
text_box(s, Inches(0.6), Inches(5.55), Inches(12), Inches(0.3),
         "Each state transition is logged with timestamp, input, confidence, and decision rationale. Full audit trail.",
         size=13, color=GRAY, italic=True, align=PP_ALIGN.CENTER)

add_table(s, Inches(0.6), Inches(6.0), Inches(8), 0.35,
    ["Metric", "Target"],
    [
        ["Decision Accuracy", ">= 95% (validated against decision golden dataset)"],
        ["Pipeline Completion Rate", ">= 95% of pipelines reach COMPLETE state"],
        ["Escalation Rate", "< 15% (too high = alert fatigue, too low = blind trust)"],
    ])
slide_num(s, 13)


# ══════════════════════════════════════════════════════════════
# SLIDE 14 — FEEDBACK LOOP
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Feedback Loop & Continuous Learning")
add_subtitle(s, "The system gets measurably better over time")

# The loop
shape = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(1.5), Inches(12), Inches(0.8))
shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor(0xF7, 0xF9, 0xFC)
shape.line.color.rgb = LIGHT_GRAY; shape.line.width = Pt(1)
text_box(s, Inches(0.8), Inches(1.55), Inches(11.5), Inches(0.6),
         "Execution Results   -->   Metrics Analysis   -->   Identify Weak Areas   -->   Tune Prompts   -->   Better Output   -->   Repeat",
         size=17, color=BLUE, bold=True, align=PP_ALIGN.CENTER)

section_box(s, Inches(0.6), Inches(2.6), Inches(3.7), Inches(2.5),
    "What Gets Tuned", [
        "LLM prompts (add rules, examples,",
        "  constraints, few-shot samples)",
        "Confidence thresholds (reduce false",
        "  escalations, increase autonomy)",
        "Retry strategies (extend waits vs",
        "  full retry based on failure type)",
    ])

section_box(s, Inches(4.6), Inches(2.6), Inches(3.7), Inches(2.5),
    "Testing the Feedback Loop", [
        "Prompt regression testing: every",
        "  prompt change vs golden dataset",
        "Model drift detection: daily canary",
        "  tests detect LLM behavior shifts",
        "Historical benchmark: monthly data",
        "  proves improvement or exposes drift",
    ])

section_box(s, Inches(8.6), Inches(2.6), Inches(3.7), Inches(2.5),
    "Safeguards", [
        "Prompt version control (Git-tracked)",
        "Rollback to previous version < 5 min",
        "No prompt deploy without regression",
        "  test passing first",
        "Monthly benchmarks: prove the loop",
        "  is actually improving, not degrading",
    ])

text_box(s, Inches(0.6), Inches(5.4), Inches(12), Inches(0.3),
         "Key Principle: Treat prompts like code -- version control, test, review, deploy, rollback.",
         size=15, color=BLUE, bold=True)

add_table(s, Inches(0.6), Inches(5.85), Inches(12), 0.38,
    ["Metric", "Month 1", "Month 2", "Month 3", "Trend"],
    [
        ["Requirement Accuracy", "78%", "83%", "87%", "Improving (+9%)"],
        ["Hallucination Rate", "9%", "5%", "3%", "Improving (-6%)"],
        ["Test Coverage Score", "72%", "78%", "84%", "Improving (+12%)"],
    ])
slide_num(s, 14)


# ══════════════════════════════════════════════════════════════
# SLIDE 15 — END-TO-END FLOW
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "End-to-End Data Flow")
add_subtitle(s, "From Jira story to measured test results -- the complete pipeline")

steps = [
    ("1. Jira Story", "Input arrives"),
    ("2. Ingest & Validate", "Parse, check, normalize"),
    ("3. Understand Req.", "Extract AC, flag ambiguity"),
    ("4. Design Test Cases", "Positive/negative/edge"),
    ("5. Generate Scripts", "Playwright/Selenium code"),
    ("6. Execute Tests", "Parallel, cross-browser"),
    ("7. Analyze & RCA", "Root cause, evidence"),
    ("8. Metrics & Learn", "Feedback, improve"),
]

y = Inches(1.5)
for i, (name, desc) in enumerate(steps):
    x = Inches(0.4) + Inches(i * 1.58)
    shape = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, x, y, Inches(1.4), Inches(1.3))
    shape.fill.solid()
    shape.fill.fore_color.rgb = RGBColor(0xF7, 0xF9, 0xFC)
    shape.line.color.rgb = LIGHT_GRAY; shape.line.width = Pt(1)
    text_box(s, x + Inches(0.05), y + Inches(0.1), Inches(1.3), Inches(0.5),
             name, size=11, color=BLUE, bold=True, align=PP_ALIGN.CENTER)
    text_box(s, x + Inches(0.05), y + Inches(0.65), Inches(1.3), Inches(0.5),
             desc, size=10, color=GRAY, align=PP_ALIGN.CENTER)
    if i < len(steps) - 1:
        text_box(s, x + Inches(1.4), y + Inches(0.35), Inches(0.2), Inches(0.3),
                 ">", size=16, color=BLUE, bold=True, align=PP_ALIGN.CENTER)

text_box(s, Inches(0.6), Inches(3.1), Inches(12), Inches(0.4),
         "At Every Step:", size=16, color=BLUE, bold=True)

bullet_list(s, Inches(0.6), Inches(3.45), Inches(5.5), [
    "Input validated against schema before processing",
    "Output carries a confidence score (0.0 - 1.0)",
    "Supervisor monitors progress and decides next action",
    "Metrics captured and sent to dashboard in real time",
], size=13)

text_box(s, Inches(6.7), Inches(3.1), Inches(6), Inches(0.4),
         "Quality Gates at Each Boundary:", size=16, color=BLUE, bold=True)

bullet_list(s, Inches(6.7), Inches(3.45), Inches(5.5), [
    "Confidence < 0.70: pipeline pauses for human review",
    "Hallucination detected: alert + investigation triggered",
    "Compilation failure: auto-retry with different strategy",
    "RCA classifies infra issue: no false bug filed in Jira",
], size=13)

# Summary row
shape = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(5.3), Inches(12), Inches(0.6))
shape.fill.solid(); shape.fill.fore_color.rgb = RGBColor(0xF7, 0xF9, 0xFC)
shape.line.color.rgb = LIGHT_GRAY; shape.line.width = Pt(1)
text_box(s, Inches(0.8), Inches(5.35), Inches(11.5), Inches(0.5),
         "The feedback arrow: Step 8 results feed back into Steps 2-5, tuning prompts and thresholds so the next cycle is measurably better.",
         size=14, color=DARK, italic=True, align=PP_ALIGN.CENTER)

slide_num(s, 15)


# ══════════════════════════════════════════════════════════════
# SLIDE 16 — COMPLETE METRICS DASHBOARD
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Complete Metrics Dashboard")
add_subtitle(s, "All metrics in one view -- AI quality, execution quality, and operations")

text_box(s, Inches(0.6), Inches(1.5), Inches(5), Inches(0.35),
         "AI Quality Metrics", size=15, color=BLUE, bold=True)
add_table(s, Inches(0.6), Inches(1.85), Inches(5.7), 0.35,
    ["Metric", "Target", "Current"],
    [
        ["Requirement Accuracy", ">= 85%", "87.3%"],
        ["Test Coverage Score", ">= 85%", "83.6%"],
        ["Hallucination Rate", "< 5%", "3.2%"],
        ["Decision Confidence", ">= 0.85", "0.88"],
    ])

text_box(s, Inches(6.7), Inches(1.5), Inches(5), Inches(0.35),
         "Execution Metrics", size=15, color=BLUE, bold=True)
add_table(s, Inches(6.7), Inches(1.85), Inches(5.7), 0.35,
    ["Metric", "Target", "Current"],
    [
        ["Pass Rate", ">= 90%", "88.4%"],
        ["Flakiness", "< 5%", "4.6%"],
        ["Auto-Heal Success", ">= 70%", "73%"],
        ["Parallel Efficiency", ">= 70%", "83%"],
    ])

text_box(s, Inches(0.6), Inches(3.7), Inches(5), Inches(0.35),
         "Operations Metrics", size=15, color=BLUE, bold=True)
add_table(s, Inches(0.6), Inches(4.05), Inches(5.7), 0.35,
    ["Metric", "Target", "Current"],
    [
        ["Pipeline Completion", ">= 95%", "96.2%"],
        ["Mean Time per Story", "< 15 min", "12 min"],
        ["Escalation Rate", "< 15%", "12%"],
    ])

text_box(s, Inches(6.7), Inches(3.7), Inches(5), Inches(0.35),
         "3-Month Learning Trend", size=15, color=BLUE, bold=True)
add_table(s, Inches(6.7), Inches(4.05), Inches(5.7), 0.35,
    ["Metric", "Month 1", "Month 3", "Change"],
    [
        ["Requirement Accuracy", "78%", "87%", "+9%"],
        ["Hallucination Rate", "9%", "3%", "-6%"],
        ["Pass Rate", "80%", "89%", "+9%"],
    ])

text_box(s, Inches(0.6), Inches(5.5), Inches(12), Inches(0.3),
         "Every metric has: a target, an alert threshold, an associated corrective action, and a trend line. No vanity metrics.",
         size=14, color=GRAY, italic=True)
slide_num(s, 16)


# ══════════════════════════════════════════════════════════════
# SLIDE 17 — CLOSING
# ══════════════════════════════════════════════════════════════
s = new_slide()
add_title(s, "Architecture Value & Closing")
add_subtitle(s, "Why this architecture is production-ready")

add_table(s, Inches(0.6), Inches(1.5), Inches(12), 0.5,
    ["Benefit", "What It Means", "Evidence"],
    [
        ["Scalable", "10 stories or 10,000 -- same platform, no extra headcount", "Queue-based, parallel execution, independent agent scaling"],
        ["Self-Healing", "Broken locators auto-fixed, transient failures auto-retried", "Auto-heal >= 70%, retry recovery >= 60%, script regen >= 80%"],
        ["Trustworthy AI", "Every AI decision is measured, audited, and explainable", "Golden datasets, hallucination tracking, confidence routing, audit logs"],
        ["Production-Ready", "CI/CD integrated, security hardened, monitoring live", "Quality gates, prompt regression in pipeline, Grafana dashboards"],
    ])

text_box(s, Inches(0.6), Inches(3.8), Inches(12), Inches(0.4),
         "Return on Investment:", size=18, color=BLUE, bold=True)

add_table(s, Inches(0.6), Inches(4.2), Inches(12), 0.4,
    ["Area", "Before (Manual + Traditional)", "After (Agentic AI Platform)", "Improvement"],
    [
        ["Test design time per story", "3-5 days", "< 15 minutes", "95% reduction"],
        ["Script maintenance effort", "40% of QA time", "Minimal (self-healing)", "70% reduction"],
        ["Bug escape rate to production", "~15%", "< 5%", "67% reduction"],
        ["Test coverage visibility", "Gut feeling / unknown", "Measured: 84% with trend", "From 0% to full visibility"],
    ])

# Closing statement
shape = s.shapes.add_shape(MSO_SHAPE.RECTANGLE, Inches(0.6), Inches(5.8), Inches(12), Inches(0.9))
shape.fill.solid()
shape.fill.fore_color.rgb = BLUE
shape.line.fill.background()
text_box(s, Inches(0.8), Inches(5.9), Inches(11.5), Inches(0.7),
         '"This architecture ensures confidence in both the application under test\nand the AI testing platform itself."',
         size=20, color=WHITE, bold=True, align=PP_ALIGN.CENTER)

slide_num(s, 17)


# ══════════════════════════════════════════════════════════════
# SAVE
# ══════════════════════════════════════════════════════════════
output = r"F:\work\testing-tool\Agentic-AI-Testing-Architecture-v2.pptx"
prs.save(output)
print(f"[OK] Saved: {output}")
print(f"     17 slides, clean white theme, interview-ready")
