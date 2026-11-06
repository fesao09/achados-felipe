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
            tik_titulo_video TEXT,
            tik_legenda TEXT,
            insta_titulo_video TEXT,
            insta_legenda TEXT,
            pin_titulo TEXT,
            pin_descricao TEXT,
            shp_legenda TEXT,
            prompt_ia TEXT,
            status TEXT DEFAULT 'Pendente 🟡',
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
  api_key = st.secrets["GEMINI_API_KEY"]
  client = genai.Client(api_key=api_key)
  IA_DISPONIVEL = True
except Exception as e:
  IA_DISPONIVEL = False

# --- NAVEGAÇÃO SUPERIOR ---
st.title("🚀 Central Achados do Felipe")

menu = st.radio(
    "Navegação Rápida",
    [
        "🎬 Gerador de Roteiros",
        "📋 Central de Pendentes",
        "📦 Catálogo",
        "📊 Dashboard",
    ],
    horizontal=True,
)

st.markdown("---")

# --- TELA 1: GERADOR DE ROTEIROS (SIMPLES E DIRETO) ---
if menu == "🎬 Gerador de Roteiros":
  st.markdown("### 🎬 Gerador de Roteiro Inteligente")
  st.markdown("Selecione o produto e gere o pacote completo para cópia.")

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

    if st.button("Gerar Pacote com IA 🚀") and IA_DISPONIVEL:
      with st.spinner("Gerando roteiro..."):
        prompt_simples = f"""
                Atue como estrategista de marketing para 'Achados do Felipe'.
                Produto: {prod_escolhido}
                Link: {link_afiliado}
                
                Gere o conteúdo respondendo EXATAMENTE com estas tags e o texto na mesma linha ou logo abaixo:
                [ESTRATEGIA] Vídeo dinâmico ou carrossel curto
                [TIK_TITULO] Gancho de 0-3s para o TikTok
                [TIK_LEGENDA] Legenda TikTok com sacolinha amarela e {link_afiliado}
                [INSTA_TITULO] Título para Capa do Instagram
                [INSTA_LEGENDA] Legenda Instagram com link na bio e {link_afiliado}
                [PIN_TITULO] Título SEO para busca no Pinterest
                [PIN_DESCRICAO] Descrição SEO Pinterest rica com {link_afiliado}
                [SHP_LEGENDA] Legenda curta Shopee Videos (max 150 caracteres) com {link_afiliado}
                [PROMPT_IA] Professional product video of {prod_escolhido}, clean lighting
                """

        try:
          response = client.models.generate_content(
              model="gemini-2.5-flash", contents=prompt_simples
          )
          texto = response.text

          # Padrões iniciais seguros
          estrategia = "Vídeo Dinâmico"
          tik_tit = f"Olha esse achado: {prod_escolhido}"
          tik_leg = f"Achado incrível! Garanta na sacolinha amarela. {link_afiliado}"
          insta_tit = f"{prod_escolhido} imperdível!"
          insta_leg = f"Olha que item incrível! Link na bio. {link_afiliado}"
          pin_tit = f"{prod_escolhido} Dicas e Achados"
          pin_desc = f"Descubra todos os detalhes sobre {prod_escolhido}. Confira o link!"
          shp_leg = f"Confira na vitrine! {link_afiliado}"
          prompt_ia = f"Professional product showcase of {prod_escolhido}"

          # Leitura linha por linha super rápida e sem travar
          for linha in texto.split("\n"):
            if "[" in linha and "]" in linha:
              tag = linha.split("]")[0].replace("[", "").strip()
              conteudo = linha.split("]")[1].strip()
              if conteudo:
                if "ESTRATEGIA" in tag:
                  estrategia = conteudo
                elif "TIK_TITULO" in tag:
                  tik_tit = conteudo
                elif "TIK_LEGENDA" in tag:
                  tik_leg = conteudo
                elif "INSTA_TITULO" in tag:
                  insta_tit = conteudo
                elif "INSTA_LEGENDA" in tag:
                  insta_leg = conteudo
                elif "PIN_TITULO" in tag:
                  pin_tit = conteudo
                elif "PIN_DESCRICAO" in tag:
                  pin_desc = conteudo
                elif "SHP_LEGENDA" in tag:
                  shp_leg = conteudo
                elif "PROMPT_IA" in tag:
                  prompt_ia = conteudo

          run_query(
              """
                    INSERT INTO conteudos (
                        produto_id, redes_alvo, estrategia_ia, 
                        tik_titulo_video, tik_legenda, 
                        insta_titulo_video, insta_legenda, 
                        pin_titulo, pin_descricao, 
                        shp_legenda, prompt_ia, status
                    )
                    VALUES (?, 'Todas', ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendente 🟡')
                """,
              (
                  prod_id,
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

          st.success("🎉 Roteiro gerado com sucesso!")
          st.rerun()

        except Exception as e:
          st.error(f"Erro ao gerar: {e}")
  else:
    st.info("Todos os produtos cadastrados já tiveram seus roteiros gerados!")

# --- TELA 2: CENTRAL DE PENDENTES (FÁCIL CÓPIA) ---
elif menu == "📋 Central de Pendentes":
  st.markdown("### 📋 Central de Pendentes")
  st.markdown("Copie os campos abaixo para cada rede social.")

  df_kanban = run_query("""
        SELECT c.id, p.nome as produto, p.link_afiliado, c.estrategia_ia, c.status, 
               c.tik_titulo_video, c.tik_legenda, c.insta_titulo_video, c.insta_legenda, 
               c.pin_titulo, c.pin_descricao, c.shp_legenda, c.prompt_ia 
        FROM conteudos c 
        LEFT JOIN produtos p ON c.produto_id = p.id 
        WHERE p.nome IS NOT NULL
        ORDER BY c.id DESC
    """)

  if not df_kanban.empty:
    for _, row in df_kanban.iterrows():
      status_ico = (
          "✔️ Concluído" if "Concluído" in str(row["status"]) else "🟡 Pendente"
      )
      nome_p = row["produto"] if pd.notna(row["produto"]) else "Produto"

      with st.expander(f"[{status_ico}] {nome_p}"):
        st.markdown(f"🤖 **Formato:** {row['estrategia_ia']}")
        st.markdown("---")

        st.markdown("### 🎵 TikTok")
        st.text_input(
            "Gancho (0-3s)",
            value=row["tik_titulo_video"] or "",
            key=f"tik_t_{row['id']}",
        )
        st.text_area(
            "Legenda (com sacolinha amarela)",
            value=row["tik_legenda"] or "",
            height=70,
            key=f"tik_l_{row['id']}",
        )

        st.markdown("---")
        st.markdown("### 📸 Instagram")
        st.text_input(
            "Título Capa",
            value=row["insta_titulo_video"] or "",
            key=f"ins_t_{row['id']}",
        )
        st.text_area(
            "Legenda (link na bio)",
            value=row["insta_legenda"] or "",
            height=70,
            key=f"ins_l_{row['id']}",
        )

        st.markdown("---")
        st.markdown("### 📌 Pinterest")
        st.text_input(
            "Título SEO",
            value=row["pin_titulo"] or "",
            key=f"pin_t_{row['id']}",
        )
        st.text_area(
            "Descrição SEO",
            value=row["pin_descricao"] or "",
            height=80,
            key=f"pin_d_{row['id']}",
        )

        st.markdown("---")
        st.markdown("### 🛍️ Shopee Vídeo (Máx 150 caracteres)")
        st.text_area(
            "Legenda Curta",
            value=row["shp_legenda"] or "",
            height=60,
            key=f"shp_l_{row['id']}",
        )

        st.markdown("---")
        st.markdown("### 🤖 Prompt de Mídia (IA)")
        st.text_area(
            "Prompt em Inglês",
            value=row["prompt_ia"] or "",
            height=70,
            key=f"prm_{row['id']}",
        )

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
          if st.button("Marcar Concluído ✔️", key=f"ok_{row['id']}"):
            run_query(
                "UPDATE conteudos SET status = 'Concluído ✔️' WHERE id = ?",
                (row["id"],),
                fetch=False,
            )
            st.rerun()
        with c2:
          if st.button("Excluir 🗑️", key=f"del_{row['id']}"):
            run_query(
                "DELETE FROM conteudos WHERE id = ?", (row["id"],), fetch=False
            )
            st.rerun()
  else:
    st.info("Nenhum conteúdo pendente.")

# --- TELA 3: CATÁLOGO DE PRODUTOS ---
elif menu == "📦 Catálogo":
  st.markdown("### 📦 Catálogo de Produtos")

  with st.form("form_cat"):
    texto_bruto = st.text_input(
        "Cole o texto ou link da Shopee:", placeholder="https://s.shopee..."
    )
    enviar = st.form_submit_button("Cadastrar Produto 🚀")

    if enviar and texto_bruto:
      with st.spinner("Cadastrando..."):
        try:
          prompt_cat = f"""
                    Analise: "{texto_bruto}"
                    Responda em formato exato:
                    [NOME] Nome limpo do produto
                    [LINK] Apenas a URL http
                    """
          res = client.models.generate_content(
              model="gemini-2.5-flash", contents=prompt_cat
          )
          nome, link = "Achado Shopee", texto_bruto

          for l in res.text.split("\n"):
            if "[NOME]" in l:
              nome = l.replace("[NOME]", "").strip()
            elif "[LINK]" in l:
              link = l.replace("[LINK]", "").strip()

          if not link.startswith("http"):
            for w in texto_bruto.split():
              if w.startswith("http"):
                link = w
                break

          run_query(
              "INSERT INTO produtos (nome, nicho, link_afiliado) VALUES (?, 'Geral', ?)",
              (nome, link),
              fetch=False,
          )
          st.success(f"Produto '{nome}' cadastrado!")
          st.rerun()
        except Exception:
          run_query(
              "INSERT INTO produtos (nome, nicho, link_afiliado) VALUES ('Achado Shopee', 'Geral', ?)",
              (texto_bruto,),
              fetch=False,
          )
          st.success("Produto cadastrado!")
          st.rerun()

  st.markdown("---")
  df_p = run_query("SELECT id, nome, link_afiliado FROM produtos ORDER BY id DESC")
  if not df_p.empty:
    for _, row in df_p.iterrows():
      c1, c2 = st.columns([4, 1])
      with c1:
        st.markdown(f"**{row['nome']}**")
      with c2:
        if st.button("Excluir 🗑️", key=f"dp_{row['id']}"):
          run_query(
              "DELETE FROM conteudos WHERE produto_id = ?",
              (row['id'],),
              fetch=False,
          )
          run_query(
              "DELETE FROM produtos WHERE id = ?", (row['id'],), fetch=False
          )
          st.rerun()
      st.markdown("---")
  else:
    st.info("Nenhum produto no catálogo.")

# --- TELA 4: DASHBOARD ---
elif menu == "📊 Dashboard":
  st.markdown("### 📊 Dashboard & Metas")
  total = len(
      run_query("SELECT * FROM conteudos WHERE status LIKE '%Concluído%'")
  )
  st.metric(label="Vídeos Concluídos", value=f"{total} / 15")
