import os
import json
import sqlite3
import pandas as pd
import streamlit as st
import random
import re

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
    
    .card { background-color: #282828; padding: 15px; border-radius: 12px; margin-bottom: 12px; box-shadow: 0 4px 6px rgba(0,0,0,0.3); border-left: 5px solid #FF4500; }
    .metric-card { background-color: #282828; padding: 15px; border-radius: 10px; text-align: center; border-bottom: 4px solid #FF4500; }
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

menu = st.radio("Navegação Rápida", ["🎬 Gerar", "📋 Pendentes", "📦 Catálogo", "🧠 Treinamento", "📊 Dashboard"], horizontal=True)
st.markdown("---")

# --- MEGA CÉREBRO V3 (COM VARIÁVEL {destaque} DINÂMICA) ---
CEREBRO_FILE = "cerebro_v3.json"

DEFAULT_CEREBRO = {
    "Casa & Decoração": {
        "tags": "#donadecasa #dicaspracasa #decoracao #achadinhosshopee #shopeebrasil",
        "ganchos_tik": ["Sua casa precisa desse achado urgente:", "Como deixar sua casa mais moderna gastando pouco:", "Testei o achado que viralizou no app vizinho!"],
        "legenda_tik": ["😱 {destaque} Já garante na sacolinha amarela antes que esgote 👇\n{link}\n\n{tags}", "✨ O segredo da casa Pinterest revelado! Link na sacolinha 👇\n{link}\n\n{tags}"],
        "titulos_insta": ["O Segredo da Casa Perfeita 🏡", "Transforme seu Lar com {nome} ✨"],
        "legenda_insta": ["✨ Por que ninguém me avisou disso antes?\n\nEsse achado chamado {nome} muda a rotina e deixa tudo mais prático. {destaque}\n\n🔗 Comente 'EU QUERO' ou clique no link da BIO para garantir com desconto.\n\n{tags}"]
    },
    "Eletrônicos": {
        "tags": "#tecnologia #eletronicos #setupgamer #dicastech #achadosshopee #shopeebr",
        "ganchos_tik": ["A tecnologia que você precisava e não sabia:", "O segredo para um setup perfeito gastando pouco:", "Não compre eletrônicos antes de ver esse achado:"],
        "legenda_tik": ["⚡ {destaque} Corre na sacolinha amarela 👇\n{link}\n\n{tags}", "Setup atualizado com sucesso 🚀 Link na sacolinha 👇\n{link}\n\n{tags}"],
        "titulos_insta": ["Tech Premium e Barata 💻", "Upgrade Obrigatório: {nome} ⚡"],
        "legenda_insta": ["⚡ Procura qualidade sem pagar preço de grife?\n\nO achado {nome} entrega tudo! {destaque} Um custo-benefício que só achando na Shopee pra acreditar.\n\n🔗 Corre no link da BIO antes que o estoque acabe!\n\n{tags}"]
    },
    "Geral": {
        "tags": "#achados #achadinhos #shopeebrasil #comprasshopee #dicas",
        "ganchos_tik": ["Pare de rolar o feed e veja esse achado:", "Comprei o item mais útil da Shopee:", "Como eu vivi tanto tempo sem isso?"],
        "legenda_tik": ["🚀 Praticidade em nível máximo! {destaque} Link na sacolinha 👇\n{link}\n\n{tags}", "Genial! E o preço tá surreal na sacolinha 👇\n{link}\n\n{tags}"],
        "titulos_insta": ["Achado de Ouro 🏆", "Você Precisa de um {nome} 🚀"],
        "legenda_insta": ["🚀 Sabe aquele produto que você não sabia que precisava até ver?\n\nO item {nome} é exatamente assim! Ele resolve problemas do dia a dia e impressiona pela qualidade. {destaque}\n\n🔗 O link tá te esperando na BIO.\n\n{tags}"]
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
            nome_curto TEXT,
            destaques TEXT,
            nicho TEXT,
            link_afiliado TEXT
        )
    """)
  # Atualiza tabela antiga caso não tenha as colunas novas
  try:
      cursor.execute("ALTER TABLE produtos ADD COLUMN nome_curto TEXT")
      cursor.execute("ALTER TABLE produtos ADD COLUMN destaques TEXT")
  except:
      pass
      
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

# --- INTELIGÊNCIA EXTRATORA OFFLINE (MOTOR DE ATRIBUTOS) ---
def limpar_e_extrair_shopee(texto_bruto):
    link_puro = texto_bruto
    for p in texto_bruto.split():
        if p.startswith("http"):
            link_puro = p.split("?")[0] if "?" in p else p
            break
            
    nome_puro = texto_bruto
    if "Dê uma olhada em " in nome_puro:
        nome_puro = nome_puro.split("Dê uma olhada em ")[1]
    if " por R$" in nome_puro:
        nome_puro = nome_puro.split(" por R$")[0]
    nome_puro = nome_puro.replace("Compre na Shopee agora!", "").replace(link_puro, "").strip()
    
    # 1. Extração Inteligente de Benefícios
    atributos = []
    t_lower = nome_puro.lower()
    
    # Busca tempo de bateria (ex: 34h)
    bat_match = re.search(r'(\d+)\s*h', t_lower)
    if bat_match: atributos.append(f"bateria de {bat_match.group(1)}h")
    elif "bateria" in t_lower: atributos.append("bateria de longa duração")
    
    if "ip" in t_lower or "água" in t_lower: atributos.append("proteção extra contra água")
    if "bluetooth" in t_lower or "sem fio" in t_lower: atributos.append("conexão sem fio")
    if "gb" in t_lower: atributos.append("alto armazenamento")
    if "led" in t_lower or "rgb" in t_lower: atributos.append("iluminação led")
    
    frase_destaque = "Design impecável e super funcional!"
    if atributos:
        frase_destaque = "Ele entrega " + " e ".join(atributos[:2]) + "!"

    # 2. Criar Nome Curto Comercial (Pega apenas as primeiras 5 palavras)
    palavras = nome_puro.split()
    nome_curto = " ".join(palavras[:5]).rstrip(",-:")
    
    if not nome_curto:
        nome_curto = "Achado Imperdível"
        nome_puro = "Produto Shopee"
        
    return nome_puro, nome_curto, link_puro, frase_destaque

def gerar_textos_enciclopedia(nome_curto, nome_longo, link, categoria, destaque):
    cerebro = carregar_cerebro()
    cat_data = cerebro.get(categoria, cerebro.get("Geral", DEFAULT_CEREBRO["Geral"]))
    
    tags = cat_data.get("tags", "#achados #shopee")

    tik_tit_template = random.choice(cat_data.get("ganchos_tik", ["Pare o que está fazendo e veja esse achado:"]))
    tik_leg_template = random.choice(cat_data.get("legenda_tik", ["😱 Garanta na sacolinha amarela 👇\n{link}\n\n{tags}"]))
    
    insta_tit_template = random.choice(cat_data.get("titulos_insta", ["Achado Obrigatório ✨"]))
    insta_leg_template = random.choice(cat_data.get("legenda_insta", ["✨ O {nome} vai mudar sua rotina! {destaque}\n🔗 Link na bio.\n\n{tags}"]))
    
    # Substitui as variáveis
    tik_tit = tik_tit_template.replace("{nome}", nome_curto).replace("{destaque}", destaque)
    tik_leg = tik_leg_template.replace("{nome}", nome_curto).replace("{link}", link).replace("{tags}", tags).replace("{destaque}", destaque)
    
    insta_tit = insta_tit_template.replace("{nome}", nome_curto)
    insta_leg = insta_leg_template.replace("{nome}", nome_curto).replace("{link}", link).replace("{tags}", tags).replace("{destaque}", destaque)
    
    pin_tit = f"{nome_curto} - Melhor Oferta e Review"
    pin_desc = f"Procurando por {nome_curto}? Descubra todos os detalhes. {destaque} Aproveite a oferta e confira o link oficial: {link}\n{tags}"
    
    shp_leg = f"Achado de ouro! {nome_curto}. Confira na vitrine 👇\n{link} #achados"
    if len(shp_leg) > 150:
        shp_leg = f"Achado de ouro! Vitrine 👇\n{link} #achados"
        
    prompt_ia = f"UGC aesthetic TikTok video showcasing {nome_curto}, trendy lifestyle background, 4k"
    
    return "Motor Offline V3 - Inteligência de Atributos", tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia

# ==========================================
# LÓGICA DE NAVEGAÇÃO DAS TELAS
# ==========================================

# --- TELA 1: GERADOR DE ROTEIROS ---
if menu == "🎬 Gerar":
  st.markdown("### 🎬 Motor de Alta Conversão (Inteligência Local)")

  df_produtos = run_query("SELECT id, nome, nome_curto, destaques, nicho, link_afiliado FROM produtos WHERE id NOT IN (SELECT produto_id FROM conteudos WHERE produto_id IS NOT NULL)")

  if not df_produtos.empty:
    with st.form("form_gerador"):
      prod_escolhido = st.selectbox("Selecione o Produto", df_produtos["nome"].tolist())
      btn_gerar = st.form_submit_button("Gerar Copy Estratégica 🚀")

      if btn_gerar:
        prod_row = df_produtos.loc[df_produtos["nome"] == prod_escolhido].iloc[0]
        prod_id = int(prod_row["id"])
        link_af = str(prod_row["link_afiliado"])
        nicho = str(prod_row["nicho"])
        
        # Puxa as variáveis inteligentes recém salvas
        n_curto = str(prod_row["nome_curto"]) if pd.notna(prod_row["nome_curto"]) else str(prod_row["nome"])[:25]
        destaque = str(prod_row["destaques"]) if pd.notna(prod_row["destaques"]) else "Design impecável e super funcional!"

        estrategia, tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia = gerar_textos_enciclopedia(n_curto, prod_escolhido, link_af, nicho, destaque)

        run_query(
            "INSERT INTO conteudos (produto_id, estrategia_ia, tik_titulo_video, tik_legenda, insta_titulo_video, insta_legenda, pin_titulo, pin_descricao, shp_legenda, prompt_ia, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendente 🟡')",
            (prod_id, estrategia, tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia),
            fetch=False
        )
        st.success("🎉 Roteiro inteligente gerado offline com sucesso!")
        st.rerun()
  else:
    st.info("Catálogo vazio ou todos os produtos já gerados!")

# --- TELA 2: CENTRAL DE PENDENTES ---
elif menu == "📋 Pendentes":
  st.markdown("### 📋 Central de Pendentes")

  df_kanban = run_query("SELECT c.id, p.nome_curto as produto, c.estrategia_ia, c.status, c.tik_titulo_video, c.tik_legenda, c.insta_titulo_video, c.insta_legenda, c.pin_titulo, c.pin_descricao, c.shp_legenda, c.prompt_ia FROM conteudos c LEFT JOIN produtos p ON c.produto_id = p.id WHERE p.nome IS NOT NULL ORDER BY c.id DESC")

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

# --- TELA 3: CATÁLOGO INTELIGENTE ---
elif menu == "📦 Catálogo":
  st.markdown("### 📦 Catálogo de Produtos")
  cerebro = carregar_cerebro()
  nichos_disponiveis = list(cerebro.keys())

  with st.form("form_cat_manual"):
    texto_zap = st.text_area("Cole a mensagem do WhatsApp:", placeholder="Dê uma olhada em Caixa de som por R$100. Compre aqui: https://...")
    nicho_prod = st.selectbox("Categoria:", nichos_disponiveis)
    
    enviar = st.form_submit_button("Analisar e Salvar 🚀")

    if enviar and texto_zap:
      # O MOTOR RODA AQUI AGORA! Extrai os dados antes de salvar no banco
      nome_puro, nome_curto, link_limpo, frase_destaque = limpar_e_extrair_shopee(texto_zap)
      
      run_query(
          "INSERT INTO produtos (nome, nome_curto, destaques, nicho, link_afiliado) VALUES (?, ?, ?, ?, ?)", 
          (nome_puro, nome_curto, frase_destaque, nicho_prod, link_limpo), 
          fetch=False
      )
      st.success(f"Analise Completa! Produto reconhecido: {nome_curto} | Identificado: {frase_destaque}")
      st.rerun()

  st.markdown("---")
  df_p = run_query("SELECT id, nome_curto, destaques FROM produtos ORDER BY id DESC")
  if not df_p.empty:
    for _, row in df_p.iterrows():
      c1, c2 = st.columns([4, 1])
      with c1: 
          st.markdown(f"**📦 {row['nome_curto']}**")
          st.caption(f"💡 {row['destaques']}")
      with c2:
        if st.button("Excluir 🗑️", key=f"dp_{row['id']}"):
          run_query("DELETE FROM conteudos WHERE produto_id = ?", (row['id'],), fetch=False)
          run_query("DELETE FROM produtos WHERE id = ?", (row['id'],), fetch=False)
          st.rerun()
      st.markdown("---")

# --- TELA 4: CÉREBRO (TREINAMENTO) ---
elif menu == "🧠 Treinamento":
  st.markdown("### 🧠 Treinamento de Copy (Modo Offline)")
  st.markdown("Variavéis mágicas: `{nome}` = Nome encurtado bonito | `{destaque}` = Benefícios extraídos | `{link}` = Seu link")
  
  cerebro = carregar_cerebro()
  nichos_atuais = list(cerebro.keys())
  
  escolha = st.radio("O que você deseja fazer?", ["Editar Categoria Existente", "Criar Nova Categoria"], horizontal=True)
  
  if escolha == "Editar Categoria Existente":
      nicho_selecionado = st.selectbox("Selecione a categoria para editar:", nichos_atuais)
  else:
      nicho_selecionado = st.text_input("Digite o nome da Nova Categoria:")
  
  st.markdown("---")
  
  if nicho_selecionado:
      dados_atuais = cerebro.get(nicho_selecionado, {"tags": "", "ganchos_tik": [], "legenda_tik": [], "titulos_insta": [], "legenda_insta": []})
      
      with st.form("form_treino"):
          st.markdown(f"**Estratégia da categoria:** {nicho_selecionado}")
          
          tags_str = st.text_area("Hashtags Padrão:", value=dados_atuais.get("tags", ""))
          ganchos_str = st.text_area("Ganchos TikTok (Um por linha - Use {nome}):", value="\n".join(dados_atuais.get("ganchos_tik", [])))
          leg_tik_str = st.text_area("Legenda TikTok (Separe opções com '---'):", value="\n---\n".join(dados_atuais.get("legenda_tik", [])))
          titulos_str = st.text_area("Títulos Insta (Um por linha - Use {nome}):", value="\n".join(dados_atuais.get("titulos_insta", [])))
          leg_ins_str = st.text_area("Legenda Insta (Separe opções com '---'):", value="\n---\n".join(dados_atuais.get("legenda_insta", [])))
          
          salvar_treino = st.form_submit_button("💾 Salvar Aprendizado")
          
          if salvar_treino:
              cerebro[nicho_selecionado] = {
                  "tags": tags_str.strip(),
                  "ganchos_tik": [g.strip() for g in ganchos_str.split("\n") if g.strip() and g != "---"],
                  "legenda_tik": [l.strip() for l in leg_tik_str.split("\n---\n") if l.strip()],
                  "titulos_insta": [t.strip() for t in titulos_str.split("\n") if t.strip() and t != "---"],
                  "legenda_insta": [l.strip() for l in leg_ins_str.split("\n---\n") if l.strip()]
              }
              salvar_cerebro(cerebro)
              st.success("🧠 Copywriter atualizado!")
              st.rerun()

# --- TELA 5: DASHBOARD ---
elif menu == "📊 Dashboard":
  st.markdown("### 📊 Dashboard & Metas")
  total = len(run_query("SELECT * FROM conteudos WHERE status LIKE '%Concluído%'"))
  st.metric(label="Vídeos Concluídos", value=f"{total} / 15")
