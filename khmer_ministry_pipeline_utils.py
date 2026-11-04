#!/usr/bin/env python3
"""
Khmer Ministry Document Preprocessing & Inference Pipeline
==========================================================
Provides rule-based OpenCV cleaning and SAHI tiled inference for real-world
Cambodian Ministry and administrative documents:
1. HSV Color-Space Stamp Erasure (removes red & blue circular official stamps/signatures
   while preserving black/gray Khmer text underneath).
2. Morphological Table Gridline Removal (erases horizontal and vertical solid table borders
   so they do not clip Khmer upper vowels or lower coeng subscripts).
3. Automated Deskewing (fixes rotated scan angles via minimum-area bounding box).
4. Dynamic Bounding-Box Padding & Batch Cropping for Word-Level Recognizers (PARSeq / SVTR / TrOCR).
5. Khmer Unicode Normalization & RapidFuzz Lexicon Post-Processing.
"""

import re
import unicodedata
from typing import List, Tuple, Dict, Optional

import cv2
import numpy as np


# ---------------------------------------------------------------------------
# 1. OPENCV STAMP ERASURE & TABLE LINE REMOVAL
# ---------------------------------------------------------------------------
def remove_colored_stamps_hsv(img_bgr: np.ndarray) -> np.ndarray:
    """
    Removes red and blue circular Ministry stamps and ink signatures using HSV color masking,
    replacing stamp pixels with clean background paper color while keeping dark text intact.
    """
    hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)

    # Red ink wraps around Hue 0-15 and 165-180 in OpenCV HSV
    mask_red1 = cv2.inRange(hsv, np.array([0, 45, 60]), np.array([15, 255, 255]))
    mask_red2 = cv2.inRange(hsv, np.array([165, 45, 60]), np.array([180, 255, 255]))
    # Blue ink (official stamps & ballpoint signatures) lies around Hue 95-135
    mask_blue = cv2.inRange(hsv, np.array([95, 45, 50]), np.array([135, 255, 255]))

    stamp_mask = cv2.bitwise_or(mask_red1, mask_red2)
    stamp_mask = cv2.bitwise_or(stamp_mask, mask_blue)

    # Protect very dark pixels (where black printed Khmer text overlaps with a stamp)
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    dark_text_mask = gray < 75
    stamp_mask[dark_text_mask] = 0

    # Replace stamp pixels with median paper background color
    cleaned = img_bgr.copy()
    bg_color = np.median(img_bgr, axis=(0, 1)).astype(np.uint8)
    cleaned[stamp_mask > 0] = bg_color
    return cleaned


def remove_table_gridlines(img_bgr: np.ndarray, min_line_length: int = 45) -> np.ndarray:
    """
    Detects and removes solid horizontal and vertical table borders using morphological
    operations so table lines do not interfere with word bounding boxes or OCR crops.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    thresh = cv2.adaptiveThreshold(
        ~gray, 255, cv2.ADAPTIVE_THRESH_MEAN_C, cv2.THRESH_BINARY, 15, -2
    )

    # Extract horizontal and vertical lines
    horiz_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (min_line_length, 1))
    vert_kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (1, min_line_length))

    horiz_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, horiz_kernel, iterations=1)
    vert_lines = cv2.morphologyEx(thresh, cv2.MORPH_OPEN, vert_kernel, iterations=1)
    table_mask = cv2.bitwise_or(horiz_lines, vert_lines)
    table_mask = cv2.dilate(table_mask, np.ones((2, 2), np.uint8), iterations=1)

    cleaned = img_bgr.copy()
    bg_color = np.median(img_bgr, axis=(0, 1)).astype(np.uint8)
    cleaned[table_mask > 0] = bg_color
    return cleaned


def deskew_page(img_bgr: np.ndarray, max_skew_deg: float = 5.0) -> np.ndarray:
    """
    Automatically straightens slightly skewed scanned pages using projection/contour angles.
    """
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY_INV | cv2.THRESH_OTSU)[1]
    coords = np.column_stack(np.where(thresh > 0))
    if len(coords) < 100:
        return img_bgr

    angle = cv2.minAreaRect(coords)[-1]
    if angle < -45:
        angle = -(90 + angle)
    else:
        angle = -angle

    if abs(angle) < 0.15 or abs(angle) > max_skew_deg:
        return img_bgr

    h, w = img_bgr.shape[:2]
    center = (w // 2, h // 2)
    M = cv2.getRotationMatrix2D(center, angle, 1.0)
    return cv2.warpAffine(img_bgr, M, (w, h), flags=cv2.INTER_CUBIC, borderMode=cv2.BORDER_REPLICATE)


# ---------------------------------------------------------------------------
# 2. DYNAMIC BOUNDING-BOX CROPPING FOR WORD RECOGNITION
# ---------------------------------------------------------------------------
def crop_words_with_khmer_padding(
    img_bgr: np.ndarray,
    boxes_xyxy: List[Tuple[int, int, int, int]],
    pad_y_ratio: float = 0.12,
    pad_x_ratio: float = 0.05,
) -> List[np.ndarray]:
    """
    Crops detected word regions with extra vertical padding (12% top/bottom) to ensure
    Khmer upper vowels (ិ, ី, ឹ, ឺ) and lower coeng subscripts are never clipped.
    """
    h, w = img_bgr.shape[:2]
    crops = []
    for (x1, y1, x2, y2) in boxes_xyxy:
        bw = max(1, x2 - x1)
        bh = max(1, y2 - y1)
        px = int(bw * pad_x_ratio)
        py = int(bh * pad_y_ratio)

        cx1 = max(0, x1 - px)
        cy1 = max(0, y1 - py)
        cx2 = min(w, x2 + px)
        cy2 = min(h, y2 + py)
        crops.append(img_bgr[cy1:cy2, cx1:cx2])
    return crops


# ---------------------------------------------------------------------------
# 3. KHMER UNICODE NORMALIZATION & LEXICON POST-PROCESSING
# ---------------------------------------------------------------------------
def normalize_khmer_unicode(text: str) -> str:
    """
    Normalizes Khmer Unicode strings into canonical NFC orthographic order
    so visually identical vowel/subscript sequences match during evaluation and SQL search.
    """
    if not text:
        return ""
    text = unicodedata.normalize("NFC", text.strip())
    # Remove zero-width spaces (U+200B) so word-level matching is deterministic
    text = text.replace("\u200b", "").replace("\u200c", "")
    return text


def lexicon_post_process(
    recognized_word: str,
    confidence: float,
    khmer_lexicon: List[str],
    conf_threshold: float = 0.85,
) -> str:
    """
    If recognizer confidence is below `conf_threshold`, snaps the prediction to the closest
    valid Khmer dictionary word within Levenshtein edit distance <= 1 (or RapidFuzz similarity >= 85%).
    """
    cleaned = normalize_khmer_unicode(recognized_word)
    if confidence >= conf_threshold or not khmer_lexicon or cleaned in khmer_lexicon:
        return cleaned

    try:
        from rapidfuzz import process, fuzz
        match = process.extractOne(cleaned, khmer_lexicon, scorer=fuzz.ratio)
        if match and match[1] >= 84.0:
            return match[0]
    except ImportError:
        pass

    return cleaned
