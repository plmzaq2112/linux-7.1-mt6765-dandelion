which ffmpeg || echo "no ffmpeg"
python3 - <<'PY'
try:
    import PIL
    print("PIL", PIL.__version__)
except Exception as e:
    print("no PIL:", e)
PY
