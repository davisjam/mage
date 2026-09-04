#!/usr/bin/env python3
"""Run the figure sensors over a site's ``figures/`` directory.

One command, two enforcement points: a site's ``scripts/check-site`` calls this,
and so does CI. Sensors are grouped by severity -- a blocking sensor fails the
build, an audit sensor reports and exits 0.

    python3 figures/check_figures.py                 # scan ./figures
    python3 figures/check_figures.py path/to/figures # scan somewhere else
    python3 figures/check_figures.py --strict-all    # flip audit sensors blocking
    python3 figures/check_figures.py --list          # what runs, and at what severity

The severity split is inherited from the MAGE book build, where it was reached
empirically: the three blocking sensors catch defects that are unambiguously
wrong at any size (text outside its box, a label painted over, text spilling
into a neighbour's box). The audit sensors encode house preference -- routing,
legibility band, colour family -- where a considered exception is legitimate.

A new site starts with everything passing because it has no figures. Once a site
has drained its audit findings to zero, flip it with ``--strict-all`` in that
site's ``check-site`` so the clean state is held.

These sensors are geometry checks. They cannot tell you a figure is making the
wrong argument -- see model/figures.md. Render it and look.
"""

from __future__ import annotations

import argparse
import contextlib
import importlib
import inspect
import io
import os
import pathlib
import sys

HERE = pathlib.Path(__file__).resolve().parent

# name -> (blocking?, one-line description)
SENSORS: dict[str, tuple[bool, str]] = {
    "lint_figure_overflow":                (True,  "text fits inside its box"),
    "lint_figure_text_occlusion":          (True,  "no opaque fill painted over a label"),
    "lint_figure_text_intrusion":          (True,  "no text flows into a foreign box"),
    "lint_figure_label_collision":         (False, "no connector runs through a free label"),
    "lint_figure_font_band":               (False, "text renders inside the legibility band"),
    "lint_figure_dangling_edge":           (False, "every edge terminates on its endpoints"),
    "lint_figure_edge_should_be_orthogonal": (False, "declared orthogonal edges route orthogonally"),
    "lint_figure_legend_text_overflow":    (False, "a boxed label clears its box right border"),
    "lint_figure_family_budget":           (False, "colours stay inside the semantic families"),
}


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("root", nargs="?", default=None,
                    help="directory of .svg figures (default: ./figures, else .)")
    ap.add_argument("--strict-all", action="store_true",
                    help="run every sensor blocking, not just the three defaults")
    ap.add_argument("--quiet", action="store_true",
                    help="suppress clean sensors; show only findings and the summary")
    ap.add_argument("--list", action="store_true", help="list sensors and severities, then exit")
    args = ap.parse_args(argv)

    if args.list:
        for name, (blocking, desc) in SENSORS.items():
            print(f"  {'BLOCKING' if blocking else 'audit   '}  {name:<40} {desc}")
        return 0

    sys.path.insert(0, str(HERE))
    import _figure_scan_root  # noqa: E402 -- must follow the sys.path insert

    root = pathlib.Path(args.root).resolve() if args.root else _figure_scan_root.scan_root()
    os.environ[_figure_scan_root.ENV_VAR] = str(root)

    if not root.is_dir():
        print(f"figure check: no such directory: {root}")
        return 1

    figures = sorted(root.glob("*.svg"))
    print(f"== figure check -- {len(figures)} figure(s) in {root} ==")
    if not figures:
        print("   no figures to check")
        return 0

    failures: list[str] = []
    audit_findings: list[str] = []

    for name, (blocking, desc) in SENSORS.items():
        strict = blocking or args.strict_all
        try:
            mod = importlib.import_module(name)
        except Exception as exc:                      # a missing sensor is a real defect
            print(f"  ERROR  {name}: could not import ({exc})")
            failures.append(name)
            continue

        # figure-overflow grades findings: OVERFLOW (the label SPILLS past its
        # padded box) is a defect; STRAIN (0.90-1.00, a tight but valid fit) is
        # advisory. MAGE's own build gates on spills only --
        # `n_issues += sum(1 for f in overflow if f.verdict == "OVERFLOW")` --
        # because full-width caption lines strain by construction and cannot be
        # widened. Passing --strict here would gate on strain too and force
        # needless rewording of approved captions. Mirror the canonical rule.
        if name == "lint_figure_overflow":
            spills = [f for f in mod.findings() if f.verdict == "OVERFLOW"]
            strain = [f for f in mod.findings() if f.verdict != "OVERFLOW"]
            if spills:
                failures.append(name)
                print(f"  FAIL   {name} -- {desc}  ({len(spills)} spill(s))")
                for f in spills[:10]:
                    print(f'         {f.svg} — fs={f.font_size:g} box_w={f.box_w:g} "{f.text[:48]}"')
            elif strain:
                audit_findings.append(name)
                print(f"  audit  {name} -- {desc}  "
                      f"(0 spills, {len(strain)} tight fit(s) -- advisory)")
            elif not args.quiet:
                print(f"  ok     {name} -- {desc}")
            continue

        # Sensor mains are not uniform: most take an argv list, but
        # lint_figure_dangling_edge reads sys.argv itself. Adapt rather than assume.
        sensor_argv = ["--strict"] if strict else []
        takes_argv = bool(inspect.signature(mod.main).parameters)

        buf = io.StringIO()
        saved_argv = sys.argv
        try:
            sys.argv = [name, *sensor_argv]
            with contextlib.redirect_stdout(buf):
                rc = mod.main(sensor_argv) if takes_argv else mod.main()
        except SystemExit as exc:                     # some sensors exit rather than return
            rc = int(exc.code or 0)
        except Exception as exc:
            print(f"  ERROR  {name}: raised {type(exc).__name__}: {exc}")
            failures.append(name)
            continue
        finally:
            sys.argv = saved_argv

        out = buf.getvalue().rstrip()
        clean = rc == 0 and "clean" in out.lower()

        if rc != 0:
            failures.append(name)
            print(f"  FAIL   {name} -- {desc}")
            print(_indent(out))
        elif clean and args.quiet:
            pass
        elif clean:
            print(f"  ok     {name} -- {desc}")
        else:
            audit_findings.append(name)
            print(f"  audit  {name} -- {desc}")
            print(_indent(out))

    print()
    if failures:
        print(f"figure check FAILED -- {len(failures)} blocking sensor(s): {', '.join(failures)}")
        return 1
    if audit_findings:
        print(f"figure check passed -- {len(audit_findings)} audit sensor(s) reported: "
              f"{', '.join(audit_findings)}")
    else:
        print("figure check passed -- clean")
    return 0


def _indent(text: str, prefix: str = "         ") -> str:
    return "\n".join(prefix + line for line in text.splitlines()) if text else ""


if __name__ == "__main__":
    raise SystemExit(main(sys.argv[1:]))
