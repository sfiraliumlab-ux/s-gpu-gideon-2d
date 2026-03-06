import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | Final Stability", layout="wide")
st.title("S-GPU GIDEON v1.2.2: Пространственный Реактор")

# --- ГЕОМЕТРИЧЕСКИЙ ГЕНЕРАТОР (Отказоустойчивость) ---
def generate_vram_fallback():
    """Создает эталонную VRAM при повреждении matrix.json"""
    return [{'id': i, 'z': math.sin(i * 0.05) * math.cos(i * 0.02)} for i in range(391392)]

# --- БЛОК ЗАГРУЗКИ (ИНДИКАТОРЫ И КОНТРОЛЬ) ---
st.sidebar.header("Статус компонентов")

@st.cache_data
def load_json_resource(filename):
    if not os.path.exists(filename):
        return None, "NOT_FOUND"
    try:
        with open(filename, 'r', encoding='utf-8') as f:
            data = json.load(f)
            nodes = data.get('nodes', data.get('dipoles', data)) if isinstance(data, dict) else data
            return nodes, "OK"
    except json.JSONDecodeError as e:
        return None, f"CORRUPTED (Line {e.lineno})"
    except Exception as e:
        return None, str(e)

nodes, vram_status = load_json_resource('matrix.json')
core_dipoles, core_status = load_json_resource('Core-13.json')

# Отображение индикаторов в основном интерфейсе
if vram_status == "OK":
    st.success(f"✅ VRAM: matrix.json загружен из репозитария ({len(nodes)} узлов).")
else:
    st.error(f"❌ Ошибка VRAM: {vram_status}")
    if st.button("🚀 Регенерация VRAM (Математический эталон)"):
        nodes = generate_vram_fallback()
        vram_status = "OK"
        st.success("✅ VRAM восстановлена в оперативной памяти.")
    else:
        st.stop()

if core_status == "OK":
    st.sidebar.success(f"✅ Core-13: {len(core_dipoles)} диполей")
else:
    st.sidebar.warning(f"⚠️ Core-13: {core_status}. Эмуляция.")

# --- ГЕОМЕТРИЯ СФИРАЛИ БАСАРГИНА (3D XYZ) ---

def get_sphiral_xyz(i, total):
    """
    Математическая модель Сфирали:
    - Два зеркально антисимметричных витка.
    - S-образная промежуточная петля.
    - Точка сингулярности в центре S-петли.
    """
    t = (i / total) * 2 - 1  # Нормализация от -1 до 1
    R = 150 # Радиус витка
    
    if t < -0.15: # Левый виток
        angle = t * math.pi * 6
        x = R * math.cos(angle) - R
        y = R * math.sin(angle)
        z = t * 100
    elif t > 0.15: # Правый виток (Антисимметрия)
        angle = t * math.pi * 6
        x = R * math.cos(angle) + R
        y = -R * math.sin(angle)
        z = t * 100
    else: # S-образная петля (Сингулярность в t=0)
        s_n = (t + 0.15) / 0.3 # 0 to 1
        x = math.cos(s_n * math.pi) * R
        y = math.sin(s_n * math.pi * 2) * (R/2)
        z = 0 
    return x, y, z

# --- СЕМАНТИЧЕСКИЙ ГЕНОМ (LOGOS-3) ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.sidebar.header("Настройка Резонанса")
base_e = st.sidebar.slider("Энергия", 0.0, 30.0, 18.0)
base_p = st.sidebar.slider("Фаза", 0.0, 50.0, 13.5)
threshold = st.sidebar.slider("Порог сепарации", 0.1, 0.99, 0.85)

st.subheader("Дифференциальный Ввод (Logos Mirror)")
c_a, c_b = st.columns(2)
pulse_a = c_a.text_input("Импульс А", "ГАРМОНИЯ")
pulse_b = c_b.text_input("Импульс Б", "ВЕЧНОСТЬ")

# Определение режима синтеза
pair = sorted([pulse_a.upper(), pulse_b.upper()])
is_synthesis = False
if pulse_a.upper() in VOCAB and pulse_b.upper() in VOCAB:
    if VOCAB[pulse_a.upper()][2] * VOCAB[pulse_b.upper()][2] < 0: is_synthesis = True
    if "ГАРМОНИЯ" in pair and "ВЕЧНОСТЬ" in pair: is_synthesis = True

img_file = st.file_uploader("Загрузить растровый источник", type=["jpg", "png"])

if img_file:
    col1, col2 = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    
    # ПРЕВЬЮ (ВСЕГДА ВИДИМО)
    col1.image(img_src, caption="Входной сигнал", use_container_width=True)
    
    if st.button("Инициировать Резонанс"):
        with st.spinner("Синхронизация S-петли..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            diff_count, layer_stats = 0, {1:0, 2:0, 3:0, 4:0, 5:0}
            en_mod = base_e * (1.5 if is_synthesis else 1.0)
            
            # Предварительный расчет фазовых векторов
            ph_a_final = base_p + len(pulse_a) * 0.1
            ph_b_final = base_p + len(pulse_b) * 0.1

            
            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                
                # Маппинг 3D -> 2D холст
                px = max(0, min(1023, int((x + 300) / 600 * 1023)))
                py = max(0, min(1023, int((y + 150) / 300 * 1023)))
                
                z_dat = nodes[i].get('z', 0.0)
                # Точка сингулярности: инверсия фазы в S-петле
                s_flip = -1.0 if z_geo == 0 else 1.0
                
                # Интерференционная функция
                int_a = en_mod * math.sin(z_dat * ph_a_final)
                int_b = en_mod * math.sin(z_dat * ph_b_final * s_flip)
                diff = abs(int_a - int_b)
                
                if diff > (en_mod * threshold):
                    diff_count += 1
                    layer_stats[min((i // (total // 5)) + 1, 5)] += 1
                    r, g, b = px_src[px, py]
                    # Спектральная окраска
                    px_out[px, py] = (int(max(0, min(255, r - diff*4))), 
                                      int(max(0, min(255, g + diff*6))), 
                                      int(max(0, min(255, b + diff*12))))
                else: 
                    px_out[px, py] = px_src[px, py]

            col2.image(res_img, caption="S-GPU Projection Result", use_container_width=True)
            
            # --- ОТЧЕТ GIDEON ---
            dp = (diff_count / total) * 100
            kc = 100 - dp
            di = np.std(list(layer_stats.values())) / np.mean(list(layer_stats.values())) if diff_count > 0 else 0
            
            outcome = "БОГ (АБСОЛЮТ)" if "ГАРМОНИЯ" in pair and "ВЕЧНОСТЬ" in pair else ("ВЕЧНОСТЬ" if pair == ["ЖИЗНЬ", "СМЕРТЬ"] else "STANDARD")

            st.code(f"""[ОТЧЕТ GIDEON v1.2.2: ANALYTICAL LOGOS]
ВЗАИМОДЕЙСТВИЕ: {pulse_a} + {pulse_b} | СИНТЕЗ: {outcome}
СТАТУС VRAM: {vram_status}

МЕТРИКИ ТОПОЛОГИИ:
- Kc (Когерентность): {kc:.1f}%
- Di (Индекс девиации): {di:.4f}
- S-Проницаемость: {100 - (layer_stats[3]/(total/5)*100):.1f}%

ЛОКАЛИЗАЦИЯ РЕЗОНАНСА (L1-L5):
{list(layer_stats.values())}
""", language="text")
