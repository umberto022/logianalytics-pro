"""Genera íconos PWA para LogiAnalytics Pro. Se ejecuta una sola vez."""
import os
from PIL import Image, ImageDraw, ImageFont

def create_icon(size: int, path: str):
    img = Image.new("RGB", (size, size), "#667eea")
    draw = ImageDraw.Draw(img)

    # Círculo interior
    margin = size // 8
    draw.ellipse([margin, margin, size - margin, size - margin], fill="#764ba2")

    # Texto "L"
    font_size = size // 2
    try:
        font = ImageFont.truetype("arial.ttf", font_size)
    except Exception:
        font = ImageFont.load_default()

    text = "L"
    bbox = draw.textbbox((0, 0), text, font=font)
    text_w = bbox[2] - bbox[0]
    text_h = bbox[3] - bbox[1]
    x = (size - text_w) // 2
    y = (size - text_h) // 2
    draw.text((x, y), text, fill="white", font=font)

    img.save(path, "PNG")
    print(f"Ícono creado: {path}")

if __name__ == "__main__":
    static_dir = os.path.join(os.path.dirname(__file__), "static")
    os.makedirs(static_dir, exist_ok=True)

    create_icon(192, os.path.join(static_dir, "icon-192.png"))
    create_icon(512, os.path.join(static_dir, "icon-512.png"))
    print("Íconos PWA generados correctamente.")
