"""Script de auxílio para preparar dependências e empacotar o TaVivo (.zip).

Gera os 3 pacotes independentes (Windows, Linux, macOS) em dist/:
  - TaVivo_Windows.zip (com python/ portátil CPython 3.12 + TaVivo.bat)
  - TaVivo_Linux.zip   (com tavivo_linux.sh + binários Linux)
  - TaVivo_macOS.zip   (com tavivo_mac.sh -ngl 99 + instruções Gatekeeper)

Uso:
  python3 preparar_pacote.py --check
  python3 preparar_pacote.py --download-deps
  python3 preparar_pacote.py --build-zips [--allow-incomplete]

Construído por Capitain Of Cruzades.
"""

import argparse
import json
import os
import shutil
import stat
import tarfile
import urllib.request
import zipfile

ROOT = os.path.dirname(os.path.abspath(__file__))
DIST_DIR = os.path.join(ROOT, "dist")
STAGING_DIR = os.path.join(ROOT, "_staging_deps")

CORE_FILES = [
    "README.md",
    "AVISO_LEGAL.md",
    "tavivo_agent.py",
    "tavivo_geo.py",
    "tavivo_bench.py",
    "servidor_tavivo.py",
    "preparar_pacote.py",
    "atualizar_biblioteca.py",
]

CORE_DIRS = [
    "app",
    "models",
    "library.noindex",
]

# URLs oficiais de referência (GitHub Releases)
PYTHON_WIN_STANDALONE_URL = (
    "https://github.com/astral-sh/python-build-standalone/releases/download/"
    "20241016/cpython-3.12.7+20241016-x86_64-pc-windows-msvc-install_only.tar.gz"
)
LLAMA_CPP_RELEASES_API = "https://api.github.com/repos/ggml-org/llama.cpp/releases?per_page=10"


def _download(url, dest):
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    print(f"Baixando {url} -> {dest}")
    req = urllib.request.Request(url, headers={"User-Agent": "TaVivo-Packager/1.0"})
    with urllib.request.urlopen(req, timeout=120) as resp, open(dest, "wb") as out:
        shutil.copyfileobj(resp, out)


def download_dependencies():
    """Baixa Python Standalone (Windows) e binários do llama.cpp para Win/Linux/Mac."""
    os.makedirs(STAGING_DIR, exist_ok=True)

    # 1. Python Standalone Windows (CPython 3.12)
    win_py_dir = os.path.join(STAGING_DIR, "windows", "python")
    if not os.path.exists(os.path.join(win_py_dir, "python.exe")):
        tgz_path = os.path.join(STAGING_DIR, "python-win.tar.gz")
        if not os.path.exists(tgz_path):
            _download(PYTHON_WIN_STANDALONE_URL, tgz_path)
        print("Extraindo Python Standalone para Windows...")
        with tarfile.open(tgz_path, "r:gz") as tar:
            tar.extractall(os.path.join(STAGING_DIR, "windows"))
    else:
        print("Python Standalone (Windows) já presente em _staging_deps/windows/python.")

    # 2. llama.cpp release assets
    print("Consultando última release com binários do llama.cpp...")
    req = urllib.request.Request(LLAMA_CPP_RELEASES_API, headers={"User-Agent": "TaVivo-Packager/1.0"})
    with urllib.request.urlopen(req, timeout=30) as resp:
        releases = json.loads(resp.read().decode("utf-8"))

    release = next((r for r in releases if len(r.get("assets", [])) > 5), {})
    assets = release.get("assets", [])
    targets = {
        "windows": lambda n: "win-vulkan-x64" in n and n.endswith(".zip"),
        "linux": lambda n: "ubuntu-vulkan-x64" in n and (n.endswith(".zip") or n.endswith(".tar.gz")),
        "macos": lambda n: "macos-arm64" in n and (n.endswith(".zip") or n.endswith(".tar.gz")),
    }
    for os_name, matcher in targets.items():
        match = next((a for a in assets if matcher(a["name"].lower())), None)
        if not match:
            print(f"[AVISO] Asset llama.cpp não encontrado automaticamente para {os_name}.")
            continue
        arc_path = os.path.join(STAGING_DIR, match["name"])
        if not os.path.exists(arc_path):
            _download(match["browser_download_url"], arc_path)
        bin_out = os.path.join(STAGING_DIR, os_name, "bin")
        os.makedirs(bin_out, exist_ok=True)
        if arc_path.endswith(".zip"):
            with zipfile.ZipFile(arc_path, "r") as zf:
                for member in zf.namelist():
                    base = os.path.basename(member)
                    if base.startswith("llama-server") or base.endswith((".dll", ".so", ".dylib")):
                        with zf.open(member) as src, open(os.path.join(bin_out, base), "wb") as dst:
                            shutil.copyfileobj(src, dst)
        elif arc_path.endswith(".tar.gz"):
            with tarfile.open(arc_path, "r:gz") as tf:
                for member in tf.getmembers():
                    base = os.path.basename(member.name)
                    if not (base.startswith("llama-server") or ".so" in base or base.endswith(".dylib")):
                        continue
                    out_file = os.path.join(bin_out, base)
                    if member.isfile():
                        src = tf.extractfile(member)
                        if src:
                            with open(out_file, "wb") as dst:
                                shutil.copyfileobj(src, dst)
                            if base == "llama-server":
                                os.chmod(out_file, 0o755)
                    elif member.issym():
                        if os.path.lexists(out_file):
                            os.remove(out_file)
                        os.symlink(os.path.basename(member.linkname), out_file)
        print(f"Binários extraídos para {bin_out}")


def check_workspace():
    """Verifica presença dos pesos GGUF, SQLite FTS5 e scripts."""
    checks = {
        "Modelo LFM3-Omni-2B-Uncensored-abliterated-Q4_K_M.gguf": os.path.join(ROOT, "models", "LFM3-Omni-2B-Uncensored-abliterated-Q4_K_M.gguf"),
        "Projetor mmproj-LFM3-Omni-2B-Q4_K_M.gguf": os.path.join(ROOT, "models", "mmproj-LFM3-Omni-2B-Q4_K_M.gguf"),
        "Banco SQLite FTS5 (index.sqlite)": os.path.join(ROOT, "library.noindex", "index.sqlite"),
    }
    ok = True
    print("=== Verificação de Integridade do Kit TaVivo ===")
    for label, path in checks.items():
        exists = os.path.isfile(path)
        status = "OK" if exists else "AUSENTE"
        print(f"  [{status}] {label} -> {path}")
        if not exists:
            ok = False
    return ok


def _add_file_to_zip(zf, src_path, arc_name, executable=False):
    is_large = src_path.endswith(".gguf") or os.path.getsize(src_path) > 32 * 1024 * 1024
    compress = zipfile.ZIP_STORED if is_large else zipfile.ZIP_DEFLATED
    if executable:
        zinfo = zipfile.ZipInfo.from_file(src_path, arc_name)
        zinfo.external_attr = (stat.S_IFREG | 0o755) << 16
        with open(src_path, "rb") as src, zf.open(zinfo, "w") as dst:
            shutil.copyfileobj(src, dst, length=1024 * 1024)
    else:
        zf.write(src_path, arc_name, compress_type=compress)


def _add_dir_to_zip(zf, src_dir, arc_prefix, exec_names=("llama-server",)):
    if not os.path.isdir(src_dir):
        return
    for root, _dirs, files in os.walk(src_dir):
        for fname in files:
            full = os.path.join(root, fname)
            rel = os.path.relpath(full, src_dir)
            arc = os.path.join(arc_prefix, rel).replace("\\", "/")
            is_exec = fname in exec_names or fname.endswith(".sh")
            _add_file_to_zip(zf, full, arc, executable=is_exec)


def build_zip_for_os(os_name):
    """Monta o .zip independente para windows, linux ou macos."""
    os.makedirs(DIST_DIR, exist_ok=True)
    zip_names = {
        "windows": "TaVivo_Windows.zip",
        "linux": "TaVivo_Linux.zip",
        "macos": "TaVivo_macOS.zip",
    }
    starters = {
        "windows": "TaVivo.bat",
        "linux": "tavivo_linux.sh",
        "macos": "tavivo_mac.sh",
    }

    zip_path = os.path.join(DIST_DIR, zip_names[os_name])
    root_arc = "TaVivo_Emergency_Kit"

    with zipfile.ZipFile(zip_path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        for fname in CORE_FILES:
            fpath = os.path.join(ROOT, fname)
            if os.path.isfile(fpath):
                _add_file_to_zip(zf, fpath, f"{root_arc}/{fname}")

        starter = starters[os_name]
        starter_path = os.path.join(ROOT, starter)
        if os.path.isfile(starter_path):
            _add_file_to_zip(
                zf, starter_path, f"{root_arc}/{starter}", executable=starter.endswith(".sh")
            )

        for dname in CORE_DIRS:
            _add_dir_to_zip(zf, os.path.join(ROOT, dname), f"{root_arc}/{dname}")

        # Binários específicos da plataforma (em _staging_deps/<os>/bin ou bin/)
        staged_bin = os.path.join(STAGING_DIR, os_name, "bin")
        if os.path.isdir(staged_bin):
            _add_dir_to_zip(zf, staged_bin, f"{root_arc}/bin")
        else:
            _add_dir_to_zip(zf, os.path.join(ROOT, "bin"), f"{root_arc}/bin")

        # Python portátil obrigatório na versão Windows
        if os_name == "windows":
            win_py = os.path.join(STAGING_DIR, "windows", "python")
            local_py = os.path.join(ROOT, "python")
            if os.path.isdir(win_py):
                _add_dir_to_zip(zf, win_py, f"{root_arc}/python")
            elif os.path.isdir(local_py):
                _add_dir_to_zip(zf, local_py, f"{root_arc}/python")
            else:
                print("[AVISO] Pasta python/ não encontrada para Windows. Rode --download-deps primeiro.")

    print(f"Pacote gerado: {zip_path}")


def main():
    parser = argparse.ArgumentParser(description="Empacotador TaVivo Emergency Kit")
    parser.add_argument("--check", action="store_true", help="Verifica arquivos e dependências")
    parser.add_argument("--download-deps", action="store_true", help="Baixa llama.cpp e Python Windows")
    parser.add_argument("--build-zips", action="store_true", help="Gera os 3 pacotes .zip em dist/")
    parser.add_argument("--allow-incomplete", action="store_true", help="Permite gerar .zip mesmo sem modelos/index")
    args = parser.parse_args()

    if not any([args.check, args.download_deps, args.build_zips]):
        parser.print_help()
        return

    if args.download_deps:
        download_dependencies()

    ok = check_workspace()
    if args.build_zips:
        if not ok and not args.allow_incomplete:
            print("\n[ERRO] Modelos ou index.sqlite ausentes. Use --allow-incomplete para gerar apenas a estrutura.")
            raise SystemExit(1)
        for os_name in ("windows", "linux", "macos"):
            build_zip_for_os(os_name)


if __name__ == "__main__":
    main()
