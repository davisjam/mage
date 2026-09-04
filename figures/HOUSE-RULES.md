# Figure house rules

The portable drawing vocabulary for the Davis web portfolio, extracted from the
MAGE book's figure system. Copied into each site as `figures/`; a site's figure
check runs from the site repo with no reference to `davis-web`.

**The doctrine is not here.** Read [`model/figures.md`](../../model/figures.md)
in the orchestrator, and invoke the `self-communicate` skill, whose drawing leg
lives at
`repos/model-based-agentic-software-engineering/plugin/mage/skills/self-communicate/drawing/`.
This file is the mechanical reference: what to run, what the colours mean, what
the sensors will reject.

## Run the checks

```bash
python3 figures/check_figures.py            # scan ./figures
python3 figures/check_figures.py --list     # what runs, and at what severity
python3 figures/check_figures.py --quiet    # findings and summary only
python3 figures/check_figures.py --strict-all   # once the site is clean, hold it
```

Individual sensors take explicit paths and a `--strict` flip:

```bash
python3 figures/lint_figure_overflow.py --strict
python3 figures/lint_figure_label_collision.py figures/research-lineage.svg
```

### Severity

| | Sensor | Catches |
|---|---|---|
| **blocking** | `figure-overflow` | text runs outside its box |
| **blocking** | `figure-text-occlusion` | an opaque fill painted over a label |
| **blocking** | `figure-text-intrusion` | text flowing into a neighbour's box |
| audit | `figure-label-collision` | a connector stroke crossing a free label |
| audit | `figure-font-band` | text below the 12 px legibility floor |
| audit | `figure-dangling-edge` | an edge not terminating on its endpoints |
| audit | `figure-edge-should-be-orthogonal` | a declared-orthogonal edge routing on a slope |
| audit | `figure-legend-text-overflow` | a boxed label crossing its box's right border |
| audit | `figure-family-budget` | colours outside the declared semantic families |

The three blocking sensors catch defects that are wrong at any size. The audit
sensors encode house preference, where a considered exception is legitimate.
Once a site's audit findings are drained to zero, add `--strict-all` to its
`scripts/check-site` so the clean state is held.

## Declare your semantic families

`figure-family-budget` wants each figure to declare the colour roles it uses, as
an HTML comment near the top of the SVG:

```svg
<!-- semantic-families: modeling, governance, neutral -->
```

An undeclared figure is reported, not failed. Declaring is how a reader — and
the next author — knows which roles the figure meant to be in, so an accidental
sixth colour shows up as drift rather than passing silently.

## Colour by role, never by hex

There are exactly **five** families. These names are what the
`semantic-families` header must use -- the sensor rejects anything else.

| Family | Meaning | Stroke | Fill |
|---|---|---|---|
| `modeling` | the governed thing, the model, established evidence | `#1f7a4d` | `#e3f0e7` |
| `governance` | authority, decision, the accent | `#9a3f12` | `#faf1e6` |
| `agent` | the acting party | `#2f5169` | `#e7edf3` |
| `failure` | failure, defect, waste, what is absent | `#b23b3b` | `#fbeaea` |
| `neutral` | structure, panels, surroundings | `#57534e` | `#f6f4ef` |

Palette tokens named `diagram-trust` exist, but **`trust` is not a family**.
Reaching for it puts colours outside the budget.

Dashed strokes mean **derived or conjectural** — never merely "less important".

Page chrome and figures use separate palettes. A figure never reaches for the
page's `--accent` as decoration; the page never imports a diagram colour.

## Type

Source Sans 3 for figure text (`figure.font-role: body`). Never below **12 px**.
Headers bold and tinted to their family; edge labels italic and muted.
Typography carries hierarchy — do not set everything bold.

Authoritative values live in `design-tokens.json`; read them through
`design_tokens.py` rather than copying hexes:

```bash
python3 figures/design_tokens.py --help
```

## Two authoring paths

**d2** — declarative, for figures that fit its constructs. `_house-style.d2` is
the class include that maps the tokens onto d2 classes:

```bash
d2 --font-regular <SourceSans3-Regular.ttf> \
   --font-bold    <SourceSans3-Bold.ttf> \
   --font-italic  <SourceSans3-It.ttf> \
   figures/research-lineage.d2 figures/research-lineage.svg
```

Commit both the `.d2` and the rendered `.svg`, so the figure is reviewable
without a d2 install. Two gotchas found in MAGE's pilot: `stroke-width` and
`font-size` must be integers; unconnected top-level blocks spread horizontally
under dagre, so force a vertical stack with a root `grid-columns: 1`.

**Hand-authored SVG** — for figures whose composition is the argument, where a
layout engine would fight you. Open one of MAGE's
(`repos/model-based-agentic-software-engineering/book/assets/*.svg`) to see the
house conventions: a header comment naming the figure and stating its ONE JOB,
explicit coordinates, semantic classes, text painted last.

Choose by fit, not by preference. If the figure is a pipeline, a cycle, a grid,
or nested containers, d2 will hold it and stay maintainable. If it needs an
axis, a spatial argument, or deliberate asymmetry, hand-author it.

## The loop

```text
recover the claim → pre-layout plan → draw → check → LOOK
```

The sensors are geometry checks. They cannot tell you the figure is making the
wrong argument, or that it is making two arguments, or that it is beautiful and
says nothing. Render it and look at it before you call it done.

## Provenance

Extracted from `repos/model-based-agentic-software-engineering`:

| Here | From |
|---|---|
| `design-tokens.json`, `design_tokens.py` | `book-models/` |
| `glyph-advances.json` | `book-models/` — font metrics, so no TTFs are needed |
| `lint_figure_*.py` (9) | `book-models/`, with the scan root parameterized |
| `_svg_fit.py` | five pure helpers from `tests/svg_fit.py` |
| `_house-style.d2` | `book/d2-pilot/` |

Deliberately **not** extracted: `catalog.py` orchestration, caption tiers, the
Typst projection, and the book's own figure-scoping rules. Those are MAGE's, and
copying them would have been the wrong abstraction.
