(() => {
  const COLS = 16;
  const ROWS = 40;
  const STORE_KEY = "cosmic-sheet-v1";

  const els = {
    wrap: document.getElementById("grid-wrap"),
    formula: document.getElementById("formula-bar"),
    addr: document.getElementById("addr-badge"),
    base: document.getElementById("base-input"),
    mode: document.getElementById("mode-select"),
    status: document.getElementById("status-main"),
    detail: document.getElementById("status-detail"),
    file: document.getElementById("file-input"),
    help: document.getElementById("help-dialog"),
    previewNum: document.getElementById("preview-num"),
    previewAop: document.getElementById("preview-aop"),
    ctx: document.getElementById("ctx-menu"),
  };

  const state = {
    base: 10,
    defaultMode: "num",
    cells: {},
    results: {},
    selected: "A1",
    editing: false,
    dirty: false,
    evaluating: false,
    evalQueued: false,
    formulaAddr: "A1",
    history: [],
    clipboard: "",
  };

  function colLetter(index) {
    let n = index + 1;
    let out = "";
    while (n) {
      const rem = (n - 1) % 26;
      out = String.fromCharCode(65 + rem) + out;
      n = Math.floor((n - 1) / 26);
    }
    return out;
  }

  function addrOf(col, row) {
    return `${colLetter(col)}${row + 1}`;
  }

  function parseAddr(addr) {
    const match = /^([A-Za-z]+)(\d+)$/.exec(addr);
    if (!match) return null;
    let col = 0;
    for (const ch of match[1].toUpperCase()) {
      col = col * 26 + (ch.charCodeAt(0) - 64);
    }
    return { col: col - 1, row: Number(match[2]) - 1 };
  }

  function cellRecord(addr) {
    return state.cells[addr] || { expr: "", output_mode: state.defaultMode };
  }

  function compactExpr(expr) {
    return String(expr || "").replace(/\s*\n\s*/g, " ⏎ ");
  }

  function truncate(text, max = 36) {
    const s = String(text || "");
    if (s.length <= max) return s;
    const head = Math.max(10, Math.floor(max * 0.55));
    const tail = Math.max(6, max - head - 1);
    return `${s.slice(0, head)}…${s.slice(-tail)}`;
  }

  function formulaIsFocused() {
    return document.activeElement === els.formula;
  }

  function setStatus(main, detail = "") {
    els.status.textContent = main;
    els.detail.textContent = detail;
  }

  function snapshot() {
    state.history.push(JSON.stringify({
      cells: state.cells,
      base: Number(els.base.value) || 10,
      defaultMode: state.defaultMode,
    }));
    if (state.history.length > 40) state.history.shift();
  }

  function persist() {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify({
        format: "cosmic-sheet",
        version: 1,
        base: Number(els.base.value) || 10,
        default_output_mode: state.defaultMode,
        cells: state.cells,
      }));
    } catch {
      /* quota / private mode */
    }
  }

  function line(className, text, title) {
    const div = document.createElement("div");
    div.className = className;
    div.textContent = text;
    if (title && title !== text) div.title = title;
    return div;
  }

  function paintCells() {
    document.querySelectorAll("td.cell").forEach((td) => {
      const addr = td.dataset.addr;
      const spec = cellRecord(addr);
      const result = state.results[addr];
      td.classList.toggle("selected", addr === state.selected);
      td.classList.toggle("has-formula", Boolean(spec.expr) && !(result && result.command));
      td.classList.toggle("is-error", Boolean(result && result.error));
      td.classList.toggle("command", Boolean(result && result.command));
      if (td.querySelector(".cell-editor")) return;

      const body = document.createElement("div");
      body.className = "cell-body" + (result && result.error ? " cell-error" : "");
      if (spec.expr) {
        body.appendChild(line("cell-src", compactExpr(spec.expr), spec.expr));
        if (result && result.primary) {
          const shown = truncate(compactExpr(result.primary));
          body.appendChild(line("cell-value", `→ ${shown}`, result.primary));
        }
        if (result && result.secondary && !result.error) {
          body.appendChild(line("cell-secondary", truncate(result.secondary), result.secondary));
        }
      }
      td.replaceChildren(body);
    });
  }

  function updatePreview(addr) {
    const spec = cellRecord(addr);
    const result = state.results[addr];
    els.previewNum.textContent = result && result.primary ? result.primary : "";
    els.previewAop.textContent = result && result.secondary && !result.error ? result.secondary : "";
    if (result && result.primary) {
      const extra = result.secondary ? `   ${truncate(result.secondary, 48)}` : "";
      els.detail.textContent = `${compactExpr(spec.expr)} → ${truncate(result.primary, 60)}${extra}`;
    } else {
      els.detail.textContent = spec.expr;
    }
  }

  function selectCell(addr) {
    state.selected = addr;
    els.addr.textContent = addr;
    if (!state.editing && !formulaIsFocused()) {
      els.formula.value = cellRecord(addr).expr;
      state.formulaAddr = addr;
    }
    paintCells();
    updatePreview(addr);
    hideCtx();
  }

  function startEdit(seed = null) {
    const addr = state.selected;
    const td = document.querySelector(`td.cell[data-addr="${addr}"]`);
    if (!td) return;
    state.editing = true;
    const input = document.createElement("textarea");
    input.className = "cell-editor";
    input.spellcheck = false;
    input.rows = 3;
    input.value = seed !== null ? seed : cellRecord(addr).expr;
    td.replaceChildren(input);
    input.focus();
    input.setSelectionRange(input.value.length, input.value.length);
    els.formula.value = input.value;
    input.addEventListener("input", () => {
      els.formula.value = input.value;
    });
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        commitEdit(true);
        moveSelection(0, 1);
      } else if (event.key === "Tab") {
        event.preventDefault();
        commitEdit(true);
        moveSelection(event.shiftKey ? -1 : 1, 0);
      } else if (event.key === "Escape") {
        event.preventDefault();
        cancelEdit();
      }
    });
  }

  function cancelEdit() {
    state.editing = false;
    els.formula.value = cellRecord(state.selected).expr;
    paintCells();
  }

  function commitEdit(evaluateAfter, addr = state.selected) {
    const editor = document.querySelector(`td.cell[data-addr="${addr}"] .cell-editor`);
    const expr = (editor ? editor.value : els.formula.value).trim();
    const previous = cellRecord(addr).expr;
    if (expr === previous) {
      if (addr === state.selected) state.editing = false;
      paintCells();
      if (evaluateAfter && expr) evaluateSheet();
      return;
    }
    snapshot();
    if (addr === state.selected) state.editing = false;
    const current = cellRecord(addr);
    if (!expr) {
      delete state.cells[addr];
      delete state.results[addr];
    } else {
      state.cells[addr] = {
        expr,
        output_mode: current.output_mode || state.defaultMode,
      };
    }
    state.dirty = true;
    paintCells();
    if (addr === state.selected) els.formula.value = expr;
    persist();
    if (evaluateAfter) evaluateSheet();
  }

  function moveSelection(dc, dr) {
    const pos = parseAddr(state.selected);
    if (!pos) return;
    const col = Math.max(0, Math.min(COLS - 1, pos.col + dc));
    const row = Math.max(0, Math.min(ROWS - 1, pos.row + dr));
    selectCell(addrOf(col, row));
  }

  function clearCell(addr) {
    if (!state.cells[addr]) return;
    snapshot();
    delete state.cells[addr];
    delete state.results[addr];
    state.dirty = true;
    if (addr === state.selected) els.formula.value = "";
    persist();
    paintCells();
    updatePreview(state.selected);
    evaluateSheet();
  }

  function toggleCellMode(addr) {
    const rec = cellRecord(addr);
    if (!rec.expr) return;
    snapshot();
    rec.output_mode = rec.output_mode === "aop" ? "num" : "aop";
    state.cells[addr] = rec;
    state.dirty = true;
    persist();
    evaluateSheet();
  }

  function errorDetail(err) {
    if (err == null) return "evaluate failed";
    if (typeof err === "string") return err;
    if (Array.isArray(err)) {
      return err.map((item) => item.msg || JSON.stringify(item)).join("; ");
    }
    return err.message || String(err);
  }

  async function evaluateSheet() {
    if (state.evaluating) {
      state.evalQueued = true;
      return;
    }
    state.evaluating = true;
    setStatus("Evaluating…");
    try {
      do {
        state.evalQueued = false;
        const payload = {
          base: Number(els.base.value) || 10,
          cells: state.cells,
        };
        const response = await fetch("/api/evaluate", {
          method: "POST",
          headers: { "Content-Type": "application/json" },
          body: JSON.stringify(payload),
        });
        if (!response.ok) {
          const err = await response.json().catch(() => ({ detail: response.statusText }));
          throw new Error(errorDetail(err.detail));
        }
        const data = await response.json();
        state.base = data.base;
        if (!formulaIsFocused()) els.base.value = String(data.base);
        state.results = data.cells || {};
        const n = Object.keys(state.cells).length;
        const vars = Object.keys(data.variables || {}).length;
        setStatus(`Evaluated ${n} cell${n === 1 ? "" : "s"} · base ${data.base}`, `${vars} bound names`);
      } while (state.evalQueued);
    } catch (err) {
      setStatus("Error", err.message || String(err));
    } finally {
      state.evaluating = false;
      if (state.evalQueued) {
        evaluateSheet();
        return;
      }
      paintCells();
      updatePreview(state.selected);
    }
  }

  function sheetPayload() {
    return {
      format: "cosmic-sheet",
      version: 1,
      base: Number(els.base.value) || 10,
      default_output_mode: state.defaultMode,
      cells: state.cells,
    };
  }

  function applySheet(data, { markDirty = false } = {}) {
    state.base = data.base || 10;
    state.defaultMode = data.default_output_mode || "num";
    state.cells = data.cells || {};
    state.results = {};
    els.base.value = String(state.base);
    els.mode.value = state.defaultMode;
    state.dirty = markDirty;
    selectCell("A1");
    persist();
    evaluateSheet();
  }

  function newSheet() {
    if (state.dirty && !confirm("Discard the current sheet?")) return;
    snapshot();
    applySheet({ base: 10, default_output_mode: "num", cells: {} });
    setStatus("New sheet");
  }

  function saveSheet() {
    const blob = new Blob([JSON.stringify(sheetPayload(), null, 2)], { type: "application/json" });
    const a = document.createElement("a");
    a.href = URL.createObjectURL(blob);
    a.download = "sheet.cosmic-sheet.json";
    a.click();
    URL.revokeObjectURL(a.href);
    state.dirty = false;
    persist();
    setStatus("Saved");
  }

  function demoSheet() {
    applySheet({
      base: 10,
      default_output_mode: "num",
      cells: {
        A1: { expr: "a * b", output_mode: "num" },
        B1: { expr: "$A1 + 1", output_mode: "num" },
        C1: { expr: "$A1 == c", output_mode: "num" },
        A2: { expr: "$x = c", output_mode: "num" },
        B2: { expr: "$x / a", output_mode: "num" },
        A3: { expr: "ba", output_mode: "num" },
        B3: { expr: "$A3 == 110", output_mode: "num" },
      },
    }, { markDirty: true });
    setStatus("Demo sheet loaded");
  }

  function undo() {
    const raw = state.history.pop();
    if (!raw) return;
    const snap = JSON.parse(raw);
    state.cells = snap.cells || {};
    state.defaultMode = snap.defaultMode || "num";
    els.base.value = String(snap.base || 10);
    els.mode.value = state.defaultMode;
    state.dirty = true;
    persist();
    selectCell(state.selected);
    evaluateSheet();
    setStatus("Undo");
  }

  async function copySource(addr = state.selected) {
    const text = cellRecord(addr).expr;
    state.clipboard = text;
    try {
      await navigator.clipboard.writeText(text);
      setStatus("Copied source");
    } catch {
      setStatus("Copied locally");
    }
  }

  async function copyResult(addr = state.selected) {
    const result = state.results[addr];
    const text = result && result.primary ? result.primary : "";
    if (!text) return;
    try {
      await navigator.clipboard.writeText(text);
      setStatus("Copied result");
    } catch {
      setStatus("Copy failed", "select the preview strip and copy");
    }
  }

  async function pasteInto(addr = state.selected) {
    let text = state.clipboard;
    try {
      const clip = await navigator.clipboard.readText();
      if (clip != null && clip !== "") text = clip;
    } catch {
      /* permission / empty */
    }
    if (!text) return;
    snapshot();
    state.cells[addr] = { expr: text.trim(), output_mode: state.defaultMode };
    state.dirty = true;
    if (addr === state.selected) els.formula.value = text.trim();
    persist();
    paintCells();
    evaluateSheet();
  }

  function hideCtx() {
    els.ctx.hidden = true;
  }

  function showCtx(event, addr) {
    selectCell(addr);
    els.ctx.hidden = false;
    els.ctx.style.left = `${Math.min(event.clientX, window.innerWidth - 180)}px`;
    els.ctx.style.top = `${Math.min(event.clientY, window.innerHeight - 180)}px`;
  }

  function buildGrid() {
    const table = document.createElement("table");
    table.className = "sheet";
    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    const corner = document.createElement("th");
    corner.className = "corner";
    headRow.appendChild(corner);
    for (let c = 0; c < COLS; c++) {
      const th = document.createElement("th");
      th.textContent = colLetter(c);
      headRow.appendChild(th);
    }
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    for (let r = 0; r < ROWS; r++) {
      const tr = document.createElement("tr");
      const rh = document.createElement("th");
      rh.textContent = String(r + 1);
      tr.appendChild(rh);
      for (let c = 0; c < COLS; c++) {
        const td = document.createElement("td");
        const addr = addrOf(c, r);
        td.className = "cell";
        td.dataset.addr = addr;
        td.addEventListener("mousedown", (event) => {
          if (event.button !== 0) return;
          if ((state.editing || formulaIsFocused()) && state.selected !== addr) {
            commitEdit(true);
          }
          selectCell(addr);
        });
        td.addEventListener("dblclick", () => startEdit());
        td.addEventListener("contextmenu", (event) => {
          event.preventDefault();
          showCtx(event, addr);
        });
        tr.appendChild(td);
      }
      tbody.appendChild(tr);
    }
    table.appendChild(tbody);
    els.wrap.replaceChildren(table);
    paintCells();
  }

  function onKey(event) {
    if (event.target === els.formula) return;
    if (event.target.tagName === "INPUT" || event.target.tagName === "SELECT" || event.target.tagName === "TEXTAREA") {
      return;
    }
    if (state.editing) return;

    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "z") {
      event.preventDefault();
      undo();
      return;
    }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "s") {
      event.preventDefault();
      saveSheet();
      return;
    }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "o") {
      event.preventDefault();
      els.file.click();
      return;
    }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "c") {
      event.preventDefault();
      copySource();
      return;
    }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "v") {
      event.preventDefault();
      pasteInto();
      return;
    }

    switch (event.key) {
      case "ArrowUp":
        event.preventDefault();
        moveSelection(0, -1);
        break;
      case "ArrowDown":
        event.preventDefault();
        moveSelection(0, 1);
        break;
      case "ArrowLeft":
        event.preventDefault();
        moveSelection(-1, 0);
        break;
      case "ArrowRight":
        event.preventDefault();
        moveSelection(1, 0);
        break;
      case "Enter":
        event.preventDefault();
        startEdit();
        break;
      case "F2":
        event.preventDefault();
        startEdit();
        break;
      case "Delete":
      case "Backspace":
        event.preventDefault();
        clearCell(state.selected);
        break;
      case "Tab":
        event.preventDefault();
        moveSelection(event.shiftKey ? -1 : 1, 0);
        break;
      default:
        if (event.key.length === 1 && !event.ctrlKey && !event.metaKey && !event.altKey) {
          event.preventDefault();
          startEdit(event.key);
        }
    }
  }

  els.formula.addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      commitEdit(true, state.formulaAddr || state.selected);
      moveSelection(0, 1);
      els.formula.value = cellRecord(state.selected).expr;
      state.formulaAddr = state.selected;
    } else if (event.key === "Escape") {
      els.formula.value = cellRecord(state.formulaAddr || state.selected).expr;
      els.formula.blur();
    }
  });

  els.formula.addEventListener("focus", () => {
    state.formulaAddr = state.selected;
  });

  els.formula.addEventListener("blur", () => {
    if (state.editing) return;
    const addr = state.formulaAddr || state.selected;
    const expr = els.formula.value.trim();
    if (expr !== (state.cells[addr]?.expr || "")) {
      commitEdit(true, addr);
    }
    els.formula.value = cellRecord(state.selected).expr;
    state.formulaAddr = state.selected;
  });

  els.base.addEventListener("change", () => {
    snapshot();
    state.dirty = true;
    persist();
    evaluateSheet();
  });

  els.mode.addEventListener("change", () => {
    snapshot();
    state.defaultMode = els.mode.value;
    for (const rec of Object.values(state.cells)) rec.output_mode = state.defaultMode;
    persist();
    evaluateSheet();
  });

  document.getElementById("btn-new").addEventListener("click", newSheet);
  document.getElementById("btn-save").addEventListener("click", saveSheet);
  document.getElementById("btn-open").addEventListener("click", () => els.file.click());
  document.getElementById("btn-recalc").addEventListener("click", () => evaluateSheet());
  document.getElementById("btn-demo").addEventListener("click", demoSheet);
  document.getElementById("btn-help").addEventListener("click", () => els.help.showModal());
  document.getElementById("help-close").addEventListener("click", () => els.help.close());
  els.file.addEventListener("change", async () => {
    const file = els.file.files[0];
    els.file.value = "";
    if (!file) return;
    try {
      applySheet(JSON.parse(await file.text()), { markDirty: false });
      setStatus(`Opened ${file.name}`);
    } catch (err) {
      setStatus("Could not open file", err.message || String(err));
    }
  });

  els.ctx.addEventListener("click", (event) => {
    const act = event.target.closest("button")?.dataset.act;
    hideCtx();
    if (act === "copy-expr") copySource();
    if (act === "copy-result") copyResult();
    if (act === "paste") pasteInto();
    if (act === "clear") clearCell(state.selected);
    if (act === "toggle-mode") toggleCellMode(state.selected);
  });

  document.addEventListener("click", (event) => {
    if (!els.ctx.contains(event.target)) hideCtx();
  });
  document.addEventListener("keydown", onKey);

  buildGrid();
  selectCell("A1");

  try {
    const saved = localStorage.getItem(STORE_KEY);
    if (saved) {
      const data = JSON.parse(saved);
      if (data && data.cells && Object.keys(data.cells).length) {
        applySheet(data);
        setStatus("Restored last sheet");
      }
    }
  } catch {
    setStatus("Ready");
  }
  if (!Object.keys(state.cells).length) {
    setStatus("Ready — same AoP core as Cosmic Scratchpad");
  }
})();
