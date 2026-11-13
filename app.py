# -*- coding: utf-8 -*-
"""
Achados do Felipe - Dashboard Oficial (app.py)
Autor: Felipe de Oliveira Gonçalves (@achadosfelipe01)
"""

import json
import os
import re
import sqlite3
import pandas as pd
import streamlit as st

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
    [data-testid="collapsedControl"] { display: none; }
    
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

# --- CABEÇALHO ---
st.markdown('<div class="banner-container">', unsafe_allow_html=True)
try:
  if os.path.exists("banner.jpg"):
    st.image("banner.jpg")
  elif os.path.exists("banner.png"):
    st.image("banner.png")
except:
  pass

st.markdown(
    '<p class="app-title">🔎 Central Achados do Felipe</p>',
    unsafe_allow_html=True,
)
st.markdown(
    '<p class="app-subtitle">Sua Máquina de Conteúdo e Automação Híbrida</p>',
    unsafe_allow_html=True,
)
st.markdown("</div>", unsafe_allow_html=True)
st.markdown("---")

menu = st.radio(
    "Navegação Rápida",
    [
        "🎬 Gerar",
        "📋 Pendentes",
        "📦 Catálogo",
        "🧠 Treinamento",
        "🧬 Auto-Evolução",
        "📊 Dashboard",
    ],
    horizontal=True,
)
st.markdown("---")


# --- GERENCIAMENTO DO CÉREBRO JSON ---
CEREBRO_FILE = "cerebro_v3.json"


def carregar_cerebro():
  if not os.path.exists(CEREBRO_FILE):
    default_base = {
        "configuracao_geral": {
            "versao": "19.0",
            "objetivo": "Matriz de inteligência de conteúdo",
        },
        "categorias_e_regras": {
            "Utilidades para Casa": {
                "tags_obrigatorias": ["#achadosshopee", "#utilidadesdomesticas", "#donadecasa"],
            }
        },
    }
    with open(CEREBRO_FILE, "w", encoding="utf-8") as f:
      json.dump(default_base, f, indent=4, ensure_ascii=False)

  try:
    with open(CEREBRO_FILE, "r", encoding="utf-8") as f:
      dados = json.load(f)
      if "categorias_e_regras" not in dados:
        dados["categorias_e_regras"] = {}
      return dados
  except:
    return {"categorias_e_regras": {}}


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


# --- CONFIGURAÇÃO DA IA (GEMINI) ---
IA_DISPONIVEL = False
client = None
try:
  from google import genai

  api_key = st.secrets.get("GEMINI_API_KEY", "")
  if api_key:
    client = genai.Client(api_key=api_key)
    IA_DISPONIVEL = True
except Exception:
  pass


# --- EXTRATOR DE ATRIBUTOS E HÍBRIDO INTELIGENTE ---
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
  nome_puro = (
      nome_puro.replace("Compre na Shopee agora!", "")
      .replace(link_puro, "")
      .strip()
  )

  t_lower = nome_puro.lower()

  # DETECÇÃO INTELIGENTE DE NICHO PARA O MODO OFFLINE
  if any(k in t_lower for k in ["controle", "xbox", "playstation", "joystick", "gamer", "console"]):
    frase_destaque = "Produto original lacrado, ergonomia perfeita e resposta ultra-rápida nos comandos para máxima imersão."
    insight_formato = "🎬 FORMATO IDEAL: VÍDEO DEMONSTRATIVO (Unboxing ou jogabilidade ao fundo engaja muito)."
    prompt_base_ia = f"Professional product photography of a sleek wireless gaming controller, clean minimalist setup, soft ambient backlighting with subtle RGB glow, dark matte surface, high-end tech aesthetic, 9:16 format"
  elif any(k in t_lower for k in ["shampoo", "condicionador", "cabelo", "infantil", "salon line", "litro"]):
    frase_destaque = "Hidratação profunda, tamanho família de 1L e resultado profissional direto em casa."
    insight_formato = "📸 FORMATO IDEAL: CARROSSEL ESTÁTICO OU FOTOS (Comparativo de antes e depois e foco no tamanho)."
    prompt_base_ia = f"Cinematic vertical product photography of a large 1L hair care product set, clean modern bathroom background, natural lighting, macro details, 9:16 format"
  elif any(k in t_lower for k in ["trento", "chocolate", "wafer", "doce", "snack"]):
    frase_destaque = "Crocância incomparável, recheio cremoso e sabor irresistível para o seu momento de pausa."
    insight_formato = "📸 FORMATO IDEAL: CARROSSEL ESTÁTICO OU FOTOS (Detalhes visuais e close nos benefícios funcionam melhor)."
    prompt_base_ia = f"Cinematic product photography of a slender cylindrical filled wafer stick, clean aesthetic background, realistic natural lighting, macro details, vertical format for Reels and TikTok"
  else:
    frase_destaque = "Design funcional, excelente acabamento e praticidade garantida para o seu dia a dia."
    insight_formato = "📸 FORMATO IDEAL: CARROSSEL ESTÁTICO OU FOTOS (Detalhes visuais e close nos benefícios funcionam melhor)."
    prompt_base_ia = f"Cinematic vertical product photography of {nome_puro[:30]}, clean background, professional studio lighting, 9:16 format"

  palavras = nome_puro.split()
  nome_curto = " ".join(palavras[:6]).rstrip(",-:")
  if not nome_curto:
    nome_curto = "Achado Imperdível"
    nome_puro = "Produto Shopee"

  return nome_puro, nome_curto, link_puro, frase_destaque, insight_formato, prompt_base_ia


def gerar_textos_hibridos(
    nome_curto,
    nome_longo,
    link,
    categoria,
    destaque,
    insight,
    prompt_fallback_ia,
    usar_ia_forcado=False,
):
  cerebro = carregar_cerebro()
  categorias_dict = cerebro.get("categorias_e_regras", {})
  cat_data = categorias_dict.get(categoria, {})
  
  tags_list = cat_data.get("tags_obrigatorias", ["#achadosshopee", "#shopeebrasil", "#dicas"])
  tags = " ".join(tags_list)

  if usar_ia_forcado and IA_DISPONIVEL:
    try:
      prompt = f"""Atue como o Felipe (especialista sênior em marketing de afiliados de alta conversão, dono do canal "Achados do Felipe"). 
Você escreve com um tom de voz humano, direto, natural, persuasivo e acolhedor — exatamente como um criador de conteúdo que indica um achado imperdível para amigos e seguidores. 
PROIBIDO estritamente o uso de gírias robóticas, termos genéricos vazios ou clichês forçados (como 'vibe', 'stans', 'maratona MVs' ou linguagem de IA corporativa). Foque estritamente nos benefícios práticos do produto, utilidade real, qualidade do material e na conexão com o público-alvo ou fandom se houver indício.

DADOS DO PRODUTO PARA ANÁLISE:
- Produto Completo: '{nome_longo}'
- Link de Afiliado: {link}
- Categoria / Pasta do Pinterest: {categoria}
- Tags Obrigatórias da Pasta: {tags}

GERE O PACOTE DE CONTEÚDO SEGUINDO RIGOROSAMENTE ESTAS REGRAS DE CADA REDE:

1. TIK_TITULO: Um gancho curto, magnético e instigante para o início do vídeo no TikTok/Reels (máximo 60 caracteres).
2. TIK_LEGENDA: Uma legenda dinâmica para o TikTok, chamando para a sacolinha amarela de forma natural e engajadora, finalizando com as tags obrigatórias: {tags}.
3. INSTA_TITULO: Um título forte e chamativo para a capa do Reels ou carrossel do Instagram.
4. INSTA_LEGENDA: Uma legenda rica e fluida para o Instagram. Comece gerando curiosidade ou valorizando o produto, explique por que ele vale a pena, insira uma chamada clara para o link na bio e feche com as tags: {tags}.
5. PIN_TITULO: Um título limpo, direto e altamente otimizado para SEO do Pinterest (Até 100 caracteres).
6. PIN_DESCRICAO: Uma descrição rica, técnica e completa para o Pinterest (Perto de 800 caracteres). Varre todos os detalhes do produto, modelos ou especificações compatíveis, durabilidade, utilidade prática, uma forte chamada para ação com o link e as tags: {tags}.
7. SHP_LEGENDA: Uma legenda curta, magnética e direta para o Shopee Vídeo contendo o link. Deve ser viciante e obrigatoriamente TER MENOS DE 150 CARACTERES.
8. PROMPT_IA: Um prompt visual detalhado e realista em inglês para gerar uma foto profissional estritamente relacionada ao produto analisado ('{nome_longo}'), em formato vertical 9:16 (ex: se for controle gamer, descreva um controle em setup minimalista com LED; se for cosmético, um banheiro limpo; etc.).

Responda EXATAMENTE no formato CHAVE: VALOR em cada linha (sem markdown adicional nos nomes das chaves):
TIK_TITULO: ...
TIK_LEGENDA: ...
INSTA_TITULO: ...
INSTA_LEGENDA: ...
PIN_TITULO: ...
PIN_DESCRICAO: ...
SHP_LEGENDA: ...
PROMPT_IA: ..."""

      res = client.models.generate_content(
          model="gemini-2.5-flash", contents=prompt
      ).text

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
        return "Gerado via Inteligência Artificial Humanizada 🤖", t_tit, t_leg, i_tit, i_leg, p_tit, p_desc, s_leg, p_ia if p_ia else prompt_fallback_ia
    except Exception as e:
      st.toast(f"Aviso de IA: {e}, usando motor offline robusto.")

  # --- MODO OFFLINE PROFISSIONAL ---
  tik_tit = f"Olha o que achei para facilitar: {nome_curto}"
  tik_leg = f"✨ Olha o nível desse achado! {destaque} Garanta o seu com desconto na sacolinha amarela 👇\n{link}\n\n{tags}"

  insta_tit = f"Dica de Ouro: {nome_curto}"
  insta_leg = f"✨ Sabe aquele produto que vale cada centavo?\n\nO {nome_curto} entrega exatamente o que promete. {destaque} Praticidade e qualidade que fazem toda a diferença.\n\n🔗 Corre no link da BIO para garantir o seu!\n\n{tags}"

  pin_tit = f"{nome_curto} - Detalhes, Benefícios e Onde Comprar"
  pin_desc = f"Procurando por {nome_longo}? Descubra todos os diferenciais desta excelente opção na categoria {categoria}. {destaque} Desenvolvido com foco total em qualidade, eficiência e utilidade real para o seu dia a dia. Excelente escolha para quem busca o melhor custo-benefício do mercado sem abrir mão de um desempenho impecável. Confira as avaliações, veja todos os detalhes técnicos e garanta o seu com entrega segura e preço promocional direto na plataforma oficial. Não perca tempo e adquira já o seu pelo link direto: {link}\n\nEste item foi selecionado estrategicamente em nossa curadoria para entregar a melhor experiência de compra. Explore mais novidades e recomendações exclusivas em nossa vitrine oficial.\n\nTermos relacionados e tags: {tags}"

  shp_leg = f"🔥 {nome_curto}! {destaque[:40]}... Garanta já o seu 👇\n{link} {tags}"
  if len(shp_leg) > 145:
    shp_leg = f"🔥 Achado imperdível: {nome_curto} 👇\n{link} #achados"

  prompt_ia = prompt_fallback_ia
  estrategia_final = f"Motor Híbrido Profissional | {insight}"

  return estrategia_final, tik_tit, tik_leg, insta_tit, insta_leg, pin_tit, pin_desc, shp_leg, prompt_ia


# ==========================================
# TELAS DO SISTEMA
# ==========================================

if menu == "🎬 Gerar":
  st.markdown("### 🎬 Central de Geração Estratégica")

  df_produtos = run_query(
      "SELECT id, nome, nome_curto, destaques, nicho, link_afiliado FROM"
      " produtos WHERE id NOT IN (SELECT produto_id FROM conteudos WHERE"
      " produto_id IS NOT NULL)"
  )

  if not df_produtos.empty:
    with st.form("form_gerador"):
      prod_escolhido = st.selectbox(
          "Selecione o Produto", df_produtos["nome"].tolist()
      )
      
      modo_gen = "⚡ Motor Offline Profissional"
      if IA_DISPONIVEL:
        modo_gen = st.radio(
            "Escolha o Motor:",
            ["⚡ Motor Offline Profissional", "🤖 Usar Inteligência Artificial (Gemini)"]
        )

      btn_gerar = st.form_submit_button("Gerar Pacote de Roteiros 🚀")

      if btn_gerar:
        prod_row = df_produtos.loc[
            df_produtos["nome"] == prod_escolhido
        ].iloc[0]
        prod_id = int(prod_row["id"])
        link_af = str(prod_row["link_afiliado"])
        nicho = str(prod_row["nicho"])
        n_longo = str(prod_row["nome"])
        n_curto = (
            str(prod_row["nome_curto"])
            if pd.notna(prod_row["nome_curto"])
            else n_longo[:25]
        )
        destaque = (
            str(prod_row["destaques"])
            if pd.notna(prod_row["destaques"])
            else "Qualidade garantida!"
        )

        _, _, _, _, insight_gerado, prompt_base_ia = limpar_e_extrair_shopee(n_longo)
        usar_ia = True if "Inteligência Artificial" in modo_gen else False

        with st.spinner("Processando roteiros e otimizando..."):
          (
              estrategia,
              tik_tit,
              tik_leg,
              insta_tit,
              insta_leg,
              pin_tit,
              pin_desc,
              shp_leg,
              prompt_ia,
          ) = gerar_textos_hibridos(
              n_curto,
              n_longo,
              link_af,
              nicho,
              destaque,
              insight_gerado,
              prompt_base_ia,
              usar_ia_forcado=usar_ia,
          )

        run_query(
            "INSERT INTO conteudos (produto_id, estrategia_ia, tik_titulo_video,"
            " tik_legenda, insta_titulo_video, insta_legenda, pin_titulo,"
            " pin_descricao, shp_legenda, prompt_ia, status) VALUES (?, ?, ?,"
            " ?, ?, ?, ?, ?, ?, ?, 'Pendente 🟡')",
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
        st.success("🎉 Sucesso! Roteiro gerado perfeitamente.")
        st.rerun()
  else:
    st.info("Catálogo vazio ou todos os produtos já gerados!")

elif menu == "📋 Pendentes":
  st.markdown("### 📋 Central de Pendentes (Com Cópia Nativa em Cada Bloco)")

  df_kanban = run_query(
      "SELECT c.id, p.nome_curto as produto, c.estrategia_ia, c.status,"
      " c.tik_titulo_video, c.tik_legenda, c.insta_titulo_video,"
      " c.insta_legenda, c.pin_titulo, c.pin_descricao, c.shp_legenda,"
      " c.prompt_ia FROM conteudos c LEFT JOIN produtos p ON c.produto_id ="
      " p.id WHERE c.produto_id IS NOT NULL ORDER BY c.id DESC"
  )

  if not df_kanban.empty:
    for _, row in df_kanban.iterrows():
      status_ico = (
          "✔️ Concluído" if "Concluído" in str(row["status"]) else "🟡 Pendente"
      )
      nome_p = row["produto"] if pd.notna(row["produto"]) else "Produto"

      with st.expander(f"[{status_ico}] {nome_p} (ID: {row['id']})"):
        st.info(f"💡 {row['estrategia_ia']}")

        # UTILIZANDO ST.CODE PARA GARANTIR O BOTÃO DE CÓPIA PERFEITO NO CELULAR E PC
        st.markdown("**TikTok Gancho**")
        st.code(row["tik_titulo_video"] or "", language="text")

        st.markdown("**TikTok Legenda**")
        st.code(row["tik_legenda"] or "", language="text")

        st.markdown("**Instagram Capa / Título**")
        st.code(row["insta_titulo_video"] or "", language="text")

        st.markdown("**Instagram Legenda**")
        st.code(row["insta_legenda"] or "", language="text")

        st.markdown("**Pinterest Título**")
        st.code(row["pin_titulo"] or "", language="text")

        st.markdown("**Pinterest Descrição SEO (Rica, ~800 caracteres)**")
        st.code(row["pin_descricao"] or "", language="text")

        st.markdown("**Shopee Legenda (<150 caracteres)**")
        st.code(row["shp_legenda"] or "", language="text")

        st.markdown("**🎥 Prompt de Vídeo / B-Roll (Para IA)**")
        st.code(row["prompt_ia"] or "", language="text")

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

elif menu == "📦 Catálogo":
  st.markdown("### 📦 Catálogo de Produtos e Grupos do Pinterest")
  cerebro = carregar_cerebro()
  
  categorias_dict = cerebro.get("categorias_e_regras", {})
  lista_nichos = list(categorias_dict.keys())
  lista_nichos.append("➕ Criar Nova Categoria / Grupo...")

  st.markdown("#### Cadastrar Novo Produto")
  texto_zap = st.text_area(
      "Cole a mensagem do WhatsApp ou Link Shopee:",
      placeholder="Dê uma olhada em...",
      key="input_zap_cat"
  )
  
  nicho_escolhido = st.selectbox("Pasta / Grupo do Pinterest:", lista_nichos, key="select_nicho_cat")

  nova_categoria = ""
  if nicho_escolhido == "➕ Criar Nova Categoria / Grupo...":
    nova_categoria = st.text_input("Digite o nome exato da nova pasta (ex: Eletrônicos, K-Pop, Doces, etc.):", key="input_nova_cat")

  if st.button("Cadastrar Produto e Salvar Grupo 🚀", key="btn_salvar_cat"):
    if not texto_zap.strip():
      st.error("Por favor, cole o link ou texto do produto antes de salvar.")
    else:
      categoria_final = nicho_escolhido
      if nicho_escolhido == "➕ Criar Nova Categoria / Grupo...":
        if nova_categoria.strip():
          categoria_final = nova_categoria.strip()
        else:
          categoria_final = "Geral"

      if categoria_final not in categorias_dict and categoria_final != "➕ Criar Nova Categoria / Grupo...":
        cerebro.setdefault("categorias_e_regras", {})[categoria_final] = {
            "tags_obrigatorias": ["#achadosshopee", "#shopeebrasil", f"#{categoria_final.lower().replace(' ', '')}"],
        }
        salvar_cerebro(cerebro)

      nome_puro, nome_curto, link_limpo, frase_destaque, _, _ = (
          limpar_e_extrair_shopee(texto_zap)
      )

      run_query(
          "INSERT INTO produtos (nome, nome_curto, destaques, nicho,"
          " link_afiliado) VALUES (?, ?, ?, ?, ?)",
          (nome_puro, nome_curto, frase_destaque, categoria_final, link_limpo),
          fetch=False,
      )
      st.success(f"Sucesso! Produto cadastrado na pasta '{categoria_final}' de primeira!")
      st.rerun()

  st.markdown("---")
  st.markdown("#### Produtos Cadastrados")
  df_p = run_query(
      "SELECT id, nome_curto, destaques, nicho FROM produtos ORDER BY id DESC"
  )
  if not df_p.empty:
    for _, row in df_p.iterrows():
      c1, c2 = st.columns([4, 1])
      with c1:
        st.markdown(
            f"**📦 {row['nome_curto']}** `[Pasta: {row['nicho']}]`"
        )
        st.caption(f"💡 {row['destaques']}")
      with c2:
        if st.button("Excluir 🗑️", key=f"del_prod_{row['id']}"):
          run_query(
              "DELETE FROM produtos WHERE id = ?", (row["id"],), fetch=False
          )
          st.rerun()

elif menu == "🧠 Treinamento":
  st.markdown("### 🧠 Treinamento e Ajustes do Cérebro V3")
  st.json(carregar_cerebro())

elif menu == "🧬 Auto-Evolução":
  st.markdown("### 🧬 Painel de Auto-Evolução")
  st.info("Módulo ativo: Sincronização de tags e grupos.")

elif menu == "📊 Dashboard":
  st.markdown("### 📊 Dashboard Consolidado")
  total_prod = len(run_query("SELECT id FROM produtos", fetch=True))
  total_cont = len(run_query("SELECT id FROM conteudos", fetch=True))
  col1, col2 = st.columns(2)
  with col1:
    st.metric("Total de Produtos", total_prod)
  with col2:
    st.metric("Roteiros Gerados", total_cont)
