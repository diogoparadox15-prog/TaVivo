(function () {
  "use strict";

  const statusAiEl = document.getElementById("status-ai");
  const statusLibEl = document.getElementById("status-lib");
  const messagesEl = document.getElementById("messages");
  const welcomeInline = document.getElementById("welcome-inline");
  const composerForm = document.getElementById("composer");
  const inputEl = document.getElementById("input");
  const sendBtn = document.getElementById("send-btn");
  const imageInput = document.getElementById("image-input");
  const attachBtn = document.getElementById("attach-btn");
  const cameraBtn = document.getElementById("camera-btn");
  const previewStrip = document.getElementById("image-preview-strip");

  const layoutEl = document.getElementById("layout");
  const readerEl = document.getElementById("reader");
  const libraryBtn = document.getElementById("library-btn");
  const closeReaderBtn = document.getElementById("close-reader");
  const searchForm = document.getElementById("search-form");
  const searchInput = document.getElementById("search-input");
  const readerBody = document.getElementById("reader-body");

  const donateBtn = document.getElementById("donate-btn");
  const donateModal = document.getElementById("donate-modal");
  const closeDonateBtn = document.getElementById("close-donate");
  const okDonateBtn = document.getElementById("ok-donate");
  const copyBtcBtn = document.getElementById("copy-btc-btn");
  const btcAddressEl = document.getElementById("btc-address");

  const newChatBtn = document.getElementById("new-chat-btn");
  const themeBtn = document.getElementById("theme-btn");
  const aboutBtn = document.getElementById("about-btn");

  const welcomeModal = document.getElementById("welcome-modal");
  const enterTerminalBtn = document.getElementById("enter-terminal-btn");
  const aboutModal = document.getElementById("about-modal");
  const closeAboutBtn = document.getElementById("close-about");
  const okAboutBtn = document.getElementById("ok-about");
  const openSourcesBtn = document.getElementById("open-sources-btn");
  const sourcesModal = document.getElementById("sources-modal");
  const closeSourcesBtn = document.getElementById("close-sources");
  const okSourcesBtn = document.getElementById("ok-sources");
  const sourcesModalBody = document.getElementById("sources-modal-body");
  const openLegalBtn = document.getElementById("open-legal-btn");
  const legalModal = document.getElementById("legal-modal");
  const closeLegalBtn = document.getElementById("close-legal");
  const okLegalBtn = document.getElementById("ok-legal");
  const legalModalBody = document.getElementById("legal-modal-body");

  const cameraModal = document.getElementById("camera-modal");
  const closeCameraBtn = document.getElementById("close-camera");
  const cameraVideo = document.getElementById("camera-video");
  const cameraCanvas = document.getElementById("camera-canvas");
  const captureBtn = document.getElementById("capture-btn");
  const cameraError = document.getElementById("camera-error");

  const samuModal = document.getElementById("samu-modal");
  const closeSamuBtn = document.getElementById("close-samu");
  const okSamuBtn = document.getElementById("ok-samu");
  const copySamuBtn = document.getElementById("copy-samu-btn");
  const samuPreview = document.getElementById("samu-preview");
  const samuFields = ["samu-idade", "samu-peso", "samu-altura", "samu-comorb", "samu-meds", "samu-hora"]
    .map((id) => document.getElementById(id));

  let chatHistory = [];
  let pendingImages = [];
  let isStreaming = false;
  let currentAbortController = null;
  let cameraStream = null;

  // Seletor de 3 temas: X (Dim), WhatsApp, Branco
  const THEMES = ["x", "whatsapp", "light"];
  const THEME_LABELS = { x: "Tema: X", whatsapp: "Tema: WhatsApp", light: "Tema: Branco" };
  let savedTheme = localStorage.getItem("tavivo_theme") || "x";
  if (!THEMES.includes(savedTheme)) savedTheme = "x";
  document.documentElement.setAttribute("data-theme", savedTheme);
  themeBtn.textContent = THEME_LABELS[savedTheme];

  themeBtn.addEventListener("click", () => {
    const cur = document.documentElement.getAttribute("data-theme") || "x";
    const idx = THEMES.indexOf(cur);
    const next = THEMES[(idx + 1) % THEMES.length];
    document.documentElement.setAttribute("data-theme", next);
    localStorage.setItem("tavivo_theme", next);
    themeBtn.textContent = THEME_LABELS[next];
  });

  const isTouchMobile = () =>
    window.matchMedia && window.matchMedia("(max-width: 720px), (pointer: coarse)").matches;

  // Pop-up inicial de acolhimento
  if (welcomeModal && typeof welcomeModal.showModal === "function") {
    welcomeModal.showModal();
  }
  enterTerminalBtn.addEventListener("click", () => {
    welcomeModal.close();
    if (!isTouchMobile()) inputEl.focus();
  });

  // Modal Sobre & Licenças + Fontes da Base
  aboutBtn.addEventListener("click", () => aboutModal.showModal());
  closeAboutBtn.addEventListener("click", () => aboutModal.close());
  okAboutBtn.addEventListener("click", () => aboutModal.close());

  async function openSourcesModal() {
    aboutModal.close();
    sourcesModalBody.innerHTML = "<p class='meta'>Carregando fontes e livros...</p>";
    sourcesModal.showModal();
    try {
      const res = await fetch("/api/sources", { cache: "no-store" });
      const data = await res.json();
      const list = data.sources || [];
      sourcesModalBody.innerHTML = "";
      list.forEach((src) => {
        const sec = document.createElement("div");
        sec.style.marginBottom = "14px";
        const h = document.createElement("div");
        h.style.fontWeight = "700";
        h.style.marginBottom = "4px";
        h.textContent = `${src.label} (${src.articles.length})`;
        const lic = document.createElement("div");
        lic.className = "meta";
        lic.style.fontSize = "12px";
        lic.style.marginBottom = "6px";
        lic.textContent = src.license;
        sec.appendChild(h);
        sec.appendChild(lic);
        const ul = document.createElement("ul");
        ul.style.margin = "0";
        ul.style.paddingLeft = "18px";
        src.articles.forEach((art) => {
          const li = document.createElement("li");
          li.style.marginBottom = "3px";
          if (art.id) {
            const btn = document.createElement("button");
            btn.type = "button";
            btn.className = "source-chip";
            btn.style.textAlign = "left";
            btn.textContent = art.title;
            btn.addEventListener("click", () => {
              sourcesModal.close();
              loadArticle(art.id);
            });
            li.appendChild(btn);
          } else {
            li.textContent = art.title;
          }
          ul.appendChild(li);
        });
        sec.appendChild(ul);
        sourcesModalBody.appendChild(sec);
      });
    } catch (err) {
      sourcesModalBody.innerHTML = `<p class='meta danger'>Erro ao carregar fontes: ${err.message}</p>`;
    }
  }
  if (openSourcesBtn) openSourcesBtn.addEventListener("click", openSourcesModal);
  if (closeSourcesBtn) closeSourcesBtn.addEventListener("click", () => sourcesModal.close());
  if (okSourcesBtn) okSourcesBtn.addEventListener("click", () => sourcesModal.close());

  async function openLegalModal() {
    aboutModal.close();
    legalModalBody.textContent = "Carregando aviso legal...";
    legalModal.showModal();
    try {
      const res = await fetch("/api/legal", { cache: "no-store" });
      const data = await res.json();
      legalModalBody.textContent = data.text || "Aviso legal indisponível.";
    } catch (err) {
      legalModalBody.textContent = "Erro ao carregar aviso legal: " + err.message;
    }
  }
  if (openLegalBtn) openLegalBtn.addEventListener("click", openLegalModal);
  if (closeLegalBtn) closeLegalBtn.addEventListener("click", () => legalModal.close());
  if (okLegalBtn) okLegalBtn.addEventListener("click", () => legalModal.close());

  function buildSamuText() {
    const userMsgs = chatHistory.filter((m) => m.role === "user").map((m) => "- " + m.content);
    const [idade, peso, altura, comorb, meds, hora] = samuFields.map((el) => (el ? el.value.trim() : ""));
    return [
      "=== RESUMO CLÍNICO DE EMERGÊNCIA (TaVivo) ===",
      `Data/Hora do registro: ${new Date().toLocaleString("pt-BR")}`,
      `Idade: ${idade || "não informada"} | Peso: ${peso || "não informado"} | Altura: ${altura || "não informada"}`,
      `Comorbidades/Alergias: ${comorb || "não informadas"}`,
      `Medicações nas últimas 24h: ${meds || "não informadas"}`,
      `Horário início / picada / torniquete: ${hora || "não informado"}`,
      "",
      "Relato / Sintomas na conversa:",
      ...(userMsgs.length ? userMsgs : ["- (nenhum relato registrado)"]),
    ].join("\n");
  }

  function openSamuModal() {
    if (!samuModal) return;
    samuPreview.value = buildSamuText();
    samuModal.showModal();
  }

  samuFields.forEach((el) => {
    if (el) el.addEventListener("input", () => { samuPreview.value = buildSamuText(); });
  });
  if (closeSamuBtn) closeSamuBtn.addEventListener("click", () => samuModal.close());
  if (okSamuBtn) okSamuBtn.addEventListener("click", () => samuModal.close());
  if (copySamuBtn) {
    copySamuBtn.addEventListener("click", async () => {
      try {
        await navigator.clipboard.writeText(samuPreview.value);
        copySamuBtn.textContent = "Copiado!";
        setTimeout(() => { copySamuBtn.textContent = "Copiar Resumo"; }, 1800);
      } catch (_e) {
        samuPreview.select();
        document.execCommand("copy");
      }
    });
  }

  // Status contínuo (/api/status)
  async function refreshStatus() {
    try {
      const res = await fetch("/api/status", { cache: "no-store" });
      if (!res.ok) throw new Error("HTTP " + res.status);
      const data = await res.json();
      const port = data.ai_port || 9931;
      statusAiEl.textContent = (data.ai_online ? "🟢" : "🔴") + ` Motor IA (${port})`;
      if (data.library_online) {
        const count = data.articles ? ` (${data.articles.toLocaleString("pt-BR")})` : "";
        statusLibEl.textContent = `🟢 Biblioteca${count}`;
      } else {
        statusLibEl.textContent = "🔴 Biblioteca";
      }
    } catch (_err) {
      statusAiEl.textContent = "🔴 Motor IA (9931)";
      statusLibEl.textContent = "🔴 Biblioteca";
    }
  }
  refreshStatus();
  setInterval(refreshStatus, 5000);

  // Preview de imagens anexadas
  function renderPreviews() {
    previewStrip.innerHTML = "";
    if (pendingImages.length === 0) {
      previewStrip.hidden = true;
      return;
    }
    previewStrip.hidden = false;
    pendingImages.forEach((dataUrl, idx) => {
      const wrap = document.createElement("div");
      wrap.className = "preview-item";
      const img = document.createElement("img");
      img.src = dataUrl;
      img.alt = "Imagem anexada";
      const rm = document.createElement("button");
      rm.type = "button";
      rm.className = "preview-remove";
      rm.textContent = "✕";
      rm.addEventListener("click", () => {
        pendingImages.splice(idx, 1);
        renderPreviews();
      });
      wrap.appendChild(img);
      wrap.appendChild(rm);
      previewStrip.appendChild(wrap);
    });
  }

  attachBtn.addEventListener("click", () => imageInput.click());
  imageInput.addEventListener("change", () => {
    const file = imageInput.files && imageInput.files[0];
    if (!file) return;
    const reader = new FileReader();
    reader.onload = () => {
      if (typeof reader.result === "string") {
        pendingImages.push(reader.result);
        renderPreviews();
      }
    };
    reader.readAsDataURL(file);
    imageInput.value = "";
  });

  // Câmera ao vivo (localiza dispositivo e solicita autorização)
  function stopCamera() {
    if (cameraStream) {
      cameraStream.getTracks().forEach((t) => t.stop());
      cameraStream = null;
    }
    cameraVideo.srcObject = null;
  }

  async function openDeviceCamera() {
    cameraError.textContent = "Solicitando autorização para acessar a câmera...";
    cameraError.classList.remove("danger");
    captureBtn.disabled = true;

    if (!window.isSecureContext) {
      cameraError.classList.add("danger");
      cameraError.textContent =
        "O navegador exige contexto seguro para ligar a câmera. Acesse por http://localhost:9876 ou http://127.0.0.1:9876.";
      return;
    }

    if (!navigator.mediaDevices || !navigator.mediaDevices.getUserMedia) {
      cameraError.classList.add("danger");
      cameraError.textContent = "API de câmera (getUserMedia) indisponível neste navegador.";
      return;
    }

    const constraintsList = [
      { video: { facingMode: { ideal: "environment" }, width: { ideal: 1280 }, height: { ideal: 720 } }, audio: false },
      { video: true, audio: false },
    ];

    let lastErr = null;
    for (const constraints of constraintsList) {
      try {
        cameraStream = await navigator.mediaDevices.getUserMedia(constraints);
        break;
      } catch (err) {
        lastErr = err;
        if (err && (err.name === "NotAllowedError" || err.name === "PermissionDeniedError")) {
          break;
        }
      }
    }

    if (!cameraStream) {
      cameraError.classList.add("danger");
      if (lastErr && (lastErr.name === "NotAllowedError" || lastErr.name === "PermissionDeniedError")) {
        cameraError.textContent =
          "Permissão de câmera negada. Autorize o acesso à câmera no ícone ao lado do endereço do navegador e tente novamente.";
      } else if (lastErr && (lastErr.name === "NotFoundError" || lastErr.name === "DevicesNotFoundError")) {
        cameraError.textContent =
          "Nenhuma câmera foi localizada neste dispositivo. Você ainda pode enviar uma imagem pelo botão 📎 Foto.";
      } else {
        cameraError.textContent = "Não foi possível ligar a câmera: " + (lastErr ? lastErr.message : "erro desconhecido");
      }
      return;
    }

    cameraVideo.srcObject = cameraStream;
    try {
      await cameraVideo.play();
    } catch (_e) {
      // autoplay pode já estar ativo
    }
    captureBtn.disabled = false;

    try {
      const devices = await navigator.mediaDevices.enumerateDevices();
      const cams = devices.filter((d) => d.kind === "videoinput");
      const activeTrack = cameraStream.getVideoTracks()[0];
      const activeLabel = (activeTrack && activeTrack.label) || (cams[0] && cams[0].label) || "Câmera padrão";
      cameraError.textContent = `Câmera ativa (${cams.length || 1} encontrada${cams.length > 1 ? "s" : ""}): ${activeLabel}`;
    } catch (_e) {
      cameraError.textContent = "Câmera autorizada e ativa.";
    }
  }

  cameraBtn.addEventListener("click", () => {
    stopCamera();
    cameraModal.showModal();
    openDeviceCamera();
  });

  cameraModal.addEventListener("close", stopCamera);

  closeCameraBtn.addEventListener("click", () => {
    stopCamera();
    cameraModal.close();
  });

  captureBtn.addEventListener("click", () => {
    if (!cameraVideo.videoWidth) return;
    cameraCanvas.width = cameraVideo.videoWidth;
    cameraCanvas.height = cameraVideo.videoHeight;
    const ctx = cameraCanvas.getContext("2d");
    ctx.drawImage(cameraVideo, 0, 0);
    pendingImages.push(cameraCanvas.toDataURL("image/jpeg", 0.85));
    renderPreviews();
    stopCamera();
    cameraModal.close();
  });

  // Leitor da Biblioteca
  function openReader() {
    readerEl.hidden = false;
    layoutEl.classList.add("with-reader");
  }

  function closeReader() {
    readerEl.hidden = true;
    layoutEl.classList.remove("with-reader");
  }

  if (libraryBtn) {
    libraryBtn.addEventListener("click", () => {
      if (readerEl.hidden) {
        openReader();
        searchInput.focus();
      } else {
        closeReader();
      }
    });
  }

  if (donateBtn && donateModal) {
    donateBtn.addEventListener("click", () => donateModal.showModal());
    if (closeDonateBtn) closeDonateBtn.addEventListener("click", () => donateModal.close());
    if (okDonateBtn) okDonateBtn.addEventListener("click", () => donateModal.close());
    if (copyBtcBtn && btcAddressEl) {
      copyBtcBtn.addEventListener("click", async () => {
        const addr = btcAddressEl.textContent.trim();
        try {
          await navigator.clipboard.writeText(addr);
        } catch (_e) {
          // fallback
        }
        copyBtcBtn.textContent = "Copiado!";
        setTimeout(() => { copyBtcBtn.textContent = "Copiar Endereço"; }, 1800);
      });
    }
  }
  closeReaderBtn.addEventListener("click", closeReader);

  async function runLibrarySearch(query) {
    openReader();
    readerBody.innerHTML = "<p class='meta'>Buscando na biblioteca offline...</p>";
    try {
      const res = await fetch("/api/search?q=" + encodeURIComponent(query));
      const data = await res.json();
      const hits = data.results || [];
      if (hits.length === 0) {
        readerBody.innerHTML = "<p class='meta'>Nenhum artigo encontrado para esta busca.</p>";
        return;
      }
      readerBody.innerHTML = "";
      hits.forEach((hit) => {
        const card = document.createElement("div");
        card.className = "search-hit";
        const h4 = document.createElement("h4");
        h4.textContent = hit.title;
        const meta = document.createElement("div");
        meta.className = "meta";
        meta.textContent = hit.source + (hit.official ? " · Oficial" : "");
        const snip = document.createElement("div");
        snip.textContent = hit.snippet;
        card.appendChild(h4);
        card.appendChild(meta);
        card.appendChild(snip);
        card.addEventListener("click", () => loadArticle(hit.id));
        readerBody.appendChild(card);
      });
    } catch (err) {
      readerBody.innerHTML = `<p class='meta danger'>Erro ao buscar: ${err.message}</p>`;
    }
  }

  async function loadArticle(passageId) {
    openReader();
    readerBody.innerHTML = "<p class='meta'>Carregando artigo...</p>";
    try {
      const res = await fetch("/api/article?id=" + encodeURIComponent(passageId));
      if (!res.ok) throw new Error("Artigo não encontrado");
      const doc = await res.json();
      readerBody.innerHTML = "";
      const title = document.createElement("h3");
      title.textContent = doc.title;
      const meta = document.createElement("p");
      meta.className = "meta";
      meta.textContent = `${doc.source}${doc.license ? " · " + doc.license : ""}`;
      readerBody.appendChild(title);
      readerBody.appendChild(meta);

      (doc.parts || []).forEach((part) => {
        const p = document.createElement("div");
        p.className = "article-part" + (part.id === doc.focus ? " focus" : "");
        p.textContent = part.text;
        readerBody.appendChild(p);
        if (part.id === doc.focus) {
          setTimeout(() => p.scrollIntoView({ behavior: "smooth", block: "center" }), 60);
        }
      });
    } catch (err) {
      readerBody.innerHTML = `<p class='meta danger'>${err.message}</p>`;
    }
  }

  searchForm.addEventListener("submit", (e) => {
    e.preventDefault();
    const q = searchInput.value.trim();
    if (q) runLibrarySearch(q);
  });

  // Nova Conversa
  newChatBtn.addEventListener("click", () => {
    if (isStreaming) return;
    chatHistory = [];
    pendingImages = [];
    renderPreviews();
    messagesEl.querySelectorAll(".msg").forEach((el) => el.remove());
    welcomeInline.hidden = false;
  });

  // Exemplos rápidos
  document.querySelectorAll(".example").forEach((btn) => {
    btn.addEventListener("click", () => {
      inputEl.value = btn.textContent.trim();
      composerForm.requestSubmit();
    });
  });

  // Envio de mensagem com streaming SSE
  function appendMessage(role, text, images) {
    welcomeInline.hidden = true;
    const card = document.createElement("div");
    card.className = "msg " + role;

    const label = document.createElement("div");
    label.className = "msg-role";
    label.textContent = role === "user" ? "Você" : "TaVivo";
    card.appendChild(label);

    const body = document.createElement("div");
    body.className = "msg-body";
    body.textContent = text;
    card.appendChild(body);

    if (images && images.length > 0) {
      const imgWrap = document.createElement("div");
      imgWrap.className = "msg-images";
      images.forEach((src) => {
        const img = document.createElement("img");
        img.src = src;
        img.alt = "Imagem enviada";
        imgWrap.appendChild(img);
      });
      card.appendChild(imgWrap);
    }

    messagesEl.appendChild(card);
    messagesEl.scrollTop = messagesEl.scrollHeight;
    return { card, body };
  }

  composerForm.addEventListener("submit", async (e) => {
    e.preventDefault();
    if (isStreaming) {
      if (currentAbortController) currentAbortController.abort();
      return;
    }

    const text = inputEl.value.trim();
    const imagesToSend = pendingImages.slice();
    if (!text && imagesToSend.length === 0) return;

    inputEl.value = "";
    if (isTouchMobile()) inputEl.blur();
    pendingImages = [];
    renderPreviews();

    appendMessage("user", text || "[Imagem enviada]", imagesToSend);
    const assistantMsg = appendMessage("assistant", "");

    isStreaming = true;
    currentAbortController = new AbortController();
    sendBtn.textContent = "Parar";
    sendBtn.classList.add("stop-mode");
    let fullReply = "";
    let sourcesWrapEl = null;

    try {
      const res = await fetch("/api/chat", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        signal: currentAbortController.signal,
        body: JSON.stringify({
          message: text,
          history: chatHistory,
          images: imagesToSend,
        }),
      });

      const reader = res.body.getReader();
      const decoder = new TextDecoder("utf-8");
      let buffer = "";

      while (true) {
        const { done, value } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const parts = buffer.split("\n\n");
        buffer = parts.pop() || "";

        for (const block of parts) {
          const line = block.trim();
          if (!line.startsWith("data:")) continue;
          const payload = JSON.parse(line.slice(5).trim());

          if (payload.type === "safety" && payload.visual_lock) {
            const banner = document.createElement("div");
            banner.className = "safety-banner";
            banner.textContent = "🛡️ " + payload.message;
            assistantMsg.card.insertBefore(banner, assistantMsg.body);
          } else if (payload.type === "red_alert") {
            const alertBox = document.createElement("div");
            alertBox.className = "red-alert-card";
            const strong = document.createElement("strong");
            strong.textContent = "🚨 " + payload.title;
            alertBox.appendChild(strong);
            const ul = document.createElement("ul");
            (payload.steps || []).forEach((st) => {
              const li = document.createElement("li");
              li.textContent = st;
              ul.appendChild(li);
            });
            alertBox.appendChild(ul);
            assistantMsg.card.insertBefore(alertBox, assistantMsg.body);
          } else if (payload.type === "token") {
            fullReply += payload.text;
            assistantMsg.body.textContent = fullReply;
            messagesEl.scrollTop = messagesEl.scrollHeight;
          } else if (payload.type === "quick_replies" && payload.options && payload.options.length > 0) {
            const qrWrap = document.createElement("div");
            qrWrap.className = "quick-replies";
            payload.options.forEach((opt) => {
              const b = document.createElement("button");
              b.type = "button";
              b.className = "quick-reply-btn";
              b.textContent = opt;
              b.addEventListener("click", () => {
                if (isStreaming) return;
                inputEl.value = opt;
                composerForm.requestSubmit();
              });
              qrWrap.appendChild(b);
            });
            assistantMsg.card.appendChild(qrWrap);
          } else if (payload.type === "samu_offer") {
            const offer = document.createElement("div");
            offer.className = "samu-offer-card";
            const msgSpan = document.createElement("span");
            msgSpan.textContent = "📋 " + payload.message;
            const genBtn = document.createElement("button");
            genBtn.type = "button";
            genBtn.className = "primary";
            genBtn.textContent = "Gerar Resumo p/ SAMU";
            genBtn.addEventListener("click", openSamuModal);
            offer.appendChild(msgSpan);
            offer.appendChild(genBtn);
            assistantMsg.card.appendChild(offer);
          } else if (payload.type === "sources" && payload.sources && payload.sources.length > 0) {
            const srcWrap = document.createElement("div");
            srcWrap.className = "sources-list";
            const lbl = document.createElement("span");
            lbl.className = "meta";
            lbl.textContent = "Fontes:";
            srcWrap.appendChild(lbl);
            payload.sources.forEach((s) => {
              const chip = document.createElement("button");
              chip.type = "button";
              chip.className = "source-chip";
              chip.textContent = s.title;
              chip.title = s.source;
              chip.addEventListener("click", () => loadArticle(s.id));
              srcWrap.appendChild(chip);
            });
            assistantMsg.card.appendChild(srcWrap);
            sourcesWrapEl = srcWrap;
          } else if (payload.type === "error") {
            assistantMsg.body.textContent = "⚠️ " + payload.message;
          }
        }
      }

      if (fullReply) {
        const lowRep = fullReply.toLowerCase();
        if (
          sourcesWrapEl &&
          (lowRep.includes("não consta nos manuais") || lowRep.includes("não há protocolo"))
        ) {
          sourcesWrapEl.remove();
        }
        chatHistory.push({ role: "user", content: text });
        chatHistory.push({ role: "assistant", content: fullReply });
      }
    } catch (err) {
      if (err && err.name === "AbortError") {
        assistantMsg.body.textContent = (fullReply ? fullReply + "\n\n" : "") + "[Resposta interrompida]";
      } else {
        assistantMsg.body.textContent = "⚠️ Falha de comunicação com o servidor local: " + err.message;
      }
    } finally {
      isStreaming = false;
      currentAbortController = null;
      sendBtn.textContent = "Enviar";
      sendBtn.classList.remove("stop-mode");
      sendBtn.disabled = false;
      if (!isTouchMobile()) inputEl.focus();
    }
  });

  // Enter envia, Shift+Enter quebra linha
  inputEl.addEventListener("keydown", (e) => {
    if (e.key === "Enter" && !e.shiftKey) {
      e.preventDefault();
      composerForm.requestSubmit();
    }
  });
})();
