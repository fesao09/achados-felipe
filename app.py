import io
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

# --- BANCO DE DADOS LOCAL (SQLite com Auto-Correção) ---
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
            tipo_midia TEXT,
            pacote_completo TEXT,
            post_tiktok INTEGER DEFAULT 0,
            post_instagram INTEGER DEFAULT 0,
            post_pinterest INTEGER DEFAULT 0,
            post_shopee INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pendente 🟡',
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)
  for col, tipo in [
      ("post_tiktok", "INTEGER DEFAULT 0"),
      ("post_instagram", "INTEGER DEFAULT 0"),
      ("post_pinterest", "INTEGER DEFAULT 0"),
      ("post_shopee", "INTEGER DEFAULT 0"),
  ]:
    try:
      cursor.execute(f"ALTER TABLE conteudos ADD COLUMN {col} {tipo}")
    except sqlite3.OperationalError:
      pass

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
        "📋 Central de Pendentes (Kanban)",
    ],
)

# --- TELA 1: DASHBOARD ---
if menu == "📊 Dashboard & Metas":
  st.title("📊 Painel de Controle & Campanhas")

  df_conteudos = run_query(
      "SELECT * FROM conteudos WHERE status LIKE '%Concluído%'"
  )
  total_publicados = len(df_conteudos)
  meta_videos = 15

  col1, col2, col3 = st.columns(3)
  with col1:
    st.markdown(
        f'<div class="metric-card"><h3>Vídeos Concluídos</h3><h2>'
        f" {total_publicados} / {meta_videos}</h2></div>",
        unsafe_allow_html=True,
    )
  with col2:
    st.markdown(
        '<div class="metric-card"><h3>Campanha Ativa</h3><h2>#ViralTikTokShop</h2></div>',
        unsafe_allow_html=True,
    )
  with col3:
    progresso = (
        int((total_publicados / meta_videos) * 100)
        if meta_videos > 0
        else 0
    )
    st.markdown(
        f'<div class="metric-card"><h3>Progresso Geral</h3><h2>'
        f" {progresso}%</h2></div>",
        unsafe_allow_html=True,
    )

  st.markdown("---")
  st.subheader("🚀 Últimos Projetos Criados")
  df_recentes = run_query("""
        SELECT c.id, p.nome as produto, c.titulo, c.status 
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
                <small>Status: <b>{row['status']}</b></small>
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
    nome_prod = st.text_input("Nome do Produto (ex: Luminária Capivara 3D)")
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
  st.subheader("Lista de Produtos Cadastrados")
  df_prods = run_query("SELECT * FROM produtos")
  if not df_prods.empty:
    st.dataframe(df_prods, width="stretch")
  else:
    st.info("Nenhum produto cadastrado.")

# --- TELA 3: GERADOR COM IA DO GEMINI ---
elif menu == "🎬 Gerador com IA do Gemini":
  st.title("🎬 Gerador de Pacote Inteligente (Powered by Gemini)")
  st.markdown(
      "A IA lê o produto cadastrado e cria roteiros, prompts e legendas"
      " otimizados."
  )

  if not IA_DISPONIVEL:
    st.error("⚠️ Chave da API do Gemini não configurada nos 'Secrets'.")

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
      with st.spinner(
          "A Inteligência Artificial está estruturando seu pacote..."
      ):
        prompt_sistema = f"""
                Atue como um estrategista especialista em marketing de afiliados para o projeto 'Achados do Felipe'.
                Gere um pacote completo de conteúdo em português 100% natural do Brasil para o produto: '{prod_escolhido}'.
                O formato escolhido é: '{formato_midia}'.
                
                Estruture a resposta exatamente com os seguintes tópicos em Markdown:
                ### 🎯 1. GANCHOS E TÍTULOS (0 a 3 segundos)
                (Duas opções de ganchos fortes)
                
                ### 🎬 2. ROTEIRO & PROMPT DE CRIAÇÃO
                (Prompt detalhado em inglês para IA de vídeo/imagem e dicas de direção)
                
                ### 📱 3. TEXTOS E LEGENDAS POR REDE SOCIAL
                (Legenda para TikTok/Instagram e título/descrição rica para o Pinterest)
                
                ### #️⃣ 4. HASHTAGS E INSIGHTS
                (Hashtags estratégicas e CTA para sacolinha amarela)
                """

        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt_sistema,
        )
        pacote_gerado = response.text

        st.success("Pacote gerado com sucesso!")
        st.markdown(pacote_gerado)

        if st.button("💾 Salvar na Central de Pendentes"):
          run_query(
              """
                        INSERT INTO conteudos (produto_id, titulo, tipo_midia, pacote_completo, status)
                        VALUES (?, ?, ?, ?, 'Pendente 🟡')
                    """,
              (prod_id, f"Campanha: {prod_escolhido}", formato_midia, pacote_gerado),
              fetch=False,
          )
          st.success(
              "Salvo com sucesso! Acesse a aba 'Central de Pendentes' para"
              " visualizar e gerenciar."
          )
  else:
    st.warning("Cadastre um produto na aba de Catálogo primeiro.")

# --- TELA 4: CENTRAL DE PENDENTES (COM BOTÕES DE CÓPIA RÁPIDA) ---
elif menu == "📋 Central de Pendentes (Kanban)":
  st.title("📋 Central de Pendentes & Redes Sociais")
  st.markdown(
      "Abra o card do produto, copie o que precisar com um toque e marque as"
      " redes onde já postou."
  )

  # Botão de Exportar para Excel
  df_full = run_query("""
        SELECT c.id, p.nome as produto, c.titulo, c.tipo_midia, c.status, 
               c.post_tiktok, c.post_instagram, c.post_pinterest, c.post_shopee 
        FROM conteudos c 
        LEFT JOIN produtos p ON c.produto_id = p.id
    """)

  if not df_full.empty:
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine="xlsxwriter") as writer:
      df_full.to_excel(writer, index=False, sheet_name="Pendentes_Achados")
    excel_data = output.getvalue()

    st.download_button(
        label="📥 Exportar Dados para Excel (.xlsx)",
        data=excel_data,
        file_name="central_achados_felipe.xlsx",
        mime=(
            "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        ),
    )
    st.markdown("---")

  df_kanban = run_query("""
        SELECT c.id, p.nome as produto, c.titulo, c.tipo_midia, c.status, 
               c.post_tiktok, c.post_instagram, c.post_pinterest, c.post_shopee, c.pacote_completo 
        FROM conteudos c 
        LEFT JOIN produtos p ON c.produto_id = p.id 
        WHERE c.status != 'Concluído ✔️'
        ORDER BY c.id DESC
    """)

  if not df_kanban.empty:
    for _, row in df_kanban.iterrows():
      with st.expander(f"🟡 [{row['produto']}] - {row['titulo']}"):
        st.markdown(f"**Tipo de Mídia:** {row['tipo_midia']}")
        st.markdown("---")

        # Exibe o texto completo
        texto_pacote = row["pacote_completo"]
        st.markdown(texto_pacote)

        # Botão nativo do Streamlit para copiar o pacote inteiro para a área de transferência
        st.code(texto_pacote, language="markdown")
        st.info(
            "👆 *Dica:* O bloco acima possui um botão de cópia rápida no canto"
            " superior direito para copiar todo o roteiro de uma vez só!"
        )

        st.markdown("---")
        st.markdown("**Checklist de Postagem por Rede:**")
        col1, col2, col3, col4 = st.columns(4)

        with col1:
          t = st.checkbox(
              "TikTok",
              value=bool(row["post_tiktok"]),
              key=f"tik_{row['id']}",
          )
        with col2:
          i = st.checkbox(
              "Instagram",
              value=bool(row["post_instagram"]),
              key=f"ig_{row['id']}",
          )
        with col3:
          p = st.checkbox(
              "Pinterest",
              value=bool(row["post_pinterest"]),
              key=f"pin_{row['id']}",
          )
        with col4:
          s = st.checkbox(
              "Shopee",
              value=bool(row["post_shopee"]),
              key=f"shp_{row['id']}",
          )

        if (
            t != bool(row["post_tiktok"])
            or i != bool(row["post_instagram"])
            or p != bool(row["post_pinterest"])
            or s != bool(row["post_shopee"])
        ):
          run_query(
              """
                        UPDATE conteudos 
                        SET post_tiktok = ?, post_instagram = ?, post_pinterest = ?, post_shopee = ?
                        WHERE id = ?
                    """,
              (int(t), int(i), int(p), int(s), row["id"]),
              fetch=False,
          )
          st.rerun()

        st.markdown("")
        if st.button("Concluir e remover da Central ✔️", key=f"concluir_{row['id']}"):
          run_query(
              "UPDATE conteudos SET status = 'Concluído ✔️' WHERE id = ?",
              (row["id"],),
              fetch=False,
          )
          st.success("Conteúdo concluído e arquivado!")
          st.rerun()
  else:
    st.success(
        "🎉 Nenhum item pendente na central! Todos os conteúdos foram"
        " postados e concluídos."
    )
