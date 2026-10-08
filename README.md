# Direct Subdeck Badge

Direct Subdeck Badge is an Anki Desktop add-on that shows a small badge during review with the direct subdeck of the current card, relative to the deck selected for study.

It provides lightweight context while studying a large parent deck without exposing the card's full nested deck path.

## How the badge is chosen

Given this deck tree:

```text
Animals
  Mammals
    Cats
    Dogs
  Reptiles
```

When studying `Animals`:

| Card deck | Badge |
| --- | --- |
| `Animals::Mammals::Cats` | `Mammals` |
| `Animals::Mammals::Dogs` | `Mammals` |
| `Animals::Reptiles` | `Reptiles` |
| `Animals` | No badge |

When studying `Animals::Mammals`, cards from `Cats` and `Dogs` show `Cats` and `Dogs`, respectively. The badge always represents the direct child of the selected study deck, not the deepest deck in the path.

## Features

- Shows a compact badge near the bottom-right of the reviewer window.
- Remains visible on both the question and answer sides.
- Opens a color picker when the badge is clicked.
- Saves colors by full deck path, so identically named subdecks in different trees can have different colors.
- Provides a `Hide` button to disable badges for the selected study deck.
- Leaves a small `Show` button available when badges are disabled.
- Saves color and visibility choices in Anki's add-on configuration.
- Does not modify cards, notes, decks, scheduling, or review history.

## Installation

1. Build `direct-subdeck-badge.ankiaddon` from source as described below, or download it from the repository's Releases page when a packaged release is available.
2. In Anki Desktop, select **Tools > Add-ons**.
3. Click **Install from file...** and select the `.ankiaddon` file.
4. Restart Anki when prompted.

## Use

Study a deck that contains subdecks. When the current card belongs to a nested deck, the badge and a `Hide` button appear near the bottom-right of the reviewer window.

- Click the badge to choose its color. The choice is saved for that direct child deck.
- Click `Hide` to disable badges for the currently selected study deck.
- Click `Show` to re-enable them.

Cards directly inside the selected study deck do not show a badge.

## Configuration

Normal use does not require editing JSON. Advanced users can open **Tools > Add-ons > Direct Subdeck Badge > Config**.

| Key | Purpose |
| --- | --- |
| `default_background_color` | Badge color when no custom color has been selected |
| `deck_colors` | Custom colors keyed by full direct-child deck path |
| `disabled_selected_decks` | Selected study decks for which badges are hidden |
| `badge_bottom` | Distance from the bottom of the Anki window, in pixels |
| `badge_right` | Distance from the right side of the Anki window, in pixels |
| `button_gap` | Gap between the badge and Hide/Show button, in pixels |
| `badge_max_width` | Maximum badge width, in pixels |

`config_version` is used internally for configuration migration.

## Build from source

Python 3.9 or newer is sufficient for the packaging script; Anki is not required to build the archive.

```shell
python package.py
```

The command creates `dist/direct-subdeck-badge.ankiaddon` and checks that the archive contains only the intended files at its root. Do not zip the repository's parent directory: Anki requires `__init__.py` and the other add-on files at the root of the archive.

## Limitations and compatibility

- Anki Desktop only. AnkiMobile and AnkiDroid do not load desktop add-ons.
- Widget positioning may vary with Anki version, theme, window size, and display scaling. Position offsets can be adjusted in the config.
- Tested locally on Anki 26.9.2 for Windows. Other Anki versions have not yet been verified.

## Repository files

- `__init__.py`: add-on implementation
- `config.json`: default configuration
- `config.md`: configuration help displayed by Anki
- `manifest.json`: metadata used when installing outside AnkiWeb
- `package.py`: reproducible `.ankiaddon` builder and archive validator
- `CHANGELOG.md`: release history
- `LICENSE`: MIT license

## Contributing

Bug reports and focused pull requests are welcome. Please include the Anki version, operating system, and steps needed to reproduce the issue.

## License

Direct Subdeck Badge is available under the [MIT License](LICENSE).
