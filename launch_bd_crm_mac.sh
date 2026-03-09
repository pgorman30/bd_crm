#!/bin/zsh

cd ~/Desktop/bd_crm

source .venv/bin/activate

export BD_CRM_DB_PATH="$HOME/Library/CloudStorage/GoogleDrive-philip.gorman20@gmail.com/My Drive/BD_CRM/data/bd_crm.sqlite"

python -m streamlit run app.py &

sleep 4

open http://localhost:8501

wait