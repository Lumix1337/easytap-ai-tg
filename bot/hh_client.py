from __future__ import annotations

from dataclasses import dataclass
from typing import Any

import httpx
from bot.query_parser import is_kazakhstan_location


@dataclass
class HhJob:
  title: str
  company: str
  url: str
  area: str
  salary: str | None
  snippet: str | None
  source: str = "hh.ru"


class HhClient:
  def __init__(self, base_url: str = "https://api.hh.ru", timeout_seconds: int = 20) -> None:
    self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout_seconds)

  async def close(self) -> None:
    await self._client.aclose()

  async def search_jobs(
    self,
    query: str,
    limit: int = 5,
    *,
    city: str | None = None,
    schedule: str | None = None,
    employment: str | None = None,
    experience: str | None = None,
  ) -> list[HhJob]:
    base_text = query.strip() or "стажировка"
    city_or_country = city or "Казахстан"
    search_text = f"{base_text} {city_or_country}".strip()
    params = {
      "text": search_text,
      "per_page": max(1, min(limit, 20)),
      "page": 0,
      "only_with_salary": False,
      "order_by": "relevance",
    }
    if schedule:
      params["schedule"] = schedule
    if employment:
      params["employment"] = employment
    if experience:
      params["experience"] = experience
    try:
      response = await self._client.get("/vacancies", params=params)
      if not response.is_success:
        return []
      data: Any = response.json()
      items = data.get("items", []) if isinstance(data, dict) else []
      jobs: list[HhJob] = []
      for item in items:
        if not isinstance(item, dict):
          continue
        salary = item.get("salary") or {}
        salary_text: str | None = None
        if isinstance(salary, dict) and salary:
          from_value = salary.get("from")
          to_value = salary.get("to")
          currency = salary.get("currency") or ""
          if from_value and to_value:
            salary_text = f"{from_value} - {to_value} {currency}".strip()
          elif from_value:
            salary_text = f"от {from_value} {currency}".strip()
          elif to_value:
            salary_text = f"до {to_value} {currency}".strip()

        snippet = item.get("snippet") if isinstance(item.get("snippet"), dict) else {}
        snippet_text = " ".join(
          [s for s in [snippet.get("requirement"), snippet.get("responsibility")] if isinstance(s, str)]
        ).strip() or None

        jobs.append(
          HhJob(
            title=str(item.get("name") or "Без названия"),
            company=str((item.get("employer") or {}).get("name") or "Компания"),
            url=str(item.get("alternate_url") or ""),
            area=str((item.get("area") or {}).get("name") or "Не указано"),
            salary=salary_text,
            snippet=snippet_text,
          )
        )
      return [job for job in jobs if is_kazakhstan_location(job.area)]
    except httpx.HTTPError:
      return []
