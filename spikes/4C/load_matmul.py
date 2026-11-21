"""4C load generator, version 2.

Phase order, and why it is unusual: version 1 took its idle baseline from an
8-second settle placed AFTER the cuBLAS warm-up. On this GPU that settle was
not idle -- 11 samples at 1380 MHz, 15.5 W, 46.4 C, the driver's Idle flag
clear throughout, six seconds after a synchronize(). The clock is held, not
decaying. Version 2 therefore takes the idle baseline before `torch` is
imported, so this process holds no CUDA context and the window is idle by
construction. The old settle is kept as a cool-down observation, never as a
baseline. The import sits below the idle phase deliberately; moving it to the
top would reintroduce the defect.

Short kernels on purpose: deviceQuery reports a kernel run-time limit -- the
Windows display watchdog -- so one long kernel risks a driver reset mid-run.

Usage: load_matmul.py [load_s] [idle_s] [settle_s]"""
import sys, time, datetime

DUR    = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
IDLE   = float(sys.argv[2]) if len(sys.argv) > 2 else 15.0
SETTLE = float(sys.argv[3]) if len(sys.argv) > 3 else 10.0
N = 4096

def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]

# phase 1 -- true idle: torch is not loaded, so no CUDA context exists here
print("IDLE_START", utc(), flush=True)
time.sleep(IDLE)
print("IDLE_END", utc(), flush=True)

import torch                                    # CUDA initialises below, not here
assert torch.cuda.is_available(), "CUDA not available"

# phase 2 -- setup and warm-up
dev = torch.device("cuda")
a = torch.randn(N, N, device=dev, dtype=torch.float32)
b = torch.randn(N, N, device=dev, dtype=torch.float32)
c = torch.empty(N, N, device=dev, dtype=torch.float32)
torch.mm(a, b, out=c)
torch.cuda.synchronize()
print("DEVICE", torch.cuda.get_device_name(0), flush=True)
print("VRAM_MIB", round(torch.cuda.memory_allocated() / 2**20), flush=True)
print("WARM_END", utc(), flush=True)
time.sleep(SETTLE)

# phase 3 -- the measured load
print("LOAD_START", utc(), flush=True)
t_end = time.monotonic() + DUR
n = 0
while time.monotonic() < t_end:
    torch.mm(a, b, out=c)
    n += 1
    if n % 10 == 0:
        torch.cuda.synchronize()
torch.cuda.synchronize()
print("LOAD_END", utc(), flush=True)
print("MATMULS", n, flush=True)
print("CHECKSUM", float(c[0, 0]), flush=True)

# phase 4 -- cool-down, recorded as an observation
time.sleep(SETTLE)
print("SETTLE_END", utc(), flush=True)
