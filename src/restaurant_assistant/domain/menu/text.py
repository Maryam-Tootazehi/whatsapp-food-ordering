"""Text normalisation shared by the Menu aggregate and the MenuMatcher."""

import re
import unicodedata

_NON_ALNUM = re.compile(r"[^a-z0-9]+")


def tokens(text: str) -> tuple[str, ...]:
    """Lowercase, strip accents and punctuation: "Tiramisù!" -> ("tiramisu",)."""
    decomposed = unicodedata.normalize("NFKD", text.casefold())
    without_accents = "".join(c for c in decomposed if not unicodedata.combining(c))
    return tuple(t for t in _NON_ALNUM.split(without_accents) if t)


def normalize(text: str) -> str:
    return " ".join(tokens(text))


def word_forms(token: str) -> frozenset[str]:
    """Simple singular forms, enough for menu words.

    Italian: margherite -> margherita, calzoni -> calzone/calzono, fritti -> fritto.
    English: pizzas -> pizza. Deliberately crude; covered by tests, refined with real messages.
    """
    forms = {token}
    if len(token) > 3:
        stem, last = token[:-1], token[-1]
        if last == "e":
            forms.add(stem + "a")
        elif last == "i":
            forms.update({stem + "o", stem + "e"})
        elif last == "s":
            forms.add(stem)
    return frozenset(forms)


def same_word(a: str, b: str) -> bool:
    return bool(word_forms(a) & word_forms(b))
