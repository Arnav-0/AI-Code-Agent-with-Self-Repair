from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.database import AppSettings
from app.models.schemas import (
    AppSettingsResponse,
    AppSettingsUpdate,
    ConnectionTestRequest,
    ConnectionTestResponse,
    LLMProviderSettings,
    RoutingSettings,
    SandboxSettingsSchema,
)

_DEFAULT_SETTINGS = AppSettingsResponse(
    llm=LLMProviderSettings(),
    routing=RoutingSettings(),
    sandbox=SandboxSettingsSchema(),
)


class SettingsService:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def get_all(self) -> AppSettingsResponse:
        result = await self.session.execute(select(AppSettings))
        rows = {row.key: row.value for row in result.scalars().all()}

        llm_data = rows.get("llm", {})
        routing_data = rows.get("routing", {})
        sandbox_data = rows.get("sandbox", {})

        return AppSettingsResponse(
            llm=LLMProviderSettings(**llm_data) if llm_data else LLMProviderSettings(),
            routing=RoutingSettings(**routing_data) if routing_data else RoutingSettings(),
            sandbox=(
                SandboxSettingsSchema(**sandbox_data) if sandbox_data else SandboxSettingsSchema()
            ),
        )

    async def update(self, settings_update: AppSettingsUpdate) -> AppSettingsResponse:
        if settings_update.llm is not None:
            await self._upsert("llm", settings_update.llm.model_dump())
        if settings_update.routing is not None:
            await self._upsert("routing", settings_update.routing.model_dump())
        if settings_update.sandbox is not None:
            await self._upsert("sandbox", settings_update.sandbox.model_dump())

        await self.session.flush()
        return await self.get_all()

    async def _upsert(self, key: str, value: dict) -> None:
        result = await self.session.execute(
            select(AppSettings).where(AppSettings.key == key)
        )
        existing = result.scalar_one_or_none()
        if existing:
            existing.value = value
        else:
            self.session.add(AppSettings(key=key, value=value))

    async def test_connection(
        self, request: ConnectionTestRequest
    ) -> ConnectionTestResponse:
        import time

        provider = request.provider.lower()
        start = time.perf_counter()

        try:
            if provider == "openai":
                from app.llm.providers import OpenAIProvider

                p = OpenAIProvider(api_key=request.api_key, model="gpt-4o-mini")
                ok = await p.health_check()
            elif provider == "anthropic":
                from app.llm.providers import AnthropicProvider

                p = AnthropicProvider(api_key=request.api_key)
                ok = await p.health_check()
            elif provider == "ollama":
                from app.llm.providers import OllamaProvider

                base_url = request.endpoint or "http://localhost:11434"
                p = OllamaProvider(base_url=base_url)
                ok = await p.health_check()
            elif provider == "openrouter":
                from app.llm.providers import OpenRouterProvider

                p = OpenRouterProvider(api_key=request.api_key)
                ok = await p.health_check()
            else:
                return ConnectionTestResponse(
                    success=False,
                    message=f"Unknown provider: {provider}",
                    latency_ms=None,
                )

            latency = int((time.perf_counter() - start) * 1000)

            if ok:
                return ConnectionTestResponse(
                    success=True,
                    message=f"{provider.title()} connection successful",
                    latency_ms=latency,
                )
            else:
                return ConnectionTestResponse(
                    success=False,
                    message=f"{provider.title()} health check failed",
                    latency_ms=latency,
                )
        except Exception as exc:
            latency = int((time.perf_counter() - start) * 1000)
            return ConnectionTestResponse(
                success=False,
                message=f"Connection failed: {exc}",
                latency_ms=latency,
            )
