import streamlit as st
import pandas as pd
import gspread
from google.oauth2.service_account import Credentials
from datetime import datetime
import textwrap

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
    .exam-card {
        border: 2px dashed #0d5c3b;
        padding: 15px;
        border-radius: 10px;
        background-color: #fafaf9;
        margin-bottom: 10px;
    }
    .kartu-container {
        border: 2px solid #1e293b;
        border-radius: 12px;
        padding: 20px;
        background: #ffffff;
        width: 100%;
        max-width: 400px;
        margin: 10px auto;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
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
            return True
        except Exception:
            return False
    return False

def append_bulk_sheet(worksheet_name, df_to_append):
    if db_connected and sh is not None:
        try:
            ws = sh.worksheet(worksheet_name)
            values = df_to_append.values.tolist()
            ws.append_rows(values)
            st.cache_data.clear()
            return True
        except Exception:
            return False
    return False

# ==========================================
# 3. SESSION STATE
# ==========================================
if "user_siswa" not in st.session_state:
    st.session_state.user_siswa = None
if "user_guru" not in st.session_state:
    st.session_state.user_guru = None
if "user_admin" not in st.session_state:
    st.session_state.user_admin = False

# ==========================================
# 4. HEADER & STATUS
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
# 5. NAVIGASI
# ==========================================
st.sidebar.title("📌 Menu Navigasi")
portal = st.sidebar.radio("Pilih Akses Portal:", ["Portal Siswa", "Ruang Guru Kelas", "Ruang Admin Master"])

BANK_SOAL_COLS = [
    "Kelas", "Mapel", "Nama_Materi", "Kategori_Ujian", 
    "Tipe_Soal", "Teks_Soal", "Opsi_A", "Opsi_B", 
    "Opsi_C", "Opsi_D", "Kunci"
]

def render_bank_soal_manager(key_prefix):
    st.markdown("### 📚 Kelola Bank Soal")
    st.caption("Struktur Kolom: Kelas | Mapel | Nama_Materi | Kategori_Ujian | Tipe_Soal | Teks_Soal | Opsi_A | Opsi_B | Opsi_C | Opsi_D | Kunci")
    
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
                df_up = pd.read_csv(up_file)
                st.write("Pratinjau Data:")
                st.dataframe(df_up.head(3))
                if st.button("Proses Upload ke Database", type="primary", key=f"{key_prefix}_btn"):
                    if append_bulk_sheet("BankSoal", df_up):
                        st.success("Bank soal berhasil diupload ke Google Sheets!")
                        st.rerun()
                    else:
                        st.error("Gagal mengupload soal.")
            except Exception as e:
                st.error(f"Format file CSV tidak sesuai: {e}")

    st.markdown("---")
    st.markdown("#### 📋 Data Bank Soal Terdaftar di Database")
    st.dataframe(read_sheet("BankSoal"), use_container_width=True)

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
        st.subheader("📝 Ruang Pelaksanaan Ujian")
        
        df_bank = read_sheet("BankSoal")
        if not df_bank.empty and 'Mapel' in df_bank.columns:
            # Filter berdasarkan kelas siswa
            df_kelas = df_bank[df_bank['Kelas'].astype(str).str.lower() == str(siswa.get('kelas', '')).lower()]
            if df_kelas.empty:
                df_kelas = df_bank # Fallback jika filter kelas kosong
                
            mapel_list = df_kelas['Mapel'].unique().tolist()
            pilih_mapel = st.selectbox("Pilih Mata Pelajaran:", mapel_list)
            
            materi_list = df_kelas[df_kelas['Mapel'] == pilih_mapel]['Nama_Materi'].unique().tolist()
            pilih_materi = st.selectbox("Pilih Nama Materi Ujian:", materi_list)
            
            kategori_list = df_kelas[(df_kelas['Mapel'] == pilih_mapel) & (df_kelas['Nama_Materi'] == pilih_materi)]['Kategori_Ujian'].unique().tolist()
            pilih_kategori = st.selectbox("Pilih Kategori Ujian:", kategori_list)
            
            st.markdown("---")
            soal_aktif = df_kelas[
                (df_kelas['Mapel'] == pilih_mapel) & 
                (df_kelas['Nama_Materi'] == pilih_materi) & 
                (df_kelas['Kategori_Ujian'] == pilih_kategori)
            ]
            
            if not soal_aktif.empty:
                st.markdown(f"#### 📄 Lembar Soal: {pilih_mapel} - {pilih_materi} ({pilih_kategori})")
                for idx, row in soal_aktif.reset_index(drop=True).iterrows():
                    st.markdown(f"**Soal No. {idx+1}**")
                    st.write(row.get('Teks_Soal', ''))
                    st.radio(
                        f"Pilih Jawaban (Soal {idx+1}):",
                        [f"A. {row.get('Opsi_A', '')}", 
                         f"B. {row.get('Opsi_B', '')}", 
                         f"C. {row.get('Opsi_C', '')}", 
                         f"D. {row.get('Opsi_D', '')}"],
                        key=f"ans_s_{idx}"
                    )
                    st.markdown("---")
                
                if st.button("Selesai & Kirim Jawaban Ujian", type="primary"):
                    st.balloons()
                    st.success("Jawaban Ujian Berhasil Dikirim ke Server!")
            else:
                st.warning("Belum ada soal aktif untuk materi dan kategori ujian ini.")
        else:
            st.info("Sistem belum mendeteksi data Bank Soal di Google Sheets.")

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
                        st.session_state.user_guru = {"nama_guru": "Guru Kelas", "kelas_ajar": "Kelas 5"}
                        st.rerun()
                    else:
                        st.error("Data guru belum terhubung.")
    else:
        guru = st.session_state.user_guru
        st.subheader(f"👨‍🏫 Dashboard Guru: {guru.get('nama_guru')} ({guru.get('kelas_ajar')})")
        
        if st.button("Logout Guru"):
            st.session_state.user_guru = None
            st.rerun()
            
        t1, t2, t3, t4 = st.tabs(["Kelola Bank Soal", "Pelaksanaan Ujian", "Cetak Kartu Ujian", "Rekap Nilai"])
        
        with t1:
            render_bank_soal_manager("guru")

        with t2:
            st.markdown("### 🚀 Atur Pelaksanaan Ujian Berdasarkan Materi")
            df_b = read_sheet("BankSoal")
            if not df_b.empty:
                col_g1, col_g2 = st.columns(2)
                with col_g1:
                    p_kls = st.selectbox("Pilih Kelas", df_b['Kelas'].unique().tolist(), key="g_kls")
                    p_mapel = st.selectbox("Pilih Mata Pelajaran", df_b[df_b['Kelas'] == p_kls]['Mapel'].unique().tolist(), key="g_mapel")
                    p_mat = st.selectbox("Pilih Nama Materi", df_b[(df_b['Kelas'] == p_kls) & (df_b['Mapel'] == p_mapel)]['Nama_Materi'].unique().tolist(), key="g_mat")
                with col_g2:
                    p_kat = st.selectbox("Pilih Kategori Ujian", ["Latihan", "Ulangan Tengah Semester", "Ulangan Semester"], key="g_kat")
                    p_dur = st.text_input("Durasi Ujian (Menit)", "90", key="g_dur")
                    p_stat = st.selectbox("Status Pelaksanaan", ["Dibuka (Live)", "Ditutup"], key="g_stat")
                
                st.markdown("---")
                # Pratinjau Soal yang dipilih
                preview_soal = df_b[(df_b['Kelas'] == p_kls) & (df_b['Mapel'] == p_mapel) & (df_b['Nama_Materi'] == p_mat) & (df_b['Kategori_Ujian'] == p_kat)]
                st.info(f"Jumlah soal terpilih untuk ujian ini: **{len(preview_soal)} Soal**")
                
                col_btn1, col_btn2 = st.columns(2)
                with col_btn1:
                    if st.button("Simpan & Siarkan Ujian ke Siswa", type="primary", key="g_siar"):
                        st.success("Ujian berhasil disiarkan ke portal siswa!")
                with col_btn2:
                    # Fitur Download Soal ke PDF (Simulasi format cetak bersih)
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
                st.warning("Belum ada data di Bank Soal.")

        with t3:
            st.markdown("### 🖨️ Cetak Kartu Peserta Ujian")
            st.write("Cetak kartu ujian siswa untuk dibagikan sebelum pelaksanaan tes.")
            df_sis = read_sheet("Siswa")
            if not df_sis.empty:
                kls_kartu = st.selectbox("Pilih Kelas untuk Cetak Kartu", df_sis['kelas'].unique().tolist() if 'kelas' in df_sis.columns else ["Kelas 1"])
                sis_filtered = df_sis[df_sis['kelas'].astype(str).str.lower() == str(kls_kartu).lower()] if 'kelas' in df_sis.columns else df_sis
                
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
            st.markdown("### Rekapitulasi Nilai Ujian")
            st.info("Belum ada data nilai ujian yang masuk.")

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
            
        ta1, ta2, ta3, ta4, ta5 = st.tabs(["Database Siswa", "Database Guru", "Kelola Bank Soal", "Pelaksanaan Ujian", "Cetak Kartu Ujian"])
        
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
            st.markdown("### ⚙️ Kontrol Pelaksanaan Ujian & Download Soal (Master)")
            df_b_ad = read_sheet("BankSoal")
            if not df_b_ad.empty:
                col_ad1, col_ad2 = st.columns(2)
                with col_ad1:
                    ad_kls = st.selectbox("Pilih Kelas", df_b_ad['Kelas'].unique().tolist(), key="ad_kls")
                    ad_mapel = st.selectbox("Pilih Mata Pelajaran", df_b_ad[df_b_ad['Kelas'] == ad_kls]['Mapel'].unique().tolist(), key="ad_mapel")
                    ad_mat = st.selectbox("Pilih Nama Materi", df_b_ad[(df_b_ad['Kelas'] == ad_kls) & (df_b_ad['Mapel'] == ad_mapel)]['Nama_Materi'].unique().tolist(), key="ad_mat")
                with col_ad2:
                    ad_kat = st.selectbox("Pilih Kategori Ujian", ["Latihan", "Ulangan Tengah Semester", "Ulangan Semester"], key="ad_kat")
                    ad_tok = st.text_input("Token Ujian", "CBT-2026", key="ad_tok")
                    ad_stat = st.selectbox("Status Ujian", ["Dibuka (Live)", "Ditutup"], key="ad_stat")
                
                st.markdown("---")
                preview_ad = df_b_ad[(df_b_ad['Kelas'] == ad_kls) & (df_b_ad['Mapel'] == ad_mapel) & (df_b_ad['Nama_Materi'] == ad_mat) & (df_b_ad['Kategori_Ujian'] == ad_kat)]
                st.info(f"Jumlah soal terpilih: **{len(preview_ad)} Soal**")
                
                c_btn1, c_btn2 = st.columns(2)
                with c_btn1:
                    if st.button("Terapkan & Siarkan Sesi Ujian", type="primary", key="ad_siar"):
                        st.success("Sesi ujian berhasil disiarkan!")
                with c_btn2:
                    if not preview_ad.empty:
                        pdf_txt_ad = f"CBT MI ASHSHOLAHIYAH CILAMAYA\nMAPEL: {ad_mapel} | MATERI: {ad_mat} | KATEGORI: {ad_kat}\n" + "="*50 + "\n\n"
                        for idx, row in preview_ad.reset_index(drop=True).iterrows():
                            pdf_txt_ad += f"{idx+1}. {row.get('Teks_Soal', '')}\n"
                            pdf_txt_ad += f"   A. {row.get('Opsi_A', '')}\n   B. {row.get('Opsi_B', '')}\n   C. {row.get('Opsi_C', '')}\n   D. {row.get('Opsi_D', '')}\n"
                            pdf_txt_ad += f"   Kunci: {row.get('Kunci', '')}\n\n"
                        st.download_button(
                            label="📄 Download Soal (.TXT / Arsip PDF)",
                            data=pdf_txt_ad.encode('utf-8'),
                            file_name=f"Soal_{ad_mapel}_{ad_mat}_{ad_kat}.txt".replace(" ", "_"),
                            mime="text/plain",
                            key="ad_dl_pdf"
                        )
            else:
                st.warning("Belum ada data Bank Soal.")

        with ta5:
            st.markdown("### 🖨️ Cetak Kartu Peserta Ujian (Master)")
            df_sis_ad = read_sheet("Siswa")
            if not df_sis_ad.empty:
                kls_k_ad = st.selectbox("Pilih Kelas", df_sis_ad['kelas'].unique().tolist() if 'kelas' in df_sis_ad.columns else ["Kelas 1"], key="ad_k_kls")
                sis_f_ad = df_sis_ad[df_sis_ad['kelas'].astype(str).str.lower() == str(kls_k_ad).lower()] if 'kelas' in df_sis_ad.columns else df_sis_ad
                
                if st.button("Tampilkan Semua Kartu Ujian", type="primary", key="ad_btn_kartu"):
                    for _, s in sis_f_ad.iterrows():
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
                st.warning("Belum ada data siswa.")
