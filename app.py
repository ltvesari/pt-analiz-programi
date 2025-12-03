import streamlit as st
from fpdf import FPDF
import base64

# --- SAYFA AYARLARI ---
st.set_page_config(page_title="PT Pro: Analiz Sistemi", layout="wide")

# --- VERİTABANI: ANALİZ MANTIĞI ---
LOGIC_DB = {
    # 1. STATİK POSTÜR (SADELEŞTİRİLMİŞ)
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

    # 2. OVERHEAD SQUAT (DETAYLI)
    "OHSquat": {
        "Ayaklar: Dışa Dönüyor (Turn Out)": {"view": "Anterior", "over": ["Soleus", "Lat. Gastrocnemius", "Biceps Femoris (Short)", "TFL"], "under": ["Med. Gastrocnemius", "Med. Hamstring", "Gluteus Med/Max"]},
        "Ayaklar: Düzleşiyor (Flatten)": {"view": "Anterior", "over": ["Peroneals", "Lat. Gastrocnemius", "Biceps Femoris", "TFL"], "under": ["Ant. Tibialis", "Post. Tibialis", "Med. Gastrocnemius"]},
        "Dizler: İçe Çöküyor (Valgus)": {"view": "Anterior", "over": ["Adductor Complex", "Biceps Femoris (Short)", "TFL", "Lat. Gastrocnemius"], "under": ["Med. Hamstring", "Gluteus Med/Max", "VMO"]},
        "LPHC: Aşırı Öne Eğilme": {"view": "Lateral", "over": ["Soleus", "Hip Flexors", "Abd. Complex"], "under": ["Ant. Tibialis", "Gluteus Max", "Erector Spinae"]},
        "LPHC: Bel Çukuru Artıyor": {"view": "Lateral", "over": ["Hip Flexors", "Erector Spinae", "Lats"], "under": ["Gluteus Max", "Hamstrings", "Core"]},
        "Omuzlar: Kollar Öne Düşüyor": {"view": "Lateral", "over": ["Lats", "Pectorals", "Teres Major"], "under": ["Mid/Lower Trap.", "Rhomboids", "Rotator Cuff"]},
        "LPHC: Asimetrik Kayma": {"view": "Posterior", "over": ["Adductor Complex (Shift)", "TFL"], "under": ["Gluteus Medius (Shift)"]}
    },

    # 3. PUSH-UP TESTİ
    "Pushup": {
        "Belin Çökmesi": {"over": ["Erector Spinae", "Hip Flexors"], "under": ["Core", "Gluteus Max"]},
        "Belin Yuvarlaklaşması": {"over": ["Rectus Abd.", "Ext. Obliques"], "under": ["Core"]},
        "Omuzların Kalkması": {"over": ["Upper Trap.", "Levator Scap.", "SCM"], "under": ["Mid/Lower Trap."]},
        "Kanatlaşma (Winging)": {"over": ["Pectoralis Minor"], "under": ["Serratus Ant.", "Mid/Lower Trap."]},
        "Başın Geri Gitmesi": {"over": ["Upper Trap.", "SCM", "Levator Scap."], "under": ["Deep Cervical Flexors"]}
    },

    # 4. STANDING ROW TESTİ
    "Row": {
        "LPHC: Bel Çukuru Artıyor": {"over": ["Hip Flexors", "Erector Spinae"], "under": ["Core"]},
        "Omuzlar: Yukarı Kalkıyor": {"over": ["Upper Trap.", "SCM", "Levator Scap."], "under": ["Mid/Lower Trap."]},
        "Baş: Öne Gidiyor": {"over": ["Upper Trap.", "SCM", "Levator Scap."], "under": ["Deep Cervical Flexors"]}
    },

    # 5. OVERHEAD PRESS TESTİ
    "OHPress": {
        "LPHC: Bel Çukuru Artıyor": {"over": ["Hip Flexors", "Erector Spinae", "Lats"], "under": ["Core", "Gluteus Max"]},
        "Omuzlar: Yukarı Kalkıyor": {"over": ["Upper Trap.", "SCM", "Levator Scap."], "under": ["Mid/Lower Trap."]},
        "Omuzlar: Kollar Öne Gidiyor": {"over": ["Lats", "Pectorals"], "under": ["Rotator Cuff", "Mid/Lower Trap."]},
        "Omuzlar: Dirsekler Bükülüyor": {"over": ["Lats", "Pectorals", "Biceps Brachii"], "under": ["Rotator Cuff", "Mid/Lower Trap."]},
        "Baş: Öne Gidiyor": {"over": ["Upper Trap.", "SCM", "Levator Scap."], "under": ["Deep Cervical Flexors"]}
    }
}

# --- YARDIMCI: TÜRKÇE KARAKTER TEMİZLEYİCİ (PDF İÇİN) ---
def clean_text(text):
    """PDF oluştururken hata veren Türkçe karakterleri İngilizce karşılıklarına çevirir."""
    tr_map = str.maketrans("ğĞıİöÖüÜşŞçÇ", "gGiIoOuUsScC")
    return str(text).translate(tr_map)

# --- YMCA TEST FONKSİYONU ---
def calculate_ymca_score(gender, age, pulse):
    # Görseldeki tabloya göre yaklaşık değerler
    if pulse < 85: return "Harika"
    elif pulse < 105: return "Iyi / Ortalama Ustu"
    elif pulse < 125: return "Ortalama"
    else: return "Gelistirilmeli"

# --- SESSION STATE ---
if 'student_data' not in st.session_state: st.session_state['student_data'] = {"name": "", "date": None, "age": 25, "gender": "Erkek"}
for key in ['static_results', 'ohsquat_results', 'pushup_results', 'row_results', 'ohpress_results']:
    if key not in st.session_state: st.session_state[key] = []
if 'cardio_result' not in st.session_state: st.session_state['cardio_result'] = None

# --- PDF FONKSİYONU ---
def create_pdf(student_info, static_res, ohsquat_res, pushup_res, row_res, ohpress_res, cardio_res, analysis):
    pdf = FPDF()
    pdf.add_page()
    # Standart font kullanıyoruz, bu yüzden clean_text ile temizlik şart.
    pdf.set_font("Arial", 'B', 16)
    
    # Başlık
    pdf.cell(0, 10, clean_text("PT Pro: Hareket ve Postur Analizi"), ln=True, align='C')
    pdf.set_font("Arial", size=10)
    info_str = f"Ogrenci: {student_info['name']} | Yas: {student_info['age']} | Tarih: {student_info['date']}"
    pdf.cell(0, 10, clean_text(info_str), ln=True, align='C')
    pdf.line(10, 25, 200, 25)
    pdf.ln(5)

    # 1. KARDİYO
    if cardio_res:
        pdf.set_font("Arial", 'B', 12)
        pdf.cell(0, 10, clean_text("1. Kardiyovaskuler Kapasite (YMCA)"), ln=True)
        pdf.set_font("Arial", size=10)
        res_str = f"Sonuc: {cardio_res['rating']} ({cardio_res['pulse']} bpm)"
        pdf.cell(0, 8, clean_text(res_str), ln=True)
        pdf.ln(2)

    # 2. HAREKET TESTLERİ
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, clean_text("2. Gozlem Bulgulari"), ln=True)
    
    def print_test(title, data):
        if data:
            pdf.set_font("Arial", 'B', 10)
            pdf.cell(0, 6, clean_text(title), ln=True)
            pdf.set_font("Arial", size=10)
            for item in data:
                pdf.cell(0, 5, clean_text(f"  - {item}"), ln=True)
            pdf.ln(2)

    print_test("Statik Postur:", static_res)
    print_test("Overhead Squat:", ohsquat_res)
    print_test("Push-up Testi:", pushup_res)
    print_test("Standing Row Testi:", row_res)
    print_test("Overhead Press Testi:", ohpress_res)
    pdf.ln(3)

    # 3. REÇETE
    pdf.set_font("Arial", 'B', 12)
    pdf.cell(0, 10, clean_text("3. Duzeltici Egzersiz Plani"), ln=True)
    
    # Kırmızı (Esnet)
    pdf.set_text_color(220, 50, 50)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, clean_text("ESNET (Foam Roller + Statik Esneme):"), ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    over_str = ", ".join(sorted(list(analysis['overactive'])))
    pdf.multi_cell(0, 6, clean_text(over_str))
    pdf.ln(3)

    # Yeşil (Güçlendir)
    pdf.set_text_color(50, 150, 50)
    pdf.set_font("Arial", 'B', 11)
    pdf.cell(0, 8, clean_text("GUCLENDIR (Aktivasyon + Izole Guc):"), ln=True)
    pdf.set_text_color(0, 0, 0)
    pdf.set_font("Arial", size=10)
    under_str = ", ".join(sorted(list(analysis['underactive'])))
    pdf.multi_cell(0, 6, clean_text(under_str))
    
    return pdf.output(dest='S').encode('latin-1', 'replace')

# --- MENÜ ---
st.sidebar.title("NAVİGASYON")
menu = st.sidebar.radio("Adımlar:", 
    ["1. Giriş Bilgileri", "2. Statik Analiz", "3. Overhead Squat Analizi", 
     "4. Push-up Analizi", "5. Standing Row Analizi", "6. Overhead Press Analizi", 
     "7. Kardiyo (YMCA)", "8. Sonuç ve Rapor"])

# === SAYFALAR ===

if menu == "1. Giriş Bilgileri":
    st.header("📝 Öğrenci Profili")
    name = st.text_input("Ad Soyad", value=st.session_state['student_data']['name'])
    age = st.number_input("Yaş", 18, 99, st.session_state['student_data']['age'])
    gender = st.selectbox("Cinsiyet", ["Erkek", "Kadın"], 0 if st.session_state['student_data']['gender']=="Erkek" else 1)
    date = st.date_input("Tarih")
    if st.button("Kaydet"):
        st.session_state['student_data'].update({"name": name, "age": age, "gender": gender, "date": date})
        st.success("Kayıt Başarılı!")

elif menu == "2. Statik Analiz":
    st.header("🧍 Statik Postür Analizi")
    t1, t2, t3 = st.tabs(["Anterior (Ön)", "Lateral (Yan)", "Posterior (Arka)"])
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

elif menu == "3. Overhead Squat Analizi":
    st.header("🏋️ Overhead Squat Analizi")
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

elif menu == "4. Push-up Analizi":
    st.header("💪 Push-up Analizi")
    temp = st.session_state['pushup_results'].copy()
    c = st.columns(2)
    for i, item in enumerate(LOGIC_DB["Pushup"].keys()):
        if c[i%2].checkbox(item, value=(item in temp), key=f"p_{i}"):
            if item not in temp: temp.append(item)
        elif item in temp: temp.remove(item)
    st.session_state['pushup_results'] = temp

elif menu == "5. Standing Row Analizi":
    st.header("🚣 Standing Row Analizi")
    temp = st.session_state['row_results'].copy()
    c = st.columns(2)
    for i, item in enumerate(LOGIC_DB["Row"].keys()):
        if c[i%2].checkbox(item, value=(item in temp), key=f"r_{i}"):
            if item not in temp: temp.append(item)
        elif item in temp: temp.remove(item)
    st.session_state['row_results'] = temp

elif menu == "6. Overhead Press Analizi":
    st.header("🙌 Overhead Press Analizi")
    temp = st.session_state['ohpress_results'].copy()
    c = st.columns(2)
    for i, item in enumerate(LOGIC_DB["OHPress"].keys()):
        if c[i%2].checkbox(item, value=(item in temp), key=f"o_{i}"):
            if item not in temp: temp.append(item)
        elif item in temp: temp.remove(item)
    st.session_state['ohpress_results'] = temp

elif menu == "7. Kardiyo (YMCA)":
    st.header("🫀 3 Dk Adım Testi")
    pulse = st.number_input("Ölçülen Nabız (Test bitiminden 5sn sonra, 1 dk boyunca sayılan)", 40, 220)
    if st.button("Sonucu Hesapla"):
        r = calculate_ymca_score(st.session_state['student_data']['gender'], st.session_state['student_data']['age'], pulse)
        st.session_state['cardio_result'] = {"pulse": pulse, "rating": r}
        st.rerun() # Anlık yenileme için
    
    if st.session_state['cardio_result']:
        st.success(f"Sonuç: **{st.session_state['cardio_result']['rating']}**")

# === SONUÇ VE RAPOR (GÜNCELLENDİ) ===
elif menu == "8. Sonuç ve Rapor":
    st.header("📊 Analiz Özeti ve Rapor")
    
    # 1. KARDİYO SONUCUNU GÖSTER
    st.subheader("1. Kardiyo Durumu")
    if st.session_state['cardio_result']:
        res = st.session_state['cardio_result']
        st.info(f"❤️ **Kardiyovasküler Kapasite:** {res['rating']} (Nabız: {res['pulse']} bpm)")
    else:
        st.warning("⚠️ Kardiyo testi yapılmadı.")

    st.divider()

    # 2. KAS ANALİZİ
    st.subheader("2. Kas Dengesizlikleri")
    
    all_over, all_under = set(), set()
    sources = [(st.session_state['static_results'], "Static"), (st.session_state['ohsquat_results'], "OHSquat"),
               (st.session_state['pushup_results'], "Pushup"), (st.session_state['row_results'], "Row"),
               (st.session_state['ohpress_results'], "OHPress")]
    
    for res, db in sources:
        for obs in res:
            d = LOGIC_DB[db][obs]
            all_over.update(d["over"])
            all_under.update(d["under"])

    c1, c2 = st.columns(2)
    
    # DÜZELTİLDİ: Artık liste hatası vermeyecek
    with c1: 
        st.error(f"🔥 ESNET ({len(all_over)})")
        if all_over:
            for m in sorted(list(all_over)):
                st.write(f"- {m}")
        else:
            st.caption("Sorunlu kas bulunamadı.")
            
    with c2: 
        st.success(f"✅ GÜÇLENDİR ({len(all_under)})")
        if all_under:
            for m in sorted(list(all_under)):
                st.write(f"- {m}")
        else:
            st.caption("Sorunlu kas bulunamadı.")

    st.divider()
    
    # PDF İNDİRME
    if st.button("📥 PDF Raporunu Oluştur ve İndir"):
        try:
            pdf_bytes = create_pdf(
                st.session_state['student_data'],
                st.session_state['static_results'],
                st.session_state['ohsquat_results'],
                st.session_state['pushup_results'],
                st.session_state['row_results'],
                st.session_state['ohpress_results'],
                st.session_state['cardio_result'],
                {"overactive": all_over, "underactive": all_under}
            )
            b64 = base64.b64encode(pdf_bytes).decode()
            href = f'<a href="data:application/octet-stream;base64,{b64}" download="PT_Rapor_{st.session_state["student_data"]["name"]}.pdf" style="text-decoration:none; color:white; background-color:#FF4B4B; padding:12px; border-radius:5px; font-weight:bold;">📄 Raporu İndir (PDF)</a>'
            st.markdown(href, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"PDF oluşturulurken bir hata oluştu: {e}")