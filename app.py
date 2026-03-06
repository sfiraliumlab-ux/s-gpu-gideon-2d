import streamlit as st
import json
import math
import os
from PIL import Image

st.set_page_config(page_title="S-GPU GIDEON | High-Contrast Mode", layout="wide")
st.title("Топологический процессор S-GPU GIDEON")

RAM_FILE = 'matrix.json'

@st.cache_data
def load_nodes():
    """Автоматическая загрузка матрицы из репозитория"""
    if not os.path.exists(RAM_FILE):
        return []
    try:
        with open(RAM_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('nodes', []) if isinstance(data, dict) else data
    except Exception as e:
        st.error(f"Ошибка загрузки VRAM: {e}")
        return []

# Интерфейс управления
st.sidebar.header("Настройка резонанса (Фильтр пиков)")
energy = st.sidebar.slider("Энергия (Energy)", min_value=0.0, max_value=20.0, value=15.0, step=0.5)
phase = st.sidebar.slider("Фаза (Phase)", min_value=0.0, max_value=15.0, value=9.5, step=0.1)
brush_size = st.sidebar.slider("Размер узла", min_value=1, max_value=4, value=2, step=1)
threshold = st.sidebar.slider("Порог отсечения шума", min_value=0.5, max_value=0.95, value=0.7, step=0.05)

nodes = load_nodes()
if not nodes:
    st.error(f"Файл '{RAM_FILE}' не найден в корне проекта.")
    st.stop()

st.success(f"VRAM активна: {len(nodes)} узлов.")

image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    col1.image(orig_img, caption="Входной сигнал", use_container_width=True)
    
    if st.button("Запустить High-Contrast рендеринг"):
        with st.spinner("Фильтрация топологических шумов..."):
            output_img = Image.new('RGB', (1024, 1024), (0, 0, 0))
            output_pixels = output_img.load()
            resized_orig = orig_img.resize((1024, 1024))
            rgb_map = resized_orig.load()
            
            total = len(nodes)
            side = int(math.sqrt(total))
            
            # Телеметрия
            active_pixels = set()
            purple_shifts = 0
            max_interf = 0.0
            
            for i in range(total):
                col_idx, row_idx = i % side, i // side
                px, py = int((col_idx / side) * 1023), int((row_idx / side) * 1023)
                
                node = nodes[i]
                z_coord = node.get('z', 0.0) if isinstance(node, dict) else 0.0
                
                # Формула интерференции
                interference = energy * math.sin(z_coord * phase)
                if abs(interference) > max_interf: max_interf = abs(interference)
                
                r, g, b = rgb_map[px, py]
                
                # ЛОГИКА ФИЛЬТРАЦИИ: Проявляем только пики
                if interference > (energy * threshold):
                    purple_shifts += 1
                    # Глубокий спектральный сдвиг (Фиолетовый неон)
                    new_r = int(max(0, min(255, r + interference * 12)))
                    new_g = int(max(0, min(255, g - interference * 5)))
                    new_b = int(max(0, min(255, b + interference * 15)))
                else:
                    # Фоновые узлы остаются в исходном цвете (или слегка затеняются)
                    new_r, new_g, new_b = r, g, b
                
                # Отрисовка с учетом размера
                for dx in range(brush_size):
                    for dy in range(brush_size):
                        if px+dx < 1024 and py+dy < 1024:
                            output_pixels[px+dx, py+dy] = (new_r, new_g, new_b)
                            active_pixels.add((px+dx, py+dy))
            
            col2.image(output_img, caption="Магистрали данных S-GPU", use_container_width=True)
            
            # Финальный отчет
            coverage = (len(active_pixels) / (1024*1024)) * 100
            report = f"""[ОТЧЕТ GIDEON: HIGH-CONTRAST]
Энергия: {energy} | Фаза: {phase} | Порог: {threshold}
Покрытие холста: {coverage:.2f}%
Макс. амплитуда: {max_interf:.2f}
Узлов в резонансе (пики): {purple_shifts} ({(purple_shifts/total)*100:.1f}%)"""
            
            st.info("Передай этот отчет для финальной калибровки:")
            st.code(report, language="text")
