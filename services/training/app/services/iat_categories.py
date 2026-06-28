"""
IAT category catalog -- supplies the categories, poles, and stimulus
words an Implicit Association Test session is built from.

Hardcoded stub today (two value-neutral work-style categories, chosen so
demo content never encodes a real demographic stereotype). A future
integration can swap in the company's real assessment content -- e.g. an
internal content-module API -- behind the same `get_categories` interface,
without touching IATService or the router.
"""
from dataclasses import dataclass, field
from shared.base.service import BaseService


@dataclass
class IATCategory:
    id: str
    label: str
    pole_a: str
    pole_b: str
    stimuli: list[str] = field(default_factory=list)


_STUB_CATEGORIES: list[IATCategory] = [
    IATCategory(
        id="decision-style",
        label="Decision-Making Style",
        pole_a="Analytical",
        pole_b="Intuitive",
        stimuli=["Data", "Logic", "Evidence", "Metrics"],
    ),
    IATCategory(
        id="feedback-style",
        label="Feedback Style",
        pole_a="Direct",
        pole_b="Diplomatic",
        stimuli=["Blunt", "Frank", "Candid", "Tactful"],
    ),
]


class IATCategoryCatalog(BaseService):
    """Supplies the set of categories an IAT session is built from."""

    def get_categories(self) -> list[IATCategory]:
        # Return fresh copies (including a fresh stimuli list) so callers can
        # never mutate the shared defaults, even indirectly via nested lists.
        return [
            IATCategory(
                id=c.id,
                label=c.label,
                pole_a=c.pole_a,
                pole_b=c.pole_b,
                stimuli=list(c.stimuli),
            )
            for c in _STUB_CATEGORIES
        ]
