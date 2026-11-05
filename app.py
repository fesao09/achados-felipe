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

# Estilização CSS (Dark Mode / Moderno e Otimizado para Mobile)
st.markdown(
    """
    <style>
    .main { background-color: #121212; color: #ffffff; }
    .stSidebar { background-color: #181818; }
    h1, h2, h3 { color: #1DB954 !important; }
    .card { background-color: #282828; padding: 15px; border-radius: 12px; margin-bottom: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .metric-card { background-color: #282828; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- BANCO DE DADOS LOCAL ---
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
            redes_alvo TEXT,
            estrategia_ia TEXT,
            bloco_geral TEXT,
            bloco_tiktok TEXT,
            bloco_insta TEXT,
            bloco_pinterest TEXT,
            bloco_shopee TEXT,
            prompt_ia TEXT,
            post_tiktok INTEGER DEFAULT 0,
            post_instagram INTEGER DEFAULT 0,
            post_pinterest INTEGER DEFAULT 0,
            post_shopee INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pendente 🟡',
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)
  for col in [
      "redes_alvo",
      "estrategia_ia",
      "bloco_geral",
      "bloco_tiktok",
      "bloco_insta",
      "bloco_pinterest",
      "bloco_shopee",
      "prompt_ia",
  ]:
    try:
      cursor.execute(f"ALTER TABLE conteudos ADD COLUMN {col} TEXT")
    except sqlite3.OperationalError:
      pass

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
        "🎬 Gerador com IA Inteligente",
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
        f'<div class="metric-card"><h3>Conteúdos Concluídos</h3><h2>'
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

# --- TELA 2: PRODUTOS (IMPORTAÇÃO ESTILO WHATSAPP) ---
elif menu == "📦 Catálogo de Produtos":
  st.title("📦 Gestão de Produtos & Afiliados")
  st.markdown(
      "Cole abaixo o texto bruto compartilhado da Shopee. A IA limpa o título"
      " e extrai o link automaticamente!"
  )

  with st.form("form_importacao_produto"):
    texto_bruto = st.text_area(
        "Cole o Texto/Link Bruto da Shopee aqui:",
        placeholder="Ex: Olha que achado incrível https://s.shopee.com.br/... Capa de Almofada BTS...",
        height=100,
    )
    nicho_prod = st.selectbox(
        "Nicho", ["Moda Praia", "K-pop / Colecionáveis", "Beleza", "Casa"]
    )
    submit_import = st.form_submit_button(
        "Importar e Cadastrar Produto com IA 🚀"
    )

    if submit_import and texto_bruto:
      if not IA_DISPONIVEL:
        st.error("⚠️ Chave da API do Gemini não configurada nos 'Secrets'.")
      else:
        with st.spinner("A IA está limpando o título e extraindo o link..."):
          prompt_extracao = f"""
                    Analise o texto bruto compartilhado de um produto de afiliado abaixo:
                    "{texto_bruto}"
                    
                    Sua tarefa é extrair duas informações e responder estritamente usando estas tags:
                    [NOME] (Um título limpo, comercial e atraente para o produto)
                    [LINK] (Apenas a URL do link de afiliado encontrada no texto)
                    """
          response = client.models.generate_content(
              model="gemini-2.5-flash",
              contents=prompt_extracao,
          )
          resultado = response.text

          nome_extraido, link_extraido = "", ""
          try:
            partes = resultado.split("[")
            for p in partes:
              if p.startswith("NOME]"):
                nome_extraido = p.replace("NOME]", "").strip()
              elif p.startswith("LINK]"):
                link_extraido = p.replace("LINK]", "").strip()
          except Exception:
            nome_extraido = "Produto Importado Shopee"

          if not nome_extraido:
            nome_extraido = "Produto Importado Shopee"

          run_query(
              "INSERT INTO produtos (nome, nicho, link_afiliado) VALUES (?, ?, ?)",
              (nome_extraido, nicho_prod, link_extraido),
              fetch=False,
          )
          st.success(
              f"🎉 Produto '{nome_extraido}' importado e cadastrado com sucesso!"
          )

  st.markdown("---")
  st.subheader("Lista de Produtos Cadastrados")
  df_prods = run_query("SELECT * FROM produtos")
  if not df_prods.empty:
    st.dataframe(df_prods, width="stretch")
  else:
    st.info("Nenhum produto cadastrado.")

# --- TELA 3: GERADOR COM IA INTELIGENTE ---
elif menu == "🎬 Gerador com IA Inteligente":
  st.title("🎬 Gerador Estratégico de Conteúdo")
  st.markdown(
      "A IA analisa o produto, define o formato ideal e estrutura tudo em"
      " tópicos limpos."
  )

  if not IA_DISPONIVEL:
    st.error("⚠️ Chave da API do Gemini não configurada nos 'Secrets'.")

  df_produtos = run_query("SELECT id, nome, nicho, link_afiliado FROM produtos")
  if not df_produtos.empty:
    prod_escolhido = st.selectbox(
        "Selecione o Produto", df_produtos["nome"].tolist()
    )
    prod_row = df_produtos.loc[df_produtos["nome"] == prod_escolhido].iloc[0]
    prod_id = prod_row["id"]
    nicho_prod = prod_row["nicho"]
    link_afiliado = (
        prod_row["link_afiliado"]
        if prod_row["link_afiliado"]
        else "Link de afiliado na bio/vitrine"
    )

    st.markdown("### 🌐 Onde você pretende postar este conteúdo?")
    col_r1, col_r2, col_r3, col_r4 = st.columns(4)
    with col_r1:
      sel_tiktok = st.checkbox("TikTok", value=True)
    with col_r2:
      sel_insta = st.checkbox("Instagram", value=True)
    with col_r3:
      sel_pinterest = st.checkbox("Pinterest", value=True)
    with col_r4:
      sel_shopee = st.checkbox("Shopee Video", value=False)

    redes_escolhidas = []
    if sel_tiktok:
      redes_escolhidas.append("TikTok")
    if sel_insta:
      redes_escolhidas.append("Instagram")
    if sel_pinterest:
      redes_escolhidas.append("Pinterest")
    if sel_shopee:
      redes_escolhidas.append("Shopee Video")

    redes_str = (
        ", ".join(redes_escolhidas)
        if redes_escolhidas
        else "TikTok e Instagram"
    )

    if st.button("Analisar Produto e Gerar Pacote com IA 🚀") and IA_DISPONIVEL:
      if not redes_escolhidas:
        st.warning(
            "Selecione pelo menos uma rede social para direcionar a IA."
        )
      else:
        with st.spinner("A IA está estruturando o pacote por tópicos..."):
          prompt_sistema = f"""
                    Atue como um estrategista sênior especialista em marketing de afiliados para o projeto 'Achados do Felipe'.
                    Analise o produto: '{prod_escolhido}' (Nicho: {nicho_prod}, Link: {link_afiliado}).
                    As redes de destino escolhidas são: '{redes_str}'.
                    
                    REGRAS DE PLATAFORMA:
                    - TikTok: Foco em vídeo dinâmico, ganchos fortes de 0-3s e CTA para a sacolinha amarela.
                    - Instagram: Foco em carrossel ou reels, CTA para link na bio ou direct. NUNCA fale em sacolinha amarela.
                    - Pinterest: Título e descrição ricos em SEO focados em busca visual.
                    - Shopee Vídeos: Foco no link da vitrine da Shopee. NUNCA fale em sacolinha amarela.
                    
                    Responda estritamente usando estas tags para separação:
                    
                    [BLOCO_GERAL]
                    Título: {prod_escolhido}
                    Descrição: Descrição comercial envolvente destacando os benefícios do produto.
                    Categoria: {nicho_prod}
                    Link de destino: {link_afiliado}
                    Formato Ideal: (Vídeo Dinâmico ou Carrossel)
                    
                    [BLOCO_TIKTOK]
                    Título no Vídeo / Gancho (0-3s): 
                    Cenas / Roteiro rápido: 
                    Legenda: 
                    
                    [BLOCO_INSTA]
                    Título no Vídeo / Capa: 
                    Legenda: 
                    
                    [BLOCO_PINTEREST]
                    Título para o Pin: 
                    Descrição rica para SEO: 
                    
                    [BLOCO_SHOPEE]
                    Legenda para Shopee Vídeos: 
                    
                    [PROMPT_IA]
                    (Prompt técnico em inglês limpo e direto com até 900 caracteres para gerar a mídia)
                    """

          response = client.models.generate_content(
              model="gemini-2.5-flash",
              contents=prompt_sistema,
          )
          texto_gerado = response.text

          b_geral, b_tiktok, b_insta, b_pinterest, b_shopee, prompt_ia = (
              "",
              "",
              "",
              "",
              "",
              "",
          )
          try:
            partes = texto_gerado.split("[")
            for p in partes:
              if p.startswith("BLOCO_GERAL]"):
                b_geral = p.replace("BLOCO_GERAL]", "").strip()
              elif p.startswith("BLOCO_TIKTOK]"):
                b_tiktok = p.replace("BLOCO_TIKTOK]", "").strip()
              elif p.startswith("BLOCO_INSTA]"):
                b_insta = p.replace("BLOCO_INSTA]", "").strip()
              elif p.startswith("BLOCO_PINTEREST]"):
                b_pinterest = p.replace("BLOCO_PINTEREST]", "").strip()
              elif p.startswith("BLOCO_SHOPEE]"):
                b_shopee = p.replace("BLOCO_SHOPEE]", "").strip()
              elif p.startswith("PROMPT_IA]"):
                prompt_ia = p.replace("PROMPT_IA]", "").strip()
          except Exception:
            b_geral = texto_gerado

          run_query(
              """
                    INSERT INTO conteudos (produto_id, titulo, redes_alvo, bloco_geral, bloco_tiktok, bloco_insta, bloco_pinterest, bloco_shopee, prompt_ia, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendente 🟡')
                """,
              (
                  prod_id,
                  prod_escolhido,
                  redes_str,
                  b_geral,
                  b_tiktok,
                  b_insta,
                  b_pinterest,
                  b_shopee,
                  prompt_ia,
              ),
              fetch=False,
          )

          st.success(
              "🎉 Pacote estratégico em tópicos gerado e salvo na Central!"
          )
          st.markdown(texto_gerado)
  else:
    st.warning("Cadastre um produto na aba de Catálogo primeiro.")

# --- TELA 4: CENTRAL DE PENDENTES (FORMATO DE TÓPICOS LIMPOS) ---
elif menu == "📋 Central de Pendentes (Kanban)":
  st.title("📋 Central de Pendentes & Redes Sociais")
  st.markdown(
      "Acompanhe seus produtos em formato de tópicos limpos, com botões de"
      " cópia rápida."
  )

  df_kanban = run_query("""
        SELECT c.id, p.nome as produto, c.titulo, c.redes_alvo, c.status, 
               c.post_tiktok, c.post_instagram, c.post_pinterest, c.post_shopee, 
               c.bloco_geral, c.bloco_tiktok, c.bloco_insta, c.bloco_pinterest, c.bloco_shopee, c.prompt_ia 
        FROM conteudos c 
        LEFT JOIN produtos p ON c.produto_id = p.id 
        ORDER BY c.id DESC
    """)

  if not df_kanban.empty:
    for _, row in df_kanban.iterrows():
      status_icone = (
          "✔️" if "Concluído" in str(row["status"]) else "🟡 Pendente"
      )
      nome_prod = (
          row["produto"]
          if pd.notna(row["produto"]) and row["produto"]
          else "Produto"
      )

      with st.expander(f"[{status_icone}] {nome_prod} ({row['redes_alvo']})"):
        st.markdown("---")

        # Exibição em formato de tópicos limpos com caixas de código para cópia fácil
        if row["bloco_geral"]:
          st.markdown("### 📌 Informações Gerais")
          st.code(row["bloco_geral"], language="markdown")

        if row["bloco_tiktok"]:
          st.markdown("### 🎵 TikTok")
          st.code(row["bloco_tiktok"], language="markdown")

        if row["bloco_insta"]:
          st.markdown("### 📸 Instagram / Reels")
          st.code(row["bloco_insta"], language="markdown")

        if row["bloco_pinterest"]:
          st.markdown("### 📌 Pinterest")
          st.code(row["bloco_pinterest"], language="markdown")

        if row["bloco_shopee"]:
          st.markdown("### 🛍️ Shopee Vídeo")
          st.code(row["bloco_shopee"], language="markdown")

        if row["prompt_ia"]:
          st.markdown("### 🤖 Prompt Técnico para IA")
          st.code(row["prompt_ia"], language="markdown")

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
          p_net = st.checkbox(
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
            or p_net != bool(row["post_pinterest"])
            or s != bool(row["post_shopee"])
        ):
          run_query(
              """
                        UPDATE conteudos 
                        SET post_tiktok = ?, post_instagram = ?, post_pinterest = ?, post_shopee = ?
                        WHERE id = ?
                    """,
              (int(t), int(i), int(p_net), int(s), row["id"]),
              fetch=False,
          )
          st.rerun()

        st.markdown("")
        col_btn1, col_btn2 = st.columns(2)
        with col_btn1:
          if st.button("Marcar como Concluído ✔️", key=f"concluir_{row['id']}"):
            run_query(
                "UPDATE conteudos SET status = 'Concluído ✔️' WHERE id = ?",
                (row["id"],),
                fetch=False,
            )
            st.success("Conteúdo marcado como concluído!")
            st.rerun()
        with col_btn2:
          if st.button("Excluir Item 🗑️", key=f"excluir_{row['id']}"):
            run_query(
                "DELETE FROM conteudos WHERE id = ?", (row["id"],), fetch=False
            )
            st.success("Item removido da central!")
            st.rerun()
  else:
    st.info("Nenhum conteúdo cadastrado na central ainda.")
