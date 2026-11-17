#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")"

LLAMA_PORT="${TAVIVO_LLAMA_PORT:-9931}"
WEB_PORT="${TAVIVO_WEB_PORT:-9876}"
LLAMA_BIN="./bin/llama-server"
MODEL_PATH="./models/LFM3-Omni-2B-Uncensored-abliterated-Q4_K_M.gguf"
MMPROJ_PATH="./models/mmproj-LFM3-Omni-2B-Q4_K_M.gguf"
LLAMA_PID=""
export NO_PROXY="127.0.0.1,localhost"
export no_proxy="127.0.0.1,localhost"

cleanup() {
    if [[ -n "${LLAMA_PID}" ]] && kill -0 "${LLAMA_PID}" 2>/dev/null; then
        echo ""
        echo "Encerrando Motor IA (PID ${LLAMA_PID}, porta ${LLAMA_PORT})..."
        kill "${LLAMA_PID}" 2>/dev/null || true
        wait "${LLAMA_PID}" 2>/dev/null || true
    fi
}
trap cleanup EXIT INT TERM

echo "============================================================================"
echo "  TaVivo - Terminal Offline de Emergência (macOS)"
echo "  Construído por Capitain Of Cruzades."
echo "============================================================================"
echo ""
echo "[DICA macOS Gatekeeper]"
echo "  Se o macOS bloquear a execução na primeira vez, rode no Terminal:"
echo "    xattr -cr ."
echo "    chmod +x tavivo_mac.sh bin/llama-server"
echo ""

# Tenta remover atributos de quarentena caso já esteja rodando no Terminal
xattr -cr . 2>/dev/null || true

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERRO] python3 não encontrado. Instale o Python 3 ou Xcode Command Line Tools."
    exit 1
fi

chmod +x "${LLAMA_BIN}" 2>/dev/null || true

if [[ -x "${LLAMA_BIN}" && -f "${MODEL_PATH}" ]]; then
    echo "[1/2] Iniciando Motor IA (llama-server) na porta ${LLAMA_PORT}..."
    LLAMA_HW_ARGS="-c 4096 -np 1 -ngl 99"
    if [[ -f "./tavivo_bench.py" ]]; then
        LLAMA_HW_ARGS="$(python3 ./tavivo_bench.py --args 2>/dev/null || echo '-c 4096 -np 1 -ngl 99')"
    fi
    echo "      Perfil de hardware (tavivo_bench.py): ${LLAMA_HW_ARGS}"
    MMPROJ_ARGS=()
    if [[ -f "${MMPROJ_PATH}" ]]; then
        MMPROJ_ARGS=(--mmproj "${MMPROJ_PATH}")
    fi
    # shellcheck disable=SC2086
    DYLD_LIBRARY_PATH="./bin:${DYLD_LIBRARY_PATH:-}" "${LLAMA_BIN}" -m "${MODEL_PATH}" "${MMPROJ_ARGS[@]}" \
        --host 127.0.0.1 --port "${LLAMA_PORT}" ${LLAMA_HW_ARGS} \
        > /tmp/tavivo_llama.log 2>&1 &
    LLAMA_PID=$!
    sleep 1
    if ! kill -0 "${LLAMA_PID}" 2>/dev/null; then
        echo "[AVISO] llama-server encerrou logo ao iniciar. Ultimas linhas de /tmp/tavivo_llama.log:"
        tail -n 15 /tmp/tavivo_llama.log 2>/dev/null || true
    fi
else
    echo "[AVISO] Binário (${LLAMA_BIN}) ou modelo (${MODEL_PATH}) ausente."
    echo "        O servidor web iniciará, mas o Motor IA (${LLAMA_PORT}) ficará offline."
fi

echo "[2/2] Iniciando servidor TaVivo na porta ${WEB_PORT}..."
echo "      Acesse: http://127.0.0.1:${WEB_PORT}"
echo ""

(
    for _ in $(seq 1 40); do
        if python3 -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:${WEB_PORT}/api/status', timeout=1)" >/dev/null 2>&1; then
            break
        fi
        sleep 0.5
    done
    open "http://127.0.0.1:${WEB_PORT}" >/dev/null 2>&1 || true
) &

export TAVIVO_LLAMA_PORT="${LLAMA_PORT}"
export TAVIVO_WEB_PORT="${WEB_PORT}"
python3 servidor_tavivo.py
