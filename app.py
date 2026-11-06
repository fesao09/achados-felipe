import os
import json
import sqlite3
import pandas as pd
import streamlit as st
import random

# --- CONFIGURAÇÃO DA PÁGINA E CSS ---
st.set_page_config(
    page_title="Achados do Felipe",
    page_icon="🔎", 
    layout="wide",
    initial_sidebar_state="collapsed",
)

st.markdown(
    """
    <style>
    .main { background-color: #121212; color: #ffffff; }
    h1, h2, h3 { color: #FF4500 !important; }
    
    .stButton>button { 
        background: linear-gradient(90deg, #FF7F50 0%, #FF4500 100%) !important; 
        color: white !important; 
        border: none !important; 
        border-radius: 8px !important; 
        font-weight: bold; 
    }
    .stButton>button:hover { opacity: 0.8 !important; }
    
    .card { 
        background-color: #282828; 
        padding: 15px; 
        border-radius: 12px; 
        margin-bottom: 12px; 
        box-shadow: 0 4px 6px rgba(0,0,0,0.3); 
        border-left: 5px solid #FF4500; 
    }
    
    .metric-card { 
        background-color: #282828; 
        padding: 15px; 
        border-radius: 10px; 
        text-align: center; 
        border-bottom: 4px solid #FF4500; 
    }
    
    [data-testid="collapsedControl"] { display: none; }
    </style>
""",
    unsafe_allow_html=True,
)

# --- CABEÇALHO PRINCIPAL ---
try:
    st.image("banner.jpg", use_container_width=True)
except:
    try:
        st.image("banner.png", use_container_width=True)
    except:
        st.title("Central Achados do Felipe")
        st.markdown("<p style='color: #FF7F50; margin-top: -15px;'>As Melhores Ofertas</p>", unsafe_allow_html=True)

st.markdown("---")

menu = st.radio(
    "Navegação Rápida",
    ["🎬 Gerar", "📋 Pendentes", "📦 Catálogo", "🧠 Treinamento", "📊 Dashboard"],
    horizontal=True,
)
st.markdown("---")

# --- SISTEMA DE ARQUIVOS: MEGA CÉREBRO V2 (COPYWRITING AVANÇADO OFFLINE) ---
CEREBRO_FILE = "cerebro_v2.json"

DEFAULT_CEREBRO = {
    "Casa & Decoração": {
        "tags": "#donadecasa #dicaspracasa #decoracao #achadinhosshopee #shopeebrasil #casaorganizada #cozinha",
        "ganchos_tik": [
            "Seu apartamento precisa de {nome} urgente:",
            "Como deixar sua casa com cara de rica gastando pouco:",
            "Testei o {nome} que viralizou no app vizinho!",
            "Pare de sofrer em casa e veja esse achado:"
        ],
        "legenda_tik": [
            "😱 Transformação total! Já garante o seu na sacolinha amarela antes que esgote 👇\n{link}\n\n{tags}",
            "✨ O segredo da casa Pinterest revelado! Link na sacolinha 👇\n{link}\n\n{tags}",
            "Praticidade que fala, né? Corre na sacolinha pra aproveitar o preço 👇\n{link}\n\n{tags}"
        ],
        "titulos_insta": [
            "O Segredo da Casa Perfeita 🏡",
            "Transforme seu Lar com {nome} ✨",
            "Fim da bagunça! Você precisa disso"
        ],
        "legenda_insta": [
            "✨ Por que ninguém me avisou disso antes?\n\nO {nome} é aquele tipo de achado que muda a rotina e deixa tudo mais prático. Se você também ama uma casa organizada e moderna, esse item é obrigatório!\n\n🔗 Comente 'EU QUERO' ou clique no link da BIO para garantir com desconto.\n\n{tags}",
            "🏡 Chega de passar vontade!\n\nEncontrei o {nome} com um preço surreal. Perfeito para dar aquele 'glow up' na sua casa sem gastar uma fortuna.\n\n🔗 Link na BIO!\n\n{tags}"
        ]
    },
    "Eletrônicos": {
        "tags": "#tecnologia #eletronicos #setupgamer #dicastech #achadosshopee #shopeebr #gadgets",
        "ganchos_tik": [
            "A Apple não quer que você saiba desse achado:",
            "O segredo para um setup perfeito gastando pouco:",
            "Não compre {nome} antes de ver esse vídeo:",
            "Tecnologia barata que parece premium:"
        ],
        "legenda_tik": [
            "⚡ Qualidade surreal pelo preço! Corre na sacolinha amarela 👇\n{link}\n\n{tags}",
            "Setup atualizado com sucesso 🚀 Link na sacolinha 👇\n{link}\n\n{tags}",
            "Esse entrega muito mais do que promete! Garanta o seu na sacolinha 👇\n{link}\n\n{tags}"
        ],
        "titulos_insta": [
            "Tech Barata e Premium 💻",
            "Upgrade Obrigatório: {nome} ⚡",
            "Custo-Benefício Imbatível"
        ],
        "legenda_insta": [
            "⚡ Procura qualidade sem pagar o preço de grife?\n\nO {nome} entrega tudo! Bateria duradoura, design premium e um custo-benefício que só achando na Shopee pra acreditar.\n\n🔗 Corre no link da BIO antes que o estoque acabe!\n\n{tags}",
            "🚀 Eleva o nível do seu dia a dia!\n\nChegou a hora de ter o seu {nome}. Tecnologia de ponta, super funcional e por um preço que cabe no bolso.\n\n🔗 Link direto na BIO.\n\n{tags}"
        ]
    },
    "Beleza & Cuidado": {
        "tags": "#dicasdebeleza #autocuidado #skincarebrasil #achadosshopee #beleza #maquiagem",
        "ganchos_tik": [
            "O segredo do glow up perfeito gastando R$30:",
            "Testando o {nome} que as gringas amam:",
            "Seu skincare nunca mais será o mesmo:",
            "Produto de farmácia vs Achado da Shopee:"
        ],
        "legenda_tik": [
            "✨ Resultado de salão em casa! Link na sacolinha amarela 👇\n{link}\n\n{tags}",
            "Autoestima lá no teto! Garanta o seu na sacolinha 👇\n{link}\n\n{tags}"
        ],
        "titulos_insta": [
            "Glow Up Automático ✨",
            "Seu Novo Favorito: {nome} 💄",
            "Rotina de Milhões (Gasta Pouco)"
        ],
        "legenda_insta": [
            "✨ O segredo da pele de milhões revelado!\n\nSe você quer praticidade na rotina de beleza, o {nome} é o seu novo melhor amigo. Textura incrível e resultados reais.\n\n🔗 Link na BIO para brilhar!\n\n{tags}"
        ]
    },
    "Geral": {
        "tags": "#achados #achadinhos #shopeebrasil #comprasshopee #dicas #comprinhas",
        "ganchos_tik": [
            "Pare de rolar o feed e veja esse achado:",
            "Comprei o item mais útil e bizarro da Shopee:",
            "Como eu vivi tanto tempo sem o {nome}?",
            "Achado da Shopee que resolve a sua vida:"
        ],
        "legenda_tik": [
            "🚀 Praticidade em nível máximo! Link na sacolinha amarela 👇\n{link}\n\n{tags}",
            "Genial! E o preço tá surreal na sacolinha 👇\n{link}\n\n{tags}",
            "Achadinho de ouro! Clica na sacolinha e confira 👇\n{link}\n\n{tags}"
        ],
        "titulos_insta": [
            "Achado de Ouro 🏆",
            "Você Precisa Desse {nome} 🚀",
            "O Melhor Investimento do Mês"
        ],
        "legenda_insta": [
            "🚀 Sabe aquele produto que você não sabia que precisava até ver?\n\nO {nome} é exatamente assim! Ele resolve problemas do dia a dia de um jeito tão simples que impressiona.\n\n🔗 O link tá te esperando na BIO.\n\n{tags}",
            "🏆 Campeão de vendas por um motivo!\n\nO {nome} virou febre e não é à toa. Qualidade, preço baixo e super útil. Você não vai se arrepender.\n\n🔗 Clica no link da BIO e aproveita!\n\n{tags}"
        ]
    }
}

def carregar_cerebro():
    if not os.path.exists(CEREBRO_FILE):
        with open(CEREBRO_FILE, "w", encoding="utf-8") as f:
            json.dump(DEFAULT_CEREBRO, f, indent=4, ensure_ascii=False)
    
    with open(CEREBRO_FILE, "r", encoding="utf-8") as f:
        return json.load(f)

def salvar_cerebro(dados):
    with open(CEREBRO_FILE, "w", encoding="utf-8") as f:
        json.dump(dados, f, indent=4, ensure_ascii=False)

# --- BANCO DE DADOS LOCAL (SQLITE) ---
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

# --- CONFIGURAÇÃO DA IA Opcional ---
IA_DISPONIVEL = False
try:
  from google import genai
  api_key = st.secrets["GEMINI_API_KEY"]
  client = genai.Client(api_key=api_key)
  IA_DISPONIVEL = True
except Exception:
  pass


# --- MOTORES OFFLINE DE LIMPEZA E TEXTO ---
def limpar_texto_shopee(texto_bruto):
    link_puro = texto_bruto
    nome_puro = texto_bruto

    palavras = texto_bruto.split()
    for p in palavras:
        if p.startswith("http"):
            link_puro = p.split("?")[0] if "?" in p else p
            break
            
    if "Dê uma olhada em " in nome_puro:
        nome_puro = nome_puro.split("Dê uma olhada em ")[1]
    if " por R$" in nome_puro:
        nome_puro = nome_puro.split(" por R$")[0]
    if "Compre na Shopee agora!" in nome_puro:
        nome_puro = nome_puro.replace("Compre na Shopee agora!", "")
    
    nome_puro = nome_puro.replace(link_puro, "").strip()
    
    if not nome_puro or len(nome_puro) < 3:
        nome_puro = "Achado Imperdível"
        
    return nome_puro, link_puro

def gerar_textos_enciclopedia(nome, link, categoria):
    cerebro = carregar_cerebro()
    cat_data = cerebro.get(categoria, cerebro.get("Geral", DEFAULT_CEREBRO["Geral"]))
    
    tags = cat_data.get("tags", "#achados #shopee")
    
    # Processamento Inteligente de Variaveis {nome}, {link}, {tags}
    nome_curto = nome[:25] + "..." if len(nome) > 25 else nome

    tik_tit_template = random.choice(cat_data.get("ganchos_tik", ["Pare o que está fazendo e veja o {nome}:"]))
    tik_leg_template = random.choice(cat_data.get("legenda_tik", ["😱 Garanta na sacolinha amarela 👇\n{link}\n\n{tags}"]))
    
    insta_tit_template = random.choice(cat_data.get("titulos_insta", ["Você Precisa Desse {nome} ✨"]))
    insta_leg_template = random.choice(cat_data.get("legenda_insta", ["✨ O {nome} vai mudar sua rotina!\n🔗 Link na bio.\n\n{tags}"]))
    
    # Substitui as variáveis nos templates
    tik_tit = tik_tit_template.replace("{nome}", nome_curto)
    tik_leg = tik_leg_template.replace("{nome}", nome_curto).replace("{link}", link).replace("{tags}", tags)
    
    insta_tit = insta_tit_template.replace("{nome}", nome_curto)
    insta_leg = insta_leg_template.replace("{nome}", nome_curto).replace("{link}", link).replace("{tags}", tags)
    
    pin_tit = f"{nome_curto} - Review e Onde Comprar Barato"
    pin_desc = f"Procurando por {nome}? Descubra todos os detalhes e por que esse é o melhor investimento de {categoria}. Aproveite a oferta e confira o link oficial: {link}\n{tags}"
    
    shp_leg = f"Achado de ouro! {nome_curto} Confira na vitrine 👇\n{link} #achados"
    if len(shp_leg) > 150:
        shp_leg = f"Achado de ouro! Vitrine 👇\n{link} #achados"
        
    prompt_ia = f"UGC aesthetic TikTok video showcasing {nome_curto}, trendy lifestyle background, 4k"
    
    return "Vídeo Dinâmico (Alta Conversão)", tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia

# ==========================================
# LÓGICA DE NAVEGAÇÃO DAS TELAS
# ==========================================

# --- TELA 1: GERADOR DE ROTEIROS ---
if menu == "🎬 Gerar":
  st.markdown("### 🎬 Motor de Alta Conversão (100% Offline)")

  df_produtos = run_query("SELECT id, nome, nicho, link_afiliado FROM produtos WHERE id NOT IN (SELECT produto_id FROM conteudos WHERE produto_id IS NOT NULL)")

  if not df_produtos.empty:
    with st.form("form_gerador"):
      prod_escolhido = st.selectbox("Selecione o Produto", df_produtos["nome"].tolist())
      usar_ia = st.checkbox("🤖 Opcional: Tentar reescrever com IA Externa (Sujeito a limite de cota)", value=False)
      btn_gerar = st.form_submit_button("Gerar Copy Estratégica 🚀")

      if btn_gerar:
        prod_row = df_produtos.loc[df_produtos["nome"] == prod_escolhido].iloc[0]
        prod_id = int(prod_row["id"])
        link_af = str(prod_row["link_afiliado"])
        nicho = str(prod_row["nicho"])

        estrategia, tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia = gerar_textos_enciclopedia(prod_escolhido, link_af, nicho)

        if usar_ia and IA_DISPONIVEL:
          with st.spinner("Chamando a IA do Google..."):
            try:
              prompt = f"Gere textos persuasivos para afiliado. Produto: '{prod_escolhido}'. Link: {link_af}. Categoria: {nicho}.\nResponda EXATAMENTE neste formato:\nTIK_TITULO: Gancho\nTIK_LEGENDA: Legenda com sacolinha, link e hashtags\nINSTA_TITULO: Titulo\nINSTA_LEGENDA: Legenda com link na bio e hashtags\nPIN_TITULO: Titulo SEO\nPIN_DESCRICAO: Descricao rica\nSHP_LEGENDA: Legenda super curta com link\nPROMPT_IA: Prompt em inglês"
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
              st.toast("Textos gerados via Inteligência Artificial!")
            except Exception:
              st.toast("Falha na API. Acionando Motor de Copy Offline (Garantido).")

        run_query(
            "INSERT INTO conteudos (produto_id, estrategia_ia, tik_titulo_video, tik_legenda, insta_titulo_video, insta_legenda, pin_titulo, pin_descricao, shp_legenda, prompt_ia, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendente 🟡')",
            (prod_id, estrategia, tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia),
            fetch=False
        )
        st.success("🎉 Estratégia criada com sucesso! Veja na Central de Pendentes.")
        st.rerun()
  else:
    st.info("Catálogo vazio ou todos os produtos já gerados!")

# --- TELA 2: CENTRAL DE PENDENTES ---
elif menu == "📋 Pendentes":
  st.markdown("### 📋 Central de Pendentes")

  df_kanban = run_query("SELECT c.id, p.nome as produto, c.estrategia_ia, c.status, c.tik_titulo_video, c.tik_legenda, c.insta_titulo_video, c.insta_legenda, c.pin_titulo, c.pin_descricao, c.shp_legenda, c.prompt_ia FROM conteudos c LEFT JOIN produtos p ON c.produto_id = p.id WHERE p.nome IS NOT NULL ORDER BY c.id DESC")

  if not df_kanban.empty:
    for _, row in df_kanban.iterrows():
      status_ico = "✔️ Concluído" if "Concluído" in str(row["status"]) else "🟡 Pendente"
      nome_p = row["produto"] if pd.notna(row["produto"]) else "Produto"

      with st.expander(f"[{status_ico}] {nome_p}"):
        st.text_input("TikTok Gancho", value=row["tik_titulo_video"] or "", key=f"tt_{row['id']}")
        st.text_area("TikTok Legenda", value=row["tik_legenda"] or "", height=90, key=f"tl_{row['id']}")
        st.text_input("Insta Capa", value=row["insta_titulo_video"] or "", key=f"it_{row['id']}")
        st.text_area("Insta Legenda", value=row["insta_legenda"] or "", height=150, key=f"il_{row['id']}")
        st.text_input("Pinterest Título", value=row["pin_titulo"] or "", key=f"pt_{row['id']}")
        st.text_area("Pinterest Descrição", value=row["pin_descricao"] or "", height=120, key=f"pd_{row['id']}")
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

# --- TELA 3: CATÁLOGO ---
elif menu == "📦 Catálogo":
  st.markdown("### 📦 Catálogo de Produtos")
  cerebro = carregar_cerebro()
  nichos_disponiveis = list(cerebro.keys())

  with st.form("form_cat_manual"):
    texto_zap = st.text_area("Cole a mensagem do WhatsApp ou Link Shopee:", placeholder="Dê uma olhada em Caixa de som por R$100. Compre aqui: https://...")
    nicho_prod = st.selectbox("Categoria (Vinculada à sua Enciclopédia):", nichos_disponiveis)
    
    enviar = st.form_submit_button("Processar e Salvar 🚀")

    if enviar and texto_zap:
      nome_limpo, link_limpo = limpar_texto_shopee(texto_zap)
      run_query("INSERT INTO produtos (nome, nicho, link_afiliado) VALUES (?, ?, ?)", (nome_limpo, nicho_prod, link_limpo), fetch=False)
      st.success(f"Produto isolado e cadastrado: {nome_limpo}")
      st.rerun()

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

# --- TELA 4: CÉREBRO (TREINAMENTO) ---
elif menu == "🧠 Treinamento":
  st.markdown("### 🧠 Treinamento de Copy (Modo Offline)")
  st.markdown("Use `{nome}`, `{link}` e `{tags}` nos textos para o sistema substituir automaticamente na hora de gerar os roteiros.")
  
  cerebro = carregar_cerebro()
  nichos_atuais = list(cerebro.keys())
  
  escolha = st.radio("O que você deseja fazer?", ["Editar Categoria Existente", "Criar Nova Categoria"], horizontal=True)
  
  if escolha == "Editar Categoria Existente":
      nicho_selecionado = st.selectbox("Selecione a categoria para editar:", nichos_atuais)
  else:
      nicho_selecionado = st.text_input("Digite o nome da Nova Categoria (Ex: Pets, Ferramentas):")
  
  st.markdown("---")
  
  if nicho_selecionado:
      dados_atuais = cerebro.get(nicho_selecionado, {"tags": "", "ganchos_tik": [], "legenda_tik": [], "titulos_insta": [], "legenda_insta": []})
      
      with st.form("form_treino"):
          st.markdown(f"**Estratégia da categoria:** {nicho_selecionado}")
          
          tags_str = st.text_area("Hashtags Padrão:", value=dados_atuais.get("tags", ""))
          
          ganchos_str = st.text_area("Ganchos TikTok (Um por linha - Use {nome}):", value="\n".join(dados_atuais.get("ganchos_tik", [])))
          leg_tik_str = st.text_area("Legenda TikTok (Uma por linha - Use {link} e {tags}):", value="\n---\n".join(dados_atuais.get("legenda_tik", [])))
          
          titulos_str = st.text_area("Títulos Insta (Um por linha - Use {nome}):", value="\n".join(dados_atuais.get("titulos_insta", [])))
          leg_ins_str = st.text_area("Legenda Insta (Uma por linha - Separe opções com '---'):", value="\n---\n".join(dados_atuais.get("legenda_insta", [])))
          
          salvar_treino = st.form_submit_button("💾 Salvar Aprendizado no Cérebro")
          
          if salvar_treino:
              cerebro[nicho_selecionado] = {
                  "tags": tags_str.strip(),
                  "ganchos_tik": [g.strip() for g in ganchos_str.split("\n") if g.strip() and g != "---"],
                  "legenda_tik": [l.strip() for l in leg_tik_str.split("\n---\n") if l.strip()],
                  "titulos_insta": [t.strip() for t in titulos_str.split("\n") if t.strip() and t != "---"],
                  "legenda_insta": [l.strip() for l in leg_ins_str.split("\n---\n") if l.strip()]
              }
              
              salvar_cerebro(cerebro)
              st.success(f"🧠 Copywriter atualizado! A categoria '{nicho_selecionado}' usará essas estratégias de alta conversão.")
              st.rerun()

# --- TELA 5: DASHBOARD ---
elif menu == "📊 Dashboard":
  st.markdown("### 📊 Dashboard & Metas")
  total = len(run_query("SELECT * FROM conteudos WHERE status LIKE '%Concluído%'"))
  st.metric(label="Vídeos Concluídos", value=f"{total} / 15")
