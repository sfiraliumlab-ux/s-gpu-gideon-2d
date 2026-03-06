import streamlit as st
import json
import math
from PIL import Image

# Базовые настройки интерфейса
st.set_page_config(page_title="S-GPU GIDEON", layout="wide")
st.title("Топологический процессор S-GPU GIDEON")

@st.cache_data
def load_nodes(uploaded_file):
    """Десериализация JSON-файла напрямую из веб-интерфейса в ОЗУ"""
    if uploaded_file is None:
        return []
    try:
        data = json.load(uploaded_file)
        return data.get('nodes', []) if isinstance(data, dict) else data
    except Exception as e:
        st.error(f"Ошибка десериализации данных: {e}")
        return []

# Блок 1: Инициализация архитектуры
st.subheader("1. Загрузка памяти (VRAM)")
matrix_file = st.file_uploader("Загрузите JSON-массив (файл 18 МБ)", type=["json"])

nodes = load_nodes(matrix_file)

# Блокировка интерфейса до загрузки матрицы
if not nodes:
    st.warning("Ожидание загрузки топологической матрицы.")
    st.stop()

st.success(f"Топологическая матрица активна: {len(nodes)} узлов.")

# Блок 2: Вычислительный процесс
st.subheader("2. Ввод данных и резонанс")
image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    
    orig_img = Image.open(image_file).convert('RGB')
    col1.image(orig_img, caption="Исходные данные", use_container_width=True)
    
    if st.button("Инициировать топологический перенос"):
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
                    output_pixels[safe_x, safe_y] = rgb_map[safe_x, safe_y]
                except Exception:
                    continue
            
            col2.image(output_img, caption="Графический отпечаток состояния памяти", use_container_width=True)
