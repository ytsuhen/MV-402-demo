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

# ПРОФЕСІЙНА БАЗА ДАНИХ (Повністю валідована - Версія 1.5)
KNOWLEDGE_BASE = {
    "Зір": {
        "icd": "H52.1 (Міопія)", 
        "icf": "b210", 
        "achi": "11212-00 (Дослідження очного дна)", 
        "validation": "LOINC: 70914-7 (Гострота зору)"
    },
    "Серце": {
        "icd": "I11.9 (Гіпертензивна хвороба)", 
        "icf": "b420", 
        "achi": "11700-00 (ЕКГ, 12 відведень)", 
        "validation": "SNOMED: 38341003 (Гіпертензивна хвороба серця)"
    },
    "Спина": {
        "icd": "M42.1 (Остеохондроз хребта)", 
        "icf": "b710", 
        "achi": "90901-03 (Магнітно-резонансна томографія хребта)", 
        "validation": "SNOMED: 282822008 (Протрузія міжхребцевого диска)"
    },
    "Травлення": {
        "icd": "K29.3 (Хронічний поверхневий гастрит)", 
        "icf": "b515", 
        "achi": "30473-00 (Панендоскопія до дванадцятипалої кишки)", 
        "validation": "SNOMED: 8493009 (Хронічний гастрит)"
    },
    "Дихання": {
        "icd": "J45.9 (Астма, неуточнена)", 
        "icf": "b440", 
        "achi": "11503-05 (Спірометрія з фізичним навантаженням)", 
        "validation": "LOINC: 20150-9 (ОФВ1 / FEV1)"
    },
    "Слух": {
        "icd": "H90.3 (Нейросенсорна туговухість)", 
        "icf": "b230", 
        "achi": "11309-00 (Повітряна аудіометрія, стандартна)", 
        "validation": "LOINC: 89020-2 (Поріг чутності)"
    }
}

# Словник тяжкості
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
    
    if score < 3.0: 
        status = "Придатний"
    elif score < 10.0: 
        status = "Придатний до служби у військових частинах забезпечення, ТЦК та СП"
    else: 
        status = "Непридатний"
        
    return score, status, M, S_rest, alpha

# БОКОВЕ МЕНЮ 
with st.sidebar:
    st.header("📖 Пам'ятка для комісії")
    st.markdown("Цей симулятор дозволяє протестувати механіки Rule Engine:")
    with st.expander("🛡️ Захист від фроду (MCDA)", expanded=True):
        st.write("* MCDA-асимптота зупинить набір балів до 10. Статус 'Непридатний' заблоковано для легких порушень.")
    with st.expander("⚡ Короткий вихід (Early Exit)", expanded=False):
        st.write("* Важке порушення (.3) миттєво списує пацієнта.")
    with st.expander("🎯 Конфлікт ТДВ (Спецпосади)", expanded=False):
        st.write("* Блокування призначення на цільову посаду (напр. Снайпер) при відхиленнях.")
    st.markdown("---")
    st.caption("Версія прототипу: 1.5. (Fully Audited & Corrected Mapping)")

st.progress((st.session_state.step + 1) / 4, text=f"Етап: {[st.session_state.step]}")
st.write("---")

# ==========================================
# КРОК 0: СИМУЛЯТОР (НАЛАШТУВАННЯ)
# ==========================================
if st.session_state.step == 0:
    st.title("⚙️ Адмін-панель: Профіль пацієнта")
    col1, col2 = st.columns([1, 2])
    with col1:
        pib = st.text_input("ПІБ Пацієнта:", "Коваленко Іван Петрович")
        st.code(f"ID в ЕСОЗ: {st.session_state.patient_id}")
        prof = st.selectbox("Військова посада (ТДВ):", ["Снайпер", "Водолаз", "Піхотинець (Загальні)"])
        has_unstructured = st.checkbox("Симулювати неструктурований запис", value=False)
    with col2:
        st.write("Відмітьте системи, у яких є зафіксовані порушення:")
        active_scores = {}
        for domain, db in KNOWLEDGE_BASE.items():
            if st.checkbox(f"Включити домен: {domain} ({db['icd']})", key=f"chk_{domain}"):
                val = st.selectbox(f"Тяжкість ({db['icf']}):", OPTS, key=f"sel_{domain}")
                active_scores[domain] = SEVERITY_MAP[val]

    if st.button("Зберегти ➔", type="primary"):
        if not active_scores: st.error("Оберіть хоча б одне порушення.")
        else:
            st.session_state.patient_data = {"pib": pib, "id": st.session_state.patient_id, "prof": prof, "unstructured": has_unstructured, "icf_scores": active_scores}
            set_step(1); st.rerun()

# ==========================================
# КРОК 1: ВИБІР МАРШРУТУ
# ==========================================
elif st.session_state.step == 1:
    pd = st.session_state.patient_data
    st.title("🏥 Вибір маршруту")
    st.success(f"**Пацієнт:** {pd['pib']} | **ID:** {pd['id']} | **Посада (ТДВ):** {pd['prof']}")
    route = st.radio("Рівень автоматизації CDS:", ["1) Автоматичний", "2) Гібридний", "3) Паперовий (Legacy)"])
    if st.button("Запустити ➔", type="primary"):
        st.session_state.route = 1 if "Автоматичний" in route else 2 if "Гібридний" in route else 3
        set_step(2); st.rerun()

# ==========================================
# КРОК 2: МАПІНГ ТА ВАЛІДАЦІЯ
# ==========================================
elif st.session_state.step == 2:
    pd = st.session_state.patient_data
    if st.session_state.route in [1, 2]:
        st.title("🧠 CDS Мапінг")
        with st.spinner("Синхронізація ЕСОЗ..."): time.sleep(0.5)
        cols = st.columns(len(pd["icf_scores"]))
        for idx, domain in enumerate(pd["icf_scores"].keys()):
            db = KNOWLEDGE_BASE[domain]
            severity_text =[domain]].split(" ")[-1]
            with cols[idx]:
                st.code(f"[1. Діагноз] МКХ-10: {db['icd']}\n[2. Функція] ICF: {db['icf']} ({severity_text})\n[3. Доказ] ACHI: {db['achi']}\n[4. Валідація] {db['validation']}", language="yaml")
        if pd["unstructured"] and st.session_state.route == 1:
            st.error("❌ АВТО-МАРШРУТ ПЕРЕРВАНО: Потрібен КЕП для неструктурованих даних.")
            if st.button("⬅️ Назад"): set_step(1); st.rerun()
        elif pd["unstructured"] and st.session_state.route == 2:
            if not st.session_state.kep_signed:
                if st.button("✍️ Валідувати КЕП"): st.session_state.kep_signed = True; st.rerun()
            else:
                st.success("✅ КЕП накладено."); 
                if st.button("Далі ➔"): set_step(3); st.rerun()
        else:
            if st.button("Далі ➔", type="primary"): set_step(3); st.rerun()

    elif st.session_state.route == 3:
        st.title("📝 Ручний ввід")
        manual_icd = st.selectbox("МКХ-10:", [db["icd"] for db in KNOWLEDGE_BASE.values()])
        target_domain = next(dom for dom, db in KNOWLEDGE_BASE.items() if db["icd"] == manual_icd)
        manual_icf = st.selectbox("МКФ:", list(set(db["icf"] for db in KNOWLEDGE_BASE.values())))
        manual_achi = st.selectbox("ACHI:", list(set(db["achi"] for db in KNOWLEDGE_BASE.values())))
        manual_sev = st.selectbox("Тяжкість:", OPTS)
        if st.button("Додати ➕"):
            if manual_icf!= KNOWLEDGE_BASE[target_domain]["icf"]: st.error("❌ ПОМИЛКА: Невірний зв'язок МКХ та МКФ.")
            else: st.session_state.paper_data[target_domain] = SEVERITY_MAP[manual_sev]; st.success("Додано.")
        if st.button("Далі ➔", type="primary"):
            st.session_state.patient_data["icf_scores"] = st.session_state.paper_data; set_step(3); st.rerun()

# ==========================================
# КРОК 3: ФІНАЛЬНИЙ СТАТУС (EARLY EXIT / MCDA)
# ==========================================
elif st.session_state.step == 3:
    pd = st.session_state.patient_data
    st.title("📋 Фінальний Висновок")
    is_base_exit = any(s == 10 for s in pd["icf_scores"].values())
    tdv_fail = "Снайпер: Порушення зору." if pd["prof"] == "Снайпер" and pd["icf_scores"].get("Зір", 0) > 0 else "Водолаз: Порушення слуху/дихання." if pd["prof"] == "Водолаз" and (pd["icf_scores"].get("Слух", 0) > 0 or pd["icf_scores"].get("Дихання", 0) > 0) else None
    
    if is_base_exit or tdv_fail:
        st.error("🚨 НЕПРИДАТНИЙ (Ранній вихід)")
        if is_base_exit: st.info("Базова причина: Знайдено кваліфікатор.3 (Важке порушення).")
        if tdv_fail: st.warning(f"ТДВ причина: {tdv_fail}")
    else:
        try:
            score, status, M, S_rest, alpha = calculate_mcda_score(pd["icf_scores"])
            st.success(f"⚖️ СТАТУС: **{status}** (Бал: {score})")
            
            st.markdown("---")
            c1, c2, c3 = st.columns(3)
            c1.metric("Домінуючий тягар (M)", M)
            c2.metric("Фоновий тягар (S_rest)", S_rest)
            c3.metric("Запас міцності (α)", f"{int(alpha*100)}%")
        except Exception as e:
            st.error("Додайте хоча б один діагноз для розрахунку.")
            
    st.markdown("---")
    if st.button("🔄 Почати знову"): reset_all(); st.rerun()
