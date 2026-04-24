from __future__ import annotations

from dataclasses import dataclass

from bot.groq_client import GroqClient
from bot.hh_client import HhClient, HhJob
from bot.query_parser import is_kazakhstan_location, parse_user_query
from bot.remotive_client import RemotiveClient


@dataclass
class AssistantResult:
  answer: str
  jobs: list[HhJob]


class AssistantService:
  def __init__(self, groq: GroqClient, hh: HhClient, remotive: RemotiveClient, jobs_limit: int = 5) -> None:
    self._groq = groq
    self._hh = hh
    self._remotive = remotive
    self._jobs_limit = jobs_limit

  async def close(self) -> None:
    await self._groq.close()
    await self._hh.close()
    await self._remotive.close()

  async def handle_user_message(self, user_text: str) -> AssistantResult:
    parsed = parse_user_query(user_text)

    jobs: list[HhJob] = []
    seen_urls: set[str] = set()

    async def collect(query: str, *, city: str | None, schedule: str | None) -> None:
      nonlocal jobs
      found = await self._hh.search_jobs(
        query,
        limit=self._jobs_limit,
        city=city,
        schedule=schedule,
        employment=parsed.employment,
        experience=parsed.experience,
      )
      for item in found:
        key = item.url or f"{item.company}:{item.title}:{item.area}"
        if key in seen_urls:
          continue
        seen_urls.add(key)
        jobs.append(item)
        if len(jobs) >= self._jobs_limit:
          return

    # 1) Strict queries with extracted filters.
    for candidate in parsed.query_candidates:
      if len(jobs) >= self._jobs_limit:
        break
      await collect(candidate, city=parsed.city, schedule=parsed.schedule)

    # 2) Loosen schedule filter if still empty.
    if not jobs and parsed.schedule is not None:
      for candidate in parsed.query_candidates[:3]:
        if len(jobs) >= self._jobs_limit:
          break
        await collect(candidate, city=parsed.city, schedule=None)

    # 3) Global broad fallback when zero results.
    if not jobs:
      fallback_queries = [
        "junior developer",
        "internship стажировка",
        "web developer",
      ]
      for candidate in fallback_queries:
        if len(jobs) >= self._jobs_limit:
          break
        await collect(candidate, city=None, schedule=None)

    # 4) Extend with another platform if HH is empty or too narrow.
    if len(jobs) < max(2, self._jobs_limit // 2):
      for candidate in parsed.query_candidates[:3]:
        remotive_jobs = await self._remotive.search_jobs(candidate, limit=self._jobs_limit)
        for item in remotive_jobs:
          key = item.url or f"{item.company}:{item.title}:{item.area}:{item.source}"
          if key in seen_urls:
            continue
          seen_urls.add(key)
          jobs.append(item)
          if len(jobs) >= self._jobs_limit:
            break
        if len(jobs) >= self._jobs_limit:
          break

    # Hard limit: Kazakhstan only.
    jobs = [job for job in jobs if is_kazakhstan_location(job.area)]

    jobs_context = "\n".join(
      [
        f"- {job.title} | {job.company} | {job.area} | {job.salary or 'зарплата не указана'} | {job.url}"
        for job in jobs[:5]
      ]
    )
    if not jobs_context:
      jobs_context = "Релевантные вакансии пока не найдены."

    system_prompt = (
      "Ты карьерный AI-ассистент EasyTap. Отвечай по-русски, коротко и полезно. "
      "Дай персональные рекомендации по трудоустройству, отклику, резюме и интервью. "
      "Не выдумывай факты: опирайся на список вакансий из контекста."
    )
    user_prompt = (
      f"Запрос пользователя: {user_text}\n\n"
      f"Разбор запроса: city={parsed.city}, schedule={parsed.schedule}, experience={parsed.experience}\n\n"
      f"Найденные вакансии (hh.ru + другие платформы):\n{jobs_context}\n\n"
      "Сформируй ответ: 1) краткий вывод, 2) лучшие вакансии и почему, "
      "3) практический план отклика (резюме, сопроводительное, интервью) на ближайшие 48 часов."
    )
    answer = await self._groq.chat(system_prompt=system_prompt, user_prompt=user_prompt)
    return AssistantResult(answer=answer, jobs=jobs)
