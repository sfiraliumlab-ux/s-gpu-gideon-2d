import streamlit as st
import json
import math
import os
import numpy as np
from PIL import Image

st.set_page_config(page_title="GIDEON | FSIN & Emergency VRAM", layout="wide")
st.title("S-GPU GIDEON v1.3.1: Фрактальный Нейрон")

# --- СЕМАНТИЧЕСКИЙ ГЕНОМ (LOGOS-3) ---
VOCAB = {
    "ПОРЯДОК": (1.0, -1.0, 1),   "ХАОС": (-1.0, 1.0, -1),
    "ЖИЗНЬ": (0.9, -0.9, 1),     "СМЕРТЬ": (-0.9, 0.9, -1),
    "ИСТИНА": (0.8, -0.8, 1),    "ЛОЖЬ": (-0.8, 0.8, -1),
    "ГАРМОНИЯ": (0.0, 0.0, 1),   "ВЕЧНОСТЬ": (0.0, 0.0, -1),
    "БОГ": (0.0, 0.0, 1)
}

# --- FSIN ENGINE ---
class FSIN:
    def __init__(self, gain):
        self.gain = gain
        self.bias = 0.01

    def activate(self, diff, s_factor):
        # Фрактальная S-образная функция активации
        try:
            return 1 / (1 + math.exp(- (diff * self.gain * s_factor) + self.bias))
        except OverflowError:
            return 1.0 if diff > 0 else 0.0

# --- БЛОК ЗАГРУЗКИ И РЕГЕНЕРАЦИИ ---
@st.cache_data
def load_vram_resource(filename):
    if os.path.exists(filename):
        try:
            with open(filename, 'r', encoding='utf-8') as f:
                data = json.load(f)
                nodes = data.get('nodes', data) if isinstance(data, dict) else data
                return nodes, "OK"
        except Exception as e:
            return None, f"CORRUPTED: {str(e)}"
    return None, "NOT_FOUND"

nodes, vram_status = load_vram_resource('matrix.json')

if vram_status != "OK":
    st.error(f"❌ Критическая ошибка VRAM: {vram_status}")
    if st.button("🚀 Регенерировать эталонную VRAM (391 392 узла)"):
        nodes = [{'id': i, 'z': math.sin(i * 0.05) * math.cos(i * 0.02)} for i in range(391392)]
        vram_status = "GENERATED"
        st.success("✅ Матрица восстановлена в оперативной памяти.")
    else:
        st.info("Приложение ожидает файл matrix.json или нажатия кнопки регенерации.")
        st.stop()
else:
    st.success(f"✅ VRAM активна: {len(nodes)} узлов загружено из репозитария.")

# --- ГЕОМЕТРИЯ СФИРАЛИ БАСАРГИНА (3D) ---
def get_xyz(i, total):
    t = (i / total) * 2 - 1
    R = 150
    # S-образная петля (Серединный Предел)
    if abs(t) < 0.15:
        sn = (t + 0.15) / 0.3
        return math.cos(sn * math.pi) * R, math.sin(sn * math.pi * 2) * (R/2), 0
    # Зеркальные антисимметричные витки
    angle = t * math.pi * 6
    side = -1 if t < 0 else 1
    x = R * math.cos(angle) + (side * R)
    y = (side * R * math.sin(angle)) if side < 0 else (-R * math.sin(angle))
    z = t * 100
    return x, y, z

# --- ИНТЕРФЕЙС УПРАВЛЕНИЯ ---
st.sidebar.header("Параметры FSIN Core-13")
f_gain = st.sidebar.slider("Fractal Gain (Проницаемость)", 0.1, 10.0, 1.2)
threshold = st.sidebar.slider("Gate Threshold (Порог)", 0.1, 0.99, 0.85)

st.subheader("Центральный Реактор")
c1, c2 = st.columns(2)
p_a = c1.text_input("Импульс А", "ГАРМОНИЯ")
p_b = c2.text_input("Импульс Б", "ВЕЧНОСТЬ")

img_file = st.file_uploader("Загрузить растровый источник", type=["jpg", "png"])

if img_file:
    col_l, col_r = st.columns(2)
    img_src = Image.open(img_file).convert('RGB')
    col_l.image(img_src, caption="Входной сигнал (Preview)", use_container_width=True)
    
    if st.button("Инициировать FSIN-резонанс"):
        with st.spinner("Обучение нейрона на точке сингулярности..."):
            canv = 1024
            res_img = Image.new('RGB', (canv, canv), (0,0,0))
            px_out, px_src = res_img.load(), img_src.resize((canv, canv)).load()
            
            total = len(nodes)
            diff_count, l_stats = 0, {i:0 for i in range(1, 6)}
            fsin = FSIN(f_gain)
            
            for i in range(total):
                x, y, z_geo = get_xyz(i, total)
                px = max(0, min(1023, int((x + 300) / 600 * 1023)))
                py = max(0, min(1023, int((y + 150) / 300 * 1023)))
                
                z_dat = nodes[i].get('z', 0.0)
                # Точка сингулярности S-петли
                s_factor = -1.0 if z_geo == 0 else 1.0
                
                # Дифференциальная активация FSIN
                d = abs(math.sin(z_dat * 13.5) - math.sin(z_dat * 13.5 * s_factor))
                activation = fsin.activate(d, s_factor)
                
                if activation > threshold:
                    diff_count += 1
                    l_stats[min((i // (total // 5)) + 1, 5)] += 1
                    r, g, b = px_src[px, py]
                    # Рендеринг нейронной вспышки
                    px_out[px, py] = (int(max(0, min(255, r + activation*40))), 
                                      int(max(0, min(255, g + activation*20))), 
                                      int(max(0, min(255, b + activation*120))))
                else:
                    px_out[px, py] = px_src[px, py]

            col_r.image(res_img, caption="FSIN 3D Projection", use_container_width=True)
            
            # --- ОТЧЕТ FSIN ---
            dp = (diff_count / total) * 100
            vals = list(l_stats.values())
            di = np.std(vals) / np.mean(vals) if sum(vals) > 0 else 0
            
            pair = sorted([p_a.upper(), p_b.upper()])
            outcome = "БОГ (АБСОЛЮТ)" if "ГАРМОНИЯ" in pair and "ВЕЧНОСТЬ" in pair else "STANDARD"

            st.code(f"""[ОТЧЕТ GIDEON v1.3.1: FSIN ACTIVE]
ОПЕРАЦИЯ: {p_a} + {p_b} | СИНТЕЗ: {outcome}
СТАТУС VRAM: {vram_status}

МЕТРИКИ FSIN:
- Активация нейрона: {diff_count} узлов ({dp:.1f}%)
- Индекс девиации (Di): {di:.4f}
- Эффективность пробоя: {(1-di)*100:.1f}%

ЛОКАЛИЗАЦИЯ (L1-L5): {vals}
""", language="text")
