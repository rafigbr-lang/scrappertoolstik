import streamlit as st
import pandas as pd

st.set_page_config(page_title="TikTok GMV Bulk Search", layout="wide")

st.title("📊 TikTok Campaign GMV Bulk Recapper")
st.write("Upload file campaign, lalu masukkan daftar username untuk filter cepat.")

# 1. Sidebar - Pengaturan Nama Kolom
st.sidebar.header("Pengaturan Kolom")
name_col = st.sidebar.text_input("Nama Kolom Username/Creator", value="Creator Name")
gmv_col = st.sidebar.text_input("Nama Kolom GMV", value="GMV")

# 2. Upload File (Multi-file)
uploaded_files = st.file_uploader("Pilih file Excel atau CSV", accept_multiple_files=True, type=['csv', 'xlsx'])

if uploaded_files:
    all_data = []
    for file in uploaded_files:
        try:
            df = pd.read_csv(file) if file.name.endswith('.csv') else pd.read_excel(file)
            df['Source Campaign'] = file.name # Tandai asal file
            all_data.append(df)
        except Exception as e:
            st.error(f"Gagal membaca file {file.name}: {e}")

    if all_data:
        combined_df = pd.concat(all_data, ignore_index=True)
        
        # Bersihkan format GMV agar jadi angka
        if combined_df[gmv_col].dtype == 'object':
            combined_df[gmv_col] = combined_df[gmv_col].replace(r'[\$,R p.]', '', regex=True).astype(float)

        st.divider()

        # 3. Fitur Input Banyak Username (Copy-Paste)
        st.subheader("🔍 Pencarian Banyak Username")
        input_usernames = st.text_area("Copy-paste daftar username di sini (satu username per baris):", height=150)

        # Proses daftar username
        list_search = [name.strip() for name in input_usernames.split('\n') if name.strip() != ""]

        # 4. Grouping Data (Total GMV per Creator)
        recap_df = combined_df.groupby(name_col).agg({
            gmv_col: 'sum',
            'Source Campaign': lambda x: ", ".join(x.unique()) # List campaign yang diikuti
        }).reset_index()

        # 5. Filter Berdasarkan List Username
        if list_search:
            # Menggunakan isin() untuk mencocokkan banyak nama sekaligus
            final_df = recap_df[recap_df[name_col].isin(list_search)]
            
            # Cek jika ada username yang dicari tapi tidak ditemukan di data
            found_names = final_df[name_col].tolist()
            not_found = [n for n in list_search if n not in found_names]
            
            if not_found:
                st.warning(f"Ada {len(not_found)} username tidak ditemukan dalam file data.")
                with st.expander("Lihat username yang tidak ditemukan"):
                    st.write(not_found)
        else:
            final_df = recap_df # Jika kosong, tampilkan semua

        # 6. Tampilkan Hasil
        st.subheader(f"Hasil Rekap ({len(final_df)} Creator)")
        
        col1, col2 = st.columns([3, 1])
        with col1:
            st.dataframe(final_df.sort_values(by=gmv_col, ascending=False), use_container_width=True)
        
        with col2:
            total_gmv = final_df[gmv_col].sum()
            st.metric("Total GMV Group", f"Rp {total_gmv:,.0f}")
            
            csv = final_df.to_csv(index=False).encode('utf-8')
            st.download_button("📥 Download Hasil (.csv)", csv, "recap_search.csv", "text/csv")

else:
    st.info("Silakan unggah file campaign terlebih dahulu.")
