#!/usr/bin/env python3
"""
Synthetic Khmer Ministry & Administrative Document Generator
============================================================
Generates realistic Cambodian Ministry/formal document pages with:
1. Official Kingdom of Cambodia headers & subject lines (Khmer OS Muol & body fonts)
2. Multi-row, multi-column administrative tables with solid gridlines
3. Mixed Khmer-Latin text, dates, and reference numbers
4. Automatic, pixel-accurate YOLO bounding box annotations (<class> <x_center> <y_center> <w> <h>)
5. Realistic visual degradations (Red/Blue official stamps, signatures, QR codes, paper noise, & slight skew)
   that are NOT labeled in the .txt file (teaching YOLO to treat them as negative background samples).

Usage:
    python generate_synthetic_ministry_docs.py --num-samples 500 --output-dir ./dataset/ministry_synth
"""

import os
import random
import math
import argparse
import sys
from pathlib import Path
from typing import List, Tuple, Dict

import cv2
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from PIL import features

# ---------------------------------------------------------------------------
# 1. SAMPLE KHMER ADMINISTRATIVE VOCABULARY & CORPUS
# ---------------------------------------------------------------------------
KINGDOM_HEADER = ["ព្រះរាជាណាចក្រកម្ពុជា", "ជាតិ", "សាសនា", "ព្រះមហាក្សត្រ"]

MINISTRIES = [
    ["ក្រសួងអប់រំ", "យុវជន", "និងកីឡា"],
    ["ក្រសួងសេដ្ឋកិច្ច", "និងហិរញ្ញវត្ថុ"],
    ["ក្រសួងប្រៃសណីយ៍", "និងទូរគមនាគមន៍"],
    ["វិទ្យាស្ថានបច្ចេកវិទ្យាកម្ពុជា"],
    ["មជ្ឈមណ្ឌលបណ្តុះធុរកិច្ចថ្មី", "តេជោ"],
]

DOC_TITLES = [
    ["សេចក្តីជូនដំណឹង"],
    ["សេចក្តីសម្រេច"],
    ["ប្រកាស", "ស្តីពី", "ការជ្រើសរើសបុគ្គលិក"],
    ["លិខិតបង្គាប់ការ"],
]

KHMER_WORDS_POOL = [
    "ការជ្រើសរើស", "បុគ្គលិក", "ជាប់កិច្ចសន្យា", "ដើម្បី", "ចូលបម្រើការងារ",
    "សូមជម្រាបជូនដំណឹង", "ដល់សាធារណជន", "ឱ្យបានជ្រាបថា", "ត្រូវការ", "ចំនួន",
    "១៥", "រូប", "មកបម្រើការងារ", "ដែលមាន", "មុខតំណែង", "ដូចខាងក្រោម៖",
    "មន្ត្រីរាជការ", "បេក្ខជន", "ដែលត្រូវបាន", "ជ្រើសរើស", "នឹងទទួលបាន",
    "ប្រាក់បៀវត្ស", "មូលដ្ឋាន", "សមរម្យ", "ទៅតាម", "តួនាទី", "ភារកិច្ច",
    "បទពិសោធន៍", "និង", "គុណវុឌ្ឍិ", "ស្របតាម", "លក្ខខណ្ឌ", "កំណត់ជាធរមាន។",
    "មានចំណាប់អារម្មណ៍", "សូមចូល", "បំពេញបែបបទ", "ដាក់ពាក្យ", "តាមរយៈ",
    "គេហទំព័រ", "សម្រាប់", "ព័ត៌មានបន្ថែម", "សូមទំនាក់ទំនង", "លេខទូរសព្ទ",
    "០១២", "៩៥៩", "៨៥៩។", "ដំណាក់កាល", "សម្រាំងជ្រើសរើស", "នឹងត្រូវ",
    "អញ្ជើញមក", "សម្ភាស", "ផ្ទាល់មាត់។", "ការទទួលពាក្យ", "ចាប់ផ្តើមពី",
    "ថ្ងៃជូនដំណឹង", "រហូតដល់", "ថ្ងៃទី២៥", "ខែកក្កដា", "ឆ្នាំ២០២៦", "ម៉ោង",
    "១៧:០០", "នាទី។", "រាជធានីភ្នំពេញ", "នាយកដ្ឋាន", "រដ្ឋបាល", "បច្ចេកវិទ្យា",
    "ប្រព័ន្ធ", "ឌីជីថល", "ការអភិវឌ្ឍ", "កម្មវិធី", "ស្រាវជ្រាវ", "បញ្ញាសិប្បនិម្មិត",
    "(Administrative", "Officer)", "(Frontend", "Developer)", "(Backend", "Developer)",
    "(Shortlist)", "(GDP)", "1AY-2720", "No.045/26", "ITC-GIC", "2025-2026"
]

LEGAL_SECTION_TEXT = [
    "អង្គភាពពាក់ព័ន្ធត្រូវអនុវត្តតាមបទប្បញ្ញត្តិនៃច្បាប់ និងលិខិតបទដ្ឋានគតិយុត្តជាធរមាន ដោយធានាឱ្យមានតម្លាភាព ប្រសិទ្ធភាព និងទទួលខុសត្រូវចំពោះការងាររបស់ខ្លួន។",
    "ការរៀបចំ ការគ្រប់គ្រង និងការត្រួតពិនិត្យ ត្រូវអនុវត្តតាមផែនការដែលបានកំណត់ និងត្រូវរាយការណ៍អំពីលទ្ធផលជាប្រចាំទៅកាន់ថ្នាក់ដឹកនាំតាមឋានានុក្រម។",
    "ក្នុងករណីមានបញ្ហាប្រឈម ឬភាពមិនប្រក្រតី អង្គភាពអនុវត្តត្រូវចាត់វិធានការកែសម្រួលជាបន្ទាន់ និងជូនដំណឹងជាលាយលក្ខណ៍អក្សរ ដើម្បីស្វែងរកដំណោះស្រាយសមស្រប។",
    "ថវិកា សម្ភារៈ និងធនធានសាធារណៈ ត្រូវប្រើប្រាស់ដោយសន្សំសំចៃ មានប្រសិទ្ធផល និងស្របតាមគោលការណ៍គ្រប់គ្រងហិរញ្ញវត្ថុសាធារណៈ និងការអនុម័តរបស់ស្ថាប័នមានសមត្ថកិច្ច។",
    "មន្ត្រីរាជការ និងបុគ្គលិកពាក់ព័ន្ធ ត្រូវគោរពវិន័យ សីលធម៌វិជ្ជាជីវៈ ការរក្សាការសម្ងាត់ និងការពារផលប្រយោជន៍សាធារណៈ ក្នុងការបំពេញភារកិច្ចប្រចាំថ្ងៃ។",
    "សេចក្តីណែនាំនេះមានប្រសិទ្ធភាពអនុវត្តចាប់ពីថ្ងៃចុះហត្ថលេខា ហើយស្ថាប័នពាក់ព័ន្ធត្រូវផ្សព្វផ្សាយជូនដំណឹងដល់មន្ត្រី និងភាគីពាក់ព័ន្ធទាំងអស់ឱ្យបានទូលំទូលាយ។",
]

MINISTRY_PARAGRAPHS = [
    "ក្រសួងសូមជម្រាបជូនថា ដើម្បីពង្រឹងប្រសិទ្ធភាពការងារ និងលើកកម្ពស់គុណភាពសេវាសាធារណៈ អង្គភាពពាក់ព័ន្ធត្រូវរៀបចំផែនការអនុវត្តឱ្យបានច្បាស់លាស់ និងកំណត់អ្នកទទួលខុសត្រូវតាមភារកិច្ច។",
    "ការអនុវត្តការងារត្រូវផ្អែកលើគោលការណ៍ស្របច្បាប់ តម្លាភាព គណនេយ្យភាព និងការចូលរួមរបស់ភាគីពាក់ព័ន្ធ។ លទ្ធផលការងារត្រូវប្រមូល ផ្ទៀងផ្ទាត់ និងរាយការណ៍តាមទម្រង់ដែលបានកំណត់។",
    "សូមប្រធានអង្គភាពចាត់ចែងមន្ត្រីជំនាញ ដើម្បីសម្របសម្រួលការងារ ប្រមូលទិន្នន័យ និងតាមដានវឌ្ឍនភាពជាប្រចាំ។ ប្រសិនបើមានការលំបាក សូមរាយការណ៍មកក្រសួងឱ្យបានទាន់ពេលវេលា។",
    "អាស្រ័យហេតុនេះ សូមអង្គភាពពាក់ព័ន្ធអនុវត្តខ្លឹមសារខាងលើដោយយកចិត្តទុកដាក់ និងសហការជាមួយស្ថាប័នពាក់ព័ន្ធ ដើម្បីធានាឱ្យការងារសម្រេចបានតាមគោលដៅ និងតាមកាលកំណត់។",
]

TABLE_HEADERS = ["ល.រ", "មុខតំណែង / តួនាទី", "ចំនួន", "កំណត់សម្គាល់"]
TABLE_ROLES = [
    ["១", ["បុគ្គលិកគាំទ្រផ្នែករដ្ឋបាល", "និងនីតិកម្ម", "(Legal", "Officer)"], "០១ រូប", ["ពេញម៉ោង"]],
    ["២", ["បុគ្គលិកកាត់តវីដេអូ", "(Video", "Editor)"], "០១ រូប", ["កិច្ចសន្យា"]],
    ["៣", ["បុគ្គលិកផ្នែករចនា", "(Multimedia", "Designer)"], "០២ រូប", ["ពេញម៉ោង"]],
    ["៤", ["បុគ្គលិកសម្របសម្រួលគម្រោង", "(Program", "Coordinator)"], "០១ រូប", ["ពេញម៉ោង"]],
    ["៥", ["បុគ្គលិកអភិវឌ្ឍកម្មវិធី", "(Frontend", "Developer)"], "០៥ រូប", ["អាទិភាព"]],
    ["៦", ["បុគ្គលិកអភិវឌ្ឍប្រព័ន្ធ", "(Backend", "Developer)"], "០៥ រូប", ["អាទិភាព"]],
]


# ---------------------------------------------------------------------------
# 2. HELPER FUNCTIONS: FONTS, YOLO BBOX CONVERSION & VISUAL NOISE
# ---------------------------------------------------------------------------
KHMER_TITLE_FONT = "KhmerOSmuol.ttf"
KHMER_BODY_FONTS = ("KhmerOSbattambang.ttf", "KhmerOSsiemreap.ttf")


def load_khmer_fonts(
    font_dir: str, size_body: int = 24, size_header: int = 28
) -> Tuple[ImageFont.FreeTypeFont, ImageFont.FreeTypeFont]:
    """
    Loads the requested official Khmer document font roles.

    Khmer OS Muol is reserved for titles, headers, and section names. Main text uses
    Khmer OS Battambang or Khmer OS Siemreap, selected independently per page.
    """
    available = {}
    if font_dir and os.path.isdir(font_dir):
        available = {p.name.casefold(): p for p in Path(font_dir).glob("*.ttf")}

    required = (KHMER_TITLE_FONT, *KHMER_BODY_FONTS)
    missing = [name for name in required if name.casefold() not in available]
    if missing:
        raise FileNotFoundError(
            "Missing required Khmer OS fonts: "
            + ", ".join(missing)
            + f". Add them to --font-dir ({font_dir})."
        )

    if not features.check("raqm"):
        raise RuntimeError(
            "Pillow lacks libraqm, which is required for correctly shaped Khmer text. "
            f"Current Python: {sys.executable}. "
            "Use a Python environment with a RAQM-enabled Pillow build."
        )

    layout_engine = ImageFont.Layout.RAQM
    chosen_body = random.choice(
        [str(available[name.casefold()]) for name in KHMER_BODY_FONTS]
    )
    chosen_header = str(available[KHMER_TITLE_FONT.casefold()])
    return (
        ImageFont.truetype(chosen_body, size_body, layout_engine=layout_engine),
        ImageFont.truetype(chosen_header, size_header, layout_engine=layout_engine),
    )


def xyxy_to_yolo(box: Tuple[int, int, int, int], img_w: int, img_h: int, pad_x: int = 3, pad_y: int = 4) -> Tuple[float, float, float, float]:
    """
    Converts pixel (x_min, y_min, x_max, y_max) to normalized YOLO (x_center, y_center, w, h)
    with slight padding to protect Khmer upper vowels and lower coeng subscripts.
    """
    x1, y1, x2, y2 = box
    x1 = max(0, x1 - pad_x)
    y1 = max(0, y1 - pad_y)
    x2 = min(img_w, x2 + pad_x)
    y2 = min(img_h, y2 + pad_y)

    bw = x2 - x1
    bh = y2 - y1
    xc = x1 + bw / 2.0
    yc = y1 + bh / 2.0

    return (xc / img_w, yc / img_h, bw / img_w, bh / img_h)


def draw_word_and_record(
    draw: ImageDraw.ImageDraw,
    word: str,
    x: int,
    y: int,
    font: ImageFont.FreeTypeFont,
    img_w: int,
    img_h: int,
    bboxes: List[Tuple[int, float, float, float, float]],
    fill: Tuple[int, int, int] = (20, 20, 20),
) -> int:
    """
    Draws a single word onto the PIL canvas, computes its exact pixel bounding box,
    appends the YOLO normalized label to `bboxes`, and returns the width of the drawn word.
    """
    bbox = draw.textbbox((x, y), word, font=font)
    draw.text((x, y), word, font=font, fill=fill)

    # Convert and record for class 0 (word)
    xc, yc, bw, bh = xyxy_to_yolo(bbox, img_w, img_h)
    if bw > 0.002 and bh > 0.002:
        bboxes.append((0, xc, yc, bw, bh))

    return bbox[2] - bbox[0]


# ---------------------------------------------------------------------------
# 3. SYNTHETIC NOISE & ARTIFACT OVERLAYS (UNLABELED NEGATIVE SAMPLES)
# ---------------------------------------------------------------------------
def draw_synthetic_ministry_stamp(canvas: Image.Image, center_x: int, center_y: int) -> Image.Image:
    """
    Overlays a semi-transparent circular red or blue official Ministry stamp and signature scribble
    on top of existing text (without adding any bounding box labels).
    """
    overlay = Image.new("RGBA", canvas.size, (0, 0, 0, 0))
    odraw = ImageDraw.Draw(overlay)

    # Choose red or blue stamp ink
    is_red = random.random() < 0.75
    alpha = random.randint(110, 175)
    stamp_color = (random.randint(180, 220), random.randint(15, 45), random.randint(15, 45), alpha) if is_red else (20, 50, 190, alpha)

    radius_outer = random.randint(75, 95)
    radius_inner = radius_outer - random.randint(18, 24)

    # Outer double ring
    odraw.ellipse(
        (center_x - radius_outer, center_y - radius_outer, center_x + radius_outer, center_y + radius_outer),
        outline=stamp_color,
        width=3,
    )
    odraw.ellipse(
        (center_x - radius_outer + 5, center_y - radius_outer + 5, center_x + radius_outer - 5, center_y + radius_outer - 5),
        outline=stamp_color,
        width=1,
    )
    # Inner ring
    odraw.ellipse(
        (center_x - radius_inner, center_y - radius_inner, center_x + radius_inner, center_y + radius_inner),
        outline=stamp_color,
        width=2,
    )

    # Center emblem star/scribble
    for angle in range(0, 360, 45):
        rad = math.radians(angle)
        x_end = center_x + int((radius_inner - 12) * math.cos(rad))
        y_end = center_y + int((radius_inner - 12) * math.sin(rad))
        odraw.line((center_x, center_y, x_end, y_end), fill=stamp_color, width=2)

    # Simulated handwritten signature overlapping the stamp
    sig_color = (15, 30, 140, random.randint(140, 200))
    pts = []
    sx, sy = center_x - 60, center_y + random.randint(-20, 20)
    for i in range(12):
        sx += random.randint(8, 18)
        sy += random.randint(-25, 25)
        pts.append((sx, sy))
    odraw.line(pts, fill=sig_color, width=2, joint="curve")

    return Image.alpha_composite(canvas.convert("RGBA"), overlay).convert("RGB")


def draw_qr_and_emblem(draw: ImageDraw.ImageDraw, img_w: int, img_h: int):
    """
    Draws an unlabeled top-left circular emblem and bottom-left QR code to train YOLO
    not to produce false positives on non-text graphics.
    """
    # Top-left circular emblem
    ex, ey, er = 130, 115, 42
    emblem_col = (30, 80, 140)
    draw.ellipse((ex - er, ey - er, ex + er, ey + er), outline=emblem_col, width=3)
    draw.ellipse((ex - er + 6, ey - er + 6, ex + er - 6, ey + er - 6), outline=emblem_col, width=1)
    draw.polygon([(ex, ey - 22), (ex - 18, ey + 15), (ex + 18, ey + 15)], outline=emblem_col, width=2)

    # Bottom-left synthetic QR code
    qx, qy, qsize = 95, img_h - 195, 84
    cell = 6
    draw.rectangle((qx, qy, qx + qsize, qy + qsize), outline=(30, 30, 30), width=2)
    for r in range(1, (qsize // cell) - 1):
        for c in range(1, (qsize // cell) - 1):
            if random.random() < 0.48:
                x0 = qx + c * cell
                y0 = qy + r * cell
                draw.rectangle((x0, y0, x0 + cell - 1, y0 + cell - 1), fill=(25, 25, 25))


# ---------------------------------------------------------------------------
# 4. PAGE GENERATOR (HEADERS + PARAGRAPHS + TABLES + STAMPS)
# ---------------------------------------------------------------------------
def generate_modern_ministry_page(
    sample_idx: int,
    font_dir: str = None,
    img_w: int = 1240,
    img_h: int = 1754,
    page_number: int = 1,
) -> Tuple[np.ndarray, List[Tuple[int, float, float, float, float]]]:
    """
    Generates one synthetic A4 Ministry page (1240x1754 @ ~150 DPI) and its YOLO word boxes.
    """
    # Slightly off-white paper background texture
    bg_tone = random.randint(242, 253)
    canvas = Image.new("RGB", (img_w, img_h), (bg_tone, bg_tone, bg_tone - random.randint(0, 4)))
    draw = ImageDraw.Draw(canvas)

    font_body, font_header = load_khmer_fonts(
        font_dir,
        size_body=random.randint(21, 25),
        size_header=random.randint(26, 30),
    )

    bboxes: List[Tuple[int, float, float, float, float]] = []
    ink_color = (random.randint(10, 40), random.randint(10, 40), random.randint(10, 40))
    word_gap = random.randint(10, 16)

    # 1. Draw Unlabeled Emblem & QR Code (Negative samples)
    draw_qr_and_emblem(draw, img_w, img_h)

    # 2. Draw Kingdom Header (Centered)
    curr_y = 65
    w_k = draw_word_and_record(draw, KINGDOM_HEADER[0], img_w // 2 - 140, curr_y, font_header, img_w, img_h, bboxes, ink_color)
    curr_y += 45
    hx = img_w // 2 - 150
    for motto_word in KINGDOM_HEADER[1:]:
        w = draw_word_and_record(draw, motto_word, hx, curr_y, font_header, img_w, img_h, bboxes, ink_color)
        hx += w + 28

    # 3. Draw Ministry Name (Top-Left under emblem)
    curr_y = 175
    ministry = random.choice(MINISTRIES)
    mx = 85
    for m_word in ministry:
        w = draw_word_and_record(draw, m_word, mx, curr_y, font_header, img_w, img_h, bboxes, ink_color)
        mx += w + word_gap

    # 4. Draw Document Title (Centered)
    curr_y = 250
    title_words = random.choice(DOC_TITLES)
    tx = img_w // 2 - 120
    for t_word in title_words:
        w = draw_word_and_record(draw, t_word, tx, curr_y, font_header, img_w, img_h, bboxes, ink_color)
        tx += w + word_gap

    # 5. Draw Introductory Paragraph Block
    curr_y = 330
    left_margin = 95
    right_margin = img_w - 95
    for _ in range(random.randint(7, 10)):
        cx = left_margin + (50 if _ == 0 else 0)
        while cx < right_margin - 160:
            word = random.choice(KHMER_WORDS_POOL + random.choice(MINISTRY_PARAGRAPHS).split())
            w = draw_word_and_record(draw, word, cx, curr_y, font_body, img_w, img_h, bboxes, ink_color)
            cx += w + word_gap
        curr_y += 44

    # 6. Draw Administrative Table with Gridlines (75% probability)
    if random.random() < 0.75:
        curr_y += 15
        col_x = [left_margin, left_margin + 90, left_margin + 640, left_margin + 810, right_margin]
        row_h = 52
        num_rows = random.randint(4, len(TABLE_ROLES))
        selected_rows = random.sample(TABLE_ROLES, num_rows)

        # Header Row
        draw.rectangle((col_x[0], curr_y, col_x[-1], curr_y + row_h), outline=(40, 40, 40), width=2)
        for c_idx in range(len(TABLE_HEADERS)):
            draw.line((col_x[c_idx], curr_y, col_x[c_idx], curr_y + row_h), fill=(40, 40, 40), width=2)
            cell_words = TABLE_HEADERS[c_idx].split()
            cx = col_x[c_idx] + 14
            for cw in cell_words:
                w = draw_word_and_record(draw, cw, cx, curr_y + 10, font_header, img_w, img_h, bboxes, ink_color)
                cx += w + 10
        curr_y += row_h

        # Data Rows
        for r_data in selected_rows:
            draw.rectangle((col_x[0], curr_y, col_x[-1], curr_y + row_h), outline=(50, 50, 50), width=1)
            for c_idx in range(4):
                draw.line((col_x[c_idx], curr_y, col_x[c_idx], curr_y + row_h), fill=(50, 50, 50), width=1)

            # Col 0: Index
            draw_word_and_record(draw, r_data[0], col_x[0] + 25, curr_y + 10, font_body, img_w, img_h, bboxes, ink_color)
            # Col 1: Role Words
            cx = col_x[1] + 14
            for rw in r_data[1]:
                if cx + 100 < col_x[2]:
                    w = draw_word_and_record(draw, rw, cx, curr_y + 10, font_body, img_w, img_h, bboxes, ink_color)
                    cx += w + 10
            # Col 2: Count
            cx = col_x[2] + 16
            for cnt_w in r_data[2].split():
                w = draw_word_and_record(draw, cnt_w, cx, curr_y + 10, font_body, img_w, img_h, bboxes, ink_color)
                cx += w + 8
            # Col 3: Note
            cx = col_x[3] + 16
            for nw in r_data[3]:
                w = draw_word_and_record(draw, nw, cx, curr_y + 10, font_body, img_w, img_h, bboxes, ink_color)
                cx += w + 8

            curr_y += row_h

    # 7. Draw Closing Paragraph & Date/Signature Block
    curr_y += 30
    for _ in range(random.randint(6, 9)):
        cx = left_margin + (50 if _ == 0 else 0)
        while cx < right_margin - 160:
            word = random.choice(KHMER_WORDS_POOL + random.choice(MINISTRY_PARAGRAPHS).split())
            w = draw_word_and_record(draw, word, cx, curr_y, font_body, img_w, img_h, bboxes, ink_color)
            cx += w + word_gap
        curr_y += 44

    # Bottom-Right Date & Signature Header
    curr_y += 25
    sig_x = img_w - 470
    date_line = ["រាជធានីភ្នំពេញ", "ថ្ងៃទី២៥", "ខែកក្កដា", "ឆ្នាំ២០២៦"]
    cx = sig_x
    for dw in date_line:
        w = draw_word_and_record(draw, dw, cx, curr_y, font_body, img_w, img_h, bboxes, ink_color)
        cx += w + 10

    # 8. Overlay Unlabeled Official Red/Blue Stamp directly over the bottom-right text
    stamp_cx = sig_x + random.randint(80, 180)
    stamp_cy = curr_y + random.randint(25, 65)
    canvas = draw_synthetic_ministry_stamp(canvas, stamp_cx, stamp_cy)

    # 9. Apply Scanner Degradations (Blur / Paper Grain)
    if random.random() < 0.4:
        canvas = canvas.filter(ImageFilter.GaussianBlur(radius=random.uniform(0.3, 0.8)))

    img_np = cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR)
    if random.random() < 0.5:
        noise = np.random.normal(0, random.uniform(2.0, 6.0), img_np.shape).astype(np.int16)
        img_np = np.clip(img_np.astype(np.int16) + noise, 0, 255).astype(np.uint8)

    return img_np, bboxes


def draw_centered_line(
    draw: ImageDraw.ImageDraw,
    text: str,
    y: int,
    font: ImageFont.FreeTypeFont,
    img_w: int,
    img_h: int,
    bboxes: List[Tuple[int, float, float, float, float]],
    fill: Tuple[int, int, int],
) -> int:
    bbox = draw.textbbox((0, 0), text, font=font)
    x = (img_w - (bbox[2] - bbox[0])) // 2
    draw_word_and_record(draw, text, x, y, font, img_w, img_h, bboxes, fill)
    return bbox[3] - bbox[1]


def draw_wrapped_paragraph(
    draw: ImageDraw.ImageDraw,
    words: List[str],
    x: int,
    y: int,
    max_width: int,
    line_height: int,
    font: ImageFont.FreeTypeFont,
    img_w: int,
    img_h: int,
    bboxes: List[Tuple[int, float, float, float, float]],
    fill: Tuple[int, int, int],
    indent: int = 0,
) -> int:
    cursor_x = x + indent
    cursor_y = y
    gap = 9
    for word in words:
        width = draw.textbbox((0, 0), word, font=font)[2]
        if cursor_x > x + indent and cursor_x + width > x + max_width:
            cursor_x = x
            cursor_y += line_height
        draw_word_and_record(
            draw, word, cursor_x, cursor_y, font, img_w, img_h, bboxes, fill
        )
        cursor_x += width + gap
    return cursor_y + line_height


def draw_royal_emblem(draw: ImageDraw.ImageDraw, center_x: int, center_y: int) -> None:
    """Draws a neutral royal-style emblem without using a protected source image."""
    gold = (75, 75, 65)
    draw.ellipse((center_x - 30, center_y - 30, center_x + 30, center_y + 30), outline=gold, width=2)
    draw.polygon(
        [(center_x, center_y - 38), (center_x - 14, center_y + 20), (center_x + 14, center_y + 20)],
        outline=gold,
        width=2,
    )
    draw.line((center_x - 45, center_y + 25, center_x + 45, center_y + 25), fill=gold, width=2)
    draw.arc((center_x - 48, center_y - 5, center_x + 48, center_y + 42), 180, 360, fill=gold, width=2)


def generate_legal_decree_page(
    sample_idx: int,
    font_dir: str = None,
    img_w: int = 1240,
    img_h: int = 1754,
    page_number: int = 1,
) -> Tuple[np.ndarray, List[Tuple[int, float, float, float, float]]]:
    """Generates an older legal-decree layout modeled on the supplied examples."""
    bg_tone = random.randint(238, 250)
    canvas = Image.new("RGB", (img_w, img_h), (bg_tone, bg_tone, bg_tone))
    draw = ImageDraw.Draw(canvas)
    font_body, font_header = load_khmer_fonts(
        font_dir, size_body=random.randint(20, 24), size_header=random.randint(27, 31)
    )
    bboxes: List[Tuple[int, float, float, float, float]] = []
    ink = (random.randint(20, 45), random.randint(20, 45), random.randint(20, 45))
    margin = random.randint(115, 145)

    draw.line((margin, 92, img_w - margin, 92), fill=ink, width=random.choice([2, 3]))
    draw_centered_line(
        draw,
        "ព្រះរាជាណាចក្រកម្ពុជា" if page_number == 1 else "លិខិតបទដ្ឋានគតិយុត្ត - ទំព័របន្ត",
        115,
        font_header,
        img_w,
        img_h,
        bboxes,
        ink,
    )
    draw_centered_line(draw, "ជាតិ សាសនា ព្រះមហាក្សត្រ", 155, font_header, img_w, img_h, bboxes, ink)
    if page_number == 1:
        draw_royal_emblem(draw, img_w // 2, 235)

    if page_number == 1:
        draw_word_and_record(draw, random.choice(["ក្រសួងយុត្តិធម៌", "ក្រសួងមហាផ្ទៃ", "រាជរដ្ឋាភិបាល"]),
                             margin, 205, font_header, img_w, img_h, bboxes, ink)
        draw_word_and_record(draw, "លេខៈ ១២៣/២៦", margin, 245, font_body, img_w, img_h, bboxes, ink)
    if page_number == 1:
        draw_centered_line(draw, random.choice(["សេចក្តីសម្រេច", "ប្រកាស", "អនុក្រឹត្យ"]), 300,
                           font_header, img_w, img_h, bboxes, ink)
        draw_centered_line(draw, random.choice(["ស្តីពី ការគ្រប់គ្រងរដ្ឋបាល", "ស្តីពី ការរៀបចំ និងការប្រព្រឹត្តទៅ"]),
                           345, font_header, img_w, img_h, bboxes, ink)
    draw.line((img_w // 2 - 60, 395, img_w // 2 + 60, 395), fill=ink, width=2)

    y = 425 if page_number == 1 else 185
    intro = [
        "- ផ្អែកតាមរដ្ឋធម្មនុញ្ញនៃព្រះរាជាណាចក្រកម្ពុជា",
        "- យោងតាមច្បាប់ និងលិខិតបទដ្ឋានគតិយុត្តជាធរមាន",
        "- យោងតាមតម្រូវការជាក់ស្តែង និងសារៈសំខាន់នៃការងាររដ្ឋបាល",
    ]
    for line in intro:
        y = draw_wrapped_paragraph(draw, line.split(), margin + 25, y, img_w - 2 * margin - 25,
                                   34, font_body, img_w, img_h, bboxes, ink) + 2

    y = draw_centered_line(draw, "សម្រេច", y + 10, font_header, img_w, img_h, bboxes, ink) + y + 18
    khmer_numbers = ["១", "២", "៣", "៤", "៥", "៦", "៧", "៨", "៩", "១០"]
    section_count = random.randint(6, 8)
    for index in range(section_count):
        heading = f"{khmer_numbers[index]}-"
        section_words = [heading] + random.choice(LEGAL_SECTION_TEXT).split()
        section_words += random.choice(LEGAL_SECTION_TEXT).split()[:random.randint(8, 18)]
        y = draw_wrapped_paragraph(draw, section_words, margin, y, img_w - 2 * margin,
                                   35, font_body, img_w, img_h, bboxes, ink, indent=0)
        y += 8
        if y >= img_h - 470:
            break

    y = min(y + 12, img_h - 430)
    draw_wrapped_paragraph(draw, ["រាជធានីភ្នំពេញ", "ថ្ងៃទី២៥", "ខែកក្កដា", "ឆ្នាំ២០២៦"],
                           img_w - 500, y, 390, 35, font_body, img_w, img_h, bboxes, ink)
    stamp_cx, stamp_cy = img_w - 330, img_h - 260
    canvas = draw_synthetic_ministry_stamp(canvas, stamp_cx, stamp_cy)
    draw = ImageDraw.Draw(canvas)
    draw_wrapped_paragraph(draw, ["ហត្ថលេខា", "រដ្ឋមន្ត្រី"], img_w - 480, stamp_cy + 90, 330,
                           35, font_body, img_w, img_h, bboxes, ink)

    draw.line((margin, img_h - 95, img_w - margin, img_h - 95), fill=ink, width=2)
    draw_centered_line(draw, "រាជរដ្ឋាភិបាលកម្ពុជា - លិខិតបទដ្ឋានគតិយុត្ត", img_h - 75,
                       font_body, img_w, img_h, bboxes, ink)
    return cv2.cvtColor(np.array(canvas), cv2.COLOR_RGB2BGR), bboxes


def generate_single_ministry_page(
    sample_idx: int,
    font_dir: str = None,
    img_w: int = 1240,
    img_h: int = 1754,
    layout: str = "mixed",
    page_number: int = 1,
) -> Tuple[np.ndarray, List[Tuple[int, float, float, float, float]]]:
    """Generates a requested official layout or randomly mixes both families."""
    if layout == "legal" or (layout == "mixed" and random.random() < 0.5):
        return generate_legal_decree_page(sample_idx, font_dir, img_w, img_h, page_number)
    return generate_modern_ministry_page(sample_idx, font_dir, img_w, img_h, page_number)


def main():
    parser = argparse.ArgumentParser(description="Generate Synthetic Khmer Ministry Documents + YOLO Labels")
    parser.add_argument("--num-samples", type=int, default=100, help="Number of synthetic pages to generate")
    parser.add_argument("--font-dir", type=str, default="./fonts", help="Directory containing Khmer .ttf fonts")
    parser.add_argument("--output-dir", type=str, default="./dataset/ministry_synth", help="Output dataset directory")
    parser.add_argument(
        "--layout",
        choices=("mixed", "modern", "legal"),
        default="mixed",
        help="Document family: modern ministry letter, legal decree, or a mixture",
    )
    parser.add_argument(
        "--pages-per-document",
        type=int,
        default=1,
        help="Number of synthetic pages per document; useful for multi-page PDF-style data",
    )
    args = parser.parse_args()
    if args.pages_per_document < 1:
        parser.error("--pages-per-document must be at least 1")

    # Create standard Ultralytics YOLO directory structure (75% train, 15% val, 10% test)
    splits = ["train", "val", "test"]
    for sp in splits:
        os.makedirs(os.path.join(args.output_dir, "images", sp), exist_ok=True)
        os.makedirs(os.path.join(args.output_dir, "labels", sp), exist_ok=True)

    total_pages = args.num_samples * args.pages_per_document
    print(f"[*] Generating {total_pages} synthetic Khmer pages into '{args.output_dir}'...")
    page_index = 0
    for document_index in range(args.num_samples):
        for page_number in range(1, args.pages_per_document + 1):
            r = random.random()
            split = "train" if r < 0.75 else ("val" if r < 0.90 else "test")

            img_bgr, bboxes = generate_single_ministry_page(
                page_index,
                font_dir=args.font_dir,
                layout=args.layout,
                page_number=page_number,
            )
            base_name = (
                f"document_{document_index:05d}_page_{page_number:02d}"
                if args.pages_per_document > 1
                else f"ministry_page_{document_index:05d}"
            )

            img_path = os.path.join(args.output_dir, "images", split, f"{base_name}.png")
            lbl_path = os.path.join(args.output_dir, "labels", split, f"{base_name}.txt")

            cv2.imwrite(img_path, img_bgr)
            with open(lbl_path, "w", encoding="utf-8") as f:
                for cls_id, xc, yc, bw, bh in bboxes:
                    f.write(f"{cls_id} {xc:.6f} {yc:.6f} {bw:.6f} {bh:.6f}\n")
            page_index += 1

    # Write data.yaml for Ultralytics YOLO
    yaml_path = os.path.join(args.output_dir, "data.yaml")
    with open(yaml_path, "w", encoding="utf-8") as f:
        f.write(f"path: {os.path.abspath(args.output_dir)}\n")
        f.write("train: images/train\n")
        f.write("val: images/val\n")
        f.write("test: images/test\n")
        f.write("nc: 1\n")
        f.write("names: ['khmer_word']\n")

    print(f"[+] Done! YOLO dataset config written to: {yaml_path}")


if __name__ == "__main__":
    main()
