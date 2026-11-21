"""4C load generator. Saturates the GPU with short matmuls so telemetry can be
sampled under load. Short kernels on purpose: deviceQuery reports a kernel
run-time limit (the Windows display watchdog), so one long kernel risks a
driver reset mid-run. Usage: load_matmul.py [load_seconds] [settle_seconds]"""
import sys, time, datetime, torch

DUR    = float(sys.argv[1]) if len(sys.argv) > 1 else 45.0
SETTLE = float(sys.argv[2]) if len(sys.argv) > 2 else 8.0
N = 4096

def utc():
    return datetime.datetime.now(datetime.timezone.utc).strftime("%Y/%m/%d %H:%M:%S.%f")[:-3]

assert torch.cuda.is_available(), "CUDA not available"
dev = torch.device("cuda")
a = torch.randn(N, N, device=dev, dtype=torch.float32)
b = torch.randn(N, N, device=dev, dtype=torch.float32)
c = torch.empty(N, N, device=dev, dtype=torch.float32)
torch.mm(a, b, out=c)              # warm cuBLAS up outside the measured window
torch.cuda.synchronize()
print("DEVICE", torch.cuda.get_device_name(0), flush=True)
print("VRAM_MIB", round(torch.cuda.memory_allocated() / 2**20), flush=True)

print("SETTLE_START", utc(), flush=True)
time.sleep(SETTLE)
print("LOAD_START", utc(), flush=True)
t_end = time.monotonic() + DUR
n = 0
while time.monotonic() < t_end:
    torch.mm(a, b, out=c)
    n += 1
    if n % 10 == 0:                # keep the queue short so the clock reflects now
        torch.cuda.synchronize()
torch.cuda.synchronize()
print("LOAD_END", utc(), flush=True)
print("MATMULS", n, flush=True)
print("CHECKSUM", float(c[0, 0]), flush=True)
time.sleep(SETTLE)
print("SETTLE_END", utc(), flush=True)
