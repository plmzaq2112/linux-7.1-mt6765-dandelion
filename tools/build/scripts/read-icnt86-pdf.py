import sys
try:
    import pdfplumber
except ImportError:
    print("NO_PDFPLUMBER")
    sys.exit(1)

path = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/data/assets/ICNT86xx_Application.pdf"
with pdfplumber.open(path) as pdf:
    print("pages:", len(pdf.pages))
    for i, page in enumerate(pdf.pages):
        txt = page.extract_text() or ""
        if any(k in txt for k in ("SPI", "0x1001", "0x1002", "寄存器", "reset", "复位")):
            print("=" * 20, "PAGE", i + 1, "=" * 20)
            print(txt[:3000])
