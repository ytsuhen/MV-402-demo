import streamlit as st
import uuid
import time

st.set_page_config(page_title="ВЛК 2026: CDS Симулятор", layout="wide", page_icon="🏥")

# ==========================================
# УПРАВЛІННЯ СТАНОМ ТА БАЗА ЗНАНЬ
# ==========================================
def init_state():
    if 'step' not in st.session_state: st.session_state.step = 0
    if 'patient_id' not in st.session_state: st.session_state.patient_id = str(uuid.uuid4())[:8].upper()
    if 'patient_data' not in st.session_state: st.session_state.patient_data = {"icf_scores": {}}
    if 'paper_data' not in st.session_state: st.session_state.paper_data = {}
    if 'kep_signed' not in st.session_state: st.session_state.kep_signed = False

init_state()

def set_step(step): 
    st.session_state.step = step
    
def reset_all():
    st.session_state.clear()
    init_state()

# ПРОФЕСІЙНА БАЗА ДАНИХ (Реальні коди ICD-10, ICF, ACHI, LOINC/SNOMED)
KNOWLEDGE_BASE = {
    "Зір": {"icd": "H52.1 (Міопія)", "icf": "b210", "achi": "11215-00 (Перевірка гостроти зору)", "loinc": "LOINC: 32451-7 (Гострота зору)"},
    "Серце": {"icd": "I11.9 (Гіпертонія)", "icf": "b420", "achi": "11712-00 (ЕКГ у спокої)", "loinc": "LOINC: 8480-6 (Систолічний АТ)"},
    "Спина": {"icd": "M42.1 (Остеохондроз)", "icf": "b710", "achi": "56220-00 (МРТ хребта)", "loinc": "SNOMED: 282822008 (Протрузія диска)"},
    "Травлення": {"icd": "K29.3 (Хрон. гастрит)", "icf": "b515", "achi": "30473-00 (ЕГДС / Ендоскопія)", "loinc": "SNOMED: 235866006 (Запалення слизової)"},
    "Дихання": {"icd": "J45.9 (Астма)", "icf": "b440", "achi": "11503-00 (Спірометрія)", "loinc": "LOINC: 20150-9 (ОФВ1 / FEV1)"},
    "Слух": {"icd": "H90.3 (Туговухість)", "icf": "b230", "achi": "11309-00 (Тональна аудіометрія)", "loinc": "LOINC: 89020-2 (Поріг чутності)"}
}

# Словник тяжкості (Ховаємо бали від користувача)
SEVERITY_MAP = {
    "Легке порушення (.1)": 1,
    "Помірне порушення (.2)": 3,
    "Важке порушення (.3)": 10
}
OPTS = list(SEVERITY_MAP.keys())

def calculate_mcda_score(icf_scores):
    THRESHOLD = 10
    active_maxes = [v for v in icf_scores.values() if v > 0]
    if not active_maxes: return 0.0, "Придатний", 0, 0, 0.0
    M = max(active_maxes)
    S_rest = sum(active_maxes) - M
    alpha = (THRESHOLD - M) / THRESHOLD
    score = round(M + (S_rest * alpha), 2)
    
    # Офіційні статуси Наказу №402
    if score < 3.0: 
        status = "Придатний"
    elif score < 10.0: 
        status = "Придатний до служби у військових частинах забезпечення, ТЦК та СП"
    else: 
        status = "Непридатний"
        
    return score, status, M, S_rest, alpha

# БОКОВЕ МЕНЮ (ІНСТРУКЦІЯ ДЛЯ СТЕЙКХОЛДЕРІВ)
with st.sidebar:
    st.header("📖 Пам'ятка для комісії")
    st.markdown("Цей симулятор дозволяє протестувати 3 ключові механіки нашого Rule Engine:")
    
    with st.expander("🛡️ Захист від фроду (MCDA)", expanded=True):
        st.write("* **Як тестувати:** Оберіть 4-5 хвороб з тяжкістю 'Легке' або 'Помірне'.")
        st.write("* **Результат:** MCDA-асимптота зупинить набір балів до 10. Статус 'Непридатний' заблоковано.")
        
    with st.expander("⚡ Короткий вихід (Early Exit)", expanded=False):
        st.write("* **Як тестувати:** Дайте хоча б одній хворобі 'Важке порушення .3'.")
        st.write("* **Результат:** Алгоритм миттєво списує пацієнта за прямою статтею Наказу 402.")
        
    with st.expander("🎯 Конфлікт ТДВ (Спецпосади)", expanded=False):
        st.write("* **Як тестувати:** Посада 'Снайпер' + 'Легке' порушення зору.")
        st.write("* **Результат:** Загалом Придатний, але система блокує призначення на цільову посаду.")
        
    st.markdown("---")
    st.caption("Версія прототипу: 1.2. (Клінічно точний мапінг)")

# Індикатор прогресу (навігація)
steps_labels = ["1. Налаштування", "2. Вибір маршруту", "3. CDS Мапінг", "4. Фінальний статус"]
st.progress((st.session_state.step + 1) / 4, text=f"Етап: {steps_labels[st.session_state.step]}")
st.write("---")

# ==========================================
# КРОК 0: СИМУЛЯТОР (НАЛАШТУВАННЯ)
# ==========================================
if st.session_state.step == 0:
    st.title("⚙️ Адмін-панель: Профіль пацієнта (SandBox)")
    
    col1, col2 = st.columns([1, 2])
    with col1:
        st.subheader("Базові дані")
        pib = st.text_input("ПІБ Пацієнта:", "Коваленко Іван Петрович")
        st.code(f"ID в ЕСОЗ: {st.session_state.patient_id}")
        prof = st.selectbox("Військова посада (ТДВ):", ["Снайпер", "Водолаз", "Піхотинець (Загальні)"])
        has_unstructured = st.checkbox("Симулювати неструктурований запис (МРТ з приватної клініки)", value=False)
        
    with col2:
        st.subheader("Клінічна картина (Opt-in чекбокси)")
        st.write("Відмітьте системи, у яких є зафіксовані порушення:")
        
        active_scores = {}
        for domain, db in KNOWLEDGE_BASE.items():
            if st.checkbox(f"Включити домен: {domain} ({db['icd']})", key=f"chk_{domain}"):
                val = st.selectbox(f"Тяжкість ({db['icf']}):", OPTS, key=f"sel_{domain}")
                active_scores[domain] = SEVERITY_MAP[val]

    if st.button("Зберегти та Перейти в Кабінет ВЛК ➔", type="primary", key="btn_save_patient"):
        if not active_scores:
            st.error("Будь ласка, оберіть хоча б одне порушення для демонстрації.")
        else:
            st.session_state.patient_data = {
                "pib": pib, "id": st.session_state.patient_id, "prof": prof, 
                "unstructured": has_unstructured, "icf_scores": active_scores
            }
            set_step(1); st.rerun()

# ==========================================
# КРОК 1: ВИБІР МАРШРУТУ
# ==========================================
elif st.session_state.step == 1:
    pd = st.session_state.patient_data
    st.title("🏥 Кабінет Лікаря ВЛК")
    st.success(f"**Пацієнт:** {pd['pib']} | **ID:** {pd['id']} | **Посада (ТДВ):** {pd['prof']}")
    
    st.header("Оберіть сценарій маршрутизації")
    route = st.radio("Рівень автоматизації CDS:", [
        "1) Автоматичний маршрут (CDS 100%, авто-мапінг усіх реєстрів)",
        "2) Гібридний маршрут (CDS діє, але потребує КЕП для неструктурованих даних)",
        "3) Паперовий маршрут (Legacy Mode: Повністю ручне введення МКХ ➔ МКФ ➔ Обстеження)"
    ])
    
    if st.button("Запустити ➔", type="primary", key="btn_choose_route"):
        if "Автоматичний" in route: st.session_state.route = 1
        elif "Гібридний" in route: st.session_state.route = 2
        else: st.session_state.route = 3
        set_step(2); st.rerun()

# ==========================================
# КРОК 2: МАПІНГ ТА ВАЛІДАЦІЯ
# ==========================================
elif st.session_state.step == 2:
    pd = st.session_state.patient_data
    
    if st.session_state.route in [1, 2]:
        st.title("🧠 Динамічний Граф Знань (CDS Мапінг)")
        st.write("Система автоматично згенерувала дерева доказовості для обраних діагнозів.")
        
        with st.spinner("Синхронізація ЕСОЗ ↔ ВООЗ ↔ НСЗУ..."): time.sleep(0.5)
            
        active_domains = pd["icf_scores"].keys()
        cols = st.columns(len(active_domains))
        
        for idx, domain in enumerate(active_domains):
            db = KNOWLEDGE_BASE[domain]
            # Зворотний мапінг балів у текст для красивого виводу
            severity_text = [k for k, v in SEVERITY_MAP.items() if v == pd["icf_scores"][domain]][0].split(" ")[-1]
            
            with cols[idx]:
                st.info(f"Домен: {domain}")
                st.code(f"""
[1. ЕСОЗ - Діагноз]
 └── МКХ-10: {db['icd']}

[2. ВООЗ - Функція]
 └── ICF Core Set: {db['icf']}
 └── Оцінка лікаря: {severity_text}
 
[3. НСЗУ - Доказ]
 └── ACHI: {db['achi']}
 
[4. МОУ - Валідація]
 └── {db['loinc']}
 └── Статус: ПІДТВЕРДЖЕНО
                """, language="yaml")

        st.markdown("---")
        
        if pd["unstructured"]:
            if st.session_state.route == 1:
                st.error("❌ АВТО-МАРШРУТ ПЕРЕРВАНО: Виявлено неструктурований запис (Скан PDF). Система потребує Гібридного маршруту та КЕП.")
                if st.button("⬅️ Назад до вибору маршруту", key="btn_back_route"): 
                    set_step(1); st.rerun()
            elif st.session_state.route == 2:
                st.warning("⚠️ ГІБРИДНИЙ РЕЖИМ: Знайдено скан документа. Алгоритм NLP розпізнав: 'Протрузія диска'.")
                if not st.session_state.kep_signed:
                    if st.button("✍️ Валідувати КЕП", key="btn_sign_kep"): 
                        st.session_state.kep_signed = True; st.rerun()
                else:
                    st.success("✅ КЕП накладено. Дані легалізовано.")
                    if st.button("Перейти до статусів ➔", type="primary", key="btn_go_status_hybrid"): 
                        set_step(3); st.rerun()
        else:
            st.success("✅ Всі дані структуровані. Антифрод-матриця відпрацювала.")
            if st.button("Перейти до статусів ➔", type="primary", key="btn_go_status_auto"): 
                set_step(3); st.rerun()

    elif st.session_state.route == 3:
        st.title("📝 Паперовий маршрут (Legacy Mode)")
        st.warning("CDS-модуль вимкнено. Лікар має самостійно 'зібрати' зв'язки між класифікаторами для формування висновку.")
        
        st.subheader("Ручне введення даних")
        manual_icd = st.selectbox("1. Оберіть діагноз з паперової довідки (МКХ-10):", [db["icd"] for db in KNOWLEDGE_BASE.values()])
        target_domain = next(dom for dom, db in KNOWLEDGE_BASE.items() if db["icd"] == manual_icd)
        
        # Динамічні селекти на базі словника, а не жорстко прописані
        manual_icf = st.selectbox("2. Визначте порушену функцію (МКФ):", list(set(db["icf"] for db in KNOWLEDGE_BASE.values())))
        manual_achi = st.selectbox("3. Яке обстеження підтверджує це (ACHI)?", list(set(db["achi"] for db in KNOWLEDGE_BASE.values())))
        manual_sev = st.selectbox("4. Оцініть тяжкість:", OPTS)
        
        if st.button("Додати до висновку ➕", key="btn_add_paper"):
            correct_icf = KNOWLEDGE_BASE[target_domain]["icf"]
            if manual_icf != correct_icf:
                st.error(f"❌ ПОМИЛКА МЕДИЧНОГО КОДУВАННЯ: Для діагнозу {manual_icd} функція має бути {correct_icf}, а не {manual_icf}. ВЛК може бути оскаржена.")
            else:
                score_val = SEVERITY_MAP[manual_sev]
                st.session_state.paper_data[target_domain] = score_val
                st.success(f"Додано: {target_domain} -> {manual_sev}")
                
        st.write("---")
        st.write(f"**Зараз у висновку:** {st.session_state.paper_data}")
        
        if st.button("Завершити ручний ввід і порахувати ➔", type="primary", key="btn_go_status_paper"):
            if not st.session_state.paper_data: 
                st.error("Додайте хоча б один діагноз.")
            else:
                st.session_state.patient_data["icf_scores"] = st.session_state.paper_data
                set_step(3); st.rerun()

# ==========================================
# КРОК 3: ФІНАЛЬНИЙ СТАТУС (EARLY EXIT / MCDA)
# ==========================================
elif st.session_state.step == 3:
    pd = st.session_state.patient_data
    st.title("📋 Фінальний Висновок Rule Engine")
    
    is_base_early_exit = any(s == 10 for s in pd["icf_scores"].values())
    
    tdv_fail = None
    if pd["prof"] == "Снайпер" and pd.get("icf_scores", {}).get("Зір", 0) > 0:
        tdv_fail = "Снайпер: Порушення зору."
    elif pd["prof"] == "Водолаз" and (pd.get("icf_scores", {}).get("Слух", 0) > 0 or pd.get("icf_scores", {}).get("Дихання", 0) > 0):
        tdv_fail = "Водолаз: Порушення слуху/дихання."
        
    is_tdv_early_exit = tdv_fail is not None

    if is_base_early_exit or is_tdv_early_exit:
        st.error("🚨 СПРАЦЮВАВ МЕХАНІЗМ 'КОРОТКОГО ВИХОДУ'")
        st.markdown("### Загальний статус: **НЕПРИДАТНИЙ**")
        if is_base_early_exit: st.info("**Базова причина:** Знайдено кваліфікатор .3 (Важке порушення).")
        if is_tdv_early_exit: st.warning(f"**ТДВ причина:** {tdv_fail} (Таблиця Додаткових Вимог).")
            
    else:
        try:
            score, status, M, S_rest, alpha = calculate_mcda_score(pd["icf_scores"])
            
            if status == "Придатний": 
                st.success(f"⚖️ СТАТУС: **{status.upper()}** (Бал: {score})")
            elif status == "Непридатний":
                st.error(f"⚖️ СТАТУС: **{status.upper()}** (Бал: {score})")
            else: 
                st.warning(f"⚖️ СТАТУС: **{status.upper()}** (Бал: {score})")
                
            st.success(f"🎯 СТАТУС ТДВ: **Придатний до служби на посаді '{pd['prof']}'**")

            st.markdown("---")
            st.subheader("Розшифровка 'Сірої Зони' (MCDA)")
            c1, c2, c3 = st.columns(3)
            c1.metric("Домінуючий тягар (M)", M)
            c2.metric("Фоновий тягар (S_rest)", S_rest)
            c3.metric("Запас міцності (α)", f"{int(alpha*100)}%")
            st.code(f"M + (S_rest * α)  =>  {M} + ({S_rest} * {alpha}) = {score} балів")
        except Exception as e:
            st.error(f"Помилка розрахунку: {e}")
        
    st.markdown("---")
    if st.button("🔄 Почати новий кейс", key="btn_reset"): 
        reset_all(); st.rerun()
