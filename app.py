import os
import sqlite3
import pandas as pd
import streamlit as st

# Configuração da Página (Modo Responsivo e Tema Moderno)
st.set_page_config(
    page_title="Central Achados do Felipe",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização CSS personalizada para dar um toque moderno (estilo Spotify/Dark Mode)
st.markdown(
    """
    <style>
    .main {
        background-color: #121212;
        color: #ffffff;
    }
    .stSidebar {
        background-color: #181818;
    }
    h1, h2, h3 {
        color: #1DB954 !important;
    }
    .metric-card {
        background-color: #282828;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- CONFIGURAÇÃO DO BANCO DE DADOS LOCAL (SQLite) ---
DB_FILE = "achados_felipe.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  # Tabela de Produtos / Cadastros
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            nicho TEXT,
            link_afiliado TEXT,
            status_criacao TEXT
        )
    """)
  # Tabela de Conteúdos / Kanban e Metas
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS conteudos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            titulo TEXT,
            plataforma TEXT,
            tipo_midia TEXT,
            status TEXT,
            legenda TEXT,
            prompt_ia TEXT,
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)
  conn.commit()
  conn.close()


init_db()


def run_query(query, params=(), fetch=True):
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute(query, params)
  if fetch:
    data = cursor.fetchall()
    columns = [description[0] for description in cursor.description]
    conn.close()
    return pd.DataFrame(data, columns=columns)
  conn.commit()
  conn.close()


# --- BARRA LATERAL (MENU DE NAVEGAÇÃO) ---
st.sidebar.title("🚀 Achados do Felipe")
st.sidebar.markdown("---")
menu = st.sidebar.selectbox(
    "Navegação",
    [
        "📊 Dashboard & Metas",
        "📦 Catálogo de Produtos",
        "🎬 Gerador de Roteiros & IA",
        "📋 Kanban de Postagens",
    ],
)

# --- TELA 1: DASHBOARD & METAS ---
if menu == "📊 Dashboard & Metas":
  st.title("📊 Painel de Controle & Campanhas")
  st.markdown(
      "Acompanhe suas metas de vídeos para o TikTok Shop e o status das"
      " postagens."
  )

  # Métricas rápidas
  df_conteudos = run_query(
      "SELECT * FROM conteudos WHERE plataforma LIKE '%TikTok%'"
  )
  total_tiktok = len(df_conteudos)
  meta_videos = 15

  col1, col2, col3 = st.columns(3)
  with col1:
    st.markdown(
        f'<div class="metric-card"><h3>Vídeos TikTok</h3><h2>{total_tiktok} /'
        f" {meta_videos}</h2></div>",
        unsafe_allow_html=True,
    )
  with col2:
    st.markdown(
        '<div class="metric-card"><h3>Campanha Ativa</h3><h2>#ViralTikTokShop</h2></div>',
        unsafe_allow_html=True,
    )
  with col3:
    st.markdown(
        '<div class="metric-card"><h3>Status da Meta</h3><h2>'
        f" {int((total_tiktok/meta_videos)*100)}% Concluído</h2></div>",
        unsafe_allow_html=True,
    )

  st.markdown("---")
  st.subheader("📋 Últimos Conteúdos Registrados")
  df_all = run_query("""
        <select> c.id, p.nome as produto, c.titulo, c.plataforma, c.status 
        FROM conteudos c 
        LEFT JOIN produtos p ON c.produto_id = p.id
    """)
  st.dataframe(df_all, use_container_width=True)

# --- TELA 2: CATÁLOGO DE PRODUTOS ---
elif menu == "📦 Catálogo de Produtos":
  st.title("📦 Gestão de Produtos & Afiliados")

  with st.form("form_produto"):
    st.subheader("Cadastrar Novo Produto")
    nome_prod = st.text_input("Nome do Produto (ex: Biquíni Conchas)")
    nicho_prod = st.selectbox(
        "Nicho", ["Moda Praia", "K-pop / Streetwear", "Beleza / Cuidados", "Casa"]
    )
    link_af = st.text_input("Link de Afiliado (Shopee / TikTok Shop)")
    submit_prod = st.form_submit_button("Salvar Produto")

    if submit_prod and nome_prod:
      run_query(
          "INSERT INTO produtos (nome, nicho, link_afiliado, status_criacao)"
          " VALUES (?, ?, ?, ?)",
          (nome_prod, nicho_prod, link_af, "Pendente"),
          fetch=False,
      )
      st.success(f"Produto '{nome_prod}' cadastrado com sucesso!")

  st.markdown("---")
  st.subheader("Meus Produtos Cadastrados")
  df_prods = run_query("SELECT * FROM produtos")
  st.dataframe(df_prods, use_container_width=True)

# --- TELA 3: GERADOR DE ROTEIROS & IA ---
elif menu == "🎬 Gerador de Roteiros & IA":
  st.title("🎬 Central de IA & Prompts de Vídeo")
  st.markdown(
      "Simule o trabalho de criação rápida de roteiros, ganchos e prompts"
      " idênticos aos que usamos no chat."
  )

  df_produtos = run_query("SELECT id, nome FROM produtos")
  if not df_produtos.empty:
    prod_escolhido = st.selectbox(
        "Selecione o Produto", df_produtos["nome"].tolist()
    )
    prod_id = df_produtos.loc[
        df_produtos["nome"] == prod_escolhido, "id"
    ].values[0]

    tipo_conteudo = st.selectbox(
        "Formato do Conteúdo",
        [
            "Vídeo Dinâmico (TikTok / Reels)",
            "Pin Estático / Carrossel (Pinterest / Instagram)",
        ],
    )

    if st.button("Gerar Pacote Completo com IA"):
      # Simulação da inteligência de IA integrada baseada nos padrões do nosso chat
      gancho = f"O ITEM MAIS DESEJADO DA ESTAÇÃO! 🔥 (Foco em {prod_escolhido})"
      prompt_ia = (
          f"Vertical 9:16 aspect ratio, dynamic e-commerce showcase video of"
          f" {prod_escolhido}, smooth motion, cinematic lighting, 4k."
      )
      legenda = (
          f"Olha que incrível esse {prod_escolhido}! Perfeito para o dia a"
          " dia. Garanta já o seu na sacolinha amarela! 🛒✨"
          " #ViralTikTokShop #achadosshopee"
      )

      st.success("Pacote gerado com sucesso!")
      st.text_area("Gancho / Título na Tela:", value=gancho)
      st.text_area("Prompt para IA de Vídeo:", value=prompt_ia)
      st.text_area("Legenda Otimizada (BR):", value=legenda)

      if st.button("Salvar na Central de Conteúdos"):
        run_query(
            """
                    INSERT INTO conteudos (produto_id, titulo, plataforma, tipo_midia, status, legenda, prompt_ia)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
            (
                prod_id,
                gancho,
                "TikTok / Instagram",
                tipo_conteudo,
                "Pendente",
                legenda,
                prompt_ia,
            ),
            fetch=False,
        )
        st.success("Salvo com sucesso no seu banco de dados!")
  else:
    st.warning("Cadastre pelo menos um produto na aba anterior primeiro.")

# --- TELA 4: KANBAN DE POSTAGENS ---
elif menu == "📋 Kanban de Postagens":
  st.title("📋 Gestão de Status de Publicação")
  st.markdown("Acompanhe o que está pendente, pronto ou já postado.")

  df_kanban = run_query("""
        SELECT c.id, p.nome as produto, c.titulo, c.plataforma, c.status 
        FROM conteudos c 
        LEFT JOIN produtos p ON c.produto_id = p.id
    """)

  if not df_kanban.empty:
    st.dataframe(df_kanban, use_container_width=True)

    # Atualizar status
    st.subheader("Atualizar Status de Publicação")
    conteudo_id = st.number_input("ID do Conteúdo", min_value=1, step=1)
    novo_status = st.selectbox(
        "Novo Status", ["Pendente", "Pronto para Subir", "Publicado ✔️"]
    )
    if st.button("Atualizar Status"):
      run_query(
          "UPDATE conteudos SET status = ? WHERE id = ?",
          (novo_status, conteudo_id),
          fetch=False,
      )
      st.success("Status atualizado!")
      st.rerun()
  else:
    st.info("Nenhum conteúdo cadastrado ainda.")
