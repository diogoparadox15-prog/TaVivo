<div align="center">

# 👍 TaVivo — I.A. de Sobrevivência

**Terminal Offline de Emergência · 100% Local · Sem Internet · A partir de 8 GB de RAM**

![Status](https://img.shields.io/badge/Modo-100%25%20Offline-00a884?style=for-the-badge)
![Modelo](https://img.shields.io/badge/Motor%20IA-LFM3--Omni--2B-1d9bf0?style=for-the-badge)
![Biblioteca](https://img.shields.io/badge/Biblioteca-Manuais%20Reais%20de%20Sobreviv%C3%AAncia-6366f1?style=for-the-badge)
![Sistemas](https://img.shields.io/badge/SO-Windows%20%7C%20Linux%20%7C%20macOS-334155?style=for-the-badge)
![Licença](https://img.shields.io/badge/Licen%C3%A7a-MIT-f59e0b?style=for-the-badge)

[Sobre](#-sobre-o-tavivo) · [O que vem no Kit](#-o-que-o-pacote-carrega) · [Como Iniciar](#-sistemas-suportados-e-como-iniciar-1-clique) · [Como Acessar](#-como-acessar) · [Pague um Café (BTC)](#-pague-um-café-doação-em-bitcoin)

</div>

---

> **O mundo vai acabar?** Não sei.  
> **Terá apagão da internet?** Não sei.  
> **Terá uma tempestade solar e desligará toda comunicação?** Não sei.  
> **Alguém vai explodir armamento químico ou atômico?** Também não sei.  
> **Extraterrestre ou zumbi?** Vai da crença de cada um.  
> **E se o seu celular perder sinal bem na hora que você mais precisa?** Pode acontecer hoje mesmo.  
> **E se você ficar sem o seu ChatGPT para te responder?** É aí que a maioria trava.  
>
> **Mas o mínimo que você precisa ter pra sobreviver é um pouco de *brio* e *ferramenta* para diferenciar você de uma ameba.**
>
> Pensando nisso, desenvolvi o **TaVivo**: uma I.A. 100% offline que não depende de internet nem de nuvem, projetada para rodar em computadores simples (a partir de **8 GB de RAM**) e ajudar você a sobreviver, agir com segurança e manter a cabeça no lugar quando tudo lá fora falhar.

---

<div align="center">

*“Ainda que eu atravesse o vale escuro, nada temerei, pois estais comigo.”* — **(Salmo 22/23, 4)**  
*“Alegrai-vos na esperança, sede pacientes na tribulação e perseverai na oração.”* — **(Romanos 12, 12)**

</div>

---

## 🧭 Sobre o TaVivo

O **TaVivo** é um kit portátil de inteligência artificial de emergência, **100% autônomo e offline**, projetado para rodar localmente em notebooks e PCs a partir de **8 GB de RAM** (sem internet, sem nuvem, sem torres de celular) — cabendo com folga em um pendrive de **4 GB**.

Comecei focando no Brasil (manuais, bulas comerciais e genéricas da ANVISA/SUS e os **5.571 municípios do IBGE**), mas o motor **LFM3-Omni-2B** também entende e responde em **Português, Inglês, Espanhol, Francês, Alemão, Italiano, Japonês, Coreano, Chinês e Árabe** — é só pedir. E, como é um projeto vivo, você pode sugerir melhorias e novos manuais.

---

## ☕ Pague um café (Doação em Bitcoin)

Se esta ferramenta offline puder ajudar você ou sua família em uma hora difícil, considere apoiar o desenvolvimento:

<div align="center">
  <img src="./app/static/doe_btc.png" alt="QR Code Bitcoin TaVivo" width="180">
  <br><br>
  <code>bc1q4fwx7ml5casg3hanr8ep382kwvwzht7hqsl0r7</code>
</div>

---

## 📦 O que o pacote carrega

| Componente | Tecnologia / Conteúdo | Função |
| :--- | :--- | :--- |
| **Motor IA Local** | `llama.cpp` + `LFM3-Omni-2B-Q4_K_M.gguf` + `mmproj` | Chat multimodal (texto + câmera/fotos) na porta `9931` |
| **Auto-Benchmark** | `tavivo_bench.py` (cache em `tavivo_hw.json`) | Detecta RAM, CPU e GPU na 1ª execução (piso seguro para 8 GB RAM) |
| **Interface Web** | `servidor_tavivo.py` (dual-stack IPv6/IPv4) | UI familiar com temas **X**, **WhatsApp** e **Branco** na porta `9876` |
| **Biblioteca Offline** | `index.sqlite` (SQLite FTS5 BM25) | Manuais reais indexados (medicina, bulas, psicologia, mecânica, rádio, Bíblia) |
| **Geo Offline** | `tavivo_geo.py` + `geo.sqlite` | **5.571 municípios (IBGE)** + **51 pontos de rios** (Haversine) |
| **Segurança & Triagem** | Trava Visual + Cartão Vermelho + Resumo SAMU | Bloqueia chutes perigosos e gera ficha clínica rápida |

<details>
<summary><strong>📚 Ver catálogo completo de áreas cobertas pelos 209 manuais</strong></summary>

- **Primeiros Socorros & Medicina**: hemorragias, torniquete, RCP, engasgo, queimaduras, parto de emergência, convulsões/PLS, pneumotórax (curativo de 3 pontas), sinais vitais e pressão arterial sem aparelho, anatomia vascular superficial (braço/perna), intoxicação química, lavagem ocular, doenças crônicas sem remédio (hipertensão, diabetes, epilepsia) e cuidados domésticos simples.
- **Farmacologia Brasil (Comerciais + Genéricos)**: resumos de bula, posologia adulto usual e contraindicações (Analgésicos, Antibióticos, Psiquiatria, Cardiologia, Endocrinologia, Gástricos como Inzelm/Izelm/Omeprazol, Dermatologia e Oftalmologia) + leitura de caixas de remédio por foto.
- **Saúde Mental & Psicologia**: **TCC**, Guia OMS/OPAS (*Faça o que importa em tempos de estresse*: *Grounding*, Desfusão, RPD, Exposição Gradual), regulação fisiológica e triagem baseada em **DSM-5-TR** e **CID-11**.
- **Sobrevivência, Água & Alimentos**: filtração, método SODIS, alambique solar, cloração, saneamento/latrina, conservação de alimentos sem geladeira (salga, secagem, pote Zeer), caça passiva, pesca, limpeza e preparo seguro de fauna silvestre (peixes, aves, capivara, gambá, tatu).
- **Engenharia, Mecânica, Rádio & Legislação**: roldanas/alavancas, eletricidade/baterias 12V, motores (gasolina, etanol, carburador, injeção, câmbio, diesel e carros elétricos/híbridos), rádio PX/VHF/SW, Código Q, Morse, LoRa/Meshtastic, apps offline (BitChat, Briar), CF/88 (Estado de Defesa, Estado de Sítio, GLO) e Lei Marcial.
- **Bíblia, Filosofia & Cultura**: **Bíblia Sagrada Católica completa** (Ave Maria — 73 livros indexados por capítulo), George Orwell (*1984* e *A Revolução dos Bichos*), Olavo de Carvalho, Napoleon Hill, *O Caibalion*, Estoicismo, Xadrez, Damas e jogos sem internet.

</details>

---

## ⚠️ Atenção — Leia o Aviso Legal

Antes de utilizar em situações reais ou redistribuir este pacote, leia integralmente o **[AVISO_LEGAL.md](./AVISO_LEGAL.md)** (limitações do modelo de IA compacto, riscos de identificação visual de plantas/animais, isenção de responsabilidade médica e canal de remoção por direitos autorais).

---

## 🚀 Sistemas Suportados e Como Iniciar (1 Clique)

### 🪟 Windows (10 / 11 — x64)
1. Extraia **todo** o conteúdo do `.zip` antes de executar (não execute de dentro do arquivo compactado).
2. Dê um duplo clique em **`TaVivo.bat`**.
3. Se o Windows exibir o alerta do SmartScreen (*"O Windows protegeu o seu computador"*), clique em **Mais informações** → **Executar mesmo assim**.
4. O pacote Windows já inclui Python 3.12 portátil embutido — o navegador abrirá em `http://127.0.0.1:9876`.

### 🐧 Linux (x64 / WSL2)
```bash
cd TaVivo_Emergency_Kit
chmod +x tavivo_linux.sh bin/llama-server
./tavivo_linux.sh
```
O navegador abrirá em `http://localhost:9876` (ou `http://127.0.0.1:9876`).

### 🍎 macOS (Apple Silicon / Intel)
```bash
cd TaVivo_Emergency_Kit
xattr -cr .
chmod +x tavivo_mac.sh bin/llama-server
./tavivo_mac.sh
```
> O `xattr -cr .` desbloqueia os binários portáteis no Gatekeeper na primeira execução. A versão macOS ativa aceleração **Metal (`-ngl 99`)** automaticamente.

---

## 🔌 Como Acessar

O navegador abre automaticamente ao iniciar, mas caso feche a aba, acesse:

- **Interface Web (TaVivo)**: `http://127.0.0.1:9876` (ou `http://localhost:9876`)

---

## 📜 Licenças e Créditos

- **llama.cpp**: Licença MIT
- **LFM3-Omni (Liquid Foundation Models)**: Liquid Open License / Apache 2.0
- **Motor RAG TaVivo (SQLite FTS5 + GeoOffline)**: Licença MIT
- **Manuais e Enciclopédias (WikiMed, Wikilivros, Appropedia)**: Creative Commons CC BY-SA 3.0 / 4.0 e Domínio Público (FEMA, CDC, OMS/OPAS)
- **Python Standalone (Windows)**: PSF License

---

<div align="center">

**Construído por Capitain Of Cruzades.**

</div>
