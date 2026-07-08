# QML scrub field (Houdini-style drag control) — design

## Goal

Replace `src/ncca/ngl/qml/DecimalSpinBox.qml`'s internals with a Houdini-style
drag/scrub float field: left-drag to scrub the value, left-click (no drag) to
type an exact value, and middle-click-press-drag-release to pick the drag
increment from a vertical ladder popup (100/10/1/.1/.01/.001/.0001).

## Scope

Drop-in replacement of `DecimalSpinBox.qml` only. Its public interface is
unchanged (`realValue`, `from_`, `to_`, `stepSize_`, `decimals`), so no other
file needs to change: `Vec2Widget.qml`/`Vec3Widget.qml`/`Vec4Widget.qml`,
`RGBColourWidget.qml`/`RGBAColourWidget.qml`, `MatrixGridWidget.qml`, and
`Mat3Widget.qml`/`Mat4Widget.qml`'s angle field all keep working unmodified.

Out of scope: reskinning to match Houdini's dark theme (kept consistent with
this project's existing plain `QtQuick.Controls` look); automated interaction
tests (mouse-drag gestures aren't practically simulatable in the current
pytest/`QQmlApplicationEngine` QML test setup — verified by manual
smoke-testing plus the existing `test_qml_views.py` load-without-error check,
consistent with how the rest of the QML layer is tested).

## Interaction model

- **Left-click + drag** (past a small pixel threshold, e.g. 3px, so a plain
  click doesn't register as a drag): scrubs the value. Track `dragStartX` and
  `dragStartValue` on press; on each mouse move, compute
  `realValue = clamp(dragStartValue + Math.round((mouseX - dragStartX) / pixelsPerStep) * currentStep, from_, to_)`,
  where `pixelsPerStep` is a small constant (e.g. 4px) and `currentStep`
  starts at `stepSize_` and can be overridden per-instance by the ladder
  (below). Using `Math.round(...)` of the *total* delta from drag-start
  (not incremental per-move-event deltas) avoids compounding rounding error
  during a single drag gesture.
- **Left-click without drag**: on release, if the drag threshold was never
  exceeded, put the field into text-edit mode — a `TextInput` gets focus with
  its text selected, showing the raw (unrounded-for-display) number. `Enter`
  or focus-out commits: parse as float, clamp to `[from_, to_]`, round to
  `decimals`, assign to `realValue`. `Escape` cancels, reverting the
  displayed text to the current `realValue` without committing.
- **Middle-click + hold**: opens a vertical `Popup` anchored at the cursor
  listing the fixed increment tiers `[100, 10, 1, 0.1, 0.01, 0.001, 0.0001]`.
  While the button is held, vertical mouse movement highlights whichever
  entry the cursor is nearest to; releasing the middle button commits the
  highlighted entry into `currentStep` (an internal property, not written
  back to the external `stepSize_` — the ladder selection is a per-instance
  runtime preference, `stepSize_` remains the field's design-time default)
  and closes the popup. This is a **press-drag-release** gesture matching
  the reference image, not a click-to-open static menu.

## Visual design

- Idle: a flat bordered `Rectangle` (no spin-up/down buttons — those don't
  fit the drag-scrub metaphor) showing `Text` formatted to `decimals` places.
- Hover: `Qt.SizeHorCursor` to hint the field is horizontally draggable, plus
  a subtle border-color change.
- Dragging: border/background highlight distinct from hover, so the user
  gets feedback that a scrub is in progress vs. about to click-to-type.
- Ladder popup: a `Popup` with a `ColumnLayout` of 7 `Text`/`Rectangle` rows
  (100 at top through .0001 at bottom, matching the reference image's
  ordering), the currently-hovered-during-drag row highlighted with an accent
  background (e.g. `"orange"`/palette highlight colour), rest plain.

## Non-goals

- No change to any file other than `DecimalSpinBox.qml`.
- No Houdini-dark-theme reskin.
- No automated interaction/drag tests — manual + existing load-smoke-test
  coverage only, consistent with the rest of the QML layer's testing
  approach.
