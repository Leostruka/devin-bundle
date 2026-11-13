#!/bin/bash
GGUF=$(ls -d "$USERPROFILE/.cache/huggingface/hub/models--nvidia--NVIDIA-Nemotron-Labs-Dory1.0-4B-GGUF/snapshots/"*/)NVIDIA-Nemotron-Labs-Dory1.0-4B-Q5_K_M.gguf
LLAMA="$TEMP/llama-dory/build/bin/llama.exe"
cd /d/Programing/ai_workspace/devin-bundle
for K in 1 2 4; do
  taskkill //F //IM llama.exe 2>/dev/null
  sleep 3
  "$LLAMA" serve -m "$GGUF" --override-kv dory.num_loops=int:$K --port 8377 -t 8 -c 4096 > "$TEMP/dory-serve-k$K.log" 2>&1 &
  READY=0
  for i in $(seq 1 90); do
    sleep 2
    CODE=$(curl -s -o /dev/null -w "%{http_code}" -X POST http://127.0.0.1:8377/completion -H "Content-Type: application/json" -d '{"prompt":"hi","n_predict":1}')
    [ "$CODE" = "200" ] && READY=1 && break
  done
  echo "=== k=$K ready=$READY ==="
  [ "$READY" = "0" ] && continue
  python extensions/ai-tools/dory_sweep.py --cases .devin/evals/laya/skill-pick-v1/cases.heldout.json --loops $K --out .devin/scratch/dory-sweep/skill-pick-k$K.json 2>.devin/scratch/dory-sweep/skill-pick-k$K.err
  python extensions/ai-tools/dory_sweep.py --cases .devin/evals/laya/issue-category-v1/cases.heldout.json --loops $K --out .devin/scratch/dory-sweep/issue-cat-k$K.json 2>.devin/scratch/dory-sweep/issue-cat-k$K.err
  echo "=== k=$K done ==="
done
taskkill //F //IM llama.exe 2>/dev/null
echo "SWEEP COMPLETE"
