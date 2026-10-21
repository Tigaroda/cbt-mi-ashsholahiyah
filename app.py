import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import textwrap

# ==========================================
# 1. KONFIGURASI HALAMAN & CSS RESPONSIF LAPTOP
# ==========================================
st.set_page_config(
    page_title="CBT MI Ashsholahiyah Cilamaya",
    page_icon="🏫",
    layout="wide",
    initial_sidebar_state="expanded"
)

st.markdown("""
    <style>
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 2rem !important;
        padding-left: 2rem !important;
        padding-right: 2rem !important;
        max-width: 100% !important;
    }
    .main-header {
        text-align: center;
        color: #0d5c3b;
        font-weight: 800;
        font-size: 2rem;
        margin-bottom: 2px;
    }
    .sub-header {
        text-align: center;
        color: #1e3a8a;
        font-size: 0.95rem;
        margin-bottom: 15px;
    }
    .soal-teks {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        line-height: 1.5;
        padding: 18px;
        background: #fafaf9;
        border: 1px solid #e7e5e4;
        border-radius: 10px;
        margin-bottom: 15px;
        color: #1e293b;
    }
    .stRadio label p {
        font-size: 1.1rem !important;
        font-weight: 500 !important;
        color: #0f172a !important;
    }
    .kartu-container {
        border: 2px solid #1e293b;
        border-radius: 12px;
        padding: 15px;
        background: #ffffff;
        width: 100%;
        max-width: 380px;
        margin: 10px auto;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
    }
    .profil-box {
        background: #ffffff;
        border: 2px solid #cbd5e1;
        border-radius: 10px;
        padding: 12px;
        margin-bottom: 15px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.05);
    }
    .sidebar-widget {
        background: linear-gradient(135deg, #f0fdf4 0%, #e0f2fe 100%);
        border: 1px solid #bbf7d0;
        border-radius: 10px;
        padding: 12px;
        margin-top: 20px;
        font-size: 0.88rem;
    }
    .stat-card {
        background: #f8fafc;
        border: 1px solid #cbd5e1;
        border-radius: 8px;
        padding: 12px;
        text-align: center;
    }
    </style>
""", unsafe_allow_html=True)

# ==========================================
# 2. KONEKSI GOOGLE SHEETS API
# ==========================================
@st.cache_resource(ttl=60)
def init_gsheets():
    scope = [
        "https://www.googleapis.com/auth/spreadsheets",
        "https://www.googleapis.com/auth/drive"
    ]
    creds_dict = dict(st.secrets["gsheets"])
    
    if "private_key" in creds_dict:
        pk = str(creds_dict["private_key"])
        pk = pk.replace("\\n", "\n")
        if "BEGIN PRIVATE KEY" in pk and "END PRIVATE KEY" in pk:
            key_body = pk.split("-----BEGIN PRIVATE KEY-----")[1].split("-----END PRIVATE KEY-----")[0]
            key_body = "".join(key_body.split())
            formatted_body = "\n".join(textwrap.wrap(key_body, 64))
            pk = f"-----BEGIN PRIVATE KEY-----\n{formatted_body}\n-----END PRIVATE KEY-----"
        creds_dict["private_key"] = pk
    
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
            return True, ""
        except Exception as e:
            return False, str(e)
    return False, "Database belum terhubung"

def append_bulk_sheet(worksheet_name, df_to_append):
    if db_connected and sh is not None:
        try:
            ws = sh.worksheet(worksheet_name)
            existing_headers = ws.row_values(1)
            if existing_headers:
                for col in existing_headers:
                    if col not in df_to_append.columns:
                        df_to_append[col] = ""
                df_to_append = df_to_append[existing_headers]
            
            df_to_append = df_to_append.fillna("")
            values = df_to_append.values.tolist()
            ws.append_rows(values)
            st.cache_data.clear()
            return True, ""
        except Exception as e:
            return False, str(e)
    return False, "Database belum terhubung"

# ==========================================
# 3. SESSION STATE INISIALISASI
# ==========================================
if "user_siswa" not in st.session_state:
    st.session_state.user_siswa = None
if "user_guru" not in st.session_state:
    st.session_state.user_guru = None
if "user_admin" not in st.session_state:
    st.session_state.user_admin = False
if "sedang_ujian" not in st.session_state:
    st.session_state.sedang_ujian = False
if "jawaban_siswa" not in st.session_state:
    st.session_state.jawaban_siswa = {}

# ==========================================
# 4. SIDEBAR MENU & WIDGET WAKTU DI BAWAH
# ==========================================
st.sidebar.title("📌 Menu Navigasi")
portal = st.sidebar.radio("Pilih Akses Portal:", ["Portal Siswa", "Ruang Guru Kelas", "Ruang Admin Master"])

st.sidebar.markdown("---")
with st.sidebar.container():
    tgl_str = datetime.now().strftime('%d %B %Y')
    jam_str = datetime.now().strftime('%H:%M:%S')
    st.sidebar.markdown(f"""
        <div class='sidebar-widget'>
            <p style='margin: 0; font-weight: bold; color: #0d5c3b;'>🕒 WIDGET SERVER</p>
            <p style='margin: 4px 0 2px 0;'>📅 <b>Hari/Tgl:</b> {tgl_str}</p>
            <p style='margin: 2px 0 4px 0;'>⏰ <b>Waktu:</b> {jam_str} WIB</p>
        </div>
    """, unsafe_allow_html=True)
    
    if db_connected:
        st.sidebar.success("🟢 Google Sheets Terhubung")
    else:
        st.sidebar.error("🔴 Koneksi Terputus")

# ==========================================
# 5. HEADER UTAMA
# ==========================================
st.markdown("<div class='main-header'>CBT MI ASHSHOLAHIYAH CILAMAYA</div>", unsafe_allow_html=True)
st.markdown("<div class='sub-header'>Sistem Ujian Online & Bank Soal Kurikulum Merdeka</div>", unsafe_allow_html=True)

LIST_MAPEL = [
    "Akidah Akhlak", "Al-Quran Hadits", "Fiqih", "SKI", 
    "Pendidikan Pancasila", "Bahasa Indonesia", "IPAS", "Matematika", 
    "PJOK", "SBdP", "Bahasa Arab", "Bahasa Sunda", "Bahasa Inggris", "Koding dan Kecerdasan Artifisial (KKA)"
]

LIST_KATEGORI = ["Latihan", "Ulangan Tengah Semester (UTS)", "Ulangan Semester (UAS)"]

BANK_SOAL_COLS = [
    "Kelas", "Mapel", "Nama_Materi", "Kategori_Ujian", 
    "Tipe_Soal", "Teks_Soal", "Opsi_A", "Opsi_B", 
    "Opsi_C", "Opsi_D", "Kunci"
]

def render_bank_soal_manager(key_prefix):
    st.markdown("### 📚 Kelola Bank Soal (14 Mata Pelajaran & Kategori Lengkap)")
    
    df_bs_stat = read_sheet("BankSoal")
    if not df_bs_stat.empty:
        tot_soal = len(df_bs_stat)
        cols_lower = [str(c).lower() for c in df_bs_stat.columns]
        
        if 'tipe_soal' in cols_lower:
            col_tipe = df_bs_stat.columns[cols_lower.index('tipe_soal')]
            tot_pg = len(df_bs_stat[df_bs_stat[col_tipe].astype(str).str.contains("Pilihan", case=False, na=False)])
        else:
            tot_pg = tot_soal

        if 'kategori_ujian' in cols_lower:
            col_kat = df_bs_stat.columns[cols_lower.index('kategori_ujian')]
            tot_uts = len(df_bs_stat[df_bs_stat[col_kat].astype(str).str.contains("Tengah", case=False, na=False)])
            tot_uas = len(df_bs_stat[df_bs_stat[col_kat].astype(str).str.contains("Semester", case=False, na=False) & ~df_bs_stat[col_kat].astype(str).str.contains("Tengah", case=False, na=False)])
        else:
            tot_uts = 0
            tot_uas = 0
            
        sc1, sc2, sc3, sc4 = st.columns(4)
        with sc1:
            st.markdown(f"<div class='stat-card'><h4>📦 Total Soal</h4><h2>{tot_soal}</h2></div>", unsafe_allow_html=True)
        with sc2:
            st.markdown(f"<div class='stat-card'><h4>🔘 Pilihan Ganda (PG)</h4><h2>{tot_pg}</h2></div>", unsafe_allow_html=True)
        with sc3:
            st.markdown(f"<div class='stat-card'><h4>📝 Soal UTS</h4><h2>{tot_uts}</h2></div>", unsafe_allow_html=True)
        with sc4:
            st.markdown(f"<div class='stat-card'><h4>📑 Soal UAS</h4><h2>{tot_uas}</h2></div>", unsafe_allow_html=True)
        st.markdown("<br>", unsafe_allow_html=True)

    tab_bs1, tab_bs2, tab_bs3 = st.tabs(["📂 Upload & Template", "➕ Tambah Soal Satuan", "✏️ Edit / Hapus Soal"])
    
    with tab_bs1:
        col_1, col_2 = st.columns(2)
        with col_1:
            st.markdown("#### 📥 Download Template CSV")
            template_df = pd.DataFrame(columns=BANK_SOAL_COLS)
            csv_data = template_df.to_csv(index=False).encode('utf-8')
            st.download_button("Unduh Template CSV Soal", data=csv_data, file_name="template_bank_soal.csv", mime="text/csv", key=f"{key_prefix}_dl")
        with col_2:
            st.markdown("#### 📤 Upload Soal Massal (.CSV)")
            up_file = st.file_uploader("Pilih file CSV Bank Soal", type=["csv"], key=f"{key_prefix}_up")
            if up_file is not None:
                try:
                    try:
                        df_up = pd.read_csv(up_file, encoding='utf-8')
                    except UnicodeDecodeError:
                        up_file.seek(0)
                        df_up = pd.read_csv(up_file, encoding='latin-1')
                    st.write("Pratinjau Data:")
                    st.dataframe(df_up.head(3))
                    if st.button("Proses Upload ke Database", type="primary", key=f"{key_prefix}_btn"):
                        success, err_msg = append_bulk_sheet("BankSoal", df_up)
                        if success:
                            st.success("Bank soal berhasil diupload ke Google Sheets!")
                            st.rerun()
                        else:
                            st.error(f"Gagal mengupload soal. Detail: {err_msg}")
                except Exception as e:
                    st.error(f"Format file CSV tidak sesuai: {e}")

    with tab_bs2:
        st.markdown("#### ➕ Form Tambah Butir Soal Satuan")
        with st.form(f"form_tambah_soal_{key_prefix}"):
            c_ts1, c_ts2 = st.columns(2)
            with c_ts1:
                t_kelas = st.selectbox("Kelas", ["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6"], key=f"{key_prefix}_t_kls")
                t_mapel = st.selectbox("Mata Pelajaran", LIST_MAPEL, key=f"{key_prefix}_t_mpl")
                t_materi = st.text_input("Nama Materi / Bab", key=f"{key_prefix}_t_mat")
            with c_ts2:
                t_kategori = st.selectbox("Kategori Ujian", LIST_KATEGORI, key=f"{key_prefix}_t_kat")
                t_tipe = st.selectbox("Tipe Soal", ["Pilihan Ganda"], key=f"{key_prefix}_t_tip")
                t_kunci = st.selectbox("Kunci Jawaban", ["A", "B", "C", "D"], key=f"{key_prefix}_t_kun")
            
            t_teks = st.text_area("Teks Pertanyaan Soal", key=f"{key_prefix}_t_teks")
            co_a, co_b = st.columns(2)
            with co_a:
                t_opsi_a = st.text_input("Opsi A", key=f"{key_prefix}_t_oa")
                t_opsi_c = st.text_input("Opsi C", key=f"{key_prefix}_t_oc")
            with co_b:
                t_opsi_b = st.text_input("Opsi B", key=f"{key_prefix}_t_ob")
                t_opsi_d = st.text_input("Opsi D", key=f"{key_prefix}_t_od")
                
            if st.form_submit_button("Simpan Soal ke Database", type="primary"):
                if t_mapel and t_teks:
                    row_data = [t_kelas, t_mapel, t_materi, t_kategori, t_tipe, t_teks, t_opsi_a, t_opsi_b, t_opsi_c, t_opsi_d, t_kunci]
                    success, err = write_sheet("BankSoal", row_data)
                    if success:
                        st.success("Butir soal berhasil ditambahkan!")
                        st.rerun()
                    else:
                        st.error(f"Gagal menyimpan soal: {err}")
                else:
                    st.warning("Mata Pelajaran dan Teks Pertanyaan wajib diisi.")

    with tab_bs3:
        st.markdown("#### ✏️ Edit atau Perbarui Soal")
        df_bs_edit = read_sheet("BankSoal")
        if not df_bs_edit.empty and 'Teks_Soal' in df_bs_edit.columns:
            soal_options = df_bs_edit['Teks_Soal'].dropna().tolist()
            pilih_soal_edit = st.selectbox("Pilih Soal yang akan diedit:", soal_options, key=f"{key_prefix}_pilih_edit")
            row_idx = df_bs_edit[df_bs_edit['Teks_Soal'] == pilih_soal_edit].index[0]
            current_data = df_bs_edit.iloc[row_idx]
            with st.form(f"form_edit_soal_{key_prefix}"):
                e_kelas = st.selectbox("Kelas", ["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6"], index=0, key=f"{key_prefix}_e_kls")
                e_mapel = st.selectbox("Mata Pelajaran", LIST_MAPEL, key=f"{key_prefix}_e_mpl")
                e_materi = st.text_input("Nama Materi", value=str(current_data.get('Nama_Materi', '')), key=f"{key_prefix}_e_mat")
                e_kategori = st.selectbox("Kategori Ujian", LIST_KATEGORI, key=f"{key_prefix}_e_kat")
                e_teks = st.text_area("Teks Pertanyaan", value=str(current_data.get('Teks_Soal', '')), key=f"{key_prefix}_e_teks")
                
                ec1, ec2 = st.columns(2)
                with ec1:
                    e_oa = st.text_input("Opsi A", value=str(current_data.get('Opsi_A', '')), key=f"{key_prefix}_e_oa")
                    e_oc = st.text_input("Opsi C", value=str(current_data.get('Opsi_C', '')), key=f"{key_prefix}_e_oc")
                with ec2:
                    e_ob = st.text_input("Opsi B", value=str(current_data.get('Opsi_B', '')), key=f"{key_prefix}_e_ob")
                    e_od = st.text_input("Opsi D", value=str(current_data.get('Opsi_D', '')), key=f"{key_prefix}_e_od")
                e_kunci = st.text_input("Kunci Jawaban (A/B/C/D)", value=str(current_data.get('Kunci', '')), key=f"{key_prefix}_e_kun")
                
                if st.form_submit_button("Simpan Perubahan Soal", type="primary"):
                    st.info("Silakan lakukan penyesuaian langsung di Google Spreadsheet untuk update data.")
        else:
            st.info("Belum ada data soal untuk diedit.")

    st.markdown("---")
    st.markdown("#### 📋 Data Bank Soal Terdaftar di Database")
    df_bs = read_sheet("BankSoal")
    st.dataframe(df_bs, use_container_width=True)

def render_rekap_nilai_panel(key_prefix):
    st.markdown("### 📊 Rekapitulasi Nilai Siswa (Berdasarkan Kategori Ujian)")
    df_nilai = read_sheet("Nilai")
    
    if not df_nilai.empty and 'Mapel' in df_nilai.columns:
        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            f_mapel = st.selectbox("Filter Mapel", ["Semua"] + df_nilai['Mapel'].dropna().unique().tolist(), key=f"{key_prefix}_f_mpl")
        with col_f2:
            f_kat = st.selectbox("Filter Kategori Ujian", ["Semua", "Latihan", "Ulangan Tengah Semester (UTS)", "Ulangan Semester (UAS)"], key=f"{key_prefix}_f_kat")
        with col_f3:
            f_kls = st.selectbox("Filter Kelas", ["Semua"] + df_nilai['Kelas'].dropna().unique().tolist(), key=f"{key_prefix}_f_kls")
            
        df_filtered = df_nilai.copy()
        if f_mapel != "Semua":
            df_filtered = df_filtered[df_filtered['Mapel'] == f_mapel]
        if f_kat != "Semua":
            df_filtered = df_filtered[df_filtered['Kategori_Ujian'] == f_kat]
        if f_kls != "Semua":
            df_filtered = df_filtered[df_filtered['Kelas'] == f_kls]
            
        st.markdown("---")
        st.dataframe(df_filtered, use_container_width=True)
        
        csv_rekap = df_filtered.to_csv(index=False).encode('utf-8')
        st.download_button("📥 Download Rekap Nilai (.CSV)", data=csv_rekap, file_name="rekap_nilai_cbt.csv", mime="text/csv", key=f"{key_prefix}_dl_rekap")
    else:
        st.info("Belum ada data nilai ujian yang masuk ke database.")

# ==========================================
# A. PORTAL SISWA
# ==========================================
if portal == "Portal Siswa":
    if st.session_state.user_siswa is None:
        st.markdown("""
            <div style='
                background: linear-gradient(135deg, #0d5c3b 0%, #1e3a8a 100%);
                padding: 3px;
                border-radius: 14px;
                box-shadow: 0 8px 20px rgba(0,0,0,0.12);
                margin-top: 5px;
                margin-bottom: 15px;
            '>
                <div style='
                    background: #ffffff;
                    padding: 18px;
                    border-radius: 12px;
                    text-align: center;
                '>
                    <h2 style='color: #0d5c3b; font-weight: 800; margin-bottom: 2px; font-size: 1.6rem;'>PINTU PENGISIAN SOAL</h2>
                    <h3 style='color: #1e3a8a; font-weight: 700; margin-top: 0; font-size: 1.2rem;'>MI ASHSHOLAHIYAH CILAMAYA</h3>
                    <p style='color: #64748b; font-size: 0.88rem; margin-bottom: 0;'>Silakan masukkan data diri dengan teliti dan penuh semangat untuk memulai ujian!</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.form("form_login_siswa"):
            st.markdown("#### 🔐 **Login Siswa**")
            col_s1, col_s2 = st.columns(2)
            with col_s1:
                pilih_kelas = st.selectbox("Pilih Kelas", ["Kelas 1", "Kelas 2", "Kelas 3", "Kelas 4", "Kelas 5", "Kelas 6"])
            with col_s2:
                pilih_rombel = st.selectbox("Pilih Rombel", ["A", "B", "C"])
                
            col_s3, col_s4 = st.columns(2)
            with col_s3:
                no_peserta = st.text_input("Nomor Peserta")
            with col_s4:
                pass_siswa = st.text_input("Password / Sandi", type="password")
            
            st.markdown("<br>", unsafe_allow_html=True)
            submitted = st.form_submit_button("Masuk Ruang Ujian", type="primary", use_container_width=True)
            if submitted:
                df_siswa = read_sheet("Siswa")
                if not df_siswa.empty and 'no_peserta' in df_siswa.columns:
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
    else:
        siswa = st.session_state.user_siswa

        if not st.session_state.sedang_ujian:
            st.markdown("### 🪪 Kartu Identitas Peserta Ujian")
            
            c_foto, c_info = st.columns([1, 3])
            with c_foto:
                st.markdown("""
                    <div style='
                        border: 2px dashed #0d5c3b;
                        border-radius: 10px;
                        height: 130px;
                        display: flex;
                        align-items: center;
                        justify-content: center;
                        background: #f8fafc;
                        color: #64748b;
                        font-weight: bold;
                    '>
                        FOTO SISWA
                    </div>
                """, unsafe_allow_html=True)
            with c_info:
                st.markdown(f"""
                    <div style='padding: 10px; background: #ffffff; border: 1px solid #e2e8f0; border-radius: 10px;'>
                        <h4 style='color: #0d5c3b; margin-top:0; margin-bottom: 8px;'><b>Nama:</b> {str(siswa.get('nama', '')).upper()}</h4>
                        <p style='margin: 4px 0; font-size: 1rem;'><b>Kelas:</b> {siswa.get('kelas', '')} - Rombel {siswa.get('rombel', '')}</p>
                        <p style='margin: 4px 0; font-size: 1rem;'><b>Nomor Peserta:</b> {siswa.get('no_peserta', '')}</p>
                    </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            col_menu1, col_menu2 = st.columns(2)
            with col_menu1:
                st.markdown("#### 📁 Ujian Tersedia")
                df_bank = read_sheet("BankSoal")
                if not df_bank.empty and 'Mapel' in df_bank.columns and 'Kelas' in df_bank.columns:
                    df_kelas = df_bank[df_bank['Kelas'].astype(str).str.lower() == str(siswa.get('kelas', '')).lower()]
                    if df_kelas.empty:
                        df_kelas = df_bank 
                        
                    mapel_list = df_kelas['Mapel'].unique().tolist()
                    pilih_mapel = st.selectbox("Pilih Mata Pelajaran:", mapel_list, key="pil_mapel_ds")
                    
                    materi_list = df_kelas[df_kelas['Mapel'] == pilih_mapel]['Nama_Materi'].unique().tolist()
                    pilih_materi = st.selectbox("Pilih Nama Materi:", materi_list, key="pil_mat_ds")
                    
                    kategori_list = df_kelas[(df_kelas['Mapel'] == pilih_mapel) & (df_kelas['Nama_Materi'] == pilih_materi)]['Kategori_Ujian'].unique().tolist()
                    pilih_kategori = st.selectbox("Pilih Kategori Ujian:", kategori_list, key="pil_kat_ds")
                    
                    st.markdown("<br>", unsafe_allow_html=True)
                    if st.button("🚀 Mulai Mengerjakan Ujian", type="primary", use_container_width=True):
                        st.session_state.sedang_ujian = True
                        st.session_state.mapel_ujian = pilih_mapel
                        st.session_state.materi_ujian = pilih_materi
                        st.session_state.kategori_ujian = pilih_kategori
                        st.session_state.q_page = 0
                        if "jawaban_siswa" not in st.session_state:
                            st.session_state.jawaban_siswa = {}
                        st.rerun()
                else:
                    st.warning("Belum ada data Bank Soal yang tersedia di database.")

            with col_menu2:
                st.markdown("#### 📊 Riwayat Nilai Saya")
                df_nilai_s = read_sheet("Nilai")
                if not df_nilai_s.empty and 'No_Peserta' in df_nilai_s.columns:
                    my_nilai = df_nilai_s[df_nilai_s['No_Peserta'].astype(str) == str(siswa.get('no_peserta', ''))]
                    if not my_nilai.empty:
                        st.dataframe(my_nilai[['Mapel', 'Nama_Materi', 'Kategori_Ujian', 'Nilai', 'Tanggal']], use_container_width=True)
                    else:
                        st.info("Belum ada riwayat ujian yang diselesaikan.")
                else:
                    st.info("Belum ada data nilai.")

            st.markdown("---")
            if st.button("🚪 Keluar / Logout", type="secondary"):
                st.session_state.user_siswa = None
                st.session_state.sedang_ujian = False
                st.rerun()

        else:
            st.markdown(f"""
                <div class='profil-box'>
                    <span style='font-size: 1.05rem; color: #0d5c3b; font-weight: bold;'>👤 {str(siswa.get('nama', '')).upper()}</span> | 
                    <span><b>Kelas:</b> {siswa.get('kelas')} ({siswa.get('rombel')})</span> | 
                    <span><b>No:</b> {siswa.get('no_peserta')}</span> | 
                    <span style='color: #1e3a8a;'><b>Ujian:</b> {st.session_state.mapel_ujian} - {st.session_state.materi_ujian} ({st.session_state.kategori_ujian})</span>
                </div>
            """, unsafe_allow_html=True)

            df_bank = read_sheet("BankSoal")
            if not df_bank.empty and 'Mapel' in df_bank.columns and 'Kelas' in df_bank.columns:
                soal_aktif = df_bank[
                    (df_bank['Kelas'].astype(str).str.lower() == str(siswa.get('kelas', '')).lower()) &
                    (df_bank['Mapel'] == st.session_state.mapel_ujian) & 
                    (df_bank['Nama_Materi'] == st.session_state.materi_ujian) & 
                    (df_bank['Kategori_Ujian'] == st.session_state.kategori_ujian)
                ].reset_index(drop=True)

                if soal_aktif.empty:
                    soal_aktif = df_bank[
                        (df_bank['Mapel'] == st.session_state.mapel_ujian) & 
                        (df_bank['Nama_Materi'] == st.session_state.materi_ujian) & 
                        (df_bank['Kategori_Ujian'] == st.session_state.kategori_ujian)
                    ].reset_index(drop=True)
            else:
                soal_aktif = pd.DataFrame()

            if not soal_aktif.empty:
                total_soal = len(soal_aktif)
                if "q_page" not in st.session_state:
                    st.session_state.q_page = 0
                if "jawaban_siswa" not in st.session_state:
                    st.session_state.jawaban_siswa = {}

                col_soal_kiri, col_peta_kanan = st.columns([3, 1])

                with col_soal_kiri:
                    curr_page = st.session_state.q_page
                    row_soal = soal_aktif.iloc[curr_page]

                    st.markdown(f"#### 📄 Soal No. {curr_page + 1} dari {total_soal}")
                    st.markdown(f"<div class='soal-teks'>{row_soal.get('Teks_Soal', '')}</div>", unsafe_allow_html=True)

                    opsi_list_raw = [
                        ("A", row_soal.get('Opsi_A', '')),
                        ("B", row_soal.get('Opsi_B', '')),
                        ("C", row_soal.get('Opsi_C', '')),
                        ("D", row_soal.get('Opsi_D', ''))
                    ]
                    opsi_valid = [(huruf, teks) for huruf, teks in opsi_list_raw if str(teks).strip() != ""]
                    if not opsi_valid:
                        opsi_valid = [("A", "A"), ("B", "B"), ("C", "C"), ("D", "D")]

                    format_opsi = [f"{huruf}. {teks}" for huruf, teks in opsi_valid]

                    saved_ans = st.session_state.jawaban_siswa.get(curr_page, "")
                    default_idx = 0
                    if saved_ans in format_opsi:
                        default_idx = format_opsi.index(saved_ans)

                    ans_key = f"ans_soal_{curr_page}"
                    val_terpilih = st.radio("Pilih Opsi Jawaban:", format_opsi, key=ans_key, index=default_idx)

                    if val_terpilih:
                        st.session_state.jawaban_siswa[curr_page] = val_terpilih

                    st.markdown("<br>", unsafe_allow_html=True)
                    
                    c_btn_l, c_btn_r = st.columns(2)
                    with c_btn_l:
                        if curr_page > 0:
                            if st.button("⬅️ Sebelumnya", use_container_width=True):
                                st.session_state.q_page -= 1
                                st.rerun()
                    with c_btn_r:
                        if curr_page < total_soal - 1:
                            if st.button("Selanjutnya ➡️", use_container_width=True):
                                st.session_state.q_page += 1
                                st.rerun()

                    st.markdown("<hr>", unsafe_allow_html=True)
                    if st.button("✅ Selesai & Kirim Ujian", type="primary", use_container_width=True):
                        benar = 0
                        for idx, s_row in soal_aktif.iterrows():
                            ans = st.session_state.jawaban_siswa.get(idx, "")
                            if ans:
                                huruf_pilih = ans.split(".")[0].strip().upper()
                                kunci_asli = str(s_row.get('Kunci', '')).strip().upper()
                                if huruf_pilih == kunci_asli:
                                    benar += 1
                        
                        nilai_akhir = round((benar / total_soal) * 100, 2) if total_soal > 0 else 0
                        tgl_sekarang = datetime.now().strftime('%Y-%m-%d %H:%M')

                        row_nilai = [
                            str(siswa.get('no_peserta', '')),
                            str(siswa.get('nama', '')).upper(),
                            str(siswa.get('kelas', '')),
                            str(st.session_state.mapel_ujian),
                            str(st.session_state.materi_ujian),
                            str(st.session_state.kategori_ujian),
                            int(total_soal),
                            int(benar),
                            float(nilai_akhir),
                            str(tgl_sekarang)
                        ]
                        write_sheet("Nilai", row_nilai)

                        st.balloons()
                        st.success(f"Ujian Selesai! Perolehan Nilai Anda: {nilai_akhir} (Benar {benar} dari {total_soal} soal)")
                        st.session_state.sedang_ujian = False
                        st.session_state.jawaban_siswa = {}
                        st.rerun()

                with col_peta_kanan:
                    st.markdown("#### 🗺️ Butir Soal")
                    st.caption("Biru: Terisi | Abu: Belum")
                    
                    peta_cols = st.columns(4)
                    for idx in range(total_soal):
                        c_idx = idx % 4
                        with peta_cols[c_idx]:
                            status_jawab = st.session_state.jawaban_siswa.get(idx)
                            btn_type = "primary" if status_jawab else "secondary"
                            if st.button(f"{idx+1}", key=f"grid_peta_{idx}", type=btn_type, use_container_width=True):
                                st.session_state.q_page = idx
                                st.rerun()
            else:
                st.warning("Belum ada butir soal untuk materi ujian ini.")
                if st.button("Kembali"):
                    st.session_state.sedang_ujian = False
                    st.rerun()

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
                if not df_guru.empty and 'nama_guru' in df_guru.columns:
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
                        st.session_state.user_guru = {"nama_guru": "Guru Kelas", "kelas_ajar": "Kelas 5"}
                        st.rerun()
                    else:
                        st.error("Data guru belum terhubung.")
    else:
        guru = st.session_state.user_guru
        st.subheader(f"👨‍🏫 Dashboard Guru: {guru.get('nama_guru', 'Guru')} ({guru.get('kelas_ajar', '')})")
        
        if st.button("Logout Guru"):
            st.session_state.user_guru = None
            st.rerun()
            
        t1, t2, t3, t4 = st.tabs(["Kelola Bank Soal", "Pelaksanaan Ujian", "Cetak Kartu Ujian", "Rekap Nilai"])
        
        with t1:
            render_bank_soal_manager("guru")

        with t2:
            st.markdown("### 🚀 Atur Pelaksanaan Ujian & Ceklis Pemilihan Soal")
            df_b = read_sheet("BankSoal")
            if not df_b.empty and 'Kelas' in df_b.columns and len(df_b) > 0:
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    kls_list = df_b['Kelas'].dropna().unique().tolist()
                    p_kls = st.selectbox("Pilih Kelas", kls_list if kls_list else ["-"], key="g_kls")
                    
                    mapel_list = df_b[df_b['Kelas'] == p_kls]['Mapel'].dropna().unique().tolist() if p_kls != "-" else []
                    p_mapel = st.selectbox("Pilih Mata Pelajaran", mapel_list if mapel_list else ["-"], key="g_mapel")
                    
                    mat_list = df_b[(df_b['Kelas'] == p_kls) & (df_b['Mapel'] == p_mapel)]['Nama_Materi'].dropna().unique().tolist() if p_mapel != "-" else []
                    p_mat = st.selectbox("Pilih Nama Materi", mat_list if mat_list else ["-"], key="g_mat")
                with col_g2:
                    p_kat = st.selectbox("Pilih Kategori Ujian", LIST_KATEGORI, key="g_kat")
                    p_dur = st.text_input("Durasi Ujian (Menit)", "90", key="g_dur")
                    p_stat = st.selectbox("Status Pelaksanaan", ["Dibuka (Live)", "Ditutup"], key="g_stat")
                
                st.markdown("---")
                st.markdown("#### ☑️ Ceklis Pemilihan Soal untuk Ujian Ini")
                soal_filter_g = df_b[(df_b['Kelas'] == p_kls) & (df_b['Mapel'] == p_mapel) & (df_b['Nama_Materi'] == p_mat) & (df_b['Kategori_Ujian'] == p_kat)]
                
                if not soal_filter_g.empty:
                    selected_indices = []
                    for s_idx, s_row in soal_filter_g.reset_index(drop=True).iterrows():
                        is_checked = st.checkbox(f"Soal {s_idx+1}: {s_row.get('Teks_Soal', '')[:75]}...", value=True, key=f"chk_g_{s_idx}")
                        if is_checked:
                            selected_indices.append(s_idx)
                    
                    preview_soal = soal_filter_g.iloc[selected_indices]
                    st.info(f"Total soal terpilih untuk diujikan: **{len(preview_soal)} Soal**")
                    
                    col_btn1, col_btn2 = st.columns(2)
                    with col_btn1:
                        if st.button("Simpan & Siarkan Ujian ke Siswa", type="primary", key="g_siar"):
                            st.success("Ujian berhasil disiarkan ke portal siswa!")
                    with col_btn2:
                        if not preview_soal.empty:
                            pdf_text = f"CBT MI ASHSHOLAHIYAH CILAMAYA\nMAPEL: {p_mapel} | MATERI: {p_mat} | KATEGORI: {p_kat}\n" + "="*50 + "\n\n"
                            for idx, row in preview_soal.reset_index(drop=True).iterrows():
                                pdf_text += f"{idx+1}. {row.get('Teks_Soal', '')}\n"
                                pdf_text += f"   A. {row.get('Opsi_A', '')}\n   B. {row.get('Opsi_B', '')}\n   C. {row.get('Opsi_C', '')}\n   D. {row.get('Opsi_D', '')}\n"
                                pdf_text += f"   Kunci: {row.get('Kunci', '')}\n\n"
                            st.download_button(
                                label="📄 Download Soal (.TXT / Arsip PDF)",
                                data=pdf_text.encode('utf-8'),
                                file_name=f"Soal_{p_mapel}_{p_mat}_{p_kat}.txt".replace(" ", "_"),
                                mime="text/plain",
                                key="g_dl_pdf"
                            )
                else:
                    st.warning("Tidak ada soal yang cocok dengan filter tersebut.")
            else:
                st.warning("Belum ada data Bank Soal di Google Sheets.")

        with t3:
            st.markdown("### 🖨️ Cetak Kartu Peserta Ujian")
            df_sis = read_sheet("Siswa")
            if not df_sis.empty and 'kelas' in df_sis.columns:
                kls_kartu = st.selectbox("Pilih Kelas untuk Cetak Kartu", df_sis['kelas'].dropna().unique().tolist())
                sis_filtered = df_sis[df_sis['kelas'].astype(str).str.lower() == str(kls_kartu).lower()]
                
                if st.button("Tampilkan Kartu Ujian", type="primary"):
                    for _, s in sis_filtered.iterrows():
                        st.markdown(f"""
                        <div class='kartu-container'>
                            <h4 style='text-align: center; color: #0d5c3b; margin-bottom: 5px;'>MI ASHSHOLAHIYAH CILAMAYA</h4>
                            <p style='text-align: center; font-size: 0.85rem; color: #555; margin-top: 0;'>KARTU PESERTA UJIAN CBT</p>
                            <hr style='margin: 5px 0;'>
                            <table style='width: 100%; font-size: 0.9rem;'>
                                <tr><td><b>No Peserta</b></td><td>: {s.get('no_peserta', '')}</td></tr>
                                <tr><td><b>Nama Siswa</b></td><td>: {s.get('nama', '')}</td></tr>
                                <tr><td><b>Kelas / Rombel</b></td><td>: {s.get('kelas', '')} - {s.get('rombel', '')}</td></tr>
                                <tr><td><b>Password</b></td><td>: <code>{s.get('password', '')}</code></td></tr>
                            </table>
                            <p style='text-align: right; font-size: 0.75rem; color: #777; margin-bottom: 0; margin-top: 10px;'>Panitia CBT MI Ashsholahiyah</p>
                        </div>
                        """, unsafe_allow_html=True)
            else:
                st.warning("Belum ada data siswa di database.")

        with t4:
            render_rekap_nilai_panel("guru")

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
            
        ta1, ta2, ta3, ta4 = st.tabs(["Database Siswa", "Database Guru", "Kelola Bank Soal", "Rekap Nilai"])
        
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
                            st.success(f"Siswa {nm_in.upper()} tersimpan!")
                            st.rerun()
        
        with ta2:
            st.markdown("### Database Guru Kelas")
            st.dataframe(read_sheet("Guru"), use_container_width=True)
            
            st.markdown("---")
            st.markdown("#### Tambah Guru Baru")
            with st.form("form_add_g"):
                ng_in = st.text_input("Nama Guru")
                ka_in = st.text_input("Kelas Ajar")
                pw_in = st.text_input("Password Guru")
                if st.form_submit_button("Simpan Guru ke Google Sheets"):
                    if ng_in:
                        if write_sheet("Guru", [ng_in, ka_in, pw_in, "offline"]):
                            st.success(f"Guru {ng_in} tersimpan!")
                            st.rerun()
                            
        with ta3:
            render_bank_soal_manager("admin")

        with ta4:
            render_rekap_nilai_panel("admin")
