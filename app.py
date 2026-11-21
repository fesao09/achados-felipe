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

try:
  import requests
except Exception:
  requests = None

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
            "versao": "21.0",
            "objetivo": "Matriz de inteligência de conteúdo multiplataforma",
        },
        "categorias_e_regras": {
            "Utilidades para Casa": {
                "tags_obrigatorias": ["#achados", "#utilidadesdomesticas", "#casa"],
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


# --- DETECTOR DE PLATAFORMA POR LINK ---
def detectar_plataforma(url):
  u = (url or "").lower()
  if "tiktok.com" in u:
    return "TikTok Shop"
  if "shopee.com" in u:
    return "Shopee"
  if "mercadolivre.com" in u or "meli.la" in u:
    return "Mercado Livre"
  if "amazon.com" in u or "amzn.to" in u:
    return "Amazon"
  return "Loja Oficial"


# --- LEITURA RÁPIDA DE TÍTULO VIA LINK ---
def tentar_extrair_titulo_por_url(url):
  if not url or not url.startswith("http") or requests is None:
    return ""
  try:
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (iPhone; CPU iPhone OS 17_0 like Mac OS X) "
            "AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Mobile/15E148 Safari/604.1"
        )
    }
    resp = requests.get(url, headers=headers, timeout=5, allow_redirects=True)
    if resp.status_code == 200 and resp.text:
      html = resp.text
      og_match = re.search(
          r'<meta[^>]+property=["\']og:title["\'][^>]+content=["\']([^"\']+)["\']',
          html,
          flags=re.IGNORECASE,
      )
      if og_match:
        titulo = og_match.group(1).strip()
        if titulo and titulo.lower() not in ["tiktok", "make your day", "shopee brasil"]:
          return titulo

      title_match = re.search(
          r"<title[^>]*>([^<]+)</title>", html, flags=re.IGNORECASE
      )
      if title_match:
        titulo = title_match.group(1).strip()
        titulo = re.sub(r"\s*\|\s*TikTok.*$", "", titulo, flags=re.IGNORECASE)
        if titulo and titulo.lower() not in ["tiktok", "make your day"]:
          return titulo
  except Exception:
    pass
  return ""


# --- EXTRATOR DE ATRIBUTOS E HÍBRIDO INTELIGENTE ---
def limpar_e_extrair_shopee(texto_bruto, titulo_manual=""):
  link_puro = ""
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

  if titulo_manual and titulo_manual.strip():
    nome_puro = titulo_manual.strip()
  elif (not nome_puro or nome_puro.startswith("http")) and link_puro:
    titulo_auto = tentar_extrair_titulo_por_url(link_puro)
    if titulo_auto:
      nome_puro = titulo_auto
    else:
      nome_puro = "Achado do Link (Ajuste o título se quiser)"

  if not link_puro:
    link_puro = texto_bruto.strip()

  t_lower = nome_puro.lower()

  # DETECÇÃO DE NICHO, PROMPT VIRAL E DIRETRIZ ANTI-VIOLAÇÃO
  if any(k in t_lower for k in ["tênis", "tenis", "fila", "sneaker", "calçado", "calcado", "camiseta", "camisa", "calça", "calca", "jaqueta", "moletom", "vestuário", "vestuario", "roupa", "short"]):
    frase_destaque = "Leveza e caimento prático para encarar a rotina, treino ou caminhada sem gastar uma fortuna."
    insight_formato = "🎬 FORMATO IDEAL: VÍDEO VIRAL DE EXPERIMENTAÇÃO (Uso real em movimento, mantendo 100% da aparência original)."
    prompt_base_ia = (
        f"Vertical 9:16 UGC video for TikTok showing a person wearing the exact {nome_puro[:45]} from the reference "
        "while walking naturally on a clean sidewalk and stepping into daily routine on a bright morning. "
        "Keep the exact product design, colors, stitching, logos, and shape identical with zero alteration. "
        "Smooth natural camera tracking, realistic daylight, authentic everyday lifestyle vibe, crisp focus, no misleading claims."
    )
    aviso_seguranca = "Vestuário/Calçado: focar em experimentação real no dia a dia, conforto na rotina e fidelidade visual do item, sem promessas médicas."
  elif any(k in t_lower for k in ["principia", "sérum", "serum", "ácido", "acido", "niacinamida", "retinol", "protetor solar", "pele", "skincare", "creamy", "cerave"]):
    frase_destaque = "Textura leve que absorve rápido e encaixa fácil na rotina diária de cuidados com a pele."
    insight_formato = "📸 FORMATO IDEAL: VÍDEO DE ROTINA OU CARROSSEL (Textura e aplicação real, sem promessas clínicas)."
    prompt_base_ia = (
        f"Vertical 9:16 UGC product video of {nome_puro[:45]} on a clean minimalist bathroom counter, soft natural morning light, "
        "authentic texture close-up, calm daily skincare routine aesthetic, keeping packaging identical, no medical claims."
    )
    aviso_seguranca = "Skincare/Dermocosmético: PROIBIDO prometer cura, tratamento de acne/manchas ou efeito clínico garantido para evitar violação no TikTok."
  elif any(k in t_lower for k in ["controle", "xbox", "playstation", "joystick", "gamer", "console"]):
    frase_destaque = "Pegada firme, resposta precisa nos comandos e zero dor de cabeça com conexão no dia a dia."
    insight_formato = "🎬 FORMATO IDEAL: VÍDEO DEMONSTRATIVO (Unboxing rápido, pegada e botões em uso)."
    prompt_base_ia = (
        f"Vertical 9:16 UGC video showing hands holding and testing {nome_puro[:45]} in a clean gaming setup, "
        "natural ambient lighting, crisp close-up of buttons and matte finish, keeping exact hardware appearance unchanged."
    )
    aviso_seguranca = "Games/Eletrônicos: destacar ergonomia, compatibilidade e uso real sem exageros."
  elif any(k in t_lower for k in ["shampoo", "condicionador", "cabelo", "infantil", "salon line", "litro"]):
    frase_destaque = "Embalagem gigante de 1 litro que rende meses na rotina e evita ficar gastando caro toda semana."
    insight_formato = "🎬 FORMATO IDEAL: VÍDEO DE ECONOMIA E ESCALA (Mostrar o tamanho real dos frascos de 1L)."
    prompt_base_ia = (
        f"Vertical 9:16 UGC video showing {nome_puro[:45]} in a bright modern bathroom, natural lighting, "
        "emphasizing the large 1L bottle size and clean packaging identical to reference, authentic everyday aesthetic."
    )
    aviso_seguranca = "Cabelos: destacar rendimento, tamanho e cuidado diário sem promessas milagrosas."
  elif any(k in t_lower for k in ["trento", "chocolate", "wafer", "doce", "snack"]):
    frase_destaque = "Crocância na medida certa e recheio cremoso para salvar a pausa do café sem pesar no bolso."
    insight_formato = "📸 FORMATO IDEAL: VÍDEO CURTO DE PAUSA (Close na textura e consumo real)."
    prompt_base_ia = (
        f"Vertical 9:16 close-up lifestyle video of {nome_puro[:45]} next to a cup of coffee on a clean table, "
        "soft natural side lighting, crisp macro texture, keeping exact packaging design unchanged."
    )
    aviso_seguranca = "Alimentos: foco em sabor, crocância e momento de consumo."
  else:
    frase_destaque = "Solução prática que resolve um perrengue real do dia a dia com ótimo custo-benefício."
    insight_formato = "🎬 FORMATO IDEAL: VÍDEO DE DEMONSTRAÇÃO PRÁTICA (Mostrar o produto resolvendo o problema na prática)."
    prompt_base_ia = (
        f"Vertical 9:16 UGC lifestyle video showing {nome_puro[:45]} in real everyday use, "
        "natural daylight, clean home environment, keeping exact product appearance unchanged, authentic handheld camera feel."
    )
    aviso_seguranca = "Geral: copy direta, sem clichês vazios e fiel ao que o produto realmente entrega."

  palavras = nome_puro.split()
  nome_curto = " ".join(palavras[:6]).rstrip(",-:")
  if not nome_curto:
    nome_curto = "Achado Imperdível"
    nome_puro = "Produto"

  return (
      nome_puro,
      nome_curto,
      link_puro,
      frase_destaque,
      insight_formato,
      prompt_base_ia,
      aviso_seguranca,
  )


def gerar_textos_hibridos(
    nome_curto,
    nome_longo,
    link,
    categoria,
    destaque,
    insight,
    prompt_fallback_ia,
    aviso_seguranca="",
    usar_ia_forcado=False,
):
  plataforma = detectar_plataforma(link)
  cerebro = carregar_cerebro()
  categorias_dict = cerebro.get("categorias_e_regras", {})
  cat_data = categorias_dict.get(categoria, {})

  raw_tags = cat_data.get("tags_obrigatorias", [])
  # Filtra tags da Shopee caso o link seja do TikTok Shop (e vice-versa)
  if plataforma == "TikTok Shop":
    tags_filtradas = [
        t for t in raw_tags if "shopee" not in t.lower()
    ]
    base_tags = ["#achadostiktok", "#tiktokshopbrasil", "#achados"]
    cta_tiktok = "na sacolinha laranja aqui embaixo"
    cta_insta = "no link da bio (direto no TikTok Shop)"
    cta_curto = "Garanta o seu no link do TikTok Shop 👇"
  elif plataforma == "Shopee":
    tags_filtradas = [
        t for t in raw_tags if "tiktok" not in t.lower()
    ]
    base_tags = ["#achadosshopee", "#shopeebrasil", "#achados"]
    cta_tiktok = "no link da bio / sacolinha"
    cta_insta = "no link da bio (oferta na Shopee)"
    cta_curto = "Garanta o seu na Shopee 👇"
  else:
    tags_filtradas = raw_tags
    base_tags = ["#achados", "#dicasdecompras", "#custobeneficio"]
    cta_tiktok = "no link da bio / sacolinha"
    cta_insta = "no link da bio"
    cta_curto = "Confira a oferta no link 👇"

  # Combina tags limpas sem duplicar
  tags_finais = []
  for t in base_tags + tags_filtradas:
    if t.lower() not in [x.lower() for x in tags_finais]:
      tags_finais.append(t)
  tags = " ".join(tags_finais[:5])

  if usar_ia_forcado and IA_DISPONIVEL:
    try:
      prompt = f"""Você é o estrategista sênior de conteúdo do canal "Achados do Felipe" (Felipe de Oliveira Gonçalves).
Seu estilo de escrita é idêntico ao de um criador experiente conversando direto com o seguidor: afiado, direto ao ponto, focado em **economia real, quebra de objeção e utilidade prática**.

PROIBIÇÕES ABSOLUTAS (NUNCA FAÇA ISSO):
1. NUNCA mencione "Shopee" se a PLATAFORMA DE ORIGEM for "{plataforma}" (se for TikTok Shop, trate 100% como achado do TikTok Shop / sacolinha laranja; só fale Shopee se a plataforma for Shopee).
2. PROIBIDO usar frases bobas ou clichês robóticos como: "Olha o que achei para facilitar", "Sabe aquele produto que vale cada centavo?", "Design funcional e excelente acabamento", "Produto imperdível", "Vibe", "Stans".
3. ANTI-VIOLAÇÃO TIKTOK: Nunca faça promessas médicas, de cura, tratamento clínico ou resultados garantidos/milagrosos. Respeite: {aviso_seguranca}

DADOS DO PRODUTO:
- Produto: '{nome_longo}'
- Plataforma de Origem: {plataforma}
- Link: {link}
- Categoria / Pasta: {categoria}
- Tags permitidas: {tags}

COMO ESTRUTURAR A COPY (PADRÃO VIRAL DE ALTA RETENÇÃO):
- **Gancho (0-3s):** Comece atacando uma dor real do bolso ou da rotina (ex: pagar caro à toa, desconforto no dia a dia, falta de rendimento) ou mostrando uma oportunidade real de custo-benefício.
- **Corpo:** Explique em linguagem falada e natural por que esse item específico resolve o problema (tamanho, conforto, praticidade, durabilidade) sem parecer texto de catálogo.
- **CTA:** Chamada clara e natural para {cta_tiktok} (no TikTok) ou {cta_insta} (no Instagram).

GERE OS 8 CAMPOS ABAIXO (USE QUEBRAS DE LINHA SIMPLES DENTRO DOS TEXTOS SE PRECISAR, SEM MARKDOWN NAS CHAVES):
1. TIK_TITULO: Gancho viral curto para abrir o vídeo no TikTok/Reels (máximo 55 caracteres, direto e provocativo).
2. TIK_LEGENDA: Legenda estilo criador real para TikTok, reforçando o gancho, explicando o benefício prático, chamando para {cta_tiktok} e fechando com: {tags}.
3. INSTA_TITULO: Headline forte para capa de Reels ou primeiro card de carrossel no Instagram.
4. INSTA_LEGENDA: Legenda persuasiva e fluida para Instagram (quebra de objeção + uso real + chamada para {cta_insta}) + {tags}.
5. PIN_TITULO: Título limpo e forte para SEO no Pinterest (até 100 caracteres, sem emojis em excesso).
6. PIN_DESCRICAO: Descrição completa para SEO no Pinterest (700 a 850 caracteres), detalhando especificações, situações de uso, custo-benefício, link direto {link} e tags: {tags}.
7. SHP_LEGENDA: Legenda curta e magnética com o link {link} que tenha OBRIGATORIAMENTE MENOS DE 150 CARACTERES no total.
8. PROMPT_IA: Prompt detalhado em inglês (formato vertical 9:16) para gerar vídeo viral UGC de experimentação/uso real do produto '{nome_longo}' no dia a dia, mantendo 100% da aparência, cores, logos e formato do produto idênticos ao original, sem promessas enganosas.

Responda EXATAMENTE no formato CHAVE: VALOR (cada chave iniciando uma linha):
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

      # Parser robusto que suporta respostas multilinha por chave
      campos = {
          "TIK_TITULO": "",
          "TIK_LEGENDA": "",
          "INSTA_TITULO": "",
          "INSTA_LEGENDA": "",
          "PIN_TITULO": "",
          "PIN_DESCRICAO": "",
          "SHP_LEGENDA": "",
          "PROMPT_IA": "",
      }
      chave_atual = None
      for linha in res.split("\n"):
        linha_limpa = linha.strip()
        encontrou_chave = False
        for k in campos.keys():
          if linha_limpa.upper().startswith(f"{k}:"):
            chave_atual = k
            campos[k] = linha_limpa.split(":", 1)[1].strip()
            encontrou_chave = True
            break
        if not encontrou_chave and chave_atual and linha_limpa:
          campos[chave_atual] += "\n" + linha_limpa

      if campos["TIK_TITULO"] and campos["PIN_DESCRICAO"]:
        shp_ok = campos["SHP_LEGENDA"]
        if len(shp_ok) > 148:
          shp_ok = f"{nome_curto} com ótimo custo-benefício 👇\n{link}"
        return (
            f"IA Estratégica ({plataforma}) 🤖",
            campos["TIK_TITULO"],
            campos["TIK_LEGENDA"],
            campos["INSTA_TITULO"],
            campos["INSTA_LEGENDA"],
            campos["PIN_TITULO"],
            campos["PIN_DESCRICAO"],
            shp_ok,
            campos["PROMPT_IA"] if campos["PROMPT_IA"] else prompt_fallback_ia,
        )
    except Exception as e:
      st.toast(f"Aviso de IA: {e}, usando motor offline seguro.")

  # --- MODO OFFLINE ESTRATÉGICO (SEM CLICHÊS E RESPEITANDO A PLATAFORMA) ---
  tik_tit = f"Pare de gastar à toa: olha esse {nome_curto}"
  tik_leg = (
      f"Se você procura custo-benefício real sem cair em cilada, presta atenção no {nome_curto}. "
      f"{destaque} Já deixei o acesso direto {cta_tiktok} 👇\n{link}\n\n{tags}"
  )

  insta_tit = f"Vale a pena mesmo? Testando o {nome_curto}"
  insta_leg = (
      f"Muita gente paga bem mais caro por menos entrega.\n\n"
      f"O {nome_curto} resolve na prática: {destaque}\n\n"
      f"Quer conferir o preço atualizado? O acesso está {cta_insta}.\n\n{tags}"
  )

  pin_tit = f"{nome_curto} - Vale a Pena? Detalhes e Onde Encontrar ({plataforma})"
  pin_desc = (
      f"Buscando informações reais sobre {nome_longo}? Veja por que este item da categoria {categoria} "
      f"vem chamando atenção pelo custo-benefício. {destaque} Ideal para quem quer praticidade na rotina "
      f"sem pagar valores inflacionados. Confira disponibilidade e detalhes diretamente em {plataforma}: {link}\n\n"
      f"Curadoria Achados do Felipe.\n\n{tags}"
  )

  shp_leg = f"{cta_curto}\n{link} {tags}"
  if len(shp_leg) > 145:
    shp_leg = f"{nome_curto} 👇\n{link}"

  prompt_ia = prompt_fallback_ia
  estrategia_final = f"Motor Híbrido ({plataforma}) | {insight}"

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

      modo_gen = "⚡ Motor Offline Profissional"
      if IA_DISPONIVEL:
        modo_gen = st.radio(
            "Escolha o Motor:",
            [
                "🤖 Usar Inteligência Artificial (Gemini)",
                "⚡ Motor Offline Profissional",
            ],
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
            else "Uso prático no dia a dia."
        )

        _, _, _, _, insight_gerado, prompt_base_ia, aviso_seg = (
            limpar_e_extrair_shopee(n_longo)
        )
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
              aviso_seguranca=aviso_seg,
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

        st.markdown("**Legenda Curta (<150 caracteres)**")
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
      "Cole o Link (TikTok / Shopee) ou Mensagem do Produto:",
      placeholder="Ex: https://vt.tiktok.com/... ou Dê uma olhada em...",
      key="input_zap_cat",
  )
  titulo_rapido = st.text_input(
      "Título Rápido (Opcional — preencha se o link não trouxer o nome automaticamente):",
      placeholder="Ex: Tênis Fila Masculino Sprint",
      key="input_titulo_rapido",
  )

  nicho_escolhido = st.selectbox(
      "Pasta / Grupo do Pinterest:", lista_nichos, key="select_nicho_cat"
  )

  nova_categoria = ""
  if nicho_escolhido == "➕ Criar Nova Categoria / Grupo...":
    nova_categoria = st.text_input(
        "Digite o nome exato da nova pasta (ex: Calçados, Vestuário, Skincare, etc.):",
        key="input_nova_cat",
    )

  if st.button("Cadastrar Produto e Salvar Grupo 🚀", key="btn_salvar_cat"):
    if not texto_zap.strip() and not titulo_rapido.strip():
      st.error("Cole um link/mensagem ou informe o título rápido antes de salvar.")
    else:
      categoria_final = nicho_escolhido
      if nicho_escolhido == "➕ Criar Nova Categoria / Grupo...":
        if nova_categoria.strip():
          categoria_final = nova_categoria.strip()
        else:
          categoria_final = "Geral"

      if (
          categoria_final not in categorias_dict
          and categoria_final != "➕ Criar Nova Categoria / Grupo..."
      ):
        cerebro.setdefault("categorias_e_regras", {})[categoria_final] = {
            "tags_obrigatorias": [
                "#achados",
                "#dicasdecompras",
                f"#{categoria_final.lower().replace(' ', '')}",
            ],
        }
        salvar_cerebro(cerebro)

      nome_puro, nome_curto, link_limpo, frase_destaque, _, _, _ = (
          limpar_e_extrair_shopee(texto_zap, titulo_manual=titulo_rapido)
      )

      run_query(
          "INSERT INTO produtos (nome, nome_curto, destaques, nicho,"
          " link_afiliado) VALUES (?, ?, ?, ?, ?)",
          (nome_puro, nome_curto, frase_destaque, categoria_final, link_limpo),
          fetch=False,
      )
      plat = detectar_plataforma(link_limpo)
      st.success(
          f"Sucesso! Produto ({plat}) cadastrado na pasta '{categoria_final}'!"
      )
      st.rerun()

  st.markdown("---")
  st.markdown("#### Produtos Cadastrados")
  df_p = run_query(
      "SELECT id, nome_curto, destaques, nicho, link_afiliado FROM produtos ORDER BY id DESC"
  )
  if not df_p.empty:
    for _, row in df_p.iterrows():
      c1, c2 = st.columns([4, 1])
      plat_item = detectar_plataforma(row["link_afiliado"])
      with c1:
        st.markdown(
            f"**📦 {row['nome_curto']}** `[{plat_item} | Pasta: {row['nicho']}]`"
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
  st.info("Módulo ativo: Sincronização de tags, plataformas e grupos.")

elif menu == "📊 Dashboard":
  st.markdown("### 📊 Dashboard Consolidado")
  total_prod = len(run_query("SELECT id FROM produtos", fetch=True))
  total_cont = len(run_query("SELECT id FROM conteudos", fetch=True))
  col1, col2 = st.columns(2)
  with col1:
    st.metric("Total de Produtos", total_prod)
  with col2:
    st.metric("Roteiros Gerados", total_cont)
