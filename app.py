import os
import re
from io import BytesIO

import pandas as pd
import pytesseract
from PIL import Image
from flask import Flask, request, send_file, render_template, send_from_directory

# Windows için local geliştirme
import os

if os.name == "nt":
    pytesseract.pytesseract.tesseract_cmd = r"C:\Program Files\Tesseract-OCR\tesseract.exe"

app = Flask(__name__)

app.config["MAX_CONTENT_LENGTH"] = 2 * 1024 * 1024
ALLOWED_EXTENSIONS = {"jpg", "jpeg"}


@app.route("/favicon.ico")
def favicon():
    return send_from_directory(".", "icon.ico")


def allowed_file(filename):
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def natural_sort_key(name):
    return [
        int(t) if t.isdigit() else t.lower()
        for t in re.split(r"(\d+)", name)
    ]


def parse_line(line):
    line = line.strip()

    if not line:
        return []

    if "|" in line:
        return [p.strip() for p in line.split("|")]

    parts = re.split(r"\s{2,}", line)

    if len(parts) > 1:
        return [p.strip() for p in parts]

    return [line]


def make_unique_headers(headers):
    clean_headers = []
    used = {}

    for header in headers:
        header = header.strip()

        if not header:
            header = "Bos_Kolon"

        if header in used:
            used[header] += 1
            header = f"{header}_{used[header]}"
        else:
            used[header] = 1

        clean_headers.append(header)

    return clean_headers


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        files = request.files.getlist("files")

        if not files or files[0].filename == "":
            return render_template("index.html", error="Lütfen en az bir JPEG dosyası seçin.")

        for file in files:
            if not allowed_file(file.filename):
                return render_template(
                    "index.html",
                    error="Sadece .jpg veya .jpeg dosyası yükleyebilirsiniz."
                )

        files = sorted(files, key=lambda f: natural_sort_key(f.filename))

        rows = []
        headers = None

        try:
            for file in files:
                image = Image.open(file)

                text = pytesseract.image_to_string(
                    image,
                    lang="tur+eng",
                    config="--psm 6"
                )

                for line in text.splitlines():
                    line = line.strip()

                    if not line:
                        continue

                    parsed = parse_line(line)

                    if headers is None:
                        headers = make_unique_headers(parsed)
                        continue

                    row = {
                        "dosya": file.filename,
                        "okunan_metin": line
                    }

                    for i, header in enumerate(headers):
                        row[header] = parsed[i] if i < len(parsed) else ""

                    rows.append(row)

            if not rows:
                return render_template(
                    "index.html",
                    error="Görselden okunabilir tablo/veri çıkarılamadı."
                )

            df = pd.DataFrame(rows)

            output = BytesIO()
            df.to_excel(output, index=False)
            output.seek(0)

            return send_file(
                output,
                as_attachment=True,
                download_name="jpeg-to-excel-sonuc.xlsx",
                mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            return render_template(
                "index.html",
                error=f"Dosya işlenirken hata oluştu: {str(e)}"
            )

    return render_template("index.html")


if __name__ == "__main__":
    app.run(debug=True, port=5000)