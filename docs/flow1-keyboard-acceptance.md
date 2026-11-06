# Flow 1 keyboard-only acceptance

Status: **not yet executed**. Use this script to verify NFR-004 on Chrome or Edge without a mouse. The current workspace has no frontend E2E runner, and the desktop browser automation host was unavailable during this audit.

## Preconditions

- Start the Compose stack and open `http://localhost:3001/`.
- Keep AI and POS fail toggles off for the first run.
- Use the sample `120 m timber 45x95 C24` so the flow can reach Confirm without a substitution decision.

## Keyboard path

1. Reload the page, use `Tab` / `Shift+Tab` to reach the material-list textarea, and confirm the focus indicator is visible.
2. Type the sample list and press `F9` to read it. The browser should open the new session.
3. Press `F9` to Analyze. Confirm the result announces the line count and selected row; use `Tab` and `Shift+Tab` to move through the review controls.
4. If a line needs a decision, press `F6` to move to the next issue, focus the line with `Tab`, press `Enter` to open it, complete its native inputs/buttons with `Tab` and `Enter`, and press `Escape` to close the line panel.
5. Use `F7` to return to order-level controls, then `F9` to Confirm. Verify the result is announced and the order is locked.
6. Start a second list, enable the POS fail toggle from the keyboard, repeat the flow, and verify the locked result exposes a focusable CSV download link. Reset the POS toggle after the run.

## Pass criteria

- Every action above is possible without pointer input; focus remains visible and moves in a predictable order.
- No keyboard trap; `Enter`, arrow keys on line rows, `Escape`, and documented F-key shortcuts work.
- Blocker messages and completion state are announced; disabled Confirm has an accessible disabled state.
- The POS-failure path exposes a keyboard-focusable CSV link and the fail toggle can be reset without a mouse.

Record browser/version, date, result, and any failed step here after execution.
