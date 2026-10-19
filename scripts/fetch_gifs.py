#!/usr/bin/env python3
"""Download the videos listed in a JSON array and convert them to GIFs.

Reads a JSON file containing a list of video URLs (mp4/webm), downloads each
one to a local cache, then converts it to an animated GIF with ffmpeg.

Conversion notes:
  * GIFs from video are large. The defaults here are deliberately conservative
    (see --fps/--width/--dither); expect roughly 1-3 MB per source clip.
  * Sources are typically ~10 fps, so raising --fps above that only duplicates
    frames and barely changes the file size. Lowering --fps is what shrinks it.
  * A few entries are single-frame stills; those are written as one-frame GIFs
    via a separate path (the fps filter makes the GIF muxer fail on them).
  * A two-pass palette (palettegen -> paletteuse) is used because a plain
    video->gif conversion looks badly banded.

Usage:
    python scripts/fetch_gifs.py gifs.json --out public/gifz --start-index 81
    python scripts/fetch_gifs.py gifs.json --download-only
"""

import argparse
import json
import shutil
import subprocess
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path

USER_AGENT = "Mozilla/5.0 (compatible; gif-fetcher/1.0)"
VIDEO_SUFFIXES = {".mp4", ".webm", ".mov", ".mkv", ".m4v"}


def is_media_url(url: str) -> bool:
    """True if the URL looks like a downloadable video (not a page link)."""
    try:
        parsed = urllib.parse.urlparse(url)
    except ValueError:
        return False
    if parsed.scheme not in {"http", "https"}:
        return False
    suffix = Path(parsed.path).suffix.lower()
    # tenor's extension-less form: /videos/<hash>/mp4
    return suffix in VIDEO_SUFFIXES or parsed.path.rstrip("/").endswith("/mp4")


def download(url: str, dest: Path) -> None:
    """Download `url` to `dest`, overwriting it."""
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=60) as response:
        dest.write_bytes(response.read())


def frame_count(source: Path) -> int:
    """Number of video frames in `source`, or 0 if it can't be determined."""
    result = subprocess.run(
        [
            "ffprobe", "-v", "error", "-select_streams", "v:0",
            "-count_frames", "-show_entries", "stream=nb_read_frames",
            "-of", "csv=p=0", str(source),
        ],
        capture_output=True,
        text=True,
    )
    try:
        return int(result.stdout.strip())
    except ValueError:
        return 0


def convert(source: Path, dest: Path, *, fps: int, width: int, dither: str,
            max_seconds: float, overwrite: bool) -> bool:
    """Convert `source` to a GIF at `dest`. True on success."""
    if dest.exists() and not overwrite:
        return True

    # min(<width>,iw) avoids upscaling clips that are already small. The comma
    # is escaped because ffmpeg parses this argv value as an expression.
    scale = f"scale=min({width}\\,iw):-2:flags=lanczos"

    command = ["ffmpeg", "-y", "-v", "error", "-i", str(source)]
    if frame_count(source) <= 1:
        # Some entries are single-frame stills. Running them through the fps
        # filter makes the GIF muxer fail on the trailer, so emit one frame
        # directly instead - there is nothing to animate anyway.
        command += ["-frames:v", "1", "-vf", scale]
    else:
        filters = (
            f"fps={fps},{scale},"
            f"split[s0][s1];[s0]palettegen=stats_mode=diff[p];"
            f"[s1][p]paletteuse=dither={dither}:diff_mode=rectangle"
        )
        if max_seconds > 0:
            command += ["-t", str(max_seconds)]
        command += ["-vf", filters]
    command += ["-loop", "0", str(dest)]

    result = subprocess.run(command, capture_output=True, text=True)
    # ffmpeg leaves a 0-byte file behind when it bails out (e.g. single-frame
    # clips), which would otherwise show up as a broken image in the gallery.
    if result.returncode != 0 or not dest.exists() or dest.stat().st_size == 0:
        dest.unlink(missing_ok=True)
        detail = result.stderr.strip().splitlines()[-1:] or ["empty output"]
        print(f"  ffmpeg failed: {detail}", file=sys.stderr)
        return False
    return True


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("source", type=Path, help="JSON file with a list of URLs")
    parser.add_argument("--out", type=Path, default=Path("public/gifz"), help="GIF output dir")
    parser.add_argument("--cache", type=Path, default=Path(".cache/gif-videos"), help="video cache dir")
    parser.add_argument("--prefix", default="cat", help="output name prefix (default cat)")
    parser.add_argument("--start-index", type=int, default=81, help="first index (default 81)")
    parser.add_argument("--fps", type=int, default=12, help="output frame rate (default 12)")
    parser.add_argument("--width", type=int, default=480, help="max width in px (default 480)")
    parser.add_argument("--dither", default="none", help="paletteuse dither (default none)")
    parser.add_argument("--max-seconds", type=float, default=0, help="trim clips longer than this (0 = keep all)")
    parser.add_argument("--delay", type=float, default=0.2, help="seconds between downloads")
    parser.add_argument(
        "--max-bytes",
        type=int,
        default=25 * 1024 * 1024,
        help="warn above this GIF size (default 25 MiB, Cloudflare Pages' per-file cap)",
    )
    parser.add_argument(
        "--drop-oversized",
        action="store_true",
        help="delete GIFs that exceed --max-bytes instead of just warning",
    )
    parser.add_argument("--limit", type=int, default=0, help="process only the first N media URLs")
    parser.add_argument("--download-only", action="store_true", help="fetch videos, skip conversion")
    parser.add_argument("--overwrite", action="store_true", help="redo files that already exist")
    args = parser.parse_args()

    for tool in ("ffmpeg", "ffprobe"):
        if not shutil.which(tool):
            parser.error(f"{tool} not found on PATH")

    urls = json.loads(args.source.read_text(encoding="utf-8"))
    if not isinstance(urls, list):
        parser.error("source JSON must be an array of URLs")

    media = [u for u in urls if is_media_url(u)]
    skipped = [u for u in urls if not is_media_url(u)]
    if args.limit:
        media = media[: args.limit]

    print(f"{len(urls)} entries -> {len(media)} media URLs, {len(skipped)} skipped")
    for url in skipped:
        print(f"  skipped (not media): {url}")

    args.out.mkdir(parents=True, exist_ok=True)
    args.cache.mkdir(parents=True, exist_ok=True)

    downloaded = converted = failed = 0
    oversized: list[str] = []
    total_bytes = 0

    for offset, url in enumerate(media):
        index = args.start_index + offset
        suffix = Path(urllib.parse.urlparse(url).path).suffix or ".mp4"
        video = args.cache / f"{args.prefix}{index}{suffix}"
        gif = args.out / f"{args.prefix}{index}.gif"

        if not video.exists() or args.overwrite:
            try:
                download(url, video)
            except (urllib.error.URLError, TimeoutError) as error:
                print(f"[{index}] download failed: {error}")
                failed += 1
                continue
            time.sleep(args.delay)

        downloaded += 1

        if args.download_only:
            print(f"[{index}] cached {video.name} ({video.stat().st_size} bytes)")
            continue

        if convert(
            video,
            gif,
            fps=args.fps,
            width=args.width,
            dither=args.dither,
            max_seconds=args.max_seconds,
            overwrite=args.overwrite,
        ):
            size = gif.stat().st_size
            if size > args.max_bytes:
                oversized.append(f"{gif.name} ({size / 2**20:.1f} MiB)")
                if args.drop_oversized:
                    gif.unlink()
                    print(f"[{index}] dropped oversized {gif.name} ({size / 2**20:.1f} MiB)")
                    continue
            total_bytes += size
            converted += 1
            print(f"[{index}] {gif.name} ({video.stat().st_size} -> {size} bytes)")
        else:
            failed += 1

    print(f"\nDone: {downloaded} downloaded, {converted} converted, {failed} failed")
    if oversized:
        kept = "dropped" if args.drop_oversized else "KEPT - a static deploy will likely reject these"
        print(f"{len(oversized)} over --max-bytes ({kept}): {', '.join(oversized)}")
    if converted:
        print(f"GIF output: {total_bytes / 1_048_576:.1f} MiB "
              f"(avg {total_bytes / converted / 1024:.0f} KiB each)")
    return 1 if failed else 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\nInterrupted")
        sys.exit(130)
