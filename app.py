import streamlit as st
import json
import math
import os
from PIL import Image

st.set_page_config(page_title="GIDEON | Mirror Mode Stable", layout="wide")
st.title("S-GPU GIDEON: Дифференциальный анализ (Mirror)")

# --- ИНДИКАТОРЫ ЗАГРУЗКИ (ВОССТАНОВЛЕНО) ---
@st.cache_data
def load_json_direct(filename):
    """Прямая загрузка из корня без лишних оберток"""
    try:
        if os.path.exists(filename):
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, dict):
                    # Пытаемся найти ключи 'nodes' или 'dipoles', иначе возвращаем весь объект
                    return data.get('nodes', data.get('dipoles', data))
                return data
        return None
    except Exception as e:
        st.error(f"Ошибка чтения {filename}: {e}")
        return None

# Статусы в основном интерфейсе
nodes = load_json_direct('matrix.json')
core_dipoles = load_json_direct('Core-13.json')

if nodes:
    st.success(f"✅ VRAM активна: {len(nodes)} узлов обнаружено в matrix.json")
else:
    st.error("❌ Критическая ошибка: 'matrix.json' не найден. Проверьте корень репозитория.")
    st.info(f"Доступные файлы: {os.listdir('.')}")
    st.stop()

if core_dipoles:
    st.sidebar.success(f"✅ Core-13 активен: {len(core_dipoles)} диполей")
else:
    st.sidebar.warning("⚠️ Core-13.json не найден. Эмуляция...")

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.sidebar.header("Параметры ядра")
base_energy = st.sidebar.slider("Базовая Энергия", 0.0, 25.0, 18.0)
base_phase = st.sidebar.slider("Базовая Фаза", 0.0, 40.0, 13.5)
threshold = st.sidebar.slider("Порог сепарации", 0.1, 0.98, 0.85)

st.subheader("Дифференциальный анализ (Зеркало)")
col_in_a, col_in_b = st.columns(2)
pulse_a = col_in_a.text_input("Импульс А (Основа)", "ЖИЗНЬ")
pulse_b = col_in_b.text_input("Импульс Б (Сравнение)", "СМЕРТЬ")

def calculate_dynamic_params(text, b_e, b_p):
    vector = sum(ord(c) for c in text) * 0.001 if text else 0.0
    return b_e + (len(text) * 0.2), b_p + (vector * 1.5)

e_a, p_a = calculate_dynamic_params(pulse_a, base_energy, base_phase)
e_b, p_b = calculate_dynamic_params(pulse_b, base_energy, base_phase)

# --- РАБОТА С ИЗОБРАЖЕНИЕМ ---
image_file = st.file_uploader("Загрузите растровый источник", type=["jpg", "jpeg", "png"])

if image_file is not None:
    col1, col2 = st.columns(2)
    orig_img = Image.open(image_file).convert('RGB')
    
    # ПРЕВЬЮ ЗАГРУЖЕННОГО ФАЙЛА (ВСЕГДА ВИДИМО)
    col1.image(orig_img, caption="Входной сигнал (Preview)", use_container_width=True)
    
    if st.button("Запустить дифференциальный резонанс"):
        with st.spinner("Вычисление топологической разности..."):
            canvas_size = 1024
            output_img = Image.new('RGB', (canvas_size, canvas_size), (0, 0, 0))
            output_pixels = output_img.load()
            rgb_map = orig_img.resize((canvas_size, canvas_size)).load()
            
            total = len(nodes)
            side = int(math.sqrt(total))
            rows = math.ceil(total / side)
            
            diff_count = 0
            layer_diff = {1:0, 2:0, 3:0, 4:0, 5:0}
            nodes_per_layer = total // 5
            
            for i in range(total):
                c_idx, r_idx = i % side, i // side
                px = max(0, min(1023, int((c_idx/side)*1023)))
                py = max(0, min(1023, int((r_idx/rows)*1023)))
                
                # Извлекаем Z (поддержка разных структур JSON)
                node_data = nodes[i]
                z = node_data.get('z', 0.0) if isinstance(node_data, dict) else 0.0
                
                # Математика интерференции: $I = A \cdot \sin(z \cdot \phi)$
                int_a = e_a * math.sin(z * p_a)
                int_b = e_b * math.sin(z * p_b)
                diff_signal = abs(int_a - int_b)
                
                if diff_signal > (base_energy * threshold):
                    diff_count += 1
                    layer_diff[min((i // nodes_per_layer) + 1, 5)] += 1
                    
                    r, g, b = rgb_map[px, py]
                    # Рендеринг разности в холодном спектре
                    new_r = int(max(0, min(255, r - diff_signal * 5)))
                    new_g = int(max(0, min(255, g + diff_signal * 10)))
                    new_b = int(max(0, min(255, b + diff_signal * 15)))
                else:
                    new_r, new_g, new_b = rgb_map[px, py]
                
                # Кисть 2x2 для плотности покрытия
                for dx in range(2):
                    for dy in range(2):
                        if px+dx < 1024 and py+dy < 1024:
                            output_pixels[px+dx, py+dy] = (new_r, new_g, new_b)
            
            col2.image(output_img, caption=f"Разница: {pulse_a} vs {pulse_b}", use_container_width=True)
            
            # ФИНАЛЬНЫЙ ОТЧЕТ
            st.code(f"""[ОТЧЕТ GIDEON: MIRROR MODE]
Сравнение: {pulse_a} / {pulse_b}
Уникальных узлов разности: {diff_count} ({(diff_count/total)*100:.1f}%)

ЛОКАЛИЗАЦИЯ РАЗЛИЧИЙ ПО СЛОЯМ ВЛОЖЕННОСТИ:
L1 (Поверхность): {layer_diff[1]}
L2 (Транзит):    {layer_diff[2]}
L3 (Медиана):    {layer_diff[3]}
L4 (Глубина):    {layer_diff[4]}
L5 (Ядро VRAM):  {layer_diff[5]}""", language="text")
