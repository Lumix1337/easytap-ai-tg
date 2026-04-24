from __future__ import annotations

import httpx


class EasyTapApiClient:
  def __init__(self, base_url: str, timeout_seconds: int = 20) -> None:
    self._client = httpx.AsyncClient(base_url=base_url.rstrip("/"), timeout=timeout_seconds)

  async def close(self) -> None:
    await self._client.aclose()

  async def register_telegram_user(self, tg_user_id: int, username: str | None, full_name: str) -> str | None:
    """
    Optional link flow with backend.
    Backend may return a short code/token for linking web <-> tg identities.
    """
    payload = {
      "tg_user_id": tg_user_id,
      "username": username,
      "full_name": full_name,
    }
    try:
      res = await self._client.post("/tg/link/start/", json=payload)
      if not res.is_success:
        return None
      data = res.json()
      return data.get("link_code")
    except httpx.HTTPError:
      return None

  async def assistant_chat(self, tg_user_id: int, message: str) -> dict | None:
    payload = {
      "channel": "telegram",
      "external_user_id": str(tg_user_id),
      "message": message,
    }
    try:
      res = await self._client.post("/assistant/channel-chat/", json=payload)
      if not res.is_success:
        return None
      data = res.json()
      return data if isinstance(data, dict) else None
    except httpx.HTTPError:
      return None

