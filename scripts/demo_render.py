#!/usr/bin/env python3
"""
The Rhythm Reaper - animated demo renderer.

The demo is drawn by docs/render/demo.html (canvas, deterministic: the whole
frame is a pure function of t, so a frame can be re-rendered identically at any
time). This script drives it:

  html                       inject the captured ledger into a scratch copy of demo.html
  capture --start N --end M  render frames [N, M) through headless Chrome over CDP
  encode                     ffmpeg the frame sequence into docs/demo.mp4 and verify it
  all                        html + capture + encode

Every string on screen comes from docs/evidence/demo_scenes.json, which was
written by `demo_build.py capture` - i.e. from real handler output. This script
never invents display text, needs no network and no credentials, and the only
subprocess it spawns is ffmpeg (for encoding) plus the local Chrome that the
Hermes browser sidecar already runs.
"""
from __future__ import annotations

import argparse
import base64
import json
import os
import pathlib
import shutil
import subprocess
import sys
import time
import urllib.request

HERE = pathlib.Path(__file__).resolve().parent.parent
SCENES_JSON = HERE / "docs/evidence/demo_scenes.json"
TEMPLATE = HERE / "docs/render/demo.html"
OUT_MP4 = HERE / "docs/demo.mp4"
WORK = pathlib.Path("/opt/data/cache/scratch/rr-render")
HTML = WORK / "demo.html"
FRAMES = WORK / "frames"
MARKER = "/*__SCENES__*/ {}"

FPS = 30
CHROME = os.environ.get("CDP_ENDPOINT", "http://127.0.0.1:9222")
FFMPEG = shutil.which("ffmpeg") or "/usr/local/bin/ffmpeg"
FFPROBE = shutil.which("ffprobe") or "/usr/local/bin/ffprobe"


# --------------------------------------------------------------------------- html

def build_html() -> dict:
    """Inline the ledger into the template. Fails loudly if the ledger is absent."""
    if not SCENES_JSON.exists():
        sys.exit(f"refusing to render: {SCENES_JSON} is missing - run `demo_build.py capture` first")
    scenes = json.loads(SCENES_JSON.read_text())
    for key in ("counts", "search", "lane", "block", "bad", "good", "respell"):
        if key not in scenes:
            sys.exit(f"refusing to render: ledger is missing the {key!r} section")
    tpl = TEMPLATE.read_text()
    if MARKER not in tpl:
        sys.exit("refusing to render: the SCENES marker is gone from demo.html")
    WORK.mkdir(parents=True, exist_ok=True)
    HTML.write_text(tpl.replace(MARKER, json.dumps(scenes)))
    print(f"[html] {HTML} ({HTML.stat().st_size} bytes, ledger inlined)")
    return scenes


# ------------------------------------------------------------------------ capture

def _cdp_ws(url: str):
    from websockets.sync.client import connect
    return connect(url, max_size=None, open_timeout=30)


class Tab:
    def __init__(self, url: str):
        req = urllib.request.Request(f"{CHROME}/json/new?{url}", method="PUT")
        with urllib.request.urlopen(req, timeout=20) as r:
            self.info = json.loads(r.read())
        self.id = self.info["id"]
        self.ws = _cdp_ws(self.info["webSocketDebuggerUrl"])
        self.n = 0

    def call(self, method: str, **params) -> dict:
        self.n += 1
        self.ws.send(json.dumps({"id": self.n, "method": method, "params": params or {}}))
        while True:
            msg = json.loads(self.ws.recv())
            if msg.get("id") == self.n:
                if "error" in msg:
                    raise RuntimeError(f"{method}: {msg['error']}")
                return msg.get("result", {})

    def evaluate(self, expr: str):
        r = self.call("Runtime.evaluate", expression=expr, returnByValue=True, awaitPromise=False)
        if r.get("exceptionDetails"):
            raise RuntimeError(f"page JS error: {r['exceptionDetails'].get('text')}")
        return r.get("result", {}).get("value")

    def close(self):
        try:
            self.ws.close()
        finally:
            try:
                urllib.request.urlopen(f"{CHROME}/json/close/{self.id}", timeout=10).read()
            except Exception:
                pass


def capture(start: int, end: int, fps: int = FPS) -> None:
    """Render frames [start, end) to PNGs. Resumable: existing frames are skipped."""
    if not HTML.exists():
        sys.exit("run `demo_render.py html` first")
    FRAMES.mkdir(parents=True, exist_ok=True)
    todo = [i for i in range(start, end) if not (FRAMES / f"f{i:05d}.png").exists()]
    if not todo:
        print(f"[capture] frames {start}..{end - 1} already on disk, nothing to do")
        return
    tab = Tab(f"file://{HTML}")
    try:
        tab.call("Page.enable")
        tab.call("Runtime.enable")
        tab.call("Emulation.setDeviceMetricsOverride", width=1600, height=900, deviceScaleFactor=1, mobile=False)
        tab.call("Emulation.setEmulatedMedia", media="screen")
        for _ in range(120):                                    # wait for the page to be ready
            if tab.evaluate("window.ready === true"):
                break
            time.sleep(0.25)
        else:
            sys.exit("page never signalled ready")
        meta = tab.evaluate("JSON.stringify(window.SEEK)")
        meta = json.loads(meta)
        print(f"[capture] page ready: {meta['total']}s, {meta['fps']}fps, {meta['width']}x{meta['height']}")
        t0 = time.time()
        for k, i in enumerate(todo, 1):
            t = i / fps
            tab.evaluate(f"window.seek({t:.6f})")
            shot = tab.call("Page.captureScreenshot", format="png", fromSurface=True, optimizeForSpeed=True)
            (FRAMES / f"f{i:05d}.png").write_bytes(base64.b64decode(shot["data"]))
            if k % 60 == 0 or k == len(todo):
                el = time.time() - t0
                print(f"[capture] {k}/{len(todo)} frames  {el:.0f}s  {k / el:.1f} fps  last f{i:05d}.png", flush=True)
    finally:
        tab.close()
    print(f"[capture] done: {len(todo)} frames written to {FRAMES}")


# ------------------------------------------------------------------------- encode

def encode(scenes: dict, fps: int = FPS, keep: bool = False) -> None:
    meta_f = FRAMES / "f00000.png"
    if not meta_f.exists():
        sys.exit("no frames to encode")
    n = len([p for p in FRAMES.glob("f*.png")])
    duration = float(open(WORK / "duration.txt").read()) if (WORK / "duration.txt").exists() else None
    cmd = [FFMPEG, "-y", "-v", "error", "-framerate", str(fps), "-i", str(FRAMES / "f%05d.png"),
           "-c:v", "libx264", "-preset", "slow", "-crf", "19", "-pix_fmt", "yuv420p",
           "-movflags", "+faststart", str(OUT_MP4)]
    print(f"[encode] {n} frames -> {OUT_MP4}")
    subprocess.run(cmd, check=True)
    probe = subprocess.run([FFPROBE, "-v", "error", "-show_entries", "format=duration,size",
                            "-show_entries", "stream=width,height,codec_name,nb_frames",
                            "-of", "json", str(OUT_MP4)], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    dur = float(info["format"]["duration"])
    st = info["streams"][0]
    print(f"[verify] {st['codec_name']} {st['width']}x{st['height']} {dur:.3f}s "
          f"{st.get('nb_frames')} frames {int(info['format']['size']) / 1e6:.2f} MB")
    if abs(dur * fps - n) > fps + 1:
        sys.exit(f"[verify] FAILED: {n} frames at {fps}fps should be {n / fps:.2f}s, video says {dur:.2f}s")
    print("[verify] duration matches the frame count")
    if not keep:
        shutil.rmtree(FRAMES, ignore_errors=True)
        print(f"[encode] removed the frame sequence (kept {WORK})")


def write_proof(fps: int = FPS) -> dict:
    """Write docs/evidence/demo_proof.json from the encoded file itself - never hand-typed."""
    probe = subprocess.run([FFPROBE, "-v", "error",
                            "-show_entries", "format=duration,size",
                            "-show_entries", "stream=codec_name,pix_fmt,width,height,nb_frames",
                            "-of", "json", str(OUT_MP4)], capture_output=True, text=True, check=True)
    info = json.loads(probe.stdout)
    st = info["streams"][0]
    scenes = json.loads(SCENES_JSON.read_text())
    duration = float(info["format"]["duration"])
    frames = int(st.get("nb_frames") or 0)
    proof = {
        "file": "docs/demo.mp4",
        "duration_s": round(duration, 3),
        "frames": frames,
        "fps": fps,
        "codec": st["codec_name"],
        "pix_fmt": st.get("pix_fmt"),
        "size": f"{st['width']}x{st['height']}",
        "bytes": int(info["format"]["size"]),
        "lanes": scenes["counts"]["lanes"],
        "lane_sweep": f"{scenes['counts']['sweep_ok']}/{scenes['counts']['lanes']}",
        "tools": scenes["counts"]["tools"],
        "validator": {
            "bad_ok": scenes["bad"]["ok"],
            "good_ok": scenes["good"]["ok"],
            "bad_issues": len(scenes["bad"]["issues"]),
        },
        "renderer": "docs/render/demo.html, drawn frame-by-frame through Chrome over CDP by "
                    "scripts/demo_render.py and encoded with ffmpeg",
        "method": "Every frame is a pure function of t, and every string on screen comes from "
                  "docs/evidence/demo_capture.txt - real handler output. Not a screen recording.",
    }
    out = HERE / "docs/evidence/demo_proof.json"
    out.write_text(json.dumps(proof, indent=2) + "\n")
    expect = round(duration * fps)
    if abs(expect - frames) > 2:
        sys.exit(f"[proof] FAILED: {frames} frames at {fps}fps implies {expect}, file says {duration}s")
    print(f"[proof] wrote {out}: {duration}s, {frames} frames, {proof['lane_sweep']} lanes")
    return proof


# --------------------------------------------------------------------------- main

def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["html", "capture", "encode", "proof", "all"])
    ap.add_argument("--start", type=int, default=0)
    ap.add_argument("--end", type=int, default=None)
    ap.add_argument("--fps", type=int, default=FPS)
    ap.add_argument("--keep-frames", action="store_true")
    a = ap.parse_args()

    if a.cmd == "html":
        build_html()
    elif a.cmd == "capture":
        capture(a.start, a.end if a.end is not None else a.start + 300, a.fps)
    elif a.cmd == "encode":
        encode(json.loads(SCENES_JSON.read_text()), a.fps, a.keep_frames)
        write_proof(a.fps)
    elif a.cmd == "proof":
        write_proof(a.fps)
    else:
        build_html()
        total = build_total(a.fps)
        capture(0, total, a.fps)
        encode(json.loads(SCENES_JSON.read_text()), a.fps, a.keep_frames)
        write_proof(a.fps)


def build_total(fps: int) -> int:
    """Ask the page how long the timeline is, so `all` needs no hard-coded duration."""
    tmp = Tab(f"file://{HTML}")
    try:
        tmp.call("Runtime.enable")
        for _ in range(120):
            if tmp.evaluate("window.ready === true"):
                break
            time.sleep(0.25)
        total = tmp.evaluate("window.SEEK.total")
    finally:
        tmp.close()
    n = int(round(total * fps))
    (WORK / "duration.txt").write_text(str(total))
    print(f"[timeline] {total}s -> {n} frames at {fps}fps")
    return n


if __name__ == "__main__":
    main()
