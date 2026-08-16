"""Command line entry point.

    python -m occlusion_forensics analyse frame*.png --json report.json

The CLI writes the report to stdout or a file and, optionally, the recovered
image. The recovered image is written with unrecovered pixels as a flat mid-grey
*and* an accompanying support mask, because a viewer cannot see NaN — and a
recovery whose holes are invisible is exactly the artefact this package exists
to avoid producing.
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

import numpy as np

from .image_io import load_stack
from .pipeline import analyse_stack


def _write_png(path: Path, arr: np.ndarray) -> None:
    from PIL import Image

    out = np.clip(np.nan_to_num(arr, nan=0.5), 0.0, 1.0)
    Image.fromarray((out * 255.0 + 0.5).astype(np.uint8)).save(path)


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        prog="occlusion_forensics",
        description=(
            "Deterministic occlusion forensics. Measures what the pixels support; "
            "leaves unobserved regions unfilled."
        ),
    )
    sub = p.add_subparsers(dest="command", required=True)

    a = sub.add_parser("analyse", help="run the full pipeline over a frame stack")
    a.add_argument("frames", nargs="+", type=Path, help="input image files")
    a.add_argument("--tile", type=int, default=16, help="clarity tile size (px)")
    a.add_argument(
        "--reference", type=int, default=0, help="index of the registration reference"
    )
    a.add_argument(
        "--ibp", type=int, default=3, help="back-projection iterations (0 to disable)"
    )
    a.add_argument("--json", type=Path, help="write the report here instead of stdout")
    a.add_argument("--recovered", type=Path, help="write the fused image here (PNG)")
    a.add_argument(
        "--support", type=Path, help="write the support mask here (PNG, white=measured)"
    )
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    if args.command != "analyse":  # pragma: no cover - argparse enforces this
        return 2

    frames = load_stack(args.frames)
    result = analyse_stack(
        frames,
        tile=args.tile,
        reference_index=args.reference,
        ibp_iterations=args.ibp,
        parameters={"input_files": [str(p) for p in args.frames]},
    )

    payload = result.report.to_json()
    if args.json:
        args.json.write_text(payload)
    else:
        print(payload)

    if args.recovered:
        if result.recovery is None:
            print("no recovery to write: coverage was empty", file=sys.stderr)
        else:
            _write_png(args.recovered, result.recovery.image)
    if args.support and result.recovery is not None:
        _write_png(args.support, result.recovery.support.astype(np.float64))

    cov = result.coverage
    if cov.null_space.any():
        print(
            f"note: {cov.null_space_fraction:.1%} of the frame was never observed "
            "and was left unfilled",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
