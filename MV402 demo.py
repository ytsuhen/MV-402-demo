import streamlit as st
import uuid
import time

# Налаштування сторінки
st.set_page_config(page_title="ВЛК 2026: CDS Симулятор", layout="wide", page_icon="🏥")

# ==========================================
# УПРАВЛІННЯ СТАНОМ (SESSION STATE)
# ==========================================
if 'step' not in st.session_state:
    st.session_state.step = 0 # 0: Налаштування, 1: Вибір маршруту, 2: Мапінг, 3: Висновок
if 'patient_id' not in st.session_state:
    st.session_state.patient_id = str(uuid.uuid4())[:8].upper()
if 'patient_data' not in st.session_state:
    st.session_state.patient_data = {}
if 'kep_signed' not in st.session_state:
    st.session_state.kep_signed = False

def set_step(step): st.session_state.step = step
def reset():
    st.session_state.step = 0
    st.session_state.patient_id = str(uuid.uuid4())[:8].upper()
    st.session_state.kep_signed = False

# Математичне ядро MCDA
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
    st.title("⚙️ Адмін-панель: Створення профілю пацієнта")
    st.info("Цей крок прихований від лікаря ВЛК. Тут ми як розробники 'сетапимо' сценарій для демонстрації.")
    
    col1, col2 = st.columns(2)
    with col1:
        pib = st.text_input("ПІБ Пацієнта:", "Коваленко Іван Петрович")
        prof = st.selectbox("Військова посада:", ["Снайпер", "Кухар", "N/A (Без специфіки)"])
        has_unstructured = st.checkbox("Додати неструктурований запис (Скан МРТ з приватної клініки)", value=True)
        
    with col2:
        st.write("**Налаштування обстежень (Симуляція ЕСОЗ):**")
        
        # Домен: Зір (Впливає на снайпера)
        vision_exam = st.selectbox("Гострота зору (Міопія H52.1):", [
            "1.0 (Норма) -> 0 балів", 
            "0.6 (Легке порушення) -> 1 бал", 
            "0.2 (Помірне порушення) -> 3 бали",
            "Сліпота (Важке порушення) -> 10 балів (Early Exit)"
        ], index=1)
        
        # Домен: Серце
        heart_exam = st.selectbox("Артеріальний тиск (Гіпертонія I11.9):", [
            "Відсутній -> 0 балів",
            "АТ 140/90 (Легке) -> 1 бал",
            "АТ 160/100 (Помірне) -> 3 бали",
            "АТ 180/110+ (Важке) -> 10 балів (Early Exit)"
        ], index=2)

    if st.button("Зберегти та Перейти в Кабінет ВЛК ➔", type="primary"):
        # Парсимо бали з обраних рядків
        st.session_state.patient_data = {
            "pib": pib,
            "id": st.session_state.patient_id,
            "prof": prof,
            "unstructured": has_unstructured,
            "icf_scores": {
                "Зір (b210)": int(vision_exam.split("-> ")[1].split(" ")[0]),
                "Серце (b420)": int(heart_exam.split("-> ")[1].split(" ")[0])
            }
        }
        set_step(1)
        st.rerun()

# ==========================================
# КРОК 1: КАБІНЕТ ЛІКАРЯ (ВИБІР МАРШРУТУ)
# ==========================================
elif st.session_state.step == 1:
    pd = st.session_state.patient_data
    st.title("🏥 Кабінет ВЛК 2026-402")
    
    # Картка пацієнта
    st.success(f"**Пацієнт:** {pd['pib']} | **ID:** {pd['id']} | **Цільова посада:** {pd['prof']}")
    
    st.header("Вибір маршруту Clinical Decision Support (CDS)")
    route = st.radio("Оберіть стадію зрілості системи:", [
        "1) Повністю автоматичний маршрут (CDS 100%, авто-мапінг)",
        "2) Гібридний маршрут (Потребує ручної валідації КЕП для неструктурованих даних)"
    ])
    
    if st.button("Далі ➔", type="primary"):
        st.session_state.route = 1 if "автоматичний" in route else 2
        set_step(2)
        st.rerun()

# ==========================================
# КРОК 2: МАПІНГ ТА ВАЛІДАЦІЯ
# ==========================================
elif st.session_state.step == 2:
    pd = st.session_state.patient_data
    st.title("🧠 Архітектура Мапінгу (Граф Знань CDS)")
    st.write("Система автоматично розгортає дерево кодів з ЕСОЗ для валідації Наказу №402.")
    
    with st.spinner("Зв'язок з ЕСОЗ... Завантаження пакетів НСЗУ..."):
        time.sleep(1)
        
    # Візуалізація Мапінгу
    col1, col2 = st.columns(2)
    with col1:
        st.markdown("### Дерево Діагнозів (ICF Core Sets)")
        st.code("""
[ЕСОЗ]: I11.9 (Гіпертонічна хвороба)
  └── ICF Core Set Triggered
       └── МКФ: b420 (Функції артеріального тиску)
            └── Значення: Валідація...

[ЕСОЗ]: H52.1 (Міопія)
  └── ICF Core Set Triggered
       └── МКФ: b210 (Гострота зору)
            └── Значення: Валідація...
        """, language="yaml")

    with col2:
        st.markdown("### Антифрод Мапінг (НСЗУ ➔ Наказ 402)")
        st.code("""
[Матриця Валідації]:
IF b420 > 0:
  EXPECT ACHI: 11700-00 (ЕКГ)
  CHECK LOINC: 8480-6 (Сист. АТ) 

IF b210 > 0:
  EXPECT ACHI: 11200-00 (Офтальмоскопія)
  CHECK LOINC: Оптична сила
        """, language="yaml")

    st.markdown("---")
    
    # Логіка маршрутів
    if pd["unstructured"]:
        if st.session_state.route == 1:
            st.error("❌ АВТОМАТИЧНИЙ МАРШРУТ ПЕРЕРВАНО: Знайдено неструктурований запис (PDF Скан МРТ). Система не може самостійно встановити рівень довіри до приватних клінік без КЕП лікаря ВЛК. Будь ласка, оберіть Гібридний маршрут.")
            if st.button("⬅️ Повернутися до вибору маршруту"):
                set_step(1); st.rerun()
                
        elif st.session_state.route == 2:
            st.warning("⚠️ ГІБРИДНИЙ РЕЖИМ: Виявлено неструктурований PDF-документ (МРТ хребта, клініка 'Борис'). Алгоритм NLP (SNOMED) пропонує код: 266249003 (Протрузія).")
            if not st.session_state.kep_signed:
                if st.button("✍️ Підтвердити та підписати КЕП лікаря ВЛК"):
                    st.session_state.kep_signed = True
                    st.rerun()
            else:
                st.success("✅ КЕП накладено. Дані легалізовано для Rule Engine.")
                pd["icf_scores"]["Спина (b710)"] = 1 # Додаємо легке порушення після підпису
                if st.button("Перейти до розрахунку статусів (Наказ 402) ➔", type="primary"):
                    set_step(3); st.rerun()
    else:
        st.success("✅ Всі дані структуровані. Антифрод валідацію ПМГ пройдено автоматично.")
        if st.button("Перейти до розрахунку статусів (Наказ 402) ➔", type="primary"):
            set_step(3); st.rerun()

# ==========================================
# КРОК 3: ФІНАЛЬНИЙ СТАТУС (EARLY EXIT / MCDA)
# ==========================================
elif st.session_state.step == 3:
    pd = st.session_state.patient_data
    st.title("📋 Фінальний Висновок ВЛК")
    
    # Шукаємо Важкі порушення (10 балів) для Early Exit
    is_early_exit = any(score == 10 for score in pd["icf_scores"].values())
    
    # Перевірка додаткових вимог (Снайпер)
    sniper_fail = (pd["prof"] == "Снайпер") and (pd["icf_scores"].get("Зір (b210)", 0) > 0)

    # ВІЗУАЛІЗАЦІЯ EARLY EXIT
    if is_early_exit:
        st.error("🚨 СПРАЦЮВАВ EARLY EXIT (КОРОТКИЙ ВИХІД)")
        st.markdown("### Загальний статус: **НЕПРИДАТНИЙ ДО ВІЙСЬКОВОЇ СЛУЖБИ**")
        st.info("Система виявила кваліфікатор тяжкості .3 (Важке порушення). Згідно з прямим мапінгом Наказу №402, застосовано імперативну статтю. Обчислення за гібридною моделлю (MCDA) зупинено.")
    
    # ВІЗУАЛІЗАЦІЯ MCDA (Якщо немає Early Exit)
    else:
        score, status, M, S_rest, alpha = calculate_mcda_score(pd["icf_scores"])
        
        # Відображення основного статусу
        if status == "Придатний":
            st.success(f"⚖️ ЗАГАЛЬНИЙ СТАТУС: **{status.upper()}** (Бал: {score})")
        else:
            st.warning(f"⚖️ ЗАГАЛЬНИЙ СТАТУС: **{status.upper()}** (Бал: {score})")
            
        # Блок додаткових вимог (Снайпер конфлікт)
        if sniper_fail:
            st.error("🎯 СТАТУС ЗА ПОСАДОЮ: **Непридатний до служби на посаді 'Снайпер'**")
            st.write("*(Обґрунтування: Виявлено порушення зору b210. Навіть легке порушення порушує Таблицю 'В' додаткових вимог Наказу 402 для даної спеціальності).*")
        elif pd["prof"] != "N/A (Без специфіки)":
            st.success(f"🎯 СТАТУС ЗА ПОСАДОЮ: **Придатний до служби на посаді '{pd['prof']}'**")

        # Розшифровка MCDA
        st.markdown("---")
        st.subheader("Розшифровка гібридної моделі (Explainable AI)")
        st.write("Оскільки прямих підстав для повного списання (Early Exit) не знайдено, статус розраховано за алгоритмом динамічного запасу міцності.")
        
        col_m1, col_m2, col_m3 = st.columns(3)
        col_m1.metric("Базовий тягар (M)", M, "Найважча хвороба")
        col_m2.metric("Фоновий тягар (S_rest)", S_rest, "Сума супутніх")
        col_m3.metric("Запас міцності (α)", alpha, f"(10 - {M}) / 10")
        
        st.code(f"MCDA Score = M + (S_rest * α)  =>  {M} + ({S_rest} * {alpha}) = {score}", language="python")
        
    st.markdown("---")
    if st.button("🔄 Почати новий кейс"):
        reset(); st.rerun()
