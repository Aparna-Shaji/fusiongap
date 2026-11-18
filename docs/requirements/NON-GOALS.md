# FusionGap · Non-goals

**Status: BASELINED at gate 02 on 2026-11-18.** Changed only by a dated entry in
`docs/project/AMENDMENTS.md`. Authority: project brief v1 section 14, plus the scaling-law
exclusion named in the brief's role-alignment table (section 3). This list is the charter's EXCLUDED
tier; it reconciles those two sources rather than adding a third.

Scope discipline is a deliverable, not an omission. Each entry states what is refused and why, so an
absence cannot be mistaken for an oversight, and so a later "you should have done X" meets X already
on record as deliberately out, dated before any result existed.

Five of these are named in the target role's posting and are therefore recorded as honest gaps rather
than quiet silences: sparsity, Rust, distributed training, scaling laws, and authoring compiler passes
or intermediate representations.

| # | Not attempted | Why refused |
|---|---|---|
| 1 | A GEMM that beats cuBLAS | Without tensor cores this is unrealistic, and attempting it would consume the whole project. cuBLAS is decades of tuning |
| 2 | FlashAttention | FlashAttention-2 requires SM_80 features this GPU lacks. A correct FA1-style kernel is a project in its own right. Explicitly out of scope |
| 3 | A full compiler or a new intermediate representation | This project performs compiler *analysis*: it reads Inductor's generated code and explains it. It does not author compiler passes or IRs. Named as a gap — the posting asks for pass authoring |
| 4 | Distributed or multi-GPU kernels | One GPU. Not faked. Named as a gap |
| 5 | Sparsity methods | Named in the posting; genuinely out of reach on this hardware and timescale. Named as a gap |
| 6 | Rust | Named in the posting as an added advantage; not part of this project. Named as a gap |
| 7 | Beating Liger Kernel or Unsloth | They are tuned for datacenter GPUs by teams. This project measures and explains; it does not compete |
| 8 | Inference serving, batching, KV-cache | A different project |
| 9 | Scaling-law experiments | Named in the posting's responsibilities; needs compute this project does not have. Named as a gap |

**What is in scope and might be mistaken for one of the above:** fusing the elementwise middle of the
SwiGLU feed-forward while the surrounding matrix multiplies stay cuBLAS (REQ-F3); weight-only
quantization for a decode-shaped dequantise-fused GEMV, reported as a memory-traffic win rather than
an arithmetic one (REQ-F4); and reading Inductor's generated Triton as evidence (REQ-S4).
