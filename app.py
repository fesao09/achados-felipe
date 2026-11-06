import os
import json
import sqlite3
import pandas as pd
import streamlit as st
import random

# --- CONFIGURAÇÃO DA PÁGINA E CSS ---
st.set_page_config(
    page_title="Achados do Felipe",
    page_icon="🔎", 
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS (Dark Mode com a sua Identidade Visual Laranja)
st.markdown(
    """
    <style>
    /* Fundo geral escuro */
    .main { background-color: #121212; color: #ffffff; }
    
    /* Títulos em Laranja Vibrante */
    h1, h2, h3 { color: #FF4500 !important; }
    
    /* Botões personalizados com o laranja do seu logo */
    .stButton>button { 
        background: linear-gradient(90deg, #FF7F50 0%, #FF4500 100%) !important; 
        color: white !important; 
        border: none !important; 
        border-radius: 8px !important; 
        font-weight: bold; 
    }
    .stButton>button:hover { opacity: 0.8 !important; }
    
    /* Cards com detalhe laranja na lateral */
    .card { 
        background-color: #282828; 
        padding: 15px; 
        border-radius: 12px; 
        margin-bottom: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        border-left: 5px solid #FF4500; 
    }
    
    /* Dashboard com linha laranja */
    .metric-card { 
        background-color: #282828; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center; 
        border-bottom: 4px solid #FF4500; 
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- CABEÇALHO BANNER GIGANTE ---
try:
    # O comando use_container_width=True faz a imagem esticar bonitona na tela
    st.image("banner.png", use_container_width=True)
except:
    # Se a imagem ainda não estiver no GitHub, mostra o texto padrão
    st.title("Central Achados do Felipe")
    st.markdown("<p style='color: #FF7F50; margin-top: -15px;'>As Melhores Ofertas</p>", unsafe_allow_html=True)

st.markdown("---")

menu = st.radio(
    "Navegação",
    ["🎬 Gerar", "📋 Pendentes", "📦 Catálogo", "🧠 Treinamento", "📊 Dashboard"],
    horizontal=True,
)
st.markdown("---")

# ... [CONTINUE COM O RESTO DO CÓDIGO A PARTIR DAQUI] ...
