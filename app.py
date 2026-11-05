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
            ganchos TEXT,
            prompt_ia TEXT,
            legendas TEXT,
            hashtags TEXT,
            post_tiktok INTEGER DEFAULT 0,
            post_instagram INTEGER DEFAULT 0,
            post_pinterest INTEGER DEFAULT 0,
            post_shopee INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pendente 🟡',
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)
  # Garante compatibilidade de colunas caso o banco seja antigo
  for col in ["redes_alvo", "estrategia_ia", "ganchos", "prompt_ia", "legendas", "hashtags"]:
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

# --- TELA 2: PRODUTOS ---
elif menu == "📦 Catálogo de Produtos":
  st.title("📦 Gestão de Produtos & Afiliados")

  with st.form("form_produto"):
    st.subheader("Cadastrar Novo Produto")
    nome_prod = st.text_input("Nome do Produto")
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

# --- TELA 3: GERADOR COM IA INTELIGENTE (ESCOLHA DE REDES + ANÁLISE DE FORMATO) ---
elif menu == "🎬 Gerador com IA Inteligente":
  st.title("🎬 Gerador Estratégico de Conteúdo")
  st.markdown(
      "A IA analisa o produto, define automaticamente o melhor formato (Vídeo"
      " Dinâmico ou Carrossel) e monta os textos para as redes que você"
      " escolher."
  )

  if not IA_DISPONIVEL:
    st.error("⚠️ Chave da API do Gemini não configurada nos 'Secrets'.")

  df_produtos = run_query("SELECT id, nome FROMprodutos")
  if not df_produtos.empty:
    prod_escolhido = st.selectbox(
        "Selecione o Produto", df_produtos["nome"].tolist()
    )
    prod_id = df_produtos.loc[
        df_produtos["nome"] == prod_escolhido, "id"
    ].values[0]

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

    # Coleta quais redes foram selecionadas
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
        with st.spinner(
            "A IA está analisando o produto e decidindo o melhor formato"
            " (Vídeo ou Carrossel)..."
        ):
          prompt_sistema = f"""
                    Atue como um estrategista sênior especialista em marketing de afiliados para o projeto 'Achados do Felipe'.
                    Analise o produto: '{prod_escolhido}'.
                    As redes de destino escolhidas pelo usuário são: '{redes_str}'.
                    
                    Sua tarefa:
                    1. Decida estrategicamente se este produto performa melhor com um [Vídeo Dinâmico], [Vídeo Simples] ou [Carrossel / Imagem Estática] com base nas características dele e nas redes de destino.
                    2. Escreva uma breve [ESTRATEGIA] explicando por que escolheu esse formato.
                    3. Gere o conteúdo em português 100% natural do Brasil.
                    
                    Responda estritamente usando estas tags exatas para separação:
                    
                    [ESTRATEGIA]
                    (Explique em 1 frase curta o formato ideal escolhido pela IA para este produto)
                    
                    [GANCHOS]
                    (Insira opções de ganchos fortes adaptados para as redes escolhidas)
                    
                    [PROMPT_IA]
                    (Insira o prompt técnico em inglês otimizado para gerar a mídia ideal - seja vídeo ou carrossel)
                    
                    [LEGENDAS]
                    (Insira legendas e descrições otimizadas para as redes de destino selecionadas)
                    
                    [HASHTAGS]
                    (Insira hashtags estratégicas e CTA para a sacolinha amarela)
                    """

          response = client.models.generate_content(
              model="gemini-2.5-flash",
              contents=prompt_sistema,
          )
          texto_gerado = response.text

          # Fatiamento inteligente dos blocos
          estrategia, ganchos, prompt_ia, legendas, hashtags = (
              "",
              "",
              "",
              "",
              "",
          )
          try:
            partes = texto_gerado.split("[")
            for p in partes:
              if p.startswith("ESTRATEGIA]"):
                estrategia = p.replace("ESTRATEGIA]", "").strip()
              elif p.startswith("GANCHOS]"):
                ganchos = p.replace("GANCHOS]", "").strip()
              elif p.startswith("PROMPT_IA]"):
                prompt_ia = p.replace("PROMPT_IA]", "").strip()
              elif p.startswith("LEGENDAS]"):
                legendas = p.replace("LEGENDAS]", "").strip()
              elif p.startswith("HASHTAGS]"):
                hashtags = p.replace("HASHTAGS]", "").strip()
          except Exception:
            ganchos = texto_gerado

          # Salva no banco com a estratégia de formato escolhida pela IA
          run_query(
              """
                    INSERT INTO conteudos (produto_id, titulo, redes_alvo, estrategia_ia, ganchos, prompt_ia, legendas, hashtags, status)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'Pendente 🟡')
                """,
              (
                  prod_id,
                  f"Campanha: {prod_escolhido}",
                  redes_str,
                  estrategia
                  if estrategia
                  else "Formato Otimizado por IA (Vídeo/Carrossel)",
                  ganchos,
                  prompt_ia,
                  legendas,
                  hashtags,
              ),
              fetch=False,
          )

          st.success(
              "🎉 Análise concluída! O pacote estratégico foi salvo na Central"
              " de Pendentes."
          )
          st.markdown(texto_gerado)
  else:
    st.warning("Cadastre um produto na aba de Catálogo primeiro.")

# --- TELA 4: CENTRAL DE PENDENTES (KANBAN) ---
elif menu == "📋 Central de Pendentes (Kanban)":
  st.title("📋 Central de Pendentes & Redes Sociais")
  st.markdown(
      "Acompanhe o formato escolhido pela IA, copie os blocos separadamente e"
      " marque as postagens."
  )

  df_kanban = run_query("""
        SELECT c.id, p.nome as produto, c.titulo, c.redes_alvo, c.estrategia_ia, c.status, 
               c.post_tiktok, c.post_instagram, c.post_pinterest, c.post_shopee, 
               c.ganchos, c.prompt_ia, c.legendas, c.hashtags 
        FROM conteudos c 
        LEFT JOIN produtos p ON c.produto_id = p.id 
        ORDER BY c.id DESC
    """)

  if not df_kanban.empty:
    for _, row in df_kanban.iterrows():
      status_icone = (
          "✔️" if "Concluído" in str(row["status"]) else "🟡 Pendente"
      )
      estrategia_tag = (
          f" | 🤖 *{row['estrategia_ia']}*" if row["estrategia_ia"] else ""
      )

      with st.expander(
          f"[{status_icone}] {row['produto']} (Redes: {row['redes_alvo']})"
      ):
        st.markdown(f"**Estratégia Definida pela IA:** {estrategia_tag}")
        st.markdown("---")

        g = (
            row["ganchos"]
            if row["ganchos"]
            else "Conteúdo salvo no formato legado."
        )
        p = row["prompt_ia"] if row["prompt_ia"] else "N/A"
        l = row["legendas"] if row["legendas"] else "N/A"
        h = row["hashtags"] if row["hashtags"] else "N/A"

        st.markdown("### 🎯 1. Ganchos e Títulos")
        st.code(g, language="markdown")

        st.markdown("### 🎬 2. Prompt Estratégico (Vídeo / Carrossel)")
        st.code(p, language="markdown")

        st.markdown("### 📱 3. Textos e Legendas")
        st.code(l, language="markdown")

        st.markdown("### #️⃣ 4. Hashtags e CTA")
        st.code(h, language="markdown")

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
