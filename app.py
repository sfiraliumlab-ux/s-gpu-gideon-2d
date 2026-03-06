import streamlit as st
import json
import math
import os
from PIL import Image

st.set_page_config(page_title="S-GPU GIDEON", layout="wide")
st.title("Топологический процессор S-GPU GIDEON")

def find_matrix_file(filename_list):
    """Глубокий поиск файлов во всех директориях проекта"""
    base_dir = os.getcwd()
    for root, dirs, files in os.walk(base_dir):
        for file in files:
            if file in filename_list:
                return os.path.join(root, file)
    return None

# Поиск оригинального или переименованного файла
TARGET_FILES = ['matrix.json', 'кольцо 5 порядков вложенности.json']
RAM_FILE = find_matrix_file(TARGET_FILES)

@st.cache_data
def load_nodes(filepath, uploaded_matrix=None):
    """Десериализация JSON из файла или прямого потока загрузки"""
    try:
        if uploaded_matrix is not None:
            data = json.load(uploaded_matrix)
        elif filepath and os.path.exists(filepath):
            with open(filepath, 'r', encoding='utf-8') as f:
                data = json.load(f)
        else:
            return []
        return data.get('nodes', []) if isinstance(data, dict) else data
    except Exception as e:
        st.error(f"Ошибка чтения данных: {e}")
        return []

# Резервный механизм загрузки матрицы
matrix_stream = None
if not RAM_FILE:
    st.warning("Матрица не найдена в репозитории (превышен лимит GitHub в 25 МБ). Загрузите файл напрямую.")
    matrix_stream = st.file_uploader("Загрузить JSON-файл матрицы", type=["json"])
    if not matrix_stream:
        st.stop()

nodes = load_nodes(RAM_FILE, matrix_stream)

if not nodes:
    st.error("Критическая ошибка: Массив узлов пуст или поврежден.")
    st.stop()

st.success(f"Топологическая матрица активна: {len(nodes)} узлов.")

# Рабочий интерфейс
uploaded_file = st.file_uploader("Загрузить растровый источник", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns(2)
    
    orig_img = Image.open(uploaded_file).convert('RGB')
    col1.image(orig_img, caption="Исходные данные", use_container_width=True)
    
    if st.button("Инициировать резонанс (Топологический перенос)"):
        with st.spinner("Синхронизация узлов..."):
            output_img = Image.new('RGB', (1024, 1024), (0, 0, 0))
            output_pixels = output_img.load()
            
            resized_orig = orig_img.resize((1024, 1024))
            rgb_map = resized_orig.load()
            
            total = len(nodes)
            side = int(math.sqrt(total))
            
            for i in range(total):
                col, row = i % side, i // side
                
                px = int((col / side) * 1023)
                py = int((row / side) * 1023)
                
                safe_x = max(0, min(px, 1023))
                safe_y = max(0, min(py, 1023))
                
                try:
                    node_rgb = rgb_map[safe_x, safe_y]
                    output_pixels[safe_x, safe_y] = node_rgb
                except Exception:
                    continue
            
            col2.image(output_img, caption="Графический отпечаток состояния памяти", use_container_width=True)
