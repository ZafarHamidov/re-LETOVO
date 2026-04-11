frontend-design redesign index.html, styles.css, and script.js into a dark academic portfolio dashboard for Zafar with a dark/light theme toggle.

THEME SYSTEM — TWO COMPLETE VERSIONS
- Implement both themes as CSS custom property sets on :root[data-theme="dark"] and :root[data-theme="light"]
- Default to dark on first load; persist choice in localStorage("zafar-theme")
- Toggle button: fixed top-right, icon-only (moon/sun using CSS shapes, no emoji, no CDN icons)
- Smooth transition: transition: background-color 0.25s, color 0.25s, border-color 0.25s on :root

Dark theme (academic, serious):
  --bg-page:     #111118      deep navy-black
  --bg-surface:  #1a1a28      card surfaces
  --bg-card:     #21212f      raised cards
  --text-primary:#e8e4d9      warm off-white
  --text-muted:  #6e6b60      muted ink
  --accent:      #4a7fa5      muted blue
  --border:      rgba(255,255,255,0.08)

Light theme (clean, admissions-ready):
  --bg-page:     #f5f0e8      warm parchment
  --bg-surface:  #fffcf5      cream surface
  --bg-card:     #ffffff      pure white cards
  --text-primary:#2c2820      dark ink
  --text-muted:  #8a7f6e      warm gray
  --accent:      #2e5f85      deeper blue
  --border:      rgba(0,0,0,0.1)

TOGGLE BUTTON SPEC
- Position: fixed top-right, 16px margin, z-index 100
- Size: 36x36px, border-radius 50%, border: 1px solid var(--border)
- Dark mode shows a sun shape (CSS circle + rays); light mode shows a crescent (two overlapping circles)
- No libraries, pure CSS shapes only
- On click: toggle data-theme on <html>, save to localStorage

DATA SOURCES (read-only, do not modify)
- data/profile.json            main profile
- docs/evidence-index.json     evidence items
- docs/normalized_profile.json scores/metrics
- docs/extracted_data.json     raw evidence

LAYOUT SECTIONS
1. Header       name, tagline, readiness score badge, theme toggle
2. KPI strip    4 metric cards: readiness %, evidence count, strongest area, next action
3. Evidence grid filterable cards from evidence-index.json, status badge + strength
4. Progress     bar chart per category from normalized_profile.json
5. Focus        top 3 gaps/next steps (hidden in portfolio mode)
6. View toggle  personal vs admissions/public mode (separate from theme toggle)

TECHNICAL CONSTRAINTS
- Pure static, vanilla JS only, no build step, no framework
- fetch() from relative paths for all JSON
- styles.css: all colors via CSS custom properties, no hardcoded hex outside :root blocks
- script.js: module pattern — init(), renderKPIs(), renderEvidence(), renderProgress(), initTheme()
- No CDN fonts — system serif stack: Georgia, "Times New Roman", serif
- Responsive: 1280px desktop, 768px tablet