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

# --- CONFIGURAÇÃO DA IA (GEMINI API) Opcional ---
IA_DISPONIVEL = False
try:
  from google import genai
  api_key = st.secrets["GEMINI_API_KEY"]
  client = genai.Client(api_key=api_key)
  IA_DISPONIVEL = True
except Exception:
  pass

# --- 🧠 MOTOR 1: EXTRATOR OFFLINE (LIMPEZA DE TEXTO DO WHATSAPP) ---
def limpar_texto_shopee(texto_bruto):
    link_puro = texto_bruto
    nome_puro = texto_bruto

    # Isola o link e remove parâmetros de rastreamento de afiliados sujos (?share_channel...)
    palavras = texto_bruto.split()
    for p in palavras:
        if p.startswith("http"):
            link_puro = p.split("?")[0] if "?" in p else p
            break
            
    # Limpeza bruta do texto padrão da Shopee
    if "Dê uma olhada em " in nome_puro:
        nome_puro = nome_puro.split("Dê uma olhada em ")[1]
    if " por R$" in nome_puro:
        nome_puro = nome_puro.split(" por R$")[0]
    if "Compre na Shopee agora!" in nome_puro:
        nome_puro = nome_puro.replace("Compre na Shopee agora!", "")
    
    nome_puro = nome_puro.replace(link_puro, "").strip()
    
    # Prevenção extra
    if not nome_puro or len(nome_puro) < 3:
        nome_puro = "Achado Imperdível Shopee"
        
    return nome_puro, link_puro

# --- 🧠 MOTOR 2: A MEGA ENCICLOPÉDIA DE NICHOS ---
ENCICLOPEDIA = {
    "Casa & Decoração": {
        "ganchos_tik": ["Sua casa precisa desse achado da Shopee:", "O segredo para uma casa organizada:", "Comprei o item mais viral da Shopee:"],
        "titulos_insta": ["Decoração Inteligente ✨", "Achadinho para o seu Lar 🏡", "Você precisa ver isso!"],
        "tags": "#donadecasa #dicaspracasa #decoracao #achadinhosshopee #shopeebrasil #casaorganizada"
    },
    "Eletrônicos": {
        "ganchos_tik": ["Tecnologia que facilita a vida:", "Seu setup precisa disso urgentemente:", "O melhor custo-benefício da Shopee:"],
        "titulos_insta": ["Tech Dica do Dia 💻", "Eletrônico Indispensável ⚡", "O Mais Desejado da Shopee"],
        "tags": "#tecnologia #eletronicos #setupgamer #dicastech #achadosshopee #shopeebr"
    },
    "Beleza & Cuidado": {
        "ganchos_tik": ["O segredo de beleza que ninguém te conta:", "Testando o viral de beleza da Shopee:", "Seu autocuidado elevado de nível:"],
        "titulos_insta": ["Dica de Ouro de Beleza ✨", "Skin Care & Cuidado 💄", "O Favorito do Momento"],
        "tags": "#dicasdebeleza #autocuidado #maquiagem #skincarebrasil #achadosshopee"
    },
    "Moda": {
        "ganchos_tik": ["Look de milhões gastando pouco:", "A peça chave que faltava no seu guarda-roupa:", "Provando roupas da Shopee:"],
        "titulos_insta": ["Look Inspiração 👗", "Moda Acessível ✨", "Estilo com Economia"],
        "tags": "#lookdodia #modafeminina #estilo #roupasshopee #achadinhos"
    },
    "Infantil": {
        "ganchos_tik": ["Mães, vocês precisam ver esse achado:", "Diversão e praticidade para as crianças:", "O melhor presente infantil da Shopee:"],
        "titulos_insta": ["Dica de Mãe 👶", "Para os Pequenos 🧸", "Achado Infantil Incrível"],
        "tags": "#maternidadereal #dicasdemae #brinquedos #achadosinfantis #shopeebr"
    },
    "Geral": {
        "ganchos_tik": ["Você não vai acreditar nesse achado:", "Por que ninguém me avisou disso antes?", "Comprei o item mais útil da Shopee:"],
        "titulos_insta": ["Achado Imperdível 🚀", "Você precisa ter isso ✨", "O Melhor Custo-Benefício"],
        "tags": "#achados #achadinhos #shopeebrasil #comprasshopee #dicas"
    }
}

def gerar_textos_enciclopedia(nome, link, categoria):
    # Se a categoria não estiver no dicionário, usa a Geral
    cat_data = ENCICLOPEDIA.get(categoria, ENCICLOPEDIA["Geral"])
    
    tags = cat_data["tags"]
    
    tik_tit = random.choice(cat_data["ganchos_tik"])
    tik_leg = f"😱 Olha que achado incrível! Já garante o seu na sacolinha amarela 👇\n{link}\n\n{tags}"
    
    insta_tit = f"{random.choice(cat_data['titulos_insta'])} - {nome[:30]}"
    insta_leg = f"✨ Descubra como o {nome} pode mudar o seu dia!\n\n🔗 Link na bio para garantir o seu com desconto.\n\n{tags}"
    
    pin_tit = f"{nome[:60]} - Melhor Opção e Dicas"
    pin_desc = f"Descubra todos os detalhes sobre {nome}. A opção ideal de {categoria} para quem busca praticidade. Confira o link e aproveite a oferta: {link}\n{tags}"
    
    # Shopee Vídeo exige máximo de 150 caracteres. O nome não pode ser gigante.
    nome_curto = nome[:30] + "..." if len(nome) > 30 else nome
    shp_leg = f"Achado imperdível! {nome_curto} Confira na vitrine 👇\n{link} #achados"
    if len(shp_leg) > 150:
        shp_leg = f"Achado imperdível! Vitrine 👇\n{link} #achados"
        
    prompt_ia = f"Professional product showcase video of {nome}, clean lighting, aesthetic lifestyle background, 4k"
    
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
  st.markdown("### 🎬 Gerador Estratégico (Modo Enciclopédia)")

  df_produtos = run_query("SELECT id, nome, nicho, link_afiliado FROM produtos WHERE id NOT IN (SELECT produto_id FROM conteudos WHERE produto_id IS NOT NULL)")

  if not df_produtos.empty:
    with st.form("form_gerador"):
      prod_escolhido = st.selectbox("Selecione o Produto", df_produtos["nome"].tolist())
      
      usar_ia = st.checkbox("🤖 Reescrever usando IA Gemini (Ignorar Enciclopédia local)", value=False)
      
      btn_gerar = st.form_submit_button("Gerar Pacote Estratégico 🚀")

      if btn_gerar:
        prod_row = df_produtos.loc[df_produtos["nome"] == prod_escolhido].iloc[0]
        prod_id = int(prod_row["id"])
        link_af = str(prod_row["link_afiliado"])
        nicho = str(prod_row["nicho"])

        # Roda o motor da enciclopédia instantaneamente
        estrategia, tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia = gerar_textos_enciclopedia(prod_escolhido, link_af, nicho)

        # Se o usuário marcou a caixinha e a IA está ligada, sobrescreve.
        if usar_ia and IA_DISPONIVEL:
          with st.spinner("Chamando a IA..."):
            try:
              prompt = f"Gere textos para afiliado. Produto: '{prod_escolhido}'. Link: {link_af}. Categoria: {nicho}. Use as melhores hashtags.\nResponda EXATAMENTE neste formato:\nTIK_TITULO: Gancho\nTIK_LEGENDA: Legenda com sacolinha, link e hashtags\nINSTA_TITULO: Titulo\nINSTA_LEGENDA: Legenda com link na bio e hashtags\nPIN_TITULO: Titulo SEO\nPIN_DESCRICAO: Descricao rica\nSHP_LEGENDA: Legenda super curta com link\nPROMPT_IA: Prompt em inglês"
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
                  elif "PROMPT_IA" in ch: prompt_ia = val
              st.toast("Textos aprimorados pela IA!")
            except Exception:
              st.toast("Falha na IA. Usando a Enciclopédia de alta conversão offline.")

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
        st.text_area("TikTok Legenda", value=row["tik_legenda"] or "", height=90, key=f"tl_{row['id']}")
        st.text_input("Insta Capa", value=row["insta_titulo_video"] or "", key=f"it_{row['id']}")
        st.text_area("Insta Legenda", value=row["insta_legenda"] or "", height=90, key=f"il_{row['id']}")
        st.text_input("Pinterest Título", value=row["pin_titulo"] or "", key=f"pt_{row['id']}")
        st.text_area("Pinterest Descrição", value=row["pin_descricao"] or "", height=90, key=f"pd_{row['id']}")
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

# --- TELA 3: CATÁLOGO INTELIGENTE E OFFLINE ---
elif menu == "📦 Catálogo":
  st.markdown("### 📦 Catálogo de Produtos")
  st.markdown("O sistema limpa nomes gigantes, corta preços e rastreadores sozinho.")

  with st.form("form_cat_manual"):
    texto_zap = st.text_area("Cole a mensagem do WhatsApp ou Link Shopee:", placeholder="Dê uma olhada em Caixa de som por R$100. Compre aqui: https://...")
    nicho_prod = st.selectbox("Categoria (Importante para a Enciclopédia):", ["Casa & Decoração", "Eletrônicos", "Beleza & Cuidado", "Moda", "Infantil", "Geral"])
    
    enviar = st.form_submit_button("Processar e Salvar Produto 🚀")

    if enviar and texto_zap:
      # Aciona o motor 1 para limpar a sujeira do texto
      nome_limpo, link_limpo = limpar_texto_shopee(texto_zap)
      
      run_query("INSERT INTO produtos (nome, nicho, link_afiliado) VALUES (?, ?, ?)", (nome_limpo, nicho_prod, link_limpo), fetch=False)
      st.success(f"Produto isolado e cadastrado: {nome_limpo}")
      st.rerun()
    elif enviar:
      st.warning("Cole o texto para salvar.")

  st.markdown("---")
  df_p = run_query("SELECT id, nome FROM produtos ORDER BY id DESC")
  if not df_p.empty:
    for _, row in df_p.iterrows():
      c1, c2 = st.columns([4, 1])
      with c1: st.markdown(f"**📦 {row['nome']}**")
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
