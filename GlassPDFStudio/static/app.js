const categories = ["All", "Organize PDF", "Optimize PDF", "Convert PDF", "Edit PDF", "PDF Security", "PDF Intelligence"];
const API_BASE = window.location.protocol === "file:" ? "http://127.0.0.1:5055" : "";

const tools = [
  { id: "merge_pdf", name: "Merge PDF", category: "Organize PDF", icon: "merge", accept: ".pdf,application/pdf", multiple: true, minFiles: 2, options: [{ name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "split_pdf", name: "Split PDF", category: "Organize PDF", icon: "split", accept: ".pdf,application/pdf", options: [{ name: "ranges", label: "Ranges", type: "text", placeholder: "all or 1-3,5" }, { name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "remove_pages", name: "Remove Pages", category: "Organize PDF", icon: "remove", accept: ".pdf,application/pdf", options: [{ name: "pages", label: "Pages", type: "text", placeholder: "2,4-6" }, { name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "extract_pages", name: "Extract Pages", category: "Organize PDF", icon: "extract", accept: ".pdf,application/pdf", options: [{ name: "pages", label: "Pages", type: "text", placeholder: "1,3-5" }, { name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "organize_pdf", name: "Organize PDF", category: "Organize PDF", icon: "organize", accept: ".pdf,application/pdf", options: [{ name: "order", label: "Page order", type: "text", placeholder: "3,1,2,4-last" }, { name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "scan_to_pdf", name: "Scan to PDF", category: "Organize PDF", icon: "scan", accept: ".jpg,.jpeg,.png,.bmp,.tif,.tiff,.webp,image/*", multiple: true, options: [{ name: "enhance", label: "Enhance scans", type: "select", options: [["false", "Off"], ["true", "On"]] }] },
  { id: "compress_pdf", name: "Compress PDF", category: "Optimize PDF", icon: "compress", accept: ".pdf,application/pdf", options: [{ name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "repair_pdf", name: "Repair PDF", category: "Optimize PDF", icon: "repair", accept: ".pdf,application/pdf", options: [{ name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "ocr_pdf", name: "OCR PDF", category: "Optimize PDF", icon: "ocr", accept: ".pdf,application/pdf", options: [{ name: "language", label: "Language code", type: "text", value: "eng" }, { name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "jpg_to_pdf", name: "JPG to PDF", category: "Convert PDF", icon: "image", accept: ".jpg,.jpeg,.png,.bmp,.tif,.tiff,.webp,image/*", multiple: true, options: [{ name: "enhance", label: "Enhance images", type: "select", options: [["false", "Off"], ["true", "On"]] }] },
  { id: "word_to_pdf", name: "Word to PDF", category: "Convert PDF", icon: "doc", accept: ".docx,.doc,application/vnd.openxmlformats-officedocument.wordprocessingml.document" },
  { id: "powerpoint_to_pdf", name: "PowerPoint to PDF", category: "Convert PDF", icon: "slides", accept: ".pptx,.ppt,application/vnd.openxmlformats-officedocument.presentationml.presentation" },
  { id: "excel_to_pdf", name: "Excel to PDF", category: "Convert PDF", icon: "sheet", accept: ".xlsx,.xlsm,.xls,application/vnd.openxmlformats-officedocument.spreadsheetml.sheet" },
  { id: "html_to_pdf", name: "HTML to PDF", category: "Convert PDF", icon: "html", accept: ".html,.htm,text/html", optionalFiles: true, options: [{ name: "url", label: "URL", type: "url", placeholder: "https://example.com" }, { name: "html", label: "HTML", type: "textarea", placeholder: "<h1>Document</h1>", full: true }] },
  { id: "pdf_to_jpg", name: "PDF to JPG", category: "Convert PDF", icon: "image", accept: ".pdf,application/pdf", options: [{ name: "pages", label: "Pages", type: "text", placeholder: "all or 1-3" }, { name: "scale", label: "Scale", type: "select", options: [["1", "Standard"], ["2", "Sharp"], ["3", "Retina"], ["4", "Ultra"]] }, { name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "pdf_to_word", name: "PDF to Word", category: "Convert PDF", icon: "doc", accept: ".pdf,application/pdf", options: [{ name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "pdf_to_powerpoint", name: "PDF to PowerPoint", category: "Convert PDF", icon: "slides", accept: ".pdf,application/pdf", options: [{ name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "pdf_to_excel", name: "PDF to Excel", category: "Convert PDF", icon: "sheet", accept: ".pdf,application/pdf", options: [{ name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "pdf_to_pdfa", name: "PDF to PDF/A", category: "Convert PDF", icon: "archive", accept: ".pdf,application/pdf", options: [{ name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "rotate_pdf", name: "Rotate PDF", category: "Edit PDF", icon: "rotate", accept: ".pdf,application/pdf", options: [{ name: "angle", label: "Angle", type: "select", options: [["90", "90"], ["180", "180"], ["270", "270"]] }, { name: "pages", label: "Pages", type: "text", placeholder: "all or 1,3" }, { name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "page_numbers", name: "Page Numbers", category: "Edit PDF", icon: "number", accept: ".pdf,application/pdf", options: [{ name: "pattern", label: "Pattern", type: "text", value: "{page} / {total}" }, { name: "position", label: "Position", type: "select", options: [["bottom", "Bottom"], ["top", "Top"], ["bottom-right", "Bottom right"], ["bottom-left", "Bottom left"]] }, { name: "fontSize", label: "Size", type: "number", value: "12" }, { name: "pages", label: "Pages", type: "text", placeholder: "all" }] },
  { id: "watermark_pdf", name: "Watermark", category: "Edit PDF", icon: "watermark", accept: ".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/*", multiple: true, options: [{ name: "text", label: "Text", type: "text", value: "WATERMARK" }, { name: "position", label: "Position", type: "select", options: [["center", "Center"], ["top", "Top"], ["bottom", "Bottom"], ["bottom-right", "Bottom right"], ["bottom-left", "Bottom left"]] }, { name: "angle", label: "Angle", type: "number", value: "-30" }, { name: "fontSize", label: "Size", type: "number", value: "42" }, { name: "opacity", label: "Opacity", type: "number", value: "0.22", step: "0.05" }, { name: "color", label: "Color", type: "color", value: "#0f172a" }] },
  { id: "crop_pdf", name: "Crop PDF", category: "Edit PDF", icon: "crop", accept: ".pdf,application/pdf", options: [{ name: "margin", label: "Margin points", type: "number", value: "24" }, { name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "edit_pdf", name: "Edit PDF", category: "Edit PDF", icon: "edit", accept: ".pdf,application/pdf", options: [{ name: "text", label: "Text", type: "text", value: "New text" }, { name: "pages", label: "Pages", type: "text", placeholder: "1" }, { name: "x", label: "X", type: "number", value: "72" }, { name: "y", label: "Y", type: "number", value: "72" }, { name: "fontSize", label: "Size", type: "number", value: "16" }, { name: "color", label: "Color", type: "color", value: "#0f172a" }, { name: "rectangle", label: "Rectangle", type: "select", options: [["false", "Off"], ["true", "On"]] }] },
  { id: "pdf_forms", name: "PDF Forms", category: "Edit PDF", icon: "form", accept: ".pdf,application/pdf", optionalFiles: true, options: [{ name: "fields", label: "Fields JSON", type: "textarea", placeholder: "{\"name\":\"Ali\"}", full: true }, { name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "unlock_pdf", name: "Unlock PDF", category: "PDF Security", icon: "unlock", accept: ".pdf,application/pdf", options: [{ name: "password", label: "Current password", type: "password", placeholder: "Required for encrypted PDFs" }] },
  { id: "protect_pdf", name: "Protect PDF", category: "PDF Security", icon: "lock", accept: ".pdf,application/pdf", options: [{ name: "newPassword", label: "New password", type: "password", placeholder: "Required" }, { name: "sourcePassword", label: "Current password", type: "password", placeholder: "Optional" }] },
  { id: "sign_pdf", name: "Sign PDF", category: "PDF Security", icon: "sign", accept: ".pdf,.png,.jpg,.jpeg,.webp,application/pdf,image/*", multiple: true, options: [{ name: "text", label: "Signature text", type: "text", value: "Signed" }, { name: "position", label: "Position", type: "select", options: [["bottom-right", "Bottom right"], ["bottom-left", "Bottom left"], ["center", "Center"]] }, { name: "fontSize", label: "Size", type: "number", value: "24" }] },
  { id: "redact_pdf", name: "Redact PDF", category: "PDF Security", icon: "redact", accept: ".pdf,application/pdf", options: [{ name: "terms", label: "Terms", type: "textarea", placeholder: "secret\naccount number", full: true }, { name: "fill", label: "Fill", type: "color", value: "#050505" }, { name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "compare_pdf", name: "Compare PDF", category: "PDF Security", icon: "compare", accept: ".pdf,application/pdf", multiple: true, minFiles: 2, options: [{ name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "ai_summarizer", name: "AI Summarizer", category: "PDF Intelligence", icon: "brain", accept: ".pdf,application/pdf", options: [{ name: "sentences", label: "Sentences", type: "number", value: "8" }, { name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] },
  { id: "translate_pdf", name: "Translate PDF", category: "PDF Intelligence", icon: "translate", accept: ".pdf,application/pdf", options: [{ name: "target", label: "Target", type: "select", options: [["Spanish", "Spanish"], ["French", "French"], ["Urdu", "Urdu"], ["German", "German"]] }, { name: "password", label: "PDF password", type: "password", placeholder: "Optional" }] }
];

const iconPaths = {
  merge: "M8 7h8m-8 5h8m-8 5h8M4 5v14m16-14v14",
  split: "M12 3v18M5 7h5m-5 5h5m-5 5h5m4-10h5m-5 5h5m-5 5h5",
  remove: "M6 7h12M9 7v12m6-12v12M8 7l1-3h6l1 3",
  extract: "M12 3v12m0 0 4-4m-4 4-4-4M5 21h14",
  organize: "M4 8h16M4 16h16M8 4v8m8 0v8",
  scan: "M4 7V5h16v2M4 17v2h16v-2M7 12h10",
  compress: "M8 3v6H3m13-6v6h5M8 21v-6H3m13 6v-6h5",
  repair: "M14 7 17 4l3 3-3 3m-2-1-6 6M5 19l4-1 9-9-3-3-9 9-1 4Z",
  ocr: "M5 5h14v14H5zM8 9h8M8 13h5M8 17h7",
  image: "M5 5h14v14H5zM8 16l3-3 2 2 3-4 3 5M9 9h.1",
  doc: "M7 3h7l4 4v14H7zM14 3v5h5M9 13h6M9 17h6",
  slides: "M4 5h16v11H4zM8 21h8M12 16v5",
  sheet: "M5 4h14v16H5zM5 9h14M10 4v16M15 4v16M5 14h14",
  html: "M8 9 4 12l4 3m8-6 4 3-4 3M14 7l-4 10",
  archive: "M4 7h16v13H4zM4 7l2-4h12l2 4M9 11h6",
  rotate: "M4 12a8 8 0 1 0 3-6M4 5v7h7",
  number: "M8 7h8M8 12h8M8 17h8M5 7h.1M5 12h.1M5 17h.1",
  watermark: "M4 18 18 4M7 7h10v10H7z",
  crop: "M7 3v14h14M3 7h14v14",
  edit: "M4 20h4L19 9l-4-4L4 16zM13 7l4 4",
  form: "M6 3h12v18H6zM9 8h6M9 12h6M9 16h3",
  unlock: "M7 11h10v9H7zM9 11V8a3 3 0 0 1 5.7-1.3",
  lock: "M7 11h10v9H7zM9 11V8a3 3 0 0 1 6 0v3",
  sign: "M4 18c4 0 4-8 7-8 2 0 1 5 3 5 1 0 2-2 3-2 1 0 1 2 3 2M4 21h16",
  redact: "M5 6h14M5 12h14M5 18h14M8 5v14m8-14v14",
  compare: "M4 5h7v14H4zM13 5h7v14h-7zM7 9h1m0 4h1m7-4h1m0 4h1",
  brain: "M9 5a3 3 0 0 0-3 3 3 3 0 0 0 0 6 3 3 0 0 0 3 3m6-12a3 3 0 0 1 3 3 3 3 0 0 1 0 6 3 3 0 0 1-3 3M9 5v14m6-14v14",
  translate: "M4 5h9M9 5c-.4 4-2 7-5 9m3-5c1 2 3 4 6 5M15 19l4-10 4 10m-6.5-3h5",
  workflow: "M5 7h5v5H5zM14 12h5v5h-5zM10 9h4m-2 0v5",
  upload: "M12 17V4m0 0-5 5m5-5 5 5M5 20h14",
  play: "M8 5v14l11-7z",
  reset: "M4 12a8 8 0 1 0 3-6M4 5v7h7",
  spark: "M12 3l1.7 5.3L19 10l-5.3 1.7L12 17l-1.7-5.3L5 10l5.3-1.7z",
  download: "M12 4v12m0 0 4-4m-4 4-4-4M5 20h14"
};

let activeCategory = "All";
let activeTool = null;

const dom = {
  grid: document.getElementById("toolsGrid"),
  tabs: document.getElementById("categoryTabs"),
  search: document.getElementById("searchInput"),
  modal: document.getElementById("toolModal"),
  close: document.getElementById("closeModal"),
  modalTitle: document.getElementById("modalTitle"),
  modalCategory: document.getElementById("modalCategory"),
  modalIcon: document.getElementById("modalIcon"),
  form: document.getElementById("toolForm"),
  fileInput: document.getElementById("fileInput"),
  fileLabel: document.getElementById("fileLabel"),
  selectedFiles: document.getElementById("selectedFiles"),
  optionsGrid: document.getElementById("optionsGrid"),
  resetForm: document.getElementById("resetForm"),
  processButton: document.getElementById("processButton"),
  resultPanel: document.getElementById("resultPanel"),
  resultMessage: document.getElementById("resultMessage"),
  resultDetails: document.getElementById("resultDetails"),
  downloadLink: document.getElementById("downloadLink"),
  systemStatus: document.getElementById("systemStatus")
};

function icon(name) {
  return `<svg viewBox="0 0 24 24" aria-hidden="true"><path d="${iconPaths[name] || iconPaths.doc}"/></svg>`;
}

function hydrateIcons(root = document) {
  root.querySelectorAll("[data-icon]").forEach((node) => {
    node.innerHTML = icon(node.dataset.icon);
  });
}

function initTheme() {
  const saved = localStorage.getItem("glasspdf-theme") || "system";
  setTheme(saved);
  document.querySelectorAll("[data-theme-option]").forEach((button) => {
    button.addEventListener("click", () => setTheme(button.dataset.themeOption));
  });
  window.matchMedia("(prefers-color-scheme: dark)").addEventListener("change", () => {
    if ((localStorage.getItem("glasspdf-theme") || "system") === "system") setTheme("system");
  });
}

function setTheme(choice) {
  localStorage.setItem("glasspdf-theme", choice);
  const resolved = choice === "system" ? (window.matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light") : choice;
  document.documentElement.dataset.theme = resolved;
  document.querySelectorAll("[data-theme-option]").forEach((button) => {
    button.classList.toggle("active", button.dataset.themeOption === choice);
  });
}

function renderTabs() {
  dom.tabs.innerHTML = categories.map((category) => `<button type="button" class="${category === activeCategory ? "active" : ""}" data-category="${category}">${category}</button>`).join("");
  dom.tabs.querySelectorAll("button").forEach((button) => {
    button.addEventListener("click", () => {
      activeCategory = button.dataset.category;
      renderTabs();
      renderTools();
    });
  });
}

function renderTools() {
  const query = dom.search.value.trim().toLowerCase();
  const filtered = tools.filter((tool) => {
    const categoryOk = activeCategory === "All" || tool.category === activeCategory;
    const queryOk = !query || `${tool.name} ${tool.category}`.toLowerCase().includes(query);
    return categoryOk && queryOk;
  });
  dom.grid.innerHTML = filtered.map((tool, index) => `
    <button class="tool-card" style="animation-delay:${Math.min(index * 24, 300)}ms" type="button" data-tool="${tool.id}">
      <span class="tool-top">
        <span>
          <span class="tool-icon">${icon(tool.icon)}</span>
          <h3>${tool.name}</h3>
        </span>
        <span class="tool-arrow">${icon("play")}</span>
      </span>
      <span class="tool-bottom">
        <span class="tool-chip">${tool.category}</span>
        <span class="tool-chip">Local</span>
      </span>
    </button>
  `).join("");
  dom.grid.querySelectorAll("[data-tool]").forEach((button) => {
    button.addEventListener("click", () => openTool(button.dataset.tool));
  });
}

function openTool(id) {
  activeTool = tools.find((tool) => tool.id === id);
  if (!activeTool) return;
  dom.modalTitle.textContent = activeTool.name;
  dom.modalCategory.textContent = activeTool.category;
  dom.modalIcon.innerHTML = icon(activeTool.icon);
  dom.fileInput.value = "";
  dom.fileInput.accept = activeTool.accept || "";
  dom.fileInput.multiple = Boolean(activeTool.multiple);
  dom.fileLabel.textContent = activeTool.multiple ? "Select files" : (activeTool.optionalFiles ? "Select optional file" : "Select file");
  dom.selectedFiles.innerHTML = "";
  dom.optionsGrid.innerHTML = renderOptions(activeTool.options || []);
  dom.resultPanel.hidden = true;
  dom.downloadLink.hidden = true;
  dom.modal.hidden = false;
  hydrateIcons(dom.modal);
}

function renderOptions(options) {
  return options.map((option) => {
    const full = option.full ? " full" : "";
    const value = option.value ?? "";
    if (option.type === "textarea") {
      return `<label class="field${full}"><span>${option.label}</span><textarea name="${option.name}" rows="4" placeholder="${option.placeholder || ""}">${value}</textarea></label>`;
    }
    if (option.type === "select") {
      const items = (option.options || []).map(([val, label]) => `<option value="${val}" ${String(value) === String(val) ? "selected" : ""}>${label}</option>`).join("");
      return `<label class="field${full}"><span>${option.label}</span><select name="${option.name}">${items}</select></label>`;
    }
    const step = option.step ? ` step="${option.step}"` : "";
    return `<label class="field${full}"><span>${option.label}</span><input name="${option.name}" type="${option.type || "text"}" value="${value}" placeholder="${option.placeholder || ""}"${step}></label>`;
  }).join("");
}

function closeModal() {
  dom.modal.hidden = true;
  activeTool = null;
}

function updateFilesLabel(input, labelNode, pillsNode) {
  const files = Array.from(input.files || []);
  labelNode.textContent = files.length ? `${files.length} selected` : (activeTool?.multiple ? "Select files" : "Select file");
  if (pillsNode) {
    pillsNode.innerHTML = files.map((file) => `<span class="file-pill">${icon("doc")}<span>${file.name}</span></span>`).join("");
  }
}

function collectOptions(form) {
  const data = {};
  const fields = form.querySelectorAll("[name]");
  fields.forEach((field) => {
    if (field.type === "file") return;
    data[field.name] = field.value;
  });
  return data;
}

async function processTool(tool, files, options) {
  const formData = new FormData();
  formData.append("tool", tool.id);
  formData.append("options", JSON.stringify(options));
  files.forEach((file) => formData.append("files", file, file.name));
  const response = await fetch(`${API_BASE}/api/process`, { method: "POST", body: formData });
  const payload = await response.json();
  if (!response.ok || !payload.ok) throw new Error(payload.error || "Processing failed.");
  return payload;
}

function showBusy(message = "Processing") {
  dom.resultPanel.hidden = false;
  dom.resultPanel.classList.remove("done");
  dom.resultMessage.textContent = message;
  dom.resultDetails.innerHTML = "";
  dom.downloadLink.hidden = true;
}

function showResult(payload) {
  dom.resultPanel.classList.add("done");
  dom.resultMessage.textContent = payload.message || "Done.";
  dom.resultDetails.innerHTML = (payload.details || []).map((detail) => `<li>${detail}</li>`).join("");
  dom.downloadLink.href = payload.downloadUrl.startsWith("http") ? payload.downloadUrl : `${API_BASE}${payload.downloadUrl}`;
  dom.downloadLink.download = payload.filename;
  dom.downloadLink.hidden = false;
}

function showError(error) {
  dom.resultPanel.hidden = false;
  dom.resultPanel.classList.add("done");
  dom.resultMessage.textContent = error.message || String(error);
  dom.resultDetails.innerHTML = "";
  dom.downloadLink.hidden = true;
}

async function handleSubmit(event) {
  event.preventDefault();
  if (!activeTool) return;
  const files = Array.from(dom.fileInput.files || []);
  const minFiles = activeTool.minFiles || (activeTool.optionalFiles ? 0 : 1);
  if (files.length < minFiles) {
    showError(new Error(`Select at least ${minFiles} file${minFiles === 1 ? "" : "s"}.`));
    return;
  }
  showBusy();
  dom.processButton.disabled = true;
  try {
    const payload = await processTool(activeTool, files, collectOptions(dom.form));
    showResult(payload);
  } catch (error) {
    showError(error);
  } finally {
    dom.processButton.disabled = false;
  }
}

function wait(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function loadHealth(attempts = 8) {
  try {
    const response = await fetch(`${API_BASE}/api/health`);
    if (!response.ok) throw new Error("Health check failed.");
    const data = await response.json();
    dom.systemStatus.classList.add("ready");
    const parts = ["PDF engine ready"];
    if (!data.soffice) parts.push("Office fallback");
    if (!data.tesseract) parts.push("OCR fallback");
    dom.systemStatus.querySelector("span:last-child").textContent = parts.join(" | ");
  } catch (error) {
    if (attempts > 1) {
      await wait(800);
      return loadHealth(attempts - 1);
    }
    dom.systemStatus.classList.remove("ready");
    dom.systemStatus.querySelector("span:last-child").textContent = "Engine offline";
  }
}

function bindEvents() {
  dom.search.addEventListener("input", renderTools);
  dom.close.addEventListener("click", closeModal);
  dom.modal.addEventListener("click", (event) => {
    if (event.target === dom.modal) closeModal();
  });
  document.addEventListener("keydown", (event) => {
    if (event.key === "Escape" && !dom.modal.hidden) closeModal();
  });
  dom.fileInput.addEventListener("change", () => updateFilesLabel(dom.fileInput, dom.fileLabel, dom.selectedFiles));
  dom.resetForm.addEventListener("click", () => activeTool && openTool(activeTool.id));
  dom.form.addEventListener("submit", handleSubmit);
}

function init() {
  initTheme();
  hydrateIcons();
  renderTabs();
  renderTools();
  bindEvents();
  loadHealth();
}

init();
