(() => {
  const COLS = 26;
  const ROWS = 60;
  const STORE_KEY = "cosmic-sheet-v1";
  const DEFAULT_COL_W = 148;
  const DEFAULT_ROW_H = 62;
  const MIN_COL_W = 56;
  const MAX_COL_W = 720;
  const MIN_ROW_H = 28;
  const MAX_ROW_H = 400;

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
    sizeW: document.getElementById("size-w"),
    sizeH: document.getElementById("size-h"),
    fill: document.getElementById("fill-handle"),
  };

  const state = {
    base: 10,
    defaultMode: "num",
    cells: {},
    results: {},
    selected: "A1",
    anchor: "A1",
    editing: false,
    dirty: false,
    evaluating: false,
    evalQueued: false,
    formulaAddr: "A1",
    history: [],
    clipboard: "",
    clipOrigin: null,
    colWidths: {},
    rowHeights: {},
    defaultColW: DEFAULT_COL_W,
    defaultRowH: DEFAULT_ROW_H,
    lastRefAddr: null,
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

  function clamp(n, lo, hi) {
    const v = Number(n);
    if (!Number.isFinite(v)) return lo;
    return Math.min(hi, Math.max(lo, Math.round(v)));
  }

  function colWidth(col) {
    return state.colWidths[colLetter(col)] || state.defaultColW;
  }

  function rowHeight(row) {
    return state.rowHeights[String(row + 1)] || state.defaultRowH;
  }

  function selectionRect() {
    const a = parseAddr(state.anchor || state.selected);
    const b = parseAddr(state.selected);
    if (!a || !b) return { c0: 0, c1: 0, r0: 0, r1: 0 };
    return {
      c0: Math.min(a.col, b.col),
      c1: Math.max(a.col, b.col),
      r0: Math.min(a.row, b.row),
      r1: Math.max(a.row, b.row),
    };
  }

  function cellsInRect(rect) {
    const out = [];
    for (let r = rect.r0; r <= rect.r1; r++) {
      for (let c = rect.c0; c <= rect.c1; c++) out.push(addrOf(c, r));
    }
    return out;
  }

  function inRect(addr, rect) {
    const p = parseAddr(addr);
    return p && p.col >= rect.c0 && p.col <= rect.c1 && p.row >= rect.r0 && p.row <= rect.r1;
  }

  function shiftCellRefs(expr, dCol, dRow) {
    return String(expr || "").replace(/\$([A-Za-z]+)(\d+)\b/g, (all, letters, rowNum) => {
      const pos = parseAddr(letters + rowNum);
      if (!pos) return all;
      const col = pos.col + dCol;
      const row = pos.row + dRow;
      if (col < 0 || row < 0 || col >= COLS || row >= ROWS) return all;
      return `$${addrOf(col, row)}`;
    });
  }

  function charsForWidth(px) {
    return Math.max(8, Math.floor((px - 18) / 7.2));
  }

  function refsInExpr(expr) {
    const set = new Set();
    const s = String(expr || "");
    s.replace(/\$([A-Za-z]+)(\d+)\s*:\s*\$([A-Za-z]+)(\d+)/g, (all, a, ar, b, br) => {
      const p = parseAddr(a + ar);
      const q = parseAddr(b + br);
      if (!p || !q) return all;
      const c0 = Math.min(p.col, q.col);
      const c1 = Math.max(p.col, q.col);
      const r0 = Math.min(p.row, q.row);
      const r1 = Math.max(p.row, q.row);
      for (let r = r0; r <= r1; r++) {
        for (let c = c0; c <= c1; c++) set.add(addrOf(c, r));
      }
      return all;
    });
    s.replace(/\$([A-Za-z]+)(\d+)\b/g, (all, letters, rowNum) => {
      const pos = parseAddr(letters + rowNum);
      if (pos) set.add(addrOf(pos.col, pos.row));
      return all;
    });
    return set;
  }

  function rangeLabel() {
    const r = selectionRect();
    if (r.c0 === r.c1 && r.r0 === r.r1) return state.selected;
    return `${addrOf(r.c0, r.r0)}:${addrOf(r.c1, r.r1)}`;
  }

  function insertAtCaret(text) {
    const editor = document.querySelector(".cell-editor");
    const node = editor || els.formula;
    if (!node) return;
    const start = node.selectionStart ?? node.value.length;
    const end = node.selectionEnd ?? start;
    const before = node.value.slice(0, start);
    const after = node.value.slice(end);
    const pad = before && !/[\s+\-*/^=(:]$/.test(before) ? " " : "";
    node.value = `${before}${pad}${text}${after}`;
    const caret = (before + pad + text).length;
    node.focus();
    node.setSelectionRange(caret, caret);
    if (editor) els.formula.value = editor.value;
    else {
      const live = document.querySelector(".cell-editor");
      if (live) live.value = els.formula.value;
    }
    paintSelection();
  }

  function insertCellRef(addr) {
    state.lastRefAddr = addr;
    insertAtCaret(`$${addr}`);
  }

  function insertRangeRef(fromAddr, toAddr) {
    const a = parseAddr(fromAddr);
    const b = parseAddr(toAddr);
    if (!a || !b) {
      insertCellRef(toAddr);
      return;
    }
    const c0 = Math.min(a.col, b.col);
    const c1 = Math.max(a.col, b.col);
    const r0 = Math.min(a.row, b.row);
    const r1 = Math.max(a.row, b.row);
    if (c0 === c1 && r0 === r1) insertCellRef(toAddr);
    else {
      state.lastRefAddr = toAddr;
      insertAtCaret(`$${addrOf(c0, r0)}:$${addrOf(c1, r1)}`);
    }
  }

  function syncSizeInputs() {
    const pos = parseAddr(state.selected);
    if (!pos || !els.sizeW || !els.sizeH) return;
    els.sizeW.value = String(colWidth(pos.col));
    els.sizeH.value = String(rowHeight(pos.row));
  }

  function applySizes() {
    const table = els.wrap.querySelector("table.sheet");
    if (!table) return;
    const cols = table.querySelectorAll("col");
    if (cols[0]) {
      cols[0].style.width = "var(--row-head)";
    }
    for (let c = 0; c < COLS; c++) {
      const w = `${colWidth(c)}px`;
      if (cols[c + 1]) cols[c + 1].style.width = w;
    }
    table.querySelectorAll("thead th").forEach((th, i) => {
      if (i === 0) return;
      const w = `${colWidth(i - 1)}px`;
      th.style.width = w;
      th.style.minWidth = w;
      th.style.maxWidth = w;
    });
    table.querySelectorAll("tbody tr").forEach((tr, r) => {
      const h = `${rowHeight(r)}px`;
      tr.style.height = h;
      const rh = tr.querySelector("th");
      if (rh) rh.style.height = h;
      tr.querySelectorAll("td.cell").forEach((td, c) => {
        const w = `${colWidth(c)}px`;
        td.style.height = h;
        td.style.width = w;
        td.style.minWidth = w;
        td.style.maxWidth = w;
      });
    });
    syncSizeInputs();
    placeFillHandle();
  }

  function setColWidth(col, width, { record = true } = {}) {
    const letter = colLetter(col);
    const w = clamp(width, MIN_COL_W, MAX_COL_W);
    if (record) snapshot();
    if (w === state.defaultColW) delete state.colWidths[letter];
    else state.colWidths[letter] = w;
    state.dirty = true;
    applySizes();
    persist();
  }

  function setRowHeight(row, height, { record = true } = {}) {
    const key = String(row + 1);
    const h = clamp(height, MIN_ROW_H, MAX_ROW_H);
    if (record) snapshot();
    if (h === state.defaultRowH) delete state.rowHeights[key];
    else state.rowHeights[key] = h;
    state.dirty = true;
    applySizes();
    persist();
  }

  function resetColWidth(col) {
    snapshot();
    delete state.colWidths[colLetter(col)];
    state.dirty = true;
    applySizes();
    persist();
  }

  function resetRowHeight(row) {
    snapshot();
    delete state.rowHeights[String(row + 1)];
    state.dirty = true;
    applySizes();
    persist();
  }

  function startColResize(col, event) {
    event.preventDefault();
    event.stopPropagation();
    snapshot();
    const startX = event.clientX;
    const startW = colWidth(col);
    const handle = event.currentTarget;
    handle.classList.add("active");
    document.body.classList.add("resizing-col");
    const move = (ev) => {
      setColWidth(col, startW + (ev.clientX - startX), { record: false });
    };
    const up = () => {
      handle.classList.remove("active");
      document.body.classList.remove("resizing-col");
      document.removeEventListener("mousemove", move);
      document.removeEventListener("mouseup", up);
      persist();
    };
    document.addEventListener("mousemove", move);
    document.addEventListener("mouseup", up);
  }

  function startRowResize(row, event) {
    event.preventDefault();
    event.stopPropagation();
    snapshot();
    const startY = event.clientY;
    const startH = rowHeight(row);
    const handle = event.currentTarget;
    handle.classList.add("active");
    document.body.classList.add("resizing-row");
    const move = (ev) => {
      setRowHeight(row, startH + (ev.clientY - startY), { record: false });
    };
    const up = () => {
      handle.classList.remove("active");
      document.body.classList.remove("resizing-row");
      document.removeEventListener("mousemove", move);
      document.removeEventListener("mouseup", up);
      persist();
    };
    document.addEventListener("mousemove", move);
    document.addEventListener("mouseup", up);
  }

  function snapshot() {
    state.history.push(JSON.stringify({
      cells: state.cells,
      base: Number(els.base.value) || 10,
      defaultMode: state.defaultMode,
      colWidths: state.colWidths,
      rowHeights: state.rowHeights,
      defaultColW: state.defaultColW,
      defaultRowH: state.defaultRowH,
    }));
    if (state.history.length > 40) state.history.shift();
  }

  function persist() {
    try {
      localStorage.setItem(STORE_KEY, JSON.stringify(sheetPayload()));
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
      const pos = parseAddr(addr);
      td.classList.toggle("has-formula", Boolean(spec.expr) && !(result && result.command));
      td.classList.toggle("is-error", Boolean(result && result.error));
      td.classList.toggle("command", Boolean(result && result.command));
      if (td.querySelector(".cell-editor")) return;

      const wrap = pos && rowHeight(pos.row) >= 88;
      const maxChars = pos ? charsForWidth(colWidth(pos.col)) : 36;
      const body = document.createElement("div");
      body.className = "cell-body" + (result && result.error ? " cell-error" : "") + (wrap ? " wrap" : "");
      if (spec.expr) {
        body.appendChild(line("cell-src", wrap ? spec.expr : compactExpr(spec.expr), spec.expr));
        if (result && result.primary) {
          const shown = wrap ? result.primary : truncate(compactExpr(result.primary), maxChars);
          body.appendChild(line("cell-value", `→ ${shown}`, result.primary));
        }
        if (result && result.secondary && !result.error) {
          const shown = wrap ? result.secondary : truncate(result.secondary, maxChars);
          body.appendChild(line("cell-secondary", shown, result.secondary));
        }
      }
      td.replaceChildren(body);
    });
    paintSelection();
  }

  function paintSelection() {
    const rect = selectionRect();
    const live = state.editing || formulaIsFocused()
      ? els.formula.value
      : cellRecord(state.selected).expr;
    const refs = refsInExpr(live);
    document.querySelectorAll("td.cell").forEach((td) => {
      const addr = td.dataset.addr;
      td.classList.toggle("selected", addr === state.selected);
      td.classList.toggle("in-range", inRect(addr, rect));
      td.classList.toggle("is-ref", refs.has(addr) && addr !== state.selected);
    });
    document.querySelectorAll("thead th[data-col]").forEach((th) => {
      const col = Number(th.dataset.col);
      th.classList.toggle("in-range", col >= rect.c0 && col <= rect.c1);
    });
    document.querySelectorAll("tbody th[data-row]").forEach((th) => {
      const row = Number(th.dataset.row);
      th.classList.toggle("in-range", row >= rect.r0 && row <= rect.r1);
    });
    els.addr.textContent = rangeLabel();
    placeFillHandle();
  }

  function placeFillHandle() {
    const handle = els.fill;
    if (!handle) return;
    if (state.editing || formulaIsFocused()) {
      handle.hidden = true;
      return;
    }
    const rect = selectionRect();
    const end = addrOf(rect.c1, rect.r1);
    const td = document.querySelector(`td.cell[data-addr="${end}"]`);
    if (!td) {
      handle.hidden = true;
      return;
    }
    handle.hidden = false;
    const box = td.getBoundingClientRect();
    const wrap = els.wrap.getBoundingClientRect();
    handle.style.left = `${box.right - wrap.left + els.wrap.scrollLeft - 4}px`;
    handle.style.top = `${box.bottom - wrap.top + els.wrap.scrollTop - 4}px`;
  }

  function fillRange(targetRect) {
    const src = selectionRect();
    const srcW = src.c1 - src.c0 + 1;
    const srcH = src.r1 - src.r0 + 1;
    if (
      targetRect.c0 === src.c0 && targetRect.c1 === src.c1
      && targetRect.r0 === src.r0 && targetRect.r1 === src.r1
    ) {
      return;
    }
    snapshot();
    for (let r = targetRect.r0; r <= targetRect.r1; r++) {
      for (let c = targetRect.c0; c <= targetRect.c1; c++) {
        if (c >= src.c0 && c <= src.c1 && r >= src.r0 && r <= src.r1) continue;
        const srcC = src.c0 + ((c - targetRect.c0) % srcW);
        const srcR = src.r0 + ((r - targetRect.r0) % srcH);
        const srcAddr = addrOf(srcC, srcR);
        const rec = state.cells[srcAddr];
        if (!rec || !rec.expr) {
          delete state.cells[addrOf(c, r)];
          continue;
        }
        state.cells[addrOf(c, r)] = {
          expr: shiftCellRefs(rec.expr, c - srcC, r - srcR),
          output_mode: rec.output_mode || state.defaultMode,
        };
      }
    }
    state.dirty = true;
    persist();
    paintCells();
    evaluateSheet();
  }

  function startFillDrag(event) {
    event.preventDefault();
    event.stopPropagation();
    const src = selectionRect();
    let hover = { ...src };
    const move = (ev) => {
      const el = document.elementFromPoint(ev.clientX, ev.clientY);
      const td = el && el.closest && el.closest("td.cell");
      if (!td) return;
      const p = parseAddr(td.dataset.addr);
      if (!p) return;
      hover = {
        c0: Math.min(src.c0, p.col),
        c1: Math.max(src.c1, p.col),
        r0: Math.min(src.r0, p.row),
        r1: Math.max(src.r1, p.row),
      };
      document.querySelectorAll("td.cell").forEach((cell) => {
        cell.classList.toggle("fill-target", inRect(cell.dataset.addr, hover));
      });
    };
    const up = () => {
      document.removeEventListener("mousemove", move);
      document.removeEventListener("mouseup", up);
      document.querySelectorAll("td.cell.fill-target").forEach((cell) => cell.classList.remove("fill-target"));
      fillRange(hover);
      state.anchor = addrOf(hover.c0, hover.r0);
      state.selected = addrOf(hover.c1, hover.r1);
      paintCells();
      updatePreview(state.selected);
    };
    document.addEventListener("mousemove", move);
    document.addEventListener("mouseup", up);
  }

  function fillDown() {
    const r = selectionRect();
    if (r.r1 === r.r0) {
      const target = { ...r, r1: Math.min(ROWS - 1, r.r1 + 1) };
      fillRange(target);
      state.anchor = addrOf(r.c0, r.r0);
      state.selected = addrOf(r.c1, target.r1);
      paintCells();
      return;
    }
    const savedA = state.anchor;
    const savedS = state.selected;
    state.anchor = addrOf(r.c0, r.r0);
    state.selected = addrOf(r.c1, r.r0);
    fillRange(r);
    state.anchor = savedA;
    state.selected = savedS;
    paintCells();
    updatePreview(state.selected);
  }

  function fillRight() {
    const r = selectionRect();
    if (r.c1 === r.c0) {
      const target = { ...r, c1: Math.min(COLS - 1, r.c1 + 1) };
      fillRange(target);
      state.anchor = addrOf(r.c0, r.r0);
      state.selected = addrOf(target.c1, r.r1);
      paintCells();
      return;
    }
    const savedA = state.anchor;
    const savedS = state.selected;
    state.anchor = addrOf(r.c0, r.r0);
    state.selected = addrOf(r.c0, r.r1);
    fillRange(r);
    state.anchor = savedA;
    state.selected = savedS;
    paintCells();
    updatePreview(state.selected);
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

  function selectCell(addr, { extend = false, keepRange = false, scroll = true } = {}) {
    if (!extend && !keepRange) state.anchor = addr;
    state.selected = addr;
    if (!state.editing && !formulaIsFocused()) {
      els.formula.value = cellRecord(addr).expr;
      state.formulaAddr = addr;
    }
    paintSelection();
    updatePreview(addr);
    syncSizeInputs();
    hideCtx();
    if (scroll) {
      const td = document.querySelector(`td.cell[data-addr="${addr}"]`);
      if (td) td.scrollIntoView({ block: "nearest", inline: "nearest" });
    }
  }

  function startRangeDrag() {
    document.body.classList.add("selecting-range");
    const move = (event) => {
      const el = document.elementFromPoint(event.clientX, event.clientY);
      const td = el && el.closest && el.closest("td.cell");
      if (!td) return;
      const addr = td.dataset.addr;
      if (addr && addr !== state.selected) selectCell(addr, { extend: true, scroll: false });
    };
    const up = () => {
      document.body.classList.remove("selecting-range");
      document.removeEventListener("mousemove", move);
      document.removeEventListener("mouseup", up);
    };
    document.addEventListener("mousemove", move);
    document.addEventListener("mouseup", up);
  }

  function selectColumnRange(c0, c1) {
    const a = Math.min(c0, c1);
    const b = Math.max(c0, c1);
    state.anchor = addrOf(a, 0);
    state.selected = addrOf(b, ROWS - 1);
    paintSelection();
    updatePreview(state.selected);
    syncSizeInputs();
    hideCtx();
  }

  function selectRowRange(r0, r1) {
    const a = Math.min(r0, r1);
    const b = Math.max(r0, r1);
    state.anchor = addrOf(0, a);
    state.selected = addrOf(COLS - 1, b);
    paintSelection();
    updatePreview(state.selected);
    syncSizeInputs();
    hideCtx();
  }

  function startColHeaderDrag(col, event) {
    if (event.target.closest(".col-resizer")) return;
    event.preventDefault();
    selectColumnRange(col, col);
    const move = (ev) => {
      const el = document.elementFromPoint(ev.clientX, ev.clientY);
      const th = el && el.closest && el.closest("thead th[data-col]");
      if (th) selectColumnRange(col, Number(th.dataset.col));
    };
    const up = () => {
      document.removeEventListener("mousemove", move);
      document.removeEventListener("mouseup", up);
    };
    document.addEventListener("mousemove", move);
    document.addEventListener("mouseup", up);
  }

  function startRowHeaderDrag(row, event) {
    if (event.target.closest(".row-resizer")) return;
    event.preventDefault();
    selectRowRange(row, row);
    const move = (ev) => {
      const el = document.elementFromPoint(ev.clientX, ev.clientY);
      const th = el && el.closest && el.closest("tbody th[data-row]");
      if (th) selectRowRange(row, Number(th.dataset.row));
    };
    const up = () => {
      document.removeEventListener("mousemove", move);
      document.removeEventListener("mouseup", up);
    };
    document.addEventListener("mousemove", move);
    document.addEventListener("mouseup", up);
  }

  function startEdit(seed = null) {
    const addr = state.selected;
    const td = document.querySelector(`td.cell[data-addr="${addr}"]`);
    if (!td) return;
    state.editing = true;
    state.lastRefAddr = null;
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
      paintSelection();
    });
    input.addEventListener("keydown", (event) => {
      if (event.key === "Enter" && !event.shiftKey) {
        event.preventDefault();
        commitEdit(true);
        advanceInRange(0, 1);
      } else if (event.key === "Tab") {
        event.preventDefault();
        commitEdit(true);
        advanceInRange(event.shiftKey ? -1 : 1, 0);
      } else if (event.key === "Escape") {
        event.preventDefault();
        cancelEdit();
      }
    });
    placeFillHandle();
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

  function moveSelection(dc, dr, extend = false) {
    const pos = parseAddr(state.selected);
    if (!pos) return;
    const col = Math.max(0, Math.min(COLS - 1, pos.col + dc));
    const row = Math.max(0, Math.min(ROWS - 1, pos.row + dr));
    selectCell(addrOf(col, row), { extend });
  }

  function advanceInRange(dc, dr) {
    const rect = selectionRect();
    if (rect.c0 === rect.c1 && rect.r0 === rect.r1) {
      moveSelection(dc, dr);
      return;
    }
    const pos = parseAddr(state.selected);
    if (!pos) return;
    let col = pos.col;
    let row = pos.row;
    if (dr !== 0) {
      row += dr;
      if (row > rect.r1) {
        row = rect.r0;
        col += 1;
        if (col > rect.c1) col = rect.c0;
      } else if (row < rect.r0) {
        row = rect.r1;
        col -= 1;
        if (col < rect.c0) col = rect.c1;
      }
    } else {
      col += dc;
      if (col > rect.c1) {
        col = rect.c0;
        row += 1;
        if (row > rect.r1) row = rect.r0;
      } else if (col < rect.c0) {
        col = rect.c1;
        row -= 1;
        if (row < rect.r0) row = rect.r1;
      }
    }
    selectCell(addrOf(col, row), { keepRange: true });
  }

  function clearCell(addr) {
    const rect = addr ? null : selectionRect();
    const addrs = addr ? [addr] : cellsInRect(rect);
    if (!addrs.some((a) => state.cells[a])) return;
    snapshot();
    for (const a of addrs) {
      delete state.cells[a];
      delete state.results[a];
    }
    state.dirty = true;
    if (!addr || addr === state.selected) els.formula.value = "";
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
        if (document.activeElement !== els.base) els.base.value = String(data.base);
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
      default_col_width: state.defaultColW,
      default_row_height: state.defaultRowH,
      col_widths: state.colWidths,
      row_heights: state.rowHeights,
      cells: state.cells,
    };
  }

  function applySheet(data, { markDirty = false } = {}) {
    state.base = data.base || 10;
    state.defaultMode = data.default_output_mode || "num";
    state.cells = data.cells || {};
    state.results = {};
    state.defaultColW = clamp(data.default_col_width || DEFAULT_COL_W, MIN_COL_W, MAX_COL_W);
    state.defaultRowH = clamp(data.default_row_height || DEFAULT_ROW_H, MIN_ROW_H, MAX_ROW_H);
    state.colWidths = { ...(data.col_widths || {}) };
    state.rowHeights = { ...(data.row_heights || {}) };
    els.base.value = String(state.base);
    els.mode.value = state.defaultMode;
    state.dirty = markDirty;
    applySizes();
    selectCell("A1");
    persist();
    evaluateSheet();
  }

  function newSheet() {
    if (state.dirty && !confirm("Discard the current sheet?")) return;
    snapshot();
    applySheet({
      base: 10,
      default_output_mode: "num",
      cells: {},
      col_widths: {},
      row_heights: {},
      default_col_width: DEFAULT_COL_W,
      default_row_height: DEFAULT_ROW_H,
    });
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
        C2: { expr: "$A1:$B1", output_mode: "num" },
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
    state.colWidths = snap.colWidths || {};
    state.rowHeights = snap.rowHeights || {};
    state.defaultColW = snap.defaultColW || DEFAULT_COL_W;
    state.defaultRowH = snap.defaultRowH || DEFAULT_ROW_H;
    els.base.value = String(snap.base || 10);
    els.mode.value = state.defaultMode;
    state.dirty = true;
    persist();
    applySizes();
    selectCell(state.selected);
    evaluateSheet();
    setStatus("Undo");
  }

  async function copySource(addr) {
    const addrs = addr ? [addr] : cellsInRect(selectionRect());
    const rect = addr ? { c0: parseAddr(addr).col, c1: parseAddr(addr).col, r0: parseAddr(addr).row, r1: parseAddr(addr).row } : selectionRect();
    const rows = [];
    for (let r = rect.r0; r <= rect.r1; r++) {
      const cols = [];
      for (let c = rect.c0; c <= rect.c1; c++) cols.push(cellRecord(addrOf(c, r)).expr);
      rows.push(cols.join("\t"));
    }
    const text = rows.join("\n");
    const origin = addr ? parseAddr(addr) : { col: rect.c0, row: rect.r0 };
    state.clipboard = text;
    state.clipOrigin = origin;
    try {
      await navigator.clipboard.writeText(text);
      setStatus(addrs.length > 1 ? `Copied ${addrs.length} cells` : "Copied source");
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
      if (clip != null && clip !== "") {
        if (clip !== state.clipboard) state.clipOrigin = null;
        text = clip;
      }
    } catch {
      /* permission / empty */
    }
    if (!text) return;
    const origin = parseAddr(addr);
    if (!origin) return;
    const baseCol = state.clipOrigin ? origin.col - state.clipOrigin.col : 0;
    const baseRow = state.clipOrigin ? origin.row - state.clipOrigin.row : 0;
    const lines = text.replace(/\r/g, "").split("\n");
    snapshot();
    lines.forEach((line, ri) => {
      line.split("\t").forEach((cell, ci) => {
        const destCol = origin.col + ci;
        const destRow = origin.row + ri;
        if (destCol >= COLS || destRow >= ROWS || destCol < 0 || destRow < 0) return;
        const dest = addrOf(destCol, destRow);
        const expr = cell.trim();
        if (!expr) {
          delete state.cells[dest];
          return;
        }
        state.cells[dest] = {
          expr: shiftCellRefs(expr, baseCol + ci, baseRow + ri),
          output_mode: state.defaultMode,
        };
      });
    });
    state.dirty = true;
    if (addr === state.selected) els.formula.value = cellRecord(addr).expr;
    persist();
    paintCells();
    evaluateSheet();
  }

  function hideCtx() {
    els.ctx.hidden = true;
  }

  function showCtx(event, addr) {
    if (!inRect(addr, selectionRect())) selectCell(addr);
    else {
      state.selected = addr;
      if (!state.editing && !formulaIsFocused()) {
        els.formula.value = cellRecord(addr).expr;
        state.formulaAddr = addr;
      }
      paintSelection();
      updatePreview(addr);
      syncSizeInputs();
    }
    els.ctx.hidden = false;
    els.ctx.style.left = `${Math.min(event.clientX, window.innerWidth - 180)}px`;
    els.ctx.style.top = `${Math.min(event.clientY, window.innerHeight - 180)}px`;
  }

  function buildGrid() {
    const table = document.createElement("table");
    table.className = "sheet";
    const colgroup = document.createElement("colgroup");
    const cornerCol = document.createElement("col");
    cornerCol.style.width = "var(--row-head)";
    colgroup.appendChild(cornerCol);
    for (let c = 0; c < COLS; c++) {
      const col = document.createElement("col");
      col.style.width = `${colWidth(c)}px`;
      colgroup.appendChild(col);
    }
    table.appendChild(colgroup);

    const thead = document.createElement("thead");
    const headRow = document.createElement("tr");
    const corner = document.createElement("th");
    corner.className = "corner";
    corner.title = "Select all";
    corner.addEventListener("mousedown", (event) => {
      event.preventDefault();
      selectCell("A1");
      selectCell(addrOf(COLS - 1, ROWS - 1), { extend: true, scroll: false });
    });
    headRow.appendChild(corner);
    for (let c = 0; c < COLS; c++) {
      const th = document.createElement("th");
      th.dataset.col = String(c);
      th.title = `Column ${colLetter(c)}`;
      th.appendChild(document.createTextNode(colLetter(c)));
      const grip = document.createElement("span");
      grip.className = "col-resizer";
      grip.title = "Drag to resize column · double-click to reset";
      grip.addEventListener("mousedown", (event) => startColResize(c, event));
      grip.addEventListener("dblclick", (event) => {
        event.preventDefault();
        event.stopPropagation();
        resetColWidth(c);
      });
      th.appendChild(grip);
      th.addEventListener("mousedown", (event) => startColHeaderDrag(c, event));
      headRow.appendChild(th);
    }
    thead.appendChild(headRow);
    table.appendChild(thead);

    const tbody = document.createElement("tbody");
    for (let r = 0; r < ROWS; r++) {
      const tr = document.createElement("tr");
      const rh = document.createElement("th");
      rh.dataset.row = String(r);
      rh.title = `Row ${r + 1}`;
      rh.appendChild(document.createTextNode(String(r + 1)));
      const grip = document.createElement("span");
      grip.className = "row-resizer";
      grip.title = "Drag to resize row · double-click to reset";
      grip.addEventListener("mousedown", (event) => startRowResize(r, event));
      grip.addEventListener("dblclick", (event) => {
        event.preventDefault();
        event.stopPropagation();
        resetRowHeight(r);
      });
      rh.appendChild(grip);
      rh.addEventListener("mousedown", (event) => startRowHeaderDrag(r, event));
      tr.appendChild(rh);
      for (let c = 0; c < COLS; c++) {
        const td = document.createElement("td");
        const addr = addrOf(c, r);
        td.className = "cell";
        td.dataset.addr = addr;
        td.addEventListener("mousedown", (event) => {
          if (event.button !== 0) return;
          if (event.target.closest(".fill-handle")) return;
          if (state.editing || formulaIsFocused()) {
            event.preventDefault();
            const origin = state.lastRefAddr || state.formulaAddr || state.selected;
            if (event.shiftKey) insertRangeRef(origin, addr);
            else if (addr !== (state.formulaAddr || state.selected)) insertCellRef(addr);
            return;
          }
          if (event.shiftKey) {
            selectCell(addr, { extend: true });
            return;
          }
          selectCell(addr);
          startRangeDrag();
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
    if (!els.fill || !els.fill.isConnected) {
      const handle = document.createElement("div");
      handle.id = "fill-handle";
      handle.className = "fill-handle";
      handle.hidden = true;
      handle.title = "Drag to fill · Ctrl+D down · Ctrl+R right";
      handle.addEventListener("mousedown", startFillDrag);
      els.fill = handle;
    }
    els.wrap.appendChild(els.fill);
    applySizes();
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
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "d") {
      event.preventDefault();
      fillDown();
      return;
    }
    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "r") {
      event.preventDefault();
      fillRight();
      return;
    }

    if ((event.ctrlKey || event.metaKey) && event.key.toLowerCase() === "a") {
      event.preventDefault();
      selectCell("A1");
      selectCell(addrOf(COLS - 1, ROWS - 1), { extend: true, scroll: false });
      return;
    }

    switch (event.key) {
      case "ArrowUp":
        event.preventDefault();
        moveSelection(0, -1, event.shiftKey);
        break;
      case "ArrowDown":
        event.preventDefault();
        moveSelection(0, 1, event.shiftKey);
        break;
      case "ArrowLeft":
        event.preventDefault();
        moveSelection(-1, 0, event.shiftKey);
        break;
      case "ArrowRight":
        event.preventDefault();
        moveSelection(1, 0, event.shiftKey);
        break;
      case "Enter":
        event.preventDefault();
        advanceInRange(0, event.shiftKey ? -1 : 1);
        break;
      case "F2":
        event.preventDefault();
        startEdit();
        break;
      case "Escape":
        event.preventDefault();
        if (state.anchor !== state.selected) selectCell(state.selected);
        break;
      case "Delete":
      case "Backspace":
        event.preventDefault();
        clearCell();
        break;
      case "Tab":
        event.preventDefault();
        advanceInRange(event.shiftKey ? -1 : 1, 0);
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
      advanceInRange(0, 1);
      els.formula.value = cellRecord(state.selected).expr;
      state.formulaAddr = state.selected;
    } else if (event.key === "Escape") {
      els.formula.value = cellRecord(state.formulaAddr || state.selected).expr;
      els.formula.blur();
    }
  });

  els.formula.addEventListener("input", () => {
    if (formulaIsFocused() || state.editing) paintSelection();
  });

  els.formula.addEventListener("focus", () => {
    state.formulaAddr = state.selected;
    state.lastRefAddr = null;
    placeFillHandle();
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
    persist();
  });

  els.sizeW.addEventListener("change", () => {
    const pos = parseAddr(state.selected);
    if (!pos) return;
    setColWidth(pos.col, els.sizeW.value);
  });

  els.sizeH.addEventListener("change", () => {
    const pos = parseAddr(state.selected);
    if (!pos) return;
    setRowHeight(pos.row, els.sizeH.value);
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
    if (act === "clear") clearCell();
    if (act === "toggle-mode") toggleCellMode(state.selected);
    if (act === "fill-down") fillDown();
    if (act === "fill-right") fillRight();
    if (act === "reset-col") {
      const pos = parseAddr(state.selected);
      if (pos) resetColWidth(pos.col);
    }
    if (act === "reset-row") {
      const pos = parseAddr(state.selected);
      if (pos) resetRowHeight(pos.row);
    }
  });

  document.addEventListener("click", (event) => {
    if (!els.ctx.contains(event.target)) hideCtx();
  });
  document.addEventListener("keydown", onKey);
  els.wrap.addEventListener("scroll", placeFillHandle);
  window.addEventListener("resize", placeFillHandle);

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
