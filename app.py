import streamlit as st
import math
import pandas as pd

# Настройка страницы
st.set_page_config(page_title="Pt100 Error Calculator", layout="wide")

st.title("🧮 Калькулятор погрешности накладного датчика Pt100")
st.markdown("Расчет влияния теплоотвода через провода и стенку трубы.")

# --- БОКОВАЯ ПАНЕЛЬ (ВВОД ДАННЫХ) ---
with st.sidebar:
    st.header("Параметры системы")
    
    st.subheader("Температуры (°C)")
    Tw_C = st.number_input("T воды", value=17.0, step=1.0)
    Tair_C = st.number_input("T воздуха", value=23.0, step=1.0)
    
    st.subheader("Труба и Датчик")
    D_i_mm = st.number_input("D внутр. трубы (мм)", value=10.0)
    S_mm2 = st.number_input("Площадь контакта (мм²)", value=12.0)
    
    st.subheader("Стенка и Паста")
    t_r_mm = st.number_input("Толщина стенки (мм)", value=1.5)
    k_r = st.number_input("k резины (Вт/мК)", value=0.20)
    t_p_mm = st.number_input("Толщина пасты (мм)", value=0.20)
    k_p = st.number_input("k пасты (Вт/мК)", value=1.0)
    spread = st.slider("Фактор растекания (0-идеал, 1-реал)", 0.0, 2.0, 1.0)
    
    st.subheader("Провода")
    n_w = st.number_input("Кол-во жил", value=4, step=1)
    Lw_mm = st.number_input("Длина в воздухе (мм)", value=50.0)
    d_cu_mm = st.number_input("d жилы (мм)", value=0.20)
    d_out_mm = st.number_input("d изоляции (мм)", value=0.60)
    
    st.subheader("Конвекция (Вт/м²К)")
    h_still = st.number_input("Тихий воздух", value=10.0)
    h_draft = st.number_input("Сквозняк", value=40.0)

# --- РАСЧЕТНАЯ ЧАСТЬ (СКРЫТА ОТ ГЛАЗ ПОЛЬЗОВАТЕЛЯ) ---
# Константы
rho_w = 998.0
mu_w = 1.002e-3
k_w = 0.60
cp_w = 4182.0
Pr_w = mu_w * cp_w / k_w
k_cu = 400.0

# Пересчет
Tw_K = Tw_C + 273.15
Tair_K = Tair_C + 273.15
dT_sys = Tw_K - Tair_K
D_i = D_i_mm * 1e-3
S = S_mm2 * 1e-6
t_r = t_r_mm * 1e-3
t_p = t_p_mm * 1e-3
d_cu = d_cu_mm * 1e-3
d_out = d_out_mm * 1e-3
Lw = Lw_mm * 1e-3

# Функция Gw
def calc_Gw(h_air):
    A_cu = math.pi * (d_cu**2) / 4.0
    P_out = math.pi * d_out
    m = math.sqrt(h_air * P_out / (k_cu * A_cu))
    G1 = m * k_cu * A_cu * math.tanh(m * Lw)
    return n_w * G1

Gw_still = calc_Gw(h_still)
Gw_draft = calc_Gw(h_draft)

# Расчет для разных расходов
flows = [5.0, 10.0, 20.0]
results = []

for Q in flows:
    Q_m3s = (Q / 1000.0) / 60.0
    v_avg = Q_m3s / (math.pi * D_i**2 / 4.0)
    Re = rho_w * v_avg * D_i / mu_w
    
    if Re < 2300:
        Nu = 3.66
    else:
        Nu = 0.023 * (Re**0.8) * (Pr_w**0.4)
    
    h_i = Nu * k_w / D_i
    
    # Сопротивление
    r_unit = (1.0/h_i) + (t_r/k_r) + (t_p/k_p) + spread*(t_r/k_r)
    Kw = S / r_unit
    
    # Ошибки
    f_still = Gw_still / (Gw_still + Kw)
    err_still = abs(dT_sys * f_still)
    
    f_draft = Gw_draft / (Gw_draft + Kw)
    err_draft = abs(dT_sys * f_draft)
    
    results.append({
        "Расход (л/мин)": Q,
        "h воды (Вт/м²К)": f"{h_i:.0f}",
        "Ошибка (Тихо) [K]": f"{err_still:.2f}",
        "Ошибка (Сквозняк) [K]": f"{err_draft:.2f}"
    })

# --- ВЫВОД РЕЗУЛЬТАТОВ НА ЭКРАН ---
st.subheader("Результаты расчета")
df = pd.DataFrame(results)

# Красивая таблица
st.table(df)

# Графический вывод
col1, col2 = st.columns(2)
with col1:
    st.info(f"**Тихий воздух:**\n\nДатчик врет примерно на **{df['Ошибка (Тихо) [K]'].iloc[1]} K**")
with col2:
    st.warning(f"**Сквозняк:**\n\nДатчик врет примерно на **{df['Ошибка (Сквозняк) [K]'].iloc[1]} K**")

st.caption("Расчет выполнен на сервере. Исходный код формул скрыт.")
