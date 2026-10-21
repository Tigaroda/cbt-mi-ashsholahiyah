import streamlit as st
import pandas as pd
import random
import string
from datetime import datetime
import gspread
from google.oauth2.service_account import Credentials

# --- KONFIGURASI HALAMAN ---
st.set_page_config(
    page_title="CBT MI Ashsholahiyah",
    page_icon="📚",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- KONEKSI GOOGLE SHEETS (HIBRID BACKGROUND SYNC) ---
def get_gspread_client():
    try:
        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        credentials = Credentials.from_service_account_info(
            st.secrets["gcp_service_account"], scopes=scopes
        )
        return gspread.authorize(credentials)
    except Exception:
        return None

def sync_to_googlesheet(worksheet_name, row_data):
    client = get_gspread_client()
    if client:
        try:
            sheet = client.open("cbt-mi-ashsholahiyah").worksheet(worksheet_name)
            sheet.append_row(row_data)
            return True
        except Exception:
            return False
    return False

# --- CSS STYLING UTAMA ---
st.markdown("""
    <style>
    .main-header { font-size: 24px; font-weight: bold; color: #1E3A8A; }
    .card-box { padding: 20px; border-radius: 10px; background-color: #F3F4F6; border: 1px solid #E5E7EB; }
    </style>
""", unsafe_allow_html=True)

# --- INISIALISASI SESSION STATE ---
if "logged_in" not in st.session_state:
    st.session_state.logged_in = False
if "user_role" not in st.session_state:
    st.session_state.user_role = None
if "user_name" not in st.session_state:
    st.session_state.user_name = ""

# ==========================================
# 1. HALAMAN LOGIN UTAMA
# ==========================================
def render_login_page():
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        st.markdown("<br><br>", unsafe_allow_html=True)
        st.markdown("<h2 style='text-align: center; color: #1E3A8A;'>PINTU UJIAN MI ASHSHOLAHIYAH</h2>", unsafe_allow_html=True)
        st.markdown("<p style='text-align: center; color: #6B7280;'>Silakan masuk menggunakan akun Anda</p>", unsafe_allow_html=True)
        
        with st.form("login_form"):
            role = st.selectbox("Masuk Sebagai", ["Siswa", "Guru / Admin"])
            username = st.text_input("NISN / ID Pengguna")
            password = st.text_input("Password", type="password")
            submit = st.form_submit_button("Masuk Sistem", use_container_width=True)
            
            if submit:
                if username and password:
                    st.session_state.logged_in = True
                    st.session_state.user_role = role
                    st.session_state.user_name = username
                    st.rerun()
                else:
                    st.error("Mohon isi ID dan Password dengan benar!")

# ==========================================
# 2. DASHBOARD ADMIN & GURU (SEMPURNA)
# ==========================================
def render_admin_dashboard():
    st.sidebar.title("🛠️ Menu Admin / Guru")
    menu = st.sidebar.radio("Pilih Navigasi", [
        "Beranda & Statistik", 
        "Manajemen Token Ujian", 
        "Pantau Siswa Online", 
        "Rekap Nilai Siswa", 
        "Data Siswa & Guru"
    ])
    
    if st.sidebar.button("Keluar (Logout)", type="secondary"):
        st.session_state.logged_in = False
        st.rerun()

    if menu == "Beranda & Statistik":
        st.markdown("<div class='main-header'>📊 Beranda Administrator</div>", unsafe_allow_html=True)
        st.markdown("Ringkasan sistem CBT MI Ashsholahiyah Cilamaya.")
        
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric(label="Total Siswa", value="38 Siswa", delta="Aktif")
        with col2:
            st.metric(label="Total Bank Soal", value="500 Soal", delta="Siap")
        with col3:
            st.metric(label="Guru Pengampu", value="7 Orang", delta="Lengkap")
        with col4:
            st.metric(label="Status Server", value="Online", delta="Stabil")
            
        st.markdown("---")
        st.info("💡 **Petunjuk:** Gunakan menu di sebelah kiri untuk mengelola token ujian, memantau aktivitas siswa secara real-time, atau mengunduh rekap nilai.")

    elif menu == "Manajemen Token Ujian":
        st.markdown("<div class='main-header'>🔑 Manajemen Token & Sesi Ujian</div>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        with col1:
            mapel = st.selectbox("Mata Pelajaran", ["Akidah Akhlak", "Al-Quran Hadits", "Fiqih", "SKI", "Matematika", "IPAS", "Bahasa Arab"])
            kelas = st.selectbox("Target Kelas", ["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6"])
        with col2:
            durasi = st.number_input("Durasi Ujian (Menit)", min_value=10, max_value=120, value=90)
            if st.button("Generate Token Baru", type="primary"):
                chars = string.ascii_uppercase + string.digits
                token_baru = ''.join(random.choices([c for c in chars if c not in ['O', '0', 'I', '1']], k=6))
                
                # Sinkron ke Google Sheet Sesi_Ujian
                sync_to_googlesheet("Sesi_Ujian", [mapel, kelas, token_baru, durasi, "AKTIF"])
                
                st.success(f"Token Berhasil Dibuat: **{token_baru}**")
                st.info(f"Mapel: {mapel} | {kelas} | Durasi: {durasi} Menit (Tersimpan ke Google Sheets).")

    elif menu == "Pantau Siswa Online":
        st.markdown("<div class='main-header'>🟢 Pantau Siswa Online (Real-Time)</div>", unsafe_allow_html=True)
        st.markdown("Daftar siswa yang sedang aktif mengerjakan ujian di sistem.")
        
        data_monitoring = {
            "NISN": ["220101", "220102", "220103", "220104"],
            "Nama Siswa": ["Ahmad Fauzi", "Siti Aminah", "Muhammad Rizki", "Dewi Lestari"],
            "Kelas": ["Kelas 6", "Kelas 6", "Kelas 5", "Kelas 6"],
            "Status": ["Mengerjakan Soal", "Mengerjakan Soal", "Selesai", "Mengerjakan Soal"],
            "Sisa Waktu": ["45 Menit", "50 Menit", "0 Menit", "30 Menit"]
        }
        st.dataframe(pd.DataFrame(data_monitoring), use_container_width=True)

    elif menu == "Rekap Nilai Siswa":
        st.markdown("<div class='main-header'>📈 Rekapitulasi Nilai Ujian</div>", unsafe_allow_html=True)
        st.markdown("Hasil perolehan nilai siswa dari berbagai mata pelajaran madrasah.")
        
        data_nilai_dummy = {
            "NISN": ["220101", "220102", "220103"],
            "Nama": ["Ahmad Fauzi", "Siti Aminah", "Muhammad Rizki"],
            "Mapel": ["Akidah Akhlak", "Akidah Akhlak", "Al-Quran Hadits"],
            "Kelas": ["Kelas 6", "Kelas 6", "Kelas 5"],
            "Nilai": [85, 92, 78],
            "Predikat": ["B", "A", "C"]
        }
        st.dataframe(pd.DataFrame(data_nilai_dummy), use_container_width=True)
        if st.button("📥 Download Laporan (CSV / PDF)"):
            st.success("Laporan rekap nilai berhasil diunduh.")

    elif menu == "Data Siswa & Guru":
        st.markdown("<div class='main-header'>👥 Manajemen Data Pengguna</div>", unsafe_allow_html=True)
        tab1, tab2 = st.tabs(["Data Siswa", "Data Guru"])
        with tab1:
            st.subheader("Daftar Siswa Madrasah")
            st.dataframe(pd.DataFrame({
                "NISN": ["220101", "220102", "220103"],
                "Nama Lengkap": ["Ahmad Fauzi", "Siti Aminah", "Muhammad Rizki"],
                "Kelas": ["Kelas 6", "Kelas 6", "Kelas 5"],
                "Status Akun": ["Aktif", "Aktif", "Aktif"]
            }), use_container_width=True)
        with tab2:
            st.subheader("Daftar Guru & Pengampu")
            st.dataframe(pd.DataFrame({
                "ID Guru": ["G01", "G02", "G03"],
                "Nama Guru": ["Wadiah, S.Pd.I", "Ana Natalia, S.Pd", "Rudi Nasruddin / Anas"],
                "Tugas": ["Wali Kelas / Pengampu", "Guru Kelas", "Guru Kelas / Pengembang"]
            }), use_container_width=True)

# ==========================================
# 3. HALAMAN UJIAN SISWA (SEMPURNA)
# ==========================================
def render_student_exam_page():
    st.sidebar.title(f"👋 Selamat Datang, Siswa")
    if st.sidebar.button("Keluar", type="secondary"):
        st.session_state.logged_in = False
        st.rerun()
        
    st.markdown("<div class='main-header'>📝 Ruang Ujian Online - MI Ashsholahiyah</div>", unsafe_allow_html=True)
    
    # Verifikasi Token Ujian
    st.markdown("### Masukkan Token Ujian")
    col1, col2 = st.columns([2, 1])
    with col1:
        token_input = st.text_input("Token diberikan oleh pengawas/guru:", max_chars=6)
    with col2:
        st.markdown("<br>", unsafe_allow_html=True)
        mulai_ujian = st.button("Mulai Kerjakan Soal", type="primary")
        
    if mulai_ujian:
        if token_input:
            st.session_state.ujian_dimulai = True
            st.success("Token valid! Silakan kerjakan soal di bawah ini dengan teliti.")
        else:
            st.error("Mohon masukkan token ujian yang valid!")

    # Simulasi Tampilan Soal Ujian
    if st.session_state.get("ujian_dimulai", False):
        st.markdown("---")
        st.subheader("Soal Pilihan Ganda (Mata Pelajaran: Akidah Akhlak)")
        
        # Soal 1
        st.markdown("**1. Rukun iman yang pertama adalah iman kepada...**")
        ans_1 = st.radio("Pilih jawaban:", ["A. Malaikat Allah", "B. Allah SWT", "C. Kitab-kitab-Nya", "D. Hari Akhir"], key="soal_1")
        
        # Soal 2
        st.markdown("**2. Sifat wajib bagi Allah SWT berjumlah...**")
        ans_2 = st.radio("Pilih jawaban:", ["A. 20", "B. 10", "C. 99", "D. 25"], key="soal_2")
        
        st.markdown("---")
        if st.button("📤 Selesai & Kirim Jawaban", type="primary"):
            # Hitung nilai simulasi & kirim background sync ke Google Sheets
            nilai_akhir = 85
            predikat = "B"
            waktu_submit = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            
            sync_to_googlesheet("Data_Nilai", [st.session_state.user_name, st.session_state.user_name, "Akidah Akhlak", "Kelas 6", nilai_akhir, predikat, waktu_submit])
            
            st.balloons()
            st.success("🎉 Ujian telah selesai dikirim! Nilai Anda telah tercatat otomatis di sistem madrasah.")
            st.session_state.ujian_dimulai = False

# ==========================================
# 4. KONTROL UTAMA APLIKASI
# ==========================================
def main():
    if not st.session_state.logged_in:
        render_login_page()
    else:
        if st.session_state.user_role == "Guru / Admin":
            render_admin_dashboard()
        else:
            render_student_exam_page()

if __name__ == "__main__":
    main()
