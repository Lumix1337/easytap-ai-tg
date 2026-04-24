from __future__ import annotations

from typing import Any

import httpx

from bot.hh_client import HhJob
from bot.query_parser import is_kazakhstan_location


class RemotiveClient:
  def __init__(self, base_url: str = "https://remotive.com/api", timeout_seconds: int = 20) -> None:
    self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout_seconds)

  async def close(self) -> None:
    await self._client.aclose()

  async def search_jobs(self, query: str, limit: int = 5) -> list[HhJob]:
    params = {"search": query.strip() or "developer", "limit": max(1, min(limit, 20))}
    try:
      response = await self._client.get("/remote-jobs", params=params)
      if not response.is_success:
        return []
      data: Any = response.json()
      items = data.get("jobs", []) if isinstance(data, dict) else []
      jobs: list[HhJob] = []
      for item in items[:limit]:
        if not isinstance(item, dict):
          continue
        location = str(item.get("candidate_required_location") or "Remote")
        if not is_kazakhstan_location(location):
          continue
        jobs.append(
          HhJob(
            title=str(item.get("title") or "Без названия"),
            company=str(item.get("company_name") or "Компания"),
            url=str(item.get("url") or ""),
            area=location,
            salary=str(item.get("salary")) if item.get("salary") else None,
            snippet=str(item.get("description"))[:280] if item.get("description") else None,
            source="remotive.com",
          )
        )
      return jobs
    except httpx.HTTPError:
      return []
