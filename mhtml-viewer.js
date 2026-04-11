const $ = (selector) => document.querySelector(selector);

function createElement(tag, className, text) {
  const element = document.createElement(tag);
  if (className) element.className = className;
  if (text) element.textContent = text;
  return element;
}

function renderViewerItem(item, onSelect) {
  const button = createElement("button", "viewer-item");
  button.type = "button";
  button.append(createElement("span", "viewer-item-title", item.title));
  button.append(createElement("span", "viewer-item-meta", item.summary));
  button.addEventListener("click", () => onSelect(item, button));
  return button;
}

function selectSnapshot(item, button) {
  document.querySelectorAll(".viewer-item.is-active").forEach((node) => node.classList.remove("is-active"));
  button.classList.add("is-active");
  $("#viewer-current-title").textContent = item.title;
  $("#viewer-document-placeholder").hidden = true;
  const frame = $("#viewer-frame");
  frame.hidden = false;
  frame.src = encodeURI(item.rendered_path);
}

async function init() {
  const response = await fetch("./docs/mhtml-reports.json");
  const mhtmlItems = await response.json();
  const list = $("#viewer-list");

  mhtmlItems.forEach((item) => {
    const button = renderViewerItem(item, (selected, node) => selectSnapshot(selected, node));
    list.append(button);
  });
}

init().catch((error) => {
  $("#viewer-current-title").textContent = "Could not load snapshots";
  console.error(error);
});
