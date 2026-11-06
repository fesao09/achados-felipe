import sqlite3
import pandas as pd
import streamlit as st
import random

# Configuração da Página
st.set_page_config(
    page_title="Central Achados do Felipe",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# Estilização CSS
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
IA_DISPONIVEL = False
try:
  from google import genai
  api_key = st.secrets["GEMINI_API_KEY"]
  client = genai.Client(api_key=api_key)
  IA_DISPONIVEL = True
except Exception:
  pass

# --- MOTOR DE INTELIGÊNCIA "SEM IA" (TEMPLATES FORTES) ---
def gerar_textos_offline(nome, link, categoria):
  # Variações automáticas para não ficar tudo igual
  ganchos_tik = [
      f"{nome} vale a pena?",
      f"Testei o famoso {nome}!",
      f"Achado da Shopee que você precisa ver:",
      f"Por que ninguém me falou disso antes?"
  ]
  
  titulos_insta = [
      f"{nome} - Você precisa disso!",
      f"O melhor achado de {categoria} ✨",
      f"Já conhecia o {nome}?",
      f"Dica de ouro pra você 💡"
  ]

  tik_tit = random.choice(ganchos_tik)
  tik_leg = f"😱 Olha que achado incrível! Já garante o seu na sacolinha amarela 👇\n{link} #achados #shopee #dicas"
  
  insta_tit = random.choice(titulos_insta)
  insta_leg = f"✨ Item imperdível para o seu dia a dia!\n🔗 Link na bio para garantir o seu.\n{link} #achados #reels"
  
  pin_tit = f"{nome} - Melhor Oferta e Dicas"
  pin_desc = f"Descubra todos os detalhes sobre {nome}. A melhor opção de {categoria} para quem busca praticidade e qualidade. Confira o link e aproveite: {link}"
  
  shp_leg = f"Achado imperdível! Confira na vitrine. {link}"
  prompt_ia = f"Professional product showcase video of {nome}, clean lighting, high resolution, 4k"
  
  return "Vídeo Dinâmico (Review / Unboxing)", tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia

# --- NAVEGAÇÃO SUPERIOR ---
st.title("🚀 Central Achados do Felipe")

menu = st.radio(
    "Navegação",
    ["🎬 Gerador de Roteiros", "📋 Central de Pendentes", "📦 Catálogo", "📊 Dashboard"],
    horizontal=True,
)
st.markdown("---")

# --- TELA 1: GERADOR DE ROTEIROS ---
if menu == "🎬 Gerador de Roteiros":
  st.markdown("### 🎬 Gerador Estratégico (Modo Instantâneo)")

  df_produtos = run_query("SELECT id, nome, nicho, link_afiliado FROM produtos WHERE id NOT IN (SELECT produto_id FROM conteudos WHERE produto_id IS NOT NULL)")

  if not df_produtos.empty:
    with st.form("form_gerador"):
      prod_escolhido = st.selectbox("Selecione o Produto", df_produtos["nome"].tolist())
      
      # Opcional para tentar usar a IA se quiser
      usar_ia = st.checkbox("🤖 Tentar reescrever textos com Inteligência Artificial (Pode falhar se o limite exceder)", value=False)
      
      btn_gerar = st.form_submit_button("Gerar Pacote 🚀")

      if btn_gerar:
        prod_row = df_produtos.loc[df_produtos["nome"] == prod_escolhido].iloc[0]
        prod_id = int(prod_row["id"])
        link_af = str(prod_row["link_afiliado"]) if pd.notna(prod_row["link_afiliado"]) else "Link aqui"
        nicho = str(prod_row["nicho"])

        estrategia, tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia = gerar_textos_offline(prod_escolhido, link_af, nicho)

        if usar_ia and IA_DISPONIVEL:
          with st.spinner("Conectando com a IA..."):
            try:
              prompt = f"Gere textos para afiliado do produto '{prod_escolhido}' (Link: {link_af}). Responda EXATAMENTE neste formato:\nTIK_TITULO: Gancho\nTIK_LEGENDA: Legenda com sacolinha e link\nINSTA_TITULO: Titulo\nINSTA_LEGENDA: Legenda com link na bio\nPIN_TITULO: Titulo SEO\nPIN_DESCRICAO: Descricao SEO\nSHP_LEGENDA: Legenda curta"
              res = client.models.generate_content(model="gemini-1.5-flash", contents=prompt).text
              
              for l in res.split("\n"):
                if ":" in l:
                  ch, val = l.split(":", 1)
                  ch = ch.strip().upper()
                  val = val.strip()
                  if "TIK_TITULO" in ch: tik_tit = val
                  elif "TIK_LEGENDA" in ch: tik_leg = val
                  elif "INSTA_TITULO" in ch: insta_tit = val
                  elif "INSTA_LEGENDA" in ch: insta_leg = val
                  elif "PIN_TITULO" in ch: pin_tit = val
                  elif "PIN_DESCRICAO" in ch: pin_desc = val
                  elif "SHP_LEGENDA" in ch: shp_leg = val
              st.toast("Textos aprimorados pela IA!")
            except Exception:
              st.toast("A IA falhou. Usando textos de alta conversão salvos no sistema (Modo Offline).")

        run_query(
            "INSERT INTO conteudos (produto_id, estrategia_ia, tik_titulo_video, tik_legenda, insta_titulo_video, insta_legenda, pin_titulo, pin_descricao, shp_legenda, prompt_ia, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendente 🟡')",
            (prod_id, estrategia, tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia),
            fetch=False
        )
        st.success("🎉 Roteiro gerado e salvo instantaneamente na Central de Pendentes!")
        st.rerun()
  else:
    st.info("Todos os produtos cadastrados já tiveram seus roteiros gerados!")

# --- TELA 2: CENTRAL DE PENDENTES ---
elif menu == "📋 Central de Pendentes":
  st.markdown("### 📋 Central de Pendentes")

  df_kanban = run_query("SELECT c.id, p.nome as produto, c.estrategia_ia, c.status, c.tik_titulo_video, c.tik_legenda, c.insta_titulo_video, c.insta_legenda, c.pin_titulo, c.pin_descricao, c.shp_legenda, c.prompt_ia FROM conteudos c LEFT JOIN produtos p ON c.produto_id = p.id WHERE p.nome IS NOT NULL ORDER BY c.id DESC")

  if not df_kanban.empty:
    for _, row in df_kanban.iterrows():
      status_ico = "✔️ Concluído" if "Concluído" in str(row["status"]) else "🟡 Pendente"
      nome_p = row["produto"] if pd.notna(row["produto"]) else "Produto"

      with st.expander(f"[{status_ico}] {nome_p}"):
        st.markdown(f"🤖 **Formato:** {row['estrategia_ia']}")
        
        st.text_input("TikTok Gancho", value=row["tik_titulo_video"] or "", key=f"tt_{row['id']}")
        st.text_area("TikTok Legenda", value=row["tik_legenda"] or "", height=70, key=f"tl_{row['id']}")
        st.text_input("Insta Capa", value=row["insta_titulo_video"] or "", key=f"it_{row['id']}")
        st.text_area("Insta Legenda", value=row["insta_legenda"] or "", height=70, key=f"il_{row['id']}")
        st.text_input("Pinterest Título", value=row["pin_titulo"] or "", key=f"pt_{row['id']}")
        st.text_area("Pinterest Descrição", value=row["pin_descricao"] or "", height=70, key=f"pd_{row['id']}")
        st.text_area("Shopee Legenda", value=row["shp_legenda"] or "", height=60, key=f"sl_{row['id']}")
        
        c1, c2 = st.columns(2)
        with c1:
          if st.button("Marcar Concluído ✔️", key=f"ok_{row['id']}"):
            run_query("UPDATE conteudos SET status = 'Concluído ✔️' WHERE id = ?", (row["id"],), fetch=False)
            st.rerun()
        with c2:
          if st.button("Excluir 🗑️", key=f"del_{row['id']}"):
            run_query("DELETE FROM conteudos WHERE id = ?", (row["id"],), fetch=False)
            st.rerun()
  else:
    st.info("Nenhum conteúdo pendente.")

# --- TELA 3: CATÁLOGO MANUAL 100% GARANTIDO ---
elif menu == "📦 Catálogo":
  st.markdown("### 📦 Catálogo de Produtos")
  st.markdown("Cadastre seus produtos rapidamente. **Sem IA, sem falhas.**")

  with st.form("form_cat_manual"):
    nome_prod = st.text_input("Nome do Produto:", placeholder="Ex: Caixa de Som JBL Boombox 4")
    link_prod = st.text_input("Link de Afiliado:", placeholder="https://s.shopee...")
    nicho_prod = st.selectbox("Categoria:", ["Geral", "Casa", "Eletrônicos", "Moda", "Beleza", "Infantil"])
    
    enviar = st.form_submit_button("Salvar Produto 🚀")

    if enviar and nome_prod and link_prod:
      run_query("INSERT INTO produtos (nome, nicho, link_afiliado) VALUES (?, ?, ?)", (nome_prod, nicho_prod, link_prod), fetch=False)
      st.success(f"Produto '{nome_prod}' cadastrado na hora!")
      st.rerun()
    elif enviar:
      st.warning("Preencha o nome e o link para salvar.")

  st.markdown("---")
  df_p = run_query("SELECT id, nome FROM produtos ORDER BY id DESC")
  if not df_p.empty:
    for _, row in df_p.iterrows():
      c1, c2 = st.columns([4, 1])
      with c1: st.markdown(f"**{row['nome']}**")
      with c2:
        if st.button("Excluir 🗑️", key=f"dp_{row['id']}"):
          run_query("DELETE FROM conteudos WHERE produto_id = ?", (row['id'],), fetch=False)
          run_query("DELETE FROM produtos WHERE id = ?", (row['id'],), fetch=False)
          st.rerun()
      st.markdown("---")

# --- TELA 4: DASHBOARD ---
elif menu == "📊 Dashboard":
  st.markdown("### 📊 Dashboard & Metas")
  total = len(run_query("SELECT * FROM conteudos WHERE status LIKE '%Concluído%'"))
  st.metric(label="Vídeos Concluídos", value=f"{total} / 15")
