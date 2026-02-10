#!/usr/bin/env bash
set -e

if [ ! -d venv ]; then
    echo "Creating Python virtual environment..."
    python3 -m venv venv
fi
source venv/bin/activate
pip install -q -r requirements.txt

cleanup() {
    echo ""
    echo "Shutting down..."
    kill 0
}
trap cleanup EXIT

echo "Starting backend (Flask :5000) and frontend (Vite :3000)..."
echo "Press q to quit."
echo ""

python run.py &
npm run dev --prefix frontend &

while read -n1 -s key; do
    if [[ "$key" == "q" ]]; then
        exit 0
    fi
done
