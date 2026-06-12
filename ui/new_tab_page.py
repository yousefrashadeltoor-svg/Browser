"""
JO Browser — New Tab Page
A rich HTML dashboard served from the jo://newtab internal URL.
Features: clock, greeting, quick-access shortcuts, recent sites, search bar.
"""

import json
from datetime import datetime
from browser.utils import data_path


NEW_TAB_HTML = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>New Tab — JO Browser</title>
<style>
  :root {
    --accent: #6C63FF;
    --bg: #0d0d1a;
    --surface: #1e1e2e;
    --text: #e8e8f0;
    --text2: #9898b0;
    --border: #2a2a40;
    --radius: 14px;
  }
  * { box-sizing: border-box; margin: 0; padding: 0; }
  body {
    font-family: "Inter", "Segoe UI", sans-serif;
    background: var(--bg);
    color: var(--text);
    min-height: 100vh;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    overflow-x: hidden;
  }
  /* Background gradient animation */
  body::before {
    content: '';
    position: fixed;
    top: 0; left: 0; right: 0; bottom: 0;
    background: radial-gradient(ellipse at 20% 30%, rgba(108,99,255,.18) 0%, transparent 60%),
                radial-gradient(ellipse at 80% 70%, rgba(99,179,255,.10) 0%, transparent 60%);
    pointer-events: none;
    z-index: 0;
  }
  .container {
    position: relative;
    z-index: 1;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 36px;
    padding: 40px 24px;
    width: 100%;
    max-width: 900px;
  }
  /* Logo */
  .logo {
    display: flex;
    align-items: center;
    gap: 12px;
  }
  .logo-mark {
    width: 52px; height: 52px;
    background: linear-gradient(135deg, var(--accent), #a855f7);
    border-radius: 16px;
    display: flex; align-items: center; justify-content: center;
    font-size: 24px; font-weight: 900; color: #fff;
    box-shadow: 0 8px 32px rgba(108,99,255,.4);
  }
  .logo-text { font-size: 28px; font-weight: 800; letter-spacing: -0.5px; }
  .logo-text span { color: var(--accent); }
  /* Clock */
  .clock {
    text-align: center;
  }
  .time {
    font-size: 72px;
    font-weight: 700;
    letter-spacing: -2px;
    line-height: 1;
    background: linear-gradient(135deg, #e8e8f0, #9898b0);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
  }
  .date {
    font-size: 16px;
    color: var(--text2);
    margin-top: 6px;
  }
  /* Search */
  .search-wrap {
    width: 100%;
    max-width: 600px;
    position: relative;
  }
  .search-input {
    width: 100%;
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: 32px;
    padding: 16px 24px 16px 56px;
    font-size: 16px;
    color: var(--text);
    outline: none;
    transition: border-color .2s, box-shadow .2s;
  }
  .search-input:focus {
    border-color: var(--accent);
    box-shadow: 0 0 0 3px rgba(108,99,255,.15);
  }
  .search-icon {
    position: absolute;
    left: 20px; top: 50%;
    transform: translateY(-50%);
    color: var(--text2);
    font-size: 18px;
    pointer-events: none;
  }
  /* Quick Access */
  .section-title {
    font-size: 12px;
    font-weight: 600;
    letter-spacing: 1px;
    text-transform: uppercase;
    color: var(--text2);
    align-self: flex-start;
  }
  .shortcuts {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(100px, 1fr));
    gap: 12px;
    width: 100%;
  }
  .shortcut {
    background: var(--surface);
    border: 1px solid var(--border);
    border-radius: var(--radius);
    padding: 20px 12px;
    text-align: center;
    cursor: pointer;
    transition: background .15s, transform .15s, border-color .15s;
    text-decoration: none;
    color: var(--text);
  }
  .shortcut:hover {
    background: rgba(108,99,255,.1);
    border-color: var(--accent);
    transform: translateY(-2px);
  }
  .shortcut .icon { font-size: 28px; margin-bottom: 8px; display: block; }
  .shortcut .label { font-size: 12px; color: var(--text2); }
  /* Recent */
  .recent-list {
    width: 100%;
    display: flex;
    flex-direction: column;
    gap: 6px;
  }
  .recent-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    background: var(--surface);
    border-radius: 10px;
    cursor: pointer;
    border: 1px solid transparent;
    transition: border-color .15s;
    text-decoration: none;
    color: var(--text);
  }
  .recent-item:hover { border-color: var(--border); }
  .recent-item .favicon { width: 20px; height: 20px; border-radius: 4px; background: var(--border); display: flex; align-items: center; justify-content: center; font-size: 12px; }
  .recent-item .title { font-size: 13px; flex: 1; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
  .recent-item .url { font-size: 11px; color: var(--text2); white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 200px; }
  /* Footer */
  .footer { font-size: 11px; color: #444466; margin-top: 8px; }
</style>
</head>
<body>
<div class="container">
  <div class="logo">
    <div class="logo-mark">JO</div>
    <div class="logo-text"><span>JO</span> Browser</div>
  </div>

  <div class="clock">
    <div class="time" id="time">00:00</div>
    <div class="date" id="date">Monday, January 1</div>
  </div>

  <div class="search-wrap">
    <span class="search-icon">🔍</span>
    <input class="search-input" id="search" type="text" placeholder="Search or enter URL..." autofocus>
  </div>

  <div style="width:100%">
    <div class="section-title" style="margin-bottom:12px">Quick Access</div>
    <div class="shortcuts">
      <a class="shortcut" href="https://google.com"><span class="icon">🔍</span><span class="label">Google</span></a>
      <a class="shortcut" href="https://youtube.com"><span class="icon">▶️</span><span class="label">YouTube</span></a>
      <a class="shortcut" href="https://github.com"><span class="icon">🐙</span><span class="label">GitHub</span></a>
      <a class="shortcut" href="https://gmail.com"><span class="icon">📧</span><span class="label">Gmail</span></a>
      <a class="shortcut" href="https://drive.google.com"><span class="icon">💾</span><span class="label">Drive</span></a>
      <a class="shortcut" href="https://notion.so"><span class="icon">📝</span><span class="label">Notion</span></a>
      <a class="shortcut" href="https://twitter.com"><span class="icon">🐦</span><span class="label">Twitter</span></a>
      <a class="shortcut" href="https://reddit.com"><span class="icon">🤖</span><span class="label">Reddit</span></a>
    </div>
  </div>

  <div style="width:100%">
    <div class="section-title" style="margin-bottom:12px">Recent</div>
    <div class="recent-list" id="recent-list">
      <div style="color:#606078; font-size:13px; padding:10px;">History will appear here as you browse.</div>
    </div>
  </div>

  <div class="footer">JO Browser &middot; Premium browsing experience</div>
</div>

<script>
  // Clock
  function updateClock() {
    const now = new Date();
    document.getElementById('time').textContent =
      now.toLocaleTimeString('en-US', {hour:'2-digit', minute:'2-digit', hour12:false});
    document.getElementById('date').textContent =
      now.toLocaleDateString('en-US', {weekday:'long', month:'long', day:'numeric'});
  }
  updateClock();
  setInterval(updateClock, 1000);

  // Search
  document.getElementById('search').addEventListener('keydown', function(e) {
    if (e.key === 'Enter') {
      const val = this.value.trim();
      if (!val) return;
      const isUrl = /^https?:\\/\\//i.test(val) || /^[\\w-]+\\.[a-z]{2,}/i.test(val);
      window.location.href = isUrl
        ? (val.startsWith('http') ? val : 'https://' + val)
        : 'https://www.google.com/search?q=' + encodeURIComponent(val);
    }
  });

  // Shortcut clicks navigate via the browser omnibox
  document.querySelectorAll('.shortcut').forEach(el => {
    el.addEventListener('click', function(e) {
      e.preventDefault();
      window.location.href = this.href;
    });
  });
</script>
</body>
</html>"""


def get_new_tab_html(recent_sites: list[dict] = None) -> str:
    """Return the new tab HTML, optionally injecting recent sites."""
    html = NEW_TAB_HTML
    if recent_sites:
        items_html = ""
        for site in recent_sites[:6]:
            url = site.get("url", "")
            title = site.get("title", url)[:60]
            domain = url.split("/")[2] if "/" in url else url
            items_html += (
                f'<a class="recent-item" href="{url}">'
                f'<div class="favicon">🌐</div>'
                f'<span class="title">{title}</span>'
                f'<span class="url">{domain}</span>'
                f'</a>'
            )
        html = html.replace(
            '<div style="color:#606078; font-size:13px; padding:10px;">History will appear here as you browse.</div>',
            items_html,
        )
    return html
