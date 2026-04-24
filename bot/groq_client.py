from __future__ import annotations

import httpx


class GroqClient:
  def __init__(self, api_key: str, model: str, timeout_seconds: int = 20) -> None:
    self._model = model
    self._client = httpx.AsyncClient(
      base_url="https://api.groq.com/openai/v1",
      timeout=timeout_seconds,
      headers={
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json",
      },
    )

  async def close(self) -> None:
    await self._client.aclose()

  async def chat(self, system_prompt: str, user_prompt: str) -> str:
    payload = {
      "model": self._model,
      "messages": [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt},
      ],
      "temperature": 0.5,
      "max_tokens": 700,
    }
    try:
      response = await self._client.post("/chat/completions", json=payload)
      if not response.is_success:
        return "Не удалось получить ответ от AI-модели."
      data = response.json()
      choices = data.get("choices") or []
      if not choices:
        return "Пока не смог сформировать ответ. Попробуй переформулировать запрос."
      message = choices[0].get("message") or {}
      content = message.get("content")
      return str(content or "Пока не смог сформировать ответ. Попробуй переформулировать запрос.")
    except httpx.HTTPError:
      return "Ошибка сети при обращении к AI-модели. Попробуй позже."
