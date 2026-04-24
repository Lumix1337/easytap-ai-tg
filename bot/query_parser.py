from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ParsedQuery:
  original_text: str
  normalized_text: str
  query_candidates: list[str]
  city: str | None
  employment: str | None
  experience: str | None
  schedule: str | None


CITY_KEYWORDS = {
  "атырау": "Атырау",
  "atyrau": "Атырау",
  "алматы": "Алматы",
  "астана": "Астана",
  "шымкент": "Шымкент",
  "караганда": "Караганда",
  "костанай": "Костанай",
  "актау": "Актау",
  "павлодар": "Павлодар",
  "казахстан": "Казахстан",
  "kz": "Казахстан",
}

KAZAKHSTAN_LOCATION_KEYWORDS = {
  "казахстан",
  "қазақстан",
  "kazakhstan",
  "атырау",
  "atyrau",
  "алматы",
  "almaty",
  "астана",
  "astana",
  "шымкент",
  "shymkent",
  "караганда",
  "karaganda",
  "актау",
  "aktau",
  "костанай",
  "kostanay",
  "павлодар",
  "pavlodar",
}


def is_kazakhstan_location(text: str | None) -> bool:
  value = (text or "").lower()
  return any(keyword in value for keyword in KAZAKHSTAN_LOCATION_KEYWORDS)

ROLE_ALIASES = {
  "фуллстек": ["fullstack developer", "full stack developer", "backend developer", "frontend developer"],
  "фулстек": ["fullstack developer", "full stack developer"],
  "fullstack": ["fullstack developer", "full stack developer"],
  "веб разработчик": ["web developer", "frontend developer", "backend developer"],
  "frontend": ["frontend developer", "react developer", "javascript developer"],
  "backend": ["backend developer", "python developer", "golang developer"],
  "python": ["python developer", "backend developer python"],
  "react": ["react developer", "frontend developer react"],
  "стажировка": ["intern", "internship"],
}


def parse_user_query(text: str) -> ParsedQuery:
  normalized = " ".join(text.lower().split())
  city: str | None = None
  for key, value in CITY_KEYWORDS.items():
    if key in normalized:
      city = value
      break

  schedule = "remote" if any(x in normalized for x in ["удален", "remote", "дистанц"]) else None
  if any(x in normalized for x in ["part-time", "частич"]):
    employment = "part"
  elif any(x in normalized for x in ["полная", "full-time", "full time"]):
    employment = "full"
  else:
    employment = None
  experience = "noExperience" if any(x in normalized for x in ["junior", "джун", "стаж", "intern"]) else None

  candidates: list[str] = [normalized]
  for alias, expanded in ROLE_ALIASES.items():
    if alias in normalized:
      candidates.extend(expanded)

  # De-duplicate while preserving order
  unique_candidates: list[str] = []
  seen: set[str] = set()
  for candidate in candidates:
    clean = candidate.strip()
    if not clean or clean in seen:
      continue
    seen.add(clean)
    unique_candidates.append(clean)

  # Safety fallback to broad search
  if not unique_candidates:
    unique_candidates = ["стажировка junior developer"]

  return ParsedQuery(
    original_text=text,
    normalized_text=normalized,
    query_candidates=unique_candidates[:6],
    city=city,
    employment=employment,
    experience=experience,
    schedule=schedule,
  )
