import streamlit as st

# Налаштування сторінки
st.set_page_config(page_title="CDS Rule Engine | Pitch Deck", layout="wide", page_icon="🛡️")

# ==========================================
# МАТЕМАТИЧНЕ ЯДРО (Приховано від очей в коді)
# ==========================================
def calculate_mcda_score(patient_data):
    THRESHOLD = 10
    domain_max_scores = {}
    for domain, scores in patient_data.items():
        valid_scores = [s for s in scores if s > 0]
        domain_max_scores[domain] = max(valid_scores) if valid_scores else 0
            
    active_maxes = [v for v in domain_max_scores.values() if v > 0]
    
    if not active_maxes:
        return 0.0, "Придатний", domain_max_scores, 0, 0, 0.0
        
    M = max(active_maxes)
    S_rest = sum(active_maxes) - M
    alpha = (THRESHOLD - M) / THRESHOLD
    final_score = round(M + (S_rest * alpha), 2)
    
    if final_score < 3.0: status = "Придатний"
    elif final_score < 10.0: status = "Обмежено придатний"
    else: status = "Непридатний"
        
    return final_score, status, domain_max_scores, M, S_rest, alpha

# ==========================================
# БОКОВЕ МЕНЮ (НАВІГАЦІЯ)
# ==========================================
st.sidebar.title("🛡️ ВЛК CDS Engine")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Розділи презентації:",
    ("1. Executive Summary", "2. Клінічна Архітектура", "3. Інтерактивний Прототип", "4. Масштабування (Roadmap)")
)
st.sidebar.markdown("---")
st.sidebar.caption("Розроблено для захисту архітектурного рішення.")

# ==========================================
# РОЗДІЛ 1: ВСТУП
# ==========================================
if menu == "1. Executive Summary":
    st.title("💡 Трансформація ВЛК через Clinical Decision Support")
    st.markdown("""
    ### Проблема
    Поточна система ВЛК (Наказ №402) страждає від двох крайнощів:
    - **Гіпердіагностика (Фрод):** Штучне накопичення дрібних діагнозів для отримання статусу "Непридатний".
    - **Перевантаження лікарів:** Робота з 1400+ кодами МКФ без автоматизованої маршрутизації.

    ### Рішення: Rule Engine з Explainable AI
    Спроєктована архітектура перетворює медичний висновок з суб'єктивного процесу на математично детермінований конвеєр.
    """)
    
    st.info("👈 Використовуйте бокове меню для навігації по розділах презентації.")

# ==========================================
# РОЗДІЛ 2: АРХІТЕКТУРА
# ==========================================
elif menu == "2. Клінічна Архітектура":
    st.title("🏗️ Дворівневий міст інтеграції даних")
    
    tab1, tab2 = st.tabs(["Крок 1: Смарт-чеклісти (WHO ICF)", "Крок 2: Антифрод Валідація (НСЗУ)"])
    
    with tab1:
        st.subheader("Звуження вибору через ICF Core Sets")
        st.write("Замість ручного пошуку по всьому довіднику МКФ, система автоматично перетворює діагноз з ЕСОЗ (МКХ-10) на вузький чек-лист релевантних функцій.")
        st.code("Приклад: I11.9 (Гіпертонія) ➔ Генерує чек-лист [b420, b410, b430]", language="json")
        
    with tab2:
        st.subheader("Доказова медицина на базі Програми Медичних Гарантій")
        st.write("Система блокує встановлення важких порушень без наявності об'єктивних обстежень (кодів ACHI), визначених протоколами МОЗ.")
        st.code("""
        "Target_ICF": "b420.2 (Помірне порушення АТ)",
        "Required_Evidence": ["11700-00 (ЕКГ)", "55113-00 (ЕхоКГ)"],
        "Action_If_Failed": "BLOCK_SUBMISSION"
        """, language="json")

# ==========================================
# РОЗДІЛ 3: ПРОТОТИП (КАЛЬКУЛЯТОР)
# ==========================================
elif menu == "3. Інтерактивний Прототип":
    st.title("⚙️ MCDA Rule Engine (Proof of Concept)")
    st.markdown("Захист від парадоксу лінійної адитивності через **Асимптоту AMA** та **внутрішньодоменне поглинання**.")
    
    severity_map = {"Норма <5% (0)": 0, "Легке .1 (1)": 1, "Помірне .2 (3)": 3, "Важке .3 (10)": 10}

    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.markdown("**👁️ Зір (b2)**")
        v1 = st.selectbox("Міопія (b210)", list(severity_map.keys()), key="v1")
        v2 = st.selectbox("Катаракта (b215)", list(severity_map.keys()), key="v2")
    with col2:
        st.markdown("**🫀 Серце (b4)**")
        h1 = st.selectbox("Гіпертонія (b420)", list(severity_map.keys()), key="h1")
        h2 = st.selectbox("ІХС (b410)", list(severity_map.keys()), key="h2")
    with col3:
        st.markdown("**🦴 Спина (b7)**")
        m1 = st.selectbox("Остеохондроз (b710)", list(severity_map.keys()), key="m1")
        m2 = st.selectbox("Грижа (b715)", list(severity_map.keys()), key="m2")
    with col4:
        st.markdown("**🍏 Шлунок (b5)**")
        g1 = st.selectbox("Гастрит (b515)", list(severity_map.keys()), key="g1")
        g2 = st.selectbox("Виразка (b525)", list(severity_map.keys()), key="g2")

    if st.button("🚀 Згенерувати висновок ВЛК", type="primary", use_container_width=True):
        patient_data = {
            'b2': [severity_map[v1], severity_map[v2]],
            'b4': [severity_map[h1], severity_map[h2]],
            'b7': [severity_map[m1], severity_map[m2]],
            'b5': [severity_map[g1], severity_map[g2]]
        }
        score, status, domain_maxes, M, S_rest, alpha = calculate_mcda_score(patient_data)
        
        st.header(f"⚖️ СТАТУС: {status} (Бал: {score} / 10.0)")
        
        with st.expander("Розгорнути математичний аудит (Explainable AI)", expanded=True):
            st.markdown("### 1. Фільтрація дублікатів (MAX)")
            st.write(f"Чисті вектори по системах: {domain_maxes}")
            st.markdown("### 2. Динамічний запас міцності (AMA)")
            st.write(f"Головна хвороба (M): **{M}** | Супутні (S_rest): **{S_rest}** | Запас: **{alpha}**")
            st.info(f"Формула: {M} + ({S_rest} × {alpha}) = {score}")

# ==========================================
# РОЗДІЛ 4: ROADMAP
# ==========================================
elif menu == "4. Масштабування (Roadmap)":
    st.title("🚀 Шлях до національного розгортання")
    st.markdown("""
    ### Генерація Knowledge Graph через LLM
    Ручний мапінг 800 сторінок Наказу №402 є неефективним. 
    Стратегія передбачає використання моделей з великим контекстом (Gemini 1.5 Pro) для парсингу:
    1. Наказу МОУ №402
    2. Специфікацій ПМГ НСЗУ
    3. Уніфіковані клінічні протоколи (УКПМД)
    
    **Результат:** Автоматична генерація JSON-правил антифроду з подальшою валідацією лікарями (Human-in-the-loop).
    """)