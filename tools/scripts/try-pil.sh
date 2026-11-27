timeout 10 curl -sI https://pypi.org 2>&1 | head -3 || echo "no direct internet"
echo "---"
timeout 10 pip3 install --quiet pillow 2>&1 | tail -3
python3 - <<'PY'
try:
    import PIL
    print("PIL ok", PIL.__version__)
except Exception as e:
    print("PIL missing:", e)
PY
