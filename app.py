import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | Analytical 3D Sfiral", layout="wide")
st.title("S-GPU GIDEON v1.2.1: Пространственный Реактор")

# --- КОНСТАНТЫ LOGOS-3 (СЕМАНТИЧЕСКИЙ ГЕНОМ) ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- БЛОК ЗАГРУЗКИ С ИНДИКАТОРАМИ (ВОССТАНОВЛЕНО) ---
@st.cache_data
def load_json_data(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                return (data.get('nodes', data) if isinstance(data, dict) else data), "OK"
        except Exception as e:
            return None, f"CORRUPTED: {str(e)}"
    return None, "NOT_FOUND"

# Статусы файлов в основном интерфейсе
nodes, vram_status = load_json_data('matrix.json')
core_dipoles, core_status = load_json_data('Core-13.json')

if vram_status == "OK":
    st.success(f"✅ VRAM активна: {len(nodes)} узлов загружено из репозитария.")
else:
    st.error(f"❌ Ошибка VRAM: {vram_status}")
    if st.button("🚀 Инициировать экстренную генерацию эталонной VRAM (391 392 узла)"):
        nodes = [{'id': i, 'z': math.sin(i * 0.01) * math.cos(i * 0.005)} for i in range(391392)]
        st.success("✅ Эталонная VRAM сгенерирована в оперативной памяти.")
        vram_status = "OK"
    else:
        st.stop()

if core_status == "OK":
    st.sidebar.success(f"✅ Core-13 активен: {len(core_dipoles)} диполей")
else:
    st.sidebar.warning(f"⚠️ Core-13: {core_status}. Режим эмуляции.")

# --- ГЕОМЕТРИЯ СФИРАЛИ БАСАРГИНА (3D XYZ) ---
def get_sphiral_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    if t < -0.15: # Левый виток
        angle = t * math.pi * 6
        return R * math.cos(angle) - R, R * math.sin(angle), t * 100
    elif t > 0.15: # Правый виток (Зеркальная антисимметрия)
        angle = t * math.pi * 6
        return R * math.cos(angle) + R, -R * math.sin(angle), t * 100
    else: # S-образная петля (Сингулярность)
        s_n = (t + 0.15) / 0.3
        return math.cos(s_n * math.pi) * R, math.sin(s_n * math.pi * 2) * (R/2), 0

# --- ПАНЕЛЬ УПРАВЛЕНИЯ ---
st.sidebar.header("Параметры резонанса")
base_e = st.sidebar.slider("Базовая Энергия", 0.0, 30.0, 18.0)
base_p = st.sidebar.slider("Базовая Фаза", 0.0, 50.0, 13.5)
threshold = st.sidebar.slider("Порог сепарации", 0.1, 0.99, 0.85)

st.subheader("Дифференциальный ввод (Logos Mirror)")
c_a, c_b = st.columns(2)
pulse_a = c_a.text_input("Импульс А", "ГАРМОНИЯ")
pulse_b = c_b.text_input("Импульс Б", "ВЕЧНОСТЬ")

# Логика Logos-3
pair = sorted([pulse_a.upper(), pulse_b.upper()])
is_synthesis = False
if pulse_a.upper() in VOCAB and pulse_b.upper() in VOCAB:
    if VOCAB[pulse_a.upper()][2] * VOCAB[pulse_b.upper()][2] < 0: is_synthesis = True
    if "ГАРМОНИЯ" in pair and "ВЕЧНОСТЬ" in pair: is_synthesis = True

# --- РАБОТА С ИЗОБРАЖЕНИЕМ ---
img_file = st.file_uploader("Загрузить растровый источник", type=["jpg", "png"])

if img_file:
    col1, col2 = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    
    # ПРЕВЬЮ (ВСЕГДА ВИДИМО)
    col1.image(img_src, caption="Входной сигнал (Preview)", use_container_width=True)
    
    if st.button("Запустить аналитический резонанс"):
        with st.spinner("Свитие смыслов в S-петле..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            diff_count, layer_stats = 0, {1:0, 2:0, 3:0, 4:0, 5:0}
            en_mod = base_e * (1.5 if is_synthesis else 1.0)
            
            for i in range(total):
                x, y, z_geo = get_sphiral_xyz(i, total)
                px = max(0, min(1023, int((x + 300) / 600 * 1023)))
                py = max(0, min(1023, int((y + 150) / 300 * 1023)))
                
                z_dat = nodes[i].get('z', 0.0)
                # Точка сингулярности: инверсия фазы в S-петле
                s_flip = -1.0 if z_geo == 0 else 1.0
                
                int_a = en_mod * math.sin(z_dat * (base_p + len(pulse_a)*0.1))
                int_b = en_mod * math.sin(z_dat * (base_p + len(pulse_b)*0.1) * s_flip)
                diff = abs(int_a - int_b)
                
                if diff > (en_mod * threshold):
                    diff_count += 1
                    layer_stats[min((i // (total // 5)) + 1, 5)] += 1
                    r, g, b = px_src[px, py]
                    # Рендеринг разности
                    px_out[px, py] = (int(max(0, min(255, r - diff*4))), 
                                      int(max(0, min(255, g + diff*6))), 
                                      int(max(0, min(255, b + diff*12))))
                else: px_out[px, py] = px_src[px, py]

            col2.image(res_img, caption="3D Sfiral Projection", use_container_width=True)
            
            # --- ОТЧЕТ GIDEON ---
            dp = (diff_count / total) * 100
            kc = 100 - dp
            di = np.std(list(layer_stats.values())) / np.mean(list(layer_stats.values())) if diff_count > 0 else 0
            
            outcome = "STANDARD"
            if pair == ["ЖИЗНЬ", "СМЕРТЬ"]: outcome = "ВЕЧНОСТЬ"
            elif pair == ["ПОРЯДОК", "ХАОС"]: outcome = "ГАРМОНИЯ"
            elif "ГАРМОНИЯ" in pair and "ВЕЧНОСТЬ" in pair: outcome = "БОГ (АБСОЛЮТ)"

            st.code(f"""[ОТЧЕТ GIDEON v1.2.1: ANALYTICAL LOGOS]
ВЗАИМОДЕЙСТВИЕ: {pulse_a} + {pulse_b} | РЕЖИМ: {"SYNTHESIS" if is_synthesis else "ALLIANCE"}
РЕЗУЛЬТАТ СИНТЕЗА: {outcome}

МЕТРИКИ:
- Kc (Когерентность): {kc:.1f}%
- Di (Индекс девиации): {di:.4f}
- S-Проницаемость: {100 - (layer_stats[3]/(total/5)*100):.1f}%

ЛОКАЛИЗАЦИЯ (L1-L5): {list(layer_stats.values())}
""", language="text")
