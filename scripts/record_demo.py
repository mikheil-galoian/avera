#!/usr/bin/env python3
"""
AVERA Demo Recorder
═══════════════════
Автоматически снимает питч-ролик: запускает Streamlit, проходит 4 домена,
накладывает подписи, экспортирует MP4 + GIF.

Установка (один раз):
    pip install playwright Pillow imageio imageio-ffmpeg
    python -m playwright install chromium

Запуск:
    cd /Users/mac/Desktop/AVERA
    python scripts/record_demo.py

Результат:
    demo_output/avera_demo.mp4   ← для презентаций
    demo_output/avera_demo.gif   ← для email / LinkedIn / README
    demo_output/frames/          ← отдельные PNG-кадры

Параметры (env-переменные):
    AVERA_DEMO_PORT=8502          порт Streamlit (default: 8502)
    AVERA_DEMO_OUT=demo_output    папка вывода
    AVERA_DEMO_WIDTH=1440         ширина окна браузера
    AVERA_DEMO_HEIGHT=900         высота окна браузера
    AVERA_DEMO_FPS=1              кадров в секунду в GIF/MP4
"""

from __future__ import annotations

import os
import subprocess
import sys
import time
import textwrap
from dataclasses import dataclass, field
from pathlib import Path

# ── optional deps check ───────────────────────────────────────────────────────
_MISSING: list[str] = []
try:
    from PIL import Image, ImageDraw, ImageFont
except ImportError:
    _MISSING.append("Pillow")
try:
    import imageio
except ImportError:
    _MISSING.append("imageio imageio-ffmpeg")
try:
    from playwright.sync_api import sync_playwright, Page, Browser
except ImportError:
    _MISSING.append("playwright")

if _MISSING:
    print("❌  Missing dependencies. Install with:")
    print(f"    pip install {' '.join(_MISSING)}")
    if "playwright" in " ".join(_MISSING):
        print("    python -m playwright install chromium")
    sys.exit(1)

# ── configuration ─────────────────────────────────────────────────────────────
PORT     = int(os.environ.get("AVERA_DEMO_PORT",   "8502"))
OUT_DIR  = Path(os.environ.get("AVERA_DEMO_OUT",   "demo_output"))
WIDTH    = int(os.environ.get("AVERA_DEMO_WIDTH",  "1440"))
HEIGHT   = int(os.environ.get("AVERA_DEMO_HEIGHT", "900"))
FPS      = int(os.environ.get("AVERA_DEMO_FPS",    "1"))

BASE_URL = f"http://localhost:{PORT}"
PROJECT_ROOT = Path(__file__).resolve().parents[1]


# ── shot definition ───────────────────────────────────────────────────────────

@dataclass
class Shot:
    """One screenshot moment in the demo sequence."""
    scenario:    str            # fixture name to select in sidebar
    action:      str            # what to click/do before screenshot
    caption:     str            # bold headline shown at bottom of frame
    sub:         str = ""       # smaller explanation line
    wait_ms:     int = 3000     # ms to wait after action before screenshot
    hold_frames: int = 3        # how many times to repeat this frame in video


SHOTS: list[Shot] = [

    # ── Opening ──────────────────────────────────────────────────────────────
    Shot(
        scenario="bms-fast-charge",
        action="open",
        caption="AVERA — AI Change Verification",
        sub="4 industries · Evidence-first · CI/CD gate enforcer",
        wait_ms=6000,
        hold_frames=4,
    ),

    # ── Automotive: BMS ───────────────────────────────────────────────────────
    Shot(
        scenario="bms-fast-charge",
        action="run",
        caption="Automotive / ISO 26262 / ASIL-D",
        sub="BMS Fast-Charge Thermal — confirmed_regression · risk: HIGH",
        wait_ms=7000,
        hold_frames=5,
    ),

    # ── Automotive: Powertrain ────────────────────────────────────────────────
    Shot(
        scenario="powertrain-overspeed-regression",
        action="run",
        caption="Automotive / ASIL-D — RELEASE BLOCKING",
        sub="Powertrain overspeed: engine RPM exceeds safety limit · PR blocked",
        wait_ms=7000,
        hold_frames=5,
    ),

    # ── Aviation: FADEC ───────────────────────────────────────────────────────
    Shot(
        scenario="fadec-overspeed-regression",
        action="run",
        caption="Aviation / DO-178C / DAL-A — RELEASE BLOCKING",
        sub="FADEC overspeed response: 63 ms > 50 ms threshold",
        wait_ms=7000,
        hold_frames=5,
    ),

    # ── Railway: ETCS ─────────────────────────────────────────────────────────
    Shot(
        scenario="etcs-brake-response-regression",
        action="run",
        caption="Railway / EN-50128 / SIL-4 — RELEASE BLOCKING",
        sub="ETCS brake application: 1387 ms > 1200 ms · safety-critical",
        wait_ms=7000,
        hold_frames=5,
    ),

    # ── Medical: Infusion Pump ────────────────────────────────────────────────
    Shot(
        scenario="infusion-pump-flow-regression",
        action="run",
        caption="Medical / IEC-62304 / Class-C — HIGH RISK",
        sub="Infusion pump flow deviation: 7.8% > 5.0% · corrective action required",
        wait_ms=7000,
        hold_frames=5,
    ),

    # ── Closing ───────────────────────────────────────────────────────────────
    Shot(
        scenario="bms-fast-charge",
        action="none",
        caption="One engine. Four industries. Zero manual triage.",
        sub="avera.ai — AI-powered change verification for safety-critical systems",
        wait_ms=2000,
        hold_frames=6,
    ),
]


# ── overlay renderer ─────────────────────────────────────────────────────────

def _draw_overlay(img: Image.Image, caption: str, sub: str) -> Image.Image:
    """Burn caption + sub-text into the bottom of the frame."""
    # Work in RGBA so alpha compositing works correctly
    base = img.copy().convert("RGBA")
    w, h = base.size

    # ── Semi-transparent dark bar at bottom ──────────────────────────────────
    bar_h = 120
    overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    ov_draw = ImageDraw.Draw(overlay)
    # Solid dark band
    ov_draw.rectangle([(0, h - bar_h), (w, h)], fill=(8, 10, 18, 230))
    # Thin blue accent line at top of bar
    ov_draw.rectangle([(0, h - bar_h), (w, h - bar_h + 3)], fill=(59, 130, 246, 255))
    base = Image.alpha_composite(base, overlay)

    # ── Dark badge background top-right ──────────────────────────────────────
    badge_overlay = Image.new("RGBA", base.size, (0, 0, 0, 0))
    bd_draw = ImageDraw.Draw(badge_overlay)
    bd_draw.rectangle([(w - 310, 0), (w, 48)], fill=(8, 10, 18, 200))
    base = Image.alpha_composite(base, badge_overlay)

    # Back to RGB for drawing text
    img_out = base.convert("RGB")
    draw = ImageDraw.Draw(img_out)

    # ── Fonts ─────────────────────────────────────────────────────────────────
    font_cap = font_sub = font_badge = None
    font_candidates = [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/System/Library/Fonts/Helvetica.ttc",
        "/System/Library/Fonts/Supplemental/Arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]
    for fp in font_candidates:
        if Path(fp).exists():
            try:
                font_cap   = ImageFont.truetype(fp, 34)
                font_sub   = ImageFont.truetype(fp, 21)
                font_badge = ImageFont.truetype(fp, 18)
                break
            except Exception:
                continue

    # ── Caption (bright white on dark bar) ───────────────────────────────────
    cap_y = h - bar_h + 12
    draw.text((32, cap_y), caption, font=font_cap, fill=(255, 255, 255))

    # ── Sub-text ──────────────────────────────────────────────────────────────
    sub_y = cap_y + 48
    wrapped = textwrap.fill(sub, width=95)
    draw.text((32, sub_y), wrapped, font=font_sub, fill=(147, 197, 253))   # light blue

    # ── AVERA badge top-right ─────────────────────────────────────────────────
    badge = "AVERA  ●  AI Verification"
    draw.text((w - 298, 14), badge, font=font_badge, fill=(96, 165, 250))

    return img_out


# ── streamlit controller ─────────────────────────────────────────────────────

def _start_streamlit() -> subprocess.Popen:
    """Start Streamlit in background, return the process."""
    env = os.environ.copy()
    env["PYTHONPATH"] = str(PROJECT_ROOT / "src")
    env["AVERA_DEFAULT_SCENARIO"] = "bms-fast-charge"

    proc = subprocess.Popen(
        [
            sys.executable, "-m", "streamlit", "run",
            str(PROJECT_ROOT / "demo" / "app.py"),
            f"--server.port={PORT}",
            "--server.headless=true",
            "--server.fileWatcherType=none",
        ],
        env=env,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        cwd=str(PROJECT_ROOT),
    )
    return proc


def _wait_for_streamlit(timeout: int = 30) -> None:
    """Poll until Streamlit health endpoint responds."""
    import urllib.request, urllib.error
    deadline = time.time() + timeout
    while time.time() < deadline:
        try:
            urllib.request.urlopen(f"{BASE_URL}/_stcore/health", timeout=2)
            return
        except Exception:
            time.sleep(0.5)
    raise RuntimeError(f"Streamlit did not start within {timeout}s on port {PORT}")


def _select_scenario(page: Page, scenario: str) -> None:
    """Select a scenario in the Streamlit sidebar (Streamlit custom selectbox)."""

    # ── Strategy 1: native HTML <select> (older Streamlit) ───────────────────
    try:
        sel = page.locator("select").first
        if sel.count() and sel.is_visible(timeout=500):
            sel.select_option(label=scenario)
            page.wait_for_timeout(1500)
            return
    except Exception:
        pass

    # ── Strategy 2: Streamlit BaseWeb select — click box, then pick option ───
    # Streamlit renders: div[data-baseweb="select"] > div (shows current value)
    try:
        # Click the selectbox to open dropdown
        sb = page.locator('[data-baseweb="select"]').first
        if sb.count() and sb.is_visible(timeout=1000):
            sb.click()
            page.wait_for_timeout(600)
            # The dropdown list: li[role="option"] or div[role="option"]
            option = page.locator(
                f'[role="option"]:has-text("{scenario}"), '
                f'li:has-text("{scenario}")'
            ).first
            if option.count() and option.is_visible(timeout=1000):
                option.click()
                page.wait_for_timeout(1500)
                return
            # Close dropdown if option not found
            page.keyboard.press("Escape")
    except Exception:
        pass

    # ── Strategy 3: stSelectbox input value injection ────────────────────────
    try:
        inp = page.locator('[data-baseweb="select"] input').first
        if inp.count():
            inp.fill(scenario)
            page.wait_for_timeout(400)
            option = page.locator(f'[role="option"]:has-text("{scenario}")').first
            if option.count():
                option.click()
                page.wait_for_timeout(1500)
                return
    except Exception:
        pass

    # ── Strategy 4: URL param — reload page with scenario query string ────────
    try:
        page.goto(f"{BASE_URL}?scenario={scenario}", wait_until="networkidle", timeout=15_000)
        page.wait_for_timeout(3000)
    except Exception:
        pass


def _click_run(page: Page) -> None:
    """Click the Run Analysis button."""
    run_labels = [
        "Run Analysis",
        "Analyze",
        "Run",
        "▶",
        "Run AVERA",
    ]
    for label in run_labels:
        try:
            btn = page.get_by_text(label, exact=False).first
            if btn.is_visible(timeout=500):
                btn.click()
                return
        except Exception:
            continue

    # Fallback: find any primary button
    try:
        btns = page.locator("button[kind='primary'], button.stButton")
        if btns.count():
            btns.first.click()
    except Exception:
        pass


def _take_screenshot(page: Page, path: Path) -> Image.Image:
    """Take full-page screenshot and return as PIL Image."""
    raw = page.screenshot(full_page=False)
    from io import BytesIO
    img = Image.open(BytesIO(raw)).convert("RGB")
    img.save(path)
    return img


# ── main recording loop ──────────────────────────────────────────────────────

def record() -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    frames_dir = OUT_DIR / "frames"
    frames_dir.mkdir(exist_ok=True)

    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  AVERA Demo Recorder")
    print(f"  Output : {OUT_DIR.resolve()}")
    print(f"  Port   : {PORT}")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

    # Start Streamlit
    print("\n[1/4] Starting Streamlit...", end=" ", flush=True)
    proc = _start_streamlit()
    try:
        _wait_for_streamlit(timeout=40)
        print("ready ✓")
    except RuntimeError as e:
        print(f"\n❌  {e}")
        proc.terminate()
        sys.exit(1)

    # Launch browser
    print("[2/4] Launching browser...", end=" ", flush=True)
    all_frames: list[Image.Image] = []
    frame_idx = 0

    with sync_playwright() as pw:
        browser: Browser = pw.chromium.launch(headless=True)
        ctx = browser.new_context(
            viewport={"width": WIDTH, "height": HEIGHT},
            device_scale_factor=1,
        )
        page = ctx.new_page()
        page.goto(BASE_URL, wait_until="networkidle", timeout=30_000)
        page.wait_for_timeout(2000)
        print("ready ✓")

        print(f"[3/4] Recording {len(SHOTS)} shots...\n")

        for i, shot in enumerate(SHOTS, 1):
            print(f"  [{i:02d}/{len(SHOTS)}] {shot.scenario[:40]:40s} — {shot.caption[:35]}")

            # Select scenario in sidebar
            if shot.action != "none":
                _select_scenario(page, shot.scenario)
                page.wait_for_timeout(1200)

            # Click Run Analysis
            if shot.action == "run":
                _click_run(page)
                page.wait_for_timeout(shot.wait_ms)
            else:
                page.wait_for_timeout(max(shot.wait_ms, 1000))

            # Screenshot
            raw_path = frames_dir / f"raw_{frame_idx:04d}.png"
            img = _take_screenshot(page, raw_path)

            # Add overlay
            img_with_caption = _draw_overlay(img, shot.caption, shot.sub)

            # Repeat frame for hold duration
            for _ in range(shot.hold_frames):
                out_path = frames_dir / f"frame_{frame_idx:04d}.png"
                img_with_caption.save(out_path)
                all_frames.append(img_with_caption)
                frame_idx += 1

        browser.close()
    proc.terminate()

    # ── compile output ───────────────────────────────────────────────────────
    print(f"\n[4/4] Compiling {len(all_frames)} frames...")

    # GIF — good for web, email, LinkedIn, README
    gif_path = OUT_DIR / "avera_demo.gif"
    duration_ms = int(1000 / FPS)
    imageio.mimsave(
        str(gif_path),
        [frame for frame in all_frames],
        format="GIF",
        duration=duration_ms,
        loop=0,
    )
    gif_mb = gif_path.stat().st_size / 1_048_576
    print(f"  GIF  → {gif_path}  ({gif_mb:.1f} MB)")

    # MP4 — for presentations, Loom upload, investor deck embed
    mp4_path = OUT_DIR / "avera_demo.mp4"
    writer = imageio.get_writer(
        str(mp4_path),
        fps=FPS,
        codec="libx264",
        quality=8,
        pixelformat="yuv420p",    # max compatibility (QuickTime, PowerPoint)
    )
    for frame in all_frames:
        import numpy as np
        writer.append_data(np.array(frame))
    writer.close()
    mp4_mb = mp4_path.stat().st_size / 1_048_576
    print(f"  MP4  → {mp4_path}  ({mp4_mb:.1f} MB)")

    # Individual PNG frames
    print(f"  PNG  → {frames_dir}/frame_*.png  ({frame_idx} frames)")

    print("\n━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
    print("  Done.")
    print(f"\n  Open in Finder:")
    print(f"    open {OUT_DIR.resolve()}")
    print("\n  Embed in pitch deck:")
    print(f"    Insert → Video → {mp4_path.name}")
    print("\n  Add to README / LinkedIn:")
    print(f"    ![AVERA Demo]({gif_path.name})")
    print("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")


# ── quick thumbnail (no Streamlit needed) ────────────────────────────────────

def make_thumbnail() -> None:
    """Generate a static pitch thumbnail from fixture data — no Streamlit needed."""
    from PIL import Image, ImageDraw

    W, H = 1200, 630    # OpenGraph / LinkedIn card size
    img = Image.new("RGB", (W, H), color=(10, 12, 16))
    draw = ImageDraw.Draw(img)

    # Background grid lines
    for x in range(0, W, 80):
        draw.line([(x, 0), (x, H)], fill=(22, 27, 40), width=1)
    for y in range(0, H, 80):
        draw.line([(0, y), (W, y)], fill=(22, 27, 40), width=1)

    # Title
    font_big = font_med = font_sm = None
    for fp in [
        "/System/Library/Fonts/Supplemental/Arial Bold.ttf",
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf",
    ]:
        if Path(fp).exists():
            try:
                font_big = ImageFont.truetype(fp, 72)
                font_med = ImageFont.truetype(fp, 28)
                font_sm  = ImageFont.truetype(fp, 20)
                break
            except Exception:
                pass

    draw.text((60, 60),  "AVERA",  font=font_big, fill=(96, 165, 250))
    draw.text((60, 150), "AI Change Verification", font=font_med, fill=(226, 232, 240))
    draw.text((60, 195), "for Safety-Critical Systems", font=font_med, fill=(100, 116, 139))

    # Domain cards
    domains = [
        ("Automotive", "ISO 26262", "ASIL-D", "#3b82f6"),
        ("Aviation",   "DO-178C",   "DAL-A",  "#a855f7"),
        ("Railway",    "EN-50128",  "SIL-4",  "#22c55e"),
        ("Medical",    "IEC-62304", "Class-C","#f97316"),
    ]
    card_w, card_h = 220, 120
    gap = 24
    start_x = 60
    card_y = 310
    for i, (domain, std, level, color) in enumerate(domains):
        x = start_x + i * (card_w + gap)
        # Card bg
        draw.rounded_rectangle([(x, card_y), (x + card_w, card_y + card_h)],
                                radius=10, fill=(17, 21, 32),
                                outline=color, width=2)
        draw.text((x + 14, card_y + 14), domain, font=font_sm, fill=color)
        draw.text((x + 14, card_y + 42), std,    font=font_sm, fill=(148, 163, 184))
        draw.text((x + 14, card_y + 68), level,  font=font_sm, fill=(226, 232, 240))

    # Verdict pills
    verdicts = [
        ("confirmed_regression", (239, 68, 68)),
        ("release_blocking",     (239, 68, 68)),
        ("successful_change",    (34, 197, 94)),
        ("confidence: 0.95",     (96, 165, 250)),
    ]
    pill_x, pill_y = 60, 480
    for label, color in verdicts:
        tw = len(label) * 11 + 24
        draw.rounded_rectangle([(pill_x, pill_y), (pill_x + tw, pill_y + 36)],
                                radius=18, fill=(17, 21, 32), outline=color, width=1)
        draw.text((pill_x + 12, pill_y + 8), label, font=font_sm, fill=color)
        pill_x += tw + 12

    # Tagline
    draw.text((60, 558), "One engine. Four industries. Zero manual triage.",
              font=font_med, fill=(226, 232, 240))
    draw.text((60, 594), "avera.ai",
              font=font_sm, fill=(96, 165, 250))

    out = OUT_DIR / "avera_thumbnail.png"
    OUT_DIR.mkdir(exist_ok=True)
    img.save(out)
    print(f"Thumbnail → {out.resolve()}")
    return out


# ── entry point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(
        description="AVERA Demo Recorder — generates MP4 + GIF pitch video"
    )
    parser.add_argument(
        "--thumbnail-only",
        action="store_true",
        help="Generate only the static pitch thumbnail (no Streamlit needed)",
    )
    args = parser.parse_args()

    if args.thumbnail_only:
        make_thumbnail()
    else:
        record()
