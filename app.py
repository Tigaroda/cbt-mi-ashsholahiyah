# ==========================================
# A. PORTAL SISWA (TAMPILAN UTAMA DIPERCANTIK)
# ==========================================
if portal == "Portal Siswa":
    if st.session_state.user_siswa is None:
        # Kotak/Card Utama dengan Bingkai Warna Bergradasi & Estetik
        st.markdown("""
            <div style='
                background: linear-gradient(135deg, #0d5c3b 0%, #1e3a8a 100%);
                padding: 3px;
                border-radius: 16px;
                box-shadow: 0 10px 25px rgba(0,0,0,0.15);
                margin-top: 10px;
                margin-bottom: 20px;
            '>
                <div style='
                    background: #ffffff;
                    padding: 25px;
                    border-radius: 14px;
                '>
                    <div style='text-align: center; margin-bottom: 20px;'>
                        <h2 style='color: #0d5c3b; font-weight: 800; margin-bottom: 5px;'>pintu pengisian soal</h2>
                        <h3 style='color: #1e3a8a; font-weight: 700; margin-top: 0;'>MI ASHSHOLAHIYAH CILAMAYA</h3>
                        <p style='color: #64748b; font-size: 0.9rem;'>Silakan masukkan data diri dengan teliti dan penuh semangat untuk memulai ujian!</p>
                    </div>
                </div>
            </div>
        """, unsafe_allow_html=True)

        with st.form("form_login_siswa"):
            st.markdown("#### 🔐 **Login Siswa**")
            
            # Susunan berdampingan sesuai sketsa tulisan tangan
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
            
            # Tombol Masuk Full Lebar dengan Warna Elegan
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
                        st.success(f"Selamat Datang, {cek.iloc[0]['nama']}! Mari kerjakan dengan jujur.")
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
        # (Bagian setelah siswa berhasil login tetap berjalan seperti biasa)
        ...
