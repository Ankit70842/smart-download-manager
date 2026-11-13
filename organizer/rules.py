"""Offline deterministic filename rules; confidence is a rule label, not AI."""
from dataclasses import dataclass
import re
import unicodedata
from pathlib import Path


SUBJECTS = {
    "Computer Networks": ["computer networks", "networking", "cn"],
    "DBMS": ["dbms", "database", "databases"],
    "Operating Systems": ["operating systems", "os notes", "os lecture"],
    "Maths": ["maths", "mathematics", "calculus", "algebra"],
}


def category_path(value):
    if not isinstance(value, str) or not value or len(value) > 180 or "\\" in value:
        raise ValueError("Use a category path such as Studies/Computer Networks (maximum 180 characters).")
    parts = value.split("/")
    reserved = {"CON", "PRN", "AUX", "NUL", "CONIN$", "CONOUT$"}
    reserved.update(f"{prefix}{number}" for prefix in ("COM", "LPT") for number in range(1, 10))
    for part in parts:
        if (not part or part in (".", "..") or part != part.strip() or part.endswith(".")
                or any(ord(c) < 32 or c in '<>:"|?*' for c in part)
                or unicodedata.normalize("NFKC", part.split(".")[0]).rstrip().upper() in reserved):
            raise ValueError("Category contains an invalid or reserved Windows folder name.")
    return "/".join(parts)


def default_settings():
    categories = ["Studies", "Projects", "Personal", "Games", "Installers", "Media", "Unsorted"]
    categories += ["Studies/" + subject for subject in SUBJECTS]
    rules = [dict(id=f"subject-{index}", category="Studies/" + subject,
                  keywords=words, extensions=[], priority=100)
             for index, (subject, words) in enumerate(SUBJECTS.items())]
    for category, words in [("Studies", ["lecture", "syllabus", "textbook"]),
                            ("Projects", ["project", "assignment", "repository"]),
                            ("Personal", ["invoice", "receipt", "resume"]),
                            ("Games", ["steam", "minecraft", "game"] )]:
        rules.append(dict(id=category.lower(), category=category, keywords=words, extensions=[], priority=30))
    rules += [dict(id="installers", category="Installers", keywords=[], extensions=["exe", "msi", "msix"], priority=10),
              dict(id="media", category="Media", keywords=[], extensions=["jpg", "jpeg", "png", "webp", "mp4", "mp3", "wav", "mkv"], priority=10)]
    return dict(categories=categories, rules=rules)


@dataclass(frozen=True)
class Classification:
    category: str
    confidence: str
    reason: str


def words(value):
    return " ".join(re.findall(r"[^\W_]+", value.casefold()))


def classify(filename, settings):
    name = " " + words(Path(filename).stem) + " "
    extension = Path(filename).suffix.lower().lstrip(".")
    matches = []
    for rule in settings["rules"]:
        keywords = [word for word in rule["keywords"] if " " + words(word) + " " in name]
        if rule["keywords"] and not keywords:
            continue
        if rule["extensions"] and extension not in rule["extensions"]:
            continue
        if not rule["keywords"] and not rule["extensions"]:
            continue
        reason = f"Rule {rule['id']}: " + (f"keyword ‘{keywords[0]}’" if keywords else f"extension .{extension}")
        matches.append((rule["priority"], rule["category"], "High" if keywords else "Medium", reason))
    if not matches:
        return Classification("Unsorted", "Needs review", "No matching rule; choose a category if you know its purpose.")
    highest = max(match[0] for match in matches)
    winners = [match for match in matches if match[0] == highest]
    if len({match[1] for match in winners}) > 1:
        return Classification("Unsorted", "Needs review", "Conflicting rules at the same priority; review required.")
    _, category, confidence, reason = winners[0]
    return Classification(category, confidence, reason + f" (priority {highest}).")
