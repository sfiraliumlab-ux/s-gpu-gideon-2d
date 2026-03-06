import streamlit as st
import json
import math
import os
from PIL import Image

# Базовые настройки интерфейса
st.set_page_config(page_title="S-GPU GIDEON", layout="wide")
st.title("Топологический процессор S-GPU GIDEON")

# Прямой путь к файлу без кириллицы и пробелов
RAM_FILE = 'matrix.json'

@st.cache_data
def load_nodes(filepath):
    """Кэшированная загрузка топологических узлов"""
    if not filepath or not os.path.exists(filepath):
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('nodes', []) if isinstance(data, dict) else data
    except Exception as e:
        st.error(f"Ошибка десериализации памяти: {e}")
        return []

# Инициализация
nodes = load_nodes(RAM_FILE)

# Блокировка при отсутствии данных
if not nodes:
    st.error(f"Критическая ошибка: Файл '{RAM_FILE}' не найден. Убедитесь, что он загружен в корень репозитория GitHub.")
    st.stop()

st.success(f"Топологическая матрица активна: {len(nodes)} узлов.")

# Интерфейс ввода
uploaded_file = st.file_uploader("Загрузить растровый источник", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns(2)
    
    orig_img = Image.open(uploaded_file).convert('RGB')
    col1.image(orig_img, caption="Исходные данные", use_container_width=True)
    
    if st.button("Инициировать резонанс (Топологический перенос)"):
        with st.spinner("Синхронизация узлов..."):
            # Создание виртуального буфера
            output_img = Image.new('RGB', (1024, 1024), (0, 0, 0))
            output_pixels = output_img.load()
            
            # Масштабирование
            resized_orig = orig_img.resize((1024, 1024))
            rgb_map = resized_orig.load()
            
            total = len(nodes)
            side = int(math.sqrt(total))
            
            # Топологический перенос
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
