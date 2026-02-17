# Frontend Organization Notes

## Current Structure

- `static/js/api-client.js`
  - Centralized JSON request helpers (`getJson`, `postJson`, `postNoBody`)
  - Returns `{ response, data }` to preserve status and payload handling

- `static/js/ui-feedback.js`
  - Toast rendering and app-styled confirmation modal helper
  - Replaces blocking browser dialogs for a consistent UX flow

- `static/js/bigboard-controller.js`
  - Owns Big Board stateful interactions (load/search/add/remove/reorder/autosort)
  - Encapsulates drag-and-drop behavior and add-player dialog orchestration
  - Exposes a narrow controller API used by `app.js` wrappers

- `static/js/app.js`
  - App-level orchestration and DOM wiring
  - Routes API calls through `requestGetJson`, `requestPostJson`, and `requestPostNoBody`
  - Delegates Big Board workflows to `bigboard-controller.js`

## Maintainability Conventions

- Prefer request helpers over direct `fetch` for JSON endpoints.
- Keep `showToast` as the user-visible feedback default for non-fatal errors.
- Use `UIFeedback.confirmAction(...)` for confirmation flows.
- Reserve direct `fetch` only for non-JSON responses (for example file export text/blob).

## Suggested Next Split (Optional)

If you want to continue modularizing with low risk, extract these next:

1. `player-report-controller.js`
   - profile modal open/save, notes/grade/scout updates
2. `settings-controller.js`
   - board imports, weights, app tools actions

This keeps behavior unchanged while making each area easier to reason about and test.
