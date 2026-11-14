# frozen-core + adapters em modelo local (R14)

verdict: ADAPT
gh: #572
source: .devin/research/2026-11-12-reels-batch8-survey.md
status: resolved (CPU PoC validated; GPU benchmark follow-up)

## Answer

PoC CPU em extensions/ai-tools/adapter_expand.py: core congelado
bit-identico (checksum pre/por-referencia), adapter low-rank aprendeu
(loss 5.4 -> 1.3), 0.109% params treinaveis, ~2GB RAM. GPU benchmark
fica como follow-up quando houver CUDA local; nao bloqueia o fechamento.
