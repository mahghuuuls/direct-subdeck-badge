"""
Direct Subdeck Badge

Anki Desktop add-on that shows a small badge in the reviewer with the
current card's direct child deck under the deck selected for study.

Example:
    Selected deck: Animals
    Card deck:     Animals::Mammals::Cats
    Badge shown:   Mammals

The badge can be clicked to choose a color for that direct child deck.
A Hide/Show button disables or enables badges for the currently selected
study deck, and the setting is saved in the add-on config.
"""

from __future__ import annotations

from typing import Any, Dict, Optional, Tuple

from aqt import gui_hooks, mw
from aqt.qt import (
    QColor,
    QColorDialog,
    QEvent,
    QObject,
    QPushButton,
    QTimer,
    Qt,
)


ADDON_NAME = "Direct Subdeck Badge"
CONFIG_VERSION = 5

DEFAULT_CONFIG: Dict[str, Any] = {
    "config_version": CONFIG_VERSION,
    "default_background_color": "#202020",
    "deck_colors": {},
    "disabled_selected_decks": [],
    "badge_bottom": 72,
    "badge_right": 14,
    "button_gap": 6,
    "badge_max_width": 240,
}


def _pointing_hand_cursor() -> Any:
    """Return the pointing-hand cursor value across Qt versions."""
    try:
        return Qt.CursorShape.PointingHandCursor
    except AttributeError:
        return Qt.PointingHandCursor


def _shorten_label(text: str, max_chars: int = 34) -> str:
    """Keep very long deck names from making an oversized badge."""
    if len(text) <= max_chars:
        return text
    return text[: max_chars - 1] + "…"


def _readable_text_color(background_hex: str) -> str:
    """Choose black or white text based on the background color."""
    color = QColor(background_hex)
    if not color.isValid():
        return "#ffffff"

    # Perceptual luminance approximation. Values above this are usually
    # easier to read with black text; darker backgrounds use white text.
    luminance = 0.2126 * color.red() + 0.7152 * color.green() + 0.0722 * color.blue()
    return "#000000" if luminance >= 150 else "#ffffff"


class DirectSubdeckBadge(QObject):
    def __init__(self) -> None:
        super().__init__(mw)

        self.config: Dict[str, Any] = self._load_config()
        self.current_selected_deck: Optional[str] = None
        self.current_child_deck_path: Optional[str] = None
        self.current_child_label: Optional[str] = None

        self.badge_button = QPushButton(mw)
        self.badge_button.setObjectName("DirectSubdeckBadgeButton")
        self.badge_button.setCursor(_pointing_hand_cursor())
        self.badge_button.setToolTip("Click to choose a color for this deck badge")
        self.badge_button.clicked.connect(self._choose_color_for_current_badge)
        self.badge_button.hide()

        self.toggle_button = QPushButton(mw)
        self.toggle_button.setObjectName("DirectSubdeckBadgeToggleButton")
        self.toggle_button.setCursor(_pointing_hand_cursor())
        self.toggle_button.setToolTip("Hide or show direct subdeck badges for the selected study deck")
        self.toggle_button.clicked.connect(self._toggle_selected_deck)
        self.toggle_button.hide()

        self._style_toggle_button()

        mw.installEventFilter(self)

        gui_hooks.reviewer_did_show_question.append(self._schedule_update)
        gui_hooks.reviewer_did_show_answer.append(self._schedule_update)
        gui_hooks.state_did_change.append(self._schedule_update)
        gui_hooks.deck_browser_will_show.append(self._schedule_update)

        self._schedule_update()

    # ------------------------------------------------------------------
    # Config
    # ------------------------------------------------------------------

    def _load_config(self) -> Dict[str, Any]:
        raw = mw.addonManager.getConfig(__name__) or {}
        config = dict(DEFAULT_CONFIG)
        config.update(raw)

        if not isinstance(config.get("deck_colors"), dict):
            config["deck_colors"] = {}
        if not isinstance(config.get("disabled_selected_decks"), list):
            config["disabled_selected_decks"] = []

        # Lightweight migration for older versions that used a top position.
        # Once the bottom-right layout exists, old top coordinates are ignored.
        if config.get("config_version", 0) < CONFIG_VERSION:
            config["config_version"] = CONFIG_VERSION
            config.setdefault("badge_bottom", DEFAULT_CONFIG["badge_bottom"])
            config.setdefault("badge_right", DEFAULT_CONFIG["badge_right"])
            config.setdefault("button_gap", DEFAULT_CONFIG["button_gap"])
            config.setdefault("badge_max_width", DEFAULT_CONFIG["badge_max_width"])
            self._save_config(config)

        return config

    def _save_config(self, config: Optional[Dict[str, Any]] = None) -> None:
        if config is None:
            config = self.config
        mw.addonManager.writeConfig(__name__, config)

    # ------------------------------------------------------------------
    # Deck logic
    # ------------------------------------------------------------------

    def _selected_deck_name(self) -> Optional[str]:
        """Return the deck currently selected for study."""
        try:
            selected_did = mw.col.decks.selected()
            deck = mw.col.decks.get(selected_did)
            if deck:
                return deck.get("name")
        except Exception:
            pass

        try:
            deck = mw.col.decks.current()
            if deck:
                return deck.get("name")
        except Exception:
            pass

        return None

    def _card_deck_name(self) -> Optional[str]:
        """Return the full deck path for the current reviewer card."""
        reviewer = getattr(mw, "reviewer", None)
        card = getattr(reviewer, "card", None)
        if card is None:
            return None

        try:
            deck = mw.col.decks.get(card.did)
            if deck:
                return deck.get("name")
        except Exception:
            pass

        return None

    def _direct_child_for_selected_deck(self) -> Tuple[Optional[str], Optional[str], Optional[str]]:
        """
        Return selected deck, full child deck path, and child label.

        If selected deck is Animals and card deck is Animals::Mammals::Cats,
        the result is:
            selected = Animals
            child path = Animals::Mammals
            label = Mammals

        If the card is directly inside the selected deck, no label is returned.
        """
        selected = self._selected_deck_name()
        card_deck = self._card_deck_name()

        if not selected or not card_deck:
            return selected, None, None

        if card_deck == selected:
            return selected, None, None

        prefix = selected + "::"
        if not card_deck.startswith(prefix):
            return selected, None, None

        relative = card_deck[len(prefix) :]
        if not relative:
            return selected, None, None

        child_label = relative.split("::", 1)[0]
        child_path = prefix + child_label
        return selected, child_path, child_label

    # ------------------------------------------------------------------
    # UI update
    # ------------------------------------------------------------------

    def _schedule_update(self, *args: Any) -> None:
        QTimer.singleShot(0, self._update_ui)

    def _update_ui(self) -> None:
        if mw is None or getattr(mw, "state", None) != "review":
            self._hide_all()
            return

        selected, child_path, child_label = self._direct_child_for_selected_deck()
        self.current_selected_deck = selected
        self.current_child_deck_path = child_path
        self.current_child_label = child_label

        if not selected:
            self._hide_all()
            return

        disabled = self._selected_deck_is_disabled(selected)

        if disabled:
            self.badge_button.hide()
            self.toggle_button.setText("Show")
            self.toggle_button.show()
            self._position_widgets(show_badge=False)
            return

        if not child_path or not child_label:
            self._hide_all()
            return

        self.badge_button.setText(_shorten_label(child_label))
        self._style_badge_button(child_path)
        self.badge_button.show()

        self.toggle_button.setText("Hide")
        self.toggle_button.show()

        self._position_widgets(show_badge=True)
        self.badge_button.raise_()
        self.toggle_button.raise_()

    def _hide_all(self) -> None:
        self.badge_button.hide()
        self.toggle_button.hide()

    def _selected_deck_is_disabled(self, selected_deck: str) -> bool:
        disabled = self.config.get("disabled_selected_decks", [])
        return selected_deck in disabled

    # ------------------------------------------------------------------
    # Styling and positioning
    # ------------------------------------------------------------------

    def _style_badge_button(self, child_path: str) -> None:
        colors = self.config.get("deck_colors", {})
        background = colors.get(child_path, self.config.get("default_background_color", "#202020"))
        text_color = _readable_text_color(background)

        self.badge_button.setStyleSheet(
            f"""
            QPushButton#DirectSubdeckBadgeButton {{
                background-color: {background};
                color: {text_color};
                border: none;
                border-radius: 7px;
                padding: 4px 10px;
                font-weight: 600;
            }}
            QPushButton#DirectSubdeckBadgeButton:hover {{
                border: 1px solid rgba(255, 255, 255, 0.45);
            }}
            """
        )

    def _style_toggle_button(self) -> None:
        self.toggle_button.setStyleSheet(
            """
            QPushButton#DirectSubdeckBadgeToggleButton {
                background-color: #eeeeee;
                color: #222222;
                border: 1px solid #b8b8b8;
                border-radius: 7px;
                padding: 4px 8px;
                font-weight: 600;
            }
            QPushButton#DirectSubdeckBadgeToggleButton:hover {
                background-color: #e0e0e0;
            }
            """
        )

    def _position_widgets(self, show_badge: bool) -> None:
        right = int(self.config.get("badge_right", 14))
        bottom = int(self.config.get("badge_bottom", 72))
        gap = int(self.config.get("button_gap", 6))
        max_badge_width = int(self.config.get("badge_max_width", 240))

        window_width = mw.width()
        window_height = mw.height()

        self.toggle_button.adjustSize()
        toggle_width = max(self.toggle_button.sizeHint().width(), 52)
        toggle_height = max(self.toggle_button.sizeHint().height(), 28)
        y = max(0, window_height - bottom - toggle_height)
        toggle_x = max(0, window_width - right - toggle_width)
        self.toggle_button.setGeometry(toggle_x, y, toggle_width, toggle_height)

        if show_badge:
            self.badge_button.adjustSize()
            badge_width = min(max(self.badge_button.sizeHint().width(), 80), max_badge_width)
            badge_height = toggle_height
            badge_x = max(0, toggle_x - gap - badge_width)
            self.badge_button.setGeometry(badge_x, y, badge_width, badge_height)

    def eventFilter(self, obj: QObject, event: QEvent) -> bool:  # noqa: N802 - Qt naming convention
        if obj is mw:
            event_type = event.type()
            try:
                resize_type = QEvent.Type.Resize
                move_type = QEvent.Type.Move
            except AttributeError:
                resize_type = QEvent.Resize
                move_type = QEvent.Move

            if event_type in (resize_type, move_type):
                self._schedule_update()

        return False

    # ------------------------------------------------------------------
    # User actions
    # ------------------------------------------------------------------

    def _choose_color_for_current_badge(self) -> None:
        if not self.current_child_deck_path:
            return

        colors = self.config.setdefault("deck_colors", {})
        current_color = colors.get(
            self.current_child_deck_path,
            self.config.get("default_background_color", "#202020"),
        )

        chosen = QColorDialog.getColor(
            QColor(current_color),
            mw,
            f"Choose badge color for {self.current_child_label or self.current_child_deck_path}",
        )

        if not chosen.isValid():
            return

        colors[self.current_child_deck_path] = chosen.name()
        self._save_config()
        self._update_ui()

    def _toggle_selected_deck(self) -> None:
        selected = self.current_selected_deck or self._selected_deck_name()
        if not selected:
            return

        disabled = self.config.setdefault("disabled_selected_decks", [])

        if selected in disabled:
            disabled.remove(selected)
        else:
            disabled.append(selected)

        self._save_config()
        self._update_ui()


_badge: Optional[DirectSubdeckBadge] = None


def _initialize_addon() -> None:
    global _badge
    if _badge is None:
        _badge = DirectSubdeckBadge()


# Add-ons are usually loaded before the profile is open, so this is the safest
# initialization point. The try block also covers development reloads.
gui_hooks.profile_did_open.append(_initialize_addon)

try:
    if mw is not None and getattr(mw, "col", None) is not None:
        _initialize_addon()
except Exception:
    pass
