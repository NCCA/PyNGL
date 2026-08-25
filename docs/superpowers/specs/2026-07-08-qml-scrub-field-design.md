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
- **Middle-click + hold (or right-click + hold)**: opens a vertical `Popup`
  listing the fixed increment tiers `[100, 10, 1, 0.1, 0.01, 0.001, 0.0001]`,
  anchored **to the left of the field** (`x = -popup.width - gap`, always
  negative relative to the field regardless of where within it the press
  landed), vertically positioned so the row matching the field's current
  drag increment aligns with the press point. This is a
  **press-drag-release** gesture matching the reference image, not a
  click-to-open static menu.

  **Amended (live per-row scrubbing):** while the button is held, moving the
  mouse **vertically** selects which row (magnitude) is active — highlighted
  in the popup — and moving the mouse **horizontally** live-scrubs the
  field's actual value using that row's magnitude as the per-pixel step,
  visible in the field immediately (not just after release). Switching rows
  re-anchors the scrub's reference value and reference x-position to
  wherever the value currently is, so changing magnitude mid-gesture never
  causes a value jump — only subsequent horizontal movement at the new
  magnitude does. Releasing the button commits the row's magnitude into
  `currentStep` for future left-drags and closes the popup; the value stays
  wherever the live scrub left it (no separate "confirm" step). This matches
  Houdini's actual ladder behaviour more closely than the original design's
  "pick a sensitivity, then drag separately afterward" flow.

  **Amended (trigger):** right-click was added as an equal trigger alongside
  middle-click, because a laptop trackpad (particularly macOS) generally has
  no native middle-click at all — a two-finger tap/click is the trackpad's
  native secondary-click gesture and is delivered to Qt as `RightButton`,
  not `MiddleButton`. Without this, trackpad users had no way to open the
  ladder at all.

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
