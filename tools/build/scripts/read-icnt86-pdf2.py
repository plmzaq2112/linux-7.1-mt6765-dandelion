import pdfplumber

path = "/mnt/c/Users/31806/Documents/AI Project/Redmi 9A/kernel 7.1 mainline/data/assets/ICNT86xx_Application.pdf"
with pdfplumber.open(path) as pdf:
    for i in (4, 5, 13, 14, 15, 16, 17):
        if i < len(pdf.pages):
            txt = pdf.pages[i].extract_text() or ""
            print("=" * 20, "PAGE", i + 1, "=" * 20)
            print(txt[:2500])
