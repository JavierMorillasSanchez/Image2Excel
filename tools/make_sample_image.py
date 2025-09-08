# tools/make_sample_image.py
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

out_dir = Path("tests/data")
out_dir.mkdir(parents=True, exist_ok=True)
out_path = out_dir / "sample_text.png"

# Imagen blanca 800x300 con texto negro grande y alto contraste
img = Image.new("RGB", (800, 300), "white")
draw = ImageDraw.Draw(img)

# Fuente por defecto (portátil). No dependemos de ttf externos.
text = "Hola 123\nImage2Excel"
# Centramos el texto de forma simple
try:
    # PIL más reciente
    bbox = draw.multiline_textbbox((0, 0), text)
    w, h = bbox[2] - bbox[0], bbox[3] - bbox[1]
except AttributeError:
    # PIL más antigua - usar textsize
    w, h = draw.textsize(text)
x = (img.width - w) // 2
y = (img.height - h) // 2
draw.multiline_text((x, y), text, fill="black")

img.save(out_path)
print(f"✅ Creado: {out_path.resolve()}")
