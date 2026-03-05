import streamlit as st
import json
import math
from PIL import Image

# Базовые настройки интерфейса
st.set_page_config(page_title="S-GPU GIDEON", layout="wide")
st.title("Топологический процессор S-GPU GIDEON")

# Пути к файлам архитектуры
RAM_FILE = 'architecture/кольцо 5 порядков вложенности.json'

@st.cache_data
def load_nodes(filepath):
    """Кэшированная загрузка топологических узлов в оперативную память сервера"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('nodes', []) if isinstance(data, dict) else data
    except Exception as e:
        st.error(f"Ошибка инициализации памяти: {e}")
        return []

nodes = load_nodes(RAM_FILE)

# Блокировка работы при отсутствии матрицы
if not nodes:
    st.warning(f"Файл {RAM_FILE} не найден. Разместите его в директории /architecture репозитория.")
    st.stop()

st.success(f"Топологическая матрица активна: {len(nodes)} узлов.")

# Интерфейс ввода
uploaded_file = st.file_uploader("Загрузить растровый источник для оцифровки", type=["jpg", "jpeg", "png"])

if uploaded_file is not None:
    col1, col2 = st.columns(2)
    
    orig_img = Image.open(uploaded_file).convert('RGB')
    col1.image(orig_img, caption="Исходные данные", use_container_width=True)
    
    if st.button("Инициировать резонанс (Топологический перенос)"):
        with st.spinner("Вычисление состояний узлов..."):
            # Создание виртуального 2D-буфера кадра
            output_img = Image.new('RGB', (1024, 1024), (0, 0, 0))
            output_pixels = output_img.load()
            
            # Масштабирование источника под разрешение матрицы
            resized_orig = orig_img.resize((1024, 1024))
            rgb_map = resized_orig.load()
            
            total = len(nodes)
            side = int(math.sqrt(total))
            
            # Цикл переноса данных в узлы памяти
            for i in range(total):
                col, row = i % side, i // side
                
                # Маппинг 1D-индекса узла на 2D-координаты холста
                px = int((col / side) * 1023)
                py = int((row / side) * 1023)
                
                safe_x = max(0, min(px, 1023))
                safe_y = max(0, min(py, 1023))
                
                try:
                    # Захват цвета оригинального пикселя узлом Сфирали
                    node_rgb = rgb_map[safe_x, safe_y]
                    # Фиксация отпечатка в выходном буфере
                    output_pixels[safe_x, safe_y] = node_rgb
                except Exception:
                    continue
            
            col2.image(output_img, caption="Графический отпечаток состояния памяти VRAM", use_container_width=True)
