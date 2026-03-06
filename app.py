import streamlit as st
import json
import math
import os
from PIL import Image

st.set_page_config(page_title="S-GPU GIDEON | High-Contrast", layout="wide")
st.title("Топологический процессор S-GPU GIDEON")

RAM_FILE = 'matrix.json'

@st.cache_data
def load_nodes(uploaded_file=None):
    """Загрузка матрицы: сначала из репозитория, если нет — из загрузчика"""
    data_source = None
    
    if uploaded_file is not None:
        data_source = uploaded_file
    elif os.path.exists(RAM_FILE):
        try:
            with open(RAM_FILE, 'r', encoding='utf-8') as f:
                content = f.read().strip()
                if not content:
                    return []
                data_source = json.loads(content)
        except:
            return []

    if data_source is not None:
        if isinstance(data_source, dict):
            return data_source.get('nodes', [])
        elif isinstance(data_source, list):
            return data_source
        else:
            try:
                data = json.load(data_source)
                return data.get('nodes', []) if isinstance(data, dict) else data
            except:
                return []
    return []

# Настройки в боковой панели
st.sidebar.header("Настройка резонанса")
energy = st.sidebar.slider("Энергия (Energy)", 0.0, 20.0, 18.0, 0.5)
phase = st.sidebar.slider("Фаза (Phase)", 0.0, 15.0, 12.5, 0.1)
brush_size = st.sidebar.slider("Размер узла", 1, 4, 2, 1)
threshold = st.sidebar.slider("Порог отсечения шума", 0.5, 0.95, 0.90, 0.05)

# Логика инициализации VRAM
nodes = []
if os.path.exists(RAM_FILE):
    nodes = load_nodes()

if not nodes:
    st.warning("⚠️ Автозагрузка не удалась. Пожалуйста, выберите файл 'matrix.json' вручную.")
    manual_matrix = st.file_uploader("Загрузить матрицу (JSON)", type=["json"], key="vram_loader")
    if manual_matrix:
        nodes = load_nodes(manual_matrix)
    else:
        st.stop()

st.success(f"VRAM активна: {len(nodes)} узлов.")

# Работа с изображением
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
            rows = math.ceil(total / side)
            
            active_pixels = set()
            purple_shifts = 0
            max_interf = 0.0
            
            for i in range(total):
                col_idx = i % side
                row_idx = i // side
                
                # Безопасный расчет координат с клиппингом
                px = max(0, min(1023, int((col_idx / side) * 1023)))
                py = max(0, min(1023, int((row_idx / rows) * 1023)))

                node = nodes[i]
                z_coord = node.get('z', 0.0) if isinstance(node, dict) else 0.0
                
                # Математика интерференции
                interference = energy * math.sin(z_coord * phase)
                if abs(interference) > max_interf: 
                    max_interf = abs(interference)
                
                # Чтение цвета из исходника теперь защищено от IndexError
                r, g, b = rgb_map[px, py]
                
                # Фильтр пиков
                if interference > (energy * threshold):
                    purple_shifts += 1
                    new_r = int(max(0, min(255, r + interference * 12)))
                    new_g = int(max(0, min(255, g - interference * 5)))
                    new_b = int(max(0, min(255, b + interference * 15)))
                else:
                    new_r, new_g, new_b = r, g, b
                
                # Отрисовка кисти
                for dx in range(brush_size):
                    for dy in range(brush_size):
                        nx, ny = px + dx, py + dy
                        if nx < 1024 and ny < 1024:
                            output_pixels[nx, ny] = (new_r, new_g, new_b)
                            active_pixels.add((nx, ny))
            
            col2.image(output_img, caption="Магистрали данных S-GPU", use_container_width=True)
            
            coverage = (len(active_pixels) / (1024*1024)) * 100
            report = f"""[ОТЧЕТ GIDEON: HIGH-CONTRAST]
Энергия: {energy} | Фаза: {phase} | Порог: {threshold}
Покрытие холста: {coverage:.2f}%
Макс. амплитуда: {max_interf:.2f}
Узлов в резонансе (пики): {purple_shifts} ({(purple_shifts/total)*100:.1f}%)"""
            
            st.info("Передай этот отчет для калибровки:")
            st.code(report, language="text")
