// ---------------------------------------------------------------------------
// Tab switching
// ---------------------------------------------------------------------------
document.querySelectorAll(".rail-tab").forEach(tab => {
  tab.addEventListener("click", () => {
    document.querySelectorAll(".rail-tab").forEach(t => t.classList.remove("active"));
    document.querySelectorAll(".panel").forEach(p => p.classList.add("hidden"));
    tab.classList.add("active");
    document.getElementById("panel-" + tab.dataset.panel).classList.remove("hidden");
  });
});

// ---------------------------------------------------------------------------
// Ledger tape rendering
// ---------------------------------------------------------------------------
function pushLedgerRow(label, ok, detail) {
  const body = document.getElementById("ledger-body");
  const empty = body.querySelector(".ledger-empty");
  if (empty) empty.remove();

  const row = document.createElement("div");
  row.className = "ledger-row";
  const chipClass = ok === null ? "chip-info" : ok ? "chip-pass" : "chip-fail";
  const chipText = ok === null ? "INFO" : ok ? "PASS" : "FAIL";

  row.innerHTML = `
    <span class="ledger-time">${new Date().toLocaleTimeString()}</span>
    <span class="ledger-chip ${chipClass}">${chipText}</span>
    <span class="ledger-detail">${label} — ${detail}</span>
  `;
  body.prepend(row);
}

function renderFullLedger(entries) {
  const body = document.getElementById("ledger-body");
  body.innerHTML = "";
  if (!entries.length) {
    body.innerHTML = '<div class="ledger-empty">Ledger is empty.</div>';
    return;
  }
  entries.forEach(e => {
    const ok = "passed" in e ? e.passed : (e.stamp === "PASS" ? true : e.stamp ? false : null);
    const label = e.event || "entry";
    const detail = e.target || e.reason || "";
    const row = document.createElement("div");
    row.className = "ledger-row";
    const chipClass = ok === null ? "chip-info" : ok ? "chip-pass" : "chip-fail";
    const chipText = ok === null ? "INFO" : ok ? "PASS" : "FAIL";
    row.innerHTML = `
      <span class="ledger-time">${e.timestamp_utc ? e.timestamp_utc.slice(11,19) : ""}</span>
      <span class="ledger-chip ${chipClass}">${chipText}</span>
      <span class="ledger-detail">${label} — ${detail}</span>
    `;
    body.appendChild(row);
  });
}

// ---------------------------------------------------------------------------
// Simple no-argument commands
// ---------------------------------------------------------------------------
const SIMPLE_ACTIONS = {
  get_status: "Status",
  list_protected: "Protected Files",
  get_next_packet: "Next Command",
};

document.querySelectorAll("[data-action]").forEach(btn => {
  btn.addEventListener("click", async () => {
    const action = btn.dataset.action;
    const label = SIMPLE_ACTIONS[action] || action;
    pushLedgerRow(label, null, "running…");

    if (action === "get_ledger") {
      const result = await eel.get_ledger()();
      renderFullLedger(result.entries);
      return;
    }

    const result = await eel[action]()();
    pushLedgerRow(label, result.passed, `exit ${result.exit_code}`);
  });
});

// ---------------------------------------------------------------------------
// Forms / prompt-based commands
// ---------------------------------------------------------------------------
document.querySelectorAll("[data-form]").forEach(btn => {
  btn.addEventListener("click", async () => {
    const form = btn.dataset.form;

    if (form === "stamp") {
      const stamp = prompt("Stamp (PASS/FAIL/PARTIAL/VOID/RESTORED/BLOCKED):", "PASS");
      const target = prompt("Target:");
      const reason = prompt("Reason:");
      if (!stamp || !target || !reason) return;
      pushLedgerRow("Stamp Result", null, "running…");
      const result = await eel.stamp_result(stamp, target, reason)();
      pushLedgerRow("Stamp Result", result.passed, target);
    }

    if (form === "recover") {
      const target = prompt("File path to recover (relative to repo root):");
      if (!target) return;
      pushLedgerRow("Recover From Git", null, "dry-run…");
      const result = await eel.recover_file(target, true)();
      pushLedgerRow("Recover From Git", result.passed, target);
    }

    if (form === "check_gd") {
      const target = prompt("Path to .gd file:");
      if (!target) return;
      pushLedgerRow("Check .gd Syntax", null, "running…");
      const result = await eel.check_gd_syntax(target)();
      pushLedgerRow("Check .gd Syntax", result.passed, result.stderr || target);
    }

    if (form === "validate_tscn") {
      const target = prompt("Path to .tscn file:");
      if (!target) return;
      pushLedgerRow("Validate .tscn", null, "running…");
      const result = await eel.validate_scene_structure(target)();
      pushLedgerRow("Validate .tscn", result.passed, result.stderr || target);
    }
  });
});

// ---------------------------------------------------------------------------
// Packet creation form
// ---------------------------------------------------------------------------
document.getElementById("packet-form").addEventListener("submit", async (e) => {
  e.preventDefault();
  const fd = new FormData(e.target);
  const id = fd.get("id"), title = fd.get("title"), command = fd.get("command");
  pushLedgerRow("Create Packet", null, "running…");
  const result = await eel.create_packet(id, title, command)();
  pushLedgerRow("Create Packet", result.passed, id);
  e.target.reset();
});

// ---------------------------------------------------------------------------
// Initial load
// ---------------------------------------------------------------------------
window.addEventListener("load", async () => {
  const status = await eel.get_status()();
  document.getElementById("repo-status").textContent =
    status.passed ? "GIT · ok" : "GIT · check status panel";
  const ledger = await eel.get_ledger()();
  renderFullLedger(ledger.entries);
});
