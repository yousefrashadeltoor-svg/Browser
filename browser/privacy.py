"""
JO Browser — Privacy & Security Manager
Incognito profile management, cookie/cache clearing, safe-browsing hooks.
"""

import logging
from PyQt6.QtWebEngineCore import QWebEngineProfile, QWebEnginePage

log = logging.getLogger(__name__)

# Known tracker/ad domains — simplified list; extend as needed
BLOCKED_DOMAINS: set[str] = {
    "doubleclick.net", "googleadservices.com", "googlesyndication.com",
    "pagead2.googlesyndication.com", "ads.twitter.com", "pixel.facebook.com",
    "analytics.google.com", "hotjar.com", "mixpanel.com", "segment.io",
    "scorecardresearch.com", "criteo.com", "adnxs.com", "rubiconproject.com",
}

PHISHING_KEYWORDS = ["verify-account", "signin-secure", "update-billing",
                     "paypal-secure", "bank-verify", "account-suspended"]


class PrivacyManager:
    def __init__(self, settings):
        self._settings = settings

    # ---------- Profiles ----------

    def get_incognito_profile(self) -> QWebEngineProfile:
        """Return an off-the-record (incognito) profile."""
        profile = QWebEngineProfile()        # no name → off-the-record
        self._configure_profile(profile, incognito=True)
        return profile

    def get_normal_profile(self, name: str = "Default") -> QWebEngineProfile:
        profile = QWebEngineProfile(name)
        self._configure_profile(profile, incognito=False)
        return profile

    def _configure_profile(self, profile: QWebEngineProfile, incognito: bool):
        if self._settings.get("privacy.do_not_track", True):
            profile.setHttpAcceptLanguage("en-US,en;q=0.9")
        if incognito:
            profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.NoPersistentCookies
            )
        elif self._settings.get("privacy.block_third_party_cookies", False):
            profile.setPersistentCookiesPolicy(
                QWebEngineProfile.PersistentCookiesPolicy.ForcePersistentCookies
            )
        http_cache = self._settings.get("advanced.cache_size_mb", 256) * 1024 * 1024
        profile.setHttpCacheMaximumSize(http_cache)

    # ---------- Data Clearing ----------

    def clear_cookies(self, profile: QWebEngineProfile):
        profile.cookieStore().deleteAllCookies()
        log.info("Cleared cookies")

    def clear_cache(self, profile: QWebEngineProfile):
        profile.clearHttpCache()
        log.info("Cleared HTTP cache")

    def clear_all(self, profile: QWebEngineProfile):
        self.clear_cookies(profile)
        self.clear_cache(profile)

    # ---------- URL Safety ----------

    def is_tracker(self, url: str) -> bool:
        if not self._settings.get("privacy.do_not_track", True):
            return False
        from urllib.parse import urlparse
        host = urlparse(url).hostname or ""
        return any(host.endswith(d) for d in BLOCKED_DOMAINS)

    def phishing_warning(self, url: str) -> bool:
        """Return True if URL shows phishing signals — basic heuristic."""
        if not self._settings.get("privacy.safe_browsing", True):
            return False
        lower = url.lower()
        return any(kw in lower for kw in PHISHING_KEYWORDS)

    def force_https(self, url: str) -> str:
        """Upgrade http:// to https:// if HTTPS-only mode is on."""
        if self._settings.get("privacy.https_only", False) and url.startswith("http://"):
            return "https://" + url[7:]
        return url
