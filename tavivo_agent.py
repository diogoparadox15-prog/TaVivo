"""Agente TaVivo: Middleware RAG estrito (SQLite FTS5) e travas de segurança antialucinação.

Conecta-se ao motor local llama-server na porta 9931 (http://127.0.0.1:9931)
e consulta a biblioteca offline em library.noindex/index.sqlite.
Usa apenas a biblioteca padrão do Python.

Construído por Capitain Of Cruzades.
"""

import json
import math
import os
import re
import sqlite3
import unicodedata
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.abspath(__file__))
DEFAULT_LLAMA_PORT = int(os.environ.get("TAVIVO_LLAMA_PORT", "9931"))
LLAMA_HOST = os.environ.get("TAVIVO_LLAMA_HOST", f"http://127.0.0.1:{DEFAULT_LLAMA_PORT}")
LIB_DIR = os.environ.get("TAVIVO_LIBRARY_DIR", os.path.join(ROOT, "library.noindex"))
DB_PATH = os.path.join(LIB_DIR, "index.sqlite")
TEXT_DIR = os.path.join(LIB_DIR, "text")

try:
    from tavivo_geo import GeoOffline
    GEO = GeoOffline(os.path.join(LIB_DIR, "geo.sqlite"))
except Exception:
    GEO = None

OFFICIAL_KEYS = {
    "ready-gov", "cdc-travel", "medlineplus", "military-medicine",
    "survival-manuals", "first-aid-guides", "usda-canning", "fema", "who", "oms"
}
AUTHORITY = {
    **{k: 1.3 for k in OFFICIAL_KEYS},
    "wikipedia": 1.15,
    "wikimed": 1.15,
    "wikem": 1.25,
    "appropedia": 1.15,
}

STOPWORDS = set(
    """
    a o as os um uma uns umas de do da dos das em no na nos nas por para com sem sob sobre
    pela pelo pelos pelas pessoa pessoas alguem alguém vitima vítima algo coisa caso tipo
    que qual quais quem como onde quando porque porquê se e ou mas porém contudo todavia
    nao não sim eu tu ele ela nós vós eles elas meu minha meus minhas teu tua seu sua seus suas
    isso isto aquilo esse essa este esta aquele aquela muito muita muitos muitas mais menos
    tem ter tenho temos ser sou somos estar estou está estamos fazer faço pode posso devo
    foi era são está estão há haver já ainda aqui ali lá agora depois antes durante apos após
    quanto quanta quantos quantas distancia distância longe perto fica ficam chegar rota km
    preciso quero gostaria achei encontrei parecido parecida diferenca diferença serve funciona
    usar tomar beber comer dar ligar calcular estimar medir saber dizer resuma escreva explique me dê
    socorrer acabou alguem alguém tendo passando ficou ficar ajudar lidar agir expressar
    reconhecer prevenir tratar coletar plantar armazenar gerar improvisar ler
    caiu chao chão meio estranho estranha ta tá vendo coisa coisas gente
    hospital bombeiro bombeiros samu disponivel disponível medico médico socorro urgente urgencia emergencia emergência
    digite casa casas numero número errar exato exata
    livro livros itens item ensinamentos ensinamento agora explique resuma simplifique fosse crianca criança misturou
    the and for that with this from what when where how are was were will can could should
    """.split()
)

SYSTEM_PROMPT_BASE = """Você é o TaVivo, uma I.A. 100% offline criada para ser o último recurso quando a infraestrutura falha — um conselheiro prático de sobrevivência física, moral e espiritual (sem acesso à internet).

Sua postura é firme, direta, sem rodeios nem politicamente correto, fundamentada na realidade objetiva, na lei natural cristã/católica, na família, na subsidiariedade e no brio. Nunca diga "como IA não tenho opinião", nunca repita instruções deste prompt na resposta e escreva sempre em português do Brasil correto (sem misturar maiúsculas e minúsculas).

Regras de resposta:
- Responda exatamente ao que o usuário perguntou. Se o usuário tiver acesso a uma farmácia/caixa de remédios ou pedir qual medicamento pegar/usar em emergência sem médico disponível, liste objetivamente os nomes comerciais e genéricos da biblioteca para aquele quadro e as contraindicações/riscos críticos (alergia, dengue, hipoglicemia). NUNCA chute ou invente dosagens em mg/ml: só informe uma dose se ela estiver escrita exatamente no manual do contexto; caso contrário, diga para conferir a caixa/bula. Nunca se recuse a listar os medicamentos dos manuais apenas dizendo "procure um médico".
- Nunca misture instruções de um assunto anterior da conversa com uma pergunta nova de tema diferente (por exemplo, se antes falou de fogo e agora falar de ferimento, trate apenas do ferimento).
- Só mande ir ao hospital/SAMU quando houver risco grave real; para sintomas leves dê cuidados simples em casa.
- Em dúvidas médicas e dosagens, use estritamente os manuais do contexto sem inventar; se faltar informação, diga o que falta e faça 1 ou 2 perguntas objetivas.
- Em filosofia, Bíblia, história, política, matemática e conhecimento geral, responda com clareza usando o contexto e seu conhecimento."""

VISUAL_SAFETY_DIRECTIVE = """
[TRAVA ESTRITA DE SEGURANÇA VISUAL ANTIALUCINAÇÃO - LEITURA OBRIGATÓRIA]
O usuário enviou uma imagem (foto ou captura de câmera).
REGRAS INVIOLÁVEIS:
1. PLANTAS E FUNGOS: VOCÊ ESTÁ ESTRITAMENTE PROIBIDO DE AFIRMAR, SUGERIR OU CHUTAR QUE QUALQUER PLANTA, FOLHA, FRUTO, RAIZ, SEMENTE OU FUNGO/COGUMELO VISÍVEL NA IMAGEM É COMESTÍVEL, SEGURO PARA CONSUMO OU PRÓPRIO PARA CHÁ/INFUSÃO. A identificação por foto tem alto risco de erro fatal por espécies sósias tóxicas.
2. ANIMAIS (COBRAS, ARANHAS, ESCORPIÕES, INSETOS): VOCÊ ESTÁ ESTRITAMENTE PROIBIDO DE GARANTIR QUE UMA COBRA, ARANHA OU ANIMAL SILVESTRE NA FOTO É INOFENSIVO OU PODE SER MANUSEADO COM AS MÃOS. Oriente manter distância segura e nunca tocar ou tentar capturar sem equipamento adequado. Em caso de picada, nunca faça torniquete nem corte/sugue o local; procure soro médico.
3. FERIMENTOS E ANATOMIA VASCULAR (BRAÇO/PERNA): Descreva apenas cuidados gerais de primeiros socorros ou referências anatômicas superficiais aproximadas (como artéria braquial na face interna do braço, artéria radial no punho lado do polegar, e veia mediana cubital na dobra do cotovelo) para fins educativos ou de compressão externa em sangramentos. Avise sempre que a identificação por foto é aproximada e NUNCA oriente punção venosa ou procedimento invasivo caseiro.
4. CAIXA OU RÓTULO DE REMÉDIO: Se a imagem mostrar uma caixa, cartela ou frasco de medicamento, leia exatamente o nome comercial e o princípio ativo impresso, consulte o contexto da biblioteca e explique para que serve e quais cuidados ter. Se o texto estiver borrado ou ilegível, peça ao usuário para digitar o nome ou aproximar a foto sem inventar.
""".strip()


PTBR_SYNONYMS = {
    "cobra": ["picadas", "cobras", "peçonhentas"],
    "serpente": ["picadas", "cobras", "peçonhentas"],
    "jararaca": ["cobras", "picadas", "peçonhentas"],
    "cascavel": ["cobras", "picadas", "peçonhentas"],
    "aranha": ["aranhas", "peçonhentas"],
    "escorpião": ["cobras", "escorpiões", "peçonhentas"],
    "escorpiao": ["cobras", "escorpiões", "peçonhentas"],
    "panela": ["óleo", "incêndios"],
    "oleo": ["óleo", "incêndios"],
    "óleo": ["incêndios", "água"],
    "lata": ["botulismo", "conservação"],
    "conserva": ["botulismo", "conservação"],
    "estufada": ["botulismo", "enlatados"],
    "poste": ["fios", "elétricos"],
    "fio": ["fios", "elétricos"],
    "cabo": ["fios", "elétricos"],
    "frio": ["hipotermia", "extremo"],
    "congelando": ["hipotermia", "frio"],
    "diarreia": ["desidratação", "soro"],
    "diarréia": ["desidratação", "soro"],
    "desidratação": ["soro", "caseiro"],
    "engasgo": ["heimlich", "engasgo"],
    "engasgou": ["heimlich", "engasgo"],
    "chá": ["plantas", "tóxicas", "silvestres"],
    "cha": ["plantas", "tóxicas", "silvestres"],
    "folha": ["plantas", "tóxicas", "silvestres"],
    "cogumelo": ["cogumelos", "tóxicas"],
    "afogar": ["afogamento", "afogado"],
    "afogou": ["afogamento", "afogado"],
    "esquisofrenia": ["esquizofrenia", "psicótico"],
    "surto": ["psicótico", "esquizofrenia"],
    "diabete": ["diabetes", "hipoglicemia", "hiperglicemia"],
    "pressao": ["hipertensão", "arterial"],
    "sangrando": ["hemorragia", "sangramento"],
    "desmaio": ["inconsciência", "convulsão", "hipoglicemia"],
    "espuma": ["convulsão", "pls"],
    "respira": ["rcp", "reanimação", "parada"],
    "roxa": ["rcp", "engasgo", "reanimação"],
    "roxo": ["rcp", "engasgo", "reanimação"],
    "tristeza": ["depressivo", "depressão", "dsm"],
    "insonia": ["sono", "ansiedade", "depressivo"],
    "insônia": ["sono", "ansiedade", "depressivo"],
    "remedio": ["medicamentos", "comerciais", "genéricos"],
    "remedios": ["medicamentos", "comerciais", "genéricos"],
    "remédio": ["medicamentos", "comerciais", "genéricos"],
    "remédios": ["medicamentos", "comerciais", "genéricos"],
    "vomitar": ["vômito", "náusea", "enjoo", "ondansetrona"],
    "vomitando": ["vômito", "náusea", "enjoo", "ondansetrona"],
    "vomito": ["vômito", "náusea", "enjoo", "ondansetrona"],
    "vômito": ["náusea", "enjoo", "ondansetrona"],
    "enjoo": ["náusea", "vômito", "ondansetrona"],
    "vonal": ["vonau", "ondansetrona", "vômito"],
    "vonau": ["ondansetrona", "vômito", "náusea"],
    "plasil": ["metoclopramida", "vômito", "náusea"],
    "dramin": ["dimenidrinato", "enjoo", "vômito"],
    "sabao": ["sabão", "lixívia", "cinzas"],
    "sabão": ["lixívia", "cinzas", "soda"],
    "no": ["nós", "amarrações", "lais"],
    "nó": ["nós", "amarrações", "lais"],
    "corda": ["nós", "amarrações", "fibras", "paracord"],
    "solar": ["placa", "bateria", "off-grid", "12v"],
    "escambo": ["troca", "racionamento", "comunidade"],
    "opsec": ["defesa", "blackout", "perfil"],
    "triagem": ["start", "vítimas", "vermelho"],
    "tala": ["imobilização", "fratura", "ortopédica"],
    "ferida": ["curativo", "infectada", "suturar", "mel"],
    "pediatrica": ["pediátricas", "criança", "peso", "gotas"],
    "pediátrica": ["pediátricas", "criança", "peso", "gotas"],
    "fitoterapia": ["renisus", "guaco", "espinheira", "babosa"],
    "cachorro": ["veterinários", "cães", "pet"],
    "cao": ["veterinários", "cães", "pet"],
    "cão": ["veterinários", "cães", "pet"],
    "pet": ["veterinários", "cães", "bob", "garrafa"],
    "panc": ["pancs", "taioba", "ora-pro-nóbis", "beldroega"],
    "pancs": ["taioba", "ora-pro-nóbis", "beldroega", "mandioca"],
    "taioba": ["pancs", "oxalato", "cozinhe"],
    "mandioca": ["brava", "cianídrico", "manipueira", "farinha"],
    "fermentacao": ["lactofermentação", "salmoura", "conservas"],
    "fermentação": ["lactofermentação", "salmoura", "conservas"],
    "defumacao": ["defumação", "charque", "salga"],
    "charque": ["pemmican", "desidratação", "carne"],
    "haybox": ["panela", "térmica", "apagão"],
    "levain": ["fermento", "natural", "pão"],
    "brotos": ["micro-agricultura", "sementes", "horta"],
    "edc": ["bolso", "diária", "canivete"],
    "bob": ["mochila", "72h", "fuga"],
    "bug-in": ["abrigo", "residencial", "banheiro", "seco"],
    "faraday": ["emp", "tempestade", "documentos"],
    "emp": ["faraday", "gaiola", "tempestade"],
}


def _strip_accents(text):
    return "".join(
        ch for ch in unicodedata.normalize("NFKD", text or "")
        if not unicodedata.combining(ch)
    )


def query_words(query):
    """Extrai palavras-chave relevantes da consulta para busca FTS5."""
    words = re.findall(r"[\w']+", (query or "").lower())
    base = [w for w in words if w not in STOPWORDS and (len(w) > 1 or w.isdigit())]
    expanded = list(base)
    for w in base:
        for syn in PTBR_SYNONYMS.get(w, ()):
            if syn not in expanded:
                expanded.append(syn)
    return expanded[:14]


def _snippet(text, words, width=360):
    flat = " ".join(line.lstrip("#").strip() for line in text.splitlines() if line.strip())
    low = flat.lower()
    hits = [low.find(w) for w in words if low.find(w) >= 0]
    start = max(0, min(hits) - 80) if hits else 0
    out = flat[start:start + width]
    return ("..." if start else "") + out + ("..." if start + width < len(flat) else "")


class LibraryRAG:
    """Leitor somente-leitura do índice FTS5 SQLite (library.noindex/index.sqlite)."""

    def __init__(self, db_path=None, text_dir=None):
        self.db_path = db_path or DB_PATH
        self.text_dir = text_dir or TEXT_DIR
        self.db = None
        self._connect()

    def _connect(self):
        if not os.path.exists(self.db_path):
            self.db = None
            return
        try:
            self.db = sqlite3.connect(
                f"file:{self.db_path}?mode=ro", uri=True, check_same_thread=False
            )
            self.db.execute("SELECT 1 FROM sqlite_master LIMIT 1").fetchone()
        except sqlite3.OperationalError:
            try:
                self.db = sqlite3.connect(
                    f"file:{self.db_path}?immutable=1", uri=True, check_same_thread=False
                )
            except sqlite3.Error:
                self.db = None
        except sqlite3.Error:
            self.db = None

    def reload(self):
        if self.db is not None:
            try:
                self.db.close()
            except sqlite3.Error:
                pass
            self.db = None
        self._connect()

    @property
    def available(self):
        if self.db is None:
            self._connect()
        return self.db is not None

    def stats(self):
        """Retorna (total_artigos, total_fontes)."""
        if not self.available:
            return 0, 0
        try:
            row = self.db.execute(
                "SELECT COUNT(*), COALESCE(SUM(docs), 0) FROM sources WHERE done=1"
            ).fetchone()
            return (row[1] or 0), (row[0] or 0)
        except sqlite3.Error:
            return 0, 0

    def _read_bytes(self, file_id, offset, length):
        row = self.db.execute("SELECT path FROM files WHERE id=?", (file_id,)).fetchone()
        if not row:
            return b""
        full_path = os.path.join(self.text_dir, row[0])
        if not os.path.exists(full_path):
            return b""
        with open(full_path, "rb") as f:
            f.seek(offset)
            return f.read(length)

    def _read_text(self, file_id, offset, length):
        return self._read_bytes(file_id, offset, length).decode("utf-8", "replace")

    def search(self, query, limit=5, allow_or=True):
        """Busca passagens relevantes via FTS5 BM25."""
        if not self.available:
            return []
        words = query_words(query)
        if not words:
            return []
        terms = ['"' + w.replace('"', "") + '"' for w in words]
        joiners = (" ", " OR ") if allow_or else (" ",)
        hits = []
        try:
            for joiner in joiners:
                hits = self.db.execute(
                    "SELECT rowid, rank FROM fts WHERE fts MATCH ? AND rank MATCH 'bm25(4.0, 1.0)' "
                    "ORDER BY rank LIMIT 150",
                    (joiner.join(terms),),
                ).fetchall()
                if len(hits) >= 3 or len(words) == 1:
                    break
        except sqlite3.Error:
            return []

        if not hits:
            return []

        rank = dict(hits)
        marks = ",".join("?" * len(rank))
        try:
            rows = self.db.execute(
                "SELECT p.id, d.id, d.title, s.label, s.topic, d.file_id, p.offset, p.length, s.key "
                f"FROM passages p JOIN docs d ON d.id = p.doc_id JOIN sources s ON s.id = d.source_id "
                f"WHERE p.id IN ({marks})",
                list(rank),
            ).fetchall()
        except sqlite3.Error:
            return []

        info = {r[0]: r for r in rows}
        asks_meds = any(
            m in _strip_accents(query.lower())
            for m in ("remedio", "medicamento", "farmacia", "bula", "comprimido", "pomada", "antibiotico")
        )
        order = sorted(
            info,
            key=lambda pid: rank[pid] * AUTHORITY.get(info[pid][8], 1.0) * (1.35 if asks_meds and info[pid][8] == "anvisa-bulas" else 1.0),
        )

        results = []
        seen_docs = set()
        min_matches = 1 if len(words) <= 1 else min(len(words), max(2, math.ceil(len(words) * 0.4)))
        bib_words = ("biblia", "bíblia", "jesus", "deus", "salmo", "evangelho", "versiculo", "versículo", "genesis", "gênesis", "mateus", "lucas", "joao", "joão", "marcos", "atos", "apocalipse", "exodo", "êxodo", "proverbios", "provérbios", "isaias", "isaías", "corintios", "coríntios", "romanos", "timoteo", "timóteo")
        wants_bible = any(b in _strip_accents(query.lower()) for b in bib_words)
        has_non_bible_title_hit = any(
            not info[pid][2].startswith("Bíblia Católica")
            and any(_strip_accents(w) in _strip_accents(info[pid][2].lower()) for w in words)
            for pid in order[:10]
        )
        for pid in order:
            r = info[pid]
            doc_id = r[1]
            if doc_id in seen_docs:
                continue
            if has_non_bible_title_hit and not wants_bible and r[2].startswith("Bíblia Católica"):
                continue
            text = self._read_text(r[5], r[6], r[7])
            if not text.strip():
                continue
            haystack = _strip_accents((r[2] + " " + text).lower())
            matched_words = sum(1 for w in set(words) if _strip_accents(w) in haystack)
            if matched_words < min_matches:
                continue
            seen_docs.add(doc_id)
            results.append({
                "id": pid,
                "doc_id": doc_id,
                "title": r[2],
                "source": r[3],
                "topic": r[4],
                "official": r[8] in OFFICIAL_KEYS,
                "snippet": _snippet(text, words),
                "text": text[:2000],
            })
            if len(results) >= limit:
                break
        return results

    def document(self, passage_id):
        """Retorna o artigo completo contendo a passagem para leitura na UI."""
        if not self.available:
            return None
        try:
            row = self.db.execute(
                "SELECT d.id, d.title, s.label, d.url, d.file_id, d.offset, d.length, s.key, s.license "
                "FROM passages p JOIN docs d ON d.id = p.doc_id JOIN sources s ON s.id = d.source_id "
                "WHERE p.id=?",
                (passage_id,),
            ).fetchone()
            if not row:
                return None
            doc_id, title, label, url, file_id, start, length, key, lic = row
            raw = self._read_bytes(file_id, start, length)
            parts = []
            for pid, off, n in self.db.execute(
                "SELECT id, offset, length FROM passages WHERE doc_id=? ORDER BY id", (doc_id,)
            ):
                chunk = raw[off - start: off - start + n].decode("utf-8", "replace")
                parts.append({"id": pid, "text": chunk})
            return {
                "doc_id": doc_id,
                "title": title,
                "source": label,
                "url": url or "",
                "official": key in OFFICIAL_KEYS,
                "license": lic or "",
                "focus": passage_id,
                "parts": parts,
            }
        except sqlite3.Error:
            return None


_DIRECT_OPENER = urllib.request.build_opener(urllib.request.ProxyHandler({}))


def check_llama_status(llama_host=None):
    """Verifica se o motor llama-server na porta 9931 está ativo."""
    host = llama_host or LLAMA_HOST
    for endpoint in ("/health", "/v1/models"):
        try:
            req = urllib.request.Request(host + endpoint, method="GET")
            with _DIRECT_OPENER.open(req, timeout=1.5) as resp:
                if 200 <= resp.status < 300:
                    return {"online": True, "port": DEFAULT_LLAMA_PORT, "host": host}
        except Exception:
            continue
    return {"online": False, "port": DEFAULT_LLAMA_PORT, "host": host}


def _normalize_image_url(img):
    if not img:
        return None
    if img.startswith("data:image/"):
        return img
    return f"data:image/jpeg;base64,{img}"


def build_rag_context(passages):
    if not passages:
        return ""
    blocks = []
    for i, p in enumerate(passages, 1):
        blocks.append(
            f"[FONTE {i}: {p['title']} — {p['source']}]\n{p['text'].strip()}"
        )
    return (
        "\n\n=== CONTEXTO DA BIBLIOTECA OFFLINE (USE COMO BASE PRINCIPAL) ===\n"
        + "\n\n---\n\n".join(blocks)
        + "\n=== FIM DO CONTEXTO ==="
    )


def prepare_messages(history, user_text, passages, has_image=False, geo_context=""):
    """Monta a lista de mensagens no formato OpenAI chat/completions com RAG e travas."""
    sys_parts = [SYSTEM_PROMPT_BASE]
    if has_image:
        sys_parts.append(VISUAL_SAFETY_DIRECTIVE)
    low_user = (user_text or "").lower()
    if any(k in low_user for k in ("cobra", "serpente", "aranha", "escorpi", "picada", "picado", "mordida", "mordido")):
        sys_parts.append(
            "[TRIAGEM OBRIGATÓRIA DE ANIMAIS PEÇONHENTOS]\n"
            "Além dos primeiros socorros seguros (lavar com água e sabão, retirar anéis/relógios, manter repouso, "
            "NUNCA fazer torniquete nem cortar/sugar, ir ao hospital para soro), PERGUNTE ao usuário para ajudar na triagem "
            "(sem tentar capturar o bicho):\n"
            "- Se cobra: tinha chocalho na cauda (cascavel), anéis coloridos (coral) ou manchas/cabeça triangular (jararaca)? "
            "Há inchaço forte, sangramento, visão turva/pálpebra caída ou urina escura?\n"
            "- Se aranha/escorpião: era grande e levantava as patas (armadeira), pequena marrom (aranha-marrom, risco de necrose) "
            "ou preta com mancha vermelha? A dor é imediata e intensa ou demorou a aparecer?\n"
            "Nunca garanta que o animal é inofensivo apenas pela descrição."
        )
    if geo_context:
        sys_parts.append(geo_context)
    rag_ctx = build_rag_context(passages)
    if rag_ctx:
        sys_parts.append(rag_ctx)
    elif not geo_context and not has_image:
        sys_parts.append(
            "[ATENÇÃO: NENHUM MANUAL LOCAL CORRESPONDEU DIRETAMENTE À CONSULTA]\n"
            "1. Se for pergunta MÉDICA, de DOSAGEM DE REMÉDIO ou EMERGÊNCIA: NÃO invente protocolos nem adapte manuais errados. "
            "Diga brevemente que não consta nos manuais locais e faça 1 ou 2 perguntas objetivas para entender melhor o caso (sem mandar ao hospital por sintomas leves).\n"
            "2. Se for pergunta de CONHECIMENTO GERAL, MATEMÁTICA, LÓGICA ou RACIOCÍNIO (sem risco médico): você pode responder usando seu conhecimento próprio APENAS se tiver certeza absoluta. "
            "Se não tiver certeza ou não puder garantir precisão exata de memória (ex.: centenas de casas decimais de Pi), diga honestamente o limite do que sabe sem inventar."
        )

    messages = [{"role": "system", "content": "\n\n".join(sys_parts)}]

    # Isola o histórico para evitar contaminação entre assuntos distintos
    # (ex.: pergunta anterior sobre fogo não deve vazar para pergunta nova sobre ferimento).
    q_words = set(query_words(user_text))
    low_ut = _strip_accents((user_text or "").lower())
    is_short_followup = (
        len((user_text or "").split()) <= 10
        and any(
            p in low_ut
            for p in (
                "explique", "resuma", "simplifique", "como se fosse", "desses", "esses",
                "isso", "disso", "ela", "ele", "elas", "eles", "voce nao disse",
                "nao respondeu", "continua", "mais detalhes", "e se",
            )
        )
    )

    hist_slice = (history or [])[-8:]
    if passages and q_words and not is_short_followup:
        # Mantém apenas pares (user+assistant) do histórico que compartilham ao menos 1 termo relevante
        filtered_hist = []
        i = 0
        while i < len(hist_slice):
            m = hist_slice[i]
            if m.get("role") == "user":
                m_words = set(query_words(m.get("content", "")))
                if m_words & q_words:
                    filtered_hist.append(m)
                    if i + 1 < len(hist_slice) and hist_slice[i + 1].get("role") == "assistant":
                        filtered_hist.append(hist_slice[i + 1])
                i += 2
            else:
                i += 1
        hist_slice = filtered_hist

    for msg in hist_slice:
        role = msg.get("role")
        content = msg.get("content")
        if role in ("user", "assistant") and isinstance(content, str) and content.strip():
            messages.append({"role": role, "content": content.strip()})

    return messages


def stream_chat(
    rag: LibraryRAG,
    user_text: str,
    history=None,
    images=None,
    llama_host=None,
    max_tokens=1536,
    temperature=0.2,
):
    """Executa busca RAG, aplica travas de segurança e faz stream do llama-server (9931)."""
    host = llama_host or LLAMA_HOST
    images = [img for img in (images or []) if isinstance(img, str) and img.strip()]
    has_image = len(images) > 0

    # Trava determinística absoluta: nunca ensinar cirurgia/procedimento invasivo caseiro (ex.: traqueotomia)
    low_pre = _strip_accents((user_text or "").lower())
    invasive_terms = (
        "traqueotomia", "traqueostomia", "cricotireoidostomia",
        "punção venosa", "puncao venosa", "acesso venoso",
        "costurar ferida", "sutura caseira", "fazer cirurgia", "abrir barriga",
    )
    if any(t in low_pre for t in invasive_terms):
        yield {"type": "sources", "sources": []}
        yield {
            "type": "red_alert",
            "title": "PROCEDIMENTO INVASIVO / CIRÚRGICO BLOQUEADO",
            "steps": [
                "O TaVivo não ensina traqueotomia, punção venosa ou cirurgias caseiras (risco altíssimo de morte imediata).",
                "Se a pessoa está engasgada: aplique Manobra de Heimlich (ou 5 tapinhas + 5 compressões em bebês).",
                "Se não respira: inicie RCP (100–120 compressões/min) e acione SAMU 192 / Bombeiros 193 imediatamente.",
            ],
        }
        yield {
            "type": "token",
            "text": "Por segurança de vida, não forneço instruções para procedimentos cirúrgicos invasivos sem equipe médica. Se houver obstrução de via aérea, informe se a pessoa está engasgada ou inconsciente para eu orientar os primeiros socorros seguros (Heimlich / RCP).",
        }
        yield {"type": "done"}
        return

    geo_context = GEO.analyze_query(user_text) if (GEO and user_text.strip()) else ""
    low_ut = _strip_accents((user_text or "").lower())
    is_followup_rewrite = bool(history) and any(
        p in low_ut for p in ("explique", "resuma", "simplifique", "como se fosse", "desses itens", "esses itens", "so do livro", "apenas do livro", "nao misture")
    )
    passages = (
        rag.search(user_text, limit=3, allow_or=not bool(geo_context))
        if (rag and user_text.strip() and not is_followup_rewrite)
        else []
    )
    yield {
        "type": "sources",
        "sources": [
            {
                "id": p["id"],
                "title": p["title"],
                "source": p["source"],
                "official": p["official"],
                "snippet": p["snippet"],
            }
            for p in passages
        ],
    }

    if has_image:
        yield {
            "type": "safety",
            "visual_lock": True,
            "message": (
                "Trava de Segurança Visual ativada: o modelo está proibido de identificar "
                "plantas, folhas ou fungos como comestíveis ou próprios para chá."
            ),
        }

    # Cartão Vermelho instantâneo (< 50ms) apenas para risco imediato de vida
    low_pre = (user_text or "").lower()
    if any(k in low_pre for k in ("não respira", "nao respira", "parada cardíaca", "parada cardiaca", "sem pulso")):
        yield {
            "type": "red_alert",
            "title": "AÇÃO IMEDIATA — PARADA CARDÍACA / RCP",
            "steps": [
                "Chame SAMU 192 / Bombeiros 193 (peça um DEA se houver).",
                "Inicie compressões fortes e rápidas no centro do peito (100 a 120/min, ~5 cm).",
                "Não pare até a vítima reagir ou chegar socorro.",
            ],
        }
    elif any(k in low_pre for k in ("engasg", "sufocando")):
        yield {
            "type": "red_alert",
            "title": "AÇÃO IMEDIATA — ENGASGO GRAVE",
            "steps": [
                "Se não consegue tossir nem falar: faça compressões abdominais para dentro e para cima (Manobra de Heimlich).",
                "Em bebê (< 1 ano): 5 tapinhas firmes nas costas + 5 compressões no centro do peito.",
            ],
        }
    elif any(k in low_pre for k in ("hemorragia", "jato de sangue", "sangrando muito", "arterial")):
        yield {
            "type": "red_alert",
            "title": "AÇÃO IMEDIATA — HEMORRAGIA GRAVE",
            "steps": [
                "Pressione firme direto sobre a ferida com pano limpo sem soltar.",
                "Se jorrar sangue e não parar em membro: aplique torniquete 5–7 cm acima da ferida e anote o horário.",
            ],
        }
    elif any(k in low_pre for k in ("soda cáustica", "soda caustica", "ácido", "acido")) and any(k in low_pre for k in ("engoliu", "ingeriu", "bebeu")):
        yield {
            "type": "red_alert",
            "title": "AÇÃO IMEDIATA — INGESTÃO CÁUSTICA",
            "steps": [
                "NUNCA provoque vômito (queima o esôfago duas vezes).",
                "Não dê leite ou misturas; guarde a embalagem e busque emergência (SAMU 192).",
            ],
        }

    messages = prepare_messages(history, user_text, passages, has_image=has_image, geo_context=geo_context)

    final_user_text = user_text.strip() or "Analise a imagem enviada seguindo as regras de segurança."
    if has_image:
        content_parts = [
            {
                "type": "text",
                "text": (
                    f"{final_user_text}\n\n"
                    "[LEMBRETE DE SEGURANÇA: Não afirme nem chute que qualquer planta, folha ou fungo "
                    "na imagem é comestível ou serve para chá.]"
                ),
            }
        ]
        for img in images[:3]:
            url = _normalize_image_url(img)
            if url:
                content_parts.append({"type": "image_url", "image_url": {"url": url}})
        messages.append({"role": "user", "content": content_parts})
    else:
        messages.append({"role": "user", "content": final_user_text})

    payload = {
        "model": "LFM3-Omni-2B",
        "messages": messages,
        "stream": True,
        "temperature": temperature,
        "top_p": 0.9,
        "repeat_penalty": 1.12,
        "max_tokens": max_tokens,
    }

    req = urllib.request.Request(
        host + "/v1/chat/completions",
        data=json.dumps(payload).encode("utf-8"),
        headers={"Content-Type": "application/json"},
        method="POST",
    )

    botanical_keywords = (
        "folha", "planta", "erva", "chá", "cha", "comer", "comestível", "comestivel",
        "cogumelo", "fungo", "fruto", "raiz", "semente", "salsa", "boldo", "veneno",
    )
    animal_keywords = (
        "cobra", "serpente", "jararaca", "cascavel", "coral", "aranha", "escorpião",
        "escorpiao", "inseto", "lagarta", "animal", "bicho", "inofensiva", "pegar", "mão", "mao",
    )
    low_q = final_user_text.lower()
    is_botanical_query = has_image and any(k in low_q for k in botanical_keywords)
    is_animal_query = has_image and any(k in low_q for k in animal_keywords)

    generated_chunks = []
    try:
        with _DIRECT_OPENER.open(req, timeout=300) as resp:
            for raw_line in resp:
                line = raw_line.decode("utf-8", "replace").strip()
                if not line or not line.startswith("data:"):
                    continue
                data_str = line[5:].strip()
                if data_str == "[DONE]":
                    break
                try:
                    chunk = json.loads(data_str)
                except ValueError:
                    continue
                choices = chunk.get("choices") or []
                if not choices:
                    continue
                delta = choices[0].get("delta") or {}
                token = delta.get("content")
                if token:
                    generated_chunks.append(token)
                    yield {"type": "token", "text": token}
    except urllib.error.URLError as exc:
        yield {
            "type": "error",
            "message": (
                f"Motor IA offline na porta {DEFAULT_LLAMA_PORT} ({host}). "
                f"Verifique se o llama-server foi iniciado. Detalhe: {exc.reason}"
            ),
        }
        return
    except Exception as exc:
        yield {"type": "error", "message": f"Erro ao consultar Motor IA (9931): {exc}"}
        return

    full_reply = "".join(generated_chunks).strip()
    low_reply = full_reply.lower()
    if is_botanical_query:
        has_clear_refusal = any(
            w in low_reply for w in ("não", "nao", "proibido", "tóxic", "toxic", "venen", "perig", "risco")
        )
        if len(full_reply) < 35 or not has_clear_refusal:
            guard_msg = (
                "\n\n[ALERTA DE SEGURANÇA DO AGENTE TAVIVO]\n"
                "NÃO consuma, não faça chá e não utilize esta planta/folha/fungo. "
                "A identificação visual por câmera não distingue espécies comestíveis de sósias "
                "tóxicas mortais (como cicuta ou espirradeira), e ferver para chá não destrói "
                "diversas toxinas letais."
            )
            yield {"type": "token", "text": guard_msg}
    elif is_animal_query:
        has_animal_caution = any(
            w in low_reply for w in ("distância", "distancia", "não toque", "nao toque", "não pegue", "nao pegue", "não tente capturar", "nao tente capturar")
        )
        if len(full_reply) < 35 or not has_animal_caution:
            guard_msg = (
                "\n\n[ALERTA DE SEGURANÇA DO AGENTE TAVIVO]\n"
                "Mantenha distância segura e NÃO tente pegar ou manusear este animal com as mãos. "
                "A identificação visual por câmera não garante que seja inofensivo. "
                "Em caso de picada, não faça torniquete nem corte o local; busque socorro médico (SAMU 192)."
            )
            yield {"type": "token", "text": guard_msg}

    quick_opts = []
    if not has_image and any(k in low_q for k in ("cobra", "serpente", "jararaca", "cascavel", "coral")):
        if not any(w in low_reply for w in ("chocalho", "anéis coloridos", "aneis coloridos", "visão turva", "descrev")):
            triage_msg = (
                "\n\nPara ajudar a identificar o risco (sem tentar capturar o animal), me responda:\n"
                "- Como era a cobra? (tinha chocalho na cauda, anéis coloridos, manchas escuras ou cabeça triangular?)\n"
                "- Há inchaço forte, sangramento, visão turva/pálpebra caída ou urina escura?"
            )
            yield {"type": "token", "text": triage_msg}
        quick_opts = ["Tinha chocalho", "Anéis coloridos", "Cabeça triangular / manchas", "Visão turva ou inchaço forte"]
    elif not has_image and any(k in low_q for k in ("aranha", "escorpi")):
        if not any(w in low_reply for w in ("armadeira", "aranha-marrom", "necrose", "descrev")):
            triage_msg = (
                "\n\nPara ajudar a avaliar a gravidade (sem tentar pegar o bicho), me responda:\n"
                "- Como era o animal? (aranha grande que levantava as patas, pequena marrom, preta com mancha vermelha ou escorpião?)\n"
                "- A dor é imediata e intensa ou apareceu horas depois com bolha/mancha escura?"
            )
            yield {"type": "token", "text": triage_msg}
        quick_opts = ["Aranha grande agressiva", "Pequena marrom / bolha", "Escorpião / dor imediata"]
    elif not has_image and any(k in low_q for k in ("queimadura", "queimou")):
        if not any(w in low_reply for w in ("bolha", "palma da mão", "rosto", "vias aéreas")):
            triage_msg = (
                "\n\nPara avaliar a gravidade da queimadura, me responda:\n"
                "- Há bolhas, pele esbranquiçada/carbonizada ou apenas vermelhidão?\n"
                "- A área é maior que a palma da mão da vítima ou atingiu rosto, mãos, pés ou vias aéreas?"
            )
            yield {"type": "token", "text": triage_msg}
        quick_opts = ["Só vermelhidão leve", "Tem bolhas", "Maior que a palma da mão", "Atingiu rosto ou mãos"]
    elif not has_image and ("febre" in low_q or (any(k in low_q for k in ("bebê", "bebe", "criança", "crianca")) and any(s in low_q for s in ("febre", "doente", "quente", "vômito", "vomito", "convuls", "mancha", "tosse", "dor")))):
        if not any(w in low_reply for w in ("idade", "meses", "rigidez", "manchas roxas")):
            triage_msg = (
                "\n\nPara ajudar na triagem com segurança, me responda:\n"
                "- Qual a idade aproximada da pessoa (se bebê menor de 3 meses, é urgência imediata)?\n"
                "- Há sinais de alarme como rigidez na nuca, manchas roxas na pele, falta de ar ou prostração?"
            )
            yield {"type": "token", "text": triage_msg}
        quick_opts = ["Bebê menor de 3 meses", "Criança > 1 ano sem sinais graves", "Manchas roxas ou rigidez"]
    elif not has_image and any(k in low_q for k in ("engoliu", "ingeriu", "veneno", "intoxica", "soda", "água sanitária", "agua sanitaria")):
        if not any(w in low_reply for w in ("qual produto", "há quanto tempo", "embalagem", "consciente")):
            triage_msg = (
                "\n\nPara orientar melhor (e NÃO provoque vômito sem saber o produto), me responda:\n"
                "- Qual substância/produto foi ingerido e há quanto tempo?\n"
                "- A pessoa está consciente e respirando normalmente?"
            )
            yield {"type": "token", "text": triage_msg}
        quick_opts = ["Está consciente e respirando", "Sonolenta ou desacordada", "Ingeriu produto cáustico/ácido"]
    elif not has_image and any(k in low_q for k in ("ansiedade", "pânico", "panico", "depress", "tristeza", "angústia", "angustia", "insônia", "insonia", "trauma", "vozes", "alucina", "bipolar", "mania")):
        if not any(w in low_reply for w in ("há quanto tempo", "2 semanas", "6 meses", "sono", "pensamentos")):
            triage_msg = (
                "\n\nPara fazer uma triagem emocional/clínica melhor (referência DSM-5-TR / CID-11 — não substitui médico), me conte:\n"
                "- Há quanto tempo esses sintomas acontecem (dias, mais de 2 semanas ou meses)?\n"
                "- Estão atrapalhando o sono, alimentação ou rotina? Há pensamentos de desistir ou se machucar?"
            )
            yield {"type": "token", "text": triage_msg}
        quick_opts = ["Começou há poucos dias", "Mais de 2 semanas", "Atrapalha sono e rotina", "Quero técnica TCC para acalmar agora"]

    if quick_opts:
        yield {"type": "quick_replies", "options": quick_opts}

    severe_kw = (
        "cobra", "serpente", "escorpi", "aranha", "hemorragia", "sangrando muito",
        "convuls", "espuma", "desmaio", "infarto", "avc", "dor no peito",
        "falta de ar", "afog", "choque elétrico", "choque eletrico",
        "queimadura", "fratura", "pneumotórax", "pneumotorax",
        "engoliu", "ingeriu", "veneno", "intoxica", "anafilax", "surto psic",
    )
    if any(k in low_q for k in severe_kw):
        yield {
            "type": "samu_offer",
            "message": "Emergência médica identificada. Deseja gerar um Resumo Clínico rápido (idade, peso, comorbidades, remédios) para mostrar/ler ao SAMU 192 ou Bombeiros 193?",
        }

    yield {"type": "done"}
