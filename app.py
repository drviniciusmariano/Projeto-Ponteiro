import streamlit as st
import pandas as pd
import sqlite3
import os
import json
import io
from datetime import datetime, date, timedelta
import anthropic

# ══════════════════════════════════════════════════════════════
# CONFIG
# ══════════════════════════════════════════════════════════════
st.set_page_config(
    page_title="LAB Metrics — Cockpit Executivo",
    page_icon="🩺",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ── DESIGN SYSTEM ─────────────────────────────────────────────
NAVY   = "#0D1B2A"
GOLD   = "#C8963C"
IVORY  = "#F8F6F1"
GREEN  = "#00C896"
RED    = "#E05252"
CARD   = "#161F2E"
MID    = "#1E2D40"

st.markdown(f"""
<style>
  html, body, [class*="css"] {{ font-family: 'Segoe UI', sans-serif; }}
  .main {{ background-color: {NAVY}; }}
  .block-container {{ padding-top: 1.5rem; padding-bottom: 2rem; }}
  h1,h2,h3 {{ color: {IVORY}; }}
  p, li, label {{ color: #A3A8B4; }}
  div[data-testid="metric-container"] {{
    background-color: {CARD}; border: 1px solid rgba(200,150,60,0.2);
    border-radius: 12px; padding: 16px 20px;
  }}
  div[data-testid="stMetricValue"] {{ font-size: 1.9rem; font-weight: 700; color: {GREEN}; }}
  div[data-testid="stMetricLabel"] {{ font-size: 0.8rem; color: #A3A8B4; text-transform: uppercase; letter-spacing: 1px; }}
  div[data-testid="stMetricDelta"] > div {{ font-size: 0.75rem; }}
  .stProgress > div > div > div > div {{ background-color: {GOLD}; }}
  .stButton > button {{ background-color: {GOLD}; color: {NAVY}; border-radius: 8px;
    border: none; font-weight: 700; padding: 8px 20px; }}
  .stButton > button:hover {{ background-color: #E5B96B; color: {NAVY}; }}
  .stTabs [data-baseweb="tab-list"] {{ background-color: {CARD}; border-radius: 10px; padding: 4px; }}
  .stTabs [data-baseweb="tab"] {{ border-radius: 8px; color: #A3A8B4; font-weight: 500; }}
  .stTabs [aria-selected="true"] {{ background-color: {GOLD} !important; color: {NAVY} !important; font-weight: 700 !important; }}
  .stDataFrame {{ border-radius: 10px; overflow: hidden; }}
  .stSelectbox > div > div {{ border-radius: 8px; background-color: {CARD}; border-color: rgba(200,150,60,0.3); color: {IVORY}; }}
  .stTextInput > div > div > input {{ border-radius: 8px; background-color: {CARD}; border-color: rgba(200,150,60,0.3); color: {IVORY}; }}
  .stNumberInput > div > div > input {{ border-radius: 8px; background-color: {CARD}; border-color: rgba(200,150,60,0.3); color: {IVORY}; }}
  .stExpander {{ border-radius: 10px; border: 1px solid rgba(200,150,60,0.2); background-color: {CARD}; }}
  .stExpander summary {{ color: {IVORY}; }}
  .stCheckbox > label {{ color: #A3A8B4; }}
  div[data-testid="stSidebarContent"] {{ background-color: {CARD}; }}
  .stRadio > div > label {{ color: #A3A8B4; }}
</style>
""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# BANCO DE DADOS
# ══════════════════════════════════════════════════════════════
DB = "lab_metrics.db"

def get_conn():
    return sqlite3.connect(DB, check_same_thread=False)

def init_db():
    conn = get_conn()
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS clinica (
            id INTEGER PRIMARY KEY DEFAULT 1,
            nome TEXT DEFAULT 'Integrative Campinas',
            meta_mensal REAL DEFAULT 0,
            custo_fixo_total REAL DEFAULT 0,
            estagio TEXT DEFAULT 'Caótico',
            modelo_tributario TEXT DEFAULT 'Simples Nacional'
        );
        INSERT OR IGNORE INTO clinica (id) VALUES (1);

        CREATE TABLE IF NOT EXISTS dre (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            mes TEXT, ano INTEGER,
            receita_consultas REAL DEFAULT 0,
            receita_procedimentos REAL DEFAULT 0,
            receita_recorrencia REAL DEFAULT 0,
            receita_outros REAL DEFAULT 0,
            imposto_pct REAL DEFAULT 8.5,
            taxa_cartao_pct REAL DEFAULT 3.0,
            custo_insumos REAL DEFAULT 0,
            custo_pessoal REAL DEFAULT 0,
            custo_ocupacao REAL DEFAULT 0,
            custo_marketing REAL DEFAULT 0,
            custo_outros REAL DEFAULT 0,
            UNIQUE(mes, ano)
        );

        CREATE TABLE IF NOT EXISTS painel_dna (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            semana TEXT, ano INTEGER,
            meta_mensal REAL DEFAULT 0,
            realizado_mes REAL DEFAULT 0,
            dias_uteis_restantes INTEGER DEFAULT 5,
            consultas_agendadas_val REAL DEFAULT 0,
            procedimentos_agendados_val REAL DEFAULT 0,
            negociacoes_abertas REAL DEFAULT 0,
            orcamentos_enviados REAL DEFAULT 0,
            seg_consultas REAL DEFAULT 0, seg_procedimentos REAL DEFAULT 0, seg_negociacoes REAL DEFAULT 0,
            ter_consultas REAL DEFAULT 0, ter_procedimentos REAL DEFAULT 0, ter_negociacoes REAL DEFAULT 0,
            qua_consultas REAL DEFAULT 0, qua_procedimentos REAL DEFAULT 0, qua_negociacoes REAL DEFAULT 0,
            qui_consultas REAL DEFAULT 0, qui_procedimentos REAL DEFAULT 0, qui_negociacoes REAL DEFAULT 0,
            sex_consultas REAL DEFAULT 0, sex_procedimentos REAL DEFAULT 0, sex_negociacoes REAL DEFAULT 0,
            UNIQUE(semana, ano)
        );

        CREATE TABLE IF NOT EXISTS salas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT, medico_responsavel TEXT,
            horas_disponiveis REAL DEFAULT 8.0,
            horas_ocupadas REAL DEFAULT 0.0,
            no_show INTEGER DEFAULT 0,
            perda_noshow REAL DEFAULT 0.0,
            ticket_hora REAL DEFAULT 0.0,
            mes TEXT, ano INTEGER
        );

        CREATE TABLE IF NOT EXISTS colaboradores (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT, funcao TEXT,
            nivel_acesso TEXT DEFAULT 'Operacional',
            zona_genialidade TEXT DEFAULT '',
            ativo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS mod_tarefas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            titulo TEXT, responsavel TEXT,
            dri TEXT DEFAULT '',
            frequencia TEXT DEFAULT 'Diária',
            categoria TEXT DEFAULT 'Operacional',
            peso_pct INTEGER DEFAULT 10,
            ativo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS mod_execucao (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            tarefa_id INTEGER,
            colaborador TEXT,
            data_execucao TEXT,
            concluida INTEGER DEFAULT 0,
            UNIQUE(tarefa_id, colaborador, data_execucao)
        );

        CREATE TABLE IF NOT EXISTS onboarding (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            colaborador_id INTEGER,
            modulo TEXT,
            concluido INTEGER DEFAULT 0,
            data_conclusao TEXT
        );

        CREATE TABLE IF NOT EXISTS regua_pacientes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_paciente TEXT,
            tipo_contato TEXT DEFAULT 'Primeira Consulta',
            data_consulta TEXT,
            status_d1 TEXT DEFAULT 'Pendente',
            status_d_mais1 TEXT DEFAULT 'Pendente',
            status_d_mais3 TEXT DEFAULT 'Pendente',
            status_d_mais7 TEXT DEFAULT 'Pendente',
            status_d_mais14 TEXT DEFAULT 'Pendente',
            ticket_valor REAL DEFAULT 0.0,
            fechou_protocolo INTEGER DEFAULT 0,
            obs TEXT
        );

        CREATE TABLE IF NOT EXISTS leads (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome TEXT, canal TEXT DEFAULT 'Instagram',
            sdr_nome TEXT, status TEXT DEFAULT 'Novo',
            tempo_resposta_min INTEGER DEFAULT 0,
            compareceu INTEGER DEFAULT 0,
            convertido INTEGER DEFAULT 0,
            ticket_proposto REAL DEFAULT 0.0,
            motivo_perda TEXT DEFAULT '',
            mes TEXT, ano INTEGER,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS okrs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            objetivo TEXT, key_result TEXT,
            meta_valor REAL DEFAULT 0,
            atual_valor REAL DEFAULT 0,
            responsavel TEXT,
            trimestre TEXT, ano INTEGER,
            ativo INTEGER DEFAULT 1
        );

        CREATE TABLE IF NOT EXISTS relatorios (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nome_arquivo TEXT, conteudo TEXT,
            analise_ia TEXT, mes TEXT, ano INTEGER,
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS briefing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT UNIQUE,
            responsavel TEXT DEFAULT \'\',
            consultas_agendadas INTEGER DEFAULT 0,
            procedimentos_agendados INTEGER DEFAULT 0,
            confirmacoes_realizadas INTEGER DEFAULT 0,
            gaps_agenda INTEGER DEFAULT 0,
            valor_agenda_dia REAL DEFAULT 0,
            leads_pendentes INTEGER DEFAULT 0,
            orcamentos_abertos INTEGER DEFAULT 0,
            valor_orcamentos_abertos REAL DEFAULT 0,
            rfm_contatos_meta INTEGER DEFAULT 30,
            indicacoes_meta INTEGER DEFAULT 5,
            pacientes_retorno_hoje INTEGER DEFAULT 0,
            dm1_primeira_consulta INTEGER DEFAULT 0,
            dm1_retorno INTEGER DEFAULT 0,
            dp1_primeira_consulta INTEGER DEFAULT 0,
            dp1_retorno INTEGER DEFAULT 0,
            follow_d3 INTEGER DEFAULT 0,
            follow_d7 INTEGER DEFAULT 0,
            follow_d14 INTEGER DEFAULT 0,
            prioridade_1 TEXT DEFAULT \'\',
            prioridade_2 TEXT DEFAULT \'\',
            prioridade_3 TEXT DEFAULT \'\',
            dri_prioridade_1 TEXT DEFAULT \'\',
            dri_prioridade_2 TEXT DEFAULT \'\',
            dri_prioridade_3 TEXT DEFAULT \'\',
            obs_briefing TEXT DEFAULT \'\',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS debriefing (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            data TEXT UNIQUE,
            responsavel TEXT DEFAULT \'\',
            receita_consultas REAL DEFAULT 0,
            receita_procedimentos REAL DEFAULT 0,
            receita_recorrencia REAL DEFAULT 0,
            receita_outros_dia REAL DEFAULT 0,
            despesas_insumos REAL DEFAULT 0,
            despesas_operacionais REAL DEFAULT 0,
            despesas_outras REAL DEFAULT 0,
            consultas_realizadas INTEGER DEFAULT 0,
            procedimentos_realizados INTEGER DEFAULT 0,
            no_show_dia INTEGER DEFAULT 0,
            cancelamentos_dia INTEGER DEFAULT 0,
            perda_noshow_dia REAL DEFAULT 0,
            leads_respondidos INTEGER DEFAULT 0,
            tempo_resposta_medio INTEGER DEFAULT 0,
            agendamentos_gerados INTEGER DEFAULT 0,
            orcamentos_fechados INTEGER DEFAULT 0,
            valor_orcamentos_fechados REAL DEFAULT 0,
            rfm_contatos_realizados INTEGER DEFAULT 0,
            indicacoes_solicitadas INTEGER DEFAULT 0,
            indicacoes_recebidas INTEGER DEFAULT 0,
            avaliacoes_google INTEGER DEFAULT 0,
            dm1_executados INTEGER DEFAULT 0,
            dp1_executados INTEGER DEFAULT 0,
            follow_executados INTEGER DEFAULT 0,
            meta_dia_batida INTEGER DEFAULT 0,
            principal_conquista TEXT DEFAULT \'\',
            principal_gargalo TEXT DEFAULT \'\',
            acao_amanha TEXT DEFAULT \'\',
            dri_acao_amanha TEXT DEFAULT \'\',
            obs_debriefing TEXT DEFAULT \'\',
            criado_em TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)
    conn.commit()
    conn.close()

init_db()

# ══════════════════════════════════════════════════════════════
# HELPERS
# ══════════════════════════════════════════════════════════════
def fmt(v):
    if v is None: return "R$ 0,00"
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def pct_safe(a, b):
    return round((a / b) * 100, 1) if b else 0.0

def semaforo(p, limiar=85):
    if p >= 100: return "🟢", GREEN
    if p >= limiar: return "🟡", GOLD
    return "🔴", RED

def card(titulo, valor, sub="", cor=GREEN, grande=False):
    fs = "2rem" if grande else "1.5rem"
    return f"""<div style="background:{CARD};border-radius:12px;padding:18px 20px;
               border:1px solid rgba(200,150,60,0.2);margin-bottom:12px">
        <div style="font-size:10px;color:#A3A8B4;text-transform:uppercase;
                    letter-spacing:1.5px;margin-bottom:6px">{titulo}</div>
        <div style="font-size:{fs};font-weight:800;color:{cor};
                    font-family:Georgia,serif;line-height:1.1">{valor}</div>
        {f'<div style="font-size:11px;color:#A3A8B4;margin-top:5px">{sub}</div>' if sub else ''}
    </div>"""

def barra(p, label="", cor=None, bg="#1E2D40"):
    c = cor or (GREEN if p >= 100 else GOLD if p >= 70 else RED)
    return f"""<div style="margin-bottom:10px">
        <div style="display:flex;justify-content:space-between;font-size:12px;
                    color:#A3A8B4;margin-bottom:3px">
            <span>{label}</span>
            <span style="color:{c};font-weight:700">{min(int(p),100)}%</span>
        </div>
        <div style="height:7px;background:{bg};border-radius:4px;overflow:hidden">
            <div style="height:7px;width:{min(int(p),100)}%;background:{c};
                        border-radius:4px"></div>
        </div>
    </div>"""

def badge(texto, cor=GOLD):
    return f"""<span style="background:{cor}22;color:{cor};border:1px solid {cor}44;
               border-radius:20px;padding:3px 10px;font-size:11px;font-weight:700">{texto}</span>"""

def titulo_secao(t, sub=""):
    return f"""<div style="display:flex;align-items:center;margin-bottom:6px">
        <div style="width:4px;height:22px;background:{GOLD};border-radius:2px;margin-right:10px"></div>
        <h2 style="margin:0;font-size:20px;color:{IVORY};font-family:Georgia,serif;font-weight:700">{t}</h2>
    </div>
    {f'<p style="margin:2px 0 16px 14px;font-size:12px;color:#A3A8B4">{sub}</p>' if sub else '<div style="margin-bottom:16px"></div>'}"""

MESES = ["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]

# ══════════════════════════════════════════════════════════════
# SIDEBAR
# ══════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown(f"""
    <div style="margin-bottom:8px">
        <div style="font-family:Georgia,serif;font-size:20px;color:{GOLD};font-weight:700">
            🩺 LAB Metrics
        </div>
        <div style="color:#555;font-size:10px;letter-spacing:2px;text-transform:uppercase">
            Sovereignty & Previsibilidade
        </div>
    </div>""", unsafe_allow_html=True)

    conn = get_conn()
    clin = conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    conn.close()
    nome_clin = clin[1] if clin else "Minha Clínica"

    st.markdown(f"""
    <div style="color:#A3A8B4;font-size:12px;margin-bottom:4px">{nome_clin}</div>
    <div style="color:{GOLD};font-size:11px;margin-bottom:16px">
        {clin[4] if clin and len(clin)>4 else 'Caótico'}
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:{MID};border-radius:8px;padding:10px 14px;margin-bottom:16px">
        <div style="color:{GOLD};font-size:10px;letter-spacing:1px;
                    text-transform:uppercase;margin-bottom:6px">Período</div>""",
    unsafe_allow_html=True)
    c1, c2 = st.columns([3,2])
    with c1:
        mes_sel = st.selectbox("M", MESES, index=datetime.now().month-1, label_visibility="collapsed")
    with c2:
        ano_sel = st.number_input("A", value=datetime.now().year, min_value=2020, max_value=2030, label_visibility="collapsed")
    st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("---")
    aba = st.radio("", [
        "🩺  Cockpit CEO",
        "☀️  Briefing — Abertura do Dia",
        "🌙  Debriefing — Fechamento do Dia",
        "📊  Painel DNA Semanal",
        "🏥  Auditoria de Salas",
        "📈  Comercial & SDR",
        "🔄  Réguas D-1 / D+1",
        "🎓  Programa Integra",
        "💰  Financeiro & EBITDA",
        "📐  OKRs",
        "🧬  Importar Support Clinic",
        "🤖  Assistente LAB Metrics",
        "⚙️  Configurações"
    ], label_visibility="collapsed")

    st.markdown(f"""
    <div style="margin-top:24px;padding:12px;background:{MID};border-radius:8px;
                border-left:3px solid {GOLD}">
        <div style="font-size:10px;color:#555;font-style:italic;line-height:1.6">
            "Ideia é prata. Mentalidade é ouro.<br>
            <strong style="color:{GOLD}">Execução é diamante.</strong>"
        </div>
    </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 1. COCKPIT CEO — Decisão em 30 segundos
# ══════════════════════════════════════════════════════════════
if aba == "🩺  Cockpit CEO":
    st.markdown(titulo_secao("Cockpit de Decisão Executiva",
        "Tudo que você precisa saber em 30 segundos"), unsafe_allow_html=True)

    conn = get_conn()
    dre_r = conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?", (mes_sel, ano_sel)).fetchone()
    salas_r = pd.read_sql("SELECT * FROM salas WHERE mes=? AND ano=?", conn, params=(mes_sel, ano_sel))
    leads_r = conn.execute("""SELECT COUNT(*) as tot, SUM(convertido) as conv,
        SUM(ticket_proposto) as pipeline FROM leads WHERE mes=? AND ano=?""",
        (mes_sel, ano_sel)).fetchone()
    clin_r = conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    tarefas_r = pd.read_sql("SELECT * FROM mod_tarefas WHERE ativo=1", conn)
    exec_hoje = conn.execute("""SELECT COUNT(*) as tot, SUM(concluida) as ok
        FROM mod_execucao WHERE data_execucao=?""",
        (date.today().isoformat(),)).fetchone()
    conn.close()

    # Cálculos DRE
    rb = sum([(dre_r[i] or 0) for i in [3,4,5,6]]) if dre_r else 0
    imp = dre_r[7] if dre_r else 8.5
    taxa_c = dre_r[8] if dre_r else 3.0
    insumos = dre_r[9] if dre_r else 0
    pessoal = dre_r[10] if dre_r else 0
    ocupacao = dre_r[11] if dre_r else 0
    mkt = dre_r[12] if dre_r else 0
    outros = dre_r[13] if dre_r else 0

    deducoes = rb * (imp + taxa_c) / 100
    rl = rb - deducoes
    margem_contrib = rl - insumos
    custos_fixos = pessoal + ocupacao + mkt + outros
    ebitda = margem_contrib - custos_fixos
    margem_ebitda = pct_safe(ebitda, rb)

    perda_noshow = float(salas_r['perda_noshow'].sum()) if not salas_r.empty else 0.0
    meta_fat = clin_r[2] if clin_r else 0
    custo_fixo_total = clin_r[3] if clin_r else custos_fixos or 1
    prog_be = pct_safe(rb, custo_fixo_total)

    l_tot = leads_r[0] if leads_r else 0
    l_conv = leads_r[1] if leads_r else 0
    pipeline = leads_r[2] if leads_r else 0

    tarefas_peso = tarefas_r['peso_pct'].sum() if not tarefas_r.empty else 0
    exec_peso = 0
    if not tarefas_r.empty and exec_hoje and exec_hoje[0]:
        exec_peso = min(int(exec_hoje[1] or 0) / max(len(tarefas_r), 1) * 100, 100)
    score_mod = round(exec_peso, 1)

    # KPIs linha 1
    st.markdown(f"""
    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px;margin-bottom:20px">
        <div style="background:{CARD};border-radius:12px;padding:18px 20px;
                    border:1px solid rgba(200,150,60,0.25)">
            <div style="font-size:10px;color:#A3A8B4;text-transform:uppercase;letter-spacing:1.5px">
                Receita Realizada
            </div>
            <div style="font-size:2rem;font-weight:800;color:{GREEN};font-family:Georgia,serif;margin:6px 0">
                {fmt(rb)}
            </div>
            <div style="font-size:11px;color:#A3A8B4">{pct_safe(rb, meta_fat):.0f}% da meta mensal</div>
        </div>
        <div style="background:{CARD};border-radius:12px;padding:18px 20px;
                    border:1px solid rgba(200,150,60,0.25)">
            <div style="font-size:10px;color:#A3A8B4;text-transform:uppercase;letter-spacing:1.5px">
                EBITDA Operacional
            </div>
            <div style="font-size:2rem;font-weight:800;color:{''+GREEN if ebitda>0 else RED};font-family:Georgia,serif;margin:6px 0">
                {fmt(ebitda)}
            </div>
            <div style="font-size:11px;color:#A3A8B4">{margem_ebitda:.1f}% de margem EBITDA</div>
        </div>
        <div style="background:{CARD};border-radius:12px;padding:18px 20px;
                    border:1px solid rgba(228,82,82,0.35)">
            <div style="font-size:10px;color:#A3A8B4;text-transform:uppercase;letter-spacing:1.5px">
                Prejuízo Oculto (No-Show)
            </div>
            <div style="font-size:2rem;font-weight:800;color:{RED};font-family:Georgia,serif;margin:6px 0">
                {fmt(perda_noshow)}
            </div>
            <div style="font-size:11px;color:#A3A8B4">Faturamento que saiu pela porta</div>
        </div>
        <div style="background:{CARD};border-radius:12px;padding:18px 20px;
                    border:1px solid rgba(200,150,60,0.25)">
            <div style="font-size:10px;color:#A3A8B4;text-transform:uppercase;letter-spacing:1.5px">
                Score MOD da Equipe
            </div>
            <div style="font-size:2rem;font-weight:800;color:{''+GREEN if score_mod>=85 else RED};font-family:Georgia,serif;margin:6px 0">
                {score_mod:.1f}%
            </div>
            <div style="font-size:11px;color:#A3A8B4">Meta: acima de 85%</div>
        </div>
    </div>""", unsafe_allow_html=True)

    col_esq, col_dir = st.columns([3,2])

    with col_esq:
        st.markdown(f"<div style='color:{IVORY};font-weight:700;margin-bottom:10px'>Faturamento por Prescritor</div>", unsafe_allow_html=True)
        conn = get_conn()
        leads_df = pd.read_sql("SELECT * FROM leads WHERE mes=? AND ano=?", conn, params=(mes_sel, ano_sel))
        conn.close()
        if not leads_df.empty and 'sdr_nome' in leads_df.columns:
            fat_sdr = leads_df[leads_df['convertido']==1].groupby('sdr_nome')['ticket_proposto'].sum()
            if not fat_sdr.empty:
                st.bar_chart(fat_sdr)
            else:
                st.info("Lance leads convertidos com ticket para ver o gráfico por prescritor.")
        else:
            st.info("Sem dados de leads neste período.")

        # Termômetro Break-Even
        st.markdown(f"<div style='color:{IVORY};font-weight:700;margin:16px 0 8px'>Termômetro Ponto de Equilíbrio</div>", unsafe_allow_html=True)
        st.progress(min(prog_be/100, 1.0), text=f"Progresso: {prog_be:.1f}%")
        if rb >= custo_fixo_total:
            st.success(f"Break-Even batido! Operando em lucro real de {fmt(ebitda)}")
        else:
            st.warning(f"Faltam {fmt(custo_fixo_total - rb)} para pagar os custos fixos.")

    with col_dir:
        st.markdown(f"<div style='color:{IVORY};font-weight:700;margin-bottom:10px'>DRE Rápido</div>", unsafe_allow_html=True)
        linhas_dre = [
            ("Receita Bruta", rb, GREEN, False),
            (f"Impostos + Taxas ({imp+taxa_c:.1f}%)", deducoes, RED, False),
            ("Receita Líquida", rl, IVORY, False),
            ("Insumos Médicos", insumos, RED, False),
            ("Margem de Contribuição", margem_contrib, GOLD, False),
            ("Custos Fixos", custos_fixos, RED, False),
            ("EBITDA OPERACIONAL", ebitda, GREEN if ebitda>0 else RED, True),
        ]
        for label_d, val_d, cor_d, dest in linhas_dre:
            bg_d = NAVY if dest else CARD
            bd = f"2px solid {GOLD}" if dest else f"1px solid rgba(200,150,60,0.15)"
            st.markdown(f"""
            <div style="background:{bg_d};border-radius:8px;padding:9px 14px;margin-bottom:4px;
                        border:{bd};display:flex;justify-content:space-between;align-items:center">
                <span style="font-size:12px;color:{'#ccc' if dest else '#A3A8B4'}">{label_d}</span>
                <span style="font-size:{'15' if dest else '13'}px;font-weight:{'800' if dest else '600'};
                             color:{cor_d}">{fmt(val_d)}</span>
            </div>""", unsafe_allow_html=True)

        st.markdown(f"<div style='color:{IVORY};font-weight:700;margin:16px 0 8px'>Pipeline Comercial</div>", unsafe_allow_html=True)
        st.markdown(f"""
        <div style="background:{MID};border-radius:10px;padding:14px">
            <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                <span style="color:#A3A8B4;font-size:12px">Leads totais</span>
                <span style="color:{IVORY};font-weight:700">{l_tot}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                <span style="color:#A3A8B4;font-size:12px">Convertidos</span>
                <span style="color:{GREEN};font-weight:700">{int(l_conv or 0)}</span>
            </div>
            <div style="display:flex;justify-content:space-between">
                <span style="color:#A3A8B4;font-size:12px">Pipeline aberto</span>
                <span style="color:{GOLD};font-weight:700">{fmt(pipeline)}</span>
            </div>
        </div>""", unsafe_allow_html=True)



# ══════════════════════════════════════════════════════════════
# BRIEFING — ABERTURA DO DIA
# ══════════════════════════════════════════════════════════════
elif aba == "☀️  Briefing — Abertura do Dia":
    from datetime import date as _date
    hoje_str = _date.today().isoformat()
    hoje_fmt = _date.today().strftime("%d/%m/%Y")

    st.markdown(titulo_secao(f"Briefing de Abertura — {hoje_fmt}",
        "Rituais de 10 minutos. Agenda, oportunidades e prioridades do dia definidas antes do primeiro atendimento."),
        unsafe_allow_html=True)

    conn = get_conn()
    bf = conn.execute("SELECT * FROM briefing WHERE data=?", (hoje_str,)).fetchone()
    dre_bf = conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?", (mes_sel, ano_sel)).fetchone()
    clin_bf = conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    db_ontem = conn.execute("SELECT * FROM debriefing WHERE data=?",
        ((_date.today() - __import__("datetime").timedelta(days=1)).isoformat(),)).fetchone()
    conn.close()

    meta_mensal = clin_bf[2] if clin_bf else 0
    rb_mes = sum([(dre_bf[i] or 0) for i in [3,4,5,6]]) if dre_bf else 0
    dias_uteis_passados = _date.today().day
    meta_dia = (meta_mensal / 22) if meta_mensal else 0
    falta_meta = max(meta_mensal - rb_mes, 0)

    # Resumo do dia anterior
    if db_ontem:
        rec_ontem = (db_ontem[3] or 0) + (db_ontem[4] or 0) + (db_ontem[5] or 0) + (db_ontem[6] or 0)
        st.markdown(f"""
        <div style="background:{MID};border-radius:10px;padding:14px 20px;
                    margin-bottom:20px;border-left:3px solid {GOLD}">
            <div style="color:{GOLD};font-size:10px;font-weight:700;letter-spacing:1px;
                        text-transform:uppercase;margin-bottom:8px">ONTEM — RESUMO RÁPIDO</div>
            <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;font-size:12px">
                <div><span style="color:#A3A8B4">Receita</span><br>
                    <strong style="color:{IVORY}">{fmt(rec_ontem)}</strong></div>
                <div><span style="color:#A3A8B4">Consultas</span><br>
                    <strong style="color:{IVORY}">{db_ontem[11] or 0}</strong></div>
                <div><span style="color:#A3A8B4">No-shows</span><br>
                    <strong style="color:{RED}">{db_ontem[13] or 0}</strong></div>
                <div><span style="color:#A3A8B4">Leads resp.</span><br>
                    <strong style="color:{IVORY}">{db_ontem[16] or 0}</strong></div>
                <div><span style="color:#A3A8B4">Ação de hoje</span><br>
                    <strong style="color:{GOLD}">{db_ontem[30] or "—"}</strong></div>
            </div>
        </div>""", unsafe_allow_html=True)

    # Barra da meta mensal
    p_meta = pct_safe(rb_mes, meta_mensal)
    _, cor_meta = semaforo(p_meta, 80)
    st.markdown(barra(p_meta, f"Meta mensal: {fmt(rb_mes)} de {fmt(meta_mensal)} — falta {fmt(falta_meta)}", cor_meta),
        unsafe_allow_html=True)
    st.markdown("---")

    with st.form("form_briefing"):
        st.markdown(f"""<div style="color:{GOLD};font-weight:700;font-size:13px;
            letter-spacing:1px;text-transform:uppercase;margin-bottom:14px">
            ☀️ BRIEFING — {hoje_fmt}</div>""", unsafe_allow_html=True)

        resp_bf = st.text_input("Responsável pelo briefing (DRI)",
            value=bf[2] if bf else "", placeholder="Nome de quem conduz")

        # BLOCO 1 — AGENDA
        st.markdown(f"<div style='color:{GOLD};font-weight:700;margin:16px 0 10px'>01 — AGENDA DO DIA</div>",
            unsafe_allow_html=True)
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: cons_ag = st.number_input("Consultas agendadas", value=int(bf[3] if bf else 0), min_value=0)
        with c2: proc_ag = st.number_input("Procedimentos agendados", value=int(bf[4] if bf else 0), min_value=0)
        with c3: conf_r  = st.number_input("Confirmações realizadas", value=int(bf[5] if bf else 0), min_value=0)
        with c4: gaps    = st.number_input("Gaps na agenda (vazios)", value=int(bf[6] if bf else 0), min_value=0)
        with c5: val_ag  = st.number_input("Valor projetado da agenda (R$)", value=float(bf[7] if bf else 0), step=100.0)

        # BLOCO 2 — OPORTUNIDADES COMERCIAIS
        st.markdown(f"<div style='color:{GOLD};font-weight:700;margin:16px 0 10px'>02 — OPORTUNIDADES COMERCIAIS</div>",
            unsafe_allow_html=True)
        c1,c2,c3,c4,c5,c6 = st.columns(6)
        with c1: leads_p   = st.number_input("Leads pendentes", value=int(bf[8] if bf else 0), min_value=0)
        with c2: orc_ab    = st.number_input("Orçamentos abertos", value=int(bf[9] if bf else 0), min_value=0)
        with c3: val_orc   = st.number_input("Valor em aberto (R$)", value=float(bf[10] if bf else 0), step=100.0)
        with c4: rfm_m     = st.number_input("Meta RFM hoje", value=int(bf[11] if bf else 30), min_value=0)
        with c5: ind_m     = st.number_input("Meta indicações hoje", value=int(bf[12] if bf else 5), min_value=0)
        with c6: ret_hoje  = st.number_input("Pacientes em retorno", value=int(bf[13] if bf else 0), min_value=0)

        # BLOCO 3 — RÉGUA DO DIA
        st.markdown(f"<div style='color:{GOLD};font-weight:700;margin:16px 0 10px'>03 — RÉGUA D-1 / D+1 E FOLLOW-UP</div>",
            unsafe_allow_html=True)
        c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
        with c1: dm1_pc  = st.number_input("D-1 Prim. Consulta", value=int(bf[14] if bf else 0), min_value=0)
        with c2: dm1_rt  = st.number_input("D-1 Retorno", value=int(bf[15] if bf else 0), min_value=0)
        with c3: dp1_pc  = st.number_input("D+1 Prim. Consulta", value=int(bf[16] if bf else 0), min_value=0)
        with c4: dp1_rt  = st.number_input("D+1 Retorno", value=int(bf[17] if bf else 0), min_value=0)
        with c5: fw_d3   = st.number_input("Follow D+3", value=int(bf[18] if bf else 0), min_value=0)
        with c6: fw_d7   = st.number_input("Follow D+7", value=int(bf[19] if bf else 0), min_value=0)
        with c7: fw_d14  = st.number_input("Follow D+14", value=int(bf[20] if bf else 0), min_value=0)

        total_contatos = dm1_pc + dm1_rt + dp1_pc + dp1_rt + fw_d3 + fw_d7 + fw_d14
        st.markdown(f"""<div style="background:{MID};border-radius:8px;padding:10px 14px;
            display:flex;justify-content:space-between;align-items:center;margin-top:4px">
            <span style="color:#A3A8B4;font-size:12px">Total de contatos planejados hoje</span>
            <span style="color:{GOLD};font-size:18px;font-weight:800">{total_contatos} contatos</span>
        </div>""", unsafe_allow_html=True)

        # BLOCO 4 — PRIORIDADES COM DRI
        st.markdown(f"<div style='color:{GOLD};font-weight:700;margin:16px 0 10px'>04 — PRIORIDADES DO DIA (AME)</div>",
            unsafe_allow_html=True)
        c1, c2 = st.columns([3,1])
        with c1: pr1 = st.text_input("Prioridade 1", value=bf[21] if bf else "", placeholder="Ação principal do dia")
        with c2: dr1 = st.text_input("DRI 1", value=bf[24] if bf else "")
        c1, c2 = st.columns([3,1])
        with c1: pr2 = st.text_input("Prioridade 2", value=bf[22] if bf else "", placeholder="Segunda ação")
        with c2: dr2 = st.text_input("DRI 2", value=bf[25] if bf else "")
        c1, c2 = st.columns([3,1])
        with c1: pr3 = st.text_input("Prioridade 3", value=bf[23] if bf else "", placeholder="Terceira ação")
        with c2: dr3 = st.text_input("DRI 3", value=bf[26] if bf else "")

        obs_bf = st.text_area("Observações do briefing", value=bf[27] if bf else "",
            placeholder="Alertas, contextos especiais, decisões tomadas...", height=70)

        if st.form_submit_button("✅ Registrar Briefing", use_container_width=True):
            conn = get_conn()
            conn.execute("""
                INSERT INTO briefing (data, responsavel, consultas_agendadas, procedimentos_agendados,
                    confirmacoes_realizadas, gaps_agenda, valor_agenda_dia,
                    leads_pendentes, orcamentos_abertos, valor_orcamentos_abertos,
                    rfm_contatos_meta, indicacoes_meta, pacientes_retorno_hoje,
                    dm1_primeira_consulta, dm1_retorno, dp1_primeira_consulta, dp1_retorno,
                    follow_d3, follow_d7, follow_d14,
                    prioridade_1, prioridade_2, prioridade_3,
                    dri_prioridade_1, dri_prioridade_2, dri_prioridade_3, obs_briefing)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(data) DO UPDATE SET
                    responsavel=excluded.responsavel,
                    consultas_agendadas=excluded.consultas_agendadas,
                    procedimentos_agendados=excluded.procedimentos_agendados,
                    confirmacoes_realizadas=excluded.confirmacoes_realizadas,
                    gaps_agenda=excluded.gaps_agenda, valor_agenda_dia=excluded.valor_agenda_dia,
                    leads_pendentes=excluded.leads_pendentes,
                    orcamentos_abertos=excluded.orcamentos_abertos,
                    valor_orcamentos_abertos=excluded.valor_orcamentos_abertos,
                    rfm_contatos_meta=excluded.rfm_contatos_meta,
                    indicacoes_meta=excluded.indicacoes_meta,
                    pacientes_retorno_hoje=excluded.pacientes_retorno_hoje,
                    dm1_primeira_consulta=excluded.dm1_primeira_consulta,
                    dm1_retorno=excluded.dm1_retorno,
                    dp1_primeira_consulta=excluded.dp1_primeira_consulta,
                    dp1_retorno=excluded.dp1_retorno,
                    follow_d3=excluded.follow_d3, follow_d7=excluded.follow_d7,
                    follow_d14=excluded.follow_d14,
                    prioridade_1=excluded.prioridade_1, prioridade_2=excluded.prioridade_2,
                    prioridade_3=excluded.prioridade_3,
                    dri_prioridade_1=excluded.dri_prioridade_1,
                    dri_prioridade_2=excluded.dri_prioridade_2,
                    dri_prioridade_3=excluded.dri_prioridade_3,
                    obs_briefing=excluded.obs_briefing
            """, (hoje_str, resp_bf, cons_ag, proc_ag, conf_r, gaps, val_ag,
                  leads_p, orc_ab, val_orc, rfm_m, ind_m, ret_hoje,
                  dm1_pc, dm1_rt, dp1_pc, dp1_rt, fw_d3, fw_d7, fw_d14,
                  pr1, pr2, pr3, dr1, dr2, dr3, obs_bf))
            conn.commit(); conn.close()
            st.success("Briefing registrado!"); st.rerun()

    # Painel visual do briefing registrado
    if bf:
        st.markdown("---")
        st.markdown(f"""
        <div style="background:{NAVY};border-radius:12px;padding:20px 24px;
                    border:1px solid rgba(200,150,60,0.3)">
            <div style="color:{GOLD};font-size:11px;font-weight:700;
                        letter-spacing:2px;text-transform:uppercase;margin-bottom:14px">
                PAINEL DO DIA — {hoje_fmt}
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">

                <div>
                    <div style="color:#A3A8B4;font-size:10px;text-transform:uppercase;
                                letter-spacing:1px;margin-bottom:8px">Agenda</div>
                    <div style="background:{MID};border-radius:8px;padding:12px;font-size:12px;line-height:2">
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:#A3A8B4">Consultas</span>
                            <strong style="color:{IVORY}">{bf[3]}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:#A3A8B4">Procedimentos</span>
                            <strong style="color:{IVORY}">{bf[4]}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:#A3A8B4">Confirmações</span>
                            <strong style="color:{GREEN}">{bf[5]}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:#A3A8B4">Gaps</span>
                            <strong style="color:{RED if (bf[6] or 0)>0 else IVORY}">{bf[6]}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:#A3A8B4">Valor projetado</span>
                            <strong style="color:{GOLD}">{fmt(bf[7])}</strong>
                        </div>
                    </div>
                </div>

                <div>
                    <div style="color:#A3A8B4;font-size:10px;text-transform:uppercase;
                                letter-spacing:1px;margin-bottom:8px">Oportunidades</div>
                    <div style="background:{MID};border-radius:8px;padding:12px;font-size:12px;line-height:2">
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:#A3A8B4">Leads pendentes</span>
                            <strong style="color:{RED if (bf[8] or 0)>0 else IVORY}">{bf[8]}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:#A3A8B4">Orçamentos abertos</span>
                            <strong style="color:{GOLD}">{bf[9]}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:#A3A8B4">Valor em pipeline</span>
                            <strong style="color:{GOLD}">{fmt(bf[10])}</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:#A3A8B4">Meta RFM</span>
                            <strong style="color:{IVORY}">{bf[11]} contatos</strong>
                        </div>
                        <div style="display:flex;justify-content:space-between">
                            <span style="color:#A3A8B4">Meta indicações</span>
                            <strong style="color:{IVORY}">{bf[12]} pedidos</strong>
                        </div>
                    </div>
                </div>

                <div>
                    <div style="color:#A3A8B4;font-size:10px;text-transform:uppercase;
                                letter-spacing:1px;margin-bottom:8px">Prioridades AME</div>
                    <div style="background:{MID};border-radius:8px;padding:12px;font-size:12px">
                        {f'''<div style="display:flex;gap:8px;margin-bottom:8px;align-items:flex-start">
                            <div style="width:20px;height:20px;background:{GOLD};border-radius:50%;
                                        display:flex;align-items:center;justify-content:center;
                                        color:{NAVY};font-weight:800;font-size:10px;flex-shrink:0">1</div>
                            <div>
                                <div style="color:{IVORY};font-weight:600">{bf[21] or "—"}</div>
                                <div style="color:#A3A8B4;font-size:10px">DRI: {bf[24] or "—"}</div>
                            </div>
                        </div>''' if bf[21] else ""}
                        {f'''<div style="display:flex;gap:8px;margin-bottom:8px;align-items:flex-start">
                            <div style="width:20px;height:20px;background:{GOLD}88;border-radius:50%;
                                        display:flex;align-items:center;justify-content:center;
                                        color:{NAVY};font-weight:800;font-size:10px;flex-shrink:0">2</div>
                            <div>
                                <div style="color:{IVORY};font-weight:600">{bf[22] or "—"}</div>
                                <div style="color:#A3A8B4;font-size:10px">DRI: {bf[25] or "—"}</div>
                            </div>
                        </div>''' if bf[22] else ""}
                        {f'''<div style="display:flex;gap:8px;align-items:flex-start">
                            <div style="width:20px;height:20px;background:{GOLD}44;border-radius:50%;
                                        display:flex;align-items:center;justify-content:center;
                                        color:{NAVY};font-weight:800;font-size:10px;flex-shrink:0">3</div>
                            <div>
                                <div style="color:{IVORY};font-weight:600">{bf[23] or "—"}</div>
                                <div style="color:#A3A8B4;font-size:10px">DRI: {bf[26] or "—"}</div>
                            </div>
                        </div>''' if bf[23] else ""}
                    </div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Histórico dos últimos 7 dias
    st.markdown("---")
    st.markdown(f"<div style='color:{IVORY};font-weight:700;margin-bottom:10px'>Últimos 7 Briefings</div>",
        unsafe_allow_html=True)
    conn = get_conn()
    hist_bf = pd.read_sql("""SELECT data, responsavel, consultas_agendadas, procedimentos_agendados,
        gaps_agenda, valor_agenda_dia, orcamentos_abertos, valor_orcamentos_abertos, prioridade_1
        FROM briefing ORDER BY data DESC LIMIT 7""", conn)
    conn.close()
    if not hist_bf.empty:
        hist_bf.columns = ["Data","DRI","Consultas","Proced.","Gaps","Valor Agenda","Orç. Abertos","Valor Pipeline","Prioridade 1"]
        hist_bf["Valor Agenda"] = hist_bf["Valor Agenda"].apply(fmt)
        hist_bf["Valor Pipeline"] = hist_bf["Valor Pipeline"].apply(fmt)
        st.dataframe(hist_bf, hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum briefing registrado ainda.")


# ══════════════════════════════════════════════════════════════
# DEBRIEFING — FECHAMENTO DO DIA
# ══════════════════════════════════════════════════════════════
elif aba == "🌙  Debriefing — Fechamento do Dia":
    from datetime import date as _date
    hoje_str = _date.today().isoformat()
    hoje_fmt = _date.today().strftime("%d/%m/%Y")

    st.markdown(titulo_secao(f"Debriefing de Fechamento — {hoje_fmt}",
        "Caixa do dia, agenda realizada e ações comerciais concretizadas. Feche o dia com clareza."),
        unsafe_allow_html=True)

    conn = get_conn()
    db   = conn.execute("SELECT * FROM debriefing WHERE data=?", (hoje_str,)).fetchone()
    bf_h = conn.execute("SELECT * FROM briefing WHERE data=?", (hoje_str,)).fetchone()
    dre_db = conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?", (mes_sel, ano_sel)).fetchone()
    clin_db = conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    conn.close()

    meta_mensal = clin_db[2] if clin_db else 0
    meta_dia = meta_mensal / 22 if meta_mensal else 0

    # Painel de comparação planejado vs realizado
    if bf_h:
        st.markdown(f"""
        <div style="background:{MID};border-radius:10px;padding:14px 20px;
                    margin-bottom:20px;border-left:3px solid {GOLD}">
            <div style="color:{GOLD};font-size:10px;font-weight:700;letter-spacing:1px;
                        text-transform:uppercase;margin-bottom:10px">
                PLANEJADO NO BRIEFING × REALIZADO
            </div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;font-size:12px">
                <div>
                    <div style="color:#A3A8B4">Consultas planejadas</div>
                    <div style="color:{GOLD};font-size:18px;font-weight:800">{bf_h[3] or 0}</div>
                </div>
                <div>
                    <div style="color:#A3A8B4">Procedimentos planejados</div>
                    <div style="color:{GOLD};font-size:18px;font-weight:800">{bf_h[4] or 0}</div>
                </div>
                <div>
                    <div style="color:#A3A8B4">Valor projetado</div>
                    <div style="color:{GOLD};font-size:18px;font-weight:800">{fmt(bf_h[7])}</div>
                </div>
                <div>
                    <div style="color:#A3A8B4">Prioridade 1</div>
                    <div style="color:{IVORY};font-size:13px;font-weight:700">{bf_h[21] or "não definida"}</div>
                </div>
            </div>
        </div>""", unsafe_allow_html=True)

    with st.form("form_debriefing"):
        st.markdown(f"""<div style="color:{GOLD};font-weight:700;font-size:13px;
            letter-spacing:1px;text-transform:uppercase;margin-bottom:14px">
            🌙 DEBRIEFING — {hoje_fmt}</div>""", unsafe_allow_html=True)

        resp_db = st.text_input("Responsável pelo fechamento (DRI)",
            value=db[2] if db else "", placeholder="Nome de quem fecha o dia")

        # BLOCO 1 — CAIXA DO DIA
        st.markdown(f"<div style='color:{GOLD};font-weight:700;margin:16px 0 10px'>01 — CAIXA DO DIA</div>",
            unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        with c1: rc_db  = st.number_input("Receita Consultas (R$)", value=float(db[3] if db else 0), step=100.0)
        with c2: rp_db  = st.number_input("Receita Procedimentos (R$)", value=float(db[4] if db else 0), step=100.0)
        with c3: rr_db  = st.number_input("Recorrência / LTV (R$)", value=float(db[5] if db else 0), step=100.0)
        with c4: ro_db  = st.number_input("Outros (R$)", value=float(db[6] if db else 0), step=100.0)

        receita_total_dia = rc_db + rp_db + rr_db + ro_db
        st.markdown(f"""<div style="background:{MID};border-radius:8px;padding:10px 16px;
            display:flex;justify-content:space-between;margin:4px 0 12px">
            <span style="color:#A3A8B4;font-size:12px">Receita total do dia</span>
            <span style="color:{GREEN if receita_total_dia >= meta_dia else RED};
                         font-size:20px;font-weight:800">{fmt(receita_total_dia)}</span>
        </div>""", unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        with c1: di_db  = st.number_input("Despesas Insumos (R$)", value=float(db[7] if db else 0), step=10.0)
        with c2: do_db  = st.number_input("Despesas Operacionais (R$)", value=float(db[8] if db else 0), step=10.0)
        with c3: da_db  = st.number_input("Outras Despesas (R$)", value=float(db[9] if db else 0), step=10.0)

        total_desp = di_db + do_db + da_db
        saldo_dia  = receita_total_dia - total_desp
        st.markdown(f"""<div style="background:{NAVY};border-radius:8px;padding:10px 16px;
            display:flex;justify-content:space-between;align-items:center;margin:4px 0 12px;
            border:1px solid rgba(200,150,60,0.2)">
            <div>
                <span style="color:#A3A8B4;font-size:12px">Despesas: </span>
                <span style="color:{RED};font-weight:700">{fmt(total_desp)}</span>
                <span style="color:#A3A8B4;font-size:12px;margin-left:16px">Saldo líquido do dia: </span>
                <span style="color:{GREEN if saldo_dia>=0 else RED};font-size:18px;font-weight:800">{fmt(saldo_dia)}</span>
            </div>
            <div style="color:{GREEN if receita_total_dia>=meta_dia else RED};font-size:11px;font-weight:700">
                {f"✅ Meta diária batida ({fmt(meta_dia)})" if receita_total_dia>=meta_dia else f"⚠️ Abaixo da meta diária ({fmt(meta_dia)})"}
            </div>
        </div>""", unsafe_allow_html=True)

        # BLOCO 2 — AGENDA REALIZADA
        st.markdown(f"<div style='color:{GOLD};font-weight:700;margin:16px 0 10px'>02 — AGENDA REALIZADA</div>",
            unsafe_allow_html=True)
        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: cons_r  = st.number_input("Consultas realizadas", value=int(db[11] if db else 0), min_value=0)
        with c2: proc_r  = st.number_input("Procedimentos realizados", value=int(db[12] if db else 0), min_value=0)
        with c3: ns_db   = st.number_input("No-shows", value=int(db[13] if db else 0), min_value=0)
        with c4: canc_db = st.number_input("Cancelamentos", value=int(db[14] if db else 0), min_value=0)
        with c5: perda_db= st.number_input("Perda no-show (R$)", value=float(db[15] if db else 0), step=100.0)

        if bf_h:
            cons_plan = bf_h[3] or 0
            delta_cons = cons_r - cons_plan
            cor_dc = GREEN if delta_cons >= 0 else RED
            st.markdown(f"""<div style="background:{MID};border-radius:8px;padding:8px 14px;
                display:flex;gap:20px;font-size:12px;margin-top:4px">
                <span style="color:#A3A8B4">Planejado: <strong style="color:{GOLD}">{cons_plan} consultas</strong></span>
                <span style="color:#A3A8B4">Realizado: <strong style="color:{IVORY}">{cons_r} consultas</strong></span>
                <span style="color:#A3A8B4">Variação: <strong style="color:{cor_dc}">{"+"+str(delta_cons) if delta_cons>=0 else delta_cons}</strong></span>
            </div>""", unsafe_allow_html=True)

        # BLOCO 3 — COMERCIAL REALIZADO
        st.markdown(f"<div style='color:{GOLD};font-weight:700;margin:16px 0 10px'>03 — AÇÕES COMERCIAIS REALIZADAS</div>",
            unsafe_allow_html=True)
        c1,c2,c3,c4 = st.columns(4)
        with c1: lr_db  = st.number_input("Leads respondidos", value=int(db[16] if db else 0), min_value=0)
        with c2: trm_db = st.number_input("Tempo resp. médio (min)", value=int(db[17] if db else 0), min_value=0)
        with c3: ag_db  = st.number_input("Agendamentos gerados", value=int(db[18] if db else 0), min_value=0)
        with c4: of_db  = st.number_input("Orçamentos fechados", value=int(db[19] if db else 0), min_value=0)

        c1,c2,c3,c4,c5 = st.columns(5)
        with c1: vof_db = st.number_input("Valor fechado (R$)", value=float(db[20] if db else 0), step=100.0)
        with c2: rfm_db = st.number_input("Contatos RFM", value=int(db[21] if db else 0), min_value=0)
        with c3: ind_s  = st.number_input("Indicações solicitadas", value=int(db[22] if db else 0), min_value=0)
        with c4: ind_r  = st.number_input("Indicações recebidas", value=int(db[23] if db else 0), min_value=0)
        with c5: av_db  = st.number_input("Avaliações Google", value=int(db[24] if db else 0), min_value=0)

        # Semáforos comerciais
        rfm_meta = bf_h[11] if bf_h else 30
        ind_meta = bf_h[12] if bf_h else 5
        col_sem = st.columns(5)
        indicadores_sem = [
            ("RFM", rfm_db, rfm_meta),
            ("Indicações", ind_s, ind_meta),
            ("Avaliações Google", av_db, 5),
            ("Resp < 5min", 100 if trm_db <= 5 else 0, 100),
            ("Agendamentos", ag_db, 2),
        ]
        for col_s, (label_s, val_s, meta_s) in zip(col_sem, indicadores_sem):
            p_s = pct_safe(val_s, meta_s)
            em_s, cor_s = semaforo(p_s)
            with col_s:
                st.markdown(f"""<div style="background:{MID};border-radius:8px;padding:10px;
                    text-align:center;font-size:11px">
                    <div style="color:#A3A8B4">{label_s}</div>
                    <div style="font-size:20px">{em_s}</div>
                    <div style="color:{cor_s};font-weight:700">{val_s}/{meta_s}</div>
                </div>""", unsafe_allow_html=True)

        # BLOCO 4 — RÉGUA EXECUTADA
        st.markdown(f"<div style='color:{GOLD};font-weight:700;margin:16px 0 10px'>04 — RÉGUA D-1 / D+1 EXECUTADA</div>",
            unsafe_allow_html=True)
        c1,c2,c3 = st.columns(3)
        with c1: dm1_ex = st.number_input("D-1 executados", value=int(db[25] if db else 0), min_value=0)
        with c2: dp1_ex = st.number_input("D+1 executados", value=int(db[26] if db else 0), min_value=0)
        with c3: fw_ex  = st.number_input("Follow-ups executados", value=int(db[27] if db else 0), min_value=0)

        # BLOCO 5 — ANÁLISE DO DIA
        st.markdown(f"<div style='color:{GOLD};font-weight:700;margin:16px 0 10px'>05 — ANÁLISE E PRÓXIMO DIA</div>",
            unsafe_allow_html=True)
        meta_bat = st.checkbox("Meta diária batida?", value=bool(db[28] if db else receita_total_dia >= meta_dia))
        c1, c2 = st.columns(2)
        with c1:
            conquista = st.text_input("Principal conquista do dia",
                value=db[29] if db else "", placeholder="O que funcionou bem?")
        with c2:
            gargalo = st.text_input("Principal gargalo do dia",
                value=db[30] if db else "", placeholder="O que travar ou desperdiçou?")
        c1, c2 = st.columns([3,1])
        with c1: acao_am = st.text_input("Ação prioritária de amanhã",
            value=db[31] if db else "", placeholder="Já defina o próximo passo")
        with c2: dri_am  = st.text_input("DRI de amanhã",
            value=db[32] if db else "")
        obs_db = st.text_area("Observações do fechamento",
            value=db[33] if db else "", height=60,
            placeholder="Contextos, decisões, alertas para o próximo dia...")

        if st.form_submit_button("🌙 Registrar Fechamento do Dia", use_container_width=True):
            conn = get_conn()
            conn.execute("""
                INSERT INTO debriefing (data, responsavel,
                    receita_consultas, receita_procedimentos, receita_recorrencia, receita_outros_dia,
                    despesas_insumos, despesas_operacionais, despesas_outras,
                    consultas_realizadas, procedimentos_realizados, no_show_dia, cancelamentos_dia, perda_noshow_dia,
                    leads_respondidos, tempo_resposta_medio, agendamentos_gerados,
                    orcamentos_fechados, valor_orcamentos_fechados,
                    rfm_contatos_realizados, indicacoes_solicitadas, indicacoes_recebidas, avaliacoes_google,
                    dm1_executados, dp1_executados, follow_executados,
                    meta_dia_batida, principal_conquista, principal_gargalo,
                    acao_amanha, dri_acao_amanha, obs_debriefing)
                VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(data) DO UPDATE SET
                    responsavel=excluded.responsavel,
                    receita_consultas=excluded.receita_consultas,
                    receita_procedimentos=excluded.receita_procedimentos,
                    receita_recorrencia=excluded.receita_recorrencia,
                    receita_outros_dia=excluded.receita_outros_dia,
                    despesas_insumos=excluded.despesas_insumos,
                    despesas_operacionais=excluded.despesas_operacionais,
                    despesas_outras=excluded.despesas_outras,
                    consultas_realizadas=excluded.consultas_realizadas,
                    procedimentos_realizados=excluded.procedimentos_realizados,
                    no_show_dia=excluded.no_show_dia,
                    cancelamentos_dia=excluded.cancelamentos_dia,
                    perda_noshow_dia=excluded.perda_noshow_dia,
                    leads_respondidos=excluded.leads_respondidos,
                    tempo_resposta_medio=excluded.tempo_resposta_medio,
                    agendamentos_gerados=excluded.agendamentos_gerados,
                    orcamentos_fechados=excluded.orcamentos_fechados,
                    valor_orcamentos_fechados=excluded.valor_orcamentos_fechados,
                    rfm_contatos_realizados=excluded.rfm_contatos_realizados,
                    indicacoes_solicitadas=excluded.indicacoes_solicitadas,
                    indicacoes_recebidas=excluded.indicacoes_recebidas,
                    avaliacoes_google=excluded.avaliacoes_google,
                    dm1_executados=excluded.dm1_executados,
                    dp1_executados=excluded.dp1_executados,
                    follow_executados=excluded.follow_executados,
                    meta_dia_batida=excluded.meta_dia_batida,
                    principal_conquista=excluded.principal_conquista,
                    principal_gargalo=excluded.principal_gargalo,
                    acao_amanha=excluded.acao_amanha,
                    dri_acao_amanha=excluded.dri_acao_amanha,
                    obs_debriefing=excluded.obs_debriefing
            """, (hoje_str, resp_db,
                  rc_db, rp_db, rr_db, ro_db,
                  di_db, do_db, da_db,
                  cons_r, proc_r, ns_db, canc_db, perda_db,
                  lr_db, trm_db, ag_db, of_db, vof_db,
                  rfm_db, ind_s, ind_r, av_db,
                  dm1_ex, dp1_ex, fw_ex,
                  1 if meta_bat else 0, conquista, gargalo,
                  acao_am, dri_am, obs_db))

            # Alimenta o DRE mensal automaticamente com os dados do dia
            conn.execute("""
                INSERT INTO dre (mes, ano, receita_consultas, receita_procedimentos,
                    receita_recorrencia, receita_outros, custo_insumos)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                ON CONFLICT(mes, ano) DO UPDATE SET
                    receita_consultas = receita_consultas + ?,
                    receita_procedimentos = receita_procedimentos + ?,
                    receita_recorrencia = receita_recorrencia + ?,
                    receita_outros = receita_outros + ?,
                    custo_insumos = custo_insumos + ?
            """, (mes_sel, ano_sel, rc_db, rp_db, rr_db, ro_db, di_db,
                  rc_db, rp_db, rr_db, ro_db, di_db))

            conn.commit(); conn.close()
            st.success("Fechamento registrado! DRE mensal atualizado automaticamente."); st.rerun()

    # Histórico dos últimos 7 dias
    st.markdown("---")
    st.markdown(f"<div style='color:{IVORY};font-weight:700;margin-bottom:10px'>Últimos 7 Fechamentos</div>",
        unsafe_allow_html=True)
    conn = get_conn()
    hist_db = pd.read_sql("""
        SELECT data, responsavel,
            (receita_consultas+receita_procedimentos+receita_recorrencia+receita_outros_dia) as receita_total,
            (despesas_insumos+despesas_operacionais+despesas_outras) as despesas_total,
            consultas_realizadas, no_show_dia, rfm_contatos_realizados,
            indicacoes_solicitadas, avaliacoes_google, meta_dia_batida,
            principal_conquista, principal_gargalo
        FROM debriefing ORDER BY data DESC LIMIT 7""", conn)
    conn.close()
    if not hist_db.empty:
        hist_db["receita_total"] = hist_db["receita_total"].apply(fmt)
        hist_db["despesas_total"] = hist_db["despesas_total"].apply(fmt)
        hist_db["meta_dia_batida"] = hist_db["meta_dia_batida"].apply(lambda x: "✅" if x else "⚠️")
        hist_db.columns = ["Data","DRI","Receita","Despesas","Consultas","No-show",
                           "RFM","Indicações","Av.Google","Meta","Conquista","Gargalo"]
        st.dataframe(hist_db, hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum debriefing registrado ainda.")


# ══════════════════════════════════════════════════════════════
# 2. PAINEL DNA SEMANAL
# ══════════════════════════════════════════════════════════════
elif aba == "📊  Painel DNA Semanal":
    st.markdown(titulo_secao("Painel de Metas Semanais DNA",
        "Quem sabe o número fecha o número. Preencha toda segunda-feira."), unsafe_allow_html=True)

    semana_atual = f"S{date.today().isocalendar()[1]}"
    conn = get_conn()
    dna_r = conn.execute("SELECT * FROM painel_dna WHERE semana=? AND ano=?",
        (semana_atual, ano_sel)).fetchone()
    clin_r = conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    conn.close()

    meta_mensal = clin_r[2] if clin_r else 0

    with st.expander("✏️ Preencher Painel da Semana", expanded=not bool(dna_r)):
        with st.form("form_dna"):
            st.markdown(f"<div style='color:{GOLD};font-weight:700;margin-bottom:12px'>A LÓGICA QUE MUDA O JOGO</div>", unsafe_allow_html=True)
            c1, c2, c3 = st.columns(3)
            with c1:
                meta_m = st.number_input("Meta Mensal (R$)", value=float(dna_r[4] if dna_r else meta_mensal), step=1000.0)
                realiz = st.number_input("Já realizado no mês (R$)", value=float(dna_r[5] if dna_r else 0), step=100.0)
                dias_r = st.number_input("Dias úteis restantes", value=int(dna_r[6] if dna_r else 5), min_value=1, max_value=25)
            with c2:
                cons_ag  = st.number_input("01 - Consultas agendadas (R$)", value=float(dna_r[7] if dna_r else 0), step=100.0)
                proc_ag  = st.number_input("02 - Procedimentos agendados (R$)", value=float(dna_r[8] if dna_r else 0), step=100.0)
            with c3:
                negoc    = st.number_input("03 - Negociações em aberto (R$)", value=float(dna_r[9] if dna_r else 0), step=100.0)
                orcam    = st.number_input("04 - Orçamentos enviados (R$)", value=float(dna_r[10] if dna_r else 0), step=100.0)

            st.markdown(f"<div style='color:{GOLD};font-weight:700;margin:16px 0 8px'>ACOMPANHAMENTO DIÁRIO</div>", unsafe_allow_html=True)
            dias_cols = st.columns(5)
            dias_nomes = ["SEG","TER","QUA","QUI","SEX"]
            vals_dias = []
            for i, (col_d, dia) in enumerate(zip(dias_cols, dias_nomes)):
                with col_d:
                    st.markdown(f"<div style='color:{IVORY};font-weight:700;text-align:center'>{dia}</div>", unsafe_allow_html=True)
                    base = 11 + (i * 3)
                    c_v = st.number_input(f"Consultas {dia}", value=float(dna_r[base] if dna_r else 0), step=100.0, key=f"c_{dia}", label_visibility="collapsed")
                    p_v = st.number_input(f"Proc {dia}", value=float(dna_r[base+1] if dna_r else 0), step=100.0, key=f"p_{dia}", label_visibility="collapsed")
                    n_v = st.number_input(f"Neg {dia}", value=float(dna_r[base+2] if dna_r else 0), step=100.0, key=f"n_{dia}", label_visibility="collapsed")
                    vals_dias.extend([c_v, p_v, n_v])

            if st.form_submit_button("💾 Salvar Painel da Semana"):
                conn = get_conn()
                conn.execute("""
                    INSERT INTO painel_dna (semana, ano, meta_mensal, realizado_mes, dias_uteis_restantes,
                        consultas_agendadas_val, procedimentos_agendados_val, negociacoes_abertas, orcamentos_enviados,
                        seg_consultas, seg_procedimentos, seg_negociacoes,
                        ter_consultas, ter_procedimentos, ter_negociacoes,
                        qua_consultas, qua_procedimentos, qua_negociacoes,
                        qui_consultas, qui_procedimentos, qui_negociacoes,
                        sex_consultas, sex_procedimentos, sex_negociacoes)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(semana, ano) DO UPDATE SET
                        meta_mensal=excluded.meta_mensal, realizado_mes=excluded.realizado_mes,
                        dias_uteis_restantes=excluded.dias_uteis_restantes,
                        consultas_agendadas_val=excluded.consultas_agendadas_val,
                        procedimentos_agendados_val=excluded.procedimentos_agendados_val,
                        negociacoes_abertas=excluded.negociacoes_abertas,
                        orcamentos_enviados=excluded.orcamentos_enviados,
                        seg_consultas=excluded.seg_consultas, seg_procedimentos=excluded.seg_procedimentos, seg_negociacoes=excluded.seg_negociacoes,
                        ter_consultas=excluded.ter_consultas, ter_procedimentos=excluded.ter_procedimentos, ter_negociacoes=excluded.ter_negociacoes,
                        qua_consultas=excluded.qua_consultas, qua_procedimentos=excluded.qua_procedimentos, qua_negociacoes=excluded.qua_negociacoes,
                        qui_consultas=excluded.qui_consultas, qui_procedimentos=excluded.qui_procedimentos, qui_negociacoes=excluded.qui_negociacoes,
                        sex_consultas=excluded.sex_consultas, sex_procedimentos=excluded.sex_procedimentos, sex_negociacoes=excluded.sex_negociacoes
                """, (semana_atual, ano_sel, meta_m, realiz, dias_r,
                      cons_ag, proc_ag, negoc, orcam, *vals_dias))
                conn.commit(); conn.close()
                st.success("Painel salvo!"); st.rerun()

    if dna_r:
        meta_m  = dna_r[4] or 0
        realiz  = dna_r[5] or 0
        dias_r  = dna_r[6] or 5
        cons_ag = dna_r[7] or 0
        proc_ag = dna_r[8] or 0
        negoc   = dna_r[9] or 0
        orcam   = dna_r[10] or 0

        meta_sem     = meta_m / 4
        total_prev   = cons_ag + proc_ag + negoc + orcam
        falta_buscar = meta_sem - total_prev
        meta_diaria  = max((meta_m - realiz) / max(dias_r, 1), 0)

        st.markdown("---")
        st.markdown(f"<div style='color:{GOLD};font-weight:700;font-size:16px;margin-bottom:14px'>AS 3 PERGUNTAS QUE REVELAM ONDE VOCÊ ESTÁ DE VERDADE</div>", unsafe_allow_html=True)

        c1, c2, c3 = st.columns(3)
        with c1:
            st.markdown(card("01 — Receita travada esta semana", fmt(total_prev),
                "Consultas + Procedimentos + Negociações + Orçamentos", GREEN), unsafe_allow_html=True)
        with c2:
            st.markdown(card("02 — Pode entrar com follow-up hoje", fmt(negoc + orcam),
                "Negociações quentes + Orçamentos sem resposta", GOLD), unsafe_allow_html=True)
        with c3:
            st.markdown(card("03 — Ainda precisa gerar do zero", fmt(max(falta_buscar,0)),
                f"Meta semanal ({fmt(meta_sem)}) menos previsto", RED if falta_buscar > 0 else GREEN, grande=True), unsafe_allow_html=True)

        st.markdown(f"""
        <div style="background:{NAVY};border:2px solid {GOLD};border-radius:14px;
                    padding:22px 28px;text-align:center;margin:16px 0">
            <div style="color:#A3A8B4;font-size:11px;letter-spacing:2px;
                        text-transform:uppercase;margin-bottom:8px">
                O ÚNICO NÚMERO QUE VOCÊ CONTROLA AGORA
            </div>
            <div style="color:{GOLD};font-size:3rem;font-weight:800;font-family:Georgia,serif">
                {fmt(meta_diaria)}
            </div>
            <div style="color:#A3A8B4;font-size:12px;margin-top:6px">
                Meta Diária de Ritmo — {dias_r} dias úteis restantes
            </div>
        </div>""", unsafe_allow_html=True)

        # Tabela diária
        st.markdown(f"<div style='color:{IVORY};font-weight:700;margin:16px 0 8px'>Acompanhamento Diário</div>", unsafe_allow_html=True)
        dias_data = []
        for i, dia in enumerate(["SEG","TER","QUA","QUI","SEX"]):
            base = 11 + (i*3)
            c_v = dna_r[base] or 0
            p_v = dna_r[base+1] or 0
            n_v = dna_r[base+2] or 0
            total_dia = c_v + p_v + n_v
            dias_data.append({"Dia": dia, "Consultas": fmt(c_v), "Procedimentos": fmt(p_v),
                               "Negociações": fmt(n_v), "Total": fmt(total_dia)})
        df_dias = pd.DataFrame(dias_data)
        st.dataframe(df_dias, hide_index=True, use_container_width=True)


# ══════════════════════════════════════════════════════════════
# 3. AUDITORIA DE SALAS
# ══════════════════════════════════════════════════════════════
elif aba == "🏥  Auditoria de Salas":
    st.markdown(titulo_secao("Auditoria de Eficiência das Salas",
        "Inventário de tempo perecível. Hora não vendida não volta."), unsafe_allow_html=True)

    conn = get_conn()
    salas_df = pd.read_sql("SELECT * FROM salas WHERE mes=? AND ano=?", conn, params=(mes_sel, ano_sel))
    conn.close()

    with st.expander("➕ Registrar Ocupação de Sala"):
        with st.form("form_sala"):
            c1,c2,c3 = st.columns(3)
            with c1:
                nome_s   = st.text_input("Nome da sala")
                medico_s = st.text_input("Médico responsável")
            with c2:
                hd_s  = st.number_input("Horas disponíveis/dia", value=8.0, step=0.5)
                ho_s  = st.number_input("Horas ocupadas/dia", value=0.0, step=0.5)
            with c3:
                ns_s  = st.number_input("No-shows hoje", value=0, min_value=0)
                tk_s  = st.number_input("Ticket médio/hora (R$)", value=0.0, step=10.0)
                perda_s = ns_s * tk_s if tk_s else 0
            if st.form_submit_button("Salvar"):
                if nome_s:
                    conn = get_conn()
                    conn.execute("""INSERT INTO salas
                        (nome, medico_responsavel, horas_disponiveis, horas_ocupadas,
                         no_show, perda_noshow, ticket_hora, mes, ano)
                        VALUES (?,?,?,?,?,?,?,?,?)""",
                        (nome_s, medico_s, hd_s, ho_s, ns_s, perda_s, tk_s, mes_sel, ano_sel))
                    conn.commit(); conn.close()
                    st.success("Sala registrada!"); st.rerun()

    if salas_df.empty:
        st.info("Nenhuma sala registrada para este período.")
    else:
        salas_df['tx_ocup'] = (salas_df['horas_ocupadas']/salas_df['horas_disponiveis']*100).round(1)
        salas_df['ociosidade'] = (100 - salas_df['tx_ocup']).round(1)

        for _, s in salas_df.iterrows():
            tx = s['tx_ocup']
            cor_s = GREEN if tx >= 85 else GOLD if tx >= 50 else RED
            alerta = ""
            if tx >= 85:
                alerta = f"⚡ Ocupação crítica: considere subir preço ou contratar médico assistente."
            elif s['ociosidade'] >= 50:
                alerta = f"💡 Alta ociosidade: acionar base inativa (RFM) para protocolos nesta sala."

            st.markdown(f"""
            <div style="background:{CARD};border-radius:12px;padding:18px 22px;
                        border:1px solid rgba(200,150,60,0.2);margin-bottom:14px">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div>
                        <div style="font-weight:700;color:{IVORY};font-size:16px">{s['nome']}</div>
                        <div style="font-size:12px;color:#A3A8B4">
                            {s['medico_responsavel']} · Ticket/hora: {fmt(s['ticket_hora'])}
                        </div>
                    </div>
                    <div style="text-align:right">
                        <div style="font-size:28px;font-weight:800;color:{cor_s}">{tx:.1f}%</div>
                        <div style="font-size:11px;color:#A3A8B4">ocupação</div>
                    </div>
                </div>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0">
                    <div style="background:{MID};padding:10px;border-radius:8px;text-align:center">
                        <div style="font-size:10px;color:#A3A8B4">Disponíveis</div>
                        <div style="font-size:18px;font-weight:800;color:{IVORY}">{s['horas_disponiveis']}h</div>
                    </div>
                    <div style="background:{MID};padding:10px;border-radius:8px;text-align:center">
                        <div style="font-size:10px;color:#A3A8B4">Ocupadas</div>
                        <div style="font-size:18px;font-weight:800;color:{GREEN}">{s['horas_ocupadas']}h</div>
                    </div>
                    <div style="background:{MID};padding:10px;border-radius:8px;text-align:center">
                        <div style="font-size:10px;color:#A3A8B4">No-Shows</div>
                        <div style="font-size:18px;font-weight:800;color:{RED}">{int(s['no_show'])}</div>
                    </div>
                    <div style="background:{MID};padding:10px;border-radius:8px;text-align:center">
                        <div style="font-size:10px;color:#A3A8B4">Perda</div>
                        <div style="font-size:16px;font-weight:800;color:{RED}">{fmt(s['perda_noshow'])}</div>
                    </div>
                </div>
                <div style="height:8px;background:{MID};border-radius:4px;overflow:hidden;margin-bottom:8px">
                    <div style="height:8px;width:{min(int(tx),100)}%;background:{cor_s};border-radius:4px"></div>
                </div>
                {f'<div style="background:{cor_s}22;border-radius:8px;padding:8px 12px;font-size:12px;color:{cor_s}">{alerta}</div>' if alerta else ''}
            </div>""", unsafe_allow_html=True)

        total_perda = salas_df['perda_noshow'].sum()
        if total_perda > 0:
            st.markdown(f"""
            <div style="background:{RED}22;border-radius:10px;padding:14px 18px;
                        border:1px solid {RED}44;margin-top:8px">
                <span style="color:{RED};font-weight:700">Total de prejuízo oculto no período: {fmt(total_perda)}</span>
                <span style="color:#A3A8B4;font-size:12px"> — dinheiro que saiu pela porta sem atendimento</span>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 4. COMERCIAL & SDR — 9 Gargalos
# ══════════════════════════════════════════════════════════════
elif aba == "📈  Comercial & SDR":
    st.markdown(titulo_secao("Comercial & SDR",
        "Os 9 Gargalos das Vendas Médicas — funil com método"), unsafe_allow_html=True)

    conn = get_conn()
    leads_df = pd.read_sql("SELECT * FROM leads WHERE mes=? AND ano=? ORDER BY id DESC",
        conn, params=(mes_sel, ano_sel))
    conn.close()

    tot   = len(leads_df)
    ag    = int(leads_df[leads_df['status'].isin(['Agendado','Compareceu','Convertido'])].shape[0]) if not leads_df.empty else 0
    comp  = int(leads_df['compareceu'].sum()) if not leads_df.empty else 0
    conv  = int(leads_df['convertido'].sum()) if not leads_df.empty else 0

    resp_5min = int((leads_df['tempo_resposta_min'] <= 5).sum()) if not leads_df.empty and 'tempo_resposta_min' in leads_df.columns else 0
    tx_veloc  = pct_safe(resp_5min, tot)

    st.markdown(f"""
    <div style="background:{CARD};border-radius:12px;padding:20px 24px;margin-bottom:20px;
                border:1px solid rgba(200,150,60,0.2)">
        <div style="color:{GOLD};font-size:11px;font-weight:700;letter-spacing:2px;
                    text-transform:uppercase;margin-bottom:14px">
            FUNIL SPIN — DA CAPTAÇÃO À CONVERSÃO
        </div>
        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:1px;
                    background:rgba(200,150,60,0.15);border-radius:8px;overflow:hidden">
            {''.join([f"""
            <div style="background:{CARD};padding:16px;text-align:center">
                <div style="color:#A3A8B4;font-size:9px;text-transform:uppercase;letter-spacing:1px">{lb}</div>
                <div style="color:{IVORY};font-size:26px;font-weight:800;margin:4px 0">{vl}</div>
                <div style="color:{cr};font-size:12px;font-weight:700">{tx}</div>
            </div>""" for lb,vl,tx,cr in [
                ("Leads",tot,"100%","#A3A8B4"),
                ("Agendados",ag,f"{pct_safe(ag,tot):.0f}%",GOLD),
                ("Compareceram",comp,f"{pct_safe(comp,ag):.0f}%",GOLD),
                ("Convertidos",conv,f"{pct_safe(conv,tot):.0f}% final",GREEN),
                ("Resp. <5min",resp_5min,f"{tx_veloc:.0f}%",GREEN if tx_veloc>=80 else RED),
            ]])}
        </div>
    </div>""", unsafe_allow_html=True)

    col_orig, col_mot = st.columns(2)
    with col_orig:
        st.markdown(f"<div style='color:{IVORY};font-weight:700;margin-bottom:10px'>Origem dos Leads</div>", unsafe_allow_html=True)
        if not leads_df.empty:
            orig = leads_df.groupby('canal').size().reset_index(name='leads').sort_values('leads',ascending=False)
            for _, row in orig.iterrows():
                p_o = pct_safe(row['leads'], tot)
                st.markdown(barra(p_o, f"{row['canal']}: {row['leads']} leads", GOLD), unsafe_allow_html=True)
        else:
            st.info("Sem leads neste período.")

    with col_mot:
        st.markdown(f"<div style='color:{IVORY};font-weight:700;margin-bottom:10px'>Motivos de Perda</div>", unsafe_allow_html=True)
        if not leads_df.empty and leads_df['motivo_perda'].any():
            perdas = leads_df[leads_df['motivo_perda']!=''].groupby('motivo_perda').size().reset_index(name='qtd')
            if not perdas.empty:
                for _, row in perdas.iterrows():
                    st.markdown(barra(pct_safe(row['qtd'], tot), f"{row['motivo_perda']}: {row['qtd']}", RED), unsafe_allow_html=True)
            else:
                st.info("Registre motivos de perda nos leads para ver aqui.")
        else:
            st.info("Sem motivos de perda registrados.")

    st.markdown("---")
    with st.expander("➕ Adicionar Lead"):
        with st.form("form_lead_v2"):
            c1,c2,c3,c4 = st.columns(4)
            with c1: nome_l  = st.text_input("Nome do Lead")
            with c2: canal_l = st.selectbox("Canal", ["Instagram","Indicação","Google","WhatsApp","Tráfego Pago","Outro"])
            with c3: sdr_l   = st.text_input("SDR (DRI deste lead)")
            with c4: tk_l    = st.number_input("Ticket proposto (R$)", min_value=0.0, step=50.0)
            c5,c6,c7,c8 = st.columns(4)
            with c5: status_l  = st.selectbox("Status", ["Novo","Qualificado","Agendado","Compareceu","Convertido","Descartado"])
            with c6: resp_l    = st.number_input("Tempo de resposta (min)", min_value=0, value=0)
            with c7: comp_l    = st.checkbox("Compareceu")
            with c8: conv_l    = st.checkbox("Convertido")
            motivo_l = st.text_input("Motivo de perda (se descartado)")
            if st.form_submit_button("➕ Adicionar"):
                if nome_l:
                    conn = get_conn()
                    conn.execute("""INSERT INTO leads
                        (nome,canal,sdr_nome,status,tempo_resposta_min,compareceu,convertido,
                         ticket_proposto,motivo_perda,mes,ano)
                        VALUES (?,?,?,?,?,?,?,?,?,?,?)""",
                        (nome_l,canal_l,sdr_l or None,status_l,resp_l,
                         1 if comp_l else 0,1 if conv_l else 0,
                         tk_l,motivo_l or '',mes_sel,ano_sel))
                    conn.commit(); conn.close()
                    st.success(f"Lead '{nome_l}' adicionado!"); st.rerun()

    if not leads_df.empty:
        st.markdown(f"<div style='color:{IVORY};font-weight:700;margin:12px 0 8px'>Leads — {mes_sel}/{ano_sel}</div>", unsafe_allow_html=True)
        cols_show = ['nome','canal','sdr_nome','status','tempo_resposta_min','compareceu','convertido','ticket_proposto']
        st.dataframe(leads_df[cols_show], hide_index=True, use_container_width=True,
            column_config={
                "ticket_proposto": st.column_config.NumberColumn("Ticket", format="R$ %.2f"),
                "tempo_resposta_min": "Resp. (min)",
                "compareceu": st.column_config.CheckboxColumn("Comp."),
                "convertido": st.column_config.CheckboxColumn("Conv."),
            })


# ══════════════════════════════════════════════════════════════
# 5. RÉGUAS D-1 / D+1
# ══════════════════════════════════════════════════════════════
elif aba == "🔄  Réguas D-1 / D+1":
    st.markdown(titulo_secao("Réguas D-1 / D+1",
        "A entrega começa um dia antes e segue um dia depois"), unsafe_allow_html=True)

    st.markdown(f"""
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px">
        <div style="background:{MID};border-radius:12px;padding:18px;border-left:3px solid {GOLD}">
            <div style="color:{GOLD};font-size:11px;font-weight:700;letter-spacing:1px;margin-bottom:8px">D-1 — A VÉSPERA</div>
            <div style="color:{IVORY};font-size:13px;font-weight:700;margin-bottom:6px">Primeira Consulta</div>
            <div style="color:#A3A8B4;font-size:12px;line-height:1.8">
                ① Mensagem de boas-vindas com assinatura da clínica<br>
                ② Alinhamento de expectativas (tempo, preparo)<br>
                ③ Envio do questionário pré-consulta<br>
                ④ Convocação do decisor (cônjuge/acompanhante)<br>
                ⑤ Geração de expectativas (tecnologia, conforto, plano)
            </div>
            <div style="color:{GOLD};font-size:11px;font-weight:700;margin-top:10px;letter-spacing:1px">Retorno</div>
            <div style="color:#A3A8B4;font-size:12px;line-height:1.8;margin-top:4px">
                ① Reativar vínculo — paciente é lembrado pelo nome<br>
                ② Alinhar expectativas do retorno<br>
                ③ Confirmar realização dos exames<br>
                ④ Convocar decisor (foco em fechamento)<br>
                ⑤ Sinalizar clareza do plano de conduta
            </div>
        </div>
        <div style="background:{MID};border-radius:12px;padding:18px;border-left:3px solid {GREEN}">
            <div style="color:{GREEN};font-size:11px;font-weight:700;letter-spacing:1px;margin-bottom:8px">D+1 — O DIA SEGUINTE</div>
            <div style="color:{IVORY};font-size:13px;font-weight:700;margin-bottom:6px">Primeira Consulta</div>
            <div style="color:#A3A8B4;font-size:12px;line-height:1.8">
                ① Mensagem de direcionamento e agradecimento<br>
                ② Importância dos exames solicitados<br>
                ③ Alinhamento do tempo de retorno<br>
                ④ Repetir exames e especificidades<br>
                ⑤ Retorno já agendado (regra, não exceção)
            </div>
            <div style="color:{GREEN};font-size:11px;font-weight:700;margin-top:10px;letter-spacing:1px">Retorno</div>
            <div style="color:#A3A8B4;font-size:12px;line-height:1.8;margin-top:4px">
                ① Mensagem de direcionamento<br>
                ② Reforçar importância do protocolo<br>
                ③ Reexplicar tratamentos propostos<br>
                ④ Retorno agendado confirmado<br>
                ⑤ 2 vouchers para indicação ativa
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:{CARD};border-radius:12px;padding:16px 20px;margin-bottom:20px;
                border:1px solid rgba(200,150,60,0.2)">
        <div style="color:{GOLD};font-size:11px;font-weight:700;letter-spacing:1px;margin-bottom:10px">
            RÉGUA DE FOLLOW-UP — ORÇAMENTOS ABERTOS
        </div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px">
            {''.join([f"""
            <div style="background:{MID};border-radius:8px;padding:12px;text-align:center">
                <div style="color:{GOLD};font-size:18px;font-weight:800">{dia}</div>
                <div style="color:#A3A8B4;font-size:11px">{desc}</div>
            </div>""" for dia,desc in [
                ("D+1","Primeiro contato pós-orçamento"),
                ("D+3","Esclarecer dúvidas"),
                ("D+7","Reforço de valor"),
                ("D+14","Reativação final"),
            ]])}
        </div>
    </div>""", unsafe_allow_html=True)

    conn = get_conn()
    reguas = pd.read_sql("SELECT * FROM regua_pacientes ORDER BY data_consulta DESC", conn)
    conn.close()

    with st.expander("➕ Adicionar Paciente na Régua"):
        with st.form("form_regua"):
            c1,c2,c3 = st.columns(3)
            with c1: nome_rg   = st.text_input("Nome do paciente")
            with c2: tipo_rg   = st.selectbox("Tipo", ["Primeira Consulta","Retorno"])
            with c3: data_rg   = st.date_input("Data da consulta", value=date.today())
            tk_rg = st.number_input("Ticket / valor do protocolo (R$)", min_value=0.0, step=50.0)
            if st.form_submit_button("Adicionar"):
                if nome_rg:
                    conn = get_conn()
                    conn.execute("""INSERT INTO regua_pacientes
                        (nome_paciente, tipo_contato, data_consulta, ticket_valor)
                        VALUES (?,?,?,?)""", (nome_rg, tipo_rg, data_rg.isoformat(), tk_rg))
                    conn.commit(); conn.close()
                    st.success(f"Paciente '{nome_rg}' adicionado!"); st.rerun()

    if not reguas.empty:
        st.markdown(f"<div style='color:{IVORY};font-weight:700;margin:12px 0 8px'>Pacientes na Régua</div>", unsafe_allow_html=True)
        cols_rg = ['nome_paciente','tipo_contato','data_consulta','status_d1','status_d_mais1',
                   'status_d_mais3','status_d_mais7','status_d_mais14','ticket_valor','fechou_protocolo']
        st.dataframe(reguas[cols_rg], hide_index=True, use_container_width=True,
            column_config={
                "ticket_valor": st.column_config.NumberColumn("Ticket", format="R$ %.2f"),
                "fechou_protocolo": st.column_config.CheckboxColumn("Fechou"),
                "status_d1": "D-1",
                "status_d_mais1": "D+1",
                "status_d_mais3": "D+3",
                "status_d_mais7": "D+7",
                "status_d_mais14": "D+14",
            })
        pendentes = reguas[reguas['fechou_protocolo']==0]
        if not pendentes.empty:
            pipeline_regua = pendentes['ticket_valor'].sum()
            st.markdown(f"""
            <div style="background:{GOLD}22;border-radius:8px;padding:10px 14px;
                        border:1px solid {GOLD}44;margin-top:8px">
                <span style="color:{GOLD};font-weight:700">Pipeline na régua: {fmt(pipeline_regua)}</span>
                <span style="color:#A3A8B4;font-size:12px"> em {len(pendentes)} pacientes aguardando follow-up</span>
            </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 6. PROGRAMA INTEGRA — MOD Gamificado
# ══════════════════════════════════════════════════════════════
elif aba == "🎓  Programa Integra":
    st.markdown(titulo_secao("Programa Integra — MOD & Onboarding",
        "Score de execução diária por colaborador. Meta: acima de 85%."), unsafe_allow_html=True)

    conn = get_conn()
    colabs = pd.read_sql("SELECT * FROM colaboradores WHERE ativo=1", conn)
    tarefas_df = pd.read_sql("SELECT * FROM mod_tarefas WHERE ativo=1 ORDER BY frequencia, peso_pct DESC", conn)
    conn.close()

    col_colab, col_mod = st.columns([1, 2])

    with col_colab:
        st.markdown(f"<div style='color:{IVORY};font-weight:700;margin-bottom:12px'>Equipe Ativa</div>", unsafe_allow_html=True)
        if colabs.empty:
            st.info("Cadastre colaboradores em Configurações.")
            colab_sel = "Sem colaborador"
        else:
            colab_sel = st.selectbox("Colaborador para reunião 1:1:",
                colabs['nome'].tolist(), label_visibility="collapsed")

        st.markdown(f"<div style='color:{IVORY};font-weight:700;margin:16px 0 10px'>Trilha de Onboarding</div>", unsafe_allow_html=True)
        modulos = [
            ("Módulo 1", "Cultura & Posicionamento Premium"),
            ("Módulo 2", "SupportClinic & Métricas de Sala"),
            ("Módulo 3", "Scripts D-1/D+1 & Follow-up"),
            ("Módulo 4", "Vendas High-Ticket & Objeções"),
        ]
        concl = 0
        for i, (cod, desc) in enumerate(modulos):
            conn = get_conn()
            on_r = conn.execute("""SELECT concluido FROM onboarding
                WHERE colaborador_id=(SELECT id FROM colaboradores WHERE nome=? LIMIT 1)
                AND modulo=?""", (colab_sel, cod)).fetchone()
            conn.close()
            check = st.checkbox(f"{cod}: {desc}", value=bool(on_r and on_r[0]), key=f"on_{i}")
            if check:
                concl += 1
                if not (on_r and on_r[0]):
                    conn = get_conn()
                    colab_id_r = conn.execute("SELECT id FROM colaboradores WHERE nome=?", (colab_sel,)).fetchone()
                    if colab_id_r:
                        conn.execute("""INSERT OR REPLACE INTO onboarding
                            (colaborador_id, modulo, concluido, data_conclusao)
                            VALUES (?,?,1,?)""",
                            (colab_id_r[0], cod, date.today().isoformat()))
                        conn.commit()
                    conn.close()

        prog_on = concl / len(modulos)
        st.markdown(f"**Progresso:** {int(prog_on*100)}%")
        st.progress(prog_on)
        if prog_on < 1.0:
            st.warning("Bônus travado. Onboarding incompleto.")
        else:
            st.success("Onboarding completo. Bônus liberado.")

    with col_mod:
        st.markdown(f"<div style='color:{IVORY};font-weight:700;margin-bottom:12px'>Auditoria MOD — {colab_sel}</div>", unsafe_allow_html=True)

        if tarefas_df.empty:
            st.info("Nenhuma tarefa no MOD. Adicione em Configurações.")
        else:
            score_total = 0
            for _, t in tarefas_df.iterrows():
                conn = get_conn()
                exec_r = conn.execute("""SELECT concluida FROM mod_execucao
                    WHERE tarefa_id=? AND colaborador=? AND data_execucao=?""",
                    (t['id'], colab_sel, date.today().isoformat())).fetchone()
                conn.close()
                check_t = st.checkbox(
                    f"{t['titulo']} (Peso: {t['peso_pct']}%)",
                    value=bool(exec_r and exec_r[0]),
                    key=f"t_{t['id']}_{colab_sel}"
                )
                if check_t:
                    score_total += t['peso_pct']
                    if not (exec_r and exec_r[0]):
                        conn = get_conn()
                        conn.execute("""INSERT OR REPLACE INTO mod_execucao
                            (tarefa_id, colaborador, data_execucao, concluida)
                            VALUES (?,?,?,1)""",
                            (t['id'], colab_sel, date.today().isoformat()))
                        conn.commit(); conn.close()

            score_total = min(score_total, 100)
            cor_score = GREEN if score_total >= 85 else GOLD if score_total >= 60 else RED
            st.markdown(f"""
            <div style="background:{NAVY};border:2px solid {cor_score};border-radius:12px;
                        padding:20px;text-align:center;margin-top:16px">
                <div style="color:#A3A8B4;font-size:10px;letter-spacing:2px;
                            text-transform:uppercase">SCORE DE EXECUÇÃO DIÁRIA</div>
                <div style="font-size:3rem;font-weight:800;color:{cor_score};
                            font-family:Georgia,serif">{score_total}%</div>
                <div style="color:#A3A8B4;font-size:12px">
                    {'✅ Zona de Genialidade — meta batida' if score_total>=85 else '⚠️ Abaixo da meta crítica de 85%'}
                </div>
            </div>""", unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("➕ Adicionar Tarefa ao MOD"):
        with st.form("form_mod_v2"):
            c1,c2,c3,c4,c5 = st.columns(5)
            with c1: tit_t  = st.text_input("Tarefa (Ação)")
            with c2: resp_t = st.text_input("Responsável (DRI)")
            with c3: freq_t = st.selectbox("Frequência", ["Diária","Semanal","Mensal"])
            with c4: cat_t  = st.selectbox("Categoria", ["Comercial","Operacional","Financeiro","Pessoas","Liderança"])
            with c5: peso_t = st.number_input("Peso (%)", value=10, min_value=1, max_value=50)
            dri_t = st.text_input("Entrega esperada")
            if st.form_submit_button("Adicionar"):
                if tit_t:
                    conn = get_conn()
                    conn.execute("""INSERT INTO mod_tarefas
                        (titulo, responsavel, dri, frequencia, categoria, peso_pct)
                        VALUES (?,?,?,?,?,?)""",
                        (tit_t, resp_t, dri_t, freq_t, cat_t, peso_t))
                    conn.commit(); conn.close()
                    st.success("Tarefa adicionada!"); st.rerun()


# ══════════════════════════════════════════════════════════════
# 7. FINANCEIRO & EBITDA
# ══════════════════════════════════════════════════════════════
elif aba == "💰  Financeiro & EBITDA":
    st.markdown(titulo_secao("Financeiro & EBITDA",
        "DRE Gerencial completo. Faturamento sem margem é ilusão."), unsafe_allow_html=True)

    conn = get_conn()
    dre_r = conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?", (mes_sel, ano_sel)).fetchone()
    hist  = pd.read_sql("""
        SELECT mes, ano,
            (receita_consultas+receita_procedimentos+receita_recorrencia+receita_outros) as receita_bruta,
            (custo_pessoal+custo_ocupacao+custo_marketing+custo_outros) as custos_fixos,
            custo_insumos
        FROM dre ORDER BY ano, mes LIMIT 12""", conn)
    conn.close()

    with st.expander("✏️ Lançar DRE do Mês", expanded=not bool(dre_r)):
        with st.form("form_dre_v2"):
            st.markdown(f"<div style='color:{GOLD};font-weight:700;margin-bottom:12px'>RECEITAS</div>", unsafe_allow_html=True)
            c1,c2,c3,c4 = st.columns(4)
            with c1: rc  = st.number_input("Consultas (R$)", value=float(dre_r[3] if dre_r else 0), step=100.0)
            with c2: rp  = st.number_input("Procedimentos (R$)", value=float(dre_r[4] if dre_r else 0), step=100.0)
            with c3: rr  = st.number_input("Recorrência LTV (R$)", value=float(dre_r[5] if dre_r else 0), step=100.0)
            with c4: ro  = st.number_input("Outros (R$)", value=float(dre_r[6] if dre_r else 0), step=100.0)

            st.markdown(f"<div style='color:{GOLD};font-weight:700;margin:12px 0 8px'>DEDUÇÕES</div>", unsafe_allow_html=True)
            c1,c2 = st.columns(2)
            with c1: imp_d  = st.number_input("Impostos (%)", value=float(dre_r[7] if dre_r else 8.5), step=0.1)
            with c2: tc_d   = st.number_input("Taxa Cartão (%)", value=float(dre_r[8] if dre_r else 3.0), step=0.1)

            st.markdown(f"<div style='color:{GOLD};font-weight:700;margin:12px 0 8px'>CUSTOS</div>", unsafe_allow_html=True)
            c1,c2,c3,c4,c5 = st.columns(5)
            with c1: ins_d = st.number_input("Insumos (R$)", value=float(dre_r[9] if dre_r else 0), step=100.0)
            with c2: pes_d = st.number_input("Pessoal (R$)", value=float(dre_r[10] if dre_r else 0), step=100.0)
            with c3: oc_d  = st.number_input("Ocupação (R$)", value=float(dre_r[11] if dre_r else 0), step=100.0)
            with c4: mk_d  = st.number_input("Marketing (R$)", value=float(dre_r[12] if dre_r else 0), step=100.0)
            with c5: ou_d  = st.number_input("Outros (R$)", value=float(dre_r[13] if dre_r else 0), step=100.0)

            if st.form_submit_button("💾 Salvar DRE"):
                conn = get_conn()
                conn.execute("""
                    INSERT INTO dre (mes,ano,receita_consultas,receita_procedimentos,
                        receita_recorrencia,receita_outros,imposto_pct,taxa_cartao_pct,
                        custo_insumos,custo_pessoal,custo_ocupacao,custo_marketing,custo_outros)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(mes,ano) DO UPDATE SET
                        receita_consultas=excluded.receita_consultas,
                        receita_procedimentos=excluded.receita_procedimentos,
                        receita_recorrencia=excluded.receita_recorrencia,
                        receita_outros=excluded.receita_outros,
                        imposto_pct=excluded.imposto_pct,
                        taxa_cartao_pct=excluded.taxa_cartao_pct,
                        custo_insumos=excluded.custo_insumos,
                        custo_pessoal=excluded.custo_pessoal,
                        custo_ocupacao=excluded.custo_ocupacao,
                        custo_marketing=excluded.custo_marketing,
                        custo_outros=excluded.custo_outros
                """, (mes_sel,ano_sel,rc,rp,rr,ro,imp_d,tc_d,ins_d,pes_d,oc_d,mk_d,ou_d))
                conn.commit(); conn.close()
                st.success("DRE salvo!"); st.rerun()

    if dre_r:
        rb   = sum([dre_r[i] or 0 for i in [3,4,5,6]])
        imp  = dre_r[7] or 8.5
        tc   = dre_r[8] or 3.0
        ins  = dre_r[9] or 0
        pes  = dre_r[10] or 0
        oc   = dre_r[11] or 0
        mk   = dre_r[12] or 0
        ou   = dre_r[13] or 0

        ded   = rb * (imp + tc) / 100
        rl    = rb - ded
        mc    = rl - ins
        cf    = pes + oc + mk + ou
        ebitda= mc - cf
        mg_eb = pct_safe(ebitda, rb)
        pe    = cf / (1 - (imp+tc)/100) if (1-(imp+tc)/100) > 0 else 0

        st.markdown("---")
        st.markdown(f"<div style='color:{GOLD};font-weight:700;font-size:14px;letter-spacing:1px;margin-bottom:14px'>DRE GERENCIAL CONSOLIDADO — {mes_sel}/{ano_sel}</div>", unsafe_allow_html=True)

        linhas = [
            ("(+) FATURAMENTO BRUTO", rb, 100.0, GREEN, False),
            ("   Consultas", dre_r[3] or 0, pct_safe(dre_r[3] or 0, rb), "#A3A8B4", False),
            ("   Procedimentos", dre_r[4] or 0, pct_safe(dre_r[4] or 0, rb), "#A3A8B4", False),
            ("   Recorrência LTV", dre_r[5] or 0, pct_safe(dre_r[5] or 0, rb), "#A3A8B4", False),
            ("(-) Impostos + Taxas Cartão", ded, pct_safe(ded, rb), RED, False),
            ("(=) RECEITA LÍQUIDA OPERACIONAL", rl, pct_safe(rl, rb), IVORY, True),
            ("(-) Custos Variáveis (Insumos)", ins, pct_safe(ins, rb), RED, False),
            ("(=) MARGEM DE CONTRIBUIÇÃO", mc, pct_safe(mc, rb), GOLD, True),
            ("(-) Custos Fixos Totais", cf, pct_safe(cf, rb), RED, False),
            ("   Folha de Pessoal", pes, pct_safe(pes, rb), "#A3A8B4", False),
            ("   Ocupação / Aluguel", oc, pct_safe(oc, rb), "#A3A8B4", False),
            ("   Marketing / Leads", mk, pct_safe(mk, rb), "#A3A8B4", False),
            ("(=) EBITDA OPERACIONAL REAL", ebitda, mg_eb, GREEN if ebitda>0 else RED, True),
        ]

        for label_dre, val_dre, pct_dre, cor_dre, dest_dre in linhas:
            bg_dre = NAVY if dest_dre else CARD
            bd_dre = f"2px solid {cor_dre}66" if dest_dre else f"1px solid rgba(200,150,60,0.1)"
            st.markdown(f"""
            <div style="background:{bg_dre};border-radius:8px;padding:9px 16px;margin-bottom:3px;
                        border:{bd_dre};display:flex;justify-content:space-between;align-items:center">
                <span style="font-size:{'13' if dest_dre else '12'}px;
                             font-weight:{'700' if dest_dre else '400'};
                             color:{cor_dre if dest_dre else '#A3A8B4'}">{label_dre}</span>
                <div style="display:flex;gap:20px;align-items:center">
                    <span style="font-size:11px;color:#555">{pct_dre:.1f}%</span>
                    <span style="font-size:{'15' if dest_dre else '13'}px;
                                 font-weight:{'800' if dest_dre else '500'};
                                 color:{cor_dre}">{fmt(val_dre)}</span>
                </div>
            </div>""", unsafe_allow_html=True)

        c1,c2,c3 = st.columns(3)
        with c1: st.metric("Ponto de Equilíbrio", fmt(pe), "Faturamento mínimo")
        with c2: st.metric("Margem EBITDA", f"{mg_eb:.1f}%", "Saúde operacional real")
        with c3: st.metric("Margem de Contribuição", f"{pct_safe(mc,rb):.1f}%", "Após insumos variáveis")

        if not hist.empty:
            st.markdown(f"<div style='color:{IVORY};font-weight:700;margin:20px 0 10px'>Evolução do EBITDA</div>", unsafe_allow_html=True)
            hist["período"] = hist["mes"] + "/" + hist["ano"].astype(str)
            st.bar_chart(hist.set_index("período")[["receita_bruta","custos_fixos","custo_insumos"]])


# ══════════════════════════════════════════════════════════════
# 8. OKRs
# ══════════════════════════════════════════════════════════════
elif aba == "📐  OKRs":
    st.markdown(titulo_secao("OKRs — Objetivos e Resultados-Chave",
        "Objectives conectados à execução diária. Sem OKR, sem direção."), unsafe_allow_html=True)

    conn = get_conn()
    okrs_df = pd.read_sql("SELECT * FROM okrs WHERE ativo=1 ORDER BY trimestre, objetivo", conn)
    conn.close()

    with st.expander("➕ Adicionar OKR"):
        with st.form("form_okr"):
            c1,c2 = st.columns(2)
            with c1:
                obj_o = st.text_input("Objetivo (O que queremos alcançar?)")
                kr_o  = st.text_input("Key Result (Como medimos o sucesso?)")
                resp_o= st.text_input("Responsável DRI")
            with c2:
                meta_o = st.number_input("Meta (valor)", min_value=0.0, step=1.0)
                atu_o  = st.number_input("Atual (valor)", min_value=0.0, step=1.0)
                tri_o  = st.selectbox("Trimestre", ["Q1","Q2","Q3","Q4"])
                ano_o  = st.number_input("Ano", value=ano_sel, min_value=2020, max_value=2030)
            if st.form_submit_button("Salvar OKR"):
                if obj_o and kr_o:
                    conn = get_conn()
                    conn.execute("""INSERT INTO okrs
                        (objetivo,key_result,meta_valor,atual_valor,responsavel,trimestre,ano)
                        VALUES (?,?,?,?,?,?,?)""",
                        (obj_o,kr_o,meta_o,atu_o,resp_o,tri_o,ano_o))
                    conn.commit(); conn.close()
                    st.success("OKR adicionado!"); st.rerun()

    if okrs_df.empty:
        st.info("Sem OKRs cadastrados. Defina os objetivos do trimestre.")
    else:
        for tri in ["Q1","Q2","Q3","Q4"]:
            grupo = okrs_df[okrs_df["trimestre"] == tri]
            if grupo.empty: continue
            for obj in grupo["objetivo"].unique():
                krs = grupo[grupo["objetivo"] == obj]
                st.markdown(f"""
                <div style="background:{CARD};border-radius:12px;padding:18px 22px;
                            margin-bottom:14px;border:1px solid rgba(200,150,60,0.2)">
                    <div style="display:flex;justify-content:space-between;margin-bottom:14px">
                        <div style="color:{GOLD};font-size:13px;font-weight:700">🎯 {obj}</div>
                        <div style="color:#A3A8B4;font-size:11px">{tri} / {ano_sel}</div>
                    </div>""", unsafe_allow_html=True)
                for _, kr in krs.iterrows():
                    p_kr = pct_safe(kr['atual_valor'], kr['meta_valor'])
                    _, cor_kr = semaforo(p_kr)
                    st.markdown(f"""
                    <div style="background:{MID};border-radius:8px;padding:12px 14px;margin-bottom:8px">
                        <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                            <span style="color:{IVORY};font-size:13px">{kr['key_result']}</span>
                            <span style="color:{GOLD};font-size:11px">DRI: {kr['responsavel']}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:11px;
                                    color:#A3A8B4;margin-bottom:5px">
                            <span>Atual: {kr['atual_valor']}</span>
                            <span style="color:{cor_kr};font-weight:700">{p_kr:.0f}%</span>
                            <span>Meta: {kr['meta_valor']}</span>
                        </div>
                        <div style="height:5px;background:{NAVY};border-radius:3px;overflow:hidden">
                            <div style="height:5px;width:{min(int(p_kr),100)}%;
                                        background:{cor_kr};border-radius:3px"></div>
                        </div>
                    </div>""", unsafe_allow_html=True)
                st.markdown("</div>", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 9. IMPORTAR SUPPORT CLINIC
# ══════════════════════════════════════════════════════════════
elif aba == "🧬  Importar Support Clinic":
    st.markdown(titulo_secao("Ingestão — Support Clinic",
        "Arraste o relatório exportado. A IA lê, extrai e gera diagnóstico AME."), unsafe_allow_html=True)

    st.markdown(f"""
    <div style="background:{CARD};border-radius:12px;padding:18px 22px;
                border:1px solid rgba(200,150,60,0.2);margin-bottom:20px">
        <div style="color:{GOLD};font-size:11px;font-weight:700;letter-spacing:1px;margin-bottom:12px">
            COMO EXPORTAR DO SUPPORT CLINIC
        </div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
            {''.join([f"""
            <div style="display:flex;gap:10px;align-items:flex-start">
                <div style="width:26px;height:26px;background:{GOLD};border-radius:50%;
                            display:flex;align-items:center;justify-content:center;
                            color:{NAVY};font-weight:800;font-size:12px;flex-shrink:0">{n}</div>
                <div>
                    <div style="font-size:13px;font-weight:700;color:{IVORY}">{t}</div>
                    <div style="font-size:11px;color:#A3A8B4">{d}</div>
                </div>
            </div>""" for n,t,d in [
                (1,"Support Clinic","app.supportclinic.com.br"),
                (2,"Relatórios","Menu lateral → Relatórios"),
                (3,"Filtrar período","Selecione o mês"),
                (4,"Exportar CSV","Exportar → CSV (ideal)"),
            ]])}
        </div>
    </div>""", unsafe_allow_html=True)

    arquivo = st.file_uploader("Arraste o arquivo do SupportClinic", type=["csv","txt","pdf","xlsx"])

    if arquivo:
        st.success(f"Arquivo recebido: **{arquivo.name}**")
        conteudo = ""
        df_prev = None
        try:
            if arquivo.name.endswith((".csv",".txt")):
                raw = arquivo.read()
                for enc in ["utf-8","latin-1","cp1252"]:
                    try: conteudo = raw.decode(enc); break
                    except: continue
                try:
                    df_prev = pd.read_csv(io.StringIO(conteudo), sep=None, engine='python', nrows=20)
                    st.dataframe(df_prev, use_container_width=True)
                except: st.code(conteudo[:600])
            elif arquivo.name.endswith(".xlsx"):
                df_prev = pd.read_excel(arquivo, nrows=20)
                conteudo = df_prev.to_csv(index=False)
                st.dataframe(df_prev, use_container_width=True)
            elif arquivo.name.endswith(".pdf"):
                conteudo = f"[PDF: {arquivo.name} — {arquivo.size} bytes]"
                st.warning("PDF recebido. A IA vai analisar o conteúdo extraível.")
        except Exception as e:
            st.error(f"Erro ao ler arquivo: {e}")

        if conteudo and st.button("🧬 Processar com IA — Gerar Diagnóstico AME", type="primary"):
            api_key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY",""))
            if not api_key:
                st.error("Configure ANTHROPIC_API_KEY nos Secrets do Streamlit.")
            else:
                with st.spinner("IA processando relatório e aplicando Método AME..."):
                    try:
                        client = anthropic.Anthropic(api_key=api_key)
                        msg = client.messages.create(
                            model="claude-sonnet-4-20250514",
                            max_tokens=1800,
                            messages=[{"role":"user","content":f"""Você é o consultor executivo do LAB Metrics — Método Ponteiro.
Especialista em gestão de clínicas médicas premium.

Analise o relatório abaixo exportado do SupportClinic.
Aplique o Método AME: Ação, Movimento e Entrega em cada recomendação.

RELATÓRIO ({arquivo.name}):
{conteudo[:9000]}

Responda APENAS em JSON sem markdown:
{{
  "indicadores": {{
    "faturamento_bruto": número ou null,
    "consultas_realizadas": número ou null,
    "ticket_medio": número ou null,
    "novos_pacientes": número ou null,
    "procedimentos": número ou null,
    "no_show": número ou null,
    "taxa_conversao_pct": número ou null
  }},
  "estagio_maturidade": "Caótico|Intuitivo|Documentado|Previsível",
  "diagnostico_executivo": "texto direto máx 150 palavras",
  "pontos_positivos": ["p1","p2","p3"],
  "gargalos_identificados": ["g1","g2","g3"],
  "plano_ame": [
    {{"acao":"...","movimento":"...","entrega":"...","dri":"...","prazo":"..."}},
    {{"acao":"...","movimento":"...","entrega":"...","dri":"...","prazo":"..."}},
    {{"acao":"...","movimento":"...","entrega":"...","dri":"...","prazo":"..."}}
  ],
  "alerta_noshow": "texto sobre impacto financeiro do no-show se identificado"
}}"""}]
                        )
                        raw = msg.content[0].text.strip().replace("```json","").replace("```","").strip()
                        res = json.loads(raw)

                        conn = get_conn()
                        conn.execute("""INSERT INTO relatorios
                            (nome_arquivo,conteudo,analise_ia,mes,ano)
                            VALUES (?,?,?,?,?)""",
                            (arquivo.name, conteudo[:20000],
                             json.dumps(res, ensure_ascii=False), mes_sel, ano_sel))
                        if res.get("indicadores",{}).get("faturamento_bruto"):
                            fat_ia = res["indicadores"]["faturamento_bruto"]
                            conn.execute("""INSERT INTO dre
                                (mes,ano,receita_outros) VALUES (?,?,?)
                                ON CONFLICT(mes,ano) DO UPDATE SET
                                receita_outros=excluded.receita_outros""",
                                (mes_sel, ano_sel, fat_ia))
                        if res.get("estagio_maturidade"):
                            conn.execute("UPDATE clinica SET estagio=? WHERE id=1",
                                (res["estagio_maturidade"],))
                        conn.commit(); conn.close()

                        # Indicadores
                        st.markdown("---")
                        st.markdown(f"<div style='color:{GOLD};font-weight:700;margin-bottom:12px'>INDICADORES EXTRAÍDOS</div>", unsafe_allow_html=True)
                        inds = res.get("indicadores",{})
                        cols_i = st.columns(7)
                        for i,(k,label) in enumerate(zip(
                            ["faturamento_bruto","consultas_realizadas","ticket_medio",
                             "novos_pacientes","procedimentos","no_show","taxa_conversao_pct"],
                            ["Faturamento","Consultas","Ticket Médio",
                             "Novos Pac.","Procedimentos","No-Show","Conversão %"]
                        )):
                            v = inds.get(k)
                            if v is not None:
                                with cols_i[i]:
                                    display_v = fmt(v) if k in ["faturamento_bruto","ticket_medio"] else (f"{v}%" if "pct" in k else v)
                                    st.metric(label, display_v)

                        # Diagnóstico
                        st.markdown(f"""
                        <div style="background:{NAVY};border-radius:12px;padding:22px 26px;
                                    margin:16px 0;border:1px solid rgba(200,150,60,0.3)">
                            <div style="color:{GOLD};font-size:11px;font-weight:700;
                                        letter-spacing:2px;margin-bottom:12px">
                                DIAGNÓSTICO EXECUTIVO
                            </div>
                            <div style="color:{IVORY};font-size:14px;line-height:1.85">
                                {res.get('diagnostico_executivo','')}
                            </div>
                        </div>""", unsafe_allow_html=True)

                        col_pos, col_gar = st.columns(2)
                        with col_pos:
                            st.markdown(f"<div style='color:{GREEN};font-weight:700;margin-bottom:8px'>✅ Pontos Positivos</div>", unsafe_allow_html=True)
                            for p in res.get("pontos_positivos",[]):
                                st.markdown(f"<div style='color:#A3A8B4;font-size:13px;margin-bottom:5px'>→ {p}</div>", unsafe_allow_html=True)
                        with col_gar:
                            st.markdown(f"<div style='color:{RED};font-weight:700;margin-bottom:8px'>⚠️ Gargalos Identificados</div>", unsafe_allow_html=True)
                            for g in res.get("gargalos_identificados",[]):
                                st.markdown(f"<div style='color:#A3A8B4;font-size:13px;margin-bottom:5px'>→ {g}</div>", unsafe_allow_html=True)

                        # Plano AME
                        st.markdown(f"<div style='color:{GOLD};font-weight:700;font-size:15px;margin:20px 0 12px'>PLANO AME — 3 AÇÕES PRIORITÁRIAS</div>", unsafe_allow_html=True)
                        for i, ame in enumerate(res.get("plano_ame",[]), 1):
                            st.markdown(f"""
                            <div style="background:{CARD};border-radius:12px;padding:16px 20px;
                                        margin-bottom:10px;border-left:4px solid {GOLD}">
                                <div style="display:flex;gap:12px">
                                    <div style="width:32px;height:32px;background:{GOLD};
                                                border-radius:50%;display:flex;align-items:center;
                                                justify-content:center;color:{NAVY};font-weight:800;
                                                font-size:14px;flex-shrink:0">{i}</div>
                                    <div style="flex:1">
                                        <div style="color:{IVORY};font-weight:700;margin-bottom:6px;font-size:14px">
                                            AÇÃO: {ame.get('acao','')}
                                        </div>
                                        <div style="color:#A3A8B4;font-size:12px;margin-bottom:4px">
                                            <strong style="color:{GOLD}">MOVIMENTO:</strong> {ame.get('movimento','')}
                                        </div>
                                        <div style="color:{GREEN};font-size:12px;font-weight:600;margin-bottom:4px">
                                            📦 ENTREGA: {ame.get('entrega','')}
                                        </div>
                                        <div style="display:flex;gap:16px;font-size:11px">
                                            <span style="color:#A3A8B4">DRI: <strong style="color:{IVORY}">{ame.get('dri','')}</strong></span>
                                            <span style="color:#A3A8B4">Prazo: <strong style="color:{GOLD}">{ame.get('prazo','')}</strong></span>
                                        </div>
                                    </div>
                                </div>
                            </div>""", unsafe_allow_html=True)

                        alerta_ns = res.get("alerta_noshow","")
                        if alerta_ns:
                            st.warning(f"🚨 No-Show: {alerta_ns}")

                    except json.JSONDecodeError:
                        st.markdown(f"""
                        <div style="background:{CARD};border-radius:12px;padding:22px">
                            <div style="color:{IVORY};font-size:14px;line-height:1.8">{raw}</div>
                        </div>""", unsafe_allow_html=True)
                    except Exception as e:
                        st.error(f"Erro: {e}")

    st.markdown("---")
    st.markdown(f"<div style='color:{IVORY};font-weight:700;margin-bottom:10px'>Histórico de Importações</div>", unsafe_allow_html=True)
    conn = get_conn()
    hist_r = pd.read_sql("SELECT id,nome_arquivo,mes,ano,criado_em FROM relatorios ORDER BY criado_em DESC LIMIT 10", conn)
    conn.close()
    if not hist_r.empty:
        st.dataframe(hist_r, hide_index=True, use_container_width=True)
    else:
        st.info("Nenhum relatório importado ainda.")


# ══════════════════════════════════════════════════════════════
# 10. ASSISTENTE LAB METRICS
# ══════════════════════════════════════════════════════════════
elif aba == "🤖  Assistente LAB Metrics":
    st.markdown(titulo_secao("Assistente LAB Metrics",
        "Consultor executivo digital da clínica. Powered by Projeto Ponteiro."), unsafe_allow_html=True)

    # ── SYSTEM PROMPT COMPLETO ────────────────────────────────
    SYSTEM_PROMPT = """# IDENTIDADE DO AGENTE — LAB METRICS

## Quem você é
Você é o LAB Metrics, o assistente de gestão integrada de clínicas médicas. Você combina inteligência de dados com metodologia executiva para ajudar médicos gestores a tomar decisões mais rápidas, mais claras e mais lucrativas.

Você não é um chatbot genérico de saúde. Você é o consultor executivo digital da clínica, com visão simultânea de todos os setores: agenda, comercial, financeiro, equipe, marketing e indicadores.

Você conhece profundamente o Projeto Ponteiro, o Método AME, o MOD, o Programa Integra e o DNA Painel de Metas. Toda orientação que você oferece está baseada nessa metodologia.

## Tom e postura
- Direto. Sem rodeio. Sem enrolação.
- Humano. Fale como um sócio experiente, não como um sistema.
- Prático. Toda resposta termina com uma ação, um número ou uma decisão.
- Nenhuma análise existe sem encaminhar para execução.
- Nunca use travessões para substituir vírgula ou ponto.
- Evite termos corporativos vazios.
- Frases curtas. Clareza acima de tudo.

## Metodologia central: Método AME
Toda orientação, análise ou plano de ação precisa conter:
- AÇÃO: o que precisa ser feito
- MOVIMENTO: quem executa, quando executa, como executa e como acompanha
- ENTREGA: qual resultado concreto precisa acontecer, com indicador mensurável

Nunca responda sem responsável, prazo e entrega definidos.

## Pilares obrigatórios
DRI: toda meta, tarefa ou processo tem um dono. Sem DRI, a tarefa não existe.
MOD: a operação funciona por ritmos. Diário, semanal e mensal.
DNA Ponteiro: clareza, responsabilidade, execução, previsibilidade, organização antes da aceleração.

## O que o LAB Metrics monitora
AGENDA: taxa de ocupação real vs ideal por prescritor, no-show com impacto financeiro, horários vagos, ticket médio por prescritor, procedimentos com maior margem.
COMERCIAL: leads por canal, velocidade de resposta (meta: máximo 5 minutos), taxa de conversão, orçamentos abertos, follow-up ativo.
RFM: segmentação por recência, frequência e monetização, 30 contatos por dia com pacientes antigos, taxa de reativação.
INDICAÇÕES: 5 solicitações por dia, indicações convertidas, avaliações Google (meta: 5 por dia), mecânica de premiação ativa.
PRESENÇA DIGITAL: 1 reel, 1 post, mínimo 5 stories por dia. Mix: 70% especialidade, 20% geral, 10% autoridade.
FINANCEIRO: faturamento vs meta, margem de contribuição por serviço, ponto de equilíbrio, fluxo de caixa projetado, ticket médio, CAC, LTV.
EQUIPE: DRI ativo, MOD executado por função, one-one semanal, PDI ativo por colaborador.

## Padrão mínimo de execução diária
- Reels publicados: 1 por dia (Conteúdo)
- Posts no feed: 1 por dia (Conteúdo)
- Stories: mínimo 5 por dia (Toda equipe)
- Contatos RFM: 30 por dia (Recepção / Comercial)
- Solicitações de indicação: 5 por dia (Toda equipe)
- Conversões lead em agendamento: 2 por dia (Comercial)
- Velocidade de resposta a leads: 100% imediato (Comercial)
- Orçamentos com próxima ação: 100% (Closer)
- Avaliações Google: 5 por dia (Recepção)

## Follow-up padrão
- Lead novo (menos de 1h): WhatsApp imediato + 1h se sem resposta (Comercial)
- Lead frio (mais de 3 dias): WhatsApp + Ligação, 2x por semana (Comercial)
- Orçamento aberto: 48h + 7 dias + 15 dias (Closer)
- Indicação recebida: Ligação em até 2h (Closer)
- Paciente RFM alto: WhatsApp personalizado conforme segmento (Recepção)
- Lead de indicação: Ligação + WhatsApp em até 24h (Closer)

## Quatro motores de crescimento
Motor 1 — Leads Novos: tráfego pago, outdoor, conteúdo orgânico. Indicador: custo por lead e taxa de conversão.
Motor 2 — RFM: reativação de pacientes. 30 contatos por dia. Paciente reativado custa 5x menos que lead novo.
Motor 3 — Indicações: 5 solicitações por dia com mecânica ativa. Lead de indicação converte 3x mais.
Motor 4 — Recorrência Terapêutica: próxima etapa sempre definida na consulta. Alavanca mais subutilizada de qualquer clínica.

## Ritmos de gestão
DIÁRIO (MOD): verificar metas do dia anterior, checar agenda, atualizar painel, alinhamento rápido com comercial (máximo 10 minutos).
SEMANAL: one-one com comercial, análise de conversão, revisão de orçamentos abertos, análise de agenda para as próximas 2 semanas.
MENSAL: fechamento de metas (faturamento, agenda, conversão, RFM, indicações), DRE simplificado, planejamento do mês seguinte, NPS, reunião de cultura.

## Estágios de maturidade
- Caótico: tudo depende do dono, nada documentado
- Intuitivo: algumas rotinas existem, mas dependem de pessoas específicas
- Documentado: processos claros e responsabilidades definidas
- Previsível: indicadores atualizados, ritmo estabelecido, liderança por dados

## Como responder
Se a pergunta for sobre agenda: analise ocupação vs meta, mostre impacto financeiro, entregue 3 ações práticas por prioridade.
Se a pergunta for sobre faturamento: compare realizado vs meta, mostre receita garantida vs a gerar, identifique qual motor está mais fraco.
Se a pergunta for sobre equipe: verifique DRI, MOD executado e one-one realizado. Identifique quem está abaixo do padrão.
Se a pergunta for sobre leads: verifique velocidade de resposta, taxa de conversão e orçamentos abertos. Identifique o gargalo no funil.
Se a pergunta for sobre marketing: verifique publicações do dia, mix de conteúdo e engajamento vs padrão mínimo.
Se a pergunta for estratégica: identifique o estágio de maturidade, o gap em relação ao padrão Ponteiro e entregue o próximo passo em formato AME.

## Princípios inegociáveis
1. Organizar antes de acelerar.
2. Fechar os furos do balde antes de aumentar o volume.
3. Faturamento sem margem vira ilusão.
4. Crescimento sem gestão vira ansiedade.
5. Equipe sem clareza vira retrabalho.
6. Estratégia sem execução vira palestra.
7. Pessoas certas nas funções certas.
8. Nenhuma tarefa sem dono. Nenhum indicador sem responsável.
9. Ideia é prata. Mentalidade é ouro. Execução é diamante.

## Regra de ouro
Nenhuma análise sem ação prática.
Nenhuma ação sem responsável.
Nenhum responsável sem prazo.
Nenhum prazo sem indicador.
Nenhum indicador sem revisão.

## Frase central
"O LAB Metrics transforma dados da clínica em decisões práticas, usando o Projeto Ponteiro para organizar pessoas, processos e oportunidades e transformar esforço em execução, execução em faturamento e faturamento em previsibilidade."

Lab Metrics — powered by Projeto Ponteiro | Versão 1.0 | 2026"""

    # ── CONTEXTO DINÂMICO DA CLÍNICA ─────────────────────────
    conn = get_conn()
    dre_ctx   = conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?", (mes_sel, ano_sel)).fetchone()
    clin_ctx  = conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    leads_ctx = conn.execute("""SELECT COUNT(*) as tot, SUM(convertido) as conv,
        AVG(tempo_resposta_min) as resp_med FROM leads WHERE mes=? AND ano=?""",
        (mes_sel, ano_sel)).fetchone()
    salas_ctx = conn.execute("""SELECT AVG(horas_ocupadas*100.0/horas_disponiveis) as tx_med,
        SUM(perda_noshow) as perda_tot FROM salas WHERE mes=? AND ano=?""",
        (mes_sel, ano_sel)).fetchone()
    tarefas_ctx = conn.execute("SELECT COUNT(*) FROM mod_tarefas WHERE ativo=1").fetchone()
    conn.close()

    rb_ctx  = sum([(dre_ctx[i] or 0) for i in [3,4,5,6]]) if dre_ctx else 0
    ebitda_ctx = 0
    if dre_ctx:
        imp_c = dre_ctx[7] or 8.5; tc_c = dre_ctx[8] or 3.0
        rl_c  = rb_ctx * (1 - (imp_c+tc_c)/100)
        ins_c = dre_ctx[9] or 0
        cf_c  = sum([(dre_ctx[i] or 0) for i in [10,11,12,13]])
        ebitda_ctx = rl_c - ins_c - cf_c

    meta_ctx  = clin_ctx[2] if clin_ctx else 0
    estagio_ctx = clin_ctx[4] if clin_ctx and len(clin_ctx) > 4 else "Caótico"

    l_tot_ctx  = leads_ctx[0] if leads_ctx else 0
    l_conv_ctx = leads_ctx[1] if leads_ctx else 0
    resp_med   = leads_ctx[2] if leads_ctx else 0
    tx_conv_ctx = pct_safe(int(l_conv_ctx or 0), int(l_tot_ctx or 1))

    tx_ocup_ctx  = salas_ctx[0] if salas_ctx and salas_ctx[0] else 0
    perda_ns_ctx = salas_ctx[1] if salas_ctx and salas_ctx[1] else 0

    contexto_clinica = f"""
DADOS ATUAIS DA CLÍNICA ({mes_sel}/{ano_sel}):
- Nome: {clin_ctx[1] if clin_ctx else 'Não configurado'}
- Estágio de maturidade: {estagio_ctx}
- Faturamento realizado: R$ {rb_ctx:,.2f}
- Meta mensal: R$ {meta_ctx:,.2f}
- Atingimento da meta: {pct_safe(rb_ctx, meta_ctx):.1f}%
- EBITDA operacional: R$ {ebitda_ctx:,.2f}
- Leads no período: {l_tot_ctx} | Convertidos: {int(l_conv_ctx or 0)} | Conversão: {tx_conv_ctx:.1f}%
- Tempo médio de resposta a leads: {resp_med:.0f} minutos
- Taxa de ocupação média das salas: {tx_ocup_ctx:.1f}%
- Prejuízo com no-show: R$ {perda_ns_ctx:,.2f}
- Tarefas no MOD: {tarefas_ctx[0] if tarefas_ctx else 0}
"""

    # ── HISTÓRICO DE CONVERSA ─────────────────────────────────
    if "chat_history" not in st.session_state:
        st.session_state.chat_history = []

    # ── INTERFACE ─────────────────────────────────────────────
    st.markdown(f"""
    <div style="background:{CARD};border-radius:12px;padding:16px 22px;
                margin-bottom:20px;border:1px solid rgba(200,150,60,0.25)">
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
            <div style="text-align:center">
                <div style="color:{GOLD};font-size:10px;text-transform:uppercase;letter-spacing:1px">Faturamento</div>
                <div style="color:{IVORY};font-size:16px;font-weight:800">{fmt(rb_ctx)}</div>
                <div style="color:#A3A8B4;font-size:10px">{pct_safe(rb_ctx,meta_ctx):.0f}% da meta</div>
            </div>
            <div style="text-align:center">
                <div style="color:{GOLD};font-size:10px;text-transform:uppercase;letter-spacing:1px">EBITDA</div>
                <div style="color:{GREEN if ebitda_ctx>0 else RED};font-size:16px;font-weight:800">{fmt(ebitda_ctx)}</div>
                <div style="color:#A3A8B4;font-size:10px">{pct_safe(ebitda_ctx,rb_ctx):.1f}% margem</div>
            </div>
            <div style="text-align:center">
                <div style="color:{GOLD};font-size:10px;text-transform:uppercase;letter-spacing:1px">Conv. Leads</div>
                <div style="color:{GREEN if tx_conv_ctx>=30 else RED};font-size:16px;font-weight:800">{tx_conv_ctx:.1f}%</div>
                <div style="color:#A3A8B4;font-size:10px">{int(l_conv_ctx or 0)} de {l_tot_ctx}</div>
            </div>
            <div style="text-align:center">
                <div style="color:{GOLD};font-size:10px;text-transform:uppercase;letter-spacing:1px">Ocupação</div>
                <div style="color:{GREEN if tx_ocup_ctx>=85 else GOLD if tx_ocup_ctx>=60 else RED};font-size:16px;font-weight:800">{tx_ocup_ctx:.1f}%</div>
                <div style="color:#A3A8B4;font-size:10px">meta: 85%</div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── SUGESTÕES RÁPIDAS ─────────────────────────────────────
    st.markdown(f"<div style='color:#A3A8B4;font-size:11px;margin-bottom:10px;letter-spacing:1px;text-transform:uppercase'>Perguntas rápidas</div>", unsafe_allow_html=True)
    sugestoes = [
        "Qual meu principal gargalo agora?",
        "Como fechar a meta do mês?",
        "O que a equipe precisa fazer hoje?",
        "Como melhorar minha conversão de leads?",
        "Analise meu EBITDA e dê 3 ações.",
        "Minha ocupação está baixa. O que fazer?",
        "Como estruturar meu MOD semanal?",
        "Qual motor de crescimento precisa de atenção?",
    ]
    cols_s = st.columns(4)
    for i, sug in enumerate(sugestoes):
        with cols_s[i % 4]:
            if st.button(sug, key=f"sug_{i}", use_container_width=True):
                st.session_state.chat_history.append({"role": "user", "content": sug})
                st.rerun()

    st.markdown("---")

    # ── HISTÓRICO VISUAL ──────────────────────────────────────
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.markdown(f"""
            <div style="display:flex;justify-content:flex-end;margin-bottom:12px">
                <div style="background:{MID};border-radius:12px 12px 2px 12px;
                            padding:12px 16px;max-width:75%;border:1px solid rgba(200,150,60,0.2)">
                    <div style="color:{IVORY};font-size:13px;line-height:1.6">{msg['content']}</div>
                </div>
            </div>""", unsafe_allow_html=True)
        else:
            st.markdown(f"""
            <div style="display:flex;justify-content:flex-start;margin-bottom:16px;gap:10px">
                <div style="width:32px;height:32px;background:{GOLD};border-radius:50%;
                            display:flex;align-items:center;justify-content:center;
                            font-size:14px;flex-shrink:0;margin-top:2px">🩺</div>
                <div style="background:{CARD};border-radius:2px 12px 12px 12px;
                            padding:14px 18px;max-width:80%;
                            border:1px solid rgba(200,150,60,0.2)">
                    <div style="color:{GOLD};font-size:10px;font-weight:700;
                                letter-spacing:1px;text-transform:uppercase;margin-bottom:8px">
                        LAB METRICS
                    </div>
                    <div style="color:{IVORY};font-size:13px;line-height:1.8;white-space:pre-wrap">{msg['content']}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── PROCESSAR ÚLTIMA MENSAGEM DO USUÁRIO SE PENDENTE ─────
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"] == "user":
        api_key = st.secrets.get("ANTHROPIC_API_KEY", os.environ.get("ANTHROPIC_API_KEY",""))
        if not api_key:
            st.error("Configure a ANTHROPIC_API_KEY nos Secrets do Streamlit para usar o assistente.")
        else:
            with st.spinner("LAB Metrics analisando..."):
                try:
                    client = anthropic.Anthropic(api_key=api_key)
                    mensagens_api = []
                    for msg in st.session_state.chat_history:
                        if msg["role"] == "user" and msg == st.session_state.chat_history[-1]:
                            conteudo_com_ctx = f"""{contexto_clinica}

PERGUNTA DO GESTOR:
{msg['content']}"""
                            mensagens_api.append({"role": "user", "content": conteudo_com_ctx})
                        else:
                            mensagens_api.append(msg)

                    resposta = client.messages.create(
                        model="claude-sonnet-4-20250514",
                        max_tokens=1000,
                        system=SYSTEM_PROMPT,
                        messages=mensagens_api
                    )
                    texto_resposta = resposta.content[0].text
                    st.session_state.chat_history.append({"role": "assistant", "content": texto_resposta})
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao consultar IA: {e}")

    # ── INPUT ─────────────────────────────────────────────────
    st.markdown("<div style='height:16px'></div>", unsafe_allow_html=True)
    col_inp, col_btn, col_clear = st.columns([6, 1, 1])
    with col_inp:
        pergunta = st.text_input(
            "Consultor",
            placeholder="Digite sua pergunta para o LAB Metrics...",
            label_visibility="collapsed",
            key="input_chat"
        )
    with col_btn:
        enviar = st.button("Enviar", use_container_width=True)
    with col_clear:
        if st.button("Limpar", use_container_width=True):
            st.session_state.chat_history = []
            st.rerun()

    if enviar and pergunta.strip():
        st.session_state.chat_history.append({"role": "user", "content": pergunta.strip()})
        st.rerun()

    if not st.session_state.chat_history:
        st.markdown(f"""
        <div style="background:{NAVY};border-radius:12px;padding:28px 32px;
                    text-align:center;border:1px solid rgba(200,150,60,0.15);margin-top:20px">
            <div style="font-size:36px;margin-bottom:12px">🩺</div>
            <div style="color:{GOLD};font-size:16px;font-weight:700;font-family:Georgia,serif;margin-bottom:8px">
                LAB Metrics — Consultor Executivo Digital
            </div>
            <div style="color:#A3A8B4;font-size:13px;line-height:1.8;max-width:500px;margin:0 auto">
                Pergunte sobre agenda, faturamento, leads, equipe, marketing ou estratégia.
                Cada resposta termina em uma ação prática com responsável e prazo.
            </div>
            <div style="color:#555;font-size:11px;margin-top:16px;font-style:italic">
                "Nenhuma análise sem ação prática. Nenhuma ação sem responsável."
            </div>
        </div>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# 11. CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════
elif aba == "⚙️  Configurações":
    st.markdown(titulo_secao("Configurações"), unsafe_allow_html=True)

    tab1, tab2, tab3 = st.tabs(["🏥 Clínica & Metas","👥 Colaboradores","🔑 API Key"])

    with tab1:
        conn = get_conn()
        clin_r = conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
        conn.close()
        with st.form("form_clinica"):
            c1, c2 = st.columns(2)
            with c1:
                nome_c  = st.text_input("Nome da clínica", value=clin_r[1] if clin_r else "")
                meta_c  = st.number_input("Meta mensal (R$)", value=float(clin_r[2] if clin_r else 0), step=1000.0)
            with c2:
                cf_c    = st.number_input("Custo fixo total estimado (R$)", value=float(clin_r[3] if clin_r else 0), step=1000.0)
                est_c   = st.selectbox("Estágio de maturidade", ["Caótico","Intuitivo","Documentado","Previsível"],
                    index=["Caótico","Intuitivo","Documentado","Previsível"].index(clin_r[4] if clin_r and len(clin_r)>4 else "Caótico"))
                trib_c  = st.selectbox("Regime tributário", ["Simples Nacional","Lucro Presumido","Lucro Real"],
                    index=["Simples Nacional","Lucro Presumido","Lucro Real"].index(clin_r[5] if clin_r and len(clin_r)>5 else "Simples Nacional"))
            if st.form_submit_button("Salvar"):
                conn = get_conn()
                conn.execute("""UPDATE clinica SET nome=?,meta_mensal=?,custo_fixo_total=?,
                    estagio=?,modelo_tributario=? WHERE id=1""",
                    (nome_c, meta_c, cf_c, est_c, trib_c))
                conn.commit(); conn.close()
                st.success("Salvo!"); st.rerun()

    with tab2:
        conn = get_conn()
        colabs = pd.read_sql("SELECT * FROM colaboradores WHERE ativo=1", conn)
        conn.close()
        if not colabs.empty:
            st.dataframe(colabs[['nome','funcao','nivel_acesso','zona_genialidade']],
                hide_index=True, use_container_width=True)
        with st.form("form_colab"):
            c1,c2,c3 = st.columns(3)
            with c1: nome_cb = st.text_input("Nome")
            with c2: func_cb = st.text_input("Função")
            with c3: nivel_cb= st.selectbox("Nível de acesso",
                ["CEO / Proprietário","Gerente Executiva","Recepção / Técnica"])
            zg_cb = st.text_input("Zona de genialidade")
            if st.form_submit_button("Adicionar Colaborador"):
                if nome_cb:
                    conn = get_conn()
                    conn.execute("""INSERT INTO colaboradores (nome,funcao,nivel_acesso,zona_genialidade)
                        VALUES (?,?,?,?)""", (nome_cb, func_cb, nivel_cb, zg_cb))
                    conn.commit(); conn.close()
                    st.success("Adicionado!"); st.rerun()

    with tab3:
        st.markdown(f"""
        **Configure a chave da Anthropic para diagnóstico por IA.**

        Streamlit Cloud → seu app → ⋮ → **Settings → Secrets**:
        ```toml
        ANTHROPIC_API_KEY = "sk-ant-sua-chave-aqui"
        ```
        Pegue em: https://console.anthropic.com/keys
        """)
        k_test = st.text_input("Testar chave", type="password")
        if st.button("Testar") and k_test:
            try:
                client = anthropic.Anthropic(api_key=k_test)
                client.messages.create(model="claude-sonnet-4-20250514",
                    max_tokens=5, messages=[{"role":"user","content":"ok"}])
                st.success("Chave válida!")
            except Exception as e:
                st.error(f"Inválida: {e}")

        st.markdown("---")
        st.markdown(f"""
        <div style="background:{NAVY};border-radius:12px;padding:22px 26px;border:1px solid rgba(200,150,60,0.2)">
            <div style="color:{GOLD};font-size:16px;font-weight:700;font-family:Georgia,serif;margin-bottom:10px">
                LAB Metrics — Método Ponteiro
            </div>
            <div style="color:#A3A8B4;font-size:13px;line-height:1.9;margin-bottom:14px">
                O Projeto Ponteiro organiza pessoas, processos e oportunidades
                para transformar esforço em execução, execução em faturamento
                e faturamento em previsibilidade.
            </div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:12px;color:#555">
                {''.join([f'<div style="color:#666">→ {p}</div>' for p in [
                    "Cockpit CEO (30 segundos)","Painel DNA Semanal",
                    "Auditoria de Salas","Comercial & SDR",
                    "Réguas D-1 / D+1","Programa Integra (MOD)",
                    "EBITDA Operacional Real","OKRs conectados à operação",
                    "Ingestão Support Clinic","Diagnóstico AME por IA"
                ]])}
            </div>
            <div style="margin-top:14px;font-size:11px;color:#444;font-style:italic">
                "Ideia é prata. Mentalidade é ouro. Execução é diamante."
            </div>
        </div>""", unsafe_allow_html=True)
