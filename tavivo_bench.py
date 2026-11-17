"""Benchmark rápido e auto-configuração de hardware do TaVivo (Linux / Windows / macOS).

Detecta RAM, núcleos de CPU, GPU/VRAM e suporte real de backend GPU no binário
`llama-server` embutido, gerando flags ideais sem quebrar PCs com >= 8 GB de RAM.

Construído por Capitain Of Cruzades.
"""

import json
import os
import platform
import shutil
import subprocess
import sys
import time

ROOT = os.path.dirname(os.path.abspath(__file__))
HW_CACHE_PATH = os.path.join(ROOT, "tavivo_hw.json")


def get_ram_mb():
    system = platform.system()
    try:
        if system == "Linux":
            with open("/proc/meminfo", "r", encoding="utf-8") as f:
                for line in f:
                    if line.startswith("MemTotal:"):
                        kb = int(line.split()[1])
                        return kb // 1024
        elif system == "Darwin":
            out = subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True, timeout=2)
            return int(out.strip()) // (1024 * 1024)
        elif system == "Windows":
            import ctypes

            class MEMORYSTATUSEX(ctypes.Structure):
                _fields_ = [
                    ("dwLength", ctypes.c_ulong),
                    ("dwMemoryLoad", ctypes.c_ulong),
                    ("ullTotalPhys", ctypes.c_ulonglong),
                    ("ullAvailPhys", ctypes.c_ulonglong),
                    ("ullTotalPageFile", ctypes.c_ulonglong),
                    ("ullAvailPageFile", ctypes.c_ulonglong),
                    ("ullTotalVirtual", ctypes.c_ulonglong),
                    ("ullAvailVirtual", ctypes.c_ulonglong),
                    ("ullAvailExtendedVirtual", ctypes.c_ulonglong),
                ]

            stat = MEMORYSTATUSEX()
            stat.dwLength = ctypes.sizeof(MEMORYSTATUSEX)
            if ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(stat)):
                return stat.ullTotalPhys // (1024 * 1024)
    except Exception:
        pass
    return 8192


def detect_gpu():
    """Detecta GPU dedicada/integrada e VRAM aproximada (MB)."""
    system = platform.system()
    if shutil.which("nvidia-smi"):
        try:
            out = subprocess.check_output(
                ["nvidia-smi", "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                text=True,
                timeout=3,
            ).strip()
            if out:
                first = out.splitlines()[0]
                parts = [p.strip() for p in first.split(",")]
                name = parts[0]
                vram = int(float(parts[1])) if len(parts) > 1 else 0
                return {"name": name, "vram_mb": vram, "vendor": "nvidia"}
        except Exception:
            pass

    if system == "Darwin":
        try:
            out = subprocess.check_output(
                ["system_profiler", "SPDisplaysDataType"], text=True, timeout=4
            )
            if "Apple" in out or "Metal" in out:
                return {"name": "Apple Metal GPU", "vram_mb": get_ram_mb() // 2, "vendor": "apple"}
        except Exception:
            pass

    return {"name": "CPU apenas / integrada sem CUDA", "vram_mb": 0, "vendor": "none"}


def llama_supports_gpu_offload():
    """Verifica se o binário llama-server empacotado possui dispositivo GPU ativo."""
    system = platform.system()
    exe = "llama-server.exe" if system == "Windows" else "llama-server"
    bin_dir = os.path.join(ROOT, "bin")
    llama_bin = os.path.join(bin_dir, exe)
    if not os.path.exists(llama_bin):
        return False, []

    env = os.environ.copy()
    if system == "Linux":
        env["LD_LIBRARY_PATH"] = bin_dir + ":" + env.get("LD_LIBRARY_PATH", "")
    elif system == "Darwin":
        env["DYLD_LIBRARY_PATH"] = bin_dir + ":" + env.get("DYLD_LIBRARY_PATH", "")

    try:
        out = subprocess.check_output(
            [llama_bin, "--list-devices"],
            env=env,
            stderr=subprocess.STDOUT,
            text=True,
            timeout=4,
        )
        devices = [
            ln.strip()
            for ln in out.splitlines()
            if ln.strip()
            and not ln.strip().startswith("Available devices")
            and "(none)" not in ln
            and "llvmpipe" not in ln.lower()
            and "microsoft basic render" not in ln.lower()
        ]
        if devices:
            return True, devices
    except Exception:
        pass

    if system == "Darwin" and platform.machine() == "arm64":
        return True, ["Apple Metal (arm64)"]
    return False, []


def cpu_microbench_score():
    """Micro-benchmark rápido (~80ms) para aferir responsividade da CPU."""
    t0 = time.perf_counter()
    acc = 0
    for i in range(400_000):
        acc += (i * 3) ^ (i >> 2)
    dt = max(0.001, time.perf_counter() - t0)
    return round(400_000 / dt / 1_000_000, 2)  # Mops/s


def compute_profile(force=False):
    ram_mb = get_ram_mb()
    cores = os.cpu_count() or 4
    cur_os = platform.system()

    if not force and os.path.exists(HW_CACHE_PATH):
        try:
            with open(HW_CACHE_PATH, "r", encoding="utf-8") as f:
                cached = json.load(f)
            if (
                cached.get("os") == cur_os
                and cached.get("ram_mb") == ram_mb
                and cached.get("cpu_cores") == cores
                and isinstance(cached.get("args"), list)
            ):
                return cached
        except Exception:
            pass

    gpu = detect_gpu()
    bin_gpu_ok, llama_devices = llama_supports_gpu_offload()
    cpu_score = cpu_microbench_score()

    if ram_mb <= 9000:
        tier = "compat_8gb"
        ctx = 4096
        threads = min(cores, 4)
    elif ram_mb < 16000:
        tier = "balanced_12gb"
        ctx = 6144
        threads = min(cores, 8)
    else:
        tier = "high_16gb_plus"
        ctx = 8192
        threads = min(cores, 12)

    # Só ativa offload completo se houver backend GPU real e VRAM >= 2500 MB (ou desconhecida/Apple Silicon)
    vram = gpu.get("vram_mb", 0) or 0
    use_gpu = bin_gpu_ok and (vram == 0 or vram >= 2500 or gpu.get("vendor") == "apple")
    ngl = 99 if use_gpu else 0

    args = ["-c", str(ctx), "-t", str(threads), "-np", "1"]
    if ngl > 0:
        args.extend(["-ngl", str(ngl)])

    profile = {
        "os": platform.system(),
        "arch": platform.machine(),
        "ram_mb": ram_mb,
        "cpu_cores": cores,
        "cpu_mops": cpu_score,
        "gpu": gpu,
        "llama_bin_gpu_devices": llama_devices,
        "tier": tier,
        "ctx": ctx,
        "threads": threads,
        "ngl": ngl,
        "args": args,
    }
    try:
        with open(HW_CACHE_PATH, "w", encoding="utf-8") as f:
            json.dump(profile, f, indent=2, ensure_ascii=False)
    except Exception:
        pass
    return profile


def main():
    force = "--rebench" in sys.argv or "--force" in sys.argv
    prof = compute_profile(force=force)
    if "--args" in sys.argv:
        print(" ".join(prof["args"]))
        return
    print(json.dumps(prof, indent=2, ensure_ascii=False))


if __name__ == "__main__":
    main()
