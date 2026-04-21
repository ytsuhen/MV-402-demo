import streamlit as st
import time

# Налаштування сторінки
st.set_page_config(page_title="CDS: Маршрут Пацієнта", layout="wide", page_icon="🏥")

# ==========================================
# УПРАВЛІННЯ СТАНОМ (SESSION STATE)
# ==========================================
# Зберігаємо дані між кроками, щоб сторінка не оновлювалася "в нуль"
if 'step' not in st.session_state:
    st.session_state.step = 1
if 'patient_icd' not in st.session_state:
    st.session_state.patient_icd = []
if 'patient_icf' not in st.session_state:
    st.session_state.patient_icf = {}
if 'fraud_passed' not in st.session_state:
    st.session_state.fraud_passed = False

def next_step(): st.session_state.step += 1
def prev_step(): st.session_state.step -= 1
def reset():
    st.session_state.step = 1
    st.session_state.patient_icd = []
    st.session_state.patient_icf = {}
    st.session_state.fraud_passed = False

# ==========================================
# МАТЕМАТИЧНЕ ЯДРО MCDA (з попередніх кроків)
# ==========================================
def calculate_mcda_score(icf_data):
    THRESHOLD = 10
    active_maxes = [v for v in icf_data.values() if v > 0]
    
    if not active_maxes:
        return 0.0, "Придатний", 0, 0, 0.0
        
    M = max(active_maxes)
    S_rest = sum(active_maxes) - M
    alpha = (THRESHOLD - M) / THRESHOLD
    score = round(M + (S_rest * alpha), 2)
    
    if score < 3.0: status = "Придатний"
    elif score < 10.0: status = "Обмежено придатний"
    else: status = "Непридатний"
        
    return score, status, M, S_rest, alpha

# ==========================================
# ІНТЕРФЕЙС ТА ЛОГІКА КРОКІВ
# ==========================================
st.title("🏥 Клінічний маршрут ВЛК (Rule Engine Demo)")
st.progress(st.session_state.step / 4) # Смуга прогресу

# Словник тяжкості
severity_map = {"Норма <5% (0 балів)": 0, "Легке .1 (1 бал)": 1, "Помірне .2 (3 бали)": 3, "Важке .3 (10 балів)": 10}

# ------------------------------------------
# КРОК 1: ІНТЕГРАЦІЯ З ЕСОЗ (МКХ-10)
# ------------------------------------------
if st.session_state.step == 1:
    st.header("Крок 1. Завантаження діагнозів (ΕΣΟЗ)")
    st.write("Система автоматично підтягує діагнози, встановлені сімейним лікарем або в госпіталі.")
    
    # Симуляція бази діагнозів
    available_icd = [
        "I11.9 - Гіпертонічна хвороба", 
        "H52.1 - Міопія", 
        "M42.1 - Остеохондроз хребта",
        "K29.3 - Хронічний гастрит"
    ]
    
    selected_icd = st.multiselect("Підтверджені діагнози (МКХ-10):", available_icd, default=st.session_state.patient_icd)
    
    st.info("💡 Правило: Система згенерує смарт-чеклист МКФ тільки для тих систем організму, які пов'язані з обраними діагнозами.")
    
    if st.button("Далі ➔ Генерація ICF Core Sets", type="primary"):
        if not selected_icd:
            st.error("Будь ласка, оберіть хоча б один діагноз.")
        else:
            st.session_state.patient_icd = selected_icd
            next_step()
            st.rerun()

# ------------------------------------------
# КРОК 2: WHO ICF CORE SETS (СМАРТ-ЧЕКЛИСТ)
# ------------------------------------------
elif st.session_state.step == 2:
    st.header("Крок 2. Оцінка функцій лікарем ВЛК")
    st.write("Замість 1400 кодів МКФ, система згенерувала вузький профіль спеціально для обраних діагнозів.")
    
    st.session_state.patient_icf = {}
    col1, col2 = st.columns(2)
    
    # Динамічно показуємо тільки те, що треба
    with col1:
        if any("I11.9" in d for d in st.session_state.patient_icd):
            st.subheader("🫀 Серцево-судинна (I11.9)")
            st.session_state.patient_icf['Серце'] = severity_map[st.selectbox("b420 - Артеріальний тиск", list(severity_map.keys()))]
            
        if any("K29.3" in d for d in st.session_state.patient_icd):
            st.subheader("🍏 Травлення (K29.3)")
            st.session_state.patient_icf['Шлунок'] = severity_map[st.selectbox("b515 - Травні функції", list(severity_map.keys()))]

    with col2:
        if any("H52.1" in d for d in st.session_state.patient_icd):
            st.subheader("👁️ Зір (H52.1)")
            st.session_state.patient_icf['Зір'] = severity_map[st.selectbox("b210 - Гострота зору", list(severity_map.keys()))]
            
        if any("M42.1" in d for d in st.session_state.patient_icd):
            st.subheader("🦴 Опорно-руховий (M42.1)")
            st.session_state.patient_icf['Спина'] = severity_map[st.selectbox("b710 - Рухливість суглобів", list(severity_map.keys()))]

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("⬅️ Назад"): prev_step(); st.rerun()
    with col_btn2:
        if st.button("Далі ➔ Антифрод Валідація", type="primary"):
            next_step(); st.rerun()

# ------------------------------------------
# КРОК 3: ВАЛІДАЦІЯ ПМГ (АНТИФРОД)
# ------------------------------------------
elif st.session_state.step == 3:
    st.header("Крок 3. Валідація доказів (НСЗУ/ACHI)")
    st.write("Система автоматично перевіряє ЕСОЗ на наявність інструментальних досліджень для заявленої тяжкості.")
    
    # Шукаємо найважче порушення
    max_val = max(st.session_state.patient_icf.values()) if st.session_state.patient_icf else 0
    
    with st.spinner('Звернення до графа знань та реєстрів ЕСОЗ...'):
        time.sleep(1) # Симуляція завантаження
    
    if max_val >= 3: # Якщо Помірне або Важке
        st.warning("⚠️ Виявлено діагнози рівня .2 (Помірне) або .3 (Важке). Ініційовано протокол доказовості.")
        
        # Симуляція матриці валідації
        if "Серце" in st.session_state.patient_icf and st.session_state.patient_icf["Серце"] >= 3:
            st.write("**Домен: Серце (b420)**")
            st.write("🔍 *Вимога ПМГ:* ACHI 11700-00 (ЕКГ) або ACHI 55113-00 (ЕхоКГ).")
            st.success("✅ Знайдено в ЕСОЗ: ЕКГ від 12.10.2023. Дані відповідають Наказу №402.")
            
        if "Зір" in st.session_state.patient_icf and st.session_state.patient_icf["Зір"] >= 3:
            st.write("**Домен: Зір (b210)**")
            st.write("🔍 *Вимога ПМГ:* ACHI 11200-00 (Офтальмоскопія).")
            st.success("✅ Знайдено в ЕСОЗ: Висновок офтальмолога від 05.11.2023.")
            
        st.session_state.fraud_passed = True
    else:
        st.info("✅ Всі встановлені порушення належать до Легких (.1) або Норми. Жорсткий інструментальний контроль не вимагається.")
        st.session_state.fraud_passed = True

    col_btn1, col_btn2 = st.columns([1, 4])
    with col_btn1:
        if st.button("⬅️ Назад"): prev_step(); st.rerun()
    with col_btn2:
        if st.session_state.fraud_passed:
            if st.button("Схвалено ➔ Фінальний статус (MCDA)", type="primary"):
                next_step(); st.rerun()

# ------------------------------------------
# КРОК 4: ФІНАЛЬНИЙ ВИСНОВОК (MCDA)
# ------------------------------------------
elif st.session_state.step == 4:
    st.header("Крок 4. Автоматизований висновок ВЛК")
    
    # Викликаємо нашу математику
    score, status, M, S_rest, alpha = calculate_mcda_score(st.session_state.patient_icf)
    
    # Великий віджет результату
    if status == "Придатний": st.success(f"⚖️ СТАТУС: {status} | БАЛ: {score}")
    elif status == "Обмежено придатний": st.warning(f"⚖️ СТАТУС: {status} | БАЛ: {score}")
    else: st.error(f"⚖️ СТАТУС: {status} | БАЛ: {score}")

    # Лог розрахунків для комісії
    with st.expander("Розгорнути математичний аудит (AMA Asymptote)", expanded=True):
        st.write(f"Чисті максимальні вектори (вже пройшли внутрішньодоменне поглинання): `{st.session_state.patient_icf}`")
        st.markdown(f"""
        - **Головна хвороба (M):** {M}
        - **Супутній тягар (S_rest):** {S_rest}
        - **Динамічний запас міцності (α):** {alpha}
        - **Формула:** `{M} + ({S_rest} * {alpha}) = {score}`
        """)

    st.markdown("---")
    if st.button("🔄 Почати новий огляд лікаря"):
        reset()
        st.rerun()
