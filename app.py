# -*- coding: utf-8 -*-
"""
Achados do Felipe - Dashboard Oficial (app.py)
Autor: Felipe de Oliveira Gonçalves (@achadosfelipe01)
"""

import json
import os
import random
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
    '<p class="app-subtitle">Sua Máquina de Conteúdo e Automação Offline</p>',
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
            "versao": "6.0",
            "objetivo": "Matriz de inteligência",
        },
        "categorias_e_regras": {
            "Geral (Coringa / Utilidades)": {
                "foco_atributos": ["praticidade", "custo-benefício"],
                "padrao_seo_pinterest": {
                    "estrutura_titulo": (
                        "{nome_curto} - Achado Útil para o Dia a Dia"
                    ),
                    "gatilhos_descricao": (
                        "Resolva seus problemas cotidianos com facilidade."
                        " Conheça o {nome_longo}. {link}"
                    ),
                },
                "tags_obrigatorias": ["#achadosshopee", "#utilidades"],
            }
        },
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


IA_DISPONIVEL = False
client = None
try:
  from google import genai

  api_key = st.secrets["GEMINI_API_KEY"]
  client = genai.Client(api_key=api_key)
  IA_DISPONIVEL = True
except Exception:
  pass


# --- EXTRATOR DE ATRIBUTOS E INSIGHT DE FORMATO ---
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

  atributos = []
  t_lower = nome_puro.lower()

  bat_match = re.search(r"(\d+)\s*h", t_lower)
  if bat_match:
    atributos.append(f"bateria de {bat_match.group(1)}h")
  elif "bateria" in t_lower:
    atributos.append("bateria de longa duração")

  if "ip" in t_lower or "água" in t_lower:
    atributos.append("proteção total contra água")
  if "bluetooth" in t_lower or "sem fio" in t_lower:
    atributos.append("conexão sem fio de alta estabilidade")
  if "automático" in t_lower or "automatico" in t_lower:
    atributos.append("sistema de acionamento automático")
  if "vento" in t_lower or "reforçado" in t_lower:
    atributos.append("estrutura reforçada contra ventos fortes")

  frase_destaque = "Design moderno, alta durabilidade e acabamento premium."
  if atributos:
    frase_destaque = (
        f"Ele conta com {' e '.join(atributos[:2])}, garantindo máxima"
        " eficiência no uso diário!"
    )

  if any(
      k in t_lower
      for k in [
          "caixa",
          "som",
          "fone",
          "smart",
          "automático",
          "robo",
          "aspirador",
          "kit",
      ]
  ):
    insight_formato = "🎬 FORMATO IDEAL: VÍDEO DINÂMICO (Demonstração prática em funcionamento gera 3x mais cliques)."
  else:
    insight_formato = "📸 FORMATO IDEAL: CARROSSEL ESTÁTICO OU FOTOS (Detalhes estéticos e comparativos funcionam melhor)."

  palavras = nome_puro.split()
  nome_curto = " ".join(palavras[:5]).rstrip(",-:")
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
  cat_data = categorias_dict.get(
      categoria,
      categorias_dict.get(
          "Geral (Coringa / Utilidades)", list(categorias_dict.values())[0]
      ),
  )

  tags_list = cat_data.get(
      "tags_obrigatorias", ["#achadosshopee", "#shopeebrasil"]
  )
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
SHP_LEGENDA: Legenda curta para Shopee Vídeo com link (Menos de 150 caracteres)
PROMPT_IA: Prompt detalhado em inglês para gerar imagem/vídeo no Midjourney ou IA de vídeo"""

      res = client.models.generate_content(
          model="gemini-2.5-flash", contents=prompt
      ).text

      t_tit, t_leg, i_tit, i_leg, p_tit, p_desc, s_leg, p_ia = (
          "",
          "",
          "",
          "",
          "",
          "",
          "",
          "",
      )
      for l in res.split("\n"):
        if ":" in l:
          ch, val = l.split(":", 1)
          ch, val = ch.strip().upper(), val.strip()
          if "TIK_TITULO" in ch:
            t_tit = val
          elif "TIK_LEGENDA" in ch:
            t_leg = val
          elif "INSTA_TITULO" in ch:
            i_tit = val
          elif "INSTA_LEGENDA" in ch:
            i_leg = val
          elif "PIN_TITULO" in ch:
            p_tit = val
          elif "PIN_DESCRICAO" in ch:
            p_desc = val
          elif "SHP_LEGENDA" in ch:
            s_leg = val
          elif "PROMPT_IA" in ch:
            p_ia = val

      if t_tit and p_desc:
        return (
            "Gerado via IA Híbrida 🤖",
            t_tit,
            t_leg,
            i_tit,
            i_leg,
            p_tit,
            p_desc,
            s_leg,
            p_ia,
        )
    except Exception as e:
      st.toast(f"Aviso de IA: {e}")

  # --- MODO OFFLINE PROFISSIONAL E ROBUSTO ---
  tik_tit = f"Cansado de passar perrengue? Olha o que esse {nome_curto} faz:"
  tik_leg = f"😱 Salvação pura para o dia a dia! {destaque} Garanta o seu com desconto na sacolinha amarela 👇\n{link}\n\n{tags}"

  insta_tit = f"O Indispensável: {nome_curto}"
  insta_leg = f"🛡️ Sabe aquele problema corriqueiro que irrita todo mundo?\n\nO {nome_curto} resolve isso em segundos. {destaque} É o tipo de investimento prático que faz a gente se perguntar por que não comprou antes.\n\n🔗 Corre no link da BIO para garantir o seu com segurança!\n\n{tags}"

  # Padrão SEO Pinterest profissional (Gera texto longo e rico perto de 800 caracteres)
  seo_rule = cat_data.get("padrao_seo_pinterest", {})
  pin_tit = (
      seo_rule.get(
          "estrutura_titulo",
          "{nome_curto} - Review Completo e Onde Comprar",
      )
      .replace("{nome_curto}", nome_curto)
      .replace("{nome_longo}", nome_longo)
  )

  base_desc_modelo = seo_rule.get(
      "gatilhos_descricao",
      "Procurando por {nome_longo}? Conheça todas as vantagens e diferenciais"
      " deste excelente produto da categoria {categoria}. {destaque} Desenvolvido"
      " para proporcionar máxima eficiência, durabilidade e praticidade no seu"
      " dia a dia. Excelente opção para quem preza por qualidade superior e"
      " preço justo. Confira avaliações, veja todos os detalhes técnicos e"
      " garanta o seu com entrega segura e desconto exclusivo direto na"
      " plataforma oficial. Não perca tempo e adquira já o seu pelo link"
      " direto: {link}",
  )

  pin_desc = (
      base_desc_modelo.replace("{nome_longo}", nome_longo)
      .replace("{nome_curto}", nome_curto)
      .replace("{categoria}", categoria)
      .replace("{destaque}", destaque)
      .replace("{link}", link)
  )
  # Expande para garantir robustez de SEO no Pinterest (chegando próximo a 700-800 caracteres)
  pin_desc += f"\n\nEste item foi selecionado estrategicamente em nossa curadoria para entregar a melhor experiência de compra e utilidade real. Explore mais dicas, novidades e recomendações exclusivas em nossa vitrine oficial.\n\nTermos relacionados e tags: {tags}"

  # Shopee estrito a menos de 150 caracteres
  shp_leg = f"Achado imperdível! {nome_curto}. Confira na vitrine oficial 👇\n{link} {tags}"
  if len(shp_leg) > 145:
    shp_leg = f"Imperdível! {nome_curto} 👇\n{link} #achados"

  # Prompt de Vídeo / B-Roll profissional para IA
  prompt_ia = f"Cinematic UGC video showcasing {nome_curto} in a modern clean environment, realistic lighting, macro details, smooth camera movement, 4k resolution, vertical format for Reels and TikTok"

  estrategia_final = f"Motor Offline Profissional | {insight}"

  return (
      estrategia_final,
      tik_tit,
      tik_leg,
      insta_tit,
      insta_leg,
      pin_tit,
      pin_desc,
      shp_leg,
      prompt_ia,
  )


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

      modo_geracao = st.radio(
          "Escolha o Motor de Geração:",
          [
              "⚡ Motor Offline Profissional (Garantido e Completo)",
              "🤖 Tentar Forçar com Inteligência Artificial (Gemini)",
          ],
          index=0,
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
        usar_ia = True if "Inteligência Artificial" in modo_geracao else False

        with st.spinner("Processando roteiros e otimizando o SEO..."):
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
        st.success("🎉 Sucesso! Roteiro profissional gerado.")
        st.rerun()
  else:
    st.info("Catálogo vazio ou todos os produtos já gerados!")

elif menu == "📋 Pendentes":
  st.markdown("### 📋 Central de Pendentes")

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
        # Exibe o Insight de Formato (Vídeo Dinâmico vs Carrossel) no topo
        st.info(f"💡 {row['estrategia_ia']}")

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
            "Shopee Legenda (Curta, <150 caracteres)",
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
  st.markdown("### 📦 Catálogo de Produtos")
  cerebro = carregar_cerebro()
  categorias_dict = cerebro.get("categorias_e_regras", {})
  lista_nichos = list(categorias_dict.keys())
  lista_nichos.append("➕ Criar Nova Categoria...")

  with st.form("form_cat_manual"):
    texto_zap = st.text_area(
        "Cole a mensagem do WhatsApp ou Link Shopee:",
        placeholder="Dê uma olhada em...",
    )
    nicho_escolhido = st.selectbox("Categoria Principal:", lista_nichos)

    nova_categoria = ""
    if nicho_escolhido == "➕ Criar Nova Categoria...":
      nova_categoria = st.text_input("Digite o nome da nova categoria:")

    enviar = st.form_submit_button("Analisar e Salvar no Catálogo 🚀")

    if enviar and texto_zap:
      categoria_final = (
          nova_categoria.strip()
          if nova_categoria.strip()
          else nicho_escolhido
      )

      if nova_categoria.strip() and nova_categoria.strip() not in categorias_dict:
        cerebro.setdefault("categorias_e_regras", {})[
            nova_categoria.strip()
        ] = {
            "foco_atributos": ["utilidade geral", "custo-benefício"],
            "padrao_seo_pinterest": {
                "estrutura_titulo": "{nome_curto} - Achado Imperdível",
                "gatilhos_descricao": (
                    "Encontre os melhores produtos com excelente preço e"
                    " utilidade garantida para o dia a dia. {link}"
                ),
            },
            "tags_obrigatorias": ["#achadosshopee", "#shopeebrasil"],
        }
        salvar_cerebro(cerebro)

      nome_puro, nome_curto, link_limpo, frase_destaque, _ = (
          limpar_e_extrair_shopee(texto_zap)
      )

      run_query(
          "INSERT INTO produtos (nome, nome_curto, destaques, nicho,"
          " link_afiliado) VALUES (?, ?, ?, ?, ?)",
          (nome_puro, nome_curto, frase_destaque, categoria_final, link_limpo),
          fetch=False,
      )
      st.success(f"Cadastrado com sucesso na categoria: {categoria_final}!")
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
            f"**📦 {row['nome_curto']}** `[{row['nicho']}]`"
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
  st.info("Módulo ativo: Monitoramento de conversão e SEO.")

elif menu == "📊 Dashboard":
  st.markdown("### 📊 Dashboard Consolidado")
  total_prod = len(run_query("SELECT id FROM produtos", fetch=True))
  total_cont = len(run_query("SELECT id FROM conteudos", fetch=True))
  col1, col2 = st.columns(2)
  with col1:
    st.metric("Total de Produtos", total_prod)
  with col2:
    st.metric("Roteiros Gerados", total_cont)
