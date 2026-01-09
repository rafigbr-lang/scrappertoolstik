import streamlit as st
import pandas as pd

st.set_page_config(page_title="TikTok GMV Recapper", layout="wide")

st.title("📊 TikTok Campaign GMV Recapper")
st.write("Unggah beberapa file campaign untuk melihat total performa creator.")

# 1. Sidebar untuk Pengaturan Kolom
st.sidebar.header("Pengaturan Kolom")
name_col = st.sidebar.text_input("Nama Kolom Creator", value="Creator Name")
gmv_col = st.sidebar.text_input("Nama Kolom GMV", value="GMV")

# 2. Upload File (Bisa banyak file sekaligus)
uploaded_files = st.file_uploader("Pilih file Excel atau CSV", accept_multiple_files=True, type=['csv', 'xlsx'])

if uploaded_files:
    all_data = []
    
    for file in uploaded_files:
        try:
            if file.name.endswith('.csv'):
                df = pd.read_csv(file)
            else:
                df = pd.read_excel(file)
            
            # Tambahkan kolom keterangan nama file agar tahu dari campaign mana
            df['Source Campaign'] = file.name
            all_data.append(df)
        except Exception as e:
            st.error(f"Gagal membaca file {file.name}: {e}")

    if all_data:
        # Gabungkan semua data menjadi satu dataframe
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Bersihkan data GMV (jika ada karakter mata uang atau koma)
        if combined_df[gmv_col].dtype == 'object':
            combined_df[gmv_col] = combined_df[gmv_col].replace(r'[\$,R p.]', '', regex=True).astype(float)

        # 3. Fitur Pencarian & Rekap
        st.divider()
        search_query = st.text_input("🔍 Cari Nama Creator / Username (Kosongkan untuk lihat semua)")

        # Grouping Data
        recap_df = combined_df.groupby(name_col).agg({
            gmv_col: 'sum',
            'Source Campaign': 'count'
        }).rename(columns={'Source Campaign': 'Total Campaign Content'}).reset_index()

        # Filter berdasarkan pencarian
        if search_query:
            recap_df = recap_df[recap_df[name_col].str.contains(search_query, case=False, na=False)]

        # 4. Tampilan Hasil
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.subheader("Tabel Rekapitulasi")
            st.dataframe(recap_df.sort_values(by=gmv_col, ascending=False), use_container_width=True)

        with col2:
            st.subheader("Total GMV Keseluruhan")
            total_all = recap_df[gmv_col].sum()
            st.metric("Grand Total", f"Rp {total_all:,.0f}")
            st.write(f"Jumlah Creator Unik: {len(recap_df)}")

        # 5. Download Hasil Rekap
        csv = recap_df.to_csv(index=False).encode('utf-8')
        st.download_button(
            label="📥 Download Hasil Rekap (.csv)",
            data=csv,
            file_name="recap_gmv_tiktok.csv",
            mime="text/csv",
        )
else:
    st.info("Silakan unggah satu atau lebih file campaign untuk memulai.")
