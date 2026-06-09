"""
Module 1 - Domain Verification Engine and Blacklists.

Input: URL array from pre-processing.
Output: blocking_score in {0, 100} (deterministic one-to-one mapping).
"""

import asyncio
from dataclasses import dataclass

import httpx

from phishguard.config import AppConfig

SAFE_BROWSING_ENDPOINT = "https://safebrowsing.googleapis.com/v4/threatMatches:find"


@dataclass(frozen=True)
class DomainVerificationResult:
    """blocking_score: 0 = pass to Module 2, 100 = hard block."""

    blocking_score: int
    is_malicious: bool
    matched_urls: list[str]
    checked_urls: list[str]


class DomainVerificationEngine:
    """
    Async Lookup API v4 client.
    If at least one URL is in Google's malicious database -> score 100.
    Otherwise -> score 0 and downstream Module 2 may run.
    """

    def __init__(self, config: AppConfig) -> None:
        self.api_key = config.safe_browsing_api_key

    async def verify_urls(self, urls: list[str]) -> DomainVerificationResult:
        if not urls:
            return DomainVerificationResult(
                blocking_score=0,
                is_malicious=False,
                matched_urls=[],
                checked_urls=[],
            )

        if not self.api_key:
            return DomainVerificationResult(
                blocking_score=0,
                is_malicious=False,
                matched_urls=[],
                checked_urls=urls,
            )

        payload = {
            "client": {"clientId": "phishguard", "clientVersion": "1.0"},
            "threatInfo": {
                "threatTypes": [
                    "MALWARE",
                    "SOCIAL_ENGINEERING",
                    "UNWANTED_SOFTWARE",
                ],
                "platformTypes": ["ANY_PLATFORM"],
                "threatEntryTypes": ["URL"],
                "threatEntries": [{"url": url} for url in urls],
            },
        }

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                response = await client.post(
                    f"{SAFE_BROWSING_ENDPOINT}?key={self.api_key}",
                    json=payload,
                )
                response.raise_for_status()
                data = response.json()
        except Exception:
            return DomainVerificationResult(
                blocking_score=0,
                is_malicious=False,
                matched_urls=[],
                checked_urls=urls,
            )

        matches = data.get("matches", [])
        if not matches:
            return DomainVerificationResult(
                blocking_score=0,
                is_malicious=False,
                matched_urls=[],
                checked_urls=urls,
            )

        matched_urls: list[str] = []
        for match in matches:
            threat_url = match.get("threat", {}).get("url")
            if threat_url:
                matched_urls.append(threat_url)

        return DomainVerificationResult(
            blocking_score=100,
            is_malicious=True,
            matched_urls=matched_urls,
            checked_urls=urls,
        )

    def verify_urls_sync(self, urls: list[str]) -> DomainVerificationResult:
        return asyncio.run(self.verify_urls(urls))
