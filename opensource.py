import streamlit as st
import easyocr
from googletrans import Translator
from PIL import Image, ImageDraw, ImageFont
import tempfile
import os

# === CONFIG ===
FONT_PATH = "arial.ttf"  # Make sure this supports Cyrillic (e.g., DejaVuSans, Arial Unicode, etc.)
FONT_SIZE = 20


# === Step 1: Extract Chinese Text ===
def extract_chinese_text(image_path):
    reader = easyocr.Reader(['ch_sim', 'en'], gpu=False)
    results = reader.readtext(image_path)

    chinese_texts = []
    boxes = []

    for bbox, text, conf in results:
        if any('\u4e00' <= ch <= '\u9fff' for ch in text):
            chinese_texts.append(text)
            boxes.append(bbox)

    return chinese_texts, boxes


# === Step 2: Translate to Russian ===
def translate_to_russian(texts):
    translator = Translator()
    translations = []
    for txt in texts:
        try:
            translated = translator.translate(txt, src='zh-cn', dest='ru')
            translations.append(translated.text)
        except Exception:
            translations.append("[Ошибка перевода]")
    return translations


# === Step 3: Replace Text ===
def replace_text_in_image(image_path, boxes, translated_texts):
    image = Image.open(image_path).convert("RGB")
    draw = ImageDraw.Draw(image)
    font = ImageFont.truetype(FONT_PATH, FONT_SIZE)

    for box, translated_text in zip(boxes, translated_texts):
        x_coords = [int(pt[0]) for pt in box]
        y_coords = [int(pt[1]) for pt in box]
        min_x, max_x = min(x_coords), max(x_coords)
        min_y, max_y = min(y_coords), max(y_coords)

        draw.rectangle([min_x, min_y, max_x, max_y], fill="white")
        draw.text((min_x, min_y), translated_text, font=font, fill="black")

    return image


# === STREAMLIT UI ===
st.set_page_config(page_title="Chinese → Russian OCR Translator", layout="centered")
st.title("📄 Chinese to Russian Image Translator")

uploaded_file = st.file_uploader("Upload an image containing Chinese text", type=["jpg", "png", "jpeg"])

if uploaded_file:
    st.image(uploaded_file, caption="📸 Original Image", use_column_width=True)

    with tempfile.NamedTemporaryFile(delete=False, suffix=".jpg") as tmp:
        tmp.write(uploaded_file.read())
        temp_img_path = tmp.name

    with st.spinner("🔍 Step 1: Detecting Chinese text..."):
        chinese_texts, boxes = extract_chinese_text(temp_img_path)
        st.success(f"✅ Detected {len(chinese_texts)} Chinese text regions.")

    with st.spinner("🌐 Step 2: Translating to Russian..."):
        russian_texts = translate_to_russian(chinese_texts)
        st.success("✅ Translation done.")

    with st.spinner("🖌 Step 3: Replacing text in image..."):
        translated_img = replace_text_in_image(temp_img_path, boxes, russian_texts)
        st.image(translated_img, caption="📝 Translated Image", use_column_width=True)

        # Save final image for download
        result_path = os.path.join(tempfile.gettempdir(), "translated_output.jpg")
        translated_img.save(result_path)

        with open(result_path, "rb") as f:
            st.download_button("📥 Download Result", f, file_name="translated_image.jpg")

