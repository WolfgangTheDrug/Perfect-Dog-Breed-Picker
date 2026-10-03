"""
breed_match_engine.py

Fuzzy matching of dog breeds (dogapi.dog v2) against user preferences.

DATA MAPPING
------------
Each item of the API `data` list is read like this:

    attributes.name / description / hypoallergenic
    attributes.male_weight, female_weight   -> breed weight span (min..max, kg)
    attributes.traits.energy, shedding, barking, drooling, trainability,
                      apartment_friendly, good_with_children, good_with_dogs
    attributes.traits.exercise_minutes      -> "exercise" preference
    attributes.traits.temperament           -> list of adjectives

Any criterion that is missing for a particular breed is skipped (not scored as
0) and lowers that breed's `coverage`.

Scoring model
-------------
* Each active preference gets a membership score in [0, 1].
  - Inside the preferred range -> 1.0
  - Outside it -> Gaussian decay with the distance from the range:
        exp(-0.5 * (distance / sigma) ** 2),  sigma = scale * factor
    where factor is small when `strict` is true (sharp decay) and larger when
    `strict` is false (gentle decay).
* `dealbreaker: true` -> a breed outside the range is removed entirely.
* Overall score = weighted mean of the evaluated criteria
  (weight = 1, +0.5 if strict, +1.0 if dealbreaker), then reduced slightly
  when much of the preference could not be evaluated (`missing_data_penalty`).
"""

from __future__ import annotations

import math
import re
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Mapping, Optional, Sequence, Tuple

TRAIT_KEYS = (
    "energy", "shedding", "barking", "drooling", "trainability",
    "apartment_friendly", "good_with_children", "good_with_dogs",
)
_EPS = 1e-9


# --------------------------------------------------------------------------- #
# Data containers
# --------------------------------------------------------------------------- #
@dataclass
class CriterionResult:
    name: str
    weight: float
    score: Optional[float]            # 0..1, None = could not be evaluated
    breed_value: Any = None
    violated: bool = False            # outside the preferred range / mismatch
    note: str = ""


@dataclass
class BreedMatch:
    name: str
    id: Optional[str]
    score: float                      # used for sorting (0..1)
    raw_score: float                  # before the missing-data penalty
    coverage: float                   # share of preference weight evaluated
    breakdown: Dict[str, CriterionResult]
    unverified_dealbreakers: List[str] = field(default_factory=list)

    def to_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "id": self.id,
            "score": round(self.score, 4),
            "raw_score": round(self.raw_score, 4),
            "coverage": round(self.coverage, 4),
            "unverified_dealbreakers": self.unverified_dealbreakers,
            "breakdown": {
                k: {
                    "score": None if v.score is None else round(v.score, 4),
                    "weight": v.weight,
                    "breed_value": v.breed_value,
                    "note": v.note,
                }
                for k, v in self.breakdown.items()
            },
        }


@dataclass
class MatchResult:
    matches: List[BreedMatch]                       # sorted best -> worst
    rejected: List[Tuple[str, List[str]]]           # (breed, reasons)

    def names(self) -> List[str]:
        return [m.name for m in self.matches]

    def to_list(self) -> List[Dict[str, Any]]:
        return [m.to_dict() for m in self.matches]


@dataclass
class _Criterion:
    key: str
    kind: str                         # "range" | "interval" | "bool" | "terms"
    target: Any
    strict: bool = False
    dealbreaker: bool = False
    scale: float = 1.0

    @property
    def weight(self) -> float:
        return 1.0 + (0.5 if self.strict else 0.0) + (1.0 if self.dealbreaker else 0.0)


# --------------------------------------------------------------------------- #
# Engine
# --------------------------------------------------------------------------- #
class BreedMatchEngine:
    def __init__(
        self,
        preferences: Mapping[str, Any],
        breeds: Sequence[Mapping[str, Any]],
        *,
        strict_factor: float = 0.15,
        lenient_factor: float = 0.35,
        scales: Optional[Mapping[str, float]] = None,
        unknown_dealbreaker: str = "keep",      # "keep" or "exclude"
        missing_data_penalty: float = 0.25,
    ):
        """
        preferences          the preference dict (grouped, as in your example)
        breeds               the API `data` list (one dict per breed)
        strict_factor        sigma = scale * factor for strict criteria (sharp decay)
        lenient_factor       same for non-strict criteria (gentle decay)
        scales               per-key "one unit of distance" override, e.g. {"weight": 25}
        unknown_dealbreaker  what to do when a dealbreaker can't be checked
                             because the data is missing ("keep" flags it instead)
        missing_data_penalty 0..1, shrinks scores of breeds with low coverage
        """
        if unknown_dealbreaker not in ("keep", "exclude"):
            raise ValueError("unknown_dealbreaker must be 'keep' or 'exclude'")
        self.strict_factor = strict_factor
        self.lenient_factor = lenient_factor
        self.unknown_dealbreaker = unknown_dealbreaker
        self.missing_data_penalty = missing_data_penalty
        self.scales = {"weight": 30.0, "exercise": 60.0, **(scales or {})}

        self._raw_breeds: List[Mapping[str, Any]] = list(breeds)
        self.criteria = self._parse_preferences(preferences)

    # ------------------------------------------------------------------ API
    def match(self, top_n: Optional[int] = None, min_score: float = 0.0) -> MatchResult:
        matches: List[BreedMatch] = []
        rejected: List[Tuple[str, List[str]]] = []
        total_weight = sum(c.weight for c in self.criteria)

        for raw in self._raw_breeds:
            breed = self._normalise(raw)
            if not breed["name"]:
                continue

            results: Dict[str, CriterionResult] = {}
            reasons: List[str] = []
            unverified: List[str] = []

            for c in self.criteria:
                r = self._evaluate(breed, c)
                results[c.key] = r
                if not c.dealbreaker:
                    continue
                if r.violated:
                    reasons.append(r.note)
                elif r.score is None:
                    if self.unknown_dealbreaker == "exclude":
                        reasons.append(f"{c.key}: no data to verify dealbreaker")
                    else:
                        unverified.append(c.key)

            if reasons:                       # dealbreaker -> removed completely
                rejected.append((breed["name"], reasons))
                continue

            evaluated = [r for r in results.values() if r.score is not None]
            ev_weight = sum(r.weight for r in evaluated)
            if not self.criteria:
                raw_score, coverage = 1.0, 1.0
            elif ev_weight == 0:
                raw_score, coverage = 0.0, 0.0
            else:
                raw_score = sum(r.weight * r.score for r in evaluated) / ev_weight
                coverage = ev_weight / total_weight
            score = raw_score * (1.0 - self.missing_data_penalty * (1.0 - coverage))

            if score < min_score:
                continue
            matches.append(BreedMatch(
                name=breed["name"], id=breed["id"], score=score, raw_score=raw_score,
                coverage=coverage, breakdown=results, unverified_dealbreakers=unverified,
            ))

        matches.sort(key=lambda m: (-m.score, -m.coverage, m.name.lower()))
        if top_n is not None:
            matches = matches[:top_n]
        return MatchResult(matches=matches, rejected=rejected)

    # ----------------------------------------------------- preference parsing
    def _parse_preferences(self, prefs: Mapping[str, Any]) -> List[_Criterion]:
        crits: List[_Criterion] = []
        for group in prefs.values():
            if not isinstance(group, Mapping):
                continue
            for key, spec in group.items():
                if not isinstance(spec, Mapping) or "value" not in spec:
                    continue
                key = "exercise" if key == "excercise" else key   # tolerate typo
                value = spec["value"]
                strict = bool(spec.get("strict", False))
                deal = bool(spec.get("dealbreaker", False))

                if key == "hypoallergenic":
                    want = self._tristate(value)
                    if want is None:                      # "Doesn't Matter"
                        continue
                    # an explicit Yes/No is treated as a hard requirement
                    # unless the user sets "dealbreaker": false
                    crits.append(_Criterion(key, "bool", want, True,
                                            bool(spec.get("dealbreaker", True))))
                elif key == "temperament":
                    terms = [value] if isinstance(value, str) else list(value or [])
                    terms = [str(t).strip() for t in terms if str(t).strip()]
                    if terms:
                        crits.append(_Criterion(key, "terms", terms, strict, deal))
                else:
                    rng = self._range(value)
                    if rng is None:
                        continue
                    lo, hi = rng
                    if key in TRAIT_KEYS and lo <= 1 and hi >= 5:
                        continue                          # unconstrained 1-5 trait
                    scale = self.scales.get(key) or (4.0 if key in TRAIT_KEYS
                                                     else max(hi - lo, 1.0))
                    kind = "interval" if key == "weight" else "range"
                    crits.append(_Criterion(key, kind, (lo, hi), strict, deal, scale))
        return crits

    @staticmethod
    def _range(value: Any) -> Optional[Tuple[float, float]]:
        try:
            if isinstance(value, (int, float)):
                return float(value), float(value)
            lo, hi = float(value[0]), float(value[1])
            return (lo, hi) if lo <= hi else (hi, lo)
        except (TypeError, ValueError, IndexError):
            return None

    @staticmethod
    def _tristate(value: Any) -> Optional[bool]:
        if isinstance(value, bool):
            return value
        s = str(value).strip().lower()
        if s in ("yes", "true", "y", "required", "hypoallergenic"):
            return True
        if s in ("no", "false", "n", "not hypoallergenic"):
            return False
        return None                                           # "doesn't matter", ""

    # ------------------------------------------------------ breed normalising
    def _normalise(self, raw: Mapping[str, Any]) -> Dict[str, Any]:
        attrs = raw.get("attributes", raw)
        weights: List[float] = []
        for k in ("male_weight", "female_weight"):
            w = attrs.get(k) or {}
            for kk in ("min", "max"):
                v = w.get(kk)
                if isinstance(v, (int, float)) and not isinstance(v, bool) and v > 0:
                    weights.append(float(v))

        breed: Dict[str, Any] = {
            "id": raw.get("id"),
            "name": (attrs.get("name") or "").strip(),
            "description": attrs.get("description") or "",
            "hypoallergenic": attrs.get("hypoallergenic"),
            "weight": (min(weights), max(weights)) if weights else None,
        }
        traits = attrs.get("traits")
        if isinstance(traits, Mapping):
            for k, v in traits.items():
                breed[k] = v
            breed["exercise"] = traits.get("exercise_minutes", traits.get("exercise"))
        return breed

    # ------------------------------------------------------------- evaluation
    def _membership(self, distance: float, scale: float, strict: bool) -> float:
        if distance <= _EPS:
            return 1.0
        sigma = scale * (self.strict_factor if strict else self.lenient_factor)
        return math.exp(-0.5 * (distance / sigma) ** 2)

    def _evaluate(self, breed: Dict[str, Any], c: _Criterion) -> CriterionResult:
        res = CriterionResult(c.key, c.weight, None)

        if c.kind == "terms":
            return self._eval_terms(breed, c, res)

        val = breed.get(c.key)
        if val is None:
            res.note = f"{c.key}: no data"
            return res
        res.breed_value = val

        if c.kind == "bool":
            ok = bool(val) == c.target
            res.score = 1.0 if ok else 0.0
            res.violated = not ok
            res.note = f"{c.key}: breed={bool(val)}, wanted={c.target}"
            return res

        lo, hi = c.target
        if c.kind == "interval":                      # breed has a [min, max] span
            b_lo, b_hi = val
            distance = max(lo - b_hi, b_lo - hi, 0.0)  # gap between intervals
        else:                                         # single number
            try:
                v = float(val)
            except (TypeError, ValueError):
                res.note = f"{c.key}: non-numeric data"
                return res
            distance = max(lo - v, v - hi, 0.0)

        res.score = self._membership(distance, c.scale, c.strict)
        res.violated = distance > _EPS
        res.note = f"{c.key}: {val} outside [{lo:g}, {hi:g}]" if res.violated else ""
        return res

    def _eval_terms(self, breed: Dict[str, Any], c: _Criterion,
                    res: CriterionResult) -> CriterionResult:
        listed = breed.get("temperament")
        if isinstance(listed, str):
            listed = [t for t in re.split(r"[,;/]", listed) if t.strip()]
        listed_text = ", ".join(map(str, listed)).lower() if listed else ""
        desc_text = (breed.get("description") or "").lower()
        if not listed_text and not desc_text:
            res.note = "temperament: no data"
            return res
        res.breed_value = list(listed) if listed else None

        # a term in the temperament list counts fully; one that only appears in
        # the free-text description counts as weaker evidence (0.6)
        total = 0.0
        for t in c.target:
            if listed_text and self._term_in(t, listed_text):
                total += 1.0
            elif desc_text and self._term_in(t, desc_text):
                total += 0.6
        res.score = total / len(c.target)
        res.violated = total == 0
        if res.violated:
            res.note = f"temperament: none of {c.target} found"
        return res

    @staticmethod
    def _term_in(term: str, text: str) -> bool:
        t = term.lower().strip()
        stem = t[: max(4, len(t) - 3)]                 # crude stemming
        return re.search(r"\b" + re.escape(stem), text) is not None


# # --------------------------------------------------------------------------- #
# # Demo
# # --------------------------------------------------------------------------- #
# if __name__ == "__main__":
#     prefs = {
#         "behavioral_&_care_traits": {
#             "energy": {"value": [2, 4], "strict": False, "dealbreaker": False},
#             "shedding": {"value": [1, 5], "strict": False, "dealbreaker": False},
#             "barking": {"value": [1, 2], "strict": True, "dealbreaker": False},
#             "drooling": {"value": [1, 5], "strict": False, "dealbreaker": False},
#             "trainability": {"value": [4, 5], "strict": False, "dealbreaker": False},
#             "apartment_friendly": {"value": [1, 5], "strict": False, "dealbreaker": False},
#             "good_with_children": {"value": [4, 5], "strict": False, "dealbreaker": True},
#             "good_with_dogs": {"value": [1, 5], "strict": False, "dealbreaker": False},
#         },
#         "physical_&_lifestyle_constraints": {
#             "weight": {"value": [10, 40], "strict": False, "dealbreaker": False},
#             "excercise": {"value": [30, 90], "strict": False, "dealbreaker": False},
#         },
#         "special_requirements": {"hypoallergenic": {"value": "Doesn't Matter"}},
#         "desired_temperament": {"temperament": {"value": ["Intelligent", "Gentle"]}},
#     }

#     breeds = []                               # the `data` list you already fetched
#     engine = BreedMatchEngine(prefs, breeds)
#     result = engine.match(top_n=10)
#     for m in result.matches:
#         print(f"{m.score:.2f}  (coverage {m.coverage:.0%})  {m.name}")
#     print(f"\n{len(result.rejected)} breeds removed by dealbreakers")