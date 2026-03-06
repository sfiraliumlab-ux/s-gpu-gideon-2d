import streamlit as st
import json
import math
import os
import glob
from PIL import Image

st.set_page_config(page_title="S-GPU GIDEON | High-Contrast", layout="wide")
st.title("Топологический процессор S-GPU GIDEON")

def find_matrix_file():
    """Поиск matrix.json в корне или подпапках"""
    # Ищем во всех поддиректориях на случай, если Git изменил структуру
    paths = glob.glob("**/matrix.json", recursive=True)
    if paths:
        return paths[0]
    # Запасной вариант для прямой проверки в корне
    if os.path.exists("matrix.json"):
        return "matrix.json"
    return None

@st.cache_data
def load_nodes(filepath):
    """Загрузка и десериализация VRAM"""
    if not filepath:
        return []
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read().strip()
            if not content:
                st.error(f"Файл {filepath} пуст.")
                return []
            data = json.loads(content)
            return data.get('nodes', []) if isinstance(data, dict) else data
    except json.JSONDecodeError as e:
        st.error(f"Ошибка формата JSON в {filepath}: {e}")
        return []
    except Exception as e:
        st.error(f"Ошибка доступа к {filepath}: {e}")
        return []

# Настройки в боковой панели
st.sidebar.header("Настройка резонанса")
energy = st.sidebar.slider("Энергия (Energy)", 0.0, 20.0, 18.0, 0.5)
phase = st.sidebar.slider("Фаза (Phase)", 0.0, 15.0, 12.5, 0.1)
brush_size = st.sidebar.slider("Размер узла", 1, 4, 2, 1)
threshold = st.sidebar.slider("Порог отсечения шума", 0.5, 0.95, 0.90, 0.05)

# Автоматический поиск и загрузка
matrix_path = find_matrix_file()
nodes = load_nodes(matrix_path)

if not nodes:
    st.warning("⚠️ matrix.json не найден в репозитории. Загрузите файл 18.6 МБ вручную.")
    manual_matrix = st.file_uploader("Загрузить матрицу вручную", type=["json"])
    if manual_matrix:
        try:
            data = json.load(manual_matrix)
            nodes = data.get('nodes', []) if isinstance(data, dict) else data
        except:
            st.error("Ошибка чтения загруженного файла.")
            st.stop()
    else:
        st.stop()

st.success(f"VRAM активна: {len(nodes)} узлов (Файл: {matrix_path or 'Ручная загрузка'}).")

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
                
                # Координаты с защитой от выхода за границы 1024x1024
                px = max(0, min(1023, int((col_idx / side) * 1023)))
                py = max(0, min(1023, int((row_idx / rows) * 1023)))

                node = nodes[i]
                z_coord = node.get('z', 0.0) if isinstance(node, dict) else 0.0
                
                # Формула интерференции
                interference = energy * math.sin(z_coord * phase)
                if abs(interference) > max_interf: 
                    max_interf = abs(interference)
                
                r, g, b = rgb_map[px, py]
                
                # Режим High-Contrast: фильтрация пиков
                if interference > (energy * threshold):
                    purple_shifts += 1
                    # Экстремальный сдвиг спектра
                    new_r = int(max(0, min(255, r + interference * 12)))
                    new_g = int(max(0, min(255, g - interference * 5)))
                    new_b = int(max(0, min(255, b + interference * 15)))
                else:
                    new_r, new_g, new_b = r, g, b
                
                # Отрисовка
                for dx in range(brush_size):
                    for dy in range(brush_size):
                        nx, ny = px + dx, py + dy
                        if nx < 1024 and ny < 1024:
                            output_pixels[nx, ny] = (new_r, new_g, new_b)
                            active_pixels.add((nx, ny))
            
            col2.image(output_img, caption="Магистрали данных S-GPU", use_container_width=True)
            
            # Статистика для калибровки
            coverage = (len(active_pixels) / (1024*1024)) * 100
            report = f"""[ОТЧЕТ GIDEON: HIGH-CONTRAST]
Энергия: {energy} | Фаза: {phase} | Порог: {threshold}
Покрытие холста: {coverage:.2f}%
Макс. амплитуда: {max_interf:.2f}
Узлов в резонансе (пики): {purple_shifts} ({(purple_shifts/total)*100:.1f}%)"""
            
            st.info("Результат резонанса зафиксирован:")
            st.code(report, language="text")
