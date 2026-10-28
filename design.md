# GH Pain Intel interface

Hallmark v2.0.0. App scope. Preserve the current sidebar, analysis pipeline and four result tabs.

- Audience: developers investigating open-source community needs. The primary action is to configure repositories and analyze their Issues.
- Keep: project identity, all input keys/defaults, model providers, source URLs, validation, progress, evidence, analysis calculations and Markdown report.
- Palette: existing dark blue-neutral background and blue action accent, solid surfaces, green/orange/red reserved for actual status. All CSS colors and fonts live in src/theme.css :root.
- Composition: compact identity and real Trending summary; analysis action; repository index; result summary, evidence tabs and report. No marketing sections or decorative status lights.
- Type: system UI, readable Chinese fallback; tabular figures; untracked labels. Base 16px, secondary 13–14px, section 19px, title 30px.
- Components: 44px button targets, restrained 10px corners, visible keyboard focus. Repository and insight rows use rules instead of nested cards.
- States: keep existing unconfigured, waiting, loading, partial failure, empty and complete states. Do not draw controls for unsupported cancellation or recovery.
- Responsive: capped 1280px desktop container, single-column title/summary below 900px, mobile 16px gutters. Add-to-analysis remains available on phones.
- Motion: no decorative animation. Respect reduced motion for framework controls.
- Rollback: baseline commit fbdd634bddfba98509873f5b4bf827a34c2bc184; redesign is isolated on hallmark-redesign. No deployment is part of this local change.
- Source: src/theme.css is loaded into the existing Streamlit style injection by src/ui.py, so the same system applies to sidebar, result tabs, alerts and report.
