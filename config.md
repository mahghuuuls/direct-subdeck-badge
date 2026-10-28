# Direct Subdeck Badge configuration

Most settings can be managed during review: click a badge to choose its color, or use **Hide** and **Show** to change visibility for the selected study deck.

- `default_background_color`: fallback badge color as a CSS hex color.
- `deck_colors`: colors keyed by the full path of each displayed deck.
- `disabled_selected_decks`: selected study deck paths for which badges are hidden.
- `selected_deck_depths`: number of subdeck levels displayed, keyed by selected study deck path. Defaults to 1; use the **Depth** button during review to change it.
- `new_badge_left`: distance of the **New** badge from the left edge of the window, in pixels. Its vertical position follows `badge_bottom`.
- `badge_bottom`: distance from the bottom of the Anki window, in pixels.
- `badge_right`: distance from the right side of the Anki window, in pixels.
- `button_gap`: gap between the badge and Hide/Show button, in pixels.
- `badge_max_width`: maximum badge width, in pixels.

Restart Anki after manually changing positioning values.
