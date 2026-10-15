"""Visual tokens shared by the Kivy implementation of the Qyro demos."""


THEMES = {
    "light": {
        "window": (0.96, 0.97, 0.99, 1),
        "surface": (1, 1, 1, 1),
        "surface_alt": (0.93, 0.95, 0.98, 1),
        "text": (0.10, 0.12, 0.18, 1),
        "muted": (0.33, 0.38, 0.48, 1),
        "accent": (0.92, 0.35, 0.05, 1),
        "accent_text": (1, 1, 1, 1),
        "input": (0.98, 0.98, 1, 1),
    },
    "dark": {
        "window": (0.05, 0.07, 0.11, 1),
        "surface": (0.10, 0.13, 0.19, 1),
        "surface_alt": (0.15, 0.18, 0.25, 1),
        "text": (0.94, 0.96, 1, 1),
        "muted": (0.68, 0.73, 0.83, 1),
        "accent": (0.92, 0.35, 0.05, 1),
        "accent_text": (1, 1, 1, 1),
        "input": (0.13, 0.16, 0.23, 1),
    },
}


def tokens(name):
    """Return the requested palette, falling back to the light theme."""
    return THEMES.get(name, THEMES["light"])
