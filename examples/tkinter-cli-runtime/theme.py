"""Tkinter visual tokens used by the Qyro demo."""

THEMES = {
    "light": {
        "window": "#F6F7FB", "surface": "#FFFFFF", "surface_alt": "#EAF0F9",
        "text": "#191E2D", "muted": "#53627F", "accent": "#EA580C",
        "accent_text": "#FFFFFF", "input": "#FFFFFF",
    },
    "dark": {
        "window": "#0D111B", "surface": "#18202F", "surface_alt": "#263044",
        "text": "#F1F5F9", "muted": "#B2BDD0", "accent": "#EA580C",
        "accent_text": "#FFFFFF", "input": "#202A3A",
    },
}


def tokens(name):
    return THEMES.get(name, THEMES["light"])
