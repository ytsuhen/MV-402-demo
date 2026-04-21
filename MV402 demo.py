import streamlit as st
import uuid
import time

# Налаштування сторінки
st.set_page_config(page_title="ВЛК 2026: CDS Симулятор", layout="wide", page_icon="🏥")

# ==========================================
# УПРАВЛІННЯ СТАНОМ (SESSION STATE)
# ==========================================
if 'step' not in st.session_state: st.session_state.step = 0
if 'patient_id' not in st.session_state: st.session_state.patient_id = str(uuid.uuid4())[:8].upper()
if 'patient_data' not in st.session_state: st.session_state.patient_data = {}
if 'kep_signed' not in st.session_state: st.session_state.kep_signed = False

def set_step(step): st.session_state.step = step
def reset():
    st.session_state.step = 0
    st.session_state.patient_id = str(uuid.uuid4())[:8].upper()
    st.session_state.kep_signed = False

def calculate_mcda_score(icf_scores):
    THRESHOLD = 10
    active_maxes = [v for v in icf_scores.values() if v > 0]
    if not active_maxes: return 0.0, "Придатний", 0, 0, 0.0
    M = max(active_maxes)
    S_rest = sum(active_maxes) - M
    alpha = (THRESHOLD - M) / THRESHOLD
    score = round(M + (S_rest * alpha), 2)
    if score < 3.0: status = "Придатний"
    elif score < 10.0: status = "Обмежено придатний"
    else: status = "Непридатний"
    return score, status, M, S_rest, alpha

# ==========================================
# КРОК 0: СИМУЛЯТОР (НАЛАШТУВАННЯ ПАЦІЄНТА)
# ==========================================
if st.session_state.step == 0:
    st.title("⚙️ Адмін-панель: Профіль пацієнта (SandBox)")
    st.info("Цей крок дозволяє налаштувати сценарій для демонстрації роботи Rule Engine різним стейкхолдерам.")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Базові дані")
        pib = st.text_input("ПІБ Пацієнта:", "Коваленко Іван Петрович")
        st.code(f"ID в ЕСОЗ: {st.session_state.patient_id}")
        prof = st.selectbox("Військова посада (ТДВ):", ["Снайпер", "Водолаз", "Піхотинець (Загальні вимоги)"])
        has_unstructured = st.checkbox("Симулювати неструктурований запис (Скан МРТ/SNOMED)", value=True)
        
    with col2:
        st.subheader("Клінічна картина (Симуляція записів ЕСОЗ)")
        st.write("Оберіть підтверджені стани з різних доменів:")
        
        opts = [
            "Норма (0 балів)", 
            "Легке порушення .1 (1 бал)", 
            "Помірне порушення .2 (3 бали)",
            "Важке порушення .3 (10 балів) -> Early Exit"
        ]
        
        # 6 Доменів
        c1, c2 = st.columns(2)
        with c1:
            v_vis = st.selectbox("👁️ Зір (b210 - Міопія/Катаракта):", opts, index=1)
            v_hrt = st.selectbox("🫀 Серце (b420 - Гіпертонія/ІХС):", opts, index=2)
            v_bck = st.selectbox("🦴 Спина (b710 - Остеохондроз):", opts, index=0)
        with c2:
            v_stm = st.selectbox("🍏 Травлення (b515 - Гастрит/Виразка):", opts, index=1)
            v_res = st.selectbox("🫁 Дихальна (b440 - Астма):", opts, index=0)
            v_ear = st.selectbox("👂 Слух (b230 - Туговухість):", opts, index=0)

    if st.button("Зберегти та Перейти в Кабінет ВЛК ➔", type="primary", use_container_width=True):
        st.session_state.patient_data = {
            "pib": pib, "id": st.session_state.patient_id, "prof": prof, "unstructured": has_unstructured,
            "icf_scores": {
                "Зір": int(v_vis.split("(")[1].split(" ")[0]),
                "Серце": int(v_hrt.split("(")[1].split(" ")[0]),
                "Спина": int(v_bck.split("(")[1].split(" ")[0]),
                "Травлення": int(v_stm.split("(")[1].split(" ")[0]),
                "Дихання": int(v_res.split("(")[1].split(" ")[0]),
                "Слух": int(v_ear.split("(")[1].split(" ")[0])
            }
        }
        set_step(1); st.rerun()

# ==========================================
# КРОК 1: ВИБІР МАРШРУТУ
# ==========================================
elif st.session_state.step == 1:
    pd = st.session_state.patient_data
    st.title("🏥 Кабінет Лікаря ВЛК")
    st.success(f"**Пацієнт:** {pd['pib']} | **ID:** {pd['id']} | **Посада (ТДВ):** {pd['prof']}")
    
    st.header("Оберіть сценарій маршрутизації (Maturity Model)")
    route = st.radio("Рівень автоматизації CDS:", [
        "1) Повністю автоматичний маршрут (CDS працює на 100%, авто-мапінг усіх реєстрів)",
        "2) Гібридний маршрут (CDS діє, але потребує ручної валідації КЕП для неструктурованих даних)"
    ])
    
    if st.button("Запустити Rule Engine ➔", type="primary"):
        st.session_state.route = 1 if "автоматичний" in route else 2
        set_step(2); st.rerun()

# ==========================================
# КРОК 2: МАПІНГ ТА ГРАФ ЗНАНЬ
# ==========================================
elif st.session_state.step == 2:
    pd = st.session_state.patient_data
    st.title("🧠 Архітектура Мапінгу (Knowledge Graph)")
    st.markdown("Презентаційний зріз того, як система створює **семантичні зв'язки** між розрізненими державними та міжнародними реєстрами.")
    
    with st.spinner("Синхронізація ЕСОЗ ↔ ВООЗ ↔ НСЗУ..."): time.sleep(1)
        
    t1, t2, t3 = st.columns(3)
    
    with t1:
        st.info("Шари 1-2: ВООЗ (ICF Core Sets)")
        st.write("Трансляція діагнозу в функції")
        st.code("""
[ЕСОЗ]: I11.9 (Гіпертонія)
 └── Протокол: WHO ICF
      └── Trigger: b420 (Функції АТ)
      └── Trigger: b410 (Функції серця)
        """, language="yaml")
        
    with t2:
        st.info("Шар 3: НСЗУ (ACHI Докази)")
        st.write("Пошук інструментальних підтверджень")
        st.code("""
[Правило ПМГ Пакет 9]:
IF b420 > 0:
 └── EXPECT ACHI: 11700-00 (ЕКГ)
 └── EXPECT ACHI: 55113-00 (ЕхоКГ)
        """, language="yaml")
        
    with t3:
        st.info("Шар 4: МОУ (Наказ №402)")
        st.write("Звірка результатів з нормами")
        st.code("""
[Клінічна валідація]:
IF ACHI 11700-00 EXIST:
 └── CHECK LOINC: 8480-6 (АТ)
      └── IF > 159 -> Severity .2
      └── IF > 180 -> Severity .3
        """, language="yaml")

    st.markdown("---")
    
    # Логіка маршрутів і неструктурованих даних
    if pd["unstructured"]:
        if st.session_state.route == 1:
            st.error("❌ АВТОМАТИЗАЦІЮ ПЕРЕРВАНО: Виявлено неструктурований запис (Скан-копія PDF від приватної клініки). За поточними стандартами довіри до даних, система не може прийняти рішення без КЕП лікаря ВЛК. Оберіть Гібридний маршрут.")
            if st.button("⬅️ Повернутися до вибору маршруту"): set_step(1); st.rerun()
                
        elif st.session_state.route == 2:
            st.warning("⚠️ ГІБРИДНИЙ РЕЖИМ: Знайдено скан МРТ (Домен Спина). Алгоритм NLP (SNOMED-мапінг) розпізнав: '266249003 (Протрузія L4-L5)'.")
            if not st.session_state.kep_signed:
                if st.button("✍️ Валідувати даний запис та накласти КЕП лікаря"):
                    st.session_state.kep_signed = True
                    st.rerun()
            else:
                st.success("✅ КЕП накладено. Юридичну відповідальність підтверджено. Дані легалізовано для MCDA.")
                if pd["icf_scores"]["Спина"] == 0: pd["icf_scores"]["Спина"] = 1
                if st.button("Перейти до розрахунку статусів ➔", type="primary"): set_step(3); st.rerun()
    else:
        st.success("✅ Всі дані структуровані. Антифрод-матриця підтвердила достовірність діагнозів в ЕСОЗ.")
        if st.button("Перейти до розрахунку статусів ➔", type="primary"): set_step(3); st.rerun()

# ==========================================
# КРОК 3: EARLY EXIT ТА MCDA
# ==========================================
elif st.session_state.step == 3:
    pd = st.session_state.patient_data
    st.title("📋 Фінальний Висновок Rule Engine")
    
    # 1. Перевірка на базовий Early Exit (Важке порушення .3)
    is_base_early_exit = any(s == 10 for s in pd["icf_scores"].values())
    
    # 2. Перевірка на TDV Early Exit (Таблиця Додаткових Вимог)
    tdv_fail_reason = None
    if pd["prof"] == "Снайпер" and pd["icf_scores"]["Зір"] > 0:
        tdv_fail_reason = "Посада Снайпер: Виявлено порушення зору (Таблиця 'В' Наказу 402)."
    elif pd["prof"] == "Водолаз" and (pd["icf_scores"]["Слух"] > 0 or pd["icf_scores"]["Дихання"] > 0):
        tdv_fail_reason = "Посада Водолаз: Виявлено порушення слуху або дихальної системи."
        
    is_tdv_early_exit = tdv_fail_reason is not None

    # ВІЗУАЛІЗАЦІЯ EARLY EXIT
    if is_base_early_exit or is_tdv_early_exit:
        st.error("🚨 СПРАЦЮВАВ 'EARLY EXIT' (КОРОТКИЙ ВИХІД)")
        st.markdown("### Загальний статус: **НЕПРИДАТНИЙ**")
        
        if is_base_early_exit:
            st.info("**Причина (Базова):** Знайдено кваліфікатор тяжкості .3 (Важке порушення). Прямий мапінг застосував імперативну статтю. MCDA обчислення зупинено для збереження обчислювальних ресурсів.")
        if is_tdv_early_exit:
            st.warning(f"**Причина (ТДВ):** Спрацював конфлікт з Таблицею Додаткових Вимог. {tdv_fail_reason} MCDA обчислення зупинено.")
            
    # ВІЗУАЛІЗАЦІЯ MCDA (Сіра зона)
    else:
        score, status, M, S_rest, alpha = calculate_mcda_score(pd["icf_scores"])
        
        if status == "Придатний": st.success(f"⚖️ СТАТУС: **{status.upper()}** (Бал: {score})")
        else: st.warning(f"⚖️ СТАТУС: **{status.upper()}** (Бал: {score})")
            
        st.success(f"🎯 СТАТУС ТДВ: **Придатний до служби на посаді '{pd['prof']}'** (Конфліктів не виявлено)")

        st.markdown("---")
        st.subheader("Розшифровка 'Сірої Зони' (Explainable AI)")
        st.write("Прямих підстав для списання (Early Exit) не знайдено. Статус розраховано за гібридною MCDA моделлю (AMA-асимптота).")
        
        c1, c2, c3 = st.columns(3)
        c1.metric("Домінуючий тягар (M)", M, "MAX серед векторів")
        c2.metric("Фоновий тягар (S_rest)", S_rest, "Сума супутніх")
        c3.metric("Запас міцності (α)", f"{alpha*100}%", f"(10 - {M}) / 10")
        
        st.code(f"Формула: M + (S_rest * α)  =>  {M} + ({S_rest} * {alpha}) = {score} балів", language="python")
        
    st.markdown("---")
    if st.button("🔄 Почати новий кейс"): reset(); st.rerun()
