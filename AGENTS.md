# Propack UI/UX Guidance

When changing user-facing screens in this project, use the project-local UI/UX skill at:

`C:\Users\Kelly\Desktop\Repo\propack\propack\.agents\skills\ui-ux-pro-max\SKILL.md`

Apply it with Propack's context in mind:

- Propack is an internal operations app for project tracking, engineering codes, notices, customers, scanner/SMB files, and bilingual Chinese/Vietnamese workflows.
- Prefer dense, calm, spreadsheet-like interfaces over landing-page or marketing layouts.
- Prioritize readable tables, stable row heights, clear filters, fast scanning, predictable modals, and bilingual labels that do not clip.
- Use icons for compact actions, but keep text where ambiguity would slow users down.
- Keep colors functional: status, urgency, selection, warning, disabled, and sync states should be easy to distinguish and not rely on color alone.
- Verify UI changes at desktop widths first, then check narrow/mobile widths for clipping, overlap, horizontal scroll, and touch target size.
- Avoid decorative gradients, oversized hero sections, nested cards, and visual effects that make operational data harder to read.

## Browser Verification

For any frontend/UI change, proactively verify it in the live app with Chrome MCP before reporting completion. Do not wait for the user to remind you.

- Open or reuse the Chrome tab for `http://localhost:8001`.
- Refresh once after asset/version changes so the browser loads the latest JS/CSS.
- Exercise the exact workflow that was changed: buttons, context menus, filters, modals, tab switching, realtime/auto-refresh behavior, and scanner-driven updates.
- Inspect the visible DOM/state and browser console when behavior looks wrong; a dark backdrop, blank modal, or unchanged table must be debugged before finishing.
- For context-menu filters, modal detail views, and notification/project interactions, verify from the user-facing UI, not only with `node --check`.
- Summarize the Chrome MCP verification result in the final response.
