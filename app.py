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
    
    /* Controle rigoroso do Banner para não estourar no tablet/desktop */
    .banner-container {
        display: flex;
        flex-direction: column;
        justify-content: center;
        align-items: center;
        width: 100%;
        text-align: center;
        margin-bottom: 10px;
    }
    .banner-container img {
        max-width: 500px !important;
        width: 100% !important;
        border-radius: 10px;
        height: auto !important;
    }
    .app-title {
        font-size: 28px;
        font-weight: bold;
        color: #FF4500;
        margin-top: 10px;
        margin-bottom: 0px;
    }
    .app-subtitle {
        color: #FF7F50;
        font-size: 14px;
        margin-top: -5px;
    }
    </style>
""",
    unsafe_allow_html=True,
)

# --- CABEÇALHO COM LOGO/BANNER CONTROLADO E TÍTULO GARANTIDO ---
st.markdown('<div class="banner-container">', unsafe_allow_html=True)

imagem_exibida = False
try:
    if os.path.exists("banner.jpg"):
        st.image("banner.jpg")
        imagem_exibida = True
    elif os.path.exists("banner.png"):
        st.image("banner.png")
        imagem_exibida = True
except:
    pass

# Se não houver imagem de banner física, ou para garantir identidade visual sempre presente:
st.markdown('<p class="app-title">🔎 Central Achados do Felipe</p>', unsafe_allow_html=True)
st.markdown('<p class="app-subtitle">Sua Máquina de Conteúdo e Automação Offline</p>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)
st.markdown("---")

menu = st.radio(
    "Navegação Rápida", 
    ["🎬 Gerar", "📋 Pendentes", "📦 Catálogo", "🧠 Treinamento", "🧬 Auto-Evolução", "📊 Dashboard"], 
    horizontal=True
)
st.markdown("---")

# --- GERENCIAMENTO DO CÉREBRO JSON ---
CEREBRO_FILE = "cerebro_v3.json"

def carregar_cerebro():
    if not os.path.exists(CEREBRO_FILE):
        default_base = {
            "Utilidades & Acessórios": {
                "tags": "#achadosshopee #utilidades #achadinhos #shopeebrasil #dicautil #solucoes",
                "ganchos_tik": [
                    "Você não vai acreditar no que o {nome} consegue resolver no dia a dia:",
                    "O item mais engenhoso que encontrei na Shopee:",
                    "Como eu sofria antes de conhecer o {nome}:"
                ],
                "legenda_tik": [
                    "😱 Chega de perrengues! {destaque} Garanta o seu na sacolinha amarela antes que acabe 👇\n{link}\n\n{tags}"
                ],
                "titulos_insta": ["Praticidade Real 🛡️", "O Item que Faltava: {nome}"],
                "legenda_insta": [
                    "🛡️ Sabe aquele produto que parece simples, mas muda completamente a sua rotina?\n\nO {nome} é exatamente isso. {destaque} Prático, funcional e com um preço surreal na Shopee.\n\n🔗 Corre no link da BIO para garantir o seu com segurança!\n\n{tags}"
                ]
            },
            "Geral (Coringa)": {
                "tags": "#achados #achadinhos #shopeebrasil #comprasshopee",
                "ganchos_tik": ["Olha esse achado imperdível:"],
                "legenda_tik": ["😱 Garanta na sacolinha amarela 👇\n{link}\n\n{tags}"],
                "titulos_insta": ["Achado de Ouro 🏆"],
                "legenda_insta": ["🚀 Sabe aquele produto útil? O {nome} é perfeito. {destaque}\n🔗 Link na BIO.\n\n{tags}"]
            }
        }
        with open(CEREBRO_FILE, "w", encoding="utf-8") as f:
            json.dump(default_base, f, indent=4, ensure_ascii=False)
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

# --- CONFIGURAÇÃO DA IA ---
IA_DISPONIVEL = False
client = None
try:
  from google import genai
  api_key = st.secrets["GEMINI_API_KEY"]
  client = genai.Client(api_key=api_key)
  IA_DISPONIVEL = True
except Exception:
  pass

# --- MOTOR DE ATRIBUTOS E EXTRATOR INTELIGENTE ---
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
    
    atributos = []
    t_lower = nome_puro.lower()
    
    bat_match = re.search(r'(\d+)\s*h', t_lower)
    if bat_match: atributos.append(f"bateria de {bat_match.group(1)}h")
    elif "bateria" in t_lower: atributos.append("bateria de longa duração")
    
    if "ip" in t_lower or "água" in t_lower: atributos.append("proteção total contra água")
    if "bluetooth" in t_lower or "sem fio" in t_lower: atributos.append("conexão sem fio de alta estabilidade")
    if "automático" in t_lower or "automatico" in t_lower: atributos.append("sistema de acionamento automático")
    if "vento" in t_lower or "reforçado" in t_lower: atributos.append("estrutura reforçada contra ventos fortes")
    if "uv" in t_lower or "proteção solar" in t_lower: atributos.append("proteção contra raios UV")
    
    frase_destaque = "Design moderno, alta durabilidade e acabamento premium."
    if atributos:
        frase_destaque = f"Ele conta com { ' e '.join(atributos[:2]) }, garantindo máxima eficiência no uso diário!"

    palavras = nome_puro.split()
    nome_curto = " ".join(palavras[:5]).rstrip(",-:")
    if not nome_curto:
        nome_curto = "Achado Imperdível"
        nome_puro = "Produto Shopee"
        
    return nome_puro, nome_curto, link_puro, frase_destaque

def gerar_textos_hibridos(nome_curto, nome_longo, link, categoria, destaque, usar_ia_forcado=False):
    cerebro = carregar_cerebro()
    cat_data = cerebro.get(categoria, cerebro.get("Geral (Coringa)", list(cerebro.values())[0]))
    
    tags = cat_data.get("tags", "#achados #shopee")
    
    if usar_ia_forcado and IA_DISPONIVEL:
        try:
            prompt = f"""Gere textos altamente persuasivos para afiliado baseados nas especificações reais, com português natural e fluído.
Produto Completo: '{nome_longo}'
Link: {link}
Categoria: {categoria}

Responda EXATAMENTE neste formato de chaves:
TIK_TITULO: Gancho curto e magnético para TikTok
TIK_LEGENDA: Legenda para TikTok com sacolinha e tags ({tags})
INSTA_TITULO: Título chamativo para Capa do Reels
INSTA_LEGENDA: Legenda rica e persuasiva para Instagram com link na bio e tags ({tags})
PIN_TITULO: Título rico em SEO para Pinterest
PIN_DESCRICAO: Descrição rica, técnica e completa para Pinterest usando todas as especificações do produto, com chamada para ação e tags ({tags})
SHP_LEGENDA: Legenda curta para Shopee Vídeo com link
PROMPT_IA: Prompt em inglês para imagem"""
            
            res = client.models.generate_content(model="gemini-2.5-flash", contents=prompt).text
            
            t_tit, t_leg, i_tit, i_leg, p_tit, p_desc, s_leg, p_ia = "", "", "", "", "", "", "", ""
            for l in res.split("\n"):
                if ":" in l:
                    ch, val = l.split(":", 1)
                    ch, val = ch.strip().upper(), val.strip()
                    if "TIK_TITULO" in ch: t_tit = val
                    elif "TIK_LEGENDA" in ch: t_leg = val
                    elif "INSTA_TITULO" in ch: i_tit = val
                    elif "INSTA_LEGENDA" in ch: i_leg = val
                    elif "PIN_TITULO" in ch: p_tit = val
                    elif "PIN_DESCRICAO" in ch: p_desc = val
                    elif "SHP_LEGENDA" in ch: s_leg = val
                    elif "PROMPT_IA" in ch: p_ia = val
            
            if t_tit and p_desc:
                return "Gerado via IA Híbrida 🤖", t_tit, t_leg, i_tit, i_leg, p_tit, p_desc, s_leg, p_ia
        except Exception as e:
            st.toast(f"Aviso de IA: {e}")

    tik_tit_template = random.choice(cat_data.get("ganchos_tik", ["Olha esse achado imperdível:"]))
    tik_leg_template = random.choice(cat_data.get("legenda_tik", ["Garanta na sacolinha 👇\n{link}\n\n{tags}"]))
    insta_tit_template = random.choice(cat_data.get("titulos_insta", ["Achado Imperdível ✨"]))
    insta_leg_template = random.choice(cat_data.get("legenda_insta", ["Confira os detalhes de {nome}! {destaque}\n🔗 Link na bio.\n\n{tags}"]))
    
    tik_tit = tik_tit_template.replace("{nome}", nome_curto).replace("{destaque}", destaque)
    tik_leg = tik_leg_template.replace("{nome}", nome_curto).replace("{link}", link).replace("{tags}", tags).replace("{destaque}", destaque)
    
    insta_tit = insta_tit_template.replace("{nome}", nome_curto)
    insta_leg = insta_leg_template.replace("{nome}", nome_curto).replace("{link}", link).replace("{tags}", tags).replace("{destaque}", destaque)
    
    pin_tit = f"{nome_curto} - Review Completo e Onde Comprar"
    pin_desc = f"Procurando por {nome_longo}? Descubra todos os detalhes e diferenciais deste excelente produto da categoria {categoria}. {destaque} O item ideal para quem busca praticidade, durabilidade e excelente custo-benefício. Aproveite a oferta oficial e confira o link de desconto direto: {link} \n\nTags recomendadas: {tags}"
    
    shp_leg = f"Achado imperdível! {nome_curto}. Confira na vitrine 👇\n{link} #achados"
    if len(shp_leg) > 150:
        shp_leg = f"Achado imperdível! Vitrine 👇\n{link} #achados"
        
    prompt_ia = f"UGC aesthetic video showcasing {nome_curto}, trendy lifestyle background, 4k"
    
    return "Motor Offline Inteligente (Aprimorado)", tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia

# ==========================================
# TELAS DO SISTEMA
# ==========================================

if menu == "🎬 Gerar":
  st.markdown("### 🎬 Central de Geração Estratégica")

  df_produtos = run_query("SELECT id, nome, nome_curto, destaques, nicho, link_afiliado FROM produtos WHERE id NOT IN (SELECT produto_id FROM conteudos WHERE produto_id IS NOT NULL)")

  if not df_produtos.empty:
    with st.form("form_gerador"):
      prod_escolhido = st.selectbox("Selecione o Produto", df_produtos["nome"].tolist())
      
      modo_geracao = st.radio(
          "Escolha o Motor de Geração:",
          ["⚡ Motor Offline Inteligente (Garantido e Natural)", "🤖 Tentar Forçar com Inteligência Artificial (Gemini)"],
          index=0
      )
      
      btn_gerar = st.form_submit_button("Gerar Pacote de Roteiros 🚀")

      if btn_gerar:
        prod_row = df_produtos.loc[df_produtos["nome"] == prod_escolhido].iloc[0]
        prod_id = int(prod_row["id"])
        link_af = str(prod_row["link_afiliado"])
        nicho = str(prod_row["nicho"])
        n_longo = str(prod_row["nome"])
        n_curto = str(prod_row["nome_curto"]) if pd.notna(prod_row["nome_curto"]) else n_longo[:25]
        destaque = str(prod_row["destaques"]) if pd.notna(prod_row["destaques"]) else "Qualidade garantida!"

        usar_ia = True if "Inteligência Artificial" in modo_geracao else False

        with st.spinner("Processando roteiros e otimizando o texto..."):
            estrategia, tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia = gerar_textos_hibridos(
                n_curto, n_longo, link_af, nicho, destaque, usar_ia_forcado=usar_ia
            )

        run_query(
            "INSERT INTO conteudos (produto_id, estrategia_ia, tik_titulo_video, tik_legenda, insta_titulo_video, insta_legenda, pin_titulo, pin_descricao, shp_legenda, prompt_ia, status) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 'Pendente 🟡')",
            (prod_id, estrategia, tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia),
            fetch=False
        )
        st.success(f"🎉 Sucesso! Método utilizado: {estrategia}")
        st.rerun()
  else:
    st.info("Catálogo vazio ou todos os produtos já gerados!")

elif menu == "📋 Pendentes":
  st.markdown("### 📋 Central de Pendentes")

  df_kanban = run_query("SELECT c.id, p.nome_curto as produto, c.estrategia_ia, c.status, c.tik_titulo_video, c.tik_legenda, c.insta_titulo_video, c.insta_legenda, c.pin_titulo, c.pin_descricao, c.shp_legenda, c.prompt_ia FROM conteudos c LEFT JOIN produtos p ON c.produto_id = p.id WHERE p.nome IS NOT NULL ORDER BY c.id DESC")

  if not df_kanban.empty:
    for _, row in df_kanban.iterrows():
      status_ico = "✔️ Concluído" if "Concluído" in str(row["status"]) else "🟡 Pendente"
      nome_p = row["produto"] if pd.notna(row["produto"]) else "Produto"

      with st.expander(f"[{status_ico}] {nome_p} — ({row['estrategia_ia']})"):
        st.text_input("TikTok Gancho", value=row["tik_titulo_video"] or "", key=f"tt_{row['id']}")
        st.text_area("TikTok Legenda", value=row["tik_legenda"] or "", height=90, key=f"tl_{row['id']}")
        st.text_input("Insta Capa", value=row["insta_titulo_video"] or "", key=f"it_{row['id']}")
        st.text_area("Insta Legenda", value=row["insta_legenda"] or "", height=150, key=f"il_{row['id']}")
        st.text_input("Pinterest Título", value=row["pin_titulo"] or "", key=f"pt_{row['id']}")
        st.text_area("Pinterest Descrição (SEO Completo)", value=row["pin_descricao"] or "", height=160, key=f"pd_{row['id']}")
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

elif menu == "📦 Catálogo":
  st.markdown("### 📦 Catálogo de Produtos")
  cerebro = carregar_cerebro()
  nichos_disponiveis = list(cerebro.keys())

  with st.form("form_cat_manual"):
    texto_zap = st.text_area("Cole a mensagem do WhatsApp ou Link Shopee:", placeholder="Dê uma olhada em Guarda-chuva automático por R$50...")
    nicho_prod = st.selectbox("Categoria:", nichos_disponiveis)
    
    enviar = st.form_submit_button("Analisar e Salvar no Catálogo 🚀")

    if enviar and texto_zap:
      nome_puro, nome_curto, link_limpo, frase_destaque = limpar_e_extrair_shopee(texto_zap)
      
      run_query(
          "INSERT INTO produtos (nome, nome_curto, destaques, nicho, link_afiliado) VALUES (?, ?, ?, ?, ?)", 
          (nome_puro, nome_curto, frase_destaque, nicho_prod, link_limpo), 
          fetch=False
      )
      st.success(f"Cadastrado! Nome Curto: {nome_curto} | Atributo extraído: {frase_destaque}")
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

elif menu == "🧠 Treinamento":
  st.markdown("### 🧠 Categorias Existentes no Cérebro")
  cerebro = carregar_cerebro()
  for cat in cerebro.keys():
      st.markdown(f"- 📁 **{cat}**")
  st.info("Dica: Use a aba '🧬 Auto-Evolução' para criar novas categorias automaticamente com a IA.")

elif menu == "🧬 Auto-Evolução":
  st.markdown("### 🧬 Auto-Evolução do Cérebro Offline")
  st.markdown("Digite abaixo o nome de uma nova categoria ou nicho (Ex: *Utilidades e Ferramentas*, *Moda e Acessórios*).")

  with st.form("form_auto_evolucao"):
    novo_nicho = st.text_input("Nome da Nova Categoria/Nicho:", placeholder="Ex: Utilidades e Ferramentas")
    btn_evoluir = st.form_submit_button("Gerar e Injetar Categoria no Cérebro 🧬")

    if btn_evoluir and novo_nicho:
      if not IA_DISPONIVEL:
        st.error("A API do Gemini não está configurada ou disponível no momento.")
      else:
        with st.spinner(f"A Inteligência Artificial está criando as regras de copy para '{novo_nicho}'..."):
          try:
            prompt_evolucao = f"""Crie uma estrutura JSON de copywriting de alta conversão para o nicho de e-commerce/afiliados chamado '{novo_nicho}'.
Responda APENAS com um objeto JSON válido, sem markdown extra, contendo exatamente estas chaves:
{{
  "{novo_nicho}": {{
    "tags": "#hashtag1 #hashtag2 #hashtag3 #hashtag4",
    "ganchos_tik": [
      "Gancho magnético 1 com {{nome}}:",
      "Gancho magnético 2 com {{nome}}:"
    ],
    "legenda_tik": [
      "Legenda envolvente para TikTok com {{link}}, {{tags}} e {{destaque}}"
    ],
    "titulos_insta": [
      "Título de Capa 1",
      "Título de Capa 2"
    ],
    "legenda_insta": [
      "Legenda persuasiva estruturada para Instagram para o produto {{nome}}, destacando benefícios, com chamada para ação, {{link}} e {{tags}}."
    ]
  }}
}}"""
            resposta_ia = client.models.generate_content(model="gemini-2.5-flash", contents=prompt_evolucao).text
            
            limpo = resposta_ia.replace("```json", "").replace("```", "").strip()
            novo_bloco = json.loads(limpo)
            
            cerebro_atual = carregar_cerebro()
            cerebro_atual.update(novo_bloco)
            salvar_cerebro(cerebro_atual)
            
            st.success(f"🧬 Sucesso absoluto! A categoria '{novo_nicho}' foi aprendida e injetada no seu arquivo JSON.")
          except Exception as e:
            st.error(f"Erro ao processar a evolução automática: {e}")

elif menu == "📊 Dashboard":
  st.markdown("### 📊 Dashboard & Metas")
  total = len(run_query("SELECT * FROM conteudos WHERE status LIKE '%Concluído%'"))
  st.metric(label="Vídeos Concluídos", value=f"{total} / 15")
