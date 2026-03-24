import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go

st.set_page_config(page_title="Analyse Financière Experte", layout="wide")
st.title("📊 Dashboard d'Analyse Financière Professionnel")

# --- BARRE LATÉRALE ---
st.sidebar.header("⚙️ Configuration & Identification")
nom_entreprise = st.sidebar.text_input("Nom de l'entreprise :", value="Ma Société SAS")
devise_option = st.sidebar.selectbox("Choisir la monnaie :", ["EUR (€)", "USD ($)", "TND (DT)", "BTC (₿)"])
symbole = devise_option.split("(")[-1].replace(")", "")
taux_actualisation = st.sidebar.slider("Taux d'actualisation (%)", 0, 20, 10) / 100

uploaded_file = st.file_uploader("Téléverse ton fichier Excel", type=["xlsx"])

if uploaded_file:
    # Lecture de l'Excel
    df_brut = pd.read_excel(uploaded_file, header=None)
    donnees = df_brut.iloc[:, 1:] 
    
    # --- TABLEAU 1 : AFFICHAGE DES DONNÉES DE BASE ---
    st.write(f"### 📄 Données de base importées : {nom_entreprise}")
    # On affiche le dataframe tel quel pour correspondre à ton image
    st.dataframe(df_brut.style.format(precision=2), use_container_width=True)

    annees_labels = [f"Année {i+1}" for i in range(donnees.shape[1])]
    cash_flows_nets = []
    
    try:
        for col in donnees.columns:
            # Extraction par index selon ton fichier (Index 1 à 9)
            ca        = pd.to_numeric(donnees[col][1], errors='coerce') or 0
            cv        = pd.to_numeric(donnees[col][2], errors='coerce') or 0
            cfix      = pd.to_numeric(donnees[col][3], errors='coerce') or 0
            amort     = pd.to_numeric(donnees[col][4], errors='coerce') or 0
            bfr       = pd.to_numeric(donnees[col][6], errors='coerce') or 0
            impots    = pd.to_numeric(donnees[col][7], errors='coerce') or 0
            val_res   = pd.to_numeric(donnees[col][8], errors='coerce') or 0
            gain_cess = pd.to_numeric(donnees[col][9], errors='coerce') or 0

            # Calcul du Cash Flow Net
            ebit = ca - cv - cfix - amort
            resultat_net = ebit - impots
            cfn = resultat_net + amort - bfr + val_res + gain_cess
            cash_flows_nets.append(cfn)

        # --- TABLEAU 2 : AFFICHAGE DES CFN CALCULÉS ---
        st.write(f"### 📈 Flux de Trésorerie Nets (CFN) par année ({symbole}) :")
        # On crée un petit tableau d'une seule ligne comme sur ton image
        df_cfn = pd.DataFrame([cash_flows_nets], columns=annees_labels)
        st.table(df_cfn.style.format("{:.2f}"))

        # --- CALCUL VAN ---
        io_total = pd.to_numeric(donnees[donnees.columns[0]][5], errors='coerce') or 0
        van = -io_total
        for t, cfn in enumerate(cash_flows_nets, start=1):
            van += cfn / (1 + taux_actualisation)**t

        # --- VISUALISATION GRAPHIQUE ---
        st.divider()
        col_g1, col_g2 = st.columns(2)
        with col_g1:
            st.write(f"### 🍩 Structure - {nom_entreprise}")
            fig_pie = go.Figure(data=[go.Pie(labels=annees_labels, values=[abs(x) for x in cash_flows_nets], hole=.5)])
            st.plotly_chart(fig_pie, use_container_width=True)
        with col_g2:
            st.write(f"### 📈 Rentabilité - {nom_entreprise}")
            cumul = np.cumsum(cash_flows_nets) - io_total
            fig_line = go.Figure()
            fig_line.add_trace(go.Scatter(x=annees_labels, y=cumul, mode='lines+markers', line=dict(color='firebrick', width=3)))
            fig_line.add_hline(y=0, line_dash="dash")
            st.plotly_chart(fig_line, use_container_width=True)

        # --- RÉSULTAT FINAL ---
        st.divider()
        if van > 0:
            st.success(f"✅ La VAN est de **{round(van, 2)} {symbole}**. Le projet est RENTABLE.")
            st.balloons()
        else:
            st.error(f"❌ La VAN est de **{round(van, 2)} {symbole}**. Le projet n'est PAS RENTABLE.")

    except Exception as e:
        st.error(f"Erreur lors du calcul : {e}")
    # --- NOUVELLE SECTION : SIMULATION DE MONTE-CARLO ---
st.divider()
st.header(f"🎲 Simulation de Risque (Monte-Carlo) - {nom_entreprise}")

with st.expander("Qu'est-ce que c'est ?"):
    st.write("L'IA simule 1000 variantes de votre projet avec une marge d'erreur de 10% pour voir si le projet reste rentable en cas de crise ou de succès imprévu.")

# Lancement de la simulation au clic
if st.button("Lancer le Stress Test (1000 scénarios)"):
    simulations_van = []
    
    for i in range(1000):
        # On ajoute une variation aléatoire de +/- 10% à chaque Cash Flow
        cf_simule = [cf * np.random.uniform(0.9, 1.1) for cf in cash_flows_nets]
        
        # Calcul de la VAN pour cette simulation
        van_sim = -io_total
        for t, cfn in enumerate(cf_simule, start=1):
            van_sim += cfn / (1 + taux_actualisation)**t
        simulations_van.append(van_sim)
    
    # Calcul des probabilités
    projets_rentables = sum(1 for v in simulations_van if v > 0)
    probabilite_succes = (projets_rentables / 1000) * 100

    # Affichage du résultat de l'IA
    st.metric("Probabilité de rentabilité réelle", f"{probabilite_succes}%")
    
    if probabilite_succes > 80:
        st.success("💪 Le projet est très solide, même en cas de variations du marché.")
    elif probabilite_succes > 50:
        st.warning("⚠️ Le projet est sensible aux risques. À surveiller.")
    else:
        st.error("🚨 Risque élevé : Le projet échoue dans la majorité des scénarios simulés.")

    # Graphique de distribution des risques
    fig_hist = go.Figure(data=[go.Histogram(x=simulations_van, marker_color='#FFA15A')])
    fig_hist.update_layout(title="Distribution des VAN possibles (Stress Test)", xaxis_title="Valeur de la VAN", yaxis_title="Nombre de scénarios")
    st.plotly_chart(fig_hist, use_container_width=True)