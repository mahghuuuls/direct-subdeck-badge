"""Behavior checks without requiring a running Anki/Qt application."""

import importlib.util
from pathlib import Path
import sys
from types import ModuleType, SimpleNamespace
import unittest
from unittest.mock import MagicMock, patch


aqt = ModuleType("aqt")
aqt.mw = None
aqt.gui_hooks = SimpleNamespace(profile_did_open=[])
qt = ModuleType("aqt.qt")
for name in ("QColor", "QColorDialog", "QEvent", "QObject", "QPushButton",
             "QTimer", "Qt", "QInputDialog", "QLabel"):
    setattr(qt, name, type(name, (), {}))
spec = importlib.util.spec_from_file_location("badge_under_test", Path(__file__).resolve().parents[1] / "__init__.py")
addon = importlib.util.module_from_spec(spec)
with patch.dict(sys.modules, {"aqt": aqt, "aqt.qt": qt}):
    spec.loader.exec_module(addon)


class BadgeTests(unittest.TestCase):
    def test_initialization_without_deck_browser_hook(self):
        hooks = SimpleNamespace(
            reviewer_did_show_question=[], reviewer_did_show_answer=[],
            state_did_change=[], profile_did_open=[],
        )
        with patch.object(addon, "gui_hooks", hooks), \
             patch.object(addon, "mw", MagicMock()), \
             patch.object(addon.QObject, "__init__", lambda self, *args: None), \
             patch.object(addon, "QPushButton", MagicMock()), \
             patch.object(addon, "QLabel", MagicMock()), \
             patch.object(addon, "_pointing_hand_cursor", return_value=0), \
             patch.object(addon.DirectSubdeckBadge, "_load_config", return_value={}), \
             patch.object(addon.DirectSubdeckBadge, "_schedule_update"):
            badge = addon.DirectSubdeckBadge()
            self.assertIn(badge._schedule_update, hooks.state_did_change)
            self.assertIn(badge._schedule_update, hooks.reviewer_did_show_question)
            self.assertIn(badge._schedule_update, hooks.reviewer_did_show_answer)

    def setUp(self):
        self.badge = addon.DirectSubdeckBadge.__new__(addon.DirectSubdeckBadge)
        self.badge.config = {"selected_deck_depths": {}, "disabled_selected_decks": []}
        self.badge.deck_badges = []
        self.badge.visible_deck_badges = []
        self.badge._selected_deck_name = lambda: "Animals"
        self.badge._card_deck_name = lambda: "Animals::Mammals::Cats"

    def test_depth_and_color_identity(self):
        self.assertEqual(self.badge._direct_child_for_selected_deck(),
                         ("Animals", "Animals::Mammals", "Mammals"))
        self.badge.config["selected_deck_depths"]["Animals"] = 2
        self.assertEqual(self.badge._direct_child_for_selected_deck(),
                         ("Animals", "Animals::Mammals", "Mammals::Cats"))
        self.badge.config["selected_deck_depths"]["Animals"] = 100
        self.assertEqual(self.badge._direct_child_for_selected_deck()[2], "Mammals::Cats")
        self.assertEqual(self.badge._depth_for_selected_deck("Other"), 1)

    def test_separate_badges_have_distinct_full_paths(self):
        self.assertEqual(self.badge._display_decks("Animals", "Mammals::Cats"),
                         [("Animals::Mammals", "Mammals"),
                          ("Animals::Mammals::Cats", "Cats")])

    def test_color_changes_only_clicked_deck(self):
        self.badge.config["deck_colors"] = {"Animals::Mammals": "#123456"}
        self.badge._save_config = MagicMock()
        self.badge._update_ui = MagicMock()
        chosen = MagicMock()
        chosen.name.return_value = "#abcdef"
        with patch.object(addon, "QColor", MagicMock()), \
             patch.object(addon.QColorDialog, "getColor", return_value=chosen, create=True):
            self.badge._choose_deck_color("Animals::Mammals::Cats", "Cats")
        self.assertEqual(self.badge.config["deck_colors"],
                         {"Animals::Mammals": "#123456", "Animals::Mammals::Cats": "#abcdef"})
        self.badge._save_config.assert_called_once()

    def test_parent_and_unrelated_cards_have_no_deck_label(self):
        for path in ("Animals", "AnimalsOther::Cats", "Other"):
            self.badge._card_deck_name = lambda: path
            self.assertEqual(self.badge._direct_child_for_selected_deck(), ("Animals", None, None))

    def test_new_learning_review_relearning_and_missing_card(self):
        for card_type, expected in ((0, True), (1, False), (2, False), (3, False)):
            with patch.object(addon, "mw", SimpleNamespace(reviewer=SimpleNamespace(card=SimpleNamespace(type=card_type)))):
                self.assertEqual(self.badge._card_is_new(), expected)
        with patch.object(addon, "mw", SimpleNamespace(reviewer=None)):
            self.assertFalse(self.badge._card_is_new())

    def test_depth_choice_is_saved_only_on_accept(self):
        self.badge.current_selected_deck = "Animals"
        self.badge._save_config = MagicMock()
        self.badge._update_ui = MagicMock()
        with patch.object(addon.QInputDialog, "getInt", return_value=(3, True), create=True):
            self.badge._choose_depth()
        self.assertEqual(self.badge.config["selected_deck_depths"], {"Animals": 3})
        self.badge._save_config.assert_called_once()
        with patch.object(addon.QInputDialog, "getInt", return_value=(5, False), create=True):
            self.badge._choose_depth()
        self.assertEqual(self.badge.config["selected_deck_depths"]["Animals"], 3)
        self.badge._save_config.assert_called_once()

    def test_new_indicator_survives_hidden_or_absent_deck_label(self):
        for name in ("badge_button", "toggle_button", "depth_button", "new_badge"):
            setattr(self.badge, name, MagicMock())
        self.badge._position_widgets = MagicMock()
        self.badge.config["disabled_selected_decks"] = ["Animals"]
        window = SimpleNamespace(state="review", reviewer=SimpleNamespace(card=SimpleNamespace(type=0)))
        with patch.object(addon, "mw", window):
            self.badge._update_ui()
            self.badge.new_badge.setVisible.assert_called_with(True)
            self.badge.toggle_button.setText.assert_called_with("Show")
            self.badge.depth_button.setVisible.assert_called_with(False)
            self.badge.config["disabled_selected_decks"] = []
            self.badge._card_deck_name = lambda: "Animals"
            self.badge._update_ui()
            self.badge.new_badge.hide.assert_not_called()
            self.badge.depth_button.setVisible.assert_called_with(True)
            window.reviewer.card.type = 1
            self.badge._update_ui()
            self.badge.new_badge.setVisible.assert_called_with(False)
            window.state = "deckBrowser"
            self.badge._update_ui()
            self.badge.new_badge.hide.assert_called_once()
            self.badge.depth_button.hide.assert_called_once()


if __name__ == "__main__":
    unittest.main()
