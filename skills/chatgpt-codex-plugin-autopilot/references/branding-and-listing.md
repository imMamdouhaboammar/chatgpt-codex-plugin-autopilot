# Branding and Directory Listing Contract

Checked against official OpenAI Plugin documentation on 2026-08-22. Re-check before public submission because portal fields and limits can change.

Official references used for this baseline:

- `https://developers.openai.com/plugins/build/plugins`
- `https://developers.openai.com/plugins/deploy/submission`
- `https://developers.openai.com/plugins/guides/optimize-metadata`

## Why this is a separate gate

A valid Plugin package can still be poorly represented in the Plugin Directory. Autopilot therefore treats branding and listing quality as a first-class conversion stage between product architecture and final submission evidence.

## Brand pack

Every public Plugin produced through the conversion workflow should leave behind a deliberate SVG identity pack:

```text
assets/
  logo-light.svg
  logo-dark.svg
  <composer-icon>.svg
```

The light and dark logos must share one core geometry. They are variants for different presentation contexts, not separate brand concepts.

The manifest should reference only fields supported by the current OpenAI contract. Keep extra dark/light variants as package assets when the manifest exposes only one logo path. Never invent an undocumented `darkLogo` field just to reference the second file.

The brand concept should come from the Plugin's actual job. Reject generic AI marks that could be attached to unrelated products.

## Listing pack

The current OpenAI public submission flow asks publishers to prepare listing details including plugin name, short description, long description, logo, category, website, support URL, privacy policy URL, and terms URL. It also requires a verified developer or business identity.

The repository-level directory pack should preserve at least:

```json
{
  "name": "Customer-facing name",
  "subtitle": "Short plain-language function",
  "description": "Longer factual description",
  "category": "Current supported category",
  "developerName": "Verified publisher identity",
  "websiteURL": "https://...",
  "customerSupportURL": "https://...",
  "privacyPolicyURL": "https://...",
  "termsOfServiceURL": "https://...",
  "version": "1.2.3",
  "packageName": "plugin-package-name",
  "capabilities": [],
  "starterPrompts": []
}
```

This JSON shape is an Autopilot evidence format, not an OpenAI upload schema.

## Metadata quality

Metadata influences both people and model routing. Use a golden prompt set to test direct, indirect, and negative prompts. Optimize for useful precision and recall, not keyword density.

When a field has a stricter portal limit than the manifest validator, obey the portal limit. In particular, if the current UI specifies a 30-character Subtitle, enforce 30 characters during listing preparation.

## Publisher truth

Do not infer the verified developer identity. Package authorship, repository ownership, and a verified OpenAI publisher identity are different facts. If the verified identity is unavailable, mark the listing as incomplete.

Do not invent support, privacy, terms, or website URLs. They must be public, accurate, and consistent with the Plugin's real behavior and data handling.

## Reviewer material

As of this baseline, OpenAI requires at least five positive test cases and three negative test cases for submission. Positive cases specify expected workflow behavior and result shape. Negative cases specify the expected refusal, clarification, or fallback and why the Plugin should not complete the request.

Starter prompts and reviewer tests serve different purposes. Starter prompts teach users useful workflows; reviewer tests prove intended and non-intended behavior.

## Status boundary

Use these separately:

- `brand_ready`
- `listing_ready`
- `submission_ready`
- `submitted`
- `approved`
- `published`

A creative logo and complete listing do not imply package validity or OpenAI approval.
