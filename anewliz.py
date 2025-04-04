# Bu dosya, birden fazla lig ve sezon seçimi ile oran analizi yapar.
# Güncelleme: Veriler Google Drive'dan otomatik indirilir

import streamlit as st
import pandas as pd
import os
import gdown

# 📥 Google Drive'dan verileri indir
DATA_DIR = "veriler"
os.makedirs(DATA_DIR, exist_ok=True)

# Google Drive ID -> Dosya adı eşleşmeleri
drive_dosyalar = {
    "1CzCSFCRAzTq4dW8WpryQIMYPAHm9f23h": "all-euro-data-2018-2019.xlsx",
    "1gC9ErNdB-L03X_AqfpZ4OymVYLyqOhfA": "all-euro-data-2019-2020.xlsx",
    "1wb7_t6opzC03KzBmvG43mdebIAOHpido": "all-euro-data-2020-2021.xlsx",
    "1Pkeqvf2StjHj6CTmDY-tFbP_v87FqNVN": "all-euro-data-2021-2022.xlsx",
    "12b_q1Hx4pNsCBqGuVWH4zwFIrN9gG3Qk": "all-euro-data-2022-2023.xlsx",
    "10dVl-HLG213DM_ohC3hqpshlDpO6N_yD": "all-euro-data-2023-2024.xlsx",
    "14NKTARmp0mBMnnsOofSLRA8NWsqL6QKb": "all-euro-data-2024-2025.xlsx"
}

for dosya_id, isim in drive_dosyalar.items():
    hedef_yol = os.path.join(DATA_DIR, isim)
    if not os.path.exists(hedef_yol):
        url = f"https://drive.google.com/uc?id={dosya_id}"
        gdown.download(url, hedef_yol, quiet=False)

# 🔍 Analiz Başlangıcı
st.set_page_config(page_title="İddaa Oran Analiz", layout="centered")
st.title("🌟 İddaa Oran Analiz Aracı")

xlsx_files = [f for f in os.listdir(DATA_DIR) if f.endswith(".xlsx")]
lig_sezon = []
for file in xlsx_files:
    sezon = file.replace("all-euro-data-", "").replace(".xlsx", "")
    xl = pd.ExcelFile(os.path.join(DATA_DIR, file))
    for sheet in xl.sheet_names:
        lig_sezon.append((sheet, sezon))

ligler = sorted(set(l for l, s in lig_sezon))
sezonlar = sorted(set(s for l, s in lig_sezon), reverse=True)

lig_isim_map = {
    "E0": "Premier League (İngiltere)",
    "B1": "Pro League (Belçika)",
    "D1": "Bundesliga (Almanya)",
    "F1": "Ligue 1 (Fransa)",
    "G1": "Super League (Yunanistan)",
    "N1": "Eredivisie (Hollanda)",
    "P1": "Primeira Liga (Portekiz)",
    "D2": "2. Bundesliga (Almanya)",
    "E1": "Championship (İngiltere)",
    "E2": "League One (İngiltere)",
    "E3": "League Two (İngiltere)",
    "EC": "FA Cup (İngiltere)",
    "F2": "Ligue 2 (Fransa)",
    "I1": "Serie A (İtalya)",
    "I2": "Serie B (İtalya)",
    "SC0": "Premiership (İskoçya)",
    "SC1": "Championship (İskoçya)",
    "SC2": "League One (İskoçya)",
    "SC3": "League Two (İskoçya)",
    "SP1": "La Liga (İspanya)",
    "SP2": "Segunda División (İspanya)",
    "T1": "Süper Lig (Türkiye)"
}
lig_gosterim = sorted([lig_isim_map.get(kod, kod) for kod in ligler])
varsayilan_lig = lig_isim_map["E0"]
secili_ligler_gosterim = st.multiselect("🏆 Lig(ler) Seç", lig_gosterim, default=[varsayilan_lig])
secili_ligler = [kod for kod, isim in lig_isim_map.items() if isim in secili_ligler_gosterim]
secili_sezonlar = st.multiselect("🗓️ Sezon(lar) Seç", sezonlar, default=["2022-2023", "2023-2024"])

with st.expander("⚙️ Oran ve Ekstra Filtreler"):
    h = st.number_input("Ev sahibi oranı (1)", value=2.00)
    d = st.number_input("Beraberlik oranı (X)", value=3.00)
    a = st.number_input("Deplasman oranı (2)", value=3.00)
    tolerans = st.slider("Oran toleransı", 0.1, 1.0, 0.25)

if st.button("🔍 Analiz Yap"):
    df_all = []
    for file in xlsx_files:
        sezon = file.replace("all-euro-data-", "").replace(".xlsx", "")
        if sezon not in secili_sezonlar:
            continue
        path = os.path.join(DATA_DIR, file)
        xl = pd.ExcelFile(path)
        for lig in secili_ligler:
            if lig in xl.sheet_names:
                try:
                    df = xl.parse(lig)
                    if {"HomeTeam", "AwayTeam", "FTR", "B365H", "B365D", "B365A"}.issubset(df.columns):
                        df = df.dropna(subset=["B365H", "B365D", "B365A"])
                        df["Sezon"] = sezon
                        df["Lig"] = lig
                        df_all.append(df)
                except:
                    continue

    if df_all:
        df = pd.concat(df_all, ignore_index=True)
        df = df.dropna(subset=["HomeTeam", "AwayTeam", "FTR"])

        benzer = df[
            ((df["B365H"] - h).abs() < tolerans) &
            ((df["B365D"] - d).abs() < tolerans) &
            ((df["B365A"] - a).abs() < tolerans)
        ]

        if not benzer.empty:
            st.success(f"{len(benzer)} benzer maç bulundu.")
            if {"FTHG", "FTAG"}.issubset(benzer.columns):
                benzer["Skor"] = benzer["FTHG"].astype(int).astype(str) + "-" + benzer["FTAG"].astype(int).astype(str)
                kolonlar = ["Sezon", "Lig", "HomeTeam", "AwayTeam", "FTR", "B365H", "B365D", "B365A", "Skor"]
            else:
                kolonlar = ["Sezon", "Lig", "HomeTeam", "AwayTeam", "FTR", "B365H", "B365D", "B365A"]
            st.dataframe(benzer[kolonlar])

            st.subheader("📊 Maç Sonucu Dağılımı")
            st.bar_chart(benzer["FTR"].value_counts(normalize=True) * 100)

            if not benzer["FTR"].value_counts().empty:
                tahmin = benzer["FTR"].value_counts().idxmax()
                tahmin_map = {"H": "Ev Sahibi Kazanır", "D": "Beraberlik", "A": "Deplasman Kazanır"}
                st.subheader("🤔 Tahmin")
                st.write(f"Bu oranlara en uygun tahmin: **{tahmin_map.get(tahmin, 'Bilinmiyor')}**")
            else:
                st.info("Tahmin üretilemedi çünkü maç sonucu bilgisi eksik.")
        else:
            st.warning("Filtreye uyan hiç maç bulunamadı.")
    else:
        st.warning("Seçilen lig + sezon için uygun veri bulunamadı.")
