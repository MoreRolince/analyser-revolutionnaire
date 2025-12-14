"""
Gestion centralisée du navigateur Playwright (async) avec rotation d'user-agents.
Conçu pour être léger et réutilisable par les pipelines de scraping.
"""
from __future__ import annotations

import asyncio
import random
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page


UA_PATH = Path(__file__).resolve().parent.parent / "config" / "ua_list.txt"


def _load_user_agents() -> list[str]:
    if UA_PATH.exists():
        return [ua.strip() for ua in UA_PATH.read_text(encoding="utf-8").splitlines() if ua.strip()]
    # Fallback si le fichier n'existe pas
    return [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    ]


USER_AGENTS = _load_user_agents()


class BrowserPool:
    """Pool simple pour ouvrir des pages Playwright avec UA rotatif."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._pw = None
        self._browser: Browser | None = None

    async def __aenter__(self):
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        return self

    async def __aexit__(self, *exc):
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()

    async def new_page(self) -> Page:
        assert self._browser, "BrowserPool non initialisé"
        context = await self._browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1366, "height": 768},
        )
        page = await context.new_page()
        # Masquer navigator.webdriver
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        return page



Gestion centralisée du navigateur Playwright (async) avec rotation d'user-agents.
Conçu pour être léger et réutilisable par les pipelines de scraping.
"""
from __future__ import annotations

import asyncio
import random
from pathlib import Path
from playwright.async_api import async_playwright, Browser, Page


UA_PATH = Path(__file__).resolve().parent.parent / "config" / "ua_list.txt"


def _load_user_agents() -> list[str]:
    if UA_PATH.exists():
        return [ua.strip() for ua in UA_PATH.read_text(encoding="utf-8").splitlines() if ua.strip()]
    # Fallback si le fichier n'existe pas
    return [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 13_5_1) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/118.0.0.0 Safari/537.36",
    ]


USER_AGENTS = _load_user_agents()


class BrowserPool:
    """Pool simple pour ouvrir des pages Playwright avec UA rotatif."""

    def __init__(self, headless: bool = True):
        self.headless = headless
        self._pw = None
        self._browser: Browser | None = None

    async def __aenter__(self):
        self._pw = await async_playwright().start()
        self._browser = await self._pw.chromium.launch(
            headless=self.headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-dev-shm-usage",
            ],
        )
        return self

    async def __aexit__(self, *exc):
        if self._browser:
            await self._browser.close()
        if self._pw:
            await self._pw.stop()

    async def new_page(self) -> Page:
        assert self._browser, "BrowserPool non initialisé"
        context = await self._browser.new_context(
            user_agent=random.choice(USER_AGENTS),
            viewport={"width": 1366, "height": 768},
        )
        page = await context.new_page()
        # Masquer navigator.webdriver
        await page.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined});"
        )
        return page


