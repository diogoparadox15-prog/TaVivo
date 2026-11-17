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
echo "  TaVivo - Terminal Offline de Emergência (Linux)"
echo "  Construído por Capitain Of Cruzades."
echo "============================================================================"
echo ""

if ! command -v python3 >/dev/null 2>&1; then
    echo "[ERRO] python3 não encontrado no sistema."
    exit 1
fi

chmod +x "${LLAMA_BIN}" 2>/dev/null || true

if [[ -x "${LLAMA_BIN}" && -f "${MODEL_PATH}" ]]; then
    echo "[1/2] Iniciando Motor IA (llama-server) na porta ${LLAMA_PORT}..."
    # Benchmark rápido e auto-ajuste de hardware (mantém piso seguro para >= 8 GB RAM)
    LLAMA_HW_ARGS="-c 4096 -np 1"
    if [[ -f "./tavivo_bench.py" ]]; then
        LLAMA_HW_ARGS="$(python3 ./tavivo_bench.py --args 2>/dev/null || echo '-c 4096 -np 1')"
    fi
    echo "      Perfil de hardware (tavivo_bench.py): ${LLAMA_HW_ARGS}"

    MMPROJ_ARGS=()
    if [[ -f "${MMPROJ_PATH}" ]]; then
        MMPROJ_ARGS=(--mmproj "${MMPROJ_PATH}")
    fi
    # shellcheck disable=SC2086
    LD_LIBRARY_PATH="./bin:${LD_LIBRARY_PATH:-}" "${LLAMA_BIN}" -m "${MODEL_PATH}" "${MMPROJ_ARGS[@]}" \
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
    URL="http://localhost:${WEB_PORT}"
    if grep -qi microsoft /proc/version 2>/dev/null && command -v cmd.exe >/dev/null 2>&1; then
        cmd.exe /c start "" "${URL}" >/dev/null 2>&1 || true
    elif command -v wslview >/dev/null 2>&1; then
        wslview "${URL}" >/dev/null 2>&1 || true
    elif command -v xdg-open >/dev/null 2>&1; then
        xdg-open "${URL}" >/dev/null 2>&1 || true
    elif command -v sensible-browser >/dev/null 2>&1; then
        sensible-browser "${URL}" >/dev/null 2>&1 || true
    elif command -v google-chrome >/dev/null 2>&1; then
        google-chrome "${URL}" >/dev/null 2>&1 || true
    elif command -v firefox >/dev/null 2>&1; then
        firefox "${URL}" >/dev/null 2>&1 || true
    fi
) &

export TAVIVO_LLAMA_PORT="${LLAMA_PORT}"
export TAVIVO_WEB_PORT="${WEB_PORT}"
python3 servidor_tavivo.py
