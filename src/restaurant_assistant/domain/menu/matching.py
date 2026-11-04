"""MenuMatcher domain service: which dish did the customer mean? (story M1)

The LLM only copies the customer's words ("margherite"); this code decides which dish that is.
It never guesses: if two dishes fit, the result is Ambiguous and the assistant asks.
A fuzzy match is acceptable because the customer sees the dish name in the summary and
must reply "sì" before anything is ordered.
"""

from __future__ import annotations

from dataclasses import dataclass
from difflib import SequenceMatcher
from typing import Literal

from restaurant_assistant.domain.menu.menu import Menu
from restaurant_assistant.domain.menu.menu_item import MenuItem
from restaurant_assistant.domain.menu.text import same_word, tokens

MatchKind = Literal["exact", "alias", "partial", "fuzzy"]

# Words customers add around a dish name. Only removed on a second attempt, so a dish that
# really contains one of them ("Pizza fritta") still matches on the first attempt.
FILLER_WORDS = frozenset(
    {"pizza", "pizze", "un", "una", "uno", "per", "favore", "piacere", "vorrei",
     "please", "the", "a", "an", "some", "i", "want", "would", "like"}
)  # fmt: skip

FUZZY_ACCEPT = 0.80  # similarity needed to accept a typo
FUZZY_SUGGEST = 0.70  # similarity needed to offer a dish as "did you mean...?"
FUZZY_MARGIN = 0.10  # the best dish must beat the runner-up by this much
FUZZY_MIN_LENGTH = 4  # don't fuzzy-match very short words


@dataclass(frozen=True, slots=True)
class Matched:
    item: MenuItem
    how: MatchKind


@dataclass(frozen=True, slots=True)
class Ambiguous:
    query: str
    candidates: tuple[MenuItem, ...]


@dataclass(frozen=True, slots=True)
class NotFound:
    query: str


MatchResult = Matched | Ambiguous | NotFound


@dataclass(frozen=True, slots=True)
class _Label:
    item: MenuItem
    words: tuple[str, ...]
    is_alias: bool


class MenuMatcher:
    def __init__(self, menu: Menu) -> None:
        self._labels = [
            _Label(dish, tokens(text), is_alias)
            for dish in menu
            for text, is_alias in (
                (dish.name, False),
                *(((dish.name_en, False),) if dish.name_en else ()),
                *((alias, True) for alias in dish.aliases),
            )
        ]

    def match(self, text: str) -> MatchResult:
        words = tokens(text)
        result = self._match_words(text, words)
        if isinstance(result, NotFound):
            core = tuple(w for w in words if w not in FILLER_WORDS)
            if core and core != words:
                result = self._match_words(text, core)
        return result

    def _match_words(self, text: str, words: tuple[str, ...]) -> MatchResult:
        if not words:
            return NotFound(text)

        exact = [label for label in self._labels if _same_words(words, label.words)]
        if exact:
            return _one_or_ambiguous(
                text, exact, "alias" if all(label.is_alias for label in exact) else "exact"
            )

        partial = [label for label in self._labels if _contained(words, label.words)]
        if partial:
            return _one_or_ambiguous(text, partial, "partial")

        return self._fuzzy(text, " ".join(words))

    def _fuzzy(self, text: str, query: str) -> MatchResult:
        if len(query) < FUZZY_MIN_LENGTH:
            return NotFound(text)
        best: dict[str, tuple[float, MenuItem]] = {}
        for label in self._labels:
            score = SequenceMatcher(None, query, " ".join(label.words)).ratio()
            if score > best.get(label.item.id, (0.0, label.item))[0]:
                best[label.item.id] = (score, label.item)
        ranked = sorted(best.values(), key=lambda pair: pair[0], reverse=True)
        top_score, top_item = ranked[0]
        runner_up = ranked[1][0] if len(ranked) > 1 else 0.0
        if top_score >= FUZZY_ACCEPT and top_score - runner_up >= FUZZY_MARGIN:
            return Matched(top_item, "fuzzy")
        close = tuple(
            item
            for score, item in ranked
            if score >= FUZZY_SUGGEST and top_score - score < FUZZY_MARGIN
        )
        return Ambiguous(text, close) if close else NotFound(text)


def _same_words(query: tuple[str, ...], label: tuple[str, ...]) -> bool:
    return len(query) == len(label) and all(map(same_word, query, label))


def _contained(query: tuple[str, ...], label: tuple[str, ...]) -> bool:
    return all(any(same_word(q, word) for word in label) for q in query)


def _one_or_ambiguous(text: str, labels: list[_Label], how: MatchKind) -> MatchResult:
    items = tuple(dict.fromkeys(label.item for label in labels))  # unique, keeps order
    return Matched(items[0], how) if len(items) == 1 else Ambiguous(text, items)
