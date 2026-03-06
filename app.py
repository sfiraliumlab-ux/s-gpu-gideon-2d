import streamlit as st
import json
import math
import os
from PIL import Image

st.set_page_config(page_title="S-GPU GIDEON", layout="wide")
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
        st.error(f"Ошибка загрузки: {e}")
        return []

# Блок управления
st.sidebar.header("Параметры резонанса")
energy = st.sidebar.slider("Энергия (Energy)", min_value=0.0, max_value=20.0, value=5.0, step=0.5)
phase = st.sidebar.slider("Фаза (Phase)", min_value=0.0, max_value=10.0, value=1.0, step=0.1)
brush_size = st.sidebar.slider("Размер узла", min_value=1, max_value=4, value=2, step=1)

# Инициализация VRAM
nodes = load_nodes()
if not nodes:
    st.error(f"Файл '{RAM_FILE}' не найден. Загрузите его в корень репозитория GitHub.")
    st.stop()

st.success(f"Топологическая матрица активна: {len(nodes)} узлов (Автозагрузка).")

# Блок вычислений
image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    col1.image(orig_img, caption="Исходные данные", use_container_width=True)
    
    if st.button("Инициировать топологический перенос"):
        with st.spinner("Синхронизация узлов и сбор телеметрии..."):
            output_img = Image.new('RGB', (1024, 1024), (0, 0, 0))
            output_pixels = output_img.load()
            resized_orig = orig_img.resize((1024, 1024))
            rgb_map = resized_orig.load()
            
            total = len(nodes)
            side = int(math.sqrt(total))
            
            # Аналитические переменные
            active_pixels = set()
            max_interference = 0.0
            total_interference = 0.0
            purple_shifts = 0
            
            # Цикл резонанса
            for i in range(total):
                col_idx, row_idx = i % side, i // side
                px = int((col_idx / side) * 1023)
                py = int((row_idx / side) * 1023)
                
                safe_x = max(0, min(px, 1023))
                safe_y = max(0, min(py, 1023))
                
                try:
                    node = nodes[i]
                    z_coord = node.get('z', 0.0) if isinstance(node, dict) else 0.0
                    
                    # Математика интерференции
                    interference = energy * math.sin(z_coord * phase)
                    abs_interf = abs(interference)
                    
                    max_interference = max(max_interference, abs_interf)
                    total_interference += abs_interf
                    
                    if interference > 0.5:
                        purple_shifts += 1
                    
                    r, g, b = rgb_map[safe_x, safe_y]
                    
                    new_r = int(max(0, min(255, r + interference * 5)))
                    new_g = int(max(0, min(255, g + interference * 2)))
                    new_b = int(max(0, min(255, b + interference * 5)))
                    
                    # Отрисовка
                    for dx in range(brush_size):
                        for dy in range(brush_size):
                            nx = safe_x + dx
                            ny = safe_y + dy
                            if nx < 1024 and ny < 1024:
                                output_pixels[nx, ny] = (new_r, new_g, new_b)
                                active_pixels.add((nx, ny))
                except Exception:
                    continue
            
            col2.image(output_img, caption="Отпечаток резонанса", use_container_width=True)
            
            # Генерация отчета
            coverage = (len(active_pixels) / (1024*1024)) * 100
            avg_interference = total_interference / total if total > 0 else 0
            
            report = f"""[ОТЧЕТ GIDEON]
Энергия: {energy} | Фаза: {phase} | Размер узла: {brush_size}
Покрытие холста: {coverage:.2f}%
Макс. амплитуда: {max_interference:.2f}
Средн. амплитуда: {avg_interference:.2f}
Узлов в фиолетовом спектре: {purple_shifts} ({(purple_shifts/total)*100:.1f}%)"""
            
            st.info("Скопируйте блок телеметрии для анализа:")
            st.code(report, language="text")
