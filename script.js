const CHECKLIST_KEY = "zafar-portfolio-checklist";

const sectionLinks = [
  ["hero", "Intro"],
  ["academic-overview", "Academics"],
  ["key-metrics", "Metrics"],
  ["achievements", "Achievements"],
  ["activities", "Activities"],
  ["documents", "Evidence"],
  ["admissions-readiness", "Readiness"],
  ["missing", "Missing"],
  ["goals", "Goals"],
  ["progress", "Progress"],
  ["plan", "90 Days"],
  ["share", "Share"],
];

const appState = { profile: null, evidence: [], filter: "all" };

const $ = (selector) => document.querySelector(selector);

function createElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text) element.textContent = text;
  return element;
}

function titleCase(value) {
  return value.replace(/_/g, " ").replace(/\b\w/g, (char) => char.toUpperCase());
}

function statusClass(status) {
  return `status-${status.replace(/\s+/g, "-").toLowerCase()}`;
}

function renderTopNav() {
  const nav = $("#topnav");
  sectionLinks.forEach(([href, label]) => {
    const link = createElement("a", "", label);
    link.href = `#${href}`;
    nav.append(link);
  });
}

function renderItemCard({ title, body, status, link }) {
  const node = $("#item-template").content.firstElementChild.cloneNode(true);
  node.querySelector(".list-item-title").textContent = title;
  node.querySelector(".list-item-body").textContent = body;
  const statusPill = node.querySelector(".status-pill");
  if (status) {
    statusPill.textContent = titleCase(status);
    statusPill.classList.add(statusClass(status));
  } else {
    statusPill.remove();
  }
  const linkNode = node.querySelector(".file-link");
  if (link) {
    linkNode.href = encodeURI(link);
  } else {
    linkNode.remove();
  }
  return node;
}

function renderList(containerSelector, items, mapper) {
  const container = $(containerSelector);
  items.forEach((item) => container.append(mapper(item)));
}

function renderHero(profile) {
  $("#student-name").textContent = profile.student.name;
  $("#hero-summary").textContent = profile.student.hero_summary;
  profile.student.focus_areas.forEach((item) => $("#focus-tags").append(createElement("span", "tag", item)));
  $("#readiness-score").textContent = profile.readiness.estimated_score;
  $("#readiness-disclaimer").textContent = profile.readiness.disclaimer;
  $("#readiness-donut").style.setProperty("--score", profile.readiness.estimated_score);
}

function renderMeta(profile) {
  const items = [
    ["School", profile.student.school],
    ["Current stage", profile.student.grade_level],
    ["Program context", profile.student.program_context],
    ["Location context", profile.student.location_context],
  ];
  items.forEach(([label, value]) => {
    const card = createElement("article", "meta-card");
    card.append(createElement("p", "meta-label", label), createElement("p", "meta-value", value));
    $("#student-meta").append(card);
  });
}

function renderMetrics(profile) {
  [
    ["Olympiads", profile.olympiads.length],
    ["Activities", profile.activities.length],
    ["Certificates", profile.certificates.length],
    ["Goal records", profile.goals.length],
  ].forEach(([label, value]) => {
    const card = createElement("article", "metric-card");
    card.append(createElement("p", "meta-label", label), createElement("strong", "", String(value)));
    $("#metrics-grid").append(card);
  });

  profile.readiness.components.forEach((component) => {
    const row = createElement("article", "bar-row");
    const head = createElement("div", "bar-head");
    head.append(createElement("span", "", component.label), createElement("span", "", `${component.score}/100`));
    const track = createElement("div", "bar-track");
    const fill = createElement("div", "bar-fill");
    fill.style.width = `${component.score}%`;
    track.append(fill);
    row.append(head, track, createElement("p", "caption", component.reason));
    $("#strength-bars").append(row);
  });
}

function renderEvidenceFilter() {
  const select = $("#evidence-filter");
  [...new Set(appState.evidence.map((item) => item.category))]
    .sort()
    .forEach((category) => {
      const option = document.createElement("option");
      option.value = category;
      option.textContent = titleCase(category);
      select.append(option);
    });
  select.addEventListener("change", () => {
    appState.filter = select.value;
    renderEvidence();
  });
}

function renderEvidence() {
  const grid = $("#evidence-grid");
  grid.innerHTML = "";
  appState.evidence
    .filter((item) => appState.filter === "all" || item.category === appState.filter)
    .forEach((item) => {
      const card = createElement("article", "evidence-card");
      card.append(createElement("span", "status-pill", titleCase(item.category)));
      card.append(createElement("h3", "", item.title));
      card.append(createElement("p", "", item.description));
      card.append(createElement("p", "caption", `${item.type.toUpperCase()} · ${item.relative_path}`));
      const link = createElement("a", "file-link", "Open file");
      link.href = encodeURI(item.relative_path);
      link.target = "_blank";
      link.rel = "noreferrer";
      card.append(link);
      grid.append(card);
    });
}

function renderTodo(profile) {
  const stored = JSON.parse(localStorage.getItem(CHECKLIST_KEY) || "{}");
  profile.todo_checklist.forEach((label, index) => {
    const wrapper = createElement("label", "todo-item");
    const checkbox = document.createElement("input");
    checkbox.type = "checkbox";
    checkbox.checked = Boolean(stored[index]);
    checkbox.addEventListener("change", () => {
      stored[index] = checkbox.checked;
      localStorage.setItem(CHECKLIST_KEY, JSON.stringify(stored));
    });
    wrapper.append(checkbox, createElement("span", "", label));
    $("#todo-list").append(wrapper);
  });
}

function renderTimeline(profile) {
  profile.next_90_days_plan.forEach((phase) => {
    const item = createElement("article", "timeline-item");
    item.append(createElement("p", "eyebrow", phase.window), createElement("h3", "", phase.focus));
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

function wireActions() {
  $("#copy-link-button").addEventListener("click", async () => {
    try {
      await navigator.clipboard.writeText(window.location.href);
      $("#copy-link-button").textContent = "Link copied";
      setTimeout(() => ($("#copy-link-button").textContent = "Copy share link"), 1500);
    } catch {
      $("#copy-link-button").textContent = "Copy failed";
    }
  });
  $("#print-button").addEventListener("click", () => window.print());
}

async function loadJson(path) {
  const response = await fetch(path);
  if (!response.ok) throw new Error(`Failed to load ${path}`);
  return response.json();
}

async function init() {
  renderTopNav();
  wireActions();

  try {
    const [profile, evidence] = await Promise.all([loadJson("./data/profile.json"), loadJson("./docs/evidence-index.json")]);
    appState.profile = profile;
    appState.evidence = evidence;

    renderHero(profile);
    renderMeta(profile);
    renderMetrics(profile);
    renderEvidenceFilter();
    renderEvidence();
    renderTodo(profile);
    renderTimeline(profile);

    renderList("#academics-list", profile.academics, (item) =>
      renderItemCard({
        title: `${item.subject} · ${item.period}`,
        body: `${item.teacher_comment ?? "Evidence available for manual review."} ${item.needs_review ? "Marked for manual confirmation." : ""}`.trim(),
        status: item.needs_review ? "needs review" : item.grade,
        link: item.evidence_link,
      }),
    );
    renderList("#olympiads-list", profile.olympiads, (item) => renderItemCard({ title: item.title, body: `${item.result} at ${item.level} level. Period: ${item.date}.`, status: item.result.toLowerCase(), link: item.evidence_link }));
    renderList("#certificates-list", profile.certificates, (item) => renderItemCard({ title: item.title, body: `${item.issuer}. Date: ${item.date}.`, status: "verified", link: item.evidence_link }));
    renderList("#activities-list", profile.activities, (item) => renderItemCard({ title: item.name, body: `${item.role}. ${item.impact}`, status: "active", link: item.evidence_link }));
    renderList("#signals-list", profile.commentary_signals, (item) => renderItemCard({ title: titleCase(item.theme), body: item.summary, status: "evidence-backed", link: item.source_file }));
    renderList("#strengths-list", profile.admissions_gap_analysis.strengths, (item) => renderItemCard({ title: "Strength", body: item, status: "completed" }));
    renderList("#weaknesses-list", profile.admissions_gap_analysis.weaknesses, (item) => renderItemCard({ title: "Growth area", body: item, status: "in progress" }));
    renderList("#missing-list", profile.admissions_gap_analysis.missing_items, (item) => renderItemCard({ title: "Missing or weakly represented", body: item, status: "missing" }));
    renderList("#next-actions-list", profile.admissions_gap_analysis.next_actions, (item) => renderItemCard({ title: "Next action", body: item, status: "planned" }));
    renderList("#goals-list", profile.goals, (item) => renderItemCard({ title: item.title, body: `Deadline: ${item.deadline}.`, status: item.status, link: item.source_file }));
    renderList("#progress-list", profile.progress_tracker, (item) => renderItemCard({ title: item.title, body: `Current status: ${titleCase(item.status)}.`, status: item.status }));
    renderList("#privacy-guidance", profile.privacy_guidance, (item) => renderItemCard({ title: item.mode, body: item.guidance, status: "recommended" }));
    renderList("#review-list", profile.manual_review_items, (item) => renderItemCard({ title: "Review item", body: item, status: "needs review" }));
  } catch (error) {
    $("#student-name").textContent = "Profile data could not be loaded";
    $("#hero-summary").textContent = "Run the build step and open the project through a local web server so the dashboard can fetch its JSON data.";
    console.error(error);
  }
}

init();
