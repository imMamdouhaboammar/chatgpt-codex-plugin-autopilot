---
name: plugin-brand-identity-designer
description: Use when a ChatGPT/Codex Plugin needs a production-ready visual identity and SVG logo system that clearly expresses the Plugin's job across light and dark surfaces.
---

# Plugin Brand Identity Designer

Create a small, distinctive identity for the Plugin after its public product boundary is clear. The logo must communicate the Plugin's actual job, not generic "AI" imagery.

## Required outputs

For every public Plugin prepared by Autopilot, create at minimum:

- `assets/logo-light.svg`
- `assets/logo-dark.svg`
- one square composer/icon asset suitable for small UI contexts
- a short brand rationale describing concept, geometry, palette, and small-size behavior

Prefer SVG for the logo system unless the current OpenAI contract or target surface requires another format. Keep all declared manifest assets package-relative and under `assets/`.

## Design procedure

1. Read the conversion brief and Plugin experience brief before drawing anything.
2. Reduce the product to one visual idea: what is being organized, checked, connected, created, translated, compared, or completed?
3. Sketch a symbol from that action or object relationship. Avoid symbols that could describe almost any AI product.
4. Build the mark with clean geometry and a square viewBox. It must remain recognizable at small sizes and in monochrome.
5. Produce light and dark variants from the same geometry. Do not make two unrelated logos.
6. Check contrast on both backgrounds. Do not rely on subtle low-contrast strokes to carry meaning.
7. Keep the SVG self-contained. Avoid external fonts, linked images, remote resources, scripts, filters that add fragility, or animation unless explicitly required and supported.
8. Use text in the logo only when the wordmark is essential and can be represented safely without depending on an unavailable font. A symbol-first mark is usually more portable for Plugin surfaces.
9. Create a simplified composer/icon asset when the full mark loses clarity at small size.
10. Validate every declared logo/icon path with the Autopilot validator before packaging.

## Creative quality gate

Reject or redraw a concept when it uses generic AI shorthand without a product-specific reason, including:

- robot heads
- brains or neural-network dots
- sparkle-only marks
- chat bubbles with no connection to the Plugin's actual job
- arbitrary circuit traces
- decorative gradients that carry no meaning
- tiny detail that disappears in a 32px icon
- a stock-looking monogram that could belong to an unrelated SaaS product

A good Plugin logo should be explainable in one sentence: "This shape represents X because the Plugin helps users do Y."

## SVG technical gate

Require:

- a square numeric `viewBox`
- valid XML/SVG markup
- no embedded secrets or remote URLs
- no absolute local file references
- deterministic source committed with the Plugin
- light and dark variants sharing the same core geometry

## Handoff

Pass the exact asset paths and brand rationale to `plugin-directory-listing-writer` and `submission-pack-builder`. Do not claim a dark-mode manifest field exists unless the current OpenAI documentation explicitly supports one; the dark SVG remains part of the packaged brand kit even when only one logo path is declared in the manifest.
