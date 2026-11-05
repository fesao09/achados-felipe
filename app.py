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
            redes_alvo TEXT,
            estrategia_ia TEXT,
            
            -- TIKTOK SEPARADO --
            tik_titulo_video TEXT,
            tik_legenda TEXT,
            
            -- INSTAGRAM SEPARADO --
            insta_titulo_video TEXT,
            insta_legenda TEXT,
            
            -- PINTEREST SEPARADO --
            pin_titulo TEXT,
            pin_descricao TEXT,
            
            -- SHOPEE VIDEO SEPARADO --
            shp_legenda TEXT,
            
            -- PROMPT IA --
            prompt_ia TEXT,
            
            post_tiktok INTEGER DEFAULT 0,
            post_instagram INTEGER DEFAULT 0,
            post_pinterest INTEGER DEFAULT 0,
            post_shopee INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pendente 🟡',
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)
  # Garante compatibilidade de colunas caso o banco seja antigo
  for col in [
      "redes_alvo",
      "estrategia_ia",
      "tik_titulo_video",
      "tik_legenda",
      "insta_titulo_video",
      "insta_legenda",
      "pin_titulo",
      "pin_descricao",
      "shp_legenda",
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
        SELECT c.id, p.nome as produto, c.status 
        FROM conteudos c 
        LEFT JOIN produtos p ON c.produto_id = p.id 
        ORDER BY c.id DESC LIMIT 5
    """)
  if not df_recentes.empty:
    for _, row in df_recentes.iterrows():
      st.markdown(
          f"""
            <div class="card">
                <b>📦 {row['produto']}</b><br>
                <small>Status: <b>{row['status']}</b></small>
            </div>
            """,
          unsafe_allow_html=True,
      )
  else:
    st.info("Nenhum conteúdo gerado ainda.")

# --- TELA 2: PRODUTOS (IMPORTAÇÃO COM SUGESTÃO DE CATEGORIA PELA IA) ---
elif menu == "📦 Catálogo de Produtos":
  st.title("📦 Gestão de Produtos & Afiliados")
  st.markdown(
      "Cole o texto bruto da Shopee. A IA limpa o título, extrai o link e"
      " sugere a categoria ideal automaticamente!"
  )

  with st.form("form_importacao_produto"):
    texto_bruto = st.text_input(
        "Cole o Texto/Link Bruto da Shopee aqui:",
        placeholder="Ex: Olha que achado incrível https://s.shopee.com.br/... Capa de Almofada BTS...",
    )
    submit_import = st.form_submit_button(
        "Importar e Cadastrar Produto com IA 🚀"
    )

    if submit_import and texto_bruto:
      if not IA_DISPONIVEL:
        st.error("⚠️ Chave da API do Gemini não configurada nos 'Secrets'.")
      else:
        with st.spinner(
            "A IA está limpando o título, extraindo o link e definindo a"
            " categoria..."
        ):
          prompt_extracao = f"""
                    Analise o texto bruto compartilhado de um produto de afiliado abaixo:
                    "{texto_bruto}"
                    
                    Sua tarefa é extrair três informações e responder estritamente usando estas tags:
                    [NOME] (Um título limpo, comercial e atraente para o produto)
                    [LINK] (Apenas a URL do link de afiliado encontrada no texto)
                    [CATEGORIA] (Defina uma categoria adequada e específica para este produto, ex: K-pop / Decoração, Moda Praia, Eletrônicos, Cozinha, etc.)
                    """
          response = client.models.generate_content(
              model="gemini-2.5-flash",
              contents=prompt_extracao,
          )
          resultado = response.text

          nome_extraido, link_extraido, nicho_extraido = "", "", "Geral"
          try:
            partes = resultado.split("[")
            for p in partes:
              if p.startswith("NOME]"):
                nome_extraido = p.replace("NOME]", "").strip()
              elif p.startswith("LINK]"):
                link_extraido = p.replace("LINK]", "").strip()
              elif p.startswith("CATEGORIA]"):
                nicho_extraido = p.replace("CATEGORIA]", "").strip()
          except Exception:
            nome_extraido = "Produto Importado Shopee"

          if not nome_extraido:
            nome_extraido = "Produto Importado Shopee"

          run_query(
              "INSERT INTO produtos (nome, nicho, link_afiliado) VALUES (?, ?, ?)",
              (nome_extraido, nicho_extraido, link_extraido),
              fetch=False,
          )
          st.success(
              f"🎉 Produto '{nome_extraido}' (Categoria: {nicho_extraido})"
              " importado com sucesso!"
          )

  st.markdown("---")
  st.subheader("Lista de Produtos Cadastrados")
  df_prods = run_query("SELECT * FROM produtos")
  if not df_prods.empty:
    st.dataframe(df_prods, width="stretch")
  else:
    st.info("Nenhum produto cadastrado.")

# --- TELA 3: GERADOR COM IA INTELIGENTE (CAMPOS SEPARADOS) ---
elif menu == "🎬 Gerador com IA Inteligente":
  st.title("🎬 Gerador Estratégico de Conteúdo")
  st.markdown(
      "A IA gera os textos perfeitamente isolados por campo para facilitar a"
      " cópia."
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
        else "Link de afiliado"
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

    if st.button("Gerar Pacote Separado com IA 🚀") and IA_DISPONIVEL:
      if not redes_escolhidas:
        st.warning(
            "Selecione pelo menos uma rede social para direcionar a IA."
        )
      else:
        with st.spinner(
            "A IA está gerando cada campo isolado e estruturado..."
        ):
          prompt_sistema = f"""
                    Atue como um estrategista sênior especialista em marketing de afiliados para o projeto 'Achados do Felipe'.
                    Analise o produto: '{prod_escolhido}' (Categoria: {nicho_prod}, Link: {link_afiliado}).
                    As redes de destino escolhidas são: '{redes_str}'.
                    
                    REGRAS DE PLATAFORMA:
                    - TikTok: Gancho forte de 0-3s e CTA para a sacolinha amarela.
                    - Instagram: Título para capa/reels e legenda com CTA para link na bio ou direct. NUNCA fale em sacolinha amarela.
                    - Pinterest: Título forte para o Pin e descrição rica em SEO voltada para busca visual.
                    - Shopee Vídeos: Legenda com CTA para o link da vitrine da Shopee. NUNCA fale em sacolinha amarela.
                    
                    Responda estritamente utilizando estas tags exatas para que cada campo fique totalmente isolado:
                    
                    [ESTRATEGIA]
                    (Explique em 1 frase curta o formato ideal: Vídeo Dinâmico ou Carrossel)
                    
                    [TIK_TITULO]
                    (Texto curto para colocar na tela / gancho de 0-3s para o TikTok)
                    
                    [TIK_LEGENDA]
                    (Legenda otimizada para o TikTok com hashtags e sacolinha amarela)
                    
                    [INSTA_TITULO]
                    (Título de capa ou carrossel para o Instagram)
                    
                    [INSTA_LEGENDA]
                    (Legenda otimizada para o Instagram com link na bio e hashtags)
                    
                    [PIN_TITULO]
                    (Título otimizado para o Pin do Pinterest)
                    
                    [PIN_DESCRICAO]
                    (Descrição rica em SEO para o Pinterest)
                    
                    [SHP_LEGENDA]
                    (Legenda otimizada para Shopee Vídeos)
                    
                    [PROMPT_IA]
                    (Prompt técnico em inglês limpo e direto com até 900 caracteres para gerar a mídia)
                    """

          response = client.models.generate_content(
              model="gemini-2.5-flash",
              contents=prompt_sistema,
          )
          texto_gerado = response.text

          estrategia, tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia = (
              "",
              "",
              "",
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
              if p.startswith("ESTRATEGIA]"):
                estrategia = p.replace("ESTRATEGIA]", "").strip()
              elif p.startswith("TIK_TITULO]"):
                tik_tit = p.replace("TIK_TITULO]", "").strip()
              elif p.startswith("TIK_LEGENDA]"):
                tik_leg = p.replace("TIK_LEGENDA]", "").strip()
              elif p.startswith("INSTA_TITULO]"):
                insta_tit = p.replace("INSTA_TITULO]", "").strip()
              elif p.startswith("INSTA_LEGENDA]"):
                insta_leg = p.replace("INSTA_LEGENDA]", "").strip()
              elif p.startswith("PIN_TITULO]"):
                pin_tit = p.replace("PIN_TITULO]", "").strip()
              elif p.startswith("PIN_DESCRICAO]"):
                pin_desc = p.replace("PIN_DESCRICAO]", "").strip()
              elif p.startswith("SHP_LEGENDA]"):
                shp_leg = p.replace("SHP_LEGENDA]", "").strip()
              elif p.startswith("PROMPT_IA]"):
                prompt_ia = p.replace("PROMPT_IA]", "").strip()
          except Exception:
            tik_tit = texto_gerado

          run_query(
              """
                    INSERT INTO conteudos (
                        produto_id, redes_alvo, estrategia_ia, 
                        tik_titulo_video, tik_legenda, 
                        insta_titulo_video, insta_legenda, 
                        pin_titulo, pin_descricao, 
                        shp_legenda, prompt_ia, status
                    )
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendente 🟡')
                """,
              (
                  prod_id,
                  redes_str,
                  estrategia
                  if estrategia
                  else "Formato Otimizado por IA",
                  tik_tit,
                  tik_leg,
                  insta_tit,
                  insta_leg,
                  pin_tit,
                  pin_desc,
                  shp_leg,
                  prompt_ia,
              ),
              fetch=False,
          )

          st.success(
              "🎉 Pacote gerado com campos 100% separados e salvo na Central!"
          )
          st.markdown(texto_gerado)
  else:
    st.warning("Cadastre um produto na aba de Catálogo primeiro.")

# --- TELA 4: CENTRAL DE PENDENTES (CAMPOS ISOLADOS COM BOTÕES DE CÓPIA) ---
elif menu == "📋 Central de Pendentes (Kanban)":
  st.title("📋 Central de Pendentes & Redes Sociais")
  st.markdown(
      "Cada informação está em sua própria caixinha isolada para você copiar"
      " exatamente o que precisa."
  )

  df_kanban = run_query("""
        SELECT c.id, p.nome as produto, p.nicho, p.link_afiliado, c.redes_alvo, c.estrategia_ia, c.status, 
               c.post_tiktok, c.post_instagram, c.post_pinterest, c.post_shopee, 
               c.tik_titulo_video, c.tik_legenda, c.insta_titulo_video, c.insta_legenda, 
               c.pin_titulo, c.pin_descricao, c.shp_legenda, c.prompt_ia 
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
      nicho_prod = (
          row["nicho"] if pd.notna(row["nicho"]) and row["nicho"] else "Geral"
      )
      link_prod = (
          row["link_afiliado"]
          if pd.notna(row["link_afiliado"]) and row["link_afiliado"]
          else "Link na bio"
      )

      with st.expander(
          f"[{status_icone}] {nome_prod} | Categoria: {nicho_prod}"
      ):
        st.markdown(f"🤖 **Formato Ideal:** {row['estrategia_ia']}")
        st.markdown("---")

        # 1. INFORMAÇÕES GERAIS ISOLADAS
        st.markdown("### 📌 Informações do Produto")

        st.text_input(
            "Título do Produto", value=nome_prod, key=f"t_prod_{row['id']}"
        )
        st.text_input("Categoria", value=nicho_prod, key=f"t_nich_{row['id']}")
        st.text_input(
            "Link de Destino", value=link_prod, key=f"t_link_{row['id']}"
        )

        st.markdown("---")

        # 2. TIKTOK ISOLADO
        st.markdown("### 🎵 TikTok")
        st.text_input(
            "Título no Vídeo / Gancho (0-3s)",
            value=row["tik_titulo_video"] or "",
            key=f"tik_tit_{row['id']}",
        )
        st.text_area(
            "Legenda TikTok",
            value=row["tik_legenda"] or "",
            height=80,
            key=f"tik_leg_{row['id']}",
        )

        st.markdown("---")

        # 3. INSTAGRAM ISOLADO
        st.markdown("### 📸 Instagram / Reels / Carrossel")
        st.text_input(
            "Título no Vídeo / Capa",
            value=row["insta_titulo_video"] or "",
            key=f"insta_tit_{row['id']}",
        )
        st.text_area(
            "Legenda Instagram",
            value=row["insta_legenda"] or "",
            height=80,
            key=f"insta_leg_{row['id']}",
        )

        st.markdown("---")

        # 4. PINTEREST ISOLADO
        st.markdown("### 📌 Pinterest")
        st.text_input(
            "Título do Pin",
            value=row["pin_titulo"] or "",
            key=f"pin_tit_{row['id']}",
        )
        st.text_area(
            "Descrição SEO Pinterest",
            value=row["pin_descricao"] or "",
            height=80,
            key=f"pin_desc_{row['id']}",
        )

        st.markdown("---")

        # 5. SHOPEE VÍDEOS ISOLADO
        st.markdown("### 🛍️ Shopee Vídeos")
        st.text_area(
            "Legenda Shopee Vídeos",
            value=row["shp_legenda"] or "",
            height=80,
            key=f"shp_leg_{row['id']}",
        )

        st.markdown("---")

        # 6. PROMPT IA ISOLADO
        st.markdown("### 🤖 Prompt Técnico para IA")
        st.text_area(
            "Prompt de Mídia (Inglês)",
            value=row["prompt_ia"] or "",
            height=90,
            key=f"prompt_{row['id']}",
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
                "DELETE FROM conteudos WHERE id = ?", (row["id"],), fetch=False,
            )
            st.success("Item removido da central!")
            st.rerun()
  else:
    st.info("Nenhum conteúdo cadastrado na central ainda.")
