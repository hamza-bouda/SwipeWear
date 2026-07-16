#!/bin/bash
# Attend le retour de Hugging Face puis lance le test complet.
URL="https://huggingface.co/Marqo/marqo-fashionSigLIP/resolve/main/open_clip_config.json"
for i in $(seq 1 40); do
  code=$(curl -sI --max-time 15 -o /dev/null -w "%{http_code}" "$URL")
  echo "[tentative $i/40] HF status: $code"
  if [ "$code" = "200" ]; then
    echo "=== Hugging Face est de retour — lancement du test ==="
    ./.venv/Scripts/python.exe -X utf8 test_stack_ia.py --all 2>&1 | tee rapport_test.txt
    exit $?
  fi
  sleep 90
done
echo "HF toujours indisponible apres 1h — relancer plus tard : python test_stack_ia.py --all"
exit 1
