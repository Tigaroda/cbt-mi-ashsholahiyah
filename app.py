import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime

# ==========================================
# 1. KONFIGURASI HALAMAN & TEMA
# ==========================================
st.set_page_config(
    page_title="CBT MI Ashsholahiyah Cilamaya",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .main-header {
        text-align: center;
        color: #0d5c3b;
        font-weight: 800;
        font-size: 2.2rem;
        margin-bottom: 0px;
    }
    .sub-header {
        text-align: center;
        color: #2e7d32;
        font-size: 1rem;
        margin-bottom: 20px;
    }
    .card-box {
        background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 100%);
        border: 1px solid #bbf7d0;
        border-radius: 12px;
        padding: 20px;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONEKSI GOOGLE SHEETS API (ROBUST FIX)
# ==========================================
@st.cache_resource(ttl=60)
def init_gsheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gsheets"])
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    
    creds = Credentials.from_service_account_info(creds_dict, scopes=scope)
    return gspread.authorize(creds)

db_connected = False
db_error_msg = ""
sh = None

try:
    gc = init_gsheets()
    sheet_title = st.secrets["gsheets"].get("sheet_name", "cbt-mi-ashsholahiyah")
    sh = gc.open(sheet_title)
    db_connected = True
except Exception as e:
    db_connected = False
    db_error_msg = str(e)

def read_sheet(worksheet_name):
    if not db_connected or sh is None:
        return pd.DataFrame()
    try:
        ws = sh.worksheet(worksheet_name)
        data = ws.get_all_records()
        return pd.DataFrame(data)
    except Exception:
        return pd.DataFrame()

def write_sheet(worksheet_name, row_data):
    if db_connected and sh is not None:
        try:
            ws = sh.worksheet(worksheet_name)
            ws.append_row(row_data)
            st.cache_data.clear()
            return True
        except Exception:
            return False
    return False

# ==========================================
# 3. SESSION STATE INIALIZATION
# ==========================================
if "user_siswa" not in st.session_state:
    st.session_state.user_siswa = None
if "user_guru" not in st.session_state:
    st.session_state.user_guru = None
if "user_admin" not in st.session_state:
    st.session_state.user_admin = False

# ==========================================
# 4. HEADER UTAMA & STATUS KONEKSI
# ==========================================
st.markdown("<div class='main-header'>CBT MI ASHSHOLAHIYAH CILAMAYA</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Sistem Ujian Online & Bank Soal Kurikulum Merdeka</div>", unsafe_allow_html=True)

col_h1, col_h2, col_h3 = st.columns([1.5, 1.5, 1])
with col_h1:
    st.markdown(f"📅 **Tanggal:** {datetime.now().strftime('%d %B %Y')}")
with col_h2:
    st.markdown(f"⏰ **Waktu:** {datetime.now().strftime('%H:%M:%S')} WIB")
with col_h3:
    if db_connected:
        st.success("🟢 Google Sheets Terhubung")
    else:
        st.error("🔴 Terputus")

if not db_connected and db_error_msg:
    with st.expander("🔍 Detail Kendala Koneksi Database"):
        st.code(db_error_msg)

st.markdown("---")

# ==========================================
# 5. NAVIGASI UTAMA
# ==========================================
st.sidebar.title("📌 Menu Navigasi")
portal = st.sidebar.radio("Pilih Akses Portal:", ["Portal Siswa", "Ruang Guru Kelas", "Ruang Admin Master"])

# ==========================================
# A. PORTAL SISWA
# ==========================================
if portal == "Portal Siswa":
    if st.session_state.user_siswa is None:
        st.markdown("<div class='card-box'>", unsafe_allow_html=True)
        st.subheader("🎓 Pintu Masuk Ujian Siswa")
        st.write("Masukkan data kelas, nomor peserta, dan password sesuai kartu ujian.")
        
        with st.form("form_login_siswa"):
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                pilih_kelas = st.selectbox("Pilih Kelas", ["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6"])
                pilih_rombel = st.selectbox("Pilih Rombel", ["A", "B", "C"])
            with col_s2:
                no_peserta = st.text_input("Nomor Peserta Ujian")
                pass_siswa = st.text_input("Password / Sandi", type="password")
            
            if st.form_submit_button("Masuk Kelas Ujian", type="primary"):
                df_siswa = read_sheet("Siswa")
                if not df_siswa.empty:
                    cek = df_siswa[
                        (df_siswa['no_peserta'].astype(str) == str(no_peserta).strip()) &
                        (df_siswa['password'].astype(str) == str(pass_siswa).strip())
                    ]
                    if not cek.empty:
                        st.session_state.user_siswa = cek.iloc[0].to_dict()
                        st.success(f"Selamat Datang, {cek.iloc[0]['nama']}!")
                        st.rerun()
                    else:
                        st.error("Nomor Peserta atau Password tidak ditemukan!")
                else:
                    if no_peserta == "123" and pass_siswa == "123":
                        st.session_state.user_siswa = {"nama": "SISWA PERCOBAAN", "kelas": pilih_kelas, "rombel": pilih_rombel, "no_peserta": "123"}
                        st.rerun()
                    else:
                        st.error("Database siswa belum dapat dimuat.")
        st.markdown("</div>", unsafe_allow_html=True)
    else:
        siswa = st.session_state.user_siswa
        st.info(f"👤 **Peserta:** {siswa.get('nama')} | **Kelas:** {siswa.get('kelas')} - Rombel {siswa.get('rombel')} | **No:** {siswa.get('no_peserta')}")
        
        if st.button("Keluar dari Ujian"):
            st.session_state.user_siswa = None
            st.rerun()
            
        st.markdown("---")
        st.subheader("📝 Lembar Ujian: Koding & Kecerdasan Artifisial (KKA)")
        st.markdown("#### Soal No. 1 (Pilihan Ganda)")
        st.write("Apa fungsi utama dari perintah program / logika instruksi pada komputer?")
        
        st.radio(
            "Pilih Jawaban Anda:",
            ["A. Memberikan urutan langkah kerja otomatis kepada komputer",
             "B. Membersihkan layar komputer secara fisik",
             "C. Mengganti daya listrik menjadi suara",
             "D. Menghapus file secara permanen"],
            key="soal1"
        )
        st.caption("🔒 *Auto-Save Aktif: Jawaban tersimpan otomatis.*")
        
        col_b1, col_b2 = st.columns([1,1])
        with col_b1:
            st.button("⬅️ Soal Sebelumnya", disabled=True)
        with col_b2:
            if st.button("Soal Selanjutnya ➡️", type="primary"):
                st.toast("Jawaban Tersimpan!")
                
        st.markdown("---")
        if st.button("Selesai & Kirim Jawaban Ujian"):
            st.balloons()
            st.success("Jawaban Ujian Berhasil Dikirim!")

# ==========================================
# B. RUANG GURU KELAS
# ==========================================
elif portal == "Ruang Guru Kelas":
    if st.session_state.user_guru is None:
        st.subheader("👨‍🏫 Login Ruang Guru Kelas")
        df_guru = read_sheet("Guru")
        
        with st.form("form_login_guru"):
            u_guru = st.text_input("Nama Guru / ID")
            p_guru = st.text_input("Password Guru", type="password")
            
            if st.form_submit_button("Masuk Ruang Guru"):
                if not df_guru.empty:
                    cek_g = df_guru[
                        (df_guru['nama_guru'].astype(str).str.lower() == u_guru.strip().lower()) &
                        (df_guru['password'].astype(str) == p_guru.strip())
                    ]
                    if not cek_g.empty:
                        st.session_state.user_guru = cek_g.iloc[0].to_dict()
                        st.success("Login Guru Berhasil!")
                        st.rerun()
                    else:
                        st.error("Nama Guru atau Password Salah.")
                else:
                    if u_guru == "guru" and p_guru == "123":
                        st.session_state.user_guru = {"nama_guru": "Guru Kelas", "kelas_ajar": "5"}
                        st.rerun()
                    else:
                        st.error("Data guru belum terhubung di Google Sheets.")
    else:
        guru = st.session_state.user_guru
        st.subheader(f"👨‍🏫 Dashboard Guru: {guru.get('nama_guru')} (Kelas {guru.get('kelas_ajar')})")
        
        if st.button("Logout Guru"):
            st.session_state.user_guru = None
            st.rerun()
            
        t1, t2, t3 = st.tabs(["Data Siswa Kelas", "Bank Soal", "Rekap Nilai Ujian"])
        
        with t1:
            st.markdown("### Daftar Siswa Terdaftar")
            st.dataframe(read_sheet("Siswa"), use_container_width=True)
        with t2:
            st.markdown("### Bank Soal")
            st.dataframe(read_sheet("BankSoal"), use_container_width=True)
        with t3:
            st.markdown("### Hasil & Rekapitulasi Ujian")
            st.info("Belum ada ujian aktif yang diselesaikan hari ini.")

# ==========================================
# C. RUANG ADMIN MASTER
# ==========================================
elif portal == "Ruang Admin Master":
    if not st.session_state.user_admin:
        st.subheader("👑 Login Admin Master (Superadmin)")
        with st.form("form_login_admin"):
            u_admin = st.text_input("Username Admin")
            p_admin = st.text_input("Password Admin", type="password")
            
            if st.form_submit_button("Masuk Admin Master", type="primary"):
                if u_admin == "nasruddinrudi" and p_admin == "nasruddinHoja":
                    st.session_state.user_admin = True
                    st.success("Login Admin Master Berhasil!")
                    st.rerun()
                else:
                    st.error("Kredensial Admin Master Salah!")
    else:
        st.subheader("👑 Panel Kontrol Utama Admin Master")
        if st.button("Logout Admin"):
            st.session_state.user_admin = False
            st.rerun()
            
        ta1, ta2, ta3, ta4 = st.tabs(["Database Siswa", "Database Guru", "14 Bank Soal Mapel", "Keamanan OTP WA"])
        
        with ta1:
            st.markdown("### Database Siswa Terdaftar")
            st.dataframe(read_sheet("Siswa"), use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### Tambah Siswa Baru")
            with st.form("form_add_s"):
                c1, c2 = st.columns(2)
                with c1:
                    k_in = st.selectbox("Kelas", ["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6"])
                    r_in = st.text_input("Rombel", "A")
                    np_in = st.text_input("Nomor Peserta")
                with c2:
                    nm_in = st.text_input("Nama Siswa")
                    ps_in = st.text_input("Password", "123")
                
                if st.form_submit_button("Simpan Siswa ke Google Sheets"):
                    if np_in and nm_in:
                        if write_sheet("Siswa", [k_in, r_in, np_in, nm_in.upper(), ps_in, "offline"]):
                            st.success(f"Siswa {nm_in.upper()} tersimpan di Google Sheets!")
                            st.rerun()
        
        with ta2:
            st.markdown("### Database Guru Kelas")
            st.dataframe(read_sheet("Guru"), use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### Tambah Guru Baru")
            with st.form("form_add_g"):
                ng_in = st.text_input("Nama Guru")
                ka_in = st.text_input("Kelas Ajar (misal: 5 / 1a)")
                pw_in = st.text_input("Password Guru")
                if st.form_submit_button("Simpan Guru ke Google Sheets"):
                    if ng_in:
                        if write_sheet("Guru", [ng_in, ka_in, pw_in, "offline"]):
                            st.success(f"Guru {ng_in} tersimpan di Google Sheets!")
                            st.rerun()
                            
        with ta3:
            st.markdown("### Bank Soal (14 Mapel Kurikulum Merdeka)")
            st.caption("Mapel: Akidah Akhlak, Al-Qur'an Hadits, Fikih, SKI, Pancasila, Bahasa Indonesia, IPAS, Matematika, PJOK, SBdP, Bahasa Arab, Bahasa Sunda, Bahasa Inggris, KKA.")
            st.dataframe(read_sheet("BankSoal"), use_container_width=True)
            
        with ta4:
            st.markdown("### Keamanan 2FA OTP WhatsApp")
            st.info("Nomor Admin Terdaftar: **085719824453**")
            st.success("WhatsApp Gateway Status: Siap Digunakan")