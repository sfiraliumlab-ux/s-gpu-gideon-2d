import streamlit as st
import json
import math
import os
from PIL import Image

st.set_page_config(page_title="S-GPU GIDEON | Layer-5 Analysis", layout="wide")
st.title("Топологический процессор S-GPU GIDEON")

VRAM_FILE = 'matrix.json'
CORE_FILE = 'Core-13.json'

@st.cache_data
def load_json_data(file_path):
    if not os.path.exists(file_path): return None
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            return data.get('nodes', data.get('dipoles', [])) if isinstance(data, dict) else data
    except: return None

nodes = load_json_data(VRAM_FILE)
core_dipoles = load_json_data(CORE_FILE)

if nodes is None:
    st.error("Критическая ошибка: VRAM (matrix.json) не обнаружена.")
    st.stop()

# Панель управления
st.sidebar.header("Ядро GIDEON (Core-13)")
base_energy = st.sidebar.slider("Базовая Энергия", 0.0, 25.0, 18.0)
base_phase = st.sidebar.slider("Базовая Фаза", 0.0, 40.0, 13.5)
threshold = st.sidebar.slider("Порог отсечения (Gate)", 0.5, 0.98, 0.95)

st.subheader("Центральный процессор: Ввод данных")
user_input = st.text_input("Введите информационный импульс", "ГЕОМЕТРИЯ ПУСТОТЫ")

# Динамическая модуляция
text_vector = sum(ord(c) for c in user_input) * 0.001 if user_input else 0.0
dynamic_phase = base_phase + (text_vector * 1.5)
dynamic_energy = base_energy + (len(user_input) * 0.2 if user_input else 0.0)

image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    col1.image(orig_img, caption="Входной сигнал", use_container_width=True)
    
    if st.button("Инициировать глубокий резонанс"):
        with st.spinner("Расчет прохождения через слои L1-L5..."):
            canvas_size = 1024
            output_img = Image.new('RGB', (canvas_size, canvas_size), (0, 0, 0))
            output_pixels = output_img.load()
            rgb_map = orig_img.resize((canvas_size, canvas_size)).load()
            
            total_nodes = len(nodes)
            side = int(math.sqrt(total_nodes))
            rows = math.ceil(total_nodes / side)
            
            purple_shifts = 0
            # Инициализация счетчиков слоев (5 уровней вложенности)
            layer_stats = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            nodes_per_layer = total_nodes // 5
            
            for i in range(total_nodes):
                col_idx, row_idx = i % side, i // side
                px = max(0, min(1023, int((col_idx / side) * 1023)))
                py = max(0, min(1023, int((row_idx / rows) * 1023)))

                node = nodes[i]
                z_coord = node.get('z', 0.0)
                
                # Определение слоя вложенности
                current_layer = min((i // nodes_per_layer) + 1, 5)
                
                interference = dynamic_energy * math.sin(z_coord * dynamic_phase)
                
                if interference > (dynamic_energy * threshold):
                    purple_shifts += 1
                    layer_stats[current_layer] += 1
                    
                    r, g, b = rgb_map[px, py]
                    new_r = int(max(0, min(255, r + interference * 12)))
                    new_g = int(max(0, min(255, g - interference * 5)))
                    new_b = int(max(0, min(255, b + interference * 15)))
                else:
                    new_r, new_g, new_b = rgb_map[px, py]
                
                for dx in range(2):
                    for dy in range(2):
                        if px+dx < 1024 and py+dy < 1024:
                            output_pixels[px+dx, py+dy] = (new_r, new_g, new_b)
            
            col2.image(output_img, caption=f"Резонанс: {user_input}", use_container_width=True)
            
            # Послойный отчет
            res_percent = (purple_shifts / total_nodes) * 100
            st.code(f"""[ОТЧЕТ GIDEON: LAYER ANALYSIS]
Импульс: '{user_input}' | Фаза: {dynamic_phase:.4f}
Общий резонанс системы: {res_percent:.1f}%

АКТИВНОСТЬ ПО СЛОЯМ ВЛОЖЕННОСТИ:
L1 (Поверхность): {layer_stats[1]} узлов
L2 (Транзит):    {layer_stats[2]} узлов
L3 (Медиана):    {layer_stats[3]} узлов
L4 (Глубина):    {layer_stats[4]} узлов
L5 (Ядро VRAM):  {layer_stats[5]} узлов""", language="text")
