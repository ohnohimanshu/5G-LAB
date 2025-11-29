#!/bin/bash

ssh -t core@10.7.43.12 << 'EOF'

echo "[INFO] Switching to project directory..."
cd oai-workshops/cn 

echo "--------------------------------------------------------"
echo "[STEP 1] Bringing DOWN the OAI Core..."
echo "--------------------------------------------------------"
sudo docker compose -f docker-compose.yml down

echo "--------------------------------------------------------"
echo "[STEP 5] Starting OAI Core Again (docker compose up)"
echo "--------------------------------------------------------"
sudo docker compose -f docker-compose.yml up -d

echo "--------------------------------------------------------"
echo "[STEP 6] Starting RAN & UE Again"
echo "--------------------------------------------------------"
sudo docker compose -f docker-compose-ran.yml up -d oai-gnb oai-nr-ue oai-nr-ue2


echo "--------------------------------------------------------"
echo "[INFO] ALL TASKS COMPLETED FOR THIS VM"
echo "--------------------------------------------------------"

EOF
