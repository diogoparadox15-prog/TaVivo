"""Módulo Geográfico Offline do TaVivo (5.571 municípios IBGE + principais rios do Brasil).

Calcula distâncias (Haversine), direção cardeal, rios mais próximos e
cidades vizinhas em milissegundos usando apenas SQLite e Python padrão.

Construído por Capitain Of Cruzades.
"""

import math
import os
import re
import sqlite3
import unicodedata

ROOT = os.path.dirname(os.path.abspath(__file__))
GEO_DB_PATH = os.environ.get(
    "TAVIVO_GEO_DB", os.path.join(ROOT, "library.noindex", "geo.sqlite")
)

GEO_TRIGGER_WORDS = (
    "distância", "distancia", "longe", "perto", "próximo", "proximo", "próxima", "proxima",
    "rio", "rios", "água", "agua", "rota", "caminho", "estrada", "rodovia", "km",
    "quilômetro", "quilometro", "cidade", "cidades", "município", "municipio", "estou em",
    "coordenada", "latitude", "longitude", "direção", "direcao", "norte", "sul", "leste", "oeste",
)


def _norm(text):
    s = unicodedata.normalize("NFKD", text or "").encode("ascii", "ignore").decode("ascii")
    return " ".join(s.lower().strip().split())


def haversine_km(lat1, lon1, lat2, lon2):
    r = 6371.0
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dp = math.radians(lat2 - lat1)
    dl = math.radians(lon2 - lon1)
    a = math.sin(dp / 2) ** 2 + math.cos(p1) * math.cos(p2) * math.sin(dl / 2) ** 2
    return 2 * r * math.atan2(math.sqrt(a), math.sqrt(1 - a))


def bearing_cardinal(lat1, lon1, lat2, lon2):
    p1, p2 = math.radians(lat1), math.radians(lat2)
    dl = math.radians(lon2 - lon1)
    x = math.sin(dl) * math.cos(p2)
    y = math.cos(p1) * math.sin(p2) - math.sin(p1) * math.cos(p2) * math.cos(dl)
    deg = (math.degrees(math.atan2(x, y)) + 360) % 360
    dirs = ("Norte", "Nordeste", "Leste", "Sudeste", "Sul", "Sudoeste", "Oeste", "Noroeste")
    return dirs[int((deg + 22.5) // 45) % 8]


class GeoOffline:
    def __init__(self, db_path=None):
        self.db_path = db_path or GEO_DB_PATH
        self.db = None
        self._city_index = None
        self._connect()

    def _connect(self):
        if not os.path.exists(self.db_path):
            self.db = None
            return
        try:
            self.db = sqlite3.connect(
                f"file:{self.db_path}?mode=ro", uri=True, check_same_thread=False
            )
            self.db.execute("SELECT 1 FROM municipios LIMIT 1").fetchone()
        except sqlite3.Error:
            self.db = None

    @property
    def available(self):
        if self.db is None:
            self._connect()
        return self.db is not None

    def _load_cities(self):
        if self._city_index is not None or not self.available:
            return
        rows = self.db.execute(
            "SELECT nome, nome_norm, uf, lat, lon, capital FROM municipios"
        ).fetchall()
        # Índice por nome normalizado (capitais primeiro em caso de homônimos)
        by_name = {}
        for nome, nnorm, uf, lat, lon, cap in rows:
            by_name.setdefault(nnorm, []).append(
                {"nome": nome, "uf": uf, "lat": lat, "lon": lon, "capital": cap}
            )
        for k in by_name:
            by_name[k].sort(key=lambda c: -c["capital"])
        self._city_index = by_name

    def find_cities_in_text(self, text):
        """Encontra até 2 cidades brasileiras citadas no texto."""
        self._load_cities()
        if not self._city_index:
            return []
        ntext = " " + re.sub(r"[^\w\s]", " ", _norm(text)) + " "
        words = ntext.split()
        found = []
        seen = set()
        # Tenta n-gramas de 4 até 1 palavra (para pegar 'sao paulo', 'rio de janeiro', etc.)
        i = 0
        while i < len(words):
            matched = None
            for n in (4, 3, 2, 1):
                if i + n > len(words):
                    continue
                cand = " ".join(words[i:i + n])
                if len(cand) < 3 or cand in ("de", "da", "do", "em", "na", "no", "para", "ate", "com", "rio", "agua", "sul", "norte"):
                    continue
                if cand in self._city_index:
                    # Checa se há UF logo após (ex: "campinas sp")
                    uf_next = words[i + n].upper() if i + n < len(words) and len(words[i + n]) == 2 else None
                    cands = self._city_index[cand]
                    pick = next((c for c in cands if c["uf"] == uf_next), cands[0])
                    key = (pick["nome"], pick["uf"])
                    if key not in seen:
                        seen.add(key)
                        found.append(pick)
                    matched = n
                    break
            i += matched if matched else 1
            if len(found) >= 2:
                break
        return found

    def nearest_rivers(self, lat, lon, limit=3):
        if not self.available:
            return []
        rows = self.db.execute("SELECT nome, bacia, trecho, lat, lon FROM rios").fetchall()
        best_by_river = {}
        for nome, bacia, trecho, rlat, rlon in rows:
            dist = haversine_km(lat, lon, rlat, rlon)
            if nome not in best_by_river or dist < best_by_river[nome]["km"]:
                best_by_river[nome] = {
                    "nome": nome,
                    "bacia": bacia,
                    "trecho": trecho,
                    "km": dist,
                    "dir": bearing_cardinal(lat, lon, rlat, rlon),
                }
        return sorted(best_by_river.values(), key=lambda x: x["km"])[:limit]

    def nearest_cities(self, lat, lon, limit=5, exclude_name=None):
        if not self.available:
            return []
        rows = self.db.execute("SELECT nome, uf, lat, lon FROM municipios").fetchall()
        out = []
        for nome, uf, clat, clon in rows:
            if exclude_name and nome == exclude_name:
                continue
            dist = haversine_km(lat, lon, clat, clon)
            out.append({
                "nome": nome,
                "uf": uf,
                "km": dist,
                "dir": bearing_cardinal(lat, lon, clat, clon),
            })
        out.sort(key=lambda x: x["km"])
        return out[:limit]

    def analyze_query(self, query):
        """Retorna texto estruturado com cálculos geodésicos exatos se a consulta for geográfica."""
        if not self.available:
            return ""
        low = query.lower()
        coord_match = re.search(r"(-?\d{1,2}\.\d+)\s*[,;\s]\s*(-?\d{1,2}\.\d+)", query)
        has_geo_word = any(w in low for w in GEO_TRIGGER_WORDS)
        if not coord_match and not has_geo_word:
            return ""

        lines = []
        cities = self.find_cities_in_text(query)

        if coord_match:
            lat, lon = float(coord_match.group(1)), float(coord_match.group(2))
            lines.append(f"Ponto informado (GPS): {lat:.4f}, {lon:.4f}")
            near_c = self.nearest_cities(lat, lon, limit=4)
            if near_c:
                lines.append("Cidades mais próximas: " + "; ".join(
                    f"{c['nome']}/{c['uf']} ({c['km']:.1f} km a {c['dir']})" for c in near_c
                ))
            near_r = self.nearest_rivers(lat, lon, limit=3)
            if near_r:
                lines.append("Rios mais próximos (referência de bacia): " + "; ".join(
                    f"{r['nome']} — trecho {r['trecho']} (~{r['km']:.1f} km a {r['dir']})" for r in near_r
                ))

        if len(cities) >= 2:
            c1, c2 = cities[0], cities[1]
            km_reta = haversine_km(c1["lat"], c1["lon"], c2["lat"], c2["lon"])
            km_estrada = km_reta * 1.25
            direcao = bearing_cardinal(c1["lat"], c1["lon"], c2["lat"], c2["lon"])
            horas_pe = km_estrada / 4.5
            horas_carro = km_estrada / 70.0
            lines.append(
                f"Distância {c1['nome']}/{c1['uf']} → {c2['nome']}/{c2['uf']}: "
                f"{km_reta:.1f} km em linha reta (direção {direcao}); "
                f"estimativa por estrada ~{km_estrada:.0f} km "
                f"(~{horas_carro:.1f}h de carro a 70 km/h ou ~{horas_pe:.0f}h a pé a 4,5 km/h)."
            )

        if len(cities) >= 1 and not coord_match:
            c = cities[0]
            near_r = self.nearest_rivers(c["lat"], c["lon"], limit=3)
            if near_r:
                lines.append(
                    f"Rios mais próximos de {c['nome']}/{c['uf']}: " + "; ".join(
                        f"{r['nome']} (trecho {r['trecho']}, ~{r['km']:.1f} km a {r['dir']})" for r in near_r
                    )
                )
            if len(cities) == 1:
                near_c = self.nearest_cities(c["lat"], c["lon"], limit=4, exclude_name=c["nome"])
                if near_c:
                    lines.append(
                        f"Cidades vizinhas de {c['nome']}/{c['uf']}: " + "; ".join(
                            f"{nc['nome']}/{nc['uf']} ({nc['km']:.1f} km a {nc['dir']})" for nc in near_c
                        )
                    )

        if not lines:
            return ""
        return (
            "\n\n=== DADOS GEOGRÁFICOS OFFLINE EXATOS (IBGE / HAVERSINE) ===\n"
            + "\n".join(lines)
            + "\n=== FIM DOS DADOS GEOGRÁFICOS ==="
        )
