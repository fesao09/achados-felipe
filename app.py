import os
import sqlite3
import pandas as pd
import streamlit as st
from google import genai

# Configuração da Página
st.set_page_config(
    page_title="Central Achados do Felipe",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Estilização CSS (Dark Mode / Moderno)
st.markdown(
    """
    <style>
    .main { background-color: #121212; color: #ffffff; }
    .stSidebar { background-color: #181818; }
    h1, h2, h3 { color: #1DB954 !important; }
    .card { background-color: #282828; padding: 20px; border-radius: 12px; margin-bottom: 15px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .metric-card { background-color: #282828; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- BANCO DE DADOS LOCAL (SQLite) ---
DB_FILE = "achados_felipe.db"


def init_db():
  conn = sqlite3.connect(DB_FILE)
  cursor = conn.cursor()
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS produtos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT,
            nicho TEXT,
            link_afiliado TEXT
        )
    """)
  cursor.execute("""
        CREATE TABLE IF NOT EXISTS conteudos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            produto_id INTEGER,
            titulo TEXT,
            plataforma TEXT,
            tipo_midia TEXT,
            status TEXT,
            pacote_completo TEXT,
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


# --- CONFIGURAÇÃO DA IA (GEMINI API) ---
try:
  # Pega a chave dos secrets do Streamlit
  api_key = st.secrets["GEMINI_API_KEY"]
  client = genai.Client(api_key=api_key)
  IA_DISPONIVEL = True
except Exception as e:
  IA_DISPONIVEL = False

# --- MENU LATERAL ---
st.sidebar.title("🚀 Achados do Felipe")
st.sidebar.markdown("---")
menu = st.sidebar.selectbox(
    "Navegação",
    [
        "📊 Dashboard & Metas",
        "📦 Catálogo de Produtos",
        "🎬 Gerador com IA do Gemini",
        "📋 Kanban de Postagens",
    ],
)

# --- TELA 1: DASHBOARD ---
if menu == "📊 Dashboard & Metas":
  st.title("📊 Painel de Controle & Campanhas")

  df_conteudos = run_query(
      "SELECT * FROM conteudos WHERE status LIKE '%Publicado%'"
  )
  total_publicados = len(df_conteudos)
  meta_videos = 15

  col1, col2, col3 = st.columns(3)
  with col1:
    st.markdown(
        f'<div class="metric-card"><h3>Vídeos TikTok</h3><h2>'
        f" {total_publicados} / {meta_videos}</h2></div>",
        unsafe_allow_html=True,
    )
  with col2:
    st.markdown(
        '<div class="metric-card"><h3>Campanha Ativa</h3><h2>#ViralTikTokShop</h2></div>',
        unsafe_allow_html=True,
    )
  with col3:
    progresso = int((total_publicados / meta_videos) * 100)
    st.markdown(
        f'<div class="metric-card"><h3>Progresso</h3><h2>{progresso}%</h2></div>',
        unsafe_allow_html=True,
    )

  st.markdown("---")
  st.subheader("🚀 Últimos Projetos")
  df_recentes = run_query("""
        SELECT c.id, p.nome as produto, c.titulo, c.plataforma, c.status 
        FROM conteudos c 
        LEFT JOIN produtos p ON c.produto_id = p.id 
        ORDER BY c.id DESC LIMIT 5
    """)
  if not df_recentes.empty:
    for _, row in df_recentes.iterrows():
      st.markdown(
          f"""
            <div class="card">
                <b>📦 {row['produto']}</b> | 🎯 {row['titulo']}<br>
                <small>Plataforma: {row['plataforma']} | Status: <b>{row['status']}</b></small>
            </div>
            """,
          unsafe_allow_html=True,
      )
  else:
    st.info("Nenhum conteúdo gerado ainda.")

# --- TELA 2: PRODUTOS ---
elif menu == "📦 Catálogo de Produtos":
  st.title("📦 Gestão de Produtos & Afiliados")

  with st.form("form_produto"):
    st.subheader("Cadastrar Novo Produto")
    nome_prod = st.text_input("Nome do Produto (ex: Kit BT21 Secret Fragrance)")
    nicho_prod = st.selectbox(
        "Nicho", ["Moda Praia", "K-pop / Colecionáveis", "Beleza", "Casa"]
    )
    link_af = st.text_input("Link de Afiliado (Shopee / TikTok Shop)")
    submit_prod = st.form_submit_button("Salvar Produto")

    if submit_prod and nome_prod:
      run_query(
          "INSERT INTO produtos (nome, nicho, link_afiliado) VALUES (?, ?, ?)",
          (nome_prod, nicho_prod, link_af),
          fetch=False,
      )
      st.success(f"Produto '{nome_prod}' cadastrado com sucesso!")

  st.markdown("---")
  st.subheader("Lista de Produtos")
  df_prods = run_query("SELECT * FROM produtos")
  if not df_prods.empty:
    st.dataframe(df_prods, width="stretch")
  else:
    st.info("Nenhum produto cadastrado.")

# --- TELA 3: GERADOR COM IA DO GEMINI ---
elif menu == "🎬 Gerador com IA do Gemini":
  st.title("🎬 Gerador de Pacote Inteligente (Powered by Gemini)")
  st.markdown(
      "A IA vai ler o produto selecionado e estruturar o pacote completo com"
      " ganchos, prompts e legendas em português do Brasil 100% natural."
  )

  if not IA_DISPONIVEL:
    st.error(
        "⚠️ Chave da API do Gemini não configurada nos 'Secrets' do Streamlit."
        " Configure para ativar a IA."
    )

  df_produtos = run_query("SELECT id, nome FROM produtos")
  if not df_produtos.empty:
    prod_escolhido = st.selectbox(
        "Selecione o Produto", df_produtos["nome"].tolist()
    )
    prod_id = df_produtos.loc[
        df_produtos["nome"] == prod_escolhido, "id"
    ].values[0]

    formato_midia = st.selectbox(
        "Formato Principal",
        [
            "Vídeo Dinâmico (Ideal para TikTok / Reels)",
            "Carrossel / Imagem Estática (Ideal para Pinterest / Instagram)",
        ],
    )

    if st.button("Gerar Pacote Completo com IA 🚀") and IA_DISPONIVEL:
      with st.spinner("A Inteligência Artificial está criando o seu pacote..."):
        prompt_sistema = f"""
                Atue como um estrategista especialista em marketing de afiliados para o projeto 'Achados do Felipe'.
                Gere um pacote completo de conteúdo em português 100% natural do Brasil (sem termos de Portugal ou espanhol) para o produto: '{prod_escolhido}'.
                O formato escolhido é: '{formato_midia}'.
                
                Estruture a resposta exatamente com os seguintes tópicos em Markdown:
                ### 🎯 1. GANCHOS E TÍTULOS (0 a 3 segundos)
                (Duas opções de ganchos fortes para prender a atenção)
                
                ### 🎬 2. ROTEIRO & PROMPT DE CRIAÇÃO
                (Prompt detalhado em inglês otimizado para ferramentas de IA de vídeo ou imagem, mais dicas de direção)
                
                ### 📱 3. TEXTOS E LEGENDAS POR REDE SOCIAL
                (Legenda engajadora para TikTok/Instagram e título/descrição rica e detalhada para o Pinterest)
                
                ### #️⃣ 4. HASHTAGS E INSIGHTS
                (Hashtags estratégicas e chamada para ação / CTA para a sacolinha amarela)
                """

        # Chamada real para a API do Gemini
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_sistema,
        )
        pacote_gerado = response.text

        st.success("Pacote gerado pela IA com sucesso!")
        st.markdown(pacote_gerado)

        if st.button("💾 Salvar na Central como Pendente"):
          run_query(
              """
                        INSERT INTO conteudos (produto_id, titulo, plataforma, tipo_midia, status, pacote_completo)
                        VALUES (?, ?, ?, ?, ?, ?)
                    """,
              (
                  prod_id,
                  f"Campanha: {prod_escolhido}",
                  "TikTok / Instagram / Pinterest",
                  formato_midia,
                  "Pendente 🟡",
                  pacote_gerado,
              ),
              fetch=False,
          )
          st.success("Salvo com sucesso na sua Central de Postagens!")
  else:
    st.warning("Cadastre um produto na aba de Catálogo primeiro.")

# --- TELA 4: KANBAN DE POSTAGENS ---
elif menu == "📋 Kanban de Postagens":
  st.title("📋 Central de Publicações (Kanban)")
  st.markdown("Acompanhe o que está pendente, pronto ou postado.")

  df_kanban = run_query("""
        SELECT c.id, p.nome as produto, c.titulo, c.plataforma, c.tipo_midia, c.status, c.pacote_completo 
        FROM conteudos c 
        LEFT JOIN produtos p ON c.produto_id = p.id 
        ORDER BY c.id DESC
    """)

  if not df_kanban.empty:
    for _, row in df_kanban.iterrows():
      status_cor = (
          "🟡" if "Pendente" in str(row["status"]) else "🟢"
      )
      with st.expander(
          f"{status_cor} [{row['produto']}] - {row['titulo']} ({row['status']})"
      ):
        st.markdown(f"**Plataforma:** {row['plataforma']}")
        st.markdown(f"**Tipo de Mídia:** {row['tipo_midia']}")
        st.markdown("---")
        st.markdown(row["pacote_completo"])
        st.markdown("---")

        col_A, col_B = st.columns(2)
        with col_A:
          if st.button("Marcar como Pronto 🟢", key=f"pronto_{row['id']}"):
            run_query(
                "UPDATE conteudos SET status = 'Pronto 🟢' WHERE id = ?",
                (row["id"],),
                fetch=False,
            )
            st.rerun()
        with col_B:
          if st.button(
              "Marcar como Publicado ✔️", key=f"pub_{row['id']}"
          ):
            run_query(
                "UPDATE conteudos SET status = 'Publicado ✔️' WHERE id = ?",
                (row["id"],),
                fetch=False,
            )
            st.rerun()
  else:
    st.info("Nenhum conteúdo cadastrado na central ainda.")
