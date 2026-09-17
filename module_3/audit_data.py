"""Independently compare saved table cells and badges with applicant JSON."""

import argparse
from collections import Counter
import hashlib
import json
from pathlib import Path
import re
from urllib.parse import urljoin

from bs4 import BeautifulSoup


def _source_text(node):
    """Read semantic source text without HTML-layout whitespace artifacts."""
    return re.sub(r"\s+", " ", node.get_text(" ", strip=True)).strip()


def _narrative_value(record, key, comment):
    """Check the stored excerpt against source text and read its number."""
    evidence = [
        m
        for m in record.get("comment_score_mentions", [])
        if m["field"] == key and m["used_for_field"]
    ]
    if len(evidence) != 1:
        return None
    mention = evidence[0]
    excerpt = (comment or "")[mention["start"] : mention["end"]]
    numbers = re.findall(r"\d+(?:\.\d+)?", excerpt)
    if excerpt == mention["excerpt"] and numbers:
        return float(numbers[0])
    return None


# Keep independent source expectations together for review against the table.
def audit(data_path, raw_dir):  # pylint: disable=too-many-locals
    """Read saved evidence without invoking the production parsing code."""
    records = json.loads(Path(data_path).read_text(encoding="utf-8"))
    indexed = {row["url"]: row for row in records}
    issues, observed = [], set()
    comparisons = 0
    pages = 0
    for journal in sorted(Path(raw_dir).glob("page-*.json")):
        entry = json.loads(journal.read_text(encoding="utf-8"))
        manifest = entry["manifest"]
        payload = (Path(raw_dir) / manifest["archive"]).read_bytes()
        if hashlib.sha256(payload).hexdigest() != manifest["sha256"]:
            issues.append({"page": journal.name, "error": "HTML hash differs"})
        page_url = manifest["source_url"]
        soup = BeautifulSoup(payload, "html.parser")
        rows = soup.select("table tbody tr")
        pages += 1
        for index, row in enumerate(rows):
            cells = row.find_all("td", recursive=False)
            if len(cells) != 5:
                continue
            link = cells[4].find("a", href=re.compile(r"/result/"))
            if link is None:
                continue
            url = urljoin(page_url, link["href"])
            observed.add(url)
            if url not in indexed:
                issues.append({"url": url, "error": "Source entry omitted"})
                continue
            actual = indexed[url]
            spans = cells[1].find_all("span")
            if len(spans) != 2:
                issues.append(
                    {"url": url, "error": "Audit layout unsupported"}
                )
                continue
            school = _source_text(cells[0])
            name, degree = [
                _source_text(span) or None for span in spans
            ]
            decision = _source_text(cells[3])
            status, separator, date = decision.partition(" on ")
            date = date if separator else None
            following = []
            for detail in rows[index + 1 :]:
                if len(detail.find_all("td", recursive=False)) == 5:
                    break
                following.append(detail)
            comments, badges = [], []
            for detail in following:
                comments.extend(
                    _source_text(p) for p in detail.find_all("p")
                )
                badges.extend(
                    _source_text(div)
                    for div in detail.find_all("div")
                    if not div.find(["div", "p", "script", "iframe"])
                )
            comment = re.sub(r"\s+", " ", " ".join(comments)).strip() or None
            expected = {
                "university": school,
                "program_name": name,
                "program": name + ", " + school if name else None,
                "degree": degree,
                "date_added": _source_text(cells[2]),
                "status": {"Wait listed": "Waitlisted"}.get(status, status),
                "decision_date": date,
                "acceptance_date": date if status == "Accepted" else None,
                "rejection_date": date if status == "Rejected" else None,
                "term": next(
                    (
                        b
                        for b in badges
                        if re.fullmatch(
                            r"(Fall|Spring|Summer|Winter) \d{4}", b
                        )
                    ),
                    None,
                ),
                "citizenship": next(
                    (
                        b
                        for b in badges
                        if b
                        in {"American", "International", "Other", "Domestic"}
                    ),
                    None,
                ),
                "comments": comment,
                "raw_program": cells[1].get_text(" ", strip=True),
            }
            for label, key in [
                ("GRE AW", "gre_aw"),
                ("GRE V", "gre_v"),
                ("GRE", "gre"),
                ("GPA", "gpa"),
            ]:
                matches = [
                    re.fullmatch(re.escape(label) + r" (\d+(?:\.\d+)?)", b)
                    for b in badges
                ]
                expected[key] = next((float(m[1]) for m in matches if m), None)
            declaration = re.fullmatch(
                r"GRE,\s*Quantitative:\s*(\d+(?:\.\d+)?),"
                r"\s*Verbal:\s*(\d+(?:\.\d+)?),"
                r"\s*Analytical Writing:\s*(\d+(?:\.\d+)?)",
                comment or "",
                re.I,
            )
            if declaration:
                for key, value in zip(
                    ("gre_quantitative", "gre_v", "gre_aw"),
                    declaration.groups(),
                ):
                    if expected.get(key) is None:
                        expected[key] = float(value)
            for key, value in expected.items():
                if (
                    value is None
                    and actual.get("score_provenance", {}).get(key)
                    == "comment_labeled_narrative"
                ):
                    value = _narrative_value(actual, key, comment)
                comparisons += 1
                if actual.get(key) != value:
                    issues.append(
                        {
                            "url": url,
                            "field": key,
                            "expected": value,
                            "actual": actual.get(key),
                        }
                    )
    return {
        "records": len(records),
        "unique_urls": len(indexed),
        "source_unique_urls": len(observed),
        "pages": pages,
        "field_comparisons": comparisons,
        "mismatches": issues,
        "unbacked_urls": sorted(set(indexed) - observed),
        "statuses": dict(Counter(r["status"] for r in records)),
        "populated": {
            k: sum(r.get(k) is not None for r in records) for k in records[0]
        },
    }


def main():
    """Print the report; exit nonzero when a discrepancy needs review."""
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--file", type=Path, default=Path("applicant_data.json")
    )
    parser.add_argument("--raw-dir", type=Path, default=Path("raw"))
    args = parser.parse_args()
    report = audit(args.file, args.raw_dir)
    print(json.dumps(report, indent=2, ensure_ascii=True))
    return int(
        bool(
            report["mismatches"]
            or report["unbacked_urls"]
            or report["records"] != report["unique_urls"]
        )
    )


if __name__ == "__main__":
    raise SystemExit(main())
