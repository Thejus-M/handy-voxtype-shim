#!/usr/bin/python3 -I
"""Exit 0 if the focused window has a focused text field, else exit 1.

Terminals always count as typeable. Other apps are asked over AT-SPI
(accessibility) for a focused object with the EDITABLE state.
Uses system Python because it needs PyGObject (python-gobject).
"""
import json
import subprocess
import sys

TERMINALS = {
    "foot", "footclient", "kitty", "alacritty", "com.mitchellh.ghostty",
    "org.wezfurlong.wezterm", "xterm", "konsole", "org.gnome.console",
}


def active_window():
    out = subprocess.run(["hyprctl", "activewindow", "-j"], capture_output=True, text=True).stdout
    try:
        return json.loads(out) or {}
    except json.JSONDecodeError:
        return {}


def focused_editable(app):
    from gi.repository import Atspi

    states = Atspi.StateSet.new([Atspi.StateType.FOCUSED])
    rule = Atspi.MatchRule.new(states, Atspi.CollectionMatchType.ALL,
                               None, Atspi.CollectionMatchType.ALL,
                               [], Atspi.CollectionMatchType.ALL,
                               [], Atspi.CollectionMatchType.ALL, False)
    try:
        coll = app.get_collection_iface()
        hits = coll.get_matches(rule, Atspi.CollectionSortOrder.CANONICAL, 5, True) if coll else []
    except Exception:
        hits = []
    for obj in hits:
        try:
            if obj.get_state_set().contains(Atspi.StateType.EDITABLE):
                return True
        except Exception:
            continue
    return False


def main():
    win = active_window()
    if not win.get("address"):
        return 1
    if str(win.get("class", "")).lower() in TERMINALS:
        return 0

    import gi
    gi.require_version("Atspi", "2.0")
    from gi.repository import Atspi

    pid = win.get("pid")
    desktop = Atspi.get_desktop(0)
    for i in range(desktop.get_child_count()):
        app = desktop.get_child_at_index(i)
        try:
            if app is None or app.get_process_id() != pid:
                continue
        except Exception:
            continue
        if focused_editable(app):
            return 0
    return 1


if __name__ == "__main__":
    sys.exit(main())
