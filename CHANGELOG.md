# Changelog

All notable changes to this project will be documented in this file.

## 1.2.1 - 2026-10-28

- Hide the Depth control when deck badges are hidden; Show restores it alongside the badges.

## 1.2.0 - 2026-10-28

- Display each subdeck level as its own clickable badge, with colors saved by full deck path.
- Wrap badges onto additional rows when necessary to fit the window.

## 1.1.1 - 2026-10-28

- Fix startup on Anki 26.09.2 by removing the unavailable `deck_browser_will_show` hook. The state-change hook already updates visibility when leaving review.

## 1.1.0 - 2026-10-28

- Add an independent bottom-left New indicator for cards classified as new by Anki.
- Add a reviewer Depth control with preferences saved per selected study deck.
- Preserve existing direct-child colors and default one-level display.

## 1.0.0 - 2026-10-08

- Initial public source release.
- Show the direct child deck of the current card relative to the selected study deck.
- Support per-deck badge colors through a color picker.
- Support persistent Hide/Show state per selected study deck.
