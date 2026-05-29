"""
gerar_eventos.py
Lê eventos_mineracao_geotecnia_2026.xlsx e atualiza o index.html
Uso: python gerar_eventos.py
"""

import pandas as pd
import re
from datetime import datetime, date
from pathlib import Path

# ── CAMINHOS ──────────────────────────────────────────────────────────────
BASE_DIR   = Path(__file__).parent
XLSX_FILE  = BASE_DIR / "eventos_mineracao_geotecnia_2026.xlsx"
TEMPLATE   = BASE_DIR / "index.html"      # seu template atual
HTML_OUT   = BASE_DIR / "index.html"      # sobrescreve o mesmo arquivo
                                           # mude para "index_novo.html" se preferir

# ── DICIONÁRIOS AUXILIARES ────────────────────────────────────────────────
MESES_PT = {
    "jan":1,"fev":2,"mar":3,"abr":4,"mai":5,"jun":6,
    "jul":7,"ago":8,"set":9,"out":10,"nov":11,"dez":12,
    "janeiro":1,"fevereiro":2,"março":3,"abril":4,"maio":5,"junho":6,
    "julho":7,"agosto":8,"setembro":9,"outubro":10,"novembro":11,"dezembro":12,
}

# Mapa: texto livre de relevância → código rc usado no CSS do template
RELEV_MAP = {
    "alta":       ("ALTA",        "alta"),
    "média a alta":("Média a Alta","media-alta"),
    "media a alta":("Média a Alta","media-alta"),
    "média":      ("Média",       "media"),
    "media":      ("Média",       "media"),
    "baixa a média":("Baixa a Média","baixa"),
    "baixa a media":("Baixa a Média","baixa"),
    "baixa":      ("Baixa",       "baixa"),
}

def parse_relevancia(texto):
    """Devolve (rel_label, rel_code) a partir do texto livre."""
    t = texto.lower().strip() if texto else ""
    # testa do mais específico para o mais genérico
    for chave in ["média a alta","media a alta","baixa a média","baixa a media",
                  "alta","média","media","baixa"]:
        if chave in t:
            return RELEV_MAP[chave]
    return ("Média", "media")

def parse_dates(texto):
    """
    Devolve (d0: date|None, d1: date|None, ds: str)
    a partir de strings como '14/04/2026', '03 a 05/05/2026',
    '26 e 27/05/2026', '2026-04-06 00:00:00', 'Outubro/2026 (...)'
    """
    texto = str(texto).strip()
    ds    = texto  # string de exibição padrão

    # pandas datetime (ex: '2026-04-06 00:00:00')
    try:
        d = pd.to_datetime(texto, dayfirst=True).date()
        return d, d, d.strftime("%d/%m/%Y")
    except Exception:
        pass

    # 'DD/MM/YYYY'
    m = re.search(r"(\d{1,2})/(\d{2})/(\d{4})", texto)
    if m:
        try:
            d = date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
            return d, d, d.strftime("%d/%m/%Y")
        except Exception:
            pass

    # 'DD a DD/MM/YYYY' ou 'DD e DD/MM/YYYY'
    m = re.search(r"(\d{1,2})\s+[ae]\s+(\d{1,2})/(\d{2})/(\d{4})", texto)
    if m:
        try:
            d0 = date(int(m.group(4)), int(m.group(3)), int(m.group(1)))
            d1 = date(int(m.group(4)), int(m.group(3)), int(m.group(2)))
            return d0, d1, texto
        except Exception:
            pass

    # Mês por extenso → usa dia 1 como estimativa
    for nome, num in sorted(MESES_PT.items(), key=lambda x: -len(x[0])):
        if nome in texto.lower():
            try:
                d = date(2026, num, 1)
                return d, d, texto
            except Exception:
                pass

    return None, None, texto

def js_date(d):
    """Converte date → 'new Date(YYYY, M, D)' com mês 0-based (igual ao JS)."""
    if d is None:
        return "new Date(2026,0,1)"
    return f"new Date({d.year},{d.month - 1},{d.day})"

def js_str(s):
    """Escapa aspas duplas para uso dentro de string JS."""
    return s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", " ")

def parse_participants(texto):
    """Divide a string de participantes em lista Python."""
    if not texto or texto == "nan":
        return []
    # Separa por quebras de linha ou vírgulas seguidas de maiúscula
    partes = re.split(r'\n|,\s*(?=[A-ZÁÉÍÓÚÀÂÊÎÔÛÃÕÇ])', texto)
    result = []
    for p in partes:
        p = p.strip()
        # Remove cargo entre parênteses para manter só o nome
        nome = re.sub(r'\s*[\(\-–].*$', '', p).strip()
        if nome and nome not in ("nan", ""):
            result.append(nome)
    return result

# ── LER PLANILHA ──────────────────────────────────────────────────────────
print(f"Lendo {XLSX_FILE.name}...")
df = pd.read_excel(XLSX_FILE, sheet_name="Eventos 2026", header=3)

events = []
for i, row in df.iterrows():
    data_raw = str(row.get("Data", ""))        if pd.notna(row.get("Data"))        else ""
    evento   = str(row.get("Evento", ""))      if pd.notna(row.get("Evento"))      else ""
    org      = str(row.get("Organizador", "")) if pd.notna(row.get("Organizador")) else ""
    local    = str(row.get("Cidade/Local","")) if pd.notna(row.get("Cidade/Local"))else ""
    tema_full= str(row.get("Tema/Foco Principal","")) if pd.notna(row.get("Tema/Foco Principal")) else ""
    relev_txt= str(row.get("Relevância para a Gerência","")) if pd.notna(row.get("Relevância para a Gerência")) else ""
    part_txt = str(row.get("Participantes Sugeridos","")) if pd.notna(row.get("Participantes Sugeridos")) else ""

    # Para linhas de legenda/metadados (após os eventos)
    if not evento or evento.startswith("nan"):
        continue
    if any(k in data_raw for k in ["LEGENDA","COMPOSIÇÃO","Nota:"]):
        break
    if any(k in evento for k in ["Gerente","Coordenador","Especialista","Evento diretamente"]):
        break
    if i > 11:
        break

    # Extrair primeiro parágrafo do tema como tema curto
    tema_lines  = tema_full.split(";")
    tema_curto  = tema_lines[0].strip() if tema_lines else tema_full[:50]

    d0, d1, ds        = parse_dates(data_raw)
    rel_label, rel_code = parse_relevancia(relev_txt)
    participantes     = parse_participants(part_txt)

    # Nota resumida de relevância (primeira frase)
    rel_nota = relev_txt.split(".")[0].strip() if relev_txt else ""

    events.append({
        "id":    len(events) + 1,
        "nome":  evento.strip(),
        "d0":    d0,
        "d1":    d1,
        "ds":    ds,
        "org":   org.strip(),
        "loc":   local.strip(),
        "tema":  tema_curto,
        "foco":  tema_full.strip(),
        "rel":   rel_label,
        "rc":    rel_code,
        "rn":    rel_nota,
        "pp":    participantes,
        "ac":    [],          # ações a confirmar — deixe vazio ou preencha manualmente
    })

events.sort(key=lambda e: e["d0"] or date(2026, 12, 31))
print(f"✅ {len(events)} eventos lidos da planilha")

# ── GERAR BLOCO JS ────────────────────────────────────────────────────────
def build_event_js(e):
    pp_js = "[" + ",".join(f'"{js_str(p)}"' for p in e["pp"]) + "]"
    ac_js = "[" + ",".join(f'"{js_str(a)}"' for a in e["ac"]) + "]"
    return (
        f'  {{id:{e["id"]},'
        f'nome:"{js_str(e["nome"])}",'
        f'd0:{js_date(e["d0"])},'
        f'd1:{js_date(e["d1"])},'
        f'ds:"{js_str(e["ds"])}",'
        f'org:"{js_str(e["org"])}",'
        f'loc:"{js_str(e["loc"])}",'
        f'tema:"{js_str(e["tema"])}",'
        f'foco:"{js_str(e["foco"])}",'
        f'rel:"{js_str(e["rel"])}",'
        f'rc:"{js_str(e["rc"])}",'
        f'rn:"{js_str(e["rn"])}",'
        f'pp:{pp_js},'
        f'ac:{ac_js}}}'
    )

novo_E_block = "const E=[\n" + ",\n".join(build_event_js(e) for e in events) + "\n]"

# ── ATUALIZAR NOW ─────────────────────────────────────────────────────────
hoje = date.today()
novo_NOW = "const NOW=new Date()"

# ── LER TEMPLATE E SUBSTITUIR ─────────────────────────────────────────────
print(f"Lendo template {TEMPLATE.name}...")
html = TEMPLATE.read_text(encoding="utf-8")

# Substituir bloco const E=[...];
html = re.sub(
    r"const E=\[.*?\](?=;\s*\nconst TEAM)",
    novo_E_block,
    html,
    flags=re.DOTALL
)

# Substituir const NOW=...
html = re.sub(
    r"const NOW=new Date\(\d{4},\d{1,2},\d{1,2}\)",
    novo_NOW,
    html
)

# ── SALVAR ────────────────────────────────────────────────────────────────
HTML_OUT.write_text(html, encoding="utf-8")
print(f"✅ {HTML_OUT.name} gerado — {hoje.strftime('%d/%m/%Y')} — {len(events)} eventos")
