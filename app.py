# -*- coding: utf-8 -*-
"""
Achados do Felipe - Dashboard Oficial (app.py)
Autor: Felipe de Oliveira Gonçalves (@achadosfelipe01)
Persistência em Nuvem via GitHub API (Imune à hibernação do Streamlit)
"""

import base64
import json
import os
import re
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

# --- PERSISTÊNCIA EM NUVEM (GITHUB API) ---
GITHUB_TOKEN = st.secrets.get("GITHUB_TOKEN", "").strip()
GITHUB_REPO = st.secrets.get("GITHUB_REPO", "").strip()
GITHUB_BRANCH = st.secrets.get("GITHUB_BRANCH", "main").strip()
DB_JSON_FILE = "banco_achados.json"
CEREBRO_FILE = "cerebro_v3.json"

NUVEM_ATIVA = bool(GITHUB_TOKEN and GITHUB_REPO and requests is not None)


def _github_headers():
  return {
      "Authorization": f"token {GITHUB_TOKEN}",
      "Accept": "application/vnd.github.v3+json",
  }


def ler_json_nuvem(caminho_arquivo, padrao):
  """Lê JSON diretamente do GitHub (se configurado) ou fallback local."""
  if NUVEM_ATIVA:
    url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{caminho_arquivo}?ref={GITHUB_BRANCH}"
    try:
      resp = requests.get(url, headers=_github_headers(), timeout=8)
      if resp.status_code == 200:
        conteudo_b64 = resp.json().get("content", "")
        texto = base64.b64decode(conteudo_b64).decode("utf-8")
        dados = json.loads(texto)
        with open(caminho_arquivo, "w", encoding="utf-8") as f:
          json.dump(dados, f, indent=2, ensure_ascii=False)
        return dados
    except Exception:
      pass

  if os.path.exists(caminho_arquivo):
    try:
      with open(caminho_arquivo, "r", encoding="utf-8") as f:
        return json.load(f)
    except Exception:
      pass
  return padrao


def salvar_json_nuvem(caminho_arquivo, dados, mensagem_commit="Sync dados app"):
  """Salva localmente e faz commit automático no GitHub."""
  with open(caminho_arquivo, "w", encoding="utf-8") as f:
    json.dump(dados, f, indent=2, ensure_ascii=False)

  if not NUVEM_ATIVA:
    return False

  url = f"https://api.github.com/repos/{GITHUB_REPO}/contents/{caminho_arquivo}"
  try:
    sha = None
    get_resp = requests.get(
        f"{url}?ref={GITHUB_BRANCH}", headers=_github_headers(), timeout=8
    )
    if get_resp.status_code == 200:
      sha = get_resp.json().get("sha")

    conteudo_str = json.dumps(dados, indent=2, ensure_ascii=False)
    conteudo_b64 = base64.b64encode(conteudo_str.encode("utf-8")).decode("utf-8")

    payload = {
        "message": mensagem_commit,
        "content": conteudo_b64,
        "branch": GITHUB_BRANCH,
    }
    if sha:
      payload["sha"] = sha

    put_resp = requests.put(
        url, headers=_github_headers(), json=payload, timeout=10
    )
    return put_resp.status_code in (200, 201)
  except Exception:
    return False


def carregar_banco(forcar_nuvem=False):
  padrao = {"produtos": [], "conteudos": []}
  if "db_cache" not in st.session_state or forcar_nuvem:
    dados = ler_json_nuvem(DB_JSON_FILE, padrao)
    if "produtos" not in dados:
      dados["produtos"] = []
    if "conteudos" not in dados:
      dados["conteudos"] = []
    st.session_state["db_cache"] = dados
  return st.session_state["db_cache"]


def salvar_banco(dados, msg="Atualiza banco_achados.json"):
  st.session_state["db_cache"] = dados
  ok = salvar_json_nuvem(DB_JSON_FILE, dados, mensagem_commit=msg)
  if NUVEM_ATIVA and not ok:
    st.warning("⚠️ Salvo localmente, mas falhou ao sincronizar com o GitHub.")


def carregar_cerebro(forcar_nuvem=False):
  padrao = {
      "configuracao_geral": {
          "versao": "23.0",
          "objetivo": "Matriz de inteligência de conteúdo multiplataforma",
      },
      "categorias_e_regras": {
          "Utilidades para Casa": {
              "tags_obrigatorias": [
                  "#achados",
                  "#utilidadesdomesticas",
                  "#casa",
              ],
          }
      },
  }
  if "cerebro_cache" not in st.session_state or forcar_nuvem:
    dados = ler_json_nuvem(CEREBRO_FILE, padrao)
    if "categorias_e_regras" not in dados:
      dados["categorias_e_regras"] = padrao["categorias_e_regras"]
    st.session_state["cerebro_cache"] = dados
  return st.session_state["cerebro_cache"]


def salvar_cerebro(dados):
  st.session_state["cerebro_cache"] = dados
  salvar_json_nuvem(
      CEREBRO_FILE, dados, mensagem_commit="Atualiza cerebro_v3.json"
  )


# --- CABEÇALHO ---
st.markdown('<div class="banner-container">', unsafe_allow_html=True)
try:
  if os.path.exists("banner.jpg"):
    st.image("banner.jpg")
  elif os.path.exists("banner.png"):
    st.image("banner.png")
except Exception:
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

col_status, col_sync = st.columns([4, 1])
with col_status:
  if NUVEM_ATIVA:
    st.caption(
        f"☁️ Banco persistente conectado ao GitHub (`{GITHUB_REPO}`) — seus"
        " dados não somem na hibernação."
    )
  else:
    st.caption(
        "⚠️ Modo local ativo: configure `GITHUB_TOKEN` e `GITHUB_REPO` nos"
        " Secrets para não perder dados na hibernação."
    )
with col_sync:
  if NUVEM_ATIVA and st.button("🔄 Recarregar Nuvem"):
    carregar_banco(forcar_nuvem=True)
    carregar_cerebro(forcar_nuvem=True)
    st.rerun()

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


# --- CONFIGURAÇÃO DA IA (GEMINI) ---
IA_DISPONIVEL = False
client = None
try:
  from google import genai

  api_key = st.secrets.get("GEMINI_API_KEY", "")
  if api_key:
    client = genai.Client(api_key=api_key.strip())
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
        if titulo and titulo.lower() not in [
            "tiktok",
            "make your day",
            "shopee brasil",
        ]:
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
      # Preserva parâmetros de rastreamento de afiliado
      link_puro = p.rstrip(".,;)")
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

  if any(
      k in t_lower
      for k in [
          "tênis",
          "tenis",
          "fila",
          "sneaker",
          "calçado",
          "calcado",
          "camiseta",
          "camisa",
          "calça",
          "calca",
          "jaqueta",
          "moletom",
          "vestuário",
          "vestuario",
          "roupa",
          "short",
      ]
  ):
    frase_destaque = (
        "Leveza e caimento prático para encarar a rotina, treino ou caminhada"
        " sem gastar uma fortuna."
    )
    insight_formato = (
        "🎬 FORMATO IDEAL: VÍDEO VIRAL DE EXPERIMENTAÇÃO (Uso real em"
        " movimento, mantendo 100% da aparência original)."
    )
    prompt_base_ia = (
        "Vertical 9:16 UGC video for TikTok showing a person wearing the exact"
        f" {nome_puro[:45]} from the reference while walking naturally on a"
        " clean sidewalk and stepping into daily routine on a bright morning."
        " Keep the exact product design, colors, stitching, logos, and shape"
        " identical with zero alteration. Smooth natural camera tracking,"
        " realistic daylight, authentic everyday lifestyle vibe, crisp focus,"
        " no misleading claims."
    )
    aviso_seguranca = (
        "Vestuário/Calçado: focar em experimentação real no dia a dia,"
        " conforto na rotina e fidelidade visual do item, sem promessas"
        " médicas."
    )
  elif any(
      k in t_lower
      for k in [
          "principia",
          "sérum",
          "serum",
          "ácido",
          "acido",
          "niacinamida",
          "retinol",
          "protetor solar",
          "pele",
          "skincare",
          "creamy",
          "cerave",
      ]
  ):
    frase_destaque = (
        "Textura leve que absorve rápido e encaixa fácil na rotina diária de"
        " cuidados com a pele."
    )
    insight_formato = (
        "📸 FORMATO IDEAL: VÍDEO DE ROTINA OU CARROSSEL (Textura e aplicação"
        " real, sem promessas clínicas)."
    )
    prompt_base_ia = (
        f"Vertical 9:16 UGC product video of {nome_puro[:45]} on a clean"
        " minimalist bathroom counter, soft natural morning light,"
        " authentic texture close-up, calm daily skincare routine aesthetic,"
        " keeping packaging identical, no medical claims."
    )
    aviso_seguranca = (
        "Skincare/Dermocosmético: PROIBIDO prometer cura, tratamento de"
        " acne/manchas ou efeito clínico garantido para evitar violação no"
        " TikTok."
    )
  elif any(
      k in t_lower
      for k in [
          "controle",
          "xbox",
          "playstation",
          "joystick",
          "gamer",
          "console",
      ]
  ):
    frase_destaque = (
        "Pegada firme, resposta precisa nos comandos e zero dor de cabeça com"
        " conexão no dia a dia."
    )
    insight_formato = (
        "🎬 FORMATO IDEAL: VÍDEO DEMONSTRATIVO (Unboxing rápido, pegada e"
        " botões em uso)."
    )
    prompt_base_ia = (
        "Vertical 9:16 UGC video showing hands holding and testing"
        f" {nome_puro[:45]} in a clean gaming setup, natural ambient"
        " lighting, crisp close-up of buttons and matte finish, keeping exact"
        " hardware appearance unchanged."
    )
    aviso_seguranca = (
        "Games/Eletrônicos: destacar ergonomia, compatibilidade e uso real sem"
        " exageros."
    )
  elif any(
      k in t_lower
      for k in [
          "shampoo",
          "condicionador",
          "cabelo",
          "infantil",
          "salon line",
          "litro",
      ]
  ):
    frase_destaque = (
        "Embalagem de 1 litro com bom rendimento para a rotina de cuidados"
        " capilares."
    )
    insight_formato = (
        "🎬 FORMATO IDEAL: VÍDEO DE ECONOMIA E ESCALA (Mostrar o tamanho real"
        " dos frascos de 1L)."
    )
    prompt_base_ia = (
        f"Vertical 9:16 UGC video showing {nome_puro[:45]} in a bright modern"
        " bathroom, natural lighting, emphasizing the large 1L bottle size and"
        " clean packaging identical to reference, authentic everyday"
        " aesthetic."
    )
    aviso_seguranca = (
        "Cabelos: destacar rendimento, tamanho e cuidado diário sem promessas"
        " milagrosas."
    )
  elif any(
      k in t_lower for k in ["trento", "chocolate", "wafer", "doce", "snack"]
  ):
    frase_destaque = (
        "Crocância na medida certa e recheio cremoso para salvar a pausa do"
        " café sem pesar no bolso."
    )
    insight_formato = (
        "📸 FORMATO IDEAL: VÍDEO CURTO DE PAUSA (Close na textura e consumo"
        " real)."
    )
    prompt_base_ia = (
        f"Vertical 9:16 close-up lifestyle video of {nome_puro[:45]} next to a"
        " cup of coffee on a clean table, soft natural side lighting, crisp"
        " macro texture, keeping exact packaging design unchanged."
    )
    aviso_seguranca = "Alimentos: foco em sabor, crocância e momento de consumo."
  else:
    frase_destaque = (
        "Solução prática que resolve um perrengue real do dia a dia com ótimo"
        " custo-benefício."
    )
    insight_formato = (
        "🎬 FORMATO IDEAL: VÍDEO DE DEMONSTRAÇÃO PRÁTICA (Mostrar o produto"
        " resolvendo o problema na prática)."
    )
    prompt_base_ia = (
        f"Vertical 9:16 UGC lifestyle video showing {nome_puro[:45]} in real"
        " everyday use, natural daylight, clean home environment, keeping"
        " exact product appearance unchanged, authentic handheld camera feel."
    )
    aviso_seguranca = (
        "Geral: copy direta, sem clichês vazios e fiel ao que o produto"
        " realmente entrega."
    )

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
  if plataforma == "TikTok Shop":
    tags_filtradas = [t for t in raw_tags if "shopee" not in t.lower()]
    base_tags = ["#achadostiktok", "#tiktokshopbrasil", "#achados"]
    cta_tiktok = "na sacolinha laranja aqui embaixo"
    cta_insta = "no link da bio (direto no TikTok Shop)"
    cta_curto = f"{nome_curto} no TikTok Shop 👇"
  elif plataforma == "Shopee":
    tags_filtradas = [t for t in raw_tags if "tiktok" not in t.lower()]
    base_tags = ["#achadosshopee", "#shopeebrasil", "#achados"]
    cta_tiktok = "no link da bio / sacolinha"
    cta_insta = "no link da bio (oferta na Shopee)"
    cta_curto = f"{nome_curto} na Shopee 👇"
  else:
    tags_filtradas = raw_tags
    base_tags = ["#achados", "#dicasdecompras", "#custobeneficio"]
    cta_tiktok = "no link da bio / sacolinha"
    cta_insta = "no link da bio"
    cta_curto = f"{nome_curto} no link 👇"

  tags_finais = []
  for t in base_tags + tags_filtradas:
    if t.lower() not in [x.lower() for x in tags_finais]:
      tags_finais.append(t)
  tags = " ".join(tags_finais[:5])

  erro_ia_detalhe = ""
  if usar_ia_forcado and IA_DISPONIVEL:
    prompt = f"""Você é o estrategista sênior de conteúdo do canal "Achados do Felipe" (Felipe de Oliveira Gonçalves).
Seu estilo de escrita é idêntico ao de um criador experiente conversando direto com o seguidor: afiado, direto ao ponto, focado em economia real, quebra de objeção e utilidade prática.

PROIBIÇÕES ABSOLUTAS:
1. NUNCA mencione "Shopee" se a PLATAFORMA DE ORIGEM for "{plataforma}" (se for TikTok Shop, trate 100% como achado do TikTok Shop / sacolinha laranja; só fale Shopee se a plataforma for Shopee).
2. PROIBIDO usar frases bobas ou clichês robóticos como: "Olha o que achei para facilitar", "Sabe aquele produto que vale cada centavo?", "Design funcional e excelente acabamento", "Produto imperdível", "Vibe", "Stans".
3. ANTI-VIOLAÇÃO TIKTOK: Nunca faça promessas médicas, de cura, tratamento clínico ou resultados garantidos/milagrosos. Respeite: {aviso_seguranca}

DADOS DO PRODUTO:
- Produto: '{nome_longo}'
- Plataforma de Origem: {plataforma}
- Link: {link}
- Categoria / Pasta: {categoria}
- Tags permitidas: {tags}

COMO ESTRUTURAR A COPY:
- Gancho (0-3s): Ataque uma dor real do bolso ou da rotina ou mostre uma oportunidade real de custo-benefício.
- Corpo: Explique em linguagem falada e natural por que esse item específico resolve o problema sem parecer texto de catálogo.
- CTA: Chamada clara para {cta_tiktok} (TikTok) ou {cta_insta} (Instagram).

GERE OS 8 CAMPOS ABAIXO:
1. TIK_TITULO: Gancho viral curto para abrir o vídeo no TikTok/Reels (máximo 55 caracteres).
2. TIK_LEGENDA: Legenda estilo criador real para TikTok, chamando para {cta_tiktok} e fechando com: {tags}.
3. INSTA_TITULO: Headline forte para capa de Reels ou primeiro card de carrossel no Instagram.
4. INSTA_LEGENDA: Legenda persuasiva e fluida para Instagram + chamada para {cta_insta} + {tags}.
5. PIN_TITULO: Título limpo e forte para SEO no Pinterest (até 100 caracteres).
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

    for modelo_nome in ["gemini-2.5-flash", "gemini-2.0-flash"]:
      try:
        res = client.models.generate_content(
            model=modelo_nome, contents=prompt
        ).text

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
            shp_ok = f"{nome_curto} com bom custo-benefício 👇\n{link}"
          return (
              f"IA Estratégica ({plataforma} | {modelo_nome}) 🤖",
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
        erro_ia_detalhe = str(e)
        continue

  tik_tit = f"Olha como fica no uso: {nome_curto}"
  tik_leg = (
      f"Para quem quer evitar gasto desnecessário, o {nome_curto} entra na"
      f" rotina com {destaque.lower()} Acesso direto {cta_tiktok} 👇\n{link}\n\n{tags}"
  )

  insta_tit = f"Na prática: {nome_curto}"
  insta_leg = (
      f"Sem promessa exagerada — só o que entrega no dia a dia.\n\n"
      f"O {nome_curto} faz sentido quando o foco é praticidade e conta que"
      f" fecha. Detalhes e disponibilidade {cta_insta}.\n\n{tags}"
  )

  pin_tit = f"{nome_curto} - Especificações e Uso Diário ({plataforma})"
  pin_desc = (
      f"Guia rápido sobre {nome_longo} na pasta {categoria}. Veja como o item"
      " se comporta no uso cotidiano e avalie se encaixa no seu objetivo"
      " antes de comprar. Informações e link direto em"
      f" {plataforma}: {link}\n\n"
      f"Curadoria Achados do Felipe.\n\n{tags}"
  )

  shp_leg = f"{cta_curto}\n{link}"
  if len(shp_leg) > 145:
    shp_leg = f"{nome_curto[:45]} 👇\n{link}"

  prompt_ia = prompt_fallback_ia
  motivo_fallback = (
      f" | Motivo IA: {erro_ia_detalhe[:120]}" if erro_ia_detalhe else ""
  )
  estrategia_final = (
      f"Motor Offline ({plataforma}){motivo_fallback} | {insight}"
  )

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
banco = carregar_banco()
lista_produtos = banco.get("produtos", [])
lista_conteudos = banco.get("conteudos", [])

if menu == "🎬 Gerar":
  st.markdown("### 🎬 Central de Geração Estratégica")
  if IA_DISPONIVEL:
    st.caption("🟢 Chave GEMINI_API_KEY detectada nos Secrets.")
  else:
    st.caption(
        "🔴 Chave GEMINI_API_KEY não detectada ou biblioteca google-genai"
        " ausente (usará Motor Offline)."
    )

  ids_ja_gerados = {c.get("produto_id") for c in lista_conteudos}
  pendentes_geracao = [
      p for p in lista_produtos if p.get("id") not in ids_ja_gerados
  ]

  if pendentes_geracao:
    with st.form("form_gerador"):
      opcoes_map = {
          f"#{p['id']} - {p['nome']}": p for p in pendentes_geracao
      }
      escolha_label = st.selectbox(
          "Selecione o Produto", list(opcoes_map.keys())
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
        prod_row = opcoes_map[escolha_label]
        prod_id = int(prod_row["id"])
        link_af = str(prod_row.get("link_afiliado", ""))
        nicho = str(prod_row.get("nicho", "Geral"))
        n_longo = str(prod_row.get("nome", "Produto"))
        n_curto = str(prod_row.get("nome_curto") or n_longo[:25])
        destaque = str(
            prod_row.get("destaques") or "Uso prático no dia a dia."
        )

        _, _, _, _, insight_gerado, prompt_base_ia, aviso_seg = (
            limpar_e_extrair_shopee(n_longo)
        )
        usar_ia = "Inteligência Artificial" in modo_gen

        with st.spinner("Processando roteiros e salvando na nuvem..."):
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

          novo_id = (
              max([c.get("id", 0) for c in lista_conteudos], default=0) + 1
          )
          lista_conteudos.append({
              "id": novo_id,
              "produto_id": prod_id,
              "estrategia_ia": estrategia,
              "tik_titulo_video": tik_tit,
              "tik_legenda": tik_leg,
              "insta_titulo_video": insta_tit,
              "insta_legenda": insta_leg,
              "pin_titulo": pin_tit,
              "pin_descricao": pin_desc,
              "shp_legenda": shp_leg,
              "prompt_ia": prompt_ia,
              "status": "Pendente 🟡",
          })
          banco["conteudos"] = lista_conteudos
          salvar_banco(banco, msg=f"Gera roteiro #{novo_id}")

        st.success("🎉 Sucesso! Roteiro gerado e salvo na nuvem.")
        st.rerun()
  else:
    st.info("Catálogo vazio ou todos os produtos já gerados!")

elif menu == "📋 Pendentes":
  st.markdown("### 📋 Central de Pendentes (Com Cópia Nativa em Cada Bloco)")
  mapa_produtos = {p.get("id"): p for p in lista_produtos}

  if lista_conteudos:
    for row in sorted(
        lista_conteudos, key=lambda x: x.get("id", 0), reverse=True
    ):
      prod_info = mapa_produtos.get(row.get("produto_id"), {})
      nome_p = prod_info.get("nome_curto", "Produto")
      status_ico = (
          "✔️ Concluído"
          if "Concluído" in str(row.get("status", ""))
          else "🟡 Pendente"
      )

      with st.expander(f"[{status_ico}] {nome_p} (ID: {row.get('id')})"):
        st.info(f"💡 {row.get('estrategia_ia', '')}")

        st.markdown("**TikTok Gancho**")
        st.code(row.get("tik_titulo_video") or "", language="text")

        st.markdown("**TikTok Legenda**")
        st.code(row.get("tik_legenda") or "", language="text")

        st.markdown("**Instagram Capa / Título**")
        st.code(row.get("insta_titulo_video") or "", language="text")

        st.markdown("**Instagram Legenda**")
        st.code(row.get("insta_legenda") or "", language="text")

        st.markdown("**Pinterest Título**")
        st.code(row.get("pin_titulo") or "", language="text")

        st.markdown("**Pinterest Descrição SEO (Rica, ~800 caracteres)**")
        st.code(row.get("pin_descricao") or "", language="text")

        st.markdown("**Legenda Curta (<150 caracteres)**")
        st.code(row.get("shp_legenda") or "", language="text")

        st.markdown("**🎥 Prompt de Vídeo / B-Roll (Para IA)**")
        st.code(row.get("prompt_ia") or "", language="text")

        st.markdown("---")
        c1, c2 = st.columns(2)
        with c1:
          if st.button("Marcar Concluído ✔️", key=f"ok_{row['id']}"):
            for item in lista_conteudos:
              if item.get("id") == row.get("id"):
                item["status"] = "Concluído ✔️"
            banco["conteudos"] = lista_conteudos
            salvar_banco(banco, msg=f"Conclui roteiro #{row['id']}")
            st.rerun()
        with c2:
          if st.button("Excluir 🗑️", key=f"del_{row['id']}"):
            banco["conteudos"] = [
                c for c in lista_conteudos if c.get("id") != row.get("id")
            ]
            salvar_banco(banco, msg=f"Exclui roteiro #{row['id']}")
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
      "Título Rápido (Opcional — preencha se o link não trouxer o nome"
      " automaticamente):",
      placeholder="Ex: Tênis Fila Masculino Sprint",
      key="input_titulo_rapido",
  )

  nicho_escolhido = st.selectbox(
      "Pasta / Grupo do Pinterest:", lista_nichos, key="select_nicho_cat"
  )

  nova_categoria = ""
  if nicho_escolhido == "➕ Criar Nova Categoria / Grupo...":
    nova_categoria = st.text_input(
        "Digite o nome exato da nova pasta (ex: Calçados, Vestuário,"
        " Skincare, etc.):",
        key="input_nova_cat",
    )

  if st.button("Cadastrar Produto e Salvar Grupo 🚀", key="btn_salvar_cat"):
    if not texto_zap.strip() and not titulo_rapido.strip():
      st.error(
          "Cole um link/mensagem ou informe o título rápido antes de salvar."
      )
    else:
      categoria_final = nicho_escolhido
      if nicho_escolhido == "➕ Criar Nova Categoria / Grupo...":
        categoria_final = (
            nova_categoria.strip() if nova_categoria.strip() else "Geral"
        )

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

      novo_prod_id = (
          max([p.get("id", 0) for p in lista_produtos], default=0) + 1
      )
      lista_produtos.append({
          "id": novo_prod_id,
          "nome": nome_puro,
          "nome_curto": nome_curto,
          "destaques": frase_destaque,
          "nicho": categoria_final,
          "link_afiliado": link_limpo,
      })
      banco["produtos"] = lista_produtos
      salvar_banco(banco, msg=f"Cadastra produto #{novo_prod_id}")

      plat = detectar_plataforma(link_limpo)
      st.success(
          f"Sucesso! Produto ({plat}) salvo na pasta '{categoria_final}'!"
      )
      st.rerun()

  st.markdown("---")
  st.markdown("#### Produtos Cadastrados")
  if lista_produtos:
    for row in sorted(
        lista_produtos, key=lambda x: x.get("id", 0), reverse=True
    ):
      c1, c2 = st.columns([4, 1])
      plat_item = detectar_plataforma(row.get("link_afiliado", ""))
      with c1:
        st.markdown(
            f"**📦 {row.get('nome_curto')}** `[{plat_item} | Pasta:"
            f" {row.get('nicho')}]`"
        )
        st.caption(f"💡 {row.get('destaques', '')}")
      with c2:
        if st.button("Excluir 🗑️", key=f"del_prod_{row['id']}"):
          banco["produtos"] = [
              p for p in lista_produtos if p.get("id") != row.get("id")
          ]
          salvar_banco(banco, msg=f"Exclui produto #{row['id']}")
          st.rerun()

elif menu == "🧠 Treinamento":
  st.markdown("### 🧠 Treinamento e Ajustes do Cérebro V3")
  st.json(carregar_cerebro())

elif menu == "🧬 Auto-Evolução":
  st.markdown("### 🧬 Painel de Auto-Evolução")
  st.info(
      "Módulo ativo: Sincronização em nuvem via GitHub API, tags, plataformas e"
      " grupos."
  )

elif menu == "📊 Dashboard":
  st.markdown("### 📊 Dashboard Consolidado")
  col1, col2 = st.columns(2)
  with col1:
    st.metric("Total de Produtos", len(lista_produtos))
  with col2:
    st.metric("Roteiros Gerados", len(lista_conteudos))
