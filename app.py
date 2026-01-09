def clean_gmv_data(df):
    """Fungsi pembersihan data GMV yang lebih stabil"""
    # 1. Hapus kolom yang mengandung kata 'Refunded'
    cols_to_keep = [c for c in df.columns if 'refunded' not in c.lower()]
    df = df[cols_to_keep]
    
    # 2. Hapus baris jika ada status 'Refunded'
    status_col = next((c for c in df.columns if 'status' in c.lower()), None)
    if status_col:
        df = df[df[status_col].astype(str).str.lower() != 'refunded']
    
    # 3. Cari kolom GMV
    gmv_col = next((c for c in df.columns if 'gmv' in c.lower() and 'refund' not in c.lower()), None)
    
    if gmv_col:
        # PAKSA konversi ke angka. 
        # errors='coerce' akan mengubah teks yang tidak bisa dihitung menjadi NaN (kosong)
        if df[gmv_col].dtype == 'object':
            # Bersihkan karakter non-angka jika ada (seperti Rp, titik, koma)
            df[gmv_col] = df[gmv_col].astype(str).str.replace(r'[^\d.]', '', regex=True)
            df[gmv_col] = pd.to_numeric(df[gmv_col], errors='coerce')
        
        # Hapus baris yang GMV-nya kosong (NaN) setelah konversi
        df = df.dropna(subset=[gmv_col])
        
        # Sekarang aman untuk membandingkan dengan angka 0
        df = df[df[gmv_col] >= 0]
        
    return df
