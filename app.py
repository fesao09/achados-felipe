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
            "versao": "11.0",
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


# --- EXTRATOR DE ATRIBUTOS E HÍBRIDO ---
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

  if any(k in t_lower for k in ["shampoo", "condicionador", "cabelo", "infantil", "infante", "banho"]):
    frase_destaque = "Fórmula dermatologicamente testada, cheirinho duradouro e cuidado delicado para o dia a dia."
  elif any(k in t_lower for k in ["creatina", "whey", "suplemento", "proteina", "treino"]):
    frase_destaque = "Alta pureza e concentração ideal para turbinar seus resultados diários."
  elif any(k in t_lower for k in ["creamy", "cerave", "principia", "sérum", "protetor solar", "pele"]):
    frase_destaque = "Ativos de alta performance para uma rotina de cuidados impecável e resultados visíveis."
  elif any(k in t_lower for k in ["omo", "surf", "coala", "limpeza", "faxina", "desinfetante"]):
    frase_destaque = "Alto rendimento e poder de limpeza superior para deixar tudo limpo e perfumado."
  else:
    frase_destaque = "Design funcional, excelente acabamento e praticidade garantida para o seu dia a dia."

  if any(k in t_lower for k in ["caixa", "som", "fone", "smart", "automático", "robo", "aspirador", "kit"]):
    insight_formato = "🎬 FORMATO IDEAL: VÍDEO DINÂMICO (Demonstração prática em funcionamento gera muito mais cliques)."
  else:
    insight_formato = "📸 FORMATO IDEAL: CARROSSEL ESTÁTICO OU FOTOS (Detalhes visuais e close nos benefícios funcionam melhor)."

  palavras = nome_puro.split()
  nome_curto = " ".join(palavras[:6]).rstrip(",-:")
  if not nome_curto:
    nome_curto = "Achado Imperdível"
    nome_puro = "Produto Shopee"

  return nome_puro, nome_curto, link_puro, frase_destaque, insight_formato


def gerar_textos_hibridos(
    nome_curto,
    nome_longo,
    link,
    categoria,
    destaque,
    insight,
    usar_ia_forcado=False,
):
  cerebro = carregar_cerebro()
  categorias_dict = cerebro.get("categorias_e_regras", {})
  cat_data = categorias_dict.get(categoria, {})
  
  tags_list = cat_data.get("tags_obrigatorias", ["#achadosshopee", "#shopeebrasil", "#dicas"])
  tags = " ".join(tags_list)

  if usar_ia_forcado and IA_DISPONIVEL:
    try:
      prompt = f"""Gere textos altamente persuasivos para afiliado baseados nas especificações reais, com português natural, fluído e focado em conversão.
Produto Completo: '{nome_longo}'
Link: {link}
Categoria: {categoria}

Responda EXATAMENTE neste formato de chaves:
TIK_TITULO: Gancho curto e magnético para TikTok
TIK_LEGENDA: Legenda para TikTok com sacolinha e tags ({tags})
INSTA_TITULO: Título chamativo para Capa do Reels / Carrossel
INSTA_LEGENDA: Legenda rica e persuasiva para Instagram com link na bio e tags ({tags})
PIN_TITULO: Título rico em SEO para Pinterest (Até 100 caracteres)
PIN_DESCRICAO: Descrição rica, técnica e completa para Pinterest usando todas as especificações do produto, com chamada para ação, links e tags (Perto de 800 caracteres) ({tags})
SHP_LEGENDA: Legenda curta e magnética para Shopee Vídeo com link (Menos de 150 caracteres)
PROMPT_IA: Prompt detalhado em inglês para gerar imagem/vídeo no Midjourney ou IA de vídeo"""

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
        return "Gerado via Inteligência Artificial 🤖", t_tit, t_leg, i_tit, i_leg, p_tit, p_desc, s_leg, p_ia
    except Exception as e:
      st.toast(f"Aviso de IA: {e}, usando motor offline robusto.")

  # --- MODO OFFLINE PROFISSIONAL ---
  tik_tit = f"Olha o que achei para facilitar: {nome_curto}"
  tik_leg = f"✨ Olha o nível desse achado! {destaque} Garanta o seu com desconto na sacolinha amarela 👇\n{link}\n\n{tags}"

  insta_tit = f"Dica de Ouro: {nome_curto}"
  insta_leg = f"✨ Sabe aquele produto que vale cada centavo?\n\nO {nome_curto} entrega exatamente o que promete. {destaque} Praticidade e qualidade que fazem toda a diferença.\n\n🔗 Corre no link da BIO para garantir o seu!\n\n{tags}"

  pin_tit = f"{nome_curto} - Detalhes, Benefícios e Onde Comprar"
  pin_desc = f"Procurando por {nome_longo}? Descubra todos os diferenciais desta excelente opção na categoria {categoria}. {destaque} Desenvolvido com foco total em qualidade, eficiência e utilidade real para o seu dia a dia. Excelente escolha para quem busca o melhor custo-benefício do mercado sem abrir mão de um desempenho impecável. Confira as avaliações, veja todos os detalhes técnicos e garanta o seu com entrega segura e preço promocional direto na plataforma oficial. Não perca tempo e adquira já o seu pelo link direto: {link}\n\nEste item foi selecionado estrategicamente em nossa curadoria para entregar a melhor experiência de compra. Explore mais novidades e recomendações exclusivas em nossa vitrine oficial.\n\nTermos relacionados e tags: {tags}"

  # Shopee otimizado, magnético e estrito (<150 caracteres)
  shp_leg = f"🔥 {nome_curto}! {destaque[:40]}... Garanta já o seu 👇\n{link} {tags}"
  if len(shp_leg) > 145:
    shp_leg = f"🔥 Achado imperdível: {nome_curto} 👇\n{link} #achados"

  prompt_ia = f"Cinematic UGC video showcasing {nome_curto}, clean aesthetic background, realistic natural lighting, macro details, smooth camera movement, vertical format for Reels and TikTok"

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
      
      # Opção de usar IA caso esteja configurada
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

        _, _, _, _, insight_gerado = limpar_e_extrair_shopee(n_longo)
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
  st.markdown("### 📋 Central de Pendentes (Com Cópia Rápida 📋)")

  df_kanban = run_query(
      "SELECT c.id, p.nome_curto as produto, c.estrategia_ia, c.status,"
      " c.tik_titulo_video, c.tik_legenda, c.insta_titulo_video,"
      " c.insta_legenda, c.pin_titulo, c.pin_descricao, c.shp_legenda,"
      " c.prompt_ia FROM conteudos c LEFT JOIN produtos p ON c.produto_id ="
      " p.id WHERE p.nome IS NOT NULL ORDER BY c.id DESC"
  )

  if not df_kanban.empty:
    for _, row in df_kanban.iterrows():
      status_ico = (
          "✔️ Concluído" if "Concluído" in str(row["status"]) else "🟡 Pendente"
      )
      nome_p = row["produto"] if pd.notna(row["produto"]) else "Produto"

      with st.expander(f"[{status_ico}] {nome_p}"):
        st.info(f"💡 {row['estrategia_ia']}")

        # CAMPOS COM CÓPIA RÁPIDA INTEGRADA VIA PARÂMETRO DO STREAMLIT
        st.text_input(
            "TikTok Gancho",
            value=row["tik_titulo_video"] or "",
            key=f"tt_{row['id']}",
        )
        st.text_area(
            "TikTok Legenda",
            value=row["tik_legenda"] or "",
            height=90,
            key=f"tl_{row['id']}",
        )
        st.text_input(
            "Insta Capa / Carrossel",
            value=row["insta_titulo_video"] or "",
            key=f"it_{row['id']}",
        )
        st.text_area(
            "Insta Legenda",
            value=row["insta_legenda"] or "",
            height=150,
            key=f"il_{row['id']}",
        )
        st.text_input(
            "Pinterest Título",
            value=row["pin_titulo"] or "",
            key=f"pt_{row['id']}",
        )
        st.text_area(
            "Pinterest Descrição SEO (Rica, ~800 caracteres)",
            value=row["pin_descricao"] or "",
            height=180,
            key=f"pd_{row['id']}",
        )
        st.text_area(
            "Shopee Legenda (<150 caracteres)",
            value=row["shp_legenda"] or "",
            height=60,
            key=f"sl_{row['id']}",
        )
        st.text_area(
            "🎥 Prompt de Vídeo / B-Roll (Para IA de Geração)",
            value=row["prompt_ia"] or "",
            height=80,
            key=f"pi_{row['id']}",
        )

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

  with st.form("form_cat_manual"):
    texto_zap = st.text_area(
        "Cole a mensagem do WhatsApp ou Link Shopee:",
        placeholder="Dê uma olhada em...",
    )
    
    nicho_escolhido = st.selectbox("Pasta / Grupo do Pinterest:", lista_nichos)

    nova_categoria = ""
    if nicho_escolhido == "➕ Criar Nova Categoria / Grupo...":
      nova_categoria = st.text_input("Digite o nome limpo e exato da pasta (ex: Jogos, K-Pop, etc.):")

    enviar = st.form_submit_button("Analisar e Salvar no Catálogo 🚀")

    if enviar and texto_zap:
      categoria_final = (
          nova_categoria.strip()
          if nova_categoria.strip()
          else nicho_escolhido
      )

      # Persiste a nova categoria criada no arquivo cerebro_v3.json instantaneamente
      if nova_categoria.strip():
        cat_limpa = nova_categoria.strip()
        if cat_limpa not in categorias_dict:
          cerebro.setdefault("categorias_e_regras", {})[cat_limpa] = {
              "tags_obrigatorias": ["#achadosshopee", "#shopeebrasil", f"#{cat_limpa.lower().replace(' ', '')}"],
          }
          salvar_cerebro(cerebro)
          categoria_final = cat_limpa

      nome_puro, nome_curto, link_limpo, frase_destaque, _ = (
          limpar_e_extrair_shopee(texto_zap)
      )

      run_query(
          "INSERT INTO produtos (nome, nome_curto, destaques, nicho,"
          " link_afiliado) VALUES (?, ?, ?, ?, ?)",
          (nome_puro, nome_curto, frase_destaque, categoria_final, link_limpo),
          fetch=False,
      )
      st.success(f"Sucesso! Produto cadastrado e grupo '{categoria_final}' salvo no cérebro com sucesso!")
      st.rerun()

  st.markdown("---")
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
