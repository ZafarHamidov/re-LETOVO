/**
 * Zafar Academic Portfolio Dashboard
 * Module pattern — init(), renderKPIs(), renderEvidence(), renderProgress(), initTheme()
 */

const CHECKLIST_KEY = "zafar-portfolio-checklist";
const THEME_KEY     = "zafar-theme";
const VIEW_KEY      = "zafar-view-mode";

const sectionLinks = [
  ["hero",                "Intro"],
  ["kpi-strip",           "KPIs"],
  ["academic-overview",   "Academics"],
  ["key-metrics",         "Progress"],
  ["achievements",        "Achievements"],
  ["activities",          "Activities"],
  ["documents",           "Evidence"],
  ["admissions-readiness","Readiness"],
  ["missing",             "Gaps"],
  ["focus",               "Focus"],
  ["goals",               "Goals"],
  ["progress",            "Tracker"],
  ["calendar",            "Calendar"],
  ["plan",                "90 Days"],
  ["share",               "Share"],
];

const appState = {
  profile:  null,
  evidence: [],
  filter:   "all",
  viewMode: "personal",
};

const $ = (sel) => document.querySelector(sel);

/* ── Utilities ── */

function createElement(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined && text !== null) el.textContent = text;
  return el;
}

function titleCase(value) {
  return String(value)
    .replace(/_/g, " ")
    .replace(/-/g, " ")
    .replace(/\b\w/g, (c) => c.toUpperCase());
}

function statusClass(status) {
  return `status-${String(status).replace(/\s+/g, "-").toLowerCase()}`;
}

function parseIsoDate(value) {
  if (!value || typeof value !== "string") return null;
  const m = value.match(/^(\d{4})-(\d{2})-(\d{2})$/);
  if (!m) return null;
  const d = new Date(Number(m[1]), Number(m[2]) - 1, Number(m[3]));
  return Number.isNaN(d.getTime()) ? null : d;
}

function toLocalIsoDate(date) {
  return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, "0")}-${String(date.getDate()).padStart(2, "0")}`;
}

function formatDateLabel(value) {
  const d = parseIsoDate(value);
  if (!d) return value;
  return d.toLocaleDateString("en-US", { month: "short", day: "numeric", year: "numeric" });
}

function buildCountdownLabel(value) {
  const target = new Date(`${value}T00:00:00`);
  if (Number.isNaN(target.getTime())) return "Date needs review";
  const now   = new Date();
  const today = new Date(now.getFullYear(), now.getMonth(), now.getDate());
  const diff  = Math.round((target - today) / 86400000);
  if (diff > 1)  return `${diff} days left`;
  if (diff === 1) return "1 day left";
  if (diff === 0) return "Today";
  if (diff === -1) return "1 day ago";
  return `${Math.abs(diff)} days ago`;
}

async function loadJson(path) {
  const res = await fetch(path);
  if (!res.ok) throw new Error(`Failed to load ${path}: ${res.status}`);
  return res.json();
}

/* ── initTheme ──
   Reads localStorage("zafar-theme"), defaults to "dark".
   Applies data-theme to <html>, wires the toggle button.
*/
function initTheme() {
  const stored = localStorage.getItem(THEME_KEY) || "dark";
  document.documentElement.dataset.theme = stored;

  const btn = $("#theme-toggle");
  btn.addEventListener("click", () => {
    const current = document.documentElement.dataset.theme;
    const next    = current === "dark" ? "light" : "dark";
    document.documentElement.dataset.theme = next;
    localStorage.setItem(THEME_KEY, next);
  });
}

/* ── initViewToggle ──
   Personal mode = show all sections (incl. .personal-only)
   Admissions mode = hide .personal-only sections
*/
function initViewToggle() {
  const stored  = localStorage.getItem(VIEW_KEY) || "personal";
  appState.viewMode = stored;
  applyViewMode(stored);

  const buttons = document.querySelectorAll(".view-btn");
  buttons.forEach((btn) => {
    if (btn.dataset.mode === stored) btn.classList.add("is-active");
    else btn.classList.remove("is-active");

    btn.addEventListener("click", () => {
      const mode = btn.dataset.mode;
      appState.viewMode = mode;
      localStorage.setItem(VIEW_KEY, mode);
      applyViewMode(mode);
      buttons.forEach((b) => b.classList.toggle("is-active", b.dataset.mode === mode));
    });
  });
}

function applyViewMode(mode) {
  document.body.classList.toggle("mode-admissions", mode === "admissions");
}

/* ── renderTopNav ── */
function renderTopNav() {
  const nav = $("#topnav");
  sectionLinks.forEach(([href, label]) => {
    const a  = createElement("a", "", label);
    a.href   = `#${href}`;
    nav.append(a);
  });
}

/* ── renderItemCard ──
   Used by all list sections; reads from #item-template.
*/
function renderItemCard({ title, body, status, link, previewImage, previewAlt }) {
  const node = $("#item-template").content.firstElementChild.cloneNode(true);
  node.querySelector(".list-item-title").textContent = title;
  node.querySelector(".list-item-body").textContent  = body || "";

  const pill = node.querySelector(".status-pill");
  if (status) {
    pill.textContent = titleCase(status);
    pill.classList.add(statusClass(status));
  } else {
    pill.remove();
  }

  const linkNode = node.querySelector(".file-link");
  if (link) {
    linkNode.href = encodeURI(link);
  } else {
    linkNode.remove();
  }

  if (previewImage) {
    const img = document.createElement("img");
    img.className = "list-item-preview";
    img.src       = encodeURI(previewImage);
    img.alt       = previewAlt || `${title} preview`;
    img.loading   = "lazy";
    if (linkNode.parentNode) linkNode.before(img);
    else node.append(img);
  }

  return node;
}

function renderList(containerSelector, items, mapper) {
  const container = $(containerSelector);
  if (!container) return;
  items.forEach((item) => container.append(mapper(item)));
}

/* ── renderHero ── */
function renderHero(profile) {
  const s = profile.student;
  $("#student-name").textContent     = s.name;
  $("#hero-summary").textContent     = s.hero_summary;
  $("#badge-score").textContent      = profile.readiness.estimated_score;
  $("#readiness-score").textContent  = profile.readiness.estimated_score;
  $("#readiness-disclaimer").textContent = profile.readiness.disclaimer;
  $("#readiness-donut").style.setProperty("--score", profile.readiness.estimated_score);

  $("#vision-label").textContent     = profile.vision_panel.label;
  $("#vision-title").textContent     = profile.vision_panel.title;
  $("#vision-summary").textContent   = profile.vision_panel.summary;
  $("#target-score").textContent     = profile.vision_panel.target_score;
  $("#target-score-visual").textContent = profile.vision_panel.target_score;
  $("#target-note").textContent      = profile.vision_panel.target_note;
  $("#target-donut").style.setProperty("--score", profile.vision_panel.target_score);

  s.focus_areas.forEach((area) =>
    $("#focus-tags").append(createElement("span", "tag", area))
  );

  const photoFrame = $("#hero-photo-frame");
  const photo      = $("#student-photo");
  if (s.photo) {
    photo.src = encodeURI(s.photo);
  } else {
    photoFrame.hidden = true;
  }

  const idealFrame = $("#hero-ideal-frame");
  const idealImg   = $("#ideal-visual");
  if (s.ideal_image) {
    idealImg.src = encodeURI(s.ideal_image);
  } else {
    idealFrame.hidden = true;
  }
}

/* ── renderKPIs ──
   4 metric cards: readiness %, evidence count, strongest area, next action.
*/
function renderKPIs(profile, evidence) {
  // 1. Readiness %
  $("#kpi-readiness-value").textContent = `${profile.readiness.estimated_score}%`;

  // 2. Evidence count
  $("#kpi-evidence-value").textContent = evidence.length;

  // 3. Strongest area (highest scoring component)
  const components = profile.readiness.components || [];
  const strongest  = components.reduce(
    (best, c) => (c.score > (best?.score ?? 0) ? c : best),
    null
  );
  if (strongest) {
    $("#kpi-strength-value").textContent = strongest.label;
    $("#kpi-strength-score").textContent = `${strongest.score}/100`;
  }

  // 4. Next action (first from next_actions list)
  const nextActions = profile.admissions_gap_analysis?.next_actions || [];
  if (nextActions.length) {
    const text = nextActions[0];
    // Truncate for display
    $("#kpi-next-value").textContent =
      text.length > 80 ? text.slice(0, 77) + "…" : text;
  }
}

/* ── renderMeta ── */
function renderMeta(profile) {
  const s = profile.student;
  [
    ["School",           s.school],
    ["Current stage",    s.grade_level],
    ["Program context",  s.program_context],
    ["Location context", s.location_context],
  ].forEach(([label, value]) => {
    const card = createElement("article", "meta-card");
    card.append(
      createElement("p", "meta-label", label),
      createElement("p", "meta-value", value)
    );
    $("#student-meta").append(card);
  });
}

/* ── renderProgress ──
   Bar chart per category from normalized_profile.json (= profile.json readiness.components).
*/
function renderProgress(profile) {
  // Metric count cards
  [
    ["Olympiads",     profile.olympiads.length],
    ["Activities",    profile.activities.length],
    ["Certificates",  profile.certificates.length],
    ["Goal records",  profile.goals.length],
  ].forEach(([label, value]) => {
    const card = createElement("article", "metric-card");
    card.append(
      createElement("p", "meta-label", label),
      createElement("strong", "", String(value))
    );
    $("#metrics-grid").append(card);
  });

  // Category bar charts
  (profile.readiness.components || []).forEach((comp) => {
    const row  = createElement("article", "bar-row");
    const head = createElement("div", "bar-head");
    head.append(
      createElement("span", "", comp.label),
      createElement("span", "", `${comp.score}/100`)
    );
    const track = createElement("div", "bar-track");
    const fill  = createElement("div", "bar-fill");
    fill.style.width = `${comp.score}%`;
    track.append(fill);
    row.append(head, track, createElement("p", "caption", comp.reason));
    $("#strength-bars").append(row);
  });
}

/* ── renderEvidence ──
   Filterable evidence cards from evidence-index.json.
   Shows status badge (category) + type strength indicator.
*/
function renderEvidenceFilter() {
  const select = $("#evidence-filter");
  const categories = [...new Set(appState.evidence.map((i) => i.category))].sort();
  categories.forEach((cat) => {
    const opt       = document.createElement("option");
    opt.value       = cat;
    opt.textContent = titleCase(cat);
    select.append(opt);
  });
  select.addEventListener("change", () => {
    appState.filter = select.value;
    renderEvidence();
  });
}

function renderEvidence() {
  const grid = $("#evidence-grid");
  grid.innerHTML = "";

  const visible = appState.evidence.filter(
    (item) =>
      (appState.filter === "all" || item.category === appState.filter) &&
      item.type !== "html" &&
      item.type !== "mhtml"
  );

  visible.forEach((item) => {
    const card = createElement("article", "evidence-card");

    // Status badge = category
    const badge = createElement("span", "status-pill", titleCase(item.category));
    badge.classList.add("status-active");
    card.append(badge);

    card.append(createElement("h3", "", item.title));
    card.append(createElement("p", "", item.description || ""));

    // Strength indicator = file type
    const strength = createElement("p", "caption", `Type: ${item.type?.toUpperCase() ?? "—"}`);
    card.append(strength);

    const link      = createElement("a", "file-link", item.open_label || "Open file");
    link.href       = encodeURI(item.relative_path);
    link.target     = "_blank";
    link.rel        = "noreferrer";
    card.append(link);

    grid.append(card);
  });

  if (!visible.length) {
    grid.append(createElement("p", "caption", "No evidence matches the current filter."));
  }
}

/* ── Focus section ── (top 3 gaps / next steps; hidden in admissions mode) */
function renderFocus(profile) {
  const gaps = (profile.admissions_gap_analysis?.missing_items || []).slice(0, 3);
  const next = (profile.admissions_gap_analysis?.next_actions  || []).slice(0, 3);
  const container = $("#focus-gaps");

  if (!container) return;

  [...gaps, ...next].slice(0, 3).forEach((text, i) => {
    const item = createElement("article", "list-item");
    const head = createElement("div", "list-item-header");
    head.append(
      createElement("h3", "list-item-title focus-gap-title", `Gap ${i + 1}`),
      createElement("span", "status-pill status-missing", "Missing")
    );
    item.append(head, createElement("p", "list-item-body", text));
    container.append(item);
  });
}

/* ── renderTodo ── */
function renderTodo(profile) {
  const stored = JSON.parse(localStorage.getItem(CHECKLIST_KEY) || "{}");
  profile.todo_checklist.forEach((label, index) => {
    const wrapper  = createElement("label", "todo-item");
    const checkbox = document.createElement("input");
    checkbox.type    = "checkbox";
    checkbox.checked = Boolean(stored[index]);
    checkbox.addEventListener("change", () => {
      stored[index] = checkbox.checked;
      localStorage.setItem(CHECKLIST_KEY, JSON.stringify(stored));
    });
    wrapper.append(checkbox, createElement("span", "", label));
    $("#todo-list").append(wrapper);
  });
}

/* ── renderTimeline ── */
function renderTimeline(profile) {
  profile.next_90_days_plan.forEach((phase) => {
    const item = createElement("article", "timeline-item");
    item.append(
      createElement("p", "eyebrow", phase.window),
      createElement("h3", "", phase.focus)
    );
    const list = document.createElement("ul");
    phase.actions.forEach((action) => {
      const li = document.createElement("li");
      li.textContent = action;
      list.append(li);
    });
    item.append(list);
    $("#timeline").append(item);
  });
}

/* ── Calendar helpers ── */

function getMonthKey(value) {
  const d = new Date(`${value}T00:00:00`);
  return `${d.getFullYear()}-${String(d.getMonth() + 1).padStart(2, "0")}`;
}

function buildMonthLabel(key) {
  const [year, month] = key.split("-").map(Number);
  return new Date(year, month - 1, 1).toLocaleDateString("en-US", {
    month: "long", year: "numeric",
  });
}

function renderCalendarCard(entry) {
  const item = createElement("article", "calendar-item");

  const date = createElement("div", "calendar-date");
  date.append(createElement("strong", "", formatDateLabel(entry.date)));
  item.append(date);

  item.append(createElement("h3", "calendar-title", entry.title));
  item.append(createElement("p", "calendar-countdown", buildCountdownLabel(entry.date)));

  const meta = createElement("div", "calendar-meta");
  meta.append(createElement("span", "calendar-chip", titleCase(entry.kind)));
  meta.append(createElement("span", "calendar-chip", titleCase(entry.source_type)));
  if (entry.status) meta.append(createElement("span", "calendar-chip", titleCase(entry.status)));
  if (entry.session) meta.append(createElement("span", "calendar-chip", entry.session));
  if (entry.group)   meta.append(createElement("span", "calendar-chip", entry.group));
  item.append(meta);

  item.append(createElement("p", "caption", entry.summary || ""));

  if (entry.source_file) {
    const link  = createElement("a", "file-link", "Open related evidence");
    link.href   = encodeURI(entry.source_file);
    link.target = "_blank";
    link.rel    = "noreferrer";
    item.append(link);
  }
  return item;
}

function renderCalendarMonth(entries, monthKey) {
  $("#calendar-month-label").textContent = buildMonthLabel(monthKey);
  const grid = $("#calendar-grid");
  grid.innerHTML = "";

  const [year, month] = monthKey.split("-").map(Number);
  const firstDay      = new Date(year, month - 1, 1);
  const startWeekday  = firstDay.getDay();
  const monthStart    = new Date(year, month - 1, 1);
  const monthEnd      = new Date(year, month, 0);
  const calStart      = new Date(year, month - 1, 1 - startWeekday);

  const entryMap = new Map();
  entries.forEach((entry) => {
    const list = entryMap.get(entry.date) || [];
    list.push(entry);
    entryMap.set(entry.date, list);
  });

  const today    = new Date();
  const todayIso = toLocalIsoDate(new Date(today.getFullYear(), today.getMonth(), today.getDate()));

  for (let offset = 0; offset < 42; offset++) {
    const cur  = new Date(calStart);
    cur.setDate(calStart.getDate() + offset);
    const iso  = toLocalIsoDate(cur);
    const cell = createElement("article", "calendar-cell");

    if (cur < monthStart || cur > monthEnd) cell.classList.add("is-outside");
    if (iso === todayIso)                   cell.classList.add("is-today");

    cell.append(createElement("span", "calendar-day-number", String(cur.getDate())));

    const events = createElement("div", "calendar-day-events");
    (entryMap.get(iso) || []).forEach((entry) => {
      const dot   = createElement("span", "calendar-dot", entry.title);
      dot.title   = `${formatDateLabel(entry.date)}: ${entry.title}`;
      if (new Date(`${entry.date}T00:00:00`) < new Date(todayIso)) dot.classList.add("is-past");
      events.append(dot);
    });
    cell.append(events);
    grid.append(cell);
  }
}

function renderCalendar(profile) {
  $("#calendar-note").textContent = profile.exam_calendar.note || "";

  const entries  = [...profile.exam_calendar.entries].sort((a, b) => a.date.localeCompare(b.date));
  const today    = new Date();
  const todayIso = toLocalIsoDate(new Date(today.getFullYear(), today.getMonth(), today.getDate()));

  const futureEntries = entries.filter((e) => e.date >= todayIso);
  const pastEntries   = entries.filter((e) => e.date < todayIso).reverse();

  const futureContainer = $("#calendar-future");
  const pastContainer   = $("#calendar-past");
  futureContainer.innerHTML = "";
  pastContainer.innerHTML   = "";

  futureEntries.forEach((e) => futureContainer.append(renderCalendarCard(e)));
  pastEntries.forEach((e)   => pastContainer.append(renderCalendarCard(e)));

  if (!futureEntries.length)
    futureContainer.append(createElement("p", "caption", "No upcoming dated milestones yet."));
  if (!pastEntries.length)
    pastContainer.append(createElement("p", "caption", "No past milestones available."));

  const monthKeys    = [...new Set(entries.map((e) => getMonthKey(e.date)))];
  const defaultMonth = futureEntries.length
    ? getMonthKey(futureEntries[0].date)
    : monthKeys[monthKeys.length - 1];

  const pills = $("#calendar-month-pills");
  pills.innerHTML = "";

  if (!monthKeys.length) {
    $("#calendar-month-label").textContent = "No dated milestones";
    return;
  }

  monthKeys.forEach((key) => {
    const btn = createElement("button", "calendar-month-pill", buildMonthLabel(key));
    btn.type  = "button";
    if (key === defaultMonth) btn.classList.add("is-active");
    btn.addEventListener("click", () => {
      document.querySelectorAll(".calendar-month-pill").forEach((p) => p.classList.remove("is-active"));
      btn.classList.add("is-active");
      renderCalendarMonth(entries, key);
    });
    pills.append(btn);
  });

  if (defaultMonth) renderCalendarMonth(entries, defaultMonth);
}

/* ── wireActions ── */
function wireActions() {
  // Navigation panel
  const menuBtn  = $("#menu-button");
  const navPanel = $("#topnav-panel");

  const setNav = (open) => {
    navPanel.hidden = !open;
    menuBtn.textContent = open ? "Close" : "Nav";
    menuBtn.setAttribute("aria-expanded", String(open));
    menuBtn.setAttribute("aria-label", open ? "Close navigation" : "Open navigation");
  };

  menuBtn.addEventListener("click", () =>
    setNav(menuBtn.getAttribute("aria-expanded") !== "true")
  );
  navPanel.addEventListener("click", (e) => {
    if (e.target.closest("a")) setNav(false);
  });
  document.addEventListener("keydown", (e) => {
    if (e.key === "Escape") setNav(false);
  });

  // Copy link
  $("#copy-link-button").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      $("#copy-link-button").textContent = "Copied!";
      setTimeout(() => ($("#copy-link-button").textContent = "Copy share link"), 1600);
    } catch {
      $("#copy-link-button").textContent = "Copy failed";
    }
  });

  // Print
  $("#print-button").addEventListener("click", () => window.print());

  // MHTML workspace
  $("#open-mhtml-workspace").addEventListener("click", () =>
    window.open("./mhtml-viewer.html", "_blank", "noopener,noreferrer")
  );
}

/* ── init ── */
async function init() {
  initTheme();
  initViewToggle();
  renderTopNav();
  wireActions();

  try {
    const [profile, evidence] = await Promise.all([
      loadJson("./data/profile.json"),
      loadJson("./docs/evidence-index.json"),
    ]);

    appState.profile  = profile;
    appState.evidence = evidence;

    renderHero(profile);
    renderKPIs(profile, evidence);
    renderMeta(profile);
    renderProgress(profile);
    renderEvidenceFilter();
    renderEvidence();
    renderFocus(profile);
    renderTodo(profile);
    renderCalendar(profile);
    renderTimeline(profile);

    // Academic records
    renderList("#academics-list", profile.academics, (item) =>
      renderItemCard({
        title:  `${item.subject} — ${item.period}`,
        body:   (item.teacher_comment ?? "Evidence available for manual review.") +
                (item.needs_review ? " Marked for manual confirmation." : ""),
        status: item.needs_review ? "needs review" : item.grade,
        link:   item.evidence_link,
      })
    );

    // Olympiads
    renderList("#olympiads-list", profile.olympiads, (item) =>
      renderItemCard({
        title:  item.title,
        body:   `${item.result} at ${item.level} level. Date: ${item.date}.`,
        status: item.result.toLowerCase(),
        link:   item.evidence_link,
      })
    );

    // Certificates
    renderList("#certificates-list", profile.certificates, (item) =>
      renderItemCard({
        title:  item.title,
        body:   `${item.issuer}. Date: ${item.date}.`,
        status: "verified",
        link:   item.evidence_link,
      })
    );

    // Activities
    renderList("#activities-list", profile.activities, (item) =>
      renderItemCard({
        title:        item.name,
        body:         `${item.role}. ${item.impact}`,
        status:       "active",
        link:         item.evidence_link,
        previewImage: item.preview_image,
        previewAlt:   item.preview_alt,
      })
    );

    // Commentary signals (may be empty)
    renderList("#signals-list", profile.commentary_signals || [], (item) =>
      renderItemCard({
        title:  titleCase(item.theme),
        body:   item.summary,
        status: "evidence-backed",
        link:   item.source_file,
      })
    );

    // Admissions gap analysis
    renderList("#strengths-list", profile.admissions_gap_analysis.strengths, (item) =>
      renderItemCard({ title: "Strength", body: item, status: "completed" })
    );
    renderList("#weaknesses-list", profile.admissions_gap_analysis.weaknesses, (item) =>
      renderItemCard({ title: "Growth area", body: item, status: "in progress" })
    );
    renderList("#missing-list", profile.admissions_gap_analysis.missing_items, (item) =>
      renderItemCard({ title: "Missing", body: item, status: "missing" })
    );
    renderList("#next-actions-list", profile.admissions_gap_analysis.next_actions, (item) =>
      renderItemCard({ title: "Next action", body: item, status: "planned" })
    );

    // Goals
    renderList("#goals-list", profile.goals, (item) =>
      renderItemCard({
        title:  item.title,
        body:   `Deadline: ${item.deadline}.`,
        status: item.status,
        link:   item.source_file,
      })
    );

    // Progress tracker
    renderList("#progress-list", profile.progress_tracker, (item) =>
      renderItemCard({
        title:  item.title,
        body:   `Status: ${titleCase(item.status)}.`,
        status: item.status,
      })
    );

    // Privacy guidance
    renderList("#privacy-guidance", profile.privacy_guidance, (item) =>
      renderItemCard({ title: item.mode, body: item.guidance, status: "recommended" })
    );

    // Manual review items
    renderList("#review-list", profile.manual_review_items, (item) =>
      renderItemCard({ title: "Review item", body: item, status: "needs review" })
    );

  } catch (error) {
    $("#student-name").textContent  = "Profile data could not be loaded";
    $("#hero-summary").textContent  =
      "Serve the project from a local web server (e.g. npx serve .) so fetch() can load the JSON files.";
    console.error("[Portfolio]", error);
  }
}

init();
