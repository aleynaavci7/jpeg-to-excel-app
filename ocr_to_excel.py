import os
import re
import pandas as pd
import pytesseract
from PIL import Image

pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

image_folder = "images"
data = []

def natural_sort_key(filename):
    return [
        int(text) if text.isdigit() else text.lower()
        for text in re.split(r"(\d+)", filename)
    ]

for filename in sorted(os.listdir(image_folder), key=natural_sort_key):

    if filename.lower().endswith((".jpg", ".jpeg", ".png")):
        image_path = os.path.join(image_folder, filename)

        print(f"Okunuyor: {filename}")

        img = Image.open(image_path)

        text = pytesseract.image_to_string(img, lang="tur+eng")

        data.append({
            "dosya_adi": filename,
            "tip": "HAM_OCR",
            "id": "",
            "sira_no": "",
            "ad_soyad": "",
            "proje": "",
            "okunan_metin": text
        })

        lines = text.splitlines()

        for line in lines:
            line = line.strip()

            if not line:
                continue

            if "|" in line:
                parts = line.split("|")

                if len(parts) >= 3:
                    sol_kisim = parts[0].strip()
                    ad_soyad = parts[1].strip()
                    proje = parts[2].strip()

                    sol_parcalar = sol_kisim.split()

                    id_no = ""
                    sira_no = ""

                    if len(sol_parcalar) >= 2:
                        id_no = sol_parcalar[-2]
                        sira_no = sol_parcalar[-1]
                    elif len(sol_parcalar) == 1:
                        id_no = sol_parcalar[0]

                    data.append({
                        "dosya_adi": filename,
                        "tip": "AYRILMIS",
                        "id": id_no,
                        "sira_no": sira_no,
                        "ad_soyad": ad_soyad,
                        "proje": proje,
                        "okunan_metin": line
                    })

df = pd.DataFrame(data)
df.to_excel("jpeg_sonuc.xlsx", index=False)

print("Bitti! jpeg_sonuc.xlsx oluşturuldu.")