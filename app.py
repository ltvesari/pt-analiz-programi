import streamlit as st
from fpdf import FPDF
import base64

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="PT Pro: Analiz Paneli", layout="wide")

# --- KAS VE ANALİZ MANTIĞI (VERİTABANI) ---
LOGIC_DB = {
    # 1. STATİK POSTÜR
    "Static": {
        "Ayaklar: Dışa Dönük": {"view": "Anterior", "over": ["Soleus", "Lat. Gastrocnemius", "Biceps Femoris (Short)"], "under": ["Med. Gastrocnemius", "Med. Hamstring"]},
        "Dizler: İçe Dönük (Valgus)": {"view": "Anterior", "over": ["Adductor Complex", "TFL", "Vastus Lat."], "under": ["Gluteus Med/Max", "VMO"]},
        "Bel Çukuru Artmış (Lordoz)": {"view": "Lateral", "over": ["Hip Flexors", "Erector Spinae"], "under": ["Gluteus Max", "Hamstrings", "Core"]},
        "Bel Düzleşmiş (Kifoz)": {"view": "Lateral", "over": ["Hamstrings", "Rectus Abd."], "under": ["Erector Spinae", "Gluteus Max"]},
        "Omuzlar: Öne Yuvarlanmış": {"view": "Lateral", "over": ["Pectorals", "Latissimus Dorsi"], "under": ["Mid/Lower Trapezius", "Rhomboids"]},
        "Baş: Öne Doğru": {"view": "Lateral", "over": ["Upper Trapezius", "Levator Scapulae"], "under": ["Deep Cervical Flexors"]},
        "Ayaklar: İçe Basma (Düz Taban)": {"view": "Posterior", "over": ["Peroneals", "Lat. Gastrocnemius"], "under": ["Ant/Post Tibialis", "Gluteus Medius"]},
        "LPHC: Asimetrik Kalça": {"view": "Posterior", "over": ["Quadratus Lumborum", "TFL"], "under": ["Gluteus Medius"]}
    },
    # 2. OVERHEAD SQUAT
    "OHSquat": {
        "Ayaklar: Dışa Dönüyor": {"view": "Anterior", "over": ["Soleus", "Lat. Gastrocnemius", "Biceps Femoris", "TFL"], "under": ["Med. Gastrocnemius", "Med. Hamstring"]},
        "Ayaklar: Düzleşiyor": {"view": "Anterior", "over": ["Peroneals", "Biceps Femoris"], "under": ["Ant. Tibialis", "Post. Tibialis"]},
        "Dizler: İçe Çöküyor": {"view": "Anterior", "over": ["Adductor Complex", "TFL"], "under": ["Gluteus Med/Max", "VMO"]},
        "LPHC: Aşırı Öne Eğilme": {"view": "Lateral", "over": ["Soleus", "Hip Flexors"], "under": ["Ant. Tibialis", "Gluteus Max"]},
        "LPHC: Bel Çukuru Artıyor": {"view": "Lateral", "over": ["Hip Flexors", "Erector Spinae"], "under": ["Gluteus Max", "Core"]},
        "Omuzlar: Kollar Öne Düşüyor": {"view": "Lateral", "over": ["Lats", "Pectorals"], "under": ["Mid/Lower Trap.", "Rotator Cuff"]},
        "LPHC: Asimetrik Kayma": {"view": "Posterior", "over": ["Adductor Complex"], "under": ["Gluteus Medius"]}
    },
    # 3. PUSH-UP
    "Pushup": {
        "Belin Çökmesi": {"over": ["Erector Spinae", "Hip Flexors"], "under": ["Core", "Gluteus Max"]},
        "Belin Yuvarlaklaşması": {"over": ["Rectus Abd."], "under": ["Core"]},
        "Omuzların Kalkması": {"over": ["Upper Trap.", "Levator Scap."], "under": ["Mid/Lower Trap."]},
        "Kanatlaşma": {"over": ["Pectoralis Minor"], "under": ["Serratus Ant.", "Mid/Lower Trap."]},
        "Başın Geri Gitmesi": {"over": ["Upper Trap."], "under": ["Deep Cervical Flexors"]}
    },
    # 4. ROW
    "Row": {
        "LPHC: Bel Çukuru Artıyor": {"over": ["Hip Flexors"], "under": ["Core"]},
        "Omuzlar: Yukarı Kalkıyor": {"over": ["Upper Trap."], "under": ["Mid/Lower Trap."]},
        "Baş: Öne Gidiyor": {"over": ["Upper Trap."], "under": ["Deep Cervical Flexors"]}
    },
    # 5. OH PRESS
    "OHPress": {
        "LPHC: Bel Çukuru Artıyor": {"over": ["Hip Flexors"], "under": ["Core"]},
        "Omuzlar: Yukarı Kalkıyor": {"over": ["Upper Trap."], "under": ["Mid/Lower Trap."]},
        "Omuzlar: Kollar Öne Gidiyor": {"over": ["Lats"], "under": ["Rotator Cuff"]},
        "Omuzlar: Dirsekler Bükülüyor": {"over": ["Lats", "Pectorals"], "under": ["Rotator Cuff"]},
        "Baş: Öne Gidiyor": {"over": ["Upper Trap."], "under": ["Deep Cervical Flexors"]}
    }
}

# --- YARDIMCI FONKSİYONLAR ---
def clean_text(text):
    tr_map = str.maketrans("ğĞıİöÖüÜşŞçÇ", "gGiIoOuUsScC")
    return str(text).translate(tr_map)

def calculate_ymca_score(gender, age, pulse):
    if pulse < 85: return "Harika"
    elif pulse < 105: return "Iyi / Ortalama Ustu"
    elif pulse < 125: return "Ortalama"
    else: return "Gelistirilmeli"

# --- SESSION STATE (HAFIZA) ---
# Sayfalar arası geçişi yönetmek için 'current_page' kullanıyoruz
if 'current_page' not in st.session_state: st.session_state['current_page'] = "home"
if 'student_data' not in st.session_state: st.session_state['student_data'] = {"name": "", "date": None, "age": 25, "gender": "Erkek"}
for key in ['static_results', 'ohsquat_results', 'pushup_results', 'row_results', 'ohpress_results']:
    if key not in st.session_state: st.session_state[key] = []
if 'cardio_result' not in st.session_state: st.session_state['cardio_result'] = None

# --- NAVİGASYON FONKSİYONLARI ---
def go_to(page):
    st.session_state['current_page'] = page

def go_home():
    st.session_state['current_page'] = "home"

# --- PDF OLUŞTURMA ---
def create_pdf(student_info, static_res, ohsquat_res, pushup_res, row_res, ohpress_res, cardio_res, analysis):
    pdf = FPDF()
    pdf.add_page()
    pdf.set_font("Arial", 'B', 16)
    pdf.cell(0, 10, clean_text("PT Pro: Hareket ve Postur Analizi"), ln=True, align='C')
    pdf.set_font("Arial", size=10)
    info = f"Ogrenci: {student_info['name']} | Yas: {student_info['age']} | Tarih: {student_info['date']}"
    pdf.cell(0, 10, clean_text(info), ln=True, align='C')
    pdf.line(10, 25, 200, 25); pdf.ln(5)

    if cardio_res:
        pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, clean_text("1. Kardiyo (YMCA)"), ln=True)
        pdf.set_font("Arial", size=10); pdf.cell(0, 8, clean_text(f"Sonuc: {cardio_res['rating']} ({cardio_res['pulse']} bpm)"), ln=True); pdf.ln(2)

    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, clean_text("2. Gozlem Bulgulari"), ln=True)
    def print_t(title, data):
        if data:
            pdf.set_font("Arial", 'B', 10); pdf.cell(0, 6, clean_text(title), ln=True)
            pdf.set_font("Arial", size=10); [pdf.cell(0, 5, clean_text(f" - {i}"), ln=True) for i in data]
            pdf.ln(2)
    print_t("Statik Postur", static_res)
    print_t("Overhead Squat", ohsquat_res)
    print_t("Push-up", pushup_res)
    print_t("Row", row_res)
    print_t("Press", ohpress_res)
    pdf.ln(3)

    pdf.set_font("Arial", 'B', 12); pdf.cell(0, 10, clean_text("3. Egzersiz Plani"), ln=True)
    pdf.set_text_color(220, 50, 50); pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, clean_text("ESNET (Kisa Kaslar):"), ln=True)
    pdf.set_text_color(0,0,0); pdf.set_font("Arial", size=10); pdf.multi_cell(0, 6, clean_text(", ".join(sorted(list(analysis['overactive']))))); pdf.ln(2)
    pdf.set_text_color(50, 150, 50); pdf.set_font("Arial", 'B', 10); pdf.cell(0, 8, clean_text("GUCLENDIR (Uzun Kaslar):"), ln=True)
    pdf.set_text_color(0,0,0); pdf.set_font("Arial", size=10); pdf.multi_cell(0, 6, clean_text(", ".join(sorted(list(analysis['underactive'])))))
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# =========================================================
# === ANA UYGULAMA AKIŞI ===
# =========================================================

# --- 1. ANA MENÜ (DASHBOARD) ---
if st.session_state['current_page'] == "home":
    st.title("🏋️‍♂️ PT Pro: Analiz Paneli")
    
    # Öğrenci Bilgileri (Her zaman en üstte)
    with st.expander("📝 Öğrenci Bilgileri (Düzenlemek için tıkla)", expanded=True):
        c1, c2, c3 = st.columns(3)
        name = c1.text_input("Ad Soyad", value=st.session_state['student_data']['name'])
        age = c2.number_input("Yaş", 18, 99, st.session_state['student_data']['age'])
        gender = c3.selectbox("Cinsiyet", ["Erkek", "Kadın"], 0 if st.session_state['student_data']['gender']=="Erkek" else 1)
        date = st.date_input("Tarih", value=st.session_state['student_data']['date'])
        
        # Otomatik kaydetme (State güncelleme)
        st.session_state['student_data'].update({"name": name, "age": age, "gender": gender, "date": date})

    st.markdown("---")
    st.subheader("Test Menüsü")

    # GRID YAPISI (Çizdiğin Resimdeki Gibi)
    # Satır 1
    col1, col2 = st.columns(2)
    with col1:
        if st.button("🧍 STATİK POSTÜR ANALİZİ", use_container_width=True, type="primary"):
            go_to("static")
    with col2:
        if st.button("🏋️ OVERHEAD SQUAT ANALİZİ", use_container_width=True, type="primary"):
            go_to("ohsquat")
            
    # Satır 2
    col3, col4 = st.columns(2)
    with col3:
        if st.button("💪 PUSH-UP ANALİZİ", use_container_width=True):
            go_to("pushup")
    with col4:
        if st.button("🚣 STANDING ROW ANALİZİ", use_container_width=True):
            go_to("row")
            
    # Satır 3
    col5, col6 = st.columns(2)
    with col5:
        if st.button("🙌 OVERHEAD PRESS ANALİZİ", use_container_width=True):
            go_to("ohpress")
    with col6:
        if st.button("🫀 3MIN YMCA TESTİ", use_container_width=True):
            go_to("cardio")

    # Satır 4 (Büyük Sonuç Butonu)
    st.markdown("###")
    if st.button("📊 SONUÇ VE RAPOR OLUŞTUR", use_container_width=True, type="secondary"):
        go_to("report")


# --- 2. ALT SAYFALAR (TEST EKRANLARI) ---

elif st.session_state['current_page'] == "static":
    st.button("⬅️ Ana Menüye Dön", on_click=go_home)
    st.header("Statik Postür Analizi")
    t1, t2, t3 = st.tabs(["Anterior", "Lateral", "Posterior"])
    
    temp = st.session_state['static_results'].copy()
    def check_static(view, con):
        items = [k for k,v in LOGIC_DB["Static"].items() if v["view"]==view]
        c = con.columns(2)
        for i, item in enumerate(items):
            if c[i%2].checkbox(item, value=(item in temp), key=item):
                if item not in temp: temp.append(item)
            elif item in temp: temp.remove(item)
    check_static("Anterior", t1); check_static("Lateral", t2); check_static("Posterior", t3)
    st.session_state['static_results'] = temp

elif st.session_state['current_page'] == "ohsquat":
    st.button("⬅️ Ana Menüye Dön", on_click=go_home)
    st.header("Overhead Squat Analizi")
    t1, t2, t3 = st.tabs(["Anterior", "Lateral", "Posterior"])
    temp = st.session_state['ohsquat_results'].copy()
    def check_ohs(view, con):
        items = [k for k,v in LOGIC_DB["OHSquat"].items() if v["view"]==view]
        c = con.columns(2)
        for i, item in enumerate(items):
            if c[i%2].checkbox(item, value=(item in temp), key=f"ohs_{item}"):
                if item not in temp: temp.append(item)
            elif item in temp: temp.remove(item)
    check_ohs("Anterior", t1); check_ohs("Lateral", t2); check_ohs("Posterior", t3)
    st.session_state['ohsquat_results'] = temp

elif st.session_state['current_page'] == "pushup":
    st.button("⬅️ Ana Menüye Dön", on_click=go_home)
    st.header("Push-up Analizi")
    temp = st.session_state['pushup_results'].copy()
    c = st.columns(2)
    for i, item in enumerate(LOGIC_DB["Pushup"].keys()):
        if c[i%2].checkbox(item, value=(item in temp), key=f"p_{i}"):
            if item not in temp: temp.append(item)
        elif item in temp: temp.remove(item)
    st.session_state['pushup_results'] = temp

elif st.session_state['current_page'] == "row":
    st.button("⬅️ Ana Menüye Dön", on_click=go_home)
    st.header("Standing Row Analizi")
    temp = st.session_state['row_results'].copy()
    c = st.columns(2)
    for i, item in enumerate(LOGIC_DB["Row"].keys()):
        if c[i%2].checkbox(item, value=(item in temp), key=f"r_{i}"):
            if item not in temp: temp.append(item)
        elif item in temp: temp.remove(item)
    st.session_state['row_results'] = temp

elif st.session_state['current_page'] == "ohpress":
    st.button("⬅️ Ana Menüye Dön", on_click=go_home)
    st.header("Overhead Press Analizi")
    temp = st.session_state['ohpress_results'].copy()
    c = st.columns(2)
    for i, item in enumerate(LOGIC_DB["OHPress"].keys()):
        if c[i%2].checkbox(item, value=(item in temp), key=f"o_{i}"):
            if item not in temp: temp.append(item)
        elif item in temp: temp.remove(item)
    st.session_state['ohpress_results'] = temp

elif st.session_state['current_page'] == "cardio":
    st.button("⬅️ Ana Menüye Dön", on_click=go_home)
    st.header("3 Min YMCA Testi")
    st.info("Test sonrası 1 dakikalık nabız sayımını giriniz.")
    pulse = st.number_input("Ölçülen Nabız", 40, 220)
    if st.button("Hesapla"):
        r = calculate_ymca_score(st.session_state['student_data']['gender'], st.session_state['student_data']['age'], pulse)
        st.session_state['cardio_result'] = {"pulse": pulse, "rating": r}
        st.success(f"Sonuç: **{r}**")

elif st.session_state['current_page'] == "report":
    st.button("⬅️ Ana Menüye Dön", on_click=go_home)
    st.title("📊 Analiz Raporu")

    # Kardiyo
    if st.session_state['cardio_result']:
        res = st.session_state['cardio_result']
        st.info(f"❤️ **Kardiyo:** {res['rating']} ({res['pulse']} bpm)")
    
    # Kas Analizi
    all_over, all_under = set(), set()
    sources = [(st.session_state['static_results'], "Static"), (st.session_state['ohsquat_results'], "OHSquat"),
               (st.session_state['pushup_results'], "Pushup"), (st.session_state['row_results'], "Row"),
               (st.session_state['ohpress_results'], "OHPress")]
    for res, db in sources:
        for obs in res:
            d = LOGIC_DB[db][obs]
            all_over.update(d["over"]); all_under.update(d["under"])

    c1, c2 = st.columns(2)
    with c1: 
        st.error(f"🔥 ESNET ({len(all_over)})")
        for m in sorted(list(all_over)): st.write(f"- {m}")
    with c2: 
        st.success(f"✅ GÜÇLENDİR ({len(all_under)})")
        for m in sorted(list(all_under)): st.write(f"- {m}")
    
    st.divider()
    if st.button("📥 PDF İndir", type="primary"):
        try:
            pdf_bytes = create_pdf(st.session_state['student_data'], st.session_state['static_results'], 
                                   st.session_state['ohsquat_results'], st.session_state['pushup_results'], 
                                   st.session_state['row_results'], st.session_state['ohpress_results'], 
                                   st.session_state['cardio_result'], {"overactive": all_over, "underactive": all_under})
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="Rapor.pdf" style="background-color:#FF4B4B;color:white;padding:10px;text-decoration:none;border-radius:5px;">Dosyayı İndirmek İçin Tıkla</a>'
            st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Hata: {e}")
