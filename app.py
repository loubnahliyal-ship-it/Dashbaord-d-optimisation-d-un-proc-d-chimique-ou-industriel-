# -*- coding: utf-8 -*-
import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os

# Configuration de la page
st.set_page_config(
    page_title="Industrial Analytics Dashboard",
    page_icon="🏭",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Application d'un style CSS personnalisé pour une interface moderne
st.markdown("""
    <style>
    .main { background-color: #f8f9fa; }
    .stMetric {
        background-color: #ffffff;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.05);
        border-left: 5px solid #007bff;
    }
    .stAlert { border-radius: 10px; }
    h1, h2, h3 { color: #1e293b; font-family: 'Segoe UI', sans-serif; }
    .sidebar .sidebar-content { background-color: #ffffff; }
    </style>
""", unsafe_allow_html=True)

# 1. ETAPE 5: SYSTÈME DE LOGIN SIMPLE
if 'authenticated' not in st.session_state:
    st.session_state['authenticated'] = False

def login():
    st.sidebar.title("🔐 Authentification")
    username = st.sidebar.text_input("Utilisateur", value="loubna.process")
    password = st.sidebar.text_input("Mot de passe", type="password", value="Process@2026")
    if st.sidebar.button("Se connecter"):
        if username == "loubna.process" and password == "Process@2026":
            st.session_state['authenticated'] = True
            st.sidebar.success("Connexion réussie !")
            st.rerun()
        else:
            st.sidebar.error("Identifiants incorrects.")

def logout():
    st.session_state['authenticated'] = False
    st.rerun()

if not st.session_state['authenticated']:
    st.title("🏭 Optimisation des Procédés Industriels Chimiques")
    st.info("Veuillez vous authentifier dans le panneau latéral pour accéder au tableau de bord. (Défaut: admin / admin123)")
    login()
else:
    st.sidebar.title("👤 Menu Utilisateur")
    st.sidebar.text("Connecté en tant que: Admin")
    if st.sidebar.button("Se déconnecter"):
        logout()

    # 2. ETAPE 1 & Chargement: NETTOYAGE DES DONNÉES
    @st.cache_data
    def load_clean_data():
        file_path = "dataset.csv"
        if not os.path.exists(file_path):
            return pd.DataFrame()
        df = pd.read_csv(file_path)
        
        # Nettoyage et conversion
        df["timestamp"] = pd.to_datetime(df["timestamp"], errors="coerce")
        
        # Imputation des valeurs manquantes pour les colonnes numériques
        num_cols = ["temperature_c", "pression_bar", "ph", "debit_l_min", "energie_kwh", "temps_cycle_min", "rendement_pct", "taux_rebut_pct"]
        for col in num_cols:
            if col in df.columns:
                df[col] = df[col].fillna(df[col].median())
                
        return df

    df_clean = load_clean_data()

    if df_clean.empty:
        st.error("Le fichier dataset.csv est introuvable ou vide. Veuillez vérifier la structure du projet.")
    else:
        # 3. ETAPE 6: FILTRES AVANCÉS DANS LA SIDEBAR
        st.sidebar.header("🎯 Filtres Globaux")
        
        # Filtre Temporel
        min_date = df_clean["timestamp"].min().date()
        max_date = df_clean["timestamp"].max().date()
        date_range = st.sidebar.date_input("Période d'analyse", [min_date, max_date], min_value=min_date, max_value=max_date)
        
        # Filtre Lignes et Produits
        lignes_dispo = sorted(df_clean["ligne"].unique().tolist())
        lignes_sel = st.sidebar.multiselect("Sélection des lignes", lignes_dispo, default=lignes_dispo)
        
        produits_dispo = sorted(df_clean["produit"].unique().tolist())
        produits_sel = st.sidebar.multiselect("Sélection des produits", produits_dispo, default=produits_dispo)

        # Application des filtres
        df_filtered = df_clean.copy()
        if len(date_range) == 2:
            df_filtered = df_filtered[(df_filtered["timestamp"].dt.date >= date_range[0]) & (df_filtered["timestamp"].dt.date <= date_range[1])]
        if lignes_sel:
            df_filtered = df_filtered[df_filtered["ligne"].isin(lignes_sel)]
        if produits_sel:
            df_filtered = df_filtered[df_filtered["produit"].isin(produits_sel)]

        # Titre Principal
        st.title("🏭 Tableau de bord d'Optimisation des Procédés")
        st.markdown("Analyse de performance, détection des anomalies et aide à la décision.")

        # 4. ETAPE 3: AFFICHAGE DES KPIs PRINCIPAUX
        st.subheader("📊 Indicateurs Clés de Performance (KPIs)")
        
        kpi1, kpi2, kpi3, kpi4, kpi5 = st.columns(5)
        
        rendement_moyen = df_filtered["rendement_pct"].mean()
        taux_rebut_moyen = df_filtered["taux_rebut_pct"].mean()
        energie_totale = df_filtered["energie_kwh"].sum()
        cout_total = df_filtered["cout_batch_mad"].sum()
        co2_total = df_filtered["emission_co2_kg"].sum()
        
        kpi1.metric(label="Rendement Moyen", value=f"{rendement_moyen:.2f} %")
        kpi2.metric(label="Taux de Rebut Moyen", value=f"{taux_rebut_moyen:.2f} %", delta=f"{taux_rebut_moyen - 3.0:.1f} % vs Cible (3%)", delta_color="inverse")
        kpi3.metric(label="Énergie Consommée", value=f"{energie_totale:,.0f} kWh")
        kpi4.metric(label="Coût Global Procédé", value=f"{cout_total:,.0f} MAD")
        kpi5.metric(label="Émissions CO₂ Totales", value=f"{co2_total:,.0f} kg")

        st.markdown("---")

        # Configuration globale des graphiques
        sns.set_theme(style="whitegrid")
        plt.rcParams['figure.facecolor'] = '#f8f9fa'

        # Onglets de navigation
        tab1, tab2, tab3 = st.tabs(["📈 Visualisation de la Performance", "🚨 Gestion des Anomalies & Alarmes", "🔬 Analyse des Paramètres Physico-Chimiques"])

        with tab1:
            st.subheader("Performance Globale et Coûts")
            col_g1, col_g2 = st.columns(2)
            
            with col_g1:
                st.markdown("**Évolution du Rendement et Taux de Rebut au cours du temps**")
                df_resampled = df_filtered.set_index("timestamp").resample("D")[["rendement_pct", "taux_rebut_pct"]].mean().reset_index()
                fig1, ax1 = plt.subplots(figsize=(10, 4.5))
                ax1.plot(df_resampled["timestamp"], df_resampled["rendement_pct"], label="Rendement (%)", color="#2b5c8f", lw=2)
                ax1.set_ylabel("Rendement (%)", color="#2b5c8f")
                
                ax2 = ax1.twinx()
                ax2.plot(df_resampled["timestamp"], df_resampled["taux_rebut_pct"], label="Taux de Rebut (%)", color="#d9534f", lw=1.5, linestyle="--")
                ax2.set_ylabel("Taux de Rebut (%)", color="#d9534f")
                
                plt.title("Suivi Journalier de l'Efficacité Industrielle")
                fig1.tight_layout()
                st.pyplot(fig1)
                
            with col_g2:
                st.markdown("**Classement des Lignes de Production par Coût Total**")
                top_lignes = df_filtered.groupby("ligne")["cout_batch_mad"].sum().sort_values(ascending=False).reset_index()
                fig2, ax3 = plt.subplots(figsize=(10, 4.5))
                sns.barplot(x="cout_batch_mad", y="ligne", data=top_lignes, palette="Blues_r", ax=ax3)
                ax3.set_xlabel("Coût Cumulé (MAD)")
                ax3.set_ylabel("Ligne / Réacteur")
                st.pyplot(fig2)

        with tab2:
            st.subheader("Anomalies, Alarmes et Qualité Finale")
            col_a1, col_a2 = st.columns(2)
            
            with col_a1:
                st.markdown("**Répartition de la Qualité Finale des Batches**")
                qualite_count = df_filtered["qualite_finale"].value_counts()
                fig3, ax4 = plt.subplots(figsize=(6, 6))
                ax4.pie(qualite_count, labels=qualite_count.index, autopct="%1.1f%%", colors=["#2ca02c", "#ff7f0e", "#d62728"], wedgeprops={'width': 0.4})
                st.pyplot(fig3)
                
            with col_a2:
                st.markdown("**Typologie et Fréquence des Alarmes Déclenchées**")
                alarm_count = df_filtered[df_filtered["alarme"] != "Aucune"]["alarme"].value_counts().reset_index()
                alarm_count.columns = ["Type d'Alarme", "Nombre d'occurrences"]
                if not alarm_count.empty:
                    fig4, ax5 = plt.subplots(figsize=(10, 5))
                    sns.barplot(x="Nombre d'occurrences", y="Type d'Alarme", data=alarm_count, palette="Oranges_r", ax=ax5)
                    st.pyplot(fig4)
                else:
                    st.success("✅ Aucune alarme détectée sur cette période et pour ces filtres.")

            # Tableau de décision pour le responsable métier
            st.markdown("**📋 Liste active des batches non conformes pour action immédiate**")
            anomalies = df_filtered[df_filtered["qualite_finale"] == "Non conforme"][["batch_id", "timestamp", "ligne", "produit", "alarme", "taux_rebut_pct", "cout_batch_mad"]]
            if not anomalies.empty:
                st.dataframe(anomalies.head(20), use_container_width=True)
            else:
                st.success("Aucun batch non conforme à signaler.")

        with tab3:
            st.subheader("Corrélations et Paramètres Physico-Chimiques")
            col_p1, col_p2 = st.columns(2)
            
            with col_p1:
                st.markdown("**Relation entre Température et Rendement**")
                fig5, ax6 = plt.subplots(figsize=(10, 5))
                sns.scatterplot(x="temperature_c", y="rendement_pct", hue="ligne", alpha=0.7, data=df_filtered, ax=ax6)
                ax6.set_xlabel("Température (°C)")
                ax6.set_ylabel("Rendement (%)")
                st.pyplot(fig5)
                
            with col_p2:
                st.markdown("**Distribution du pH du procédé**")
                fig6, ax7 = plt.subplots(figsize=(10, 5))
                sns.histplot(df_filtered["ph"], kde=True, color="#4b0082", ax=ax7)
                ax7.set_xlabel("Valeur pH")
                st.pyplot(fig6)

        # Footer informatif
        st.sidebar.markdown("---")
        st.sidebar.info("💡 **Aide à la Décision :** Si le taux de rebut dépasse 5% ou si une alarme type 'Pression/Température' s'affiche, veuillez planifier une maintenance préventive sur la ligne concernée.")
