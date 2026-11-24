(function () {
  "use strict";

  const STORAGE_KEY = "tavivo_checklist_v2";

  const DEFAULT_KITS = [
    {
      id: "edc",
      name: "EDC (Bolso)",
      desc: "Itens de uso diário para emergências fora de casa.",
      items: [
        { id: "edc-1", text: "Mini lanterna LED + pilha reserva", checked: false, expiry: "" },
        { id: "edc-2", text: "Isqueiro BIC confiável (com fita isolante enrolada)", checked: false, expiry: "" },
        { id: "edc-3", text: "Canivete dobrável ou mini alicate multifunção", checked: false, expiry: "" },
        { id: "edc-4", text: "Apito de emergência de alto decibel", checked: false, expiry: "" },
        { id: "edc-5", text: "Dinheiro trocado em espécie (notas pequenas)", checked: false, expiry: "" },
        { id: "edc-6", text: "Cópia plastificada RG/CPF + contatos em papel", checked: false, expiry: "" },
        { id: "edc-7", text: "Powerbank 10.000 mAh carregado + cabo curto", checked: false, expiry: "" },
      ],
    },
    {
      id: "bob",
      name: "Mochila 72h (BOB)",
      desc: "Fuga rápida (máx. 15–20% do peso corporal).",
      items: [
        { id: "bob-1", text: "Água potável (2 a 3 L) + cantil metálico", checked: false, expiry: "" },
        { id: "bob-2", text: "Filtro portátil ou hipoclorito de sódio 2,5%", checked: false, expiry: "" },
        { id: "bob-3", text: "Comida pronta 6.000 kcal (barras, amendoim, atum)", checked: false, expiry: "" },
        { id: "bob-4", text: "Cobertor térmico aluminizado + poncho de chuva", checked: false, expiry: "" },
        { id: "bob-5", text: "Lona 2x3m + 10m de paracord 550", checked: false, expiry: "" },
        { id: "bob-6", text: "Troca de roupa seca vedada + 2 pares extras de meia", checked: false, expiry: "" },
        { id: "bob-7", text: "Lanterna de cabeça + pilhas extras + 2 isqueiros", checked: false, expiry: "" },
        { id: "bob-8", text: "Rádio AM/FM/SW a pilha ou manivela + mapa físico", checked: false, expiry: "" },
        { id: "bob-9", text: "Kit trauma (gaze, atadura, torniquete, clorexidina, N95)", checked: false, expiry: "" },
      ],
    },
    {
      id: "bugin",
      name: "Casa (15–90 dias)",
      desc: "Estoque residencial e saneamento em apagão prolongado.",
      items: [
        { id: "bi-1", text: "Reserva de água (3–4 L/pessoa/dia em galões)", checked: false, expiry: "" },
        { id: "bi-2", text: "Grãos em garrafa PET (arroz, feijão, macarrão, aveia)", checked: false, expiry: "" },
        { id: "bi-3", text: "Proteínas enlatadas/secas + óleo + sal + açúcar + mel", checked: false, expiry: "" },
        { id: "bi-4", text: "Botijão P13 reserva OU fogareiro portátil + combustível", checked: false, expiry: "" },
        { id: "bi-5", text: "Sistema banheiro seco (2 baldes 20L + sacos + serragem/cal)", checked: false, expiry: "" },
        { id: "bi-6", text: "Velas de 7 dias + lanternas + estoque de pilhas AA/AAA", checked: false, expiry: "" },
        { id: "bi-7", text: "Placa solar portátil (20–50W) + powerbanks", checked: false, expiry: "" },
        { id: "bi-8", text: "Lona/papelão para blackout nas janelas", checked: false, expiry: "" },
      ],
    },
    {
      id: "carro",
      name: "Carro (GHB)",
      desc: "Pane na estrada e retorno a pé para casa (Get Home Bag).",
      items: [
        { id: "car-1", text: "Tanque sempre acima de meio tanque", checked: false, expiry: "" },
        { id: "car-2", text: "Martelo quebra-vidro + corta-cinto ao alcance do motorista", checked: false, expiry: "" },
        { id: "car-3", text: "Cabo de chupeta grosso ou auxiliar de partida carregado", checked: false, expiry: "" },
        { id: "car-4", text: "Compressor 12V + kit reparo de pneu + fusíveis reserva", checked: false, expiry: "" },
        { id: "car-5", text: "Tênis/bota confortável + meias extras para caminhar", checked: false, expiry: "" },
        { id: "car-6", text: "2L de água (trocar a cada 3 meses) + castanhas/biscoito", checked: false, expiry: "" },
        { id: "car-7", text: "Mapa rodoviário em papel + dinheiro trocado", checked: false, expiry: "" },
      ],
    },
    {
      id: "farmacia",
      name: "Farmácia de Guerra",
      desc: "Primeiros socorros, MIPs essenciais e controle de validade.",
      items: [
        { id: "med-1", text: "Torniquete comercial (CAT/SOFTT) + gazes + ataduras", checked: false, expiry: "" },
        { id: "med-2", text: "Soro fisiológico 0,9% (frascos 100 ml) + clorexidina", checked: false, expiry: "" },
        { id: "med-3", text: "Paracetamol e Dipirona (adulto + gotas pediátricas)", checked: false, expiry: "" },
        { id: "med-4", text: "Sais de Reidratação Oral (envelopes SRO OMS)", checked: false, expiry: "" },
        { id: "med-5", text: "Antialérgico (Loratadina/Polaramine) + antiácido", checked: false, expiry: "" },
        { id: "med-6", text: "Pomadas (antibiótica, antifúngica e queimadura leve)", checked: false, expiry: "" },
        { id: "med-7", text: "Termômetro analógico + pinça + tesoura ponta romba + luvas", checked: false, expiry: "" },
        { id: "med-8", text: "Reserva 15–30 dias de remédios contínuos + receitas", checked: false, expiry: "" },
      ],
    },
    {
      id: "ferramentas",
      name: "Ferramentas & Faraday",
      desc: "Manutenção sem energia, documentos e proteção EMP.",
      items: [
        { id: "fer-1", text: "Alicate multifunção + chaves fenda/Philips + chave inglesa", checked: false, expiry: "" },
        { id: "fer-2", text: "Serra dobrável + facão/machadinha + pedra de amolar", checked: false, expiry: "" },
        { id: "fer-3", text: "Silver tape + arame recozido + abraçadeiras + durepoxi", checked: false, expiry: "" },
        { id: "fer-4", text: "Lona reforçada 4x4m + 30m de paracord", checked: false, expiry: "" },
        { id: "fer-5", text: "Pasta à prova d'água com cópias de documentos", checked: false, expiry: "" },
        { id: "fer-6", text: "Pendrive criptografado com documentos + TaVivo", checked: false, expiry: "" },
        { id: "fer-7", text: "Gaiola de Faraday (lata metálica forrada) com rádio/celular", checked: false, expiry: "" },
      ],
    },
  ];

  function loadState() {
    try {
      const raw = localStorage.getItem(STORAGE_KEY);
      if (!raw) return structuredClone(DEFAULT_KITS);
      const parsed = JSON.parse(raw);
      if (Array.isArray(parsed) && parsed.length > 0) return parsed;
    } catch (_e) {}
    return structuredClone(DEFAULT_KITS);
  }

  function saveState(kits) {
    try {
      localStorage.setItem(STORAGE_KEY, JSON.stringify(kits));
    } catch (_e) {}
  }

  function expiryStatus(dateStr) {
    if (!dateStr) return null;
    const target = new Date(dateStr + "T00:00:00");
    if (Number.isNaN(target.getTime())) return null;
    const now = new Date();
    now.setHours(0, 0, 0, 0);
    const diffDays = Math.ceil((target - now) / (1000 * 60 * 60 * 24));
    if (diffDays < 0) return { cls: "exp-dead", label: `Vencido há ${Math.abs(diffDays)}d` };
    if (diffDays <= 30) return { cls: "exp-soon", label: `Vence em ${diffDays}d` };
    return { cls: "exp-ok", label: `Val: ${dateStr}` };
  }

  let kits = loadState();
  let activeKitId = kits[0].id;

  const openBtn = document.getElementById("checklist-btn");
  const modal = document.getElementById("checklist-modal");
  const closeBtn = document.getElementById("close-checklist");
  const okBtn = document.getElementById("ok-checklist");
  const tabsEl = document.getElementById("checklist-tabs");
  const listEl = document.getElementById("checklist-list");
  const summaryEl = document.getElementById("checklist-summary");
  const barFillEl = document.getElementById("checklist-bar-fill");
  const descEl = document.getElementById("checklist-kit-desc");
  const addForm = document.getElementById("checklist-add-form");
  const addInput = document.getElementById("checklist-add-input");
  const addExpiry = document.getElementById("checklist-add-expiry");
  const exportBtn = document.getElementById("checklist-export-btn");
  const importBtn = document.getElementById("checklist-import-btn");
  const importFile = document.getElementById("checklist-import-file");

  function render() {
    if (!modal || !tabsEl || !listEl) return;

    let totalAll = 0;
    let doneAll = 0;
    let expiredCount = 0;
    kits.forEach((k) => {
      k.items.forEach((it) => {
        totalAll++;
        if (it.checked) doneAll++;
        const st = expiryStatus(it.expiry);
        if (st && st.cls === "exp-dead") expiredCount++;
      });
    });

    const pct = totalAll ? Math.round((doneAll / totalAll) * 100) : 0;
    if (barFillEl) barFillEl.style.width = `${pct}%`;
    if (summaryEl) {
      const expTxt = expiredCount > 0 ? ` · ⚠️ ${expiredCount} vencido(s)` : "";
      summaryEl.textContent = `Prontidão Geral: ${doneAll}/${totalAll} (${pct}%)${expTxt}`;
    }

    tabsEl.innerHTML = "";
    kits.forEach((kit) => {
      const done = kit.items.filter((i) => i.checked).length;
      const btn = document.createElement("button");
      btn.type = "button";
      btn.className = "ck-tab" + (kit.id === activeKitId ? " active" : "");
      btn.textContent = `${kit.name} (${done}/${kit.items.length})`;
      btn.addEventListener("click", () => {
        activeKitId = kit.id;
        render();
      });
      tabsEl.appendChild(btn);
    });

    const currentKit = kits.find((k) => k.id === activeKitId) || kits[0];
    if (descEl) descEl.textContent = currentKit.desc || "";

    listEl.innerHTML = "";
    currentKit.items.forEach((item) => {
      const row = document.createElement("div");
      row.className = "ck-row" + (item.checked ? " done" : "");

      const label = document.createElement("label");
      label.className = "ck-label";

      const cb = document.createElement("input");
      cb.type = "checkbox";
      cb.checked = !!item.checked;
      cb.addEventListener("change", () => {
        item.checked = cb.checked;
        saveState(kits);
        render();
      });

      const span = document.createElement("span");
      span.textContent = item.text;
      label.appendChild(cb);
      label.appendChild(span);

      const right = document.createElement("div");
      right.className = "ck-actions";

      const st = expiryStatus(item.expiry);
      if (st) {
        const badge = document.createElement("span");
        badge.className = "ck-badge " + st.cls;
        badge.textContent = st.label;
        right.appendChild(badge);
      }

      const dateInput = document.createElement("input");
      dateInput.type = "date";
      dateInput.className = "ck-date";
      dateInput.title = "Data de validade (opcional)";
      dateInput.value = item.expiry || "";
      dateInput.addEventListener("change", () => {
        item.expiry = dateInput.value;
        saveState(kits);
        render();
      });
      right.appendChild(dateInput);

      if (item.custom) {
        const del = document.createElement("button");
        del.type = "button";
        del.className = "ghost icon";
        del.textContent = "✕";
        del.title = "Remover item";
        del.addEventListener("click", () => {
          currentKit.items = currentKit.items.filter((x) => x.id !== item.id);
          saveState(kits);
          render();
        });
        right.appendChild(del);
      }

      row.appendChild(label);
      row.appendChild(right);
      listEl.appendChild(row);
    });
  }

  if (openBtn && modal) {
    openBtn.addEventListener("click", () => {
      render();
      modal.showModal();
    });
  }
  const welcomeCkBtn = document.getElementById("welcome-open-checklist");
  if (welcomeCkBtn && modal) {
    welcomeCkBtn.addEventListener("click", () => {
      render();
      modal.showModal();
    });
  }
  if (closeBtn && modal) closeBtn.addEventListener("click", () => modal.close());
  if (okBtn && modal) okBtn.addEventListener("click", () => modal.close());

  if (addForm && addInput) {
    addForm.addEventListener("submit", (e) => {
      e.preventDefault();
      const text = addInput.value.trim();
      if (!text) return;
      const currentKit = kits.find((k) => k.id === activeKitId);
      if (!currentKit) return;
      currentKit.items.push({
        id: "custom-" + Date.now(),
        text,
        checked: false,
        expiry: addExpiry ? addExpiry.value : "",
        custom: true,
      });
      addInput.value = "";
      if (addExpiry) addExpiry.value = "";
      saveState(kits);
      render();
    });
  }

  if (exportBtn) {
    exportBtn.addEventListener("click", () => {
      const blob = new Blob([JSON.stringify(kits, null, 2)], { type: "application/json" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = "tavivo_checklist_backup.json";
      a.click();
      URL.revokeObjectURL(url);
    });
  }

  if (importBtn && importFile) {
    importBtn.addEventListener("click", () => importFile.click());
    importFile.addEventListener("change", async () => {
      const file = importFile.files && importFile.files[0];
      if (!file) return;
      try {
        const text = await file.text();
        const parsed = JSON.parse(text);
        if (Array.isArray(parsed) && parsed.length > 0 && parsed[0].items) {
          kits = parsed;
          activeKitId = kits[0].id;
          saveState(kits);
          render();
        }
      } catch (_e) {}
      importFile.value = "";
    });
  }

  // Registro do Service Worker (PWA 100% Offline)
  if ("serviceWorker" in navigator) {
    window.addEventListener("load", () => {
      navigator.serviceWorker.register("/sw.js").catch(() => {});
    });
  }

  // Fallback offline de busca na biblioteca caso o backend Python não esteja ativo (ex.: PWA estático)
  window.TaVivoOfflineLib = {
    _cache: null,
    async load() {
      if (this._cache) return this._cache;
      const res = await fetch("/static/library_offline.json");
      this._cache = await res.json();
      return this._cache;
    },
    async search(query) {
      const lib = await this.load();
      const q = (query || "").toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
      const terms = q.split(/\s+/).filter((t) => t.length > 1);
      if (!terms.length) return [];
      const scored = [];
      for (const art of lib.articles || []) {
        const hay = (art.title + " " + art.text).toLowerCase().normalize("NFD").replace(/[\u0300-\u036f]/g, "");
        let score = 0;
        for (const t of terms) {
          if (hay.includes(t)) score += art.title.toLowerCase().includes(t) ? 3 : 1;
        }
        if (score > 0) scored.push({ score, art });
      }
      scored.sort((a, b) => b.score - a.score);
      return scored.slice(0, 15).map((s) => ({
        id: s.art.id,
        title: s.art.title,
        source: s.art.source,
        snippet: s.art.text.slice(0, 260) + "...",
      }));
    },
  };
})();
