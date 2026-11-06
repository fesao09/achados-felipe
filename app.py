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
    initial_sidebar_state="collapsed",
)

# Estilização CSS (Dark Mode / Moderno e Otimizado para Mobile)
st.markdown(
    """
    <style>
    .main { background-color: #121212; color: #ffffff; }
    h1, h2, h3 { color: #1DB954 !important; }
    .card { background-color: #282828; padding: 15px; border-radius: 12px; margin-bottom: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); }
    .metric-card { background-color: #282828; padding: 15px; border-radius: 10px; text-align: center; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- BANCO DE DADOS LOCAL & LIMPEZA DE LEGADO ---
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
            tik_titulo_video TEXT,
            tik_legenda TEXT,
            insta_titulo_video TEXT,
            insta_legenda TEXT,
            pin_titulo TEXT,
            pin_descricao TEXT,
            shp_legenda TEXT,
            prompt_ia TEXT,
            post_tiktok INTEGER DEFAULT 0,
            post_instagram INTEGER DEFAULT 0,
            post_pinterest INTEGER DEFAULT 0,
            post_shopee INTEGER DEFAULT 0,
            status TEXT DEFAULT 'Pendente 🟡',
            FOREIGN KEY(produto_id) REFERENCES produtos(id)
        )
    """)

  cursor.execute(
      "DELETE FROM conteudos WHERE produto_id NOT IN (SELECT id FROM"
      " produtos)"
  )
  cursor.execute("DELETE FROM produtos WHERE nome IS NULL OR nome = 'None'")

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

# --- NAVEGAÇÃO SUPERIOR (OTIMIZADA PARA CELULAR) ---
st.title("🚀 Central Achados do Felipe")

menu = st.radio(
    "Navegação Rápida",
    [
        "🎬 Gerador Inteligente",
        "📋 Central de Pendentes",
        "📦 Catálogo",
        "📊 Dashboard & Metas",
    ],
    horizontal=True,
)

st.markdown("---")

# --- TELA 1: GERADOR COM IA INTELIGENTE ---
if menu == "🎬 Gerador Inteligente":
  st.markdown("### 🎬 Gerador Estratégico de Conteúdo")
  st.markdown(
      "A IA aplica rigorosamente as regras de cada rede e estrutura os campos"
      " com segurança."
  )

  if not IA_DISPONIVEL:
    st.error("⚠️ Chave da API do Gemini não configurada nos 'Secrets'.")

  df_produtos = run_query("""
        SELECT id, nome, nicho, link_afiliado 
        FROM produtos 
        WHERE id NOT IN (SELECT produto_id FROM conteudos WHERE produto_id IS NOT NULL)
    """)

  if not df_produtos.empty:
    prod_escolhido = st.selectbox(
        "Selecione o Produto", df_produtos["nome"].tolist()
    )
    prod_row = df_produtos.loc[df_produtos["nome"] == prod_escolhido].iloc[0]
    prod_id = prod_row["id"]
    nicho_prod = prod_row["nicho"]
    link_afiliado = (
        prod_row["link_afiliado"]
        if pd.notna(prod_row["link_afiliado"])
        else "Link de afiliado"
    )

    st.markdown("**🌐 Onde você pretende postar este conteúdo?**")
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

    if st.button("Gerar Pacote Estratégico com IA 🚀") and IA_DISPONIVEL:
      if not redes_escolhidas:
        st.warning(
            "Selecione pelo menos uma rede social para direcionar a IA."
        )
      else:
        with st.spinner("A IA está estruturando o pacote com segurança..."):
          prompt_sistema = f"""
                    Atue como um estrategista sênior especialista em marketing de afiliados para o projeto 'Achados do Felipe'.
                    Analise o produto: '{prod_escolhido}' (Categoria: {nicho_prod}, Link: {link_afiliado}).
                    As redes de destino escolhidas são: '{redes_str}'.
                    
                    REGRAS RIGOROSAS DE PLATAFORMA (OBRIGATÓRIO SEGUIR):
                    1. TIKTOK: Foco em vídeo dinâmico, ganchos fortes de 0-3s e CTA obrigatório para a 'sacolinha amarela'.
                    2. INSTAGRAM: Título para capa/reels e legenda com CTA para 'link na bio' ou 'direct'. PROIBIDO falar em sacolinha amarela.
                    3. PINTEREST: O título deve ser focado estritamente em PALAVRAS-CHAVE DE BUSCA (SEO para intenção de pesquisa do usuário). A descrição deve ser rica, detalhada e engajadora com até 800 caracteres voltada para descoberta visual.
                    4. SHOPEE VÍDEOS: A legenda deve ser ULTRA CURTA, tendo no MÁXIMO 150 CARACTERES (já contando com as hashtags e o espaço), com CTA para o link da vitrine/comentários. PROIBIDO falar em sacolinha amarela.
                    
                    Responda estritamente utilizando estas tags exatas para separação:
                    
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
                    (Título SEO altamente voltado para palavras-chave de busca no Pinterest)
                    
                    [PIN_DESCRICAO]
                    (Descrição rica em SEO e detalhada com até 800 caracteres para o Pinterest)
                    
                    [SHP_LEGENDA]
                    (Legenda EXTREMAMENTE CURTA para Shopee Vídeos: máximo de 150 caracteres incluindo hashtags, citando link da vitrine)
                    
                    [PROMPT_IA]
                    (Prompt técnico em inglês limpo e direto com até 900 caracteres para gerar a mídia)
                    """

          try:
            response = client.models.generate_content(
                model="gemini-2.5-flash",
                contents=prompt_sistema,
            )
            texto_gerado = response.text

            # Valores padrão caso alguma tag falhe
            estrategia = "Formato Otimizado por IA"
            tik_tit = f"Olha esse achado: {prod_escolhido}"
            tik_leg = f"Achado incrível! Garanta já o seu na sacolinha amarela. {link_afiliado} #achados #shopee"
            insta_tit = f"{prod_escolhido} que você precisa!"
            insta_leg = f"Olha que item incrível para o seu dia a dia! Link na bio. {link_afiliado} #achados #reels"
            pin_tit = f"{prod_escolhido} imperdível"
            pin_desc = f"Descubra todos os detalhes sobre {prod_escolhido}. Excelente opção para quem busca qualidade e praticidade. Confira o link para saber mais!"
            shp_leg = f"Achado imperdível! Confira na vitrine. {link_afiliado}"
            prompt_ia = f"Professional product showcase video of {prod_escolhido}, clean lighting, high quality."

            # Fatiamento seguro por partes
            if "[ESTRATEGIA]" in texto_gerado:
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
                pass
            else:
              # Fallback caso a IA responda em texto corrido sem tags
              tik_tit = texto_gerado[:100]

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
                    estrategia,
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
                "🎉 Pacote gerado com sucesso! Salvo na Central de Pendentes."
            )
            st.rerun()

          except Exception as e:
            st.error(
                f"⚠️ Erro ao comunicar com a IA: {e}. Tente novamente em"
                " instantes."
            )
  else:
    st.info(
        "🎉 Todos os produtos cadastrados já tiveram seus roteiros gerados!"
        " Cadastre novos produtos na aba de Catálogo."
    )

# --- TELA 2: CENTRAL DE PENDENTES (KANBAN LIMPO) ---
elif menu == "📋 Central de Pendentes":
  st.markdown("### 📋 Central de Pendentes & Redes Sociais")
  st.markdown(
      "Copie os textos isolados por campo e marque as redes onde já postou."
  )

  df_kanban = run_query("""
        SELECT c.id, p.nome as produto, p.nicho, p.link_afiliado, c.redes_alvo, c.estrategia_ia, c.status, 
               c.post_tiktok, c.post_instagram, c.post_pinterest, c.post_shopee, 
               c.tik_titulo_video, c.tik_legenda, c.insta_titulo_video, c.insta_legenda, 
               c.pin_titulo, c.pin_descricao, c.shp_legenda, c.prompt_ia 
        FROM conteudos c 
        LEFT JOIN produtos p ON c.produto_id = p.id 
        WHERE p.nome IS NOT NULL
        ORDER BY c.id DESC
    """)

  if not df_kanban.empty:
    for _, row in df_kanban.iterrows():
      status_icone = (
          "✔️" if "Concluído" in str(row["status"]) else "🟡 Pendente"
      )
      nome_prod = row["produto"] if pd.notna(row["produto"]) else "Produto"
      nicho_prod = row["nicho"] if pd.notna(row["nicho"]) else "Geral"
      link_prod = (
          row["link_afiliado"] if pd.notna(row["link_afiliado"]) else "Link"
      )

      with st.expander(
          f"[{status_icone}] {nome_prod} | Categoria: {nicho_prod}"
      ):
        st.markdown(f"🤖 **Formato Ideal:** {row['estrategia_ia']}")
        st.markdown("---")

        st.markdown("### 📌 Informações do Produto")
        st.text_input(
            "Título do Produto", value=nome_prod, key=f"t_prod_{row['id']}"
        )
        st.text_input("Categoria", value=nicho_prod, key=f"t_nich_{row['id']}")
        st.text_input(
            "Link de Destino", value=link_prod, key=f"t_link_{row['id']}"
        )

        st.markdown("---")
        st.markdown("### 🎵 TikTok")
        st.text_input(
            "Título no Vídeo / Gancho (0-3s)",
            value=row["tik_titulo_video"] or "",
            key=f"tik_tit_{row['id']}",
        )
        st.text_area(
            "Legenda TikTok (com sacolinha amarela)",
            value=row["tik_legenda"] or "",
            height=80,
            key=f"tik_leg_{row['id']}",
        )

        st.markdown("---")
        st.markdown("### 📸 Instagram / Reels / Carrossel")
        st.text_input(
            "Título no Vídeo / Capa",
            value=row["insta_titulo_video"] or "",
            key=f"insta_tit_{row['id']}",
        )
        st.text_area(
            "Legenda Instagram (link na bio)",
            value=row["insta_legenda"] or "",
            height=80,
            key=f"insta_leg_{row['id']}",
        )

        st.markdown("---")
        st.markdown("### 📌 Pinterest (Focado em SEO de Busca)")
        st.text_input(
            "Título SEO para Busca (Palavras-chave)",
            value=row["pin_titulo"] or "",
            key=f"pin_tit_{row['id']}",
        )
        st.text_area(
            "Descrição SEO Pinterest (Até 800 caracteres)",
            value=row["pin_descricao"] or "",
            height=90,
            key=f"pin_desc_{row['id']}",
        )

        st.markdown("---")
        st.markdown("### 🛍️ Shopee Vídeos (Máx. 150 caracteres)")
        st.text_area(
            "Legenda Curta Shopee Vídeos",
            value=row["shp_legenda"] or "",
            height=70,
            key=f"shp_leg_{row['id']}",
        )

        st.markdown("---")
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
            st.success("Conteúdo concluído!")
            st.rerun()
        with col_btn2:
          if st.button("Excluir Item 🗑️", key=f"excluir_{row['id']}"):
            run_query(
                "DELETE FROM conteudos WHERE id = ?", (row["id"],), fetch=False
            )
            st.success("Item removido!")
            st.rerun()
  else:
    st.info("Nenhum conteúdo pendente na central no momento.")

# --- TELA 3: CATÁLOGO DE PRODUTOS ---
elif menu == "📦 Catálogo":
  st.markdown("### 📦 Gestão de Produtos & Afiliados")
  st.markdown(
      "Cole o texto bruto da Shopee. A IA limpa o título, extrai o link e"
      " sugere a categoria ideal!"
  )

  with st.form("form_importacao_produto"):
    texto_bruto = st.text_input(
        "Cole o Texto/Link Bruto da Shopee aqui:",
        placeholder="Ex: https://s.shopee.com.br/... Capa de Almofada...",
    )
    submit_import = st.form_submit_button(
        "Importar e Cadastrar Produto com IA 🚀"
    )

    if submit_import and texto_bruto:
      if not IA_DISPONIVEL:
        st.error("⚠️ Chave da API do Gemini não configurada nos 'Secrets'.")
      else:
        with st.spinner("A IA está processando o produto..."):
          prompt_extracao = f"""
                    Analise o texto bruto compartilhado de um produto de afiliado abaixo:
                    "{texto_bruto}"
                    
                    Sua tarefa é extrair três informações e responder estritamente usando estas tags:
                    [NOME] (Um título limpo, comercial e atraente para o produto)
                    [LINK] (Apenas a URL do link de afiliado encontrada no texto)
                    [CATEGORIA] (Defina uma categoria adequada e específica para este produto)
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
              f"🎉 Produto '{nome_extraido}' importado com sucesso!"
          )

  st.markdown("---")
  st.markdown("### 📋 Produtos Cadastrados (Gerenciamento)")
  df_prods = run_query(
      "SELECT id, nome, nicho, link_afiliado FROM produtos ORDER BY id DESC"
  )

  if not df_prods.empty:
    for _, row in df_prods.iterrows():
      col_p1, col_p2 = st.columns([4, 1])
      with col_p1:
        st.markdown(
            f"**📦 {row['nome']}**<br><small>Categoria: {row['nicho']}</small>",
            unsafe_allow_html=True,
        )
      with col_p2:
        if st.button("Excluir 🗑️", key=f"del_prod_{row['id']}"):
          run_query(
              "DELETE FROM conteudos WHERE produto_id = ?",
              (row["id"],),
              fetch=False,
          )
          run_query(
              "DELETE FROM produtos WHERE id = ?", (row["id"],), fetch=False
          )
          st.success("Produto excluído do catálogo!")
          st.rerun()
      st.markdown("---")
  else:
    st.info("Nenhum produto cadastrado.")

# --- TELA 4: DASHBOARD & METAS ---
elif menu == "📊 Dashboard & Metas":
  st.markdown("### 📊 Painel de Controle & Campanhas")

  df_concluidos = run_query(
      "SELECT * FROM conteudos WHERE status LIKE '%Concluído%'"
  )
  total_concluidos = len(df_concluidos)
  meta_videos = 15

  col1, col2, col3 = st.columns(3)
  with col1:
    st.markdown(
        f'<div class="metric-card"><h3>Vídeos Concluídos</h3><h2>'
        f" {total_concluidos} / {meta_videos}</h2></div>",
        unsafe_allow_html=True,
    )
  with col2:
    st.markdown(
        '<div class="metric-card"><h3>Campanha Ativa</h3><h2>#ViralTikTokShop</h2></div>',
        unsafe_allow_html=True,
    )
  with col3:
    progresso = (
        int((total_concluidos / meta_videos) * 100) if meta_videos > 0 else 0
    )
    st.markdown(
        f'<div class="metric-card"><h3>Progresso Geral</h3><h2>'
        f" {progresso}%</h2></div>",
        unsafe_allow_html=True,
    )

  st.markdown("---")
  st.markdown("### 🚀 Histórico de Concluídos")
  if not df_concluidos.empty:
    df_hist = run_query("""
            SELECT p.nome as produto, c.redes_alvo, c.status 
            FROM conteudos c 
            LEFT JOIN produtos p ON c.produto_id = p.id 
            WHERE c.status LIKE '%Concluído%'
            ORDER BY c.id DESC
        """)
    for _, row in df_hist.iterrows():
      st.markdown(
          f"""
            <div class="card">
                <b>📦 {row['produto']}</b> | Redes: {row['redes_alvo']}<br>
                <small>Status: <b>{row['status']} ✔️</b></small>
            </div>
            """,
          unsafe_allow_html=True,
      )
  else:
    st.info(
        "Nenhum conteúdo concluído ainda. Conclua os itens na Central de"
        " Pendentes para preencher seu dashboard!"
    )
