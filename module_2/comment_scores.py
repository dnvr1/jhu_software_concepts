"""Preserve labeled narrative scores without converting scales or totals."""

import re

PATTERN = re.compile(
    r"\b(?P<label>GRE\s*(?:Quantitative|Verbal|Analytical Writing|AW|AWA|Q|V)"
    r"|GRE|CGPA|GPA)\b\s*(?:score\s*)?(?:of\s*|is\s*|was\s*)?"
    r"[:=\-]?\s*\(?\s*(?P<value>\d+(?:\.\d+)?)"
    r"(?:\s*(?:/|out of)\s*(?P<scale>\d+(?:\.\d+)?))?",
    re.I,
)
AMBIGUOUS = re.compile(
    r"\b(friend|someone|their|his|her|previous|previously|earlier|prior|"
    r"undergrad|undergraduate|bachelor|master|masters|BS|MS|BA|MA|"
    r"minimum|requires?|required|requirements?|target|aim|"
    r"expected|hope|retake|"
    r"not|no|never|didnot|without|less|above|below)\b|\b[BM]\.\s*[AS]\."
    r"|\b(?:didn|haven|hadn|wasn|isn)['’]t\b",
    re.I,
)


def enrich_scores(item):
    """Add exact score evidence; fill only unique, unambiguous missing fields.

    Score scales are stored as stated, never inferred or converted. Generic
    GRE remains unspecified, not relabeled as quantitative or a total.
    Potential historical/third-party/requirement contexts are review-only.
    """
    comment = item.get("comments") or ""
    mentions = []
    for match in PATTERN.finditer(comment):
        label = " ".join(match["label"].upper().split())
        key = "gpa" if label in {"GPA", "CGPA"} else "gre"
        if label.startswith("GRE "):
            suffix = label[4:].strip()
            key = {
                "Q": "gre_quantitative",
                "QUANTITATIVE": "gre_quantitative",
                "V": "gre_v",
                "VERBAL": "gre_v",
            }.get(suffix, "gre_aw")
        mentions.append(
            {
                "field": key,
                "label": match["label"],
                "value": float(match["value"]),
                "scale": float(match["scale"]) if match["scale"] else None,
                "excerpt": match[0],
                "start": match.start(),
                "end": match.end(),
                "review_reason": None,
                "used_for_field": False,
            }
        )
    context = {key: None for key in item["score_provenance"]}
    for mention in mentions:
        key = mention["field"]
        if item.get(key) is not None:
            mention["review_reason"] = "existing_field_preserved"
        elif AMBIGUOUS.search(comment):
            mention["review_reason"] = "ambiguous_context"
        elif sum(m["field"] == key for m in mentions) != 1:
            mention["review_reason"] = "multiple_mentions"
        elif mention["scale"] is not None and (
            mention["scale"] <= 0 or mention["value"] > mention["scale"]
        ):
            mention["review_reason"] = "inconsistent_scale"
        else:
            item[key] = mention["value"]
            item["score_provenance"][key] = "comment_labeled_narrative"
            mention["used_for_field"] = True
            context[key] = {
                k: mention[k]
                for k in ("label", "scale", "excerpt", "start", "end")
            }
    item["comment_score_mentions"] = mentions
    item["score_context"] = context
    return item
