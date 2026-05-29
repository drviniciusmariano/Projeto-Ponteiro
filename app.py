"""
╔══════════════════════════════════════════════════════════════════════╗
║  LAB METRICS — Sistema de Gestão 360° para Clínicas de Alta          ║
║  Performance em Medicina Funcional e Integrativa                     ║
║  Powered by Projeto Ponteiro · Método AME · Programa Integra         ║
║  © 2026 — Arquitetura: Executive Management Platform                 ║
╚══════════════════════════════════════════════════════════════════════╝
"""
import streamlit as st
import pandas as pd
import sqlite3, os, json, io, hashlib, base64, re
from datetime import datetime, date, timedelta
import anthropic
try:
    from fpdf import FPDF
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

st.set_page_config(
    page_title="LAB Metrics — Gestão 360°",
    page_icon="🩺", layout="wide",
    initial_sidebar_state="collapsed"
)

# ══════════════════════════════════════════════════════════════
# DESIGN SYSTEM — EXECUTIVE DARK
# Paleta refinada: preto profundo + amarelo âmbar + branco gelo
# ══════════════════════════════════════════════════════════════
BG      = "#0A0A0B"      # fundo principal — quase preto
BG2     = "#111113"      # superfície elevada
BG3     = "#18181B"      # card
BORDER  = "#27272A"      # borda sutil
AMBER   = "#F59E0B"      # acento principal — âmbar Harvard
AMBER2  = "#D97706"      # âmbar escuro
BLUE    = "#3B82F6"      # azul de ação
GREEN   = "#10B981"      # verde sucesso
RED     = "#EF4444"      # vermelho alerta
PURPLE  = "#8B5CF6"      # roxo estratégico
WHITE   = "#FAFAFA"      # texto principal
GRAY    = "#A1A1AA"      # texto secundário
GRAY2   = "#52525B"      # texto terciário

# aliases legado
RED_B=RED; BLUE_B=BLUE; YELL_B=AMBER; FG=WHITE; FG_MUTED=GRAY
ACCENT=AMBER; GOLD=AMBER; NAVY=BG; CARD=BG3; MID=BG2; IVORY=WHITE
GREEN_B=GREEN; RED_SOFT=RED; YELL_SOFT=AMBER
BG_DEEP=BG; BORDER_ACC=AMBER; SURF=BG3; SURF_HOV=BG2

MESES=["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
EQUIPE=["Vanessa","Bianca","Aline","Beatriz","Paloma",
        "Dr. Vinícius Mariano","Dra. Bárbara Mariano"]
CARGO_MAP={"gerente":"Vanessa","bianca":"Bianca","aline":"Aline",
           "beatriz":"Beatriz","paloma":"Paloma",
           "ceo":"Dr. Vinícius Mariano","barbara":"Dra. Bárbara Mariano"}

st.markdown(f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700;800&display=swap');
*,*::before,*::after{{box-sizing:border-box;margin:0;padding:0;}}
html,body,[class*="css"]{{font-family:'Inter',system-ui,sans-serif!important;
  background:{BG}!important;color:{WHITE}!important;-webkit-font-smoothing:antialiased;}}
.main{{background:{BG}!important;}}
.block-container{{padding:1.5rem 2rem 4rem!important;max-width:1400px;margin:0 auto;}}
h1,h2,h3,h4{{color:{WHITE}!important;font-weight:700!important;letter-spacing:-0.02em;}}
div[data-testid="stSidebarContent"]{{background:{BG2}!important;border-right:1px solid {BORDER}!important;}}
/* Métricas */
div[data-testid="metric-container"]{{background:{BG3}!important;border:1px solid {BORDER}!important;
  border-radius:12px!important;padding:20px!important;transition:all 0.2s;}}
div[data-testid="metric-container"]:hover{{border-color:{AMBER}44!important;transform:translateY(-2px);}}
div[data-testid="stMetricValue"]{{color:{WHITE}!important;font-size:1.8rem!important;font-weight:700!important;}}
div[data-testid="stMetricLabel"]{{color:{GRAY}!important;font-size:0.7rem!important;
  text-transform:uppercase!important;letter-spacing:0.1em!important;font-weight:600!important;}}
/* Botões — TODOS iguais */
.stButton>button{{background:{BLUE}!important;color:{WHITE}!important;
  border:none!important;border-radius:8px!important;font-family:'Inter',sans-serif!important;
  font-weight:600!important;font-size:0.85rem!important;letter-spacing:0.02em!important;
  padding:10px 20px!important;width:100%!important;height:42px!important;
  transition:all 0.15s ease-out!important;display:flex!important;align-items:center!important;justify-content:center!important;}}
.stButton>button:hover{{background:#2563EB!important;transform:translateY(-1px)!important;
  box-shadow:0 4px 12px rgba(59,130,246,0.4)!important;}}
.stButton>button:active{{transform:scale(0.98)!important;}}
/* Form submit */
.stFormSubmitButton>button{{background:{AMBER}!important;color:#000!important;
  border:none!important;border-radius:8px!important;font-weight:700!important;
  font-size:0.85rem!important;padding:10px 20px!important;width:100%!important;height:42px!important;}}
.stFormSubmitButton>button:hover{{background:{AMBER2}!important;transform:translateY(-1px)!important;}}
/* Inputs */
.stTextInput>div>div>input,.stNumberInput>div>div>input,.stTextArea textarea{{
  background:{BG2}!important;border:1px solid {BORDER}!important;border-radius:8px!important;
  color:{WHITE}!important;font-family:'Inter',sans-serif!important;font-size:0.9rem!important;}}
.stTextInput>div>div>input:focus,.stNumberInput>div>div>input:focus,.stTextArea textarea:focus{{
  border-color:{AMBER}!important;box-shadow:0 0 0 3px {AMBER}22!important;}}
.stSelectbox>div>div{{background:{BG2}!important;border:1px solid {BORDER}!important;
  border-radius:8px!important;color:{WHITE}!important;}}
/* Tabs */
.stTabs [data-baseweb="tab-list"]{{background:{BG2}!important;border-radius:10px!important;
  padding:4px!important;border:1px solid {BORDER}!important;gap:2px!important;}}
.stTabs [data-baseweb="tab"]{{border-radius:8px!important;color:{GRAY}!important;
  font-weight:500!important;font-size:0.8rem!important;border:none!important;
  padding:8px 14px!important;transition:all 0.15s!important;}}
.stTabs [data-baseweb="tab"]:hover{{color:{WHITE}!important;background:{BG3}!important;}}
.stTabs [aria-selected="true"]{{background:{AMBER}!important;color:#000!important;font-weight:700!important;}}
/* DataFrames */
.stDataFrame{{border:1px solid {BORDER}!important;border-radius:10px!important;overflow:hidden!important;}}
.stDataFrame th{{background:{BG2}!important;color:{GRAY}!important;font-size:0.7rem!important;
  text-transform:uppercase!important;letter-spacing:0.1em!important;border-bottom:1px solid {BORDER}!important;}}
.stDataFrame td{{background:transparent!important;color:{WHITE}!important;font-size:0.85rem!important;}}
/* Expander */
.stExpander{{background:{BG3}!important;border:1px solid {BORDER}!important;border-radius:10px!important;}}
.stExpander summary{{color:{WHITE}!important;font-weight:600!important;font-size:0.875rem!important;}}
/* Checkbox/Radio */
.stCheckbox>label,.stRadio>div>label{{color:{GRAY}!important;font-size:0.875rem!important;}}
/* Progress */
.stProgress>div>div>div>div{{background:{AMBER}!important;border-radius:99px!important;}}
.stProgress>div>div{{background:{BORDER}!important;border-radius:99px!important;}}
/* Alerts */
.stSuccess{{background:rgba(16,185,129,0.1)!important;border:1px solid rgba(16,185,129,0.3)!important;
  border-radius:8px!important;color:{GREEN}!important;}}
.stWarning{{background:rgba(245,158,11,0.1)!important;border:1px solid rgba(245,158,11,0.3)!important;
  border-radius:8px!important;color:{AMBER}!important;}}
.stError{{background:rgba(239,68,68,0.1)!important;border:1px solid rgba(239,68,68,0.3)!important;
  border-radius:8px!important;color:{RED}!important;}}
.stInfo{{background:rgba(59,130,246,0.1)!important;border:1px solid rgba(59,130,246,0.3)!important;
  border-radius:8px!important;color:{BLUE}!important;}}
/* Scrollbar */
::-webkit-scrollbar{{width:4px;height:4px;}}
::-webkit-scrollbar-track{{background:transparent;}}
::-webkit-scrollbar-thumb{{background:{BORDER};border-radius:99px;}}
/* Sidebar radio */
div[data-testid="stSidebarContent"] .stRadio>div>label{{
  color:{GRAY}!important;font-size:0.8rem!important;font-weight:500!important;
  padding:8px 12px!important;border-radius:6px!important;border-left:3px solid transparent!important;}}
div[data-testid="stSidebarContent"] .stRadio>div>label:hover{{
  background:{BG3}!important;color:{WHITE}!important;}}
/* Markdown */
.stMarkdown p{{color:{GRAY};line-height:1.7;font-size:0.9rem;}}
hr{{border:none;border-top:1px solid {BORDER};margin:20px 0;}}
</style>""", unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# BANCO DE DADOS
# ══════════════════════════════════════════════════════════════
DB = "lab_metrics.db"

def _is_postgres():
    try:
        import streamlit as _st
        return bool(_st.secrets.get("DATABASE_URL",""))
    except Exception:
        return bool(os.environ.get("DATABASE_URL",""))

def _get_pg_url():
    try:
        import streamlit as _st
        return _st.secrets.get("DATABASE_URL","")
    except Exception:
        return os.environ.get("DATABASE_URL","")

class PGConn:
    def __init__(self, url):
        import psycopg2
        self._conn = psycopg2.connect(url, sslmode="require")
        self._conn.autocommit = False
    def execute(self, sql, params=()):
        sql_pg = sql.replace("?","%s")
        cur = self._conn.cursor(); cur.execute(sql_pg, params); return cur
    def executescript(self, sql):
        cur = self._conn.cursor()
        for stmt in sql.strip().split(";"):
            stmt = stmt.strip()
            if stmt:
                try: cur.execute(stmt)
                except: pass
        return cur
    def commit(self): self._conn.commit()
    def close(self): self._conn.close()
    def __enter__(self): return self
    def __exit__(self, *a): self.close()

def get_conn():
    if _is_postgres(): return PGConn(_get_pg_url())
    return sqlite3.connect(DB, check_same_thread=False)

def read_df(sql, conn, params=()):
    if _is_postgres():
        import psycopg2.extras, pandas as _pd
        raw = conn._conn if hasattr(conn,"_conn") else conn
        return _pd.read_sql(sql.replace("?","%s"), raw, params=params or None)
    import pandas as _pd
    return _pd.read_sql(sql, conn, params=params or None)

def init_db():
    conn = get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS clinica(id INTEGER PRIMARY KEY DEFAULT 1,nome TEXT DEFAULT 'Integrative Campinas',meta_mensal REAL DEFAULT 280000,custo_fixo_total REAL DEFAULT 81000,estagio TEXT DEFAULT 'Previsível',modelo_tributario TEXT DEFAULT 'Simples Nacional');
    INSERT OR IGNORE INTO clinica(id) VALUES(1);
    CREATE TABLE IF NOT EXISTS colaboradores(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT,funcao TEXT,cargo_key TEXT DEFAULT '',nivel_acesso TEXT DEFAULT 'Operacional',zona_genialidade TEXT DEFAULT '',ativo INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS dre(id INTEGER PRIMARY KEY AUTOINCREMENT,mes TEXT,ano INTEGER,receita_consultas REAL DEFAULT 0,receita_procedimentos REAL DEFAULT 0,receita_recorrencia REAL DEFAULT 0,receita_outros REAL DEFAULT 0,imposto_pct REAL DEFAULT 8.5,taxa_cartao_pct REAL DEFAULT 3.0,custo_insumos REAL DEFAULT 0,custo_pessoal REAL DEFAULT 0,custo_ocupacao REAL DEFAULT 0,custo_marketing REAL DEFAULT 0,custo_outros REAL DEFAULT 0,UNIQUE(mes,ano));
    CREATE TABLE IF NOT EXISTS painel_dna(id INTEGER PRIMARY KEY AUTOINCREMENT,semana TEXT,ano INTEGER,meta_mensal REAL DEFAULT 0,realizado_mes REAL DEFAULT 0,dias_uteis_restantes INTEGER DEFAULT 5,consultas_v REAL DEFAULT 0,procedimentos_v REAL DEFAULT 0,negociacoes_v REAL DEFAULT 0,orcamentos_v REAL DEFAULT 0,seg_c REAL DEFAULT 0,seg_p REAL DEFAULT 0,seg_n REAL DEFAULT 0,ter_c REAL DEFAULT 0,ter_p REAL DEFAULT 0,ter_n REAL DEFAULT 0,qua_c REAL DEFAULT 0,qua_p REAL DEFAULT 0,qua_n REAL DEFAULT 0,qui_c REAL DEFAULT 0,qui_p REAL DEFAULT 0,qui_n REAL DEFAULT 0,sex_c REAL DEFAULT 0,sex_p REAL DEFAULT 0,sex_n REAL DEFAULT 0,UNIQUE(semana,ano));
    CREATE TABLE IF NOT EXISTS salas(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT,medico TEXT,horas_disp REAL DEFAULT 8.0,horas_ocup REAL DEFAULT 0.0,no_show INTEGER DEFAULT 0,perda REAL DEFAULT 0.0,ticket_hora REAL DEFAULT 0.0,mes TEXT,ano INTEGER);
    CREATE TABLE IF NOT EXISTS mod_tarefas(id INTEGER PRIMARY KEY AUTOINCREMENT,titulo TEXT,cargo_key TEXT DEFAULT 'gerente',responsavel TEXT,dri TEXT DEFAULT '',frequencia TEXT DEFAULT 'Diaria',bloco TEXT DEFAULT 'Abertura',horario TEXT DEFAULT '08:30',categoria TEXT DEFAULT 'Operacional',peso INTEGER DEFAULT 10,ativo INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS mod_execucao(id INTEGER PRIMARY KEY AUTOINCREMENT,tarefa_id INTEGER,colaborador TEXT,data_exec TEXT,concluida INTEGER DEFAULT 0,UNIQUE(tarefa_id,colaborador,data_exec));
    CREATE TABLE IF NOT EXISTS integra_pont(id INTEGER PRIMARY KEY AUTOINCREMENT,colaborador_id INTEGER,semana TEXT,ano INTEGER,entregas INTEGER DEFAULT 0,qualidade INTEGER DEFAULT 0,cultura INTEGER DEFAULT 0,indicadores INTEGER DEFAULT 0,melhoria INTEGER DEFAULT 0,obs TEXT DEFAULT '',UNIQUE(colaborador_id,semana,ano));
    CREATE TABLE IF NOT EXISTS onboarding(id INTEGER PRIMARY KEY AUTOINCREMENT,colaborador_id INTEGER,modulo TEXT,fase INTEGER DEFAULT 1,concluido INTEGER DEFAULT 0,data_conclusao TEXT);
    CREATE TABLE IF NOT EXISTS leads(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT,canal TEXT DEFAULT 'Instagram',sdr TEXT DEFAULT 'Aline',status TEXT DEFAULT 'Novo',temperatura TEXT DEFAULT 'Morno',tempo_resp INTEGER DEFAULT 0,compareceu INTEGER DEFAULT 0,convertido INTEGER DEFAULT 0,ticket REAL DEFAULT 0.0,motivo TEXT DEFAULT '',mes TEXT,ano INTEGER,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS orcamentos(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente TEXT,valor REAL DEFAULT 0,data_envio TEXT,temperatura TEXT DEFAULT 'Morno',objecao TEXT DEFAULT '',proxima_acao TEXT DEFAULT '',dri TEXT DEFAULT 'Bianca',prazo TEXT DEFAULT '',status TEXT DEFAULT 'Aberto',motivo_recusa TEXT DEFAULT '',criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS rfm(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente TEXT,ultima_visita TEXT,frequencia INTEGER DEFAULT 0,valor_total REAL DEFAULT 0,segmento TEXT DEFAULT 'Inativo recente',status_contato TEXT DEFAULT 'Nao contatado',proxima_acao TEXT DEFAULT '',dri TEXT DEFAULT 'Beatriz',resultado TEXT DEFAULT '',criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS indicacoes(id INTEGER PRIMARY KEY AUTOINCREMENT,pac_indicador TEXT,pac_indicado TEXT,contato TEXT DEFAULT '',data_ind TEXT,status TEXT DEFAULT 'Novo',dri TEXT DEFAULT 'Aline',convertido INTEGER DEFAULT 0,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS sbar(id INTEGER PRIMARY KEY AUTOINCREMENT,tipo TEXT,remetente TEXT,destinatario TEXT,situacao TEXT,background TEXT,avaliacao TEXT,recomendacao TEXT,dri_acao TEXT,prazo TEXT,data TEXT DEFAULT CURRENT_TIMESTAMP,resolvido INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS seguranca(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente TEXT,data_atend TEXT,responsavel TEXT DEFAULT 'Paloma',ch1 INTEGER DEFAULT 0,ch2 INTEGER DEFAULT 0,ch3 INTEGER DEFAULT 0,ch4 INTEGER DEFAULT 0,ch5 INTEGER DEFAULT 0,ch6 INTEGER DEFAULT 0,ch7 INTEGER DEFAULT 0,intercorrencia INTEGER DEFAULT 0,desc_inter TEXT DEFAULT '',d1_enviado INTEGER DEFAULT 0,d1_resposta TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS regua(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente TEXT,tipo TEXT DEFAULT 'Primeira Consulta',data_cons TEXT,st_dm1 TEXT DEFAULT 'Pendente',st_dp1 TEXT DEFAULT 'Pendente',st_dp3 TEXT DEFAULT 'Pendente',st_dp7 TEXT DEFAULT 'Pendente',st_dp14 TEXT DEFAULT 'Pendente',st_dp30 TEXT DEFAULT 'Pendente',st_recusa TEXT DEFAULT 'N/A',ticket REAL DEFAULT 0.0,fechou INTEGER DEFAULT 0,obs TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS briefing(id INTEGER PRIMARY KEY AUTOINCREMENT,data TEXT UNIQUE,responsavel TEXT DEFAULT '',cons_ag INTEGER DEFAULT 0,proc_ag INTEGER DEFAULT 0,conf INTEGER DEFAULT 0,gaps INTEGER DEFAULT 0,val_ag REAL DEFAULT 0,leads_pend INTEGER DEFAULT 0,orc_ab INTEGER DEFAULT 0,val_orc REAL DEFAULT 0,rfm_meta INTEGER DEFAULT 30,ind_meta INTEGER DEFAULT 5,ret_hoje INTEGER DEFAULT 0,cob_12h TEXT DEFAULT 'Beatriz',cob_13h TEXT DEFAULT 'Aline',dm1_pc INTEGER DEFAULT 0,dm1_ret INTEGER DEFAULT 0,dp1_pc INTEGER DEFAULT 0,dp1_ret INTEGER DEFAULT 0,fw3 INTEGER DEFAULT 0,fw7 INTEGER DEFAULT 0,fw14 INTEGER DEFAULT 0,pr1 TEXT DEFAULT '',pr2 TEXT DEFAULT '',pr3 TEXT DEFAULT '',dr1 TEXT DEFAULT '',dr2 TEXT DEFAULT '',dr3 TEXT DEFAULT '',obs TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS debriefing(id INTEGER PRIMARY KEY AUTOINCREMENT,data TEXT UNIQUE,responsavel TEXT DEFAULT '',rc REAL DEFAULT 0,rp REAL DEFAULT 0,rr REAL DEFAULT 0,ro REAL DEFAULT 0,di REAL DEFAULT 0,do_ REAL DEFAULT 0,da REAL DEFAULT 0,cons_r INTEGER DEFAULT 0,proc_r INTEGER DEFAULT 0,ns INTEGER DEFAULT 0,canc INTEGER DEFAULT 0,perda_ns REAL DEFAULT 0,leads_r INTEGER DEFAULT 0,tempo_r INTEGER DEFAULT 0,ag_g INTEGER DEFAULT 0,orc_f INTEGER DEFAULT 0,val_of REAL DEFAULT 0,rfm_r INTEGER DEFAULT 0,ind_s INTEGER DEFAULT 0,ind_r INTEGER DEFAULT 0,av_g INTEGER DEFAULT 0,dm1_ex INTEGER DEFAULT 0,dp1_ex INTEGER DEFAULT 0,fw_ex INTEGER DEFAULT 0,meta_bat INTEGER DEFAULT 0,conquista TEXT DEFAULT '',gargalo TEXT DEFAULT '',acao_am TEXT DEFAULT '',dri_am TEXT DEFAULT '',obs TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS okrs(id INTEGER PRIMARY KEY AUTOINCREMENT,objetivo TEXT,key_result TEXT,meta_val REAL DEFAULT 0,atual_val REAL DEFAULT 0,responsavel TEXT,trimestre TEXT,ano INTEGER,ativo INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS relatorios(id INTEGER PRIMARY KEY AUTOINCREMENT,nome_arquivo TEXT,conteudo TEXT,analise_ia TEXT,mes TEXT,ano INTEGER,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS usuarios(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT NOT NULL,login TEXT UNIQUE NOT NULL,senha_hash TEXT NOT NULL,nivel TEXT DEFAULT 'Operacional',cargo_key TEXT DEFAULT '',ativo INTEGER DEFAULT 1,ultimo_acesso TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS wh_mensagens(id INTEGER PRIMARY KEY AUTOINCREMENT,remetente TEXT,nome_collab TEXT,tipo TEXT DEFAULT 'texto',conteudo TEXT,interpretacao TEXT,acao_executada TEXT,status TEXT DEFAULT 'recebido',criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS wh_numeros(id INTEGER PRIMARY KEY AUTOINCREMENT,numero TEXT UNIQUE,nome TEXT,cargo_key TEXT,nivel TEXT DEFAULT 'Operacional',ativo INTEGER DEFAULT 1,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS precificacao(id INTEGER PRIMARY KEY AUTOINCREMENT,produto TEXT,custo_insumo REAL DEFAULT 0,custo_funcionario REAL DEFAULT 0,custo_equipamento REAL DEFAULT 0,custo_sala REAL DEFAULT 0,custo_total REAL DEFAULT 0,preco_venda REAL DEFAULT 0,imposto REAL DEFAULT 0,margem_pct REAL DEFAULT 0,ativo INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS custo_funcionario(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT,cargo TEXT,salario_bruto REAL DEFAULT 0,fgts REAL DEFAULT 0,inss REAL DEFAULT 0,ferias REAL DEFAULT 0,decimo_terceiro REAL DEFAULT 0,outros REAL DEFAULT 0,custo_total REAL DEFAULT 0,horas_mes INTEGER DEFAULT 176,custo_hora REAL DEFAULT 0,ativo INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS taxa_sala(id INTEGER PRIMARY KEY AUTOINCREMENT,nome TEXT,qtd INTEGER DEFAULT 1,custo_mes REAL DEFAULT 0,dias_mes INTEGER DEFAULT 22,horas_dia REAL DEFAULT 10,taxa_hora REAL DEFAULT 0,taxa_procedimento REAL DEFAULT 0,ativo INTEGER DEFAULT 1);
    """)
    conn.commit()
    # Seed equipe
    if conn.execute("SELECT COUNT(*) FROM colaboradores").fetchone()[0] == 0:
        for n,f,k,na,zg in [
            ("Dr. Vinícius Mariano","CEO","ceo","CEO / Proprietário","Estratégia e medicina funcional"),
            ("Dra. Bárbara Mariano","Diretora Técnica","barbara","CEO / Proprietário","Protocolos e qualidade assistencial"),
            ("Vanessa","Gerente Executiva","gerente","Gerente Executiva","Execução operacional e indicadores"),
            ("Bianca","Coord. Comercial e Closer","bianca","Gerente Executiva","Fechamento e conversão de alto valor"),
            ("Aline","Analista de Leads","aline","Operacional","Qualificação e gestão de pipeline"),
            ("Beatriz","Recepção Comercial + RFM","beatriz","Operacional","Acolhimento e reativação de base"),
            ("Paloma","Enfermeira Assistencial","paloma","Operacional","Cuidado técnico e segurança clínica"),
        ]:
            conn.execute("INSERT INTO colaboradores(nome,funcao,cargo_key,nivel_acesso,zona_genialidade) VALUES(?,?,?,?,?)",(n,f,k,na,zg))
    # Seed usuários
    if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        import hashlib
        for nome,login,pw,nivel,ck in [
            ("Dr. Vinícius Mariano","vinicius","Integrative@2026","CEO","ceo"),
            ("Dra. Bárbara Mariano","barbara","Barbara@2026","CEO","barbara"),
            ("Vanessa","gerente","Gerente@2026","Gerente","gerente"),
            ("Bianca","bianca","Bianca@2026","Operacional","bianca"),
            ("Aline","aline","Aline@2026","Operacional","aline"),
            ("Beatriz","beatriz","Beatriz@2026","Operacional","beatriz"),
            ("Paloma","paloma","Paloma@2026","Operacional","paloma"),
        ]:
            conn.execute("INSERT INTO usuarios(nome,login,senha_hash,nivel,cargo_key) VALUES(?,?,?,?,?)",
                (nome,login,hashlib.sha256(pw.encode()).hexdigest(),nivel,ck))
    # Seed taxa sala
    if conn.execute("SELECT COUNT(*) FROM taxa_sala").fetchone()[0] == 0:
        for nome,qtd,custo,horas in [("Sala Atendimento",3,660,10),("Sala Procedimentos",2,880,10)]:
            taxa_h = round(custo/(22*horas),2) if horas else 0
            conn.execute("INSERT INTO taxa_sala(nome,qtd,custo_mes,dias_mes,horas_dia,taxa_hora) VALUES(?,?,?,22,?,?)",(nome,qtd,custo,horas,taxa_h))
    # Seed custo funcionários
    if conn.execute("SELECT COUNT(*) FROM custo_funcionario").fetchone()[0] == 0:
        for nome,cargo,sal in [("Vanessa","Gerente",5000),("Bianca","Closer",3500),("Aline","Analista Leads",2800),("Beatriz","Recepção",2500),("Paloma","Enfermeira",3200)]:
            fgts=sal*0.08; inss=sal*0.20; fer=sal*0.133; dec=sal*0.083; total=sal+fgts+inss+fer+dec+50
            ch=round(total/176,2)
            conn.execute("INSERT INTO custo_funcionario(nome,cargo,salario_bruto,fgts,inss,ferias,decimo_terceiro,outros,custo_total,custo_hora) VALUES(?,?,?,?,?,?,?,50,?,?)",(nome,cargo,sal,fgts,inss,fer,dec,total,ch))
    conn.commit()
    conn.close()

init_db()


# ══════════════════════════════════════════════════════════════
# AUTENTICAÇÃO
# ══════════════════════════════════════════════════════════════
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def autenticar(login, pw):
    conn = get_conn()
    r = conn.execute("SELECT id,nome,nivel,cargo_key FROM usuarios WHERE login=? AND senha_hash=? AND ativo=1",
        (login.strip().lower(), hash_pw(pw))).fetchone()
    if r:
        conn.execute("UPDATE usuarios SET ultimo_acesso=? WHERE id=?",(datetime.now().isoformat(),r[0]))
        conn.commit()
    conn.close()
    return r

# ══════════════════════════════════════════════════════════════
# HELPERS & COMPONENTES
# ══════════════════════════════════════════════════════════════
def fmt(v):
    if v is None: return "R$ 0,00"
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def fmt_pct(v): return f"{v:.1f}%"
def pct_safe(a,b): return round((a/b)*100,1) if b else 0.0

def semaforo(p,limiar=85):
    if p>=100: return "🟢",GREEN
    if p>=limiar: return "🟡",AMBER
    return "🔴",RED

def kpi_card(titulo, valor, sub="", cor=WHITE, delta=None, icon=""):
    delta_html = ""
    if delta is not None:
        dcor = GREEN if delta >= 0 else RED
        darrow = "↑" if delta >= 0 else "↓"
        delta_html = f'<div style="font-size:11px;color:{dcor};margin-top:4px;font-weight:600">{darrow} {abs(delta):.1f}% vs mês ant.</div>'
    return f"""<div style="background:{BG3};border:1px solid {BORDER};border-radius:12px;
        padding:20px;transition:all 0.2s;position:relative;overflow:hidden">
        <div style="position:absolute;top:0;right:0;width:3px;height:100%;background:{cor};opacity:0.7"></div>
        <div style="font-size:10px;color:{GRAY};text-transform:uppercase;letter-spacing:0.1em;
            font-weight:600;margin-bottom:10px">{icon} {titulo}</div>
        <div style="font-size:1.7rem;font-weight:700;color:{cor};letter-spacing:-0.02em;line-height:1">{valor}</div>
        {f'<div style="font-size:11px;color:{GRAY};margin-top:6px">{sub}</div>' if sub else ""}
        {delta_html}
    </div>"""

def kpi_grid(items, cols=4):
    html = f'<div style="display:grid;grid-template-columns:repeat({cols},1fr);gap:16px;margin-bottom:24px">'
    for item in items:
        titulo,valor,sub,cor = item[0],item[1],item[2],item[3]
        delta = item[4] if len(item)>4 else None
        icon = item[5] if len(item)>5 else ""
        html += kpi_card(titulo,valor,sub,cor,delta,icon)
    return html + "</div>"

def titulo_secao(t, sub="", icon=""):
    return f"""<div style="margin-bottom:{'6px' if sub else '20px'}">
        <div style="display:flex;align-items:center;gap:10px;margin-bottom:4px">
            <div style="width:3px;height:22px;background:{AMBER};border-radius:2px;flex-shrink:0"></div>
            <h2 style="margin:0;font-size:1.2rem;font-weight:700;color:{WHITE};letter-spacing:-0.02em">{icon} {t}</h2>
        </div>
        <div style="height:1px;background:linear-gradient(90deg,{AMBER}44,transparent);margin:8px 0"></div>
        {f'<p style="margin:0 0 16px 13px;font-size:12px;color:{GRAY};line-height:1.6">{sub}</p>' if sub else '<div style="margin-bottom:16px"></div>'}
    </div>"""

def barra(p, label="", cor=None):
    c = cor or (RED if p<70 else AMBER if p<100 else GREEN)
    return f"""<div style="margin-bottom:12px">
        <div style="display:flex;justify-content:space-between;font-size:11px;font-weight:500;
            color:{GRAY};margin-bottom:5px">
            <span>{label}</span><span style="color:{c};font-weight:600">{min(int(p),100)}%</span>
        </div>
        <div style="height:4px;background:{BORDER};border-radius:99px;overflow:hidden">
            <div style="height:4px;width:{min(int(p),100)}%;background:{c};border-radius:99px;
                transition:width 0.6s cubic-bezier(0.16,1,0.3,1)"></div>
        </div>
    </div>"""

def badge(texto, cor=AMBER):
    txt = "#000" if cor in (AMBER,AMBER2) else WHITE
    return f'<span style="background:{cor}22;color:{cor};border:1px solid {cor}44;border-radius:99px;padding:3px 10px;font-size:10px;font-weight:600;letter-spacing:0.04em">{texto}</span>'

def dre_linha(label, valor, pct_val, cor, destaque=False):
    if destaque:
        return f"""<div style="background:{AMBER}11;border:1px solid {AMBER}33;border-radius:8px;
            padding:10px 16px;margin-bottom:3px;display:flex;justify-content:space-between;align-items:center">
            <span style="font-size:13px;font-weight:700;color:{WHITE};letter-spacing:0.01em">{label}</span>
            <div style="display:flex;gap:16px;align-items:center">
                <span style="font-size:10px;color:{GRAY}">{pct_val:.1f}%</span>
                <span style="font-size:15px;font-weight:700;color:{cor}">{fmt(valor)}</span>
            </div>
        </div>"""
    return f"""<div style="border-bottom:1px solid {BORDER};padding:8px 16px;margin-bottom:2px;
        display:flex;justify-content:space-between;align-items:center">
        <span style="font-size:12px;color:{GRAY}">{label}</span>
        <div style="display:flex;gap:16px;align-items:center">
            <span style="font-size:10px;color:{GRAY2}">{pct_val:.1f}%</span>
            <span style="font-size:13px;font-weight:500;color:{cor}">{fmt(valor)}</span>
        </div>
    </div>"""

def gerar_pdf_relatorio(titulo, secoes):
    if not HAS_PDF: return None
    pdf = FPDF(); pdf.add_page(); pdf.set_margins(15,15,15)
    pdf.set_fill_color(10,10,11); pdf.rect(0,0,210,30,'F')
    pdf.set_font("Helvetica","B",14); pdf.set_text_color(245,158,11)
    pdf.set_xy(15,8); pdf.cell(0,8,"LAB METRICS — INTEGRATIVE CAMPINAS",ln=True)
    pdf.set_font("Helvetica","",9); pdf.set_text_color(161,161,170)
    pdf.set_xy(15,18); pdf.cell(0,6,f"{titulo}  |  {datetime.now().strftime('%d/%m/%Y %H:%M')}",ln=True)
    pdf.set_fill_color(245,158,11); pdf.rect(0,30,210,2,'F')
    pdf.set_y(40); pdf.set_text_color(10,10,11)
    for sec_t, linhas in secoes:
        pdf.set_fill_color(24,24,27); pdf.set_text_color(245,158,11)
        pdf.set_font("Helvetica","B",9)
        pdf.cell(0,8,f"  {sec_t.upper()}",ln=True,fill=True)
        pdf.set_text_color(39,39,42)
        for i,linha in enumerate(linhas):
            pdf.set_fill_color(245,245,245) if i%2==0 else pdf.set_fill_color(255,255,255)
            pdf.set_font("Helvetica","",9)
            pdf.cell(0,7,f"  {linha}",ln=True,fill=True)
        pdf.ln(3)
    buf = io.BytesIO(); pdf.output(buf); return buf.getvalue()

def bloco_exportar(nome_modulo, secoes_texto, texto_whats):
    st.markdown(f"""<div style="background:{BG2};border:1px solid {BORDER};border-top:2px solid {AMBER};
        padding:16px 20px;margin-top:32px;border-radius:0 0 10px 10px;display:flex;align-items:center;gap:10px">
        <div style="width:20px;height:2px;background:{AMBER}"></div>
        <span style="font-size:10px;color:{AMBER};text-transform:uppercase;letter-spacing:0.12em;font-weight:700">
            Exportar — {nome_modulo}
        </span>
    </div>""", unsafe_allow_html=True)
    c1,c2,c3 = st.columns(3)
    with c1:
        if HAS_PDF:
            pdf_b = gerar_pdf_relatorio(nome_modulo, secoes_texto)
            if pdf_b:
                st.download_button("⬇ Baixar PDF",pdf_b,f"relatorio_{nome_modulo.lower().replace(' ','_')}_{date.today()}.pdf","application/pdf",use_container_width=True,key=f"pdf_{nome_modulo}")
    with c2:
        st.download_button("⬇ Baixar TXT",texto_whats.encode(),"relatorio.txt","text/plain",use_container_width=True,key=f"txt_{nome_modulo}")
    with c3:
        st.text_area("📋 Copiar para WhatsApp",value=texto_whats,height=100,key=f"wa_{nome_modulo}",help="Ctrl+A e Ctrl+C para copiar")


# ══════════════════════════════════════════════════════════════
# DADOS HISTÓRICOS (do DRE real importado)
# ══════════════════════════════════════════════════════════════
HISTORICO_FAT = {
    "01/2024":73492,"02/2024":83347,"03/2024":102441,"04/2024":133671,
    "05/2024":102414,"06/2024":94666,"07/2024":115263,"08/2024":150427,
    "09/2024":134605,"10/2024":150993,"11/2024":130170,
    "01/2025":100545,"02/2025":180449,"03/2025":204348,"04/2025":210032,
    "05/2025":244339,"06/2025":188523,"07/2025":253780,"08/2025":270505,
    "09/2025":206645,"10/2025":285669,"11/2025":249248,"12/2025":195158,
}
CRESCIMENTO_ANUAL = {"2024":1291485,"2025":2484690}

# ══════════════════════════════════════════════════════════════
# TELA DE LOGIN
# ══════════════════════════════════════════════════════════════
def tela_login():
    st.markdown(f"""
    <style>
    .main{{background:{BG}!important;}}
    .block-container{{padding:0!important;max-width:100%!important;}}
    [data-testid="stVerticalBlock"]{{gap:0!important;}}
    [data-testid="stColumns"]{{gap:0!important;align-items:stretch;}}
    [data-testid="stColumn"]{{padding:0!important;}}
    [data-testid="stColumn"]>div{{padding:0!important;}}
    section[data-testid="stSidebar"]{{display:none!important;width:0!important;}}
    header{{display:none!important;}}
    .stTextInput>div>div>input{{background:{BG2}!important;border:1px solid {BORDER}!important;
        border-radius:8px!important;color:{WHITE}!important;font-size:1rem!important;padding:14px 16px!important;}}
    .stTextInput>div>div>input:focus{{border-color:{AMBER}!important;box-shadow:0 0 0 3px {AMBER}22!important;}}
    .stButton>button{{background:{AMBER}!important;color:#000!important;border:none!important;
        border-radius:8px!important;font-weight:700!important;font-size:1rem!important;
        padding:14px!important;width:100%!important;height:48px!important;}}
    .stButton>button:hover{{background:{AMBER2}!important;transform:translateY(-1px)!important;}}
    </style>""", unsafe_allow_html=True)
    col_l, col_r = st.columns([5,4])
    with col_l:
        # Crescimento histórico para exibir
        fat_2024 = f"R$ {CRESCIMENTO_ANUAL['2024']/1e6:.1f}M"
        fat_2025 = f"R$ {CRESCIMENTO_ANUAL['2025']/1e6:.1f}M"
        cresc = round((CRESCIMENTO_ANUAL['2025']-CRESCIMENTO_ANUAL['2024'])/CRESCIMENTO_ANUAL['2024']*100)
        st.markdown(
            f'<div style="background:{BG2};min-height:100vh;padding:60px 50px;'
            f'display:flex;flex-direction:column;justify-content:space-between;'
            f'border-right:1px solid {BORDER}">'
            f'<div>'
            f'<div style="display:flex;align-items:center;gap:10px;margin-bottom:32px">'
            f'<div style="width:32px;height:32px;background:{AMBER};border-radius:8px;'
            f'display:flex;align-items:center;justify-content:center;font-size:16px">🩺</div>'
            f'<div>'
            f'<div style="font-size:1rem;font-weight:700;color:{WHITE};letter-spacing:-0.01em">LAB Metrics</div>'
            f'<div style="font-size:10px;color:{GRAY};letter-spacing:0.08em;text-transform:uppercase">Gestão 360°</div>'
            f'</div></div>'
            f'<div style="height:1px;background:{BORDER};margin-bottom:40px"></div>'
            f'<div style="font-size:2.6rem;font-weight:800;color:{WHITE};letter-spacing:-0.04em;line-height:1;margin-bottom:16px">'
            f'A arquitetura<br>de crescimento<br><span style="color:{AMBER}">previsível.</span></div>'
            f'<div style="font-size:0.95rem;color:{GRAY};line-height:1.7;max-width:380px;margin-bottom:36px">'
            f'Clínicas de medicina funcional e integrativa que operam com método '
            f'crescem 2,4x mais rápido que a média do setor. Este sistema é a operacionalização '
            f'desse método em tempo real.</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px">'
            f'<div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {AMBER};padding:14px;border-radius:8px">'
            f'<div style="font-size:8px;color:{GRAY};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">Faturamento 2024</div>'
            f'<div style="font-size:1.4rem;font-weight:700;color:{AMBER}">{fat_2024}</div></div>'
            f'<div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {GREEN};padding:14px;border-radius:8px">'
            f'<div style="font-size:8px;color:{GRAY};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">Faturamento 2025</div>'
            f'<div style="font-size:1.4rem;font-weight:700;color:{GREEN}">{fat_2025}</div></div>'
            f'<div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {BLUE};padding:14px;border-radius:8px">'
            f'<div style="font-size:8px;color:{GRAY};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:4px">Crescimento</div>'
            f'<div style="font-size:1.4rem;font-weight:700;color:{BLUE}">+{cresc}%</div></div>'
            f'</div></div>'
            f'<div style="border-top:1px solid {BORDER};padding-top:20px">'
            f'<div style="font-size:10px;color:{GRAY2};font-style:italic">'
            f'&ldquo;Ideia é prata. Mentalidade é ouro. '
            f'<span style="color:{AMBER};font-style:normal;font-weight:600">Execução é diamante.</span>&rdquo;</div>'
            f'<div style="font-size:9px;color:{GRAY2};margin-top:6px;text-transform:uppercase;letter-spacing:0.08em">'
            f'Projeto Ponteiro · Método AME · Programa Integra</div>'
            f'</div></div>',
            unsafe_allow_html=True)
    with col_r:
        st.markdown(f"""
<style>
[data-testid="column"]:nth-child(2){{background:{BG};}}
[data-testid="column"]:nth-child(2)>div:first-child{{
    padding:60px 52px!important;max-width:420px;margin:0 auto;
    display:flex;flex-direction:column;justify-content:center;min-height:100vh;}}
</style>""", unsafe_allow_html=True)
        st.markdown(
            f'<div style="font-size:9px;color:{GRAY};text-transform:uppercase;'
            f'letter-spacing:0.18em;font-weight:600;margin-bottom:10px">Acesso Restrito</div>'
            f'<div style="font-size:2rem;font-weight:800;color:{WHITE};'
            f'letter-spacing:-0.03em;line-height:1;margin-bottom:4px">Entrar no<br>Sistema</div>'
            f'<div style="width:40px;height:3px;background:{AMBER};border-radius:2px;margin:14px 0 32px"></div>',
            unsafe_allow_html=True)
        login_i = st.text_input("USUÁRIO", placeholder="seu.login", key="login_input")
        pw_i    = st.text_input("SENHA",   type="password", placeholder="••••••••", key="pw_input")
        st.markdown("<div style='height:12px'></div>", unsafe_allow_html=True)
        if st.button("Entrar →", use_container_width=True, key="btn_login"):
            if not login_i or not pw_i:
                st.error("Preencha usuário e senha.")
            else:
                user = autenticar(login_i, pw_i)
                if user:
                    st.session_state.user_id    = user[0]
                    st.session_state.user_nome  = user[1]
                    st.session_state.user_nivel = user[2]
                    st.session_state.user_cargo = user[3]
                    st.session_state.logado     = True
                    st.session_state.aba        = "🏠  Home"
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")


# ══════════════════════════════════════════════════════════════
# HOME — TELA INICIAL COM BRIEFING DINÂMICO
# ══════════════════════════════════════════════════════════════
ACOES_PONTEIRO = {
    0: {  # Segunda
        "tema": "Abertura Estratégica da Semana",
        "foco": "Agenda, metas e alinhamento de equipe",
        "acoes": [
            {"titulo":"Confirmar 100% da agenda da semana","dri":"Vanessa","impacto":"Elimina no-show e maximiza receita prevista","kpi":"Taxa de ocupação"},
            {"titulo":"Revisar pipeline de orçamentos quentes com Bianca","dri":"Bianca","impacto":"Cada orçamento quente sem ação em 24h representa perda de receita real","kpi":"Orçamentos fechados"},
            {"titulo":"Definir meta diária de ritmo e comunicar à equipe","dri":"Vanessa","impacto":"Equipe com meta clara converte 40% mais","kpi":"Meta diária atingida"},
        ],
        "insight": "Segunda-feira é o dia de maior poder de decisão da semana. A equipe está descansada, receptiva e com energia para executar. O que você prioriza hoje determina o ritmo dos próximos cinco dias."
    },
    1: {  # Terça
        "tema": "Conversão e Pipeline Comercial",
        "foco": "Leads, follow-up e fechamento de orçamentos",
        "acoes": [
            {"titulo":"Executar follow-up D+1 em todos os leads de ontem","dri":"Aline","impacto":"Resposta em até 5min aumenta conversão em 21x vs. resposta em 1h","kpi":"Taxa de conversão de leads"},
            {"titulo":"Contato RFM com 30 pacientes inativos da base","dri":"Beatriz","impacto":"Reativação custa 5x menos que aquisição de novo paciente","kpi":"Reativação RFM"},
            {"titulo":"Fechar ao menos 2 orçamentos abertos hoje","dri":"Bianca","impacto":"Cada orçamento fechado representa receita imediata sem custo de aquisição","kpi":"Valor fechado no dia"},
        ],
        "insight": "A maior alavanca de faturamento subutilizada em qualquer clínica é a base de pacientes inativos. Pacientes que já confiaram em você uma vez têm 67% mais probabilidade de retornar quando bem abordados."
    },
    2: {  # Quarta
        "tema": "Execução Assistencial e Experiência",
        "foco": "Qualidade clínica, D+1 e indicações",
        "acoes": [
            {"titulo":"Garantir envio de D+1 para todos os atendimentos de ontem","dri":"Paloma","impacto":"D+1 reduz abandono de protocolo em 60% e gera indicações espontâneas","kpi":"D+1 executados"},
            {"titulo":"Solicitar 5 indicações ativas no final de cada atendimento","dri":"Beatriz","impacto":"Lead de indicação converte 3x mais e tem ticket 28% maior","kpi":"Indicações recebidas"},
            {"titulo":"Revisar taxa de ocupação das salas e identificar horários vazios","dri":"Vanessa","impacto":"Cada hora de sala vazia é receita irrecuperável. Uma poltrona ociosa = R$ 50/h perdidos","kpi":"Taxa de ocupação"},
        ],
        "insight": "A experiência clínica é o principal motor de retenção e indicação. Clínicas que executam o protocolo D+1 sistematicamente reduzem churn em 40% e aumentam o LTV médio do paciente em 2,8x."
    },
    3: {  # Quinta
        "tema": "Financeiro e Margem",
        "foco": "Custos, margem e ponto de equilíbrio",
        "acoes": [
            {"titulo":"Conferir caixa do dia e atualizar DRE mensal","dri":"Vanessa","impacto":"Gestão financeira em tempo real evita surpresas no fechamento mensal","kpi":"EBITDA do dia"},
            {"titulo":"Identificar ao menos 1 custo fixo passível de renegociação","dri":"Dr. Vinícius","impacto":"Redução de R$ 1.000 em custos fixos equivale a R$ 1.340 de receita bruta adicional","kpi":"Custos fixos totais"},
            {"titulo":"Verificar margem por procedimento e ajustar tabela se necessário","dri":"Dr. Vinícius","impacto":"Precificação inadequada é a causa de trabalho intenso com margem comprimida","kpi":"Margem de contribuição"},
        ],
        "insight": "Crescimento de faturamento sem gestão de margem é uma ilusão que se desfaz no fechamento. Clínicas com EBITDA acima de 25% têm estrutura para crescer sem dependência de capital externo."
    },
    4: {  # Sexta
        "tema": "Fechamento Semanal e Previsão",
        "foco": "Resultados, OKRs e planejamento da próxima semana",
        "acoes": [
            {"titulo":"Fechar SBAR semanal e enviar para Dr. Vinícius até 17h","dri":"Vanessa","impacto":"Liderança informada decide melhor e mais rápido","kpi":"SBAR enviado"},
            {"titulo":"Revisar OKRs da semana e atualizar percentual de progresso","dri":"Dr. Vinícius","impacto":"OKRs revisados semanalmente têm 4x mais chance de serem alcançados","kpi":"OKRs em progresso"},
            {"titulo":"Confirmar agenda da próxima semana e acionar RFM para gaps","dri":"Beatriz","impacto":"Agenda cheia na segunda elimina a correria para fechar meta no fim do mês","kpi":"Ocupação semana seguinte"},
        ],
        "insight": "Sexta-feira não é o fim da semana. É a preparação para a semana seguinte. Clínicas que fecham a sexta com agenda confirmada e metas claras iniciam segunda-feira com vantagem competitiva real."
    },
}

def tela_home():
    conn = get_conn()
    clin = conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    mes_a = MESES[datetime.now().month-1]; ano_a = datetime.now().year
    dre_a = conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?",(mes_a,ano_a)).fetchone()
    leads_a = conn.execute("SELECT COUNT(*),SUM(convertido),AVG(tempo_resp) FROM leads WHERE mes=? AND ano=?",(mes_a,ano_a)).fetchone()
    exec_h = conn.execute("SELECT COUNT(*),SUM(concluida) FROM mod_execucao WHERE data_exec=?",(date.today().isoformat(),)).fetchone()
    orc_q = conn.execute("SELECT COUNT(*) FROM orcamentos WHERE temperatura='Quente' AND status='Aberto'"  ).fetchone()[0]
    sbar_p = conn.execute("SELECT COUNT(*) FROM sbar WHERE resolvido=0").fetchone()[0]
    conn.close()

    rb = sum([(dre_a[i] or 0) for i in [3,4,5,6]]) if dre_a else 0
    meta = clin[2] if clin else 280000
    pct_meta = pct_safe(rb, meta)
    l_tot = leads_a[0] or 0; l_conv = leads_a[1] or 0
    tx_conv = pct_safe(int(l_conv or 0), int(l_tot or 1))
    score_mod = min(round((exec_h[1] or 0)/max(exec_h[0] or 1,1)*100,1),100) if exec_h else 0
    cor_meta = GREEN if pct_meta>=80 else AMBER if pct_meta>=50 else RED

    # Topbar
    st.markdown(f"""<div style="background:{BG2};border-bottom:1px solid {BORDER};
        padding:12px 28px;display:flex;justify-content:space-between;align-items:center;
        margin:-1.5rem -2rem 28px;position:sticky;top:0;z-index:100">
        <div style="display:flex;align-items:center;gap:12px">
            <div style="width:28px;height:28px;background:{AMBER};border-radius:6px;
                display:flex;align-items:center;justify-content:center;font-size:14px">🩺</div>
            <div>
                <div style="font-size:0.9rem;font-weight:700;color:{WHITE};letter-spacing:-0.01em">LAB Metrics</div>
                <div style="font-size:10px;color:{GRAY}">Gestão 360° · Integrative Campinas</div>
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:16px">
            <div style="font-size:11px;color:{GRAY}">{date.today().strftime('%A, %d de %B de %Y').capitalize()}</div>
            <div style="background:{BG3};border:1px solid {BORDER};border-radius:8px;padding:6px 14px">
                <span style="font-size:11px;color:{WHITE};font-weight:600">
                    {st.session_state.get('user_nome','Usuário').split()[0]}
                </span>
                <span style="font-size:10px;color:{GRAY}"> · {st.session_state.get('user_nivel','')}</span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # Briefing dinâmico do dia
    dow = datetime.now().weekday()
    if dow > 4: dow = 0  # fim de semana → usa segunda
    plano = ACOES_PONTEIRO[dow]
    dia_nome = ["Segunda","Terça","Quarta","Quinta","Sexta","Sábado","Domingo"][datetime.now().weekday()]

    st.markdown(f"""<div style="background:linear-gradient(135deg,{AMBER}11 0%,{BG2} 100%);
        border:1px solid {AMBER}33;border-radius:16px;padding:28px 32px;margin-bottom:24px">
        <div style="display:flex;align-items:flex-start;justify-content:space-between;gap:20px;flex-wrap:wrap">
            <div style="flex:1;min-width:280px">
                <div style="font-size:10px;color:{AMBER};text-transform:uppercase;letter-spacing:0.15em;
                    font-weight:700;margin-bottom:6px">{dia_nome}-feira · {plano['tema']}</div>
                <div style="font-size:1.6rem;font-weight:800;color:{WHITE};letter-spacing:-0.03em;
                    line-height:1.1;margin-bottom:12px">
                    As 3 ações que movem<br>o ponteiro <span style="color:{AMBER}">hoje.</span>
                </div>
                <div style="font-size:13px;color:{GRAY};line-height:1.7;max-width:560px;
                    font-style:italic;border-left:2px solid {AMBER}44;padding-left:14px">
                    {plano['insight']}
                </div>
            </div>
            <div style="background:{BG3};border:1px solid {BORDER};border-radius:12px;
                padding:16px 20px;min-width:200px">
                <div style="font-size:9px;color:{GRAY};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">Meta do mês</div>
                <div style="font-size:1.6rem;font-weight:700;color:{cor_meta}">{pct_meta:.0f}%</div>
                <div style="font-size:11px;color:{GRAY};margin-top:4px">{fmt(rb)} de {fmt(meta)}</div>
                <div style="height:4px;background:{BORDER};border-radius:99px;margin-top:10px;overflow:hidden">
                    <div style="height:4px;width:{min(pct_meta,100):.1f}%;background:{cor_meta};border-radius:99px"></div>
                </div>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # 3 ações do dia
    cores_acao = [AMBER, BLUE, PURPLE]
    nums = ["01","02","03"]
    html_acoes = '<div style="display:grid;grid-template-columns:repeat(3,1fr);gap:16px;margin-bottom:24px">'
    for i, acao in enumerate(plano["acoes"]):
        cor_a = cores_acao[i]
        html_acoes += f"""<div style="background:{BG3};border:1px solid {BORDER};
            border-top:3px solid {cor_a};border-radius:12px;padding:20px">
            <div style="font-size:2rem;font-weight:800;color:{cor_a}44;letter-spacing:-0.05em;margin-bottom:8px">{nums[i]}</div>
            <div style="font-size:13px;font-weight:700;color:{WHITE};line-height:1.4;margin-bottom:10px">{acao['titulo']}</div>
            <div style="font-size:11px;color:{GRAY};line-height:1.6;margin-bottom:12px">{acao['impacto']}</div>
            <div style="display:flex;justify-content:space-between;align-items:center">
                <span style="font-size:10px;color:{cor_a};font-weight:600;background:{cor_a}11;
                    border-radius:4px;padding:3px 8px">DRI: {acao['dri']}</span>
                <span style="font-size:10px;color:{GRAY2}">KPI: {acao['kpi']}</span>
            </div>
        </div>"""
    html_acoes += "</div>"
    st.markdown(html_acoes, unsafe_allow_html=True)

    # KPIs rápidos
    st.markdown(kpi_grid([
        ("Faturamento do Mês", fmt(rb), f"{pct_meta:.0f}% da meta", cor_meta, None, "💰"),
        ("Conversão de Leads", f"{tx_conv:.1f}%", f"{int(l_conv or 0)} de {l_tot} leads", GREEN if tx_conv>=30 else RED, None, "📈"),
        ("Score MOD Equipe", f"{score_mod:.1f}%", "meta: 85%", GREEN if score_mod>=85 else RED, None, "✅"),
        ("Alertas Críticos", str(orc_q+sbar_p), f"{orc_q} orç. quentes · {sbar_p} SBAR", RED if (orc_q+sbar_p)>0 else GREEN, None, "🚨"),
    ]), unsafe_allow_html=True)

    # Alertas críticos
    if orc_q > 0:
        st.error(f"🔥 {orc_q} orçamento(s) QUENTE(S) sem próxima ação definida. Bianca, acionar agora.")
    if sbar_p > 0:
        st.warning(f"📣 {sbar_p} comunicado(s) no Diário de Bordo aguardando resolução.")

    # Crescimento histórico
    st.markdown("---")
    st.markdown(titulo_secao("Crescimento Histórico", "Faturamento mensal realizado vs. trajetória de escala — dados reais da clínica","📊"), unsafe_allow_html=True)
    df_hist = pd.DataFrame([{"Mês":k,"Faturamento":v} for k,v in HISTORICO_FAT.items()])
    df_hist["Meta"] = [meta]*len(df_hist)
    col1, col2 = st.columns([3,1])
    with col1:
        st.bar_chart(df_hist.set_index("Mês")[["Faturamento"]], color=AMBER, height=280)
    with col2:
        fat_media_2024 = sum(v for k,v in HISTORICO_FAT.items() if "2024" in k) / len([k for k in HISTORICO_FAT if "2024" in k])
        fat_media_2025 = sum(v for k,v in HISTORICO_FAT.items() if "2025" in k) / len([k for k in HISTORICO_FAT if "2025" in k])
        cresc_medio = pct_safe(fat_media_2025-fat_media_2024, fat_media_2024)
        st.markdown(kpi_grid([
            ("Ticket Médio 2024", fmt(fat_media_2024), "média mensal", AMBER),
            ("Ticket Médio 2025", fmt(fat_media_2025), "média mensal", GREEN),
            ("Crescimento YoY", f"+{cresc_medio:.0f}%", "2024→2025", BLUE),
            ("Melhor Mês", fmt(max(HISTORICO_FAT.values())), "Out/2025", PURPLE),
        ], cols=1), unsafe_allow_html=True)

    # Grade de módulos
    st.markdown("---")
    MODULOS_HOME = [
        ("🩺","Cockpit CEO","Visão executiva 360° com custos, DRE e OKRs","#3B82F6","🩺  Cockpit CEO"),
        ("📊","Painel DNA","Metas, Briefing, Debriefing, Salas e Réguas","#F59E0B","📊  Painel DNA"),
        ("📈","Comercial Hub","Leads, RFM, Indicações e Orçamentos SPIN","#10B981","📈  Comercial Hub"),
        ("💡","Estratégia de Preços","Taxa de sala, custo/funcionário e precificação","#8B5CF6","💡  Estratégia de Preços"),
        ("💰","DRE Gerencial","Demonstrativo de resultado com análise de margem","#F59E0B","💰  DRE Gerencial"),
        ("🎓","Programa Integra","MOD, onboarding e pontuação semanal","#10B981","🎓  Programa Integra"),
        ("🩻","Segurança Assistencial","Checklist clínico e protocolo D+1","#EF4444","🩻  Segurança Assistencial"),
        ("📓","Diário de Bordo","Comunicação estruturada SBAR","#52525B","📓  Diário de Bordo"),
        ("📚","Biblioteca","Manual operacional e glossário executivo","#8B5CF6","📚  Biblioteca"),
        ("🧬","Importar Dados","Support Clinic e análise por IA","#EF4444","🧬  Importar Dados"),
        ("🤖","Assistente IA","Consultor executivo digital 24/7","#3B82F6","🤖  Assistente IA"),
        ("⚙️","Configurações","Clínica, equipe e integrações","#52525B","⚙️  Configurações"),
    ]
    st.markdown(titulo_secao("Módulos do Sistema","Navegue diretamente pelo módulo desejado","🗂️"), unsafe_allow_html=True)
    linhas_mod = [MODULOS_HOME[i:i+4] for i in range(0,len(MODULOS_HOME),4)]
    for linha in linhas_mod:
        cols_m = st.columns(4)
        for col_m, (emoji, nome, desc, cor_m, aba_key) in zip(cols_m, linha):
            with col_m:
                if st.button(f"{emoji} {nome}", key=f"mod_{aba_key}", use_container_width=True, help=desc):
                    st.session_state.aba = aba_key; st.rerun()
                st.markdown(f'<div style="font-size:10px;color:{GRAY};text-align:center;margin-top:-4px;margin-bottom:12px">{desc[:36]}{"…" if len(desc)>36 else ""}</div>', unsafe_allow_html=True)


# ══════════════════════════════════════════════════════════════
# CONTROLE DE FLUXO
# ══════════════════════════════════════════════════════════════
if "logado" not in st.session_state:
    st.session_state.logado     = False
    st.session_state.user_nome  = ""
    st.session_state.user_nivel = ""
    st.session_state.user_cargo = ""
    st.session_state.aba        = "🏠  Home"

if not st.session_state.logado:
    tela_login(); st.stop()

# Sidebar pós-login
with st.sidebar:
    st.markdown(f"""<div style="padding:16px 12px 8px">
        <div style="display:flex;align-items:center;gap:8px;margin-bottom:12px">
            <div style="width:24px;height:24px;background:{AMBER};border-radius:6px;
                display:flex;align-items:center;justify-content:center;font-size:12px">🩺</div>
            <div>
                <div style="font-size:0.85rem;font-weight:700;color:{WHITE}">LAB Metrics</div>
                <div style="font-size:9px;color:{GRAY}">Gestão 360°</div>
            </div>
        </div>
        <div style="background:{BG3};border:1px solid {BORDER};border-radius:8px;
            padding:8px 12px;margin-bottom:12px">
            <div style="font-size:9px;color:{GRAY};text-transform:uppercase;letter-spacing:0.08em;margin-bottom:2px">Usuário</div>
            <div style="font-size:12px;color:{WHITE};font-weight:600">{st.session_state.user_nome.split()[0]}</div>
            <div style="font-size:10px;color:{GRAY}">{st.session_state.user_nivel}</div>
        </div>
    </div>""", unsafe_allow_html=True)
    c1s,c2s = st.columns([3,2])
    with c1s: mes_sel = st.selectbox("M",MESES,index=datetime.now().month-1,label_visibility="collapsed")
    with c2s: ano_sel = st.number_input("A",value=datetime.now().year,min_value=2020,max_value=2030,label_visibility="collapsed")
    st.markdown(f'<div style="height:1px;background:{BORDER};margin:8px 0"></div>',unsafe_allow_html=True)

    NAV_GRUPOS = [
        ("ESTRATÉGICO", ["🏠  Home","🩺  Cockpit CEO","📊  Painel DNA","💰  DRE Gerencial","📐  OKRs"]),
        ("COMERCIAL", ["📈  Comercial Hub"]),
        ("FINANCEIRO / PREÇOS", ["💡  Estratégia de Preços"]),
        ("OPERACIONAL", ["🎓  Programa Integra","🩻  Segurança Assistencial","📓  Diário de Bordo"]),
        ("FERRAMENTAS", ["📚  Biblioteca","🧬  Importar Dados","🤖  Assistente IA","⚙️  Configurações"]),
    ]
    opcoes_nav = ["🏠  Home","🩺  Cockpit CEO","📊  Painel DNA","💰  DRE Gerencial","📐  OKRs","📈  Comercial Hub","💡  Estratégia de Preços","🎓  Programa Integra","🩻  Segurança Assistencial","📓  Diário de Bordo","📚  Biblioteca","🧬  Importar Dados","🤖  Assistente IA","⚙️  Configurações"]
    for grupo, abas_g in NAV_GRUPOS:
        st.markdown(f'<div style="font-size:8px;color:{GRAY2};text-transform:uppercase;letter-spacing:0.12em;font-weight:700;padding:10px 12px 4px">{grupo}</div>',unsafe_allow_html=True)
        for ab in abas_g:
            ativa = st.session_state.aba == ab
            if st.button(ab, key=f"nav_{ab}", use_container_width=True):
                st.session_state.aba = ab; st.rerun()

    st.markdown(f'<div style="height:1px;background:{BORDER};margin:8px 0"></div>',unsafe_allow_html=True)
    if st.button("↩ Sair", use_container_width=True, key="btn_sair"):
        for k in ["logado","user_nome","user_nivel","user_cargo","user_id","aba"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

aba = st.session_state.aba

# ══════════════════════════════════════════════════════════════
# ROTEAMENTO
# ══════════════════════════════════════════════════════════════
if aba == "🏠  Home":
    tela_home()


elif aba == "🩺  Cockpit CEO":
    st.markdown(titulo_secao("Cockpit de Decisão Executiva","Visão integrada de performance, custos e oportunidades — atualizada em tempo real","🩺"), unsafe_allow_html=True)
    _sel_ceo = st.selectbox("", ["🩺 Visão Geral","💸 Análise de Custos","📊 DRE Rápido","🎯 OKRs"],
        label_visibility="collapsed", key="sel_ceo")
    st.markdown("---")

    conn = get_conn()
    dre_r = conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone()
    salas_r = read_df("SELECT * FROM salas WHERE mes=? AND ano=?",conn,params=(mes_sel,ano_sel))
    leads_r = conn.execute("SELECT COUNT(*),SUM(convertido),SUM(ticket) FROM leads WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone()
    clin_r  = conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    custo_f = read_df("SELECT * FROM custo_funcionario WHERE ativo=1",conn)
    taxa_s  = read_df("SELECT * FROM taxa_sala WHERE ativo=1",conn)
    okdf    = read_df("SELECT * FROM okrs WHERE ativo=1",conn)
    conn.close()

    rb = sum([(dre_r[i] or 0) for i in [3,4,5,6]]) if dre_r else 0
    imp=dre_r[7] if dre_r else 8.5; tc=dre_r[8] if dre_r else 3.0
    ins=dre_r[9] if dre_r else 0; pes=dre_r[10] if dre_r else 0
    oc=dre_r[11] if dre_r else 0; mk=dre_r[12] if dre_r else 0; ou=dre_r[13] if dre_r else 0
    ded=rb*(imp+tc)/100; rl=rb-ded; mc=rl-ins; cf=pes+oc+mk+ou; ebitda=mc-cf
    mg_ebitda=pct_safe(ebitda,rb)
    meta=clin_r[2] if clin_r else 280000; pct_m=pct_safe(rb,meta)
    perda_ns=float(salas_r['perda'].sum()) if not salas_r.empty else 0
    l_tot=leads_r[0] or 0; l_conv=leads_r[1] or 0; pipeline=leads_r[2] or 0
    tx_conv=pct_safe(int(l_conv or 0),int(l_tot or 1))
    total_custo_func = float(custo_f['custo_total'].sum()) if not custo_f.empty else 0
    total_taxa_sala  = float(taxa_s['custo_mes'].sum()) if not taxa_s.empty else 0

    if _sel_ceo == "🩺 Visão Geral":
        st.markdown(kpi_grid([
            ("Receita Realizada",fmt(rb),f"{pct_m:.0f}% da meta de {fmt(meta)}",GREEN if pct_m>=80 else AMBER if pct_m>=50 else RED,None,"💰"),
            ("EBITDA Operacional",fmt(ebitda),f"{mg_ebitda:.1f}% de margem",GREEN if ebitda>0 else RED,None,"📊"),
            ("Prejuízo No-Show",fmt(perda_ns),"Receita irrecuperável",RED if perda_ns>0 else GREEN,None,"⚠️"),
            ("Conversão Leads",f"{tx_conv:.1f}%",f"{int(l_conv or 0)} de {l_tot}",GREEN if tx_conv>=30 else RED,None,"📈"),
        ]), unsafe_allow_html=True)
        col1,col2=st.columns([3,2])
        with col1:
            st.markdown(f"<div style='font-size:12px;font-weight:600;color:{WHITE};margin-bottom:10px'>Faturamento por Prescritor — {mes_sel}/{ano_sel}</div>",unsafe_allow_html=True)
            conn2=get_conn(); ld2=read_df("SELECT * FROM leads WHERE mes=? AND ano=? AND convertido=1",conn2,params=(mes_sel,ano_sel)); conn2.close()
            if not ld2.empty:
                fs=ld2.groupby('sdr')['ticket'].sum().sort_values(ascending=False)
                if not fs.empty: st.bar_chart(fs)
            else: st.info("Lance leads convertidos com ticket para ver o gráfico.")
        with col2:
            st.markdown(f"<div style='font-size:12px;font-weight:600;color:{WHITE};margin-bottom:10px'>Pipeline Comercial</div>",unsafe_allow_html=True)
            for lbl,val,cor in [("Leads totais",l_tot,GRAY),("Convertidos",int(l_conv or 0),GREEN),("Pipeline aberto",fmt(pipeline),AMBER)]:
                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid {BORDER}"><span style="color:{GRAY};font-size:12px">{lbl}</span><span style="color:{cor};font-weight:600">{val}</span></div>',unsafe_allow_html=True)
            pe = cf/(1-(imp+tc)/100) if (1-(imp+tc)/100)>0 else 0
            st.markdown(f'<div style="display:flex;justify-content:space-between;padding:10px 0"><span style="color:{GRAY};font-size:12px">Ponto de Equilíbrio</span><span style="color:{AMBER};font-weight:600">{fmt(pe)}</span></div>',unsafe_allow_html=True)
            prg_be=pct_safe(rb,pe); _,cor_be=semaforo(prg_be,100)
            st.progress(min(prg_be/100,1.0),text=f"Break-even: {prg_be:.1f}%")

    elif _sel_ceo == "💸 Análise de Custos":
        st.markdown(titulo_secao("Análise de Custos Fixos e Variáveis","Mapeamento completo da estrutura de custo — identificação de oportunidades de redução","💸"),unsafe_allow_html=True)
        col1,col2=st.columns(2)
        with col1:
            st.markdown(f"<div style='font-size:12px;font-weight:600;color:{WHITE};margin-bottom:12px'>Custo por Funcionário</div>",unsafe_allow_html=True)
            if not custo_f.empty:
                for _,row in custo_f.iterrows():
                    pct_sal=pct_safe(row['salario_bruto'],row['custo_total'])
                    pct_enc=100-pct_sal
                    oport=""
                    if pct_enc>45: oport=f'<span style="color:{RED};font-size:10px"> ⚠️ Encargos acima de 45%</span>'
                    st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-radius:10px;
                        padding:14px;margin-bottom:8px">
                        <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                            <div>
                                <div style="font-size:13px;font-weight:600;color:{WHITE}">{row['nome']}</div>
                                <div style="font-size:11px;color:{GRAY}">{row['cargo']} · Custo/hora: {fmt(row['custo_hora'])}</div>
                            </div>
                            <div style="text-align:right">
                                <div style="font-size:16px;font-weight:700;color:{AMBER}">{fmt(row['custo_total'])}/mês</div>
                                <div style="font-size:10px;color:{GRAY}">Salário: {fmt(row['salario_bruto'])}</div>
                            </div>
                        </div>
                        {oport}
                        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:6px;margin-top:8px">
                            {''.join([f'<div style="text-align:center;background:{BG2};border-radius:6px;padding:6px"><div style="font-size:9px;color:{GRAY2}">{lb}</div><div style="font-size:11px;font-weight:600;color:{GRAY}">{fmt(vl)}</div></div>' for lb,vl in [("FGTS",row['fgts']),("INSS",row['inss']),("Férias",row['ferias']),("13º",row['decimo_terceiro'])]])}
                        </div>
                    </div>""",unsafe_allow_html=True)
            # Totais e sinalização
            if not custo_f.empty:
                pct_pessoal = pct_safe(total_custo_func, rb)
                cor_p = GREEN if pct_pessoal<35 else AMBER if pct_pessoal<50 else RED
                st.markdown(f"""<div style="background:{cor_p}11;border:1px solid {cor_p}33;border-radius:10px;padding:14px;margin-top:8px">
                    <div style="font-size:13px;font-weight:700;color:{WHITE}">Total Pessoal: {fmt(total_custo_func)}/mês</div>
                    <div style="font-size:12px;color:{cor_p};margin-top:4px">{pct_pessoal:.1f}% do faturamento — {"✅ Saudável (<35%)" if pct_pessoal<35 else "⚠️ Atenção (35-50%)" if pct_pessoal<50 else "🚨 Crítico (>50%)"}</div>
                    {"<div style='font-size:11px;color:"+GRAY+";margin-top:6px'>Recomendação: aumentar faturamento antes de contratar. Cada R$ 1.000 em pessoal exige R$ 1.340 de receita bruta adicional para ser neutro.</div>" if pct_pessoal>=40 else ""}
                </div>""",unsafe_allow_html=True)
        with col2:
            st.markdown(f"<div style='font-size:12px;font-weight:600;color:{WHITE};margin-bottom:12px'>Taxa de Sala</div>",unsafe_allow_html=True)
            if not taxa_s.empty:
                for _,row in taxa_s.iterrows():
                    tx_h=row['taxa_hora']
                    st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-radius:10px;padding:14px;margin-bottom:8px">
                        <div style="font-size:13px;font-weight:600;color:{WHITE}">{row['nome']}</div>
                        <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:8px;margin-top:10px">
                            {''.join([f'<div style="text-align:center;background:{BG2};border-radius:6px;padding:8px"><div style="font-size:9px;color:{GRAY2};margin-bottom:2px">{lb}</div><div style="font-size:12px;font-weight:600;color:{AMBER}">{vl}</div></div>' for lb,vl in [("Custo/mês",fmt(row['custo_mes'])),("Taxa/hora",fmt(tx_h)),("Salas",str(int(row['qtd'])))]])}
                        </div>
                    </div>""",unsafe_allow_html=True)
            # Custos variáveis do DRE
            st.markdown(f"<div style='font-size:12px;font-weight:600;color:{WHITE};margin:16px 0 10px'>Custos Variáveis (DRE)</div>",unsafe_allow_html=True)
            cv_items = [("Insumos Médicos",ins),("Marketing",mk),("Outros Variáveis",ou)]
            for lb,vl in cv_items:
                pct=pct_safe(vl,rb)
                st.markdown(f'<div style="display:flex;justify-content:space-between;padding:8px 0;border-bottom:1px solid {BORDER}"><span style="color:{GRAY};font-size:12px">{lb}</span><span style="color:{WHITE};font-weight:500;font-size:12px">{fmt(vl)} <span style="color:{GRAY2};font-weight:400">({pct:.1f}%)</span></span></div>',unsafe_allow_html=True)
            # Oportunidades de redução
            st.markdown(f"""<div style="background:{BLUE}11;border:1px solid {BLUE}33;border-radius:10px;padding:14px;margin-top:12px">
                <div style="font-size:12px;font-weight:700;color:{BLUE};margin-bottom:8px">💡 Oportunidades Identificadas</div>
                <div style="font-size:11px;color:{GRAY};line-height:1.8">
                → Renegociar insumos com fornecedor único pode reduzir 8-12% no custo<br>
                → Taxa de sala pode ser cobrada nos procedimentos de baixa margem<br>
                → Marketing digital com custo por lead acima de R$ 80 merece revisão
                </div>
            </div>""",unsafe_allow_html=True)
        with st.expander("✏️ Editar Custo de Funcionário"):
            with st.form("form_custo_func"):
                c1,c2,c3=st.columns(3)
                with c1: nome_cf=st.text_input("Nome"); cargo_cf=st.text_input("Cargo")
                with c2: sal_cf=st.number_input("Salário bruto R$",min_value=0.0,step=100.0)
                with c3: outros_cf=st.number_input("Outros (benefícios) R$",min_value=0.0,step=50.0,value=50.0)
                if st.form_submit_button("Salvar",use_container_width=True):
                    if nome_cf:
                        fgts=sal_cf*0.08; inss=sal_cf*0.20; fer=sal_cf*0.133; dec=sal_cf*0.083
                        total_cf=sal_cf+fgts+inss+fer+dec+outros_cf; ch=round(total_cf/176,2)
                        conn=get_conn(); conn.execute("INSERT OR REPLACE INTO custo_funcionario(nome,cargo,salario_bruto,fgts,inss,ferias,decimo_terceiro,outros,custo_total,custo_hora) VALUES(?,?,?,?,?,?,?,?,?,?)",(nome_cf,cargo_cf,sal_cf,fgts,inss,fer,dec,outros_cf,total_cf,ch)); conn.commit();conn.close();st.rerun()
        with st.expander("✏️ Editar Taxa de Sala"):
            with st.form("form_taxa_sala"):
                c1,c2,c3,c4=st.columns(4)
                with c1: nome_ts=st.text_input("Nome da sala")
                with c2: qtd_ts=st.number_input("Qtd salas",min_value=1,value=1)
                with c3: custo_ts=st.number_input("Custo mensal R$",min_value=0.0,step=50.0)
                with c4: horas_ts=st.number_input("Horas/dia",min_value=1.0,value=10.0,step=0.5)
                if st.form_submit_button("Salvar",use_container_width=True):
                    if nome_ts:
                        th=round(custo_ts/(22*horas_ts),2) if horas_ts else 0
                        conn=get_conn(); conn.execute("INSERT OR REPLACE INTO taxa_sala(nome,qtd,custo_mes,dias_mes,horas_dia,taxa_hora) VALUES(?,?,?,22,?,?)",(nome_ts,qtd_ts,custo_ts,horas_ts,th)); conn.commit();conn.close();st.rerun()

    elif _sel_ceo == "📊 DRE Rápido":
        if dre_r:
            for lbl_d,val_d,pct_d,cor_d,dest_d in [
                ("(+) Faturamento Bruto",rb,100.0,WHITE,False),
                (f"(-) Impostos + Taxas Cartão ({imp+tc:.1f}%)",ded,pct_safe(ded,rb),RED,False),
                ("(=) Receita Líquida Operacional",rl,pct_safe(rl,rb),WHITE,True),
                ("(-) Custos Variáveis (Insumos)",ins,pct_safe(ins,rb),RED,False),
                ("(=) Margem de Contribuição",mc,pct_safe(mc,rb),AMBER,True),
                ("(-) Custos Fixos Totais",cf,pct_safe(cf,rb),RED,False),
                ("   Folha de Pessoal",pes,pct_safe(pes,rb),GRAY,False),
                ("   Ocupação / Aluguel",oc,pct_safe(oc,rb),GRAY,False),
                ("   Marketing / Leads",mk,pct_safe(mk,rb),GRAY,False),
                ("(=) EBITDA Operacional",ebitda,mg_ebitda,GREEN if ebitda>0 else RED,True),
            ]: st.markdown(dre_linha(lbl_d,val_d,pct_d,cor_d,dest_d),unsafe_allow_html=True)
            c1,c2,c3=st.columns(3)
            pe2=cf/(1-(imp+tc)/100) if (1-(imp+tc)/100)>0 else 0
            with c1: st.metric("Ponto de Equilíbrio",fmt(pe2))
            with c2: st.metric("Margem EBITDA",f"{mg_ebitda:.1f}%")
            with c3: st.metric("Margem Contribuição",f"{pct_safe(mc,rb):.1f}%")
        else:
            st.info("Lance os dados do DRE no módulo DRE Gerencial para ver o resultado aqui.")

    elif _sel_ceo == "🎯 OKRs":
        if okdf.empty: st.info("Sem OKRs cadastrados. Acesse o módulo OKRs para adicionar.")
        else:
            for tri in ["Q1","Q2","Q3","Q4"]:
                grupo=okdf[okdf["trimestre"]==tri]
                if grupo.empty: continue
                for obj in grupo["objetivo"].unique():
                    krs=grupo[grupo["objetivo"]==obj]
                    st.markdown(f'<div style="background:{BG3};border:1px solid {BORDER};border-radius:12px;padding:16px 20px;margin-bottom:14px"><div style="color:{AMBER};font-size:13px;font-weight:700;margin-bottom:12px">🎯 {obj} · {tri}</div>',unsafe_allow_html=True)
                    for _,kr in krs.iterrows():
                        p_kr=pct_safe(kr['atual_val'],kr['meta_val']); _,cor_kr=semaforo(p_kr)
                        st.markdown(barra(p_kr,f"{kr['key_result']} — {fmt(kr['atual_val'])} / {fmt(kr['meta_val'])} (DRI: {kr['responsavel']})",cor_kr),unsafe_allow_html=True)
                    st.markdown("</div>",unsafe_allow_html=True)


elif aba == "📊  Painel DNA":
    st.markdown(titulo_secao("Painel DNA de Metas","O painel que transforma metas em execução — briefing, debriefing, salas e réguas em uma visão única","📊"),unsafe_allow_html=True)
    tab_dna,tab_brf,tab_dbf,tab_sal,tab_reg = st.tabs(["📊 METAS SEMANAIS","☀️ BRIEFING","🌙 DEBRIEFING","🏥 SALAS","📋 RÉGUAS"])

    with tab_dna:
        sw=f"S{date.today().isocalendar()[1]}"
        conn=get_conn(); dna=conn.execute("SELECT * FROM painel_dna WHERE semana=? AND ano=?",(sw,ano_sel)).fetchone(); clin_r=conn.execute("SELECT * FROM clinica WHERE id=1").fetchone(); conn.close()
        meta_m=clin_r[2] if clin_r else 280000
        with st.expander("✏️ Preencher Painel da Semana",expanded=not bool(dna)):
            with st.form("form_dna"):
                c1,c2,c3=st.columns(3)
                with c1: meta_d=st.number_input("Meta Mensal R$",value=float(dna[3] if dna else meta_m),step=1000.0); realiz=st.number_input("Já realizado R$",value=float(dna[4] if dna else 0),step=100.0); dias_r=st.number_input("Dias úteis restantes",value=int(dna[5] if dna else 5),min_value=1,max_value=25)
                with c2: cv=st.number_input("01 Consultas ag. R$",value=float(dna[6] if dna else 0),step=100.0); pv=st.number_input("02 Procedimentos ag. R$",value=float(dna[7] if dna else 0),step=100.0)
                with c3: nv=st.number_input("03 Negociações R$",value=float(dna[8] if dna else 0),step=100.0); ov=st.number_input("04 Orçamentos R$",value=float(dna[9] if dna else 0),step=100.0)
                dcols=st.columns(5); vd=[]
                for i,(dc,dn) in enumerate(zip(dcols,["SEG","TER","QUA","QUI","SEX"])):
                    with dc:
                        st.markdown(f"<div style='color:{WHITE};font-weight:600;text-align:center;font-size:11px;margin-bottom:4px'>{dn}</div>",unsafe_allow_html=True)
                        b=10+(i*3)
                        c_=st.number_input(f"C{dn}",value=float(dna[b] if dna else 0),step=100.0,key=f"dc{i}",label_visibility="collapsed")
                        p_=st.number_input(f"P{dn}",value=float(dna[b+1] if dna else 0),step=100.0,key=f"dp{i}",label_visibility="collapsed")
                        n_=st.number_input(f"N{dn}",value=float(dna[b+2] if dna else 0),step=100.0,key=f"dn{i}",label_visibility="collapsed")
                        vd.extend([c_,p_,n_])
                if st.form_submit_button("💾 Salvar Painel",use_container_width=True):
                    conn=get_conn(); conn.execute("""INSERT INTO painel_dna(semana,ano,meta_mensal,realizado_mes,dias_uteis_restantes,consultas_v,procedimentos_v,negociacoes_v,orcamentos_v,seg_c,seg_p,seg_n,ter_c,ter_p,ter_n,qua_c,qua_p,qua_n,qui_c,qui_p,qui_n,sex_c,sex_p,sex_n) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(semana,ano) DO UPDATE SET meta_mensal=excluded.meta_mensal,realizado_mes=excluded.realizado_mes,dias_uteis_restantes=excluded.dias_uteis_restantes,consultas_v=excluded.consultas_v,procedimentos_v=excluded.procedimentos_v,negociacoes_v=excluded.negociacoes_v,orcamentos_v=excluded.orcamentos_v,seg_c=excluded.seg_c,seg_p=excluded.seg_p,seg_n=excluded.seg_n,ter_c=excluded.ter_c,ter_p=excluded.ter_p,ter_n=excluded.ter_n,qua_c=excluded.qua_c,qua_p=excluded.qua_p,qua_n=excluded.qua_n,qui_c=excluded.qui_c,qui_p=excluded.qui_p,qui_n=excluded.qui_n,sex_c=excluded.sex_c,sex_p=excluded.sex_p,sex_n=excluded.sex_n""",(sw,ano_sel,meta_d,realiz,dias_r,cv,pv,nv,ov,*vd)); conn.commit();conn.close();st.rerun()
        if dna:
            meta_d=dna[3] or 0; realiz=dna[4] or 0; dias_r=dna[5] or 5
            cv=dna[6] or 0; pv=dna[7] or 0; nv=dna[8] or 0; ov=dna[9] or 0
            total_prev=cv+pv+nv+ov; meta_sem=meta_d/4; falta=meta_sem-total_prev
            meta_dia=max((meta_d-realiz)/max(dias_r,1),0)
            st.markdown("---")
            st.markdown(kpi_grid([("Receita travada esta semana",fmt(total_prev),"Consultas+Proced.+Neg.+Orç.",GREEN),("Follow-up disponível hoje",fmt(nv+ov),"Negociações + Orçamentos abertos",AMBER),("Ainda precisa gerar",fmt(max(falta,0)),f"Meta semanal ({fmt(meta_sem)}) menos previsto",RED if falta>0 else GREEN)],cols=3),unsafe_allow_html=True)
            st.markdown(f"""<div style="background:{AMBER}11;border:1px solid {AMBER}33;border-radius:16px;padding:24px;text-align:center;margin:16px 0">
                <div style="font-size:10px;color:{GRAY};text-transform:uppercase;letter-spacing:0.15em;margin-bottom:8px">META DIÁRIA DE RITMO</div>
                <div style="font-size:3rem;font-weight:800;color:{AMBER};letter-spacing:-0.03em">{fmt(meta_dia)}</div>
                <div style="font-size:12px;color:{GRAY};margin-top:6px">{dias_r} dias úteis restantes · {sw}/{ano_sel}</div>
            </div>""",unsafe_allow_html=True)

    with tab_brf:
        hj=date.today().isoformat(); hj_fmt=date.today().strftime("%d/%m/%Y")
        conn=get_conn(); bf=conn.execute("SELECT * FROM briefing WHERE data=?",(hj,)).fetchone(); dre_bf=conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone(); clin_bf=conn.execute("SELECT * FROM clinica WHERE id=1").fetchone(); conn.close()
        meta_m=clin_bf[2] if clin_bf else 0; rb_mes=sum([(dre_bf[i] or 0) for i in [3,4,5,6]]) if dre_bf else 0
        p_meta=pct_safe(rb_mes,meta_m); _,cor_meta=semaforo(p_meta,80)
        st.markdown(barra(p_meta,f"Meta mensal: {fmt(rb_mes)} de {fmt(meta_m)}",cor_meta),unsafe_allow_html=True)
        with st.form("form_briefing"):
            st.markdown(f"<div style='color:{AMBER};font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:14px'>☀️ BRIEFING — {hj_fmt}</div>",unsafe_allow_html=True)
            resp_bf=st.text_input("Responsável (DRI)",value=bf[2] if bf else "")
            c1,c2,c3,c4,c5=st.columns(5)
            with c1: ca=st.number_input("Consultas ag.",value=int(bf[3] if bf else 0),min_value=0)
            with c2: pa=st.number_input("Procedimentos ag.",value=int(bf[4] if bf else 0),min_value=0)
            with c3: conf=st.number_input("Confirmações",value=int(bf[5] if bf else 0),min_value=0)
            with c4: gaps=st.number_input("Gaps na agenda",value=int(bf[6] if bf else 0),min_value=0)
            with c5: val_ag=st.number_input("Valor projetado R$",value=float(bf[7] if bf else 0),step=100.0)
            c1,c2,c3,c4=st.columns(4)
            with c1: lp=st.number_input("Leads pendentes",value=int(bf[8] if bf else 0),min_value=0)
            with c2: oa=st.number_input("Orç. abertos",value=int(bf[9] if bf else 0),min_value=0)
            with c3: vo=st.number_input("Pipeline R$",value=float(bf[10] if bf else 0),step=100.0)
            with c4: rm=st.number_input("Meta RFM",value=int(bf[11] if bf else 30),min_value=0)
            c1,c2=st.columns([3,1]); 
            with c1: pr1=st.text_input("Prioridade 1",value=bf[23] if bf else "")
            with c2: dr1=st.text_input("DRI 1",value=bf[26] if bf else "")
            c1,c2=st.columns([3,1])
            with c1: pr2=st.text_input("Prioridade 2",value=bf[24] if bf else "")
            with c2: dr2=st.text_input("DRI 2",value=bf[27] if bf else "")
            c1,c2=st.columns([3,1])
            with c1: pr3=st.text_input("Prioridade 3",value=bf[25] if bf else "")
            with c2: dr3=st.text_input("DRI 3",value=bf[28] if bf else "")
            if st.form_submit_button("✅ Registrar Briefing",use_container_width=True):
                conn=get_conn(); conn.execute("""INSERT INTO briefing(data,responsavel,cons_ag,proc_ag,conf,gaps,val_ag,leads_pend,orc_ab,val_orc,rfm_meta,pr1,pr2,pr3,dr1,dr2,dr3) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(data) DO UPDATE SET responsavel=excluded.responsavel,cons_ag=excluded.cons_ag,proc_ag=excluded.proc_ag,conf=excluded.conf,gaps=excluded.gaps,val_ag=excluded.val_ag,leads_pend=excluded.leads_pend,orc_ab=excluded.orc_ab,val_orc=excluded.val_orc,rfm_meta=excluded.rfm_meta,pr1=excluded.pr1,pr2=excluded.pr2,pr3=excluded.pr3,dr1=excluded.dr1,dr2=excluded.dr2,dr3=excluded.dr3""",(hj,resp_bf,ca,pa,conf,gaps,val_ag,lp,oa,vo,rm,pr1,pr2,pr3,dr1,dr2,dr3)); conn.commit();conn.close();st.success("Briefing registrado!");st.rerun()

    with tab_dbf:
        hj=date.today().isoformat(); hj_fmt=date.today().strftime("%d/%m/%Y")
        conn=get_conn(); db_d=conn.execute("SELECT * FROM debriefing WHERE data=?",(hj,)).fetchone(); bf_h=conn.execute("SELECT * FROM briefing WHERE data=?",(hj,)).fetchone(); clin_db=conn.execute("SELECT * FROM clinica WHERE id=1").fetchone(); conn.close()
        meta_dia_v=(clin_db[2] if clin_db else 0)/22
        with st.form("form_debriefing"):
            st.markdown(f"<div style='color:{AMBER};font-weight:700;font-size:12px;text-transform:uppercase;margin-bottom:14px'>🌙 DEBRIEFING — {hj_fmt}</div>",unsafe_allow_html=True)
            resp_db=st.text_input("Responsável",value=db_d[2] if db_d else "")
            c1,c2,c3,c4=st.columns(4)
            with c1: rc_db=st.number_input("Receita Consultas",value=float(db_d[3] if db_d else 0),step=100.0)
            with c2: rp_db=st.number_input("Receita Proced.",value=float(db_d[4] if db_d else 0),step=100.0)
            with c3: rr_db=st.number_input("Recorrência",value=float(db_d[5] if db_d else 0),step=100.0)
            with c4: ro_db=st.number_input("Outros",value=float(db_d[6] if db_d else 0),step=100.0)
            receita_d=rc_db+rp_db+rr_db+ro_db
            cor_rec=GREEN if receita_d>=meta_dia_v else RED
            st.markdown(f'<div style="background:{cor_rec}11;border:1px solid {cor_rec}33;border-radius:8px;padding:10px 16px;display:flex;justify-content:space-between;margin:4px 0 12px"><span style="color:{GRAY};font-size:12px">Receita total do dia</span><span style="color:{cor_rec};font-size:20px;font-weight:700">{fmt(receita_d)}</span></div>',unsafe_allow_html=True)
            c1,c2,c3,c4=st.columns(4)
            with c1: cons_r=st.number_input("Consultas realizadas",value=int(db_d[10] if db_d else 0),min_value=0)
            with c2: ns_db=st.number_input("No-shows",value=int(db_d[12] if db_d else 0),min_value=0)
            with c3: rfm_db=st.number_input("Contatos RFM",value=int(db_d[20] if db_d else 0),min_value=0)
            with c4: av_db=st.number_input("Avaliações Google",value=int(db_d[23] if db_d else 0),min_value=0)
            conquista=st.text_input("Principal conquista",value=db_d[28] if db_d else "")
            gargalo=st.text_input("Principal gargalo",value=db_d[29] if db_d else "")
            c1,c2=st.columns([3,1])
            with c1: acao_am=st.text_input("Ação de amanhã",value=db_d[30] if db_d else "")
            with c2: dri_am=st.text_input("DRI",value=db_d[31] if db_d else "")
            if st.form_submit_button("🌙 Registrar Fechamento",use_container_width=True):
                conn=get_conn(); conn.execute("""INSERT INTO debriefing(data,responsavel,rc,rp,rr,ro,cons_r,ns,rfm_r,av_g,conquista,gargalo,acao_am,dri_am) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(data) DO UPDATE SET responsavel=excluded.responsavel,rc=excluded.rc,rp=excluded.rp,rr=excluded.rr,ro=excluded.ro,cons_r=excluded.cons_r,ns=excluded.ns,rfm_r=excluded.rfm_r,av_g=excluded.av_g,conquista=excluded.conquista,gargalo=excluded.gargalo,acao_am=excluded.acao_am,dri_am=excluded.dri_am""",(hj,resp_db,rc_db,rp_db,rr_db,ro_db,cons_r,ns_db,rfm_db,av_db,conquista,gargalo,acao_am,dri_am))
                conn.execute("""INSERT INTO dre(mes,ano,receita_consultas,receita_procedimentos,receita_recorrencia,receita_outros) VALUES(?,?,?,?,?,?) ON CONFLICT(mes,ano) DO UPDATE SET receita_consultas=receita_consultas+?,receita_procedimentos=receita_procedimentos+?,receita_recorrencia=receita_recorrencia+?,receita_outros=receita_outros+?""",(mes_sel,ano_sel,rc_db,rp_db,rr_db,ro_db,rc_db,rp_db,rr_db,ro_db))
                conn.commit();conn.close();st.success("Fechamento registrado! DRE atualizado.");st.rerun()

    with tab_sal:
        conn=get_conn(); salas_df=read_df("SELECT * FROM salas WHERE mes=? AND ano=?",conn,params=(mes_sel,ano_sel)); conn.close()
        with st.expander("➕ Registrar Ocupação de Sala"):
            with st.form("form_sala"):
                c1,c2,c3=st.columns(3)
                with c1: nome_s=st.text_input("Sala"); medico_s=st.text_input("Médico")
                with c2: hd_s=st.number_input("Horas disponíveis",value=8.0,step=0.5); ho_s=st.number_input("Horas ocupadas",value=0.0,step=0.5)
                with c3: ns_s=st.number_input("No-shows",value=0,min_value=0); tk_s=st.number_input("Ticket/hora R$",value=0.0,step=10.0)
                if st.form_submit_button("Salvar",use_container_width=True):
                    if nome_s:
                        conn=get_conn(); conn.execute("INSERT INTO salas(nome,medico,horas_disp,horas_ocup,no_show,perda,ticket_hora,mes,ano) VALUES(?,?,?,?,?,?,?,?,?)",(nome_s,medico_s,hd_s,ho_s,ns_s,ns_s*tk_s,tk_s,mes_sel,ano_sel)); conn.commit();conn.close();st.rerun()
        if not salas_df.empty:
            salas_df['tx_ocup']=(salas_df['horas_ocup']/salas_df['horas_disp']*100).round(1).fillna(0)
            for _,s in salas_df.iterrows():
                tx=s['tx_ocup']; cor_s=GREEN if tx>=85 else AMBER if tx>=50 else RED
                st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-radius:12px;padding:16px 20px;margin-bottom:12px">
                    <div style="display:flex;justify-content:space-between;margin-bottom:10px">
                        <div><div style="font-size:14px;font-weight:600;color:{WHITE}">{s['nome']}</div>
                            <div style="font-size:11px;color:{GRAY}">{s['medico']} · {fmt(s['ticket_hora'])}/h</div></div>
                        <div style="text-align:right"><div style="font-size:2rem;font-weight:700;color:{cor_s}">{tx:.1f}%</div></div>
                    </div>
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:8px">
                        {''.join([f'<div style="background:{BG2};border-radius:8px;padding:8px;text-align:center"><div style="font-size:9px;color:{GRAY2};margin-bottom:2px">{lb}</div><div style="font-size:13px;font-weight:600;color:{cr}">{vl}</div></div>' for lb,vl,cr in [("Disponíveis",f"{s['horas_disp']}h",WHITE),("Ocupadas",f"{s['horas_ocup']}h",GREEN),("No-Shows",str(int(s['no_show'])),RED),("Perda",fmt(s['perda']),RED)]])}
                    </div>
                    {barra(tx,"Ocupação",cor_s)}
                </div>""",unsafe_allow_html=True)

    with tab_reg:
        conn=get_conn(); rg_df=read_df("SELECT * FROM regua ORDER BY data_cons DESC",conn); conn.close()
        st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-radius:12px;padding:16px 20px;margin-bottom:16px">
            <div style="font-size:11px;color:{AMBER};font-weight:700;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:12px">RÉGUA D-1 / D+1 · FOLLOW-UP · D+30 · PÓS-RECUSA</div>
            <div style="display:grid;grid-template-columns:repeat(6,1fr);gap:8px">
                {''.join([f'<div style="background:{BG2};border-radius:8px;padding:10px;text-align:center"><div style="font-size:13px;font-weight:700;color:{AMBER}">{d}</div><div style="font-size:10px;color:{GRAY};margin-top:2px">{ds}</div></div>' for d,ds in [("D-1","Véspera"),("D+1","Pós consulta"),("D+3","Esclarecer"),("D+7","Reforço"),("D+14","Reativação"),("D+30","Avaliação final"),]])}
            </div>
            <div style="margin-top:10px;background:{PURPLE}11;border-radius:8px;padding:10px 14px;font-size:11px;color:{PURPLE}">
                <strong>D+1 pós-recusa:</strong> Para pacientes que recusaram o orçamento — contato de acolhimento, sem pressão, oferecendo alternativas de acesso. Conversão histórica de 18%.
            </div>
        </div>""",unsafe_allow_html=True)
        with st.expander("➕ Adicionar Paciente na Régua"):
            with st.form("form_regua"):
                c1,c2,c3,c4=st.columns(4)
                with c1: nm_rg=st.text_input("Paciente")
                with c2: tp_rg=st.selectbox("Tipo",["Primeira Consulta","Retorno","Pós-recusa"])
                with c3: dt_rg=st.date_input("Data",value=date.today())
                with c4: tk_rg=st.number_input("Ticket R$",min_value=0.0,step=50.0)
                if st.form_submit_button("Adicionar",use_container_width=True):
                    if nm_rg:
                        conn=get_conn(); conn.execute("INSERT INTO regua(paciente,tipo,data_cons,ticket) VALUES(?,?,?,?)",(nm_rg,tp_rg,dt_rg.isoformat(),tk_rg)); conn.commit();conn.close();st.rerun()
        if not rg_df.empty:
            st.dataframe(rg_df[['paciente','tipo','data_cons','st_dm1','st_dp1','st_dp3','st_dp7','st_dp14','st_dp30','st_recusa','ticket','fechou']],hide_index=True,use_container_width=True)


elif aba == "📈  Comercial Hub":
    st.markdown(titulo_secao("Comercial Hub","Pipeline integrado: leads, orçamentos, RFM e indicações — operado como um funil de alta performance","📈"),unsafe_allow_html=True)
    tab_leads,tab_orc,tab_rfm,tab_ind = st.tabs(["📈 LEADS & FUNIL SPIN","💰 ORÇAMENTOS","🔄 RFM","🤝 INDICAÇÕES"])

    with tab_leads:
        conn=get_conn(); leads_df=read_df("SELECT * FROM leads WHERE mes=? AND ano=? ORDER BY id DESC",conn,params=(mes_sel,ano_sel)); conn.close()
        tot=len(leads_df); ag=int(leads_df[leads_df['status'].isin(['Agendado','Compareceu','Convertido'])].shape[0]) if not leads_df.empty else 0
        comp=int(leads_df['compareceu'].sum()) if not leads_df.empty else 0; conv=int(leads_df['convertido'].sum()) if not leads_df.empty else 0
        resp5=int((leads_df['tempo_resp']<=5).sum()) if not leads_df.empty else 0; tx_vel=pct_safe(resp5,tot)
        # Funil SPIN
        st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-radius:12px;padding:20px;margin-bottom:20px">
            <div style="font-size:10px;color:{AMBER};text-transform:uppercase;letter-spacing:0.12em;font-weight:700;margin-bottom:16px">FUNIL SPIN — SITUAÇÃO · PROBLEMA · IMPLICAÇÃO · NECESSIDADE</div>
            <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:2px;background:{BORDER};border-radius:8px;overflow:hidden">
                {''.join([f'<div style="background:{BG};padding:16px;text-align:center"><div style="font-size:8px;color:{GRAY};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:6px">{lb}</div><div style="font-size:2rem;font-weight:700;color:{cr}">{vl}</div><div style="font-size:11px;color:{cr};font-weight:600">{tx}</div><div style="font-size:9px;color:{GRAY};margin-top:4px">{desc}</div></div>' for lb,vl,tx,cr,desc in [("S — Leads",tot,"100%",GRAY,"Situação mapeada"),("P — Agendados",ag,f"{pct_safe(ag,tot):.0f}%",AMBER,"Problema identificado"),("I — Compareceram",comp,f"{pct_safe(comp,ag):.0f}%",AMBER,"Implicação explorada"),("N — Convertidos",conv,f"{pct_safe(conv,tot):.0f}%",GREEN,"Necessidade resolvida"),("⚡ Resp.<5min",resp5,f"{tx_vel:.0f}%",GREEN if tx_vel>=80 else RED,"Velocidade crítica")]])}
            </div>
            <div style="margin-top:12px;background:{BLUE}11;border-radius:8px;padding:10px 14px;font-size:11px;color:{GRAY};line-height:1.7">
                <strong style="color:{BLUE}">Funil SPIN:</strong> S (Situação) = entender o contexto do lead. P (Problema) = identificar a dor principal. I (Implicação) = mostrar o custo de não resolver. N (Necessidade) = apresentar a solução como investimento, não como custo. Leads trabalhados com SPIN convertem 3,2x mais.
            </div>
        </div>""",unsafe_allow_html=True)
        col_orig,col_mot=st.columns(2)
        with col_orig:
            st.markdown(f"<div style='font-size:12px;font-weight:600;color:{WHITE};margin-bottom:10px'>Origem dos Leads</div>",unsafe_allow_html=True)
            if not leads_df.empty:
                for _,row in leads_df.groupby('canal').size().reset_index(name='n').sort_values('n',ascending=False).iterrows():
                    st.markdown(barra(pct_safe(row['n'],tot),f"{row['canal']}: {row['n']} leads",AMBER),unsafe_allow_html=True)
        with col_mot:
            st.markdown(f"<div style='font-size:12px;font-weight:600;color:{WHITE};margin-bottom:10px'>Motivos de Perda</div>",unsafe_allow_html=True)
            if not leads_df.empty and leads_df['motivo'].any():
                for _,row in leads_df[leads_df['motivo']!=''].groupby('motivo').size().reset_index(name='q').iterrows():
                    st.markdown(barra(pct_safe(row['q'],tot),f"{row['motivo']}: {row['q']}",RED),unsafe_allow_html=True)
        with st.expander("➕ Adicionar Lead"):
            with st.form("form_lead"):
                c1,c2,c3,c4=st.columns(4)
                with c1: nome_l=st.text_input("Nome"); canal_l=st.selectbox("Canal",["Instagram","Indicação","Google","WhatsApp","Tráfego Pago","Outro"])
                with c2: sdr_l=st.selectbox("SDR",["Aline","Bianca","Beatriz"]); temp_l=st.selectbox("Temperatura",["Quente","Morno","Frio"])
                with c3: tk_l=st.number_input("Ticket R$",min_value=0.0,step=50.0); resp_l=st.number_input("Tempo resp. (min)",min_value=0)
                with c4: status_l=st.selectbox("Status",["Novo","Qualificado","Agendado","Compareceu","Convertido","Descartado"]); conv_l=st.checkbox("Convertido"); comp_l=st.checkbox("Compareceu")
                motivo_l=st.text_input("Motivo de perda (se descartado)")
                if st.form_submit_button("➕ Adicionar",use_container_width=True):
                    if nome_l:
                        conn=get_conn(); conn.execute("INSERT INTO leads(nome,canal,sdr,status,temperatura,tempo_resp,compareceu,convertido,ticket,motivo,mes,ano) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(nome_l,canal_l,sdr_l,status_l,temp_l,resp_l,1 if comp_l else 0,1 if conv_l else 0,tk_l,motivo_l,mes_sel,ano_sel)); conn.commit();conn.close();st.rerun()
        if not leads_df.empty:
            st.dataframe(leads_df[['nome','canal','sdr','status','temperatura','tempo_resp','compareceu','convertido','ticket']],hide_index=True,use_container_width=True)

    with tab_orc:
        conn=get_conn(); odf=read_df("SELECT * FROM orcamentos ORDER BY criado_em DESC",conn); conn.close()
        if not odf.empty:
            val_total=odf['valor'].sum(); val_fechado=odf[odf['status']=='Fechado']['valor'].sum()
            val_recusado=odf[odf['status']=='Perdido']['valor'].sum(); val_aberto=odf[odf['status']=='Aberto']['valor'].sum()
            st.markdown(kpi_grid([("Total Orçado",fmt(val_total),"todos os status",AMBER),("Fechado",fmt(val_fechado),f"{pct_safe(val_fechado,val_total):.0f}% do total",GREEN),("Recusado",fmt(val_recusado),f"{pct_safe(val_recusado,val_total):.0f}% do total",RED),("Em Aberto",fmt(val_aberto),f"{pct_safe(val_aberto,val_total):.0f}% pendente",BLUE)]),unsafe_allow_html=True)
            qt=odf[(odf['temperatura']=='Quente')&(odf['status']=='Aberto')&(odf['proxima_acao']=='')]
            if len(qt)>0: st.error(f"🚨 {len(qt)} orçamento(s) QUENTE(S) sem próxima ação — Bianca, acionar agora!")
        with st.expander("➕ Adicionar Orçamento"):
            with st.form("form_orc"):
                c1,c2,c3,c4=st.columns(4)
                with c1: pac_o=st.text_input("Paciente"); val_o=st.number_input("Valor R$",min_value=0.0,step=100.0)
                with c2: temp_o=st.selectbox("Temperatura",["Quente","Morno","Frio","Perdido"]); status_o=st.selectbox("Status",["Aberto","Fechado","Perdido"])
                with c3: dri_o=st.selectbox("DRI",["Bianca","Vanessa"]); prox_a=st.text_input("Próxima ação")
                with c4: prazo_o=st.date_input("Prazo",value=date.today()+timedelta(days=1)); motivo_r=st.text_input("Motivo recusa (se aplicável)")
                if st.form_submit_button("Salvar",use_container_width=True):
                    if pac_o:
                        conn=get_conn(); conn.execute("INSERT INTO orcamentos(paciente,valor,data_envio,temperatura,proxima_acao,dri,prazo,status,motivo_recusa) VALUES(?,?,?,?,?,?,?,?,?)",(pac_o,val_o,date.today().isoformat(),temp_o,prox_a,dri_o,prazo_o.isoformat(),status_o,motivo_r)); conn.commit();conn.close();st.rerun()
        if not odf.empty:
            st.dataframe(odf[['paciente','valor','temperatura','status','proxima_acao','dri','prazo','motivo_recusa']],hide_index=True,use_container_width=True)

    with tab_rfm:
        conn=get_conn(); rdf=read_df("SELECT * FROM rfm ORDER BY criado_em DESC",conn); conn.close()
        st.markdown(kpi_grid([("Meta Diária RFM","30 contatos","Paciente reativado custa 5x menos",AMBER),("Meta Indicações","5 pedidos/dia","Lead de indicação converte 3x mais",GREEN)],cols=2),unsafe_allow_html=True)
        with st.expander("➕ Adicionar Paciente RFM"):
            with st.form("form_rfm"):
                c1,c2,c3,c4=st.columns(4)
                with c1: pac_r=st.text_input("Paciente")
                with c2: seg_r=st.selectbox("Segmento",["Alto valor","Médio","Inativo recente","Inativo antigo"])
                with c3: val_r=st.number_input("Total investido R$",min_value=0.0,step=100.0)
                with c4: dri_r=st.selectbox("DRI",["Beatriz","Bianca"])
                prox_r=st.text_input("Próxima ação")
                if st.form_submit_button("Salvar",use_container_width=True):
                    if pac_r:
                        conn=get_conn(); conn.execute("INSERT INTO rfm(paciente,ultima_visita,segmento,valor_total,dri,proxima_acao) VALUES(?,?,?,?,?,?)",(pac_r,date.today().isoformat(),seg_r,val_r,dri_r,prox_r)); conn.commit();conn.close();st.rerun()
        if not rdf.empty:
            for seg,cor_sg in [("Alto valor",GREEN),("Médio",AMBER),("Inativo recente",BLUE),("Inativo antigo",GRAY)]:
                g=rdf[rdf['segmento']==seg]
                if g.empty: continue
                st.markdown(f"<div style='font-size:11px;color:{cor_sg};font-weight:600;text-transform:uppercase;margin:12px 0 6px'>{seg} — {len(g)} pacientes</div>",unsafe_allow_html=True)
                for _,rw in g.iterrows():
                    st.markdown(f'<div style="background:{BG3};border:1px solid {BORDER};border-radius:8px;padding:10px 14px;margin-bottom:4px;display:flex;justify-content:space-between;align-items:center"><div><strong style="color:{WHITE}">{rw["paciente"]}</strong><span style="font-size:11px;color:{GRAY}"> · {fmt(rw["valor_total"])}</span></div><div style="text-align:right"><div style="font-size:10px;color:{GRAY}">DRI: {rw["dri"]}</div><div style="font-size:11px;color:{AMBER}">{rw["proxima_acao"] or "—"}</div></div></div>',unsafe_allow_html=True)

    with tab_ind:
        conn=get_conn(); idf=read_df("SELECT * FROM indicacoes ORDER BY criado_em DESC",conn); conn.close()
        with st.expander("➕ Registrar Indicação"):
            with st.form("form_ind"):
                c1,c2,c3,c4=st.columns(4)
                with c1: ir=st.text_input("Paciente que indicou")
                with c2: id_=st.text_input("Paciente indicado")
                with c3: ct=st.text_input("Contato")
                with c4: di=st.selectbox("DRI",["Aline","Bianca"])
                if st.form_submit_button("Registrar",use_container_width=True):
                    if ir and id_:
                        conn=get_conn(); conn.execute("INSERT INTO indicacoes(pac_indicador,pac_indicado,contato,data_ind,dri) VALUES(?,?,?,?,?)",(ir,id_,ct,date.today().isoformat(),di)); conn.commit();conn.close();st.rerun()
        if not idf.empty:
            conv_i=int(idf['convertido'].sum()); tx_i=pct_safe(conv_i,len(idf))
            st.markdown(kpi_grid([("Total Indicações",str(len(idf)),"todos os tempos",WHITE),("Convertidas",str(conv_i),f"{tx_i:.0f}% de conversão",GREEN),("Pendentes",str(len(idf)-conv_i),"aguardando contato",AMBER)],cols=3),unsafe_allow_html=True)
            st.dataframe(idf[['pac_indicador','pac_indicado','data_ind','status','dri','convertido']],hide_index=True,use_container_width=True)


elif aba == "💡  Estratégia de Preços":
    st.markdown(titulo_secao("Estratégia de Preços","Precificação baseada em custo real — taxa de sala, custo de funcionário e margem de contribuição por procedimento","💡"),unsafe_allow_html=True)
    conn=get_conn(); prec_df=read_df("SELECT * FROM precificacao WHERE ativo=1",conn); taxa_df=read_df("SELECT * FROM taxa_sala WHERE ativo=1",conn); func_df=read_df("SELECT * FROM custo_funcionario WHERE ativo=1",conn); conn.close()
    tab_prec,tab_sim,tab_peq = st.tabs(["📋 TABELA DE PREÇOS","🧮 SIMULADOR","⚖️ PONTO DE EQUILÍBRIO"])

    with tab_prec:
        if not prec_df.empty:
            for _,row in prec_df.iterrows():
                mg=(row['preco_venda']-row['custo_total'])/row['preco_venda']*100 if row['preco_venda'] else 0
                cor_mg=GREEN if mg>=40 else AMBER if mg>=20 else RED
                st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-radius:10px;padding:14px 18px;margin-bottom:8px">
                    <div style="display:flex;justify-content:space-between;align-items:flex-start;flex-wrap:wrap;gap:10px">
                        <div style="font-size:13px;font-weight:600;color:{WHITE}">{row['produto']}</div>
                        <div style="display:flex;gap:16px;align-items:center">
                            <div style="text-align:center"><div style="font-size:9px;color:{GRAY}">Custo</div><div style="font-size:13px;font-weight:600;color:{RED}">{fmt(row['custo_total'])}</div></div>
                            <div style="text-align:center"><div style="font-size:9px;color:{GRAY}">Preço</div><div style="font-size:13px;font-weight:600;color:{WHITE}">{fmt(row['preco_venda'])}</div></div>
                            <div style="text-align:center"><div style="font-size:9px;color:{GRAY}">Margem</div><div style="font-size:13px;font-weight:700;color:{cor_mg}">{mg:.1f}%</div></div>
                        </div>
                    </div>
                </div>""",unsafe_allow_html=True)
        else:
            st.info("Nenhum produto precificado ainda. Use o Simulador para calcular.")

    with tab_sim:
        st.markdown(f"<div style='font-size:12px;color:{GRAY};margin-bottom:16px'>Calcule o preço ideal de qualquer procedimento baseado no custo real da sua operação.</div>",unsafe_allow_html=True)
        taxa_hora_media = float(taxa_df['taxa_hora'].mean()) if not taxa_df.empty else 50.0
        custo_hora_func = float(func_df['custo_hora'].mean()) if not func_df.empty else 35.0
        with st.form("form_sim_preco"):
            c1,c2=st.columns(2)
            with c1:
                prod_s=st.text_input("Nome do procedimento")
                custo_ins=st.number_input("Custo de insumos/materiais R$",min_value=0.0,step=1.0)
                mins_func=st.number_input("Tempo do funcionário (minutos)",min_value=0,value=30)
            with c2:
                mins_sala=st.number_input("Tempo de sala (minutos)",min_value=0,value=30)
                imposto_sim=st.number_input("Impostos %",value=16.33,step=0.1)
                margem_desej=st.number_input("Margem desejada %",value=40.0,min_value=0.0,max_value=90.0,step=5.0)
            if st.form_submit_button("🧮 Calcular Preço Ideal",use_container_width=True):
                c_func=custo_hora_func*mins_func/60; c_sala=taxa_hora_media*mins_sala/60
                c_total=custo_ins+c_func+c_sala; c_total_c_imp=c_total/(1-imposto_sim/100-margem_desej/100) if (1-imposto_sim/100-margem_desej/100)>0 else 0
                st.markdown(f"""<div style="background:{GREEN}11;border:1px solid {GREEN}33;border-radius:12px;padding:20px;margin-top:16px">
                    <div style="font-size:14px;font-weight:700;color:{WHITE};margin-bottom:16px">{prod_s or "Procedimento"}</div>
                    <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px">
                        {''.join([f'<div style="text-align:center;background:{BG3};border-radius:8px;padding:12px"><div style="font-size:9px;color:{GRAY};margin-bottom:4px">{lb}</div><div style="font-size:1.1rem;font-weight:700;color:{cr}">{vl}</div></div>' for lb,vl,cr in [("Insumos",fmt(custo_ins),RED),("Funcionário",fmt(c_func),RED),("Sala",fmt(c_sala),RED),("PREÇO IDEAL",fmt(c_total_c_imp),GREEN)]])}
                    </div>
                    <div style="margin-top:12px;font-size:12px;color:{GRAY}">
                        Custo total: {fmt(c_total)} · Margem real: {fmt(c_total_c_imp-c_total)} ({pct_safe(c_total_c_imp-c_total,c_total_c_imp):.1f}%)
                    </div>
                </div>""",unsafe_allow_html=True)
                if prod_s:
                    conn=get_conn(); conn.execute("INSERT INTO precificacao(produto,custo_insumo,custo_funcionario,custo_sala,custo_total,preco_venda,imposto,margem_pct) VALUES(?,?,?,?,?,?,?,?)",(prod_s,custo_ins,c_func,c_sala,c_total,c_total_c_imp,imposto_sim,margem_desej)); conn.commit();conn.close();st.rerun()

    with tab_peq:
        st.markdown(titulo_secao("Ponto de Equilíbrio","Baseado no modelo real da Integrative — PE calculado em R$ 81.208/mês","⚖️"),unsafe_allow_html=True)
        conn=get_conn(); clin_pe=conn.execute("SELECT * FROM clinica WHERE id=1").fetchone(); conn.close()
        col1,col2=st.columns(2)
        with col1:
            with st.form("form_pe"):
                fat_total=st.number_input("Faturamento esperado R$",value=280000.0,step=5000.0)
                cf_pe=st.number_input("Custos Fixos Totais R$",value=81000.0,step=1000.0)
                cv_pct=st.number_input("% Custos Variáveis sobre fat.",value=25.5,step=0.5)
                if st.form_submit_button("Calcular",use_container_width=True):
                    cv_total=fat_total*cv_pct/100; mc_total=fat_total-cv_total
                    imc=mc_total/fat_total if fat_total else 0; pe=cf_pe/imc if imc else 0
                    ms=fat_total-pe; ms_pct=pct_safe(ms,fat_total)
                    st.markdown(f"""<div style="background:{AMBER}11;border:1px solid {AMBER}33;border-radius:12px;padding:20px">
                        <div style="font-size:10px;color:{AMBER};text-transform:uppercase;letter-spacing:0.1em;margin-bottom:16px">Resultado do Cálculo</div>
                        {''.join([f'<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid {BORDER}"><span style="color:{GRAY};font-size:12px">{lb}</span><span style="color:{cr};font-size:14px;font-weight:700">{vl}</span></div>' for lb,vl,cr in [("Ponto de Equilíbrio",fmt(pe),AMBER),("Margem de Segurança",fmt(ms),GREEN if ms>0 else RED),(f"% Segurança",f"{ms_pct:.1f}%",GREEN if ms_pct>15 else AMBER),(f"Índice MC",f"{imc*100:.1f}%",GREEN)]])}
                    </div>""",unsafe_allow_html=True)
        with col2:
            st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-radius:12px;padding:20px">
                <div style="font-size:12px;font-weight:700;color:{WHITE};margin-bottom:16px">Referência Integrative (2026)</div>
                {''.join([f'<div style="display:flex;justify-content:space-between;padding:10px 0;border-bottom:1px solid {BORDER}"><span style="color:{GRAY};font-size:12px">{lb}</span><span style="color:{cr};font-size:13px;font-weight:600">{vl}</span></div>' for lb,vl,cr in [("Faturamento esperado",fmt(100000),WHITE),("Custos Fixos Totais",fmt(60500),RED),("Custos Variáveis",fmt(25500),RED),("PE Financeiro","R$ 81.208",AMBER),("Margem de Segurança",fmt(18792),GREEN),("% Margem de Segurança","18,8%",GREEN)]])}
                <div style="font-size:11px;color:{GRAY};margin-top:12px;line-height:1.7;border-left:2px solid {AMBER}44;padding-left:12px">
                    O Ponto de Equilíbrio representa o faturamento mínimo necessário para cobrir todos os custos. 
                    Qualquer receita acima desse valor gera EBITDA real para a clínica.
                </div>
            </div>""",unsafe_allow_html=True)

elif aba == "💰  DRE Gerencial":
    st.markdown(titulo_secao("DRE Gerencial","Demonstrativo de resultado com análise de margem — histórico completo 2024–2026","💰"),unsafe_allow_html=True)
    conn=get_conn(); dre_r=conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone(); hist=read_df("SELECT mes,ano,(receita_consultas+receita_procedimentos+receita_recorrencia+receita_outros) as rb,(custo_pessoal+custo_ocupacao+custo_marketing+custo_outros) as cf,custo_insumos FROM dre ORDER BY ano,mes LIMIT 24",conn); conn.close()
    with st.expander("✏️ Lançar DRE do Mês",expanded=not bool(dre_r)):
        with st.form("form_dre"):
            c1,c2,c3,c4=st.columns(4)
            with c1: rc=st.number_input("Consultas R$",value=float(dre_r[3] if dre_r else 0),step=100.0)
            with c2: rp=st.number_input("Procedimentos R$",value=float(dre_r[4] if dre_r else 0),step=100.0)
            with c3: rr=st.number_input("Recorrência LTV R$",value=float(dre_r[5] if dre_r else 0),step=100.0)
            with c4: ro=st.number_input("Outros R$",value=float(dre_r[6] if dre_r else 0),step=100.0)
            c1,c2=st.columns(2)
            with c1: imp_d=st.number_input("Impostos %",value=float(dre_r[7] if dre_r else 8.5),step=0.1)
            with c2: tc_d=st.number_input("Taxa Cartão %",value=float(dre_r[8] if dre_r else 3.0),step=0.1)
            c1,c2,c3,c4,c5=st.columns(5)
            with c1: ins_d=st.number_input("Insumos R$",value=float(dre_r[9] if dre_r else 0),step=100.0)
            with c2: pes_d=st.number_input("Pessoal R$",value=float(dre_r[10] if dre_r else 0),step=100.0)
            with c3: oc_d=st.number_input("Ocupação R$",value=float(dre_r[11] if dre_r else 0),step=100.0)
            with c4: mk_d=st.number_input("Marketing R$",value=float(dre_r[12] if dre_r else 0),step=100.0)
            with c5: ou_d=st.number_input("Outros R$",value=float(dre_r[13] if dre_r else 0),step=100.0)
            if st.form_submit_button("💾 Salvar DRE",use_container_width=True):
                conn=get_conn(); conn.execute("""INSERT INTO dre(mes,ano,receita_consultas,receita_procedimentos,receita_recorrencia,receita_outros,imposto_pct,taxa_cartao_pct,custo_insumos,custo_pessoal,custo_ocupacao,custo_marketing,custo_outros) VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(mes,ano) DO UPDATE SET receita_consultas=excluded.receita_consultas,receita_procedimentos=excluded.receita_procedimentos,receita_recorrencia=excluded.receita_recorrencia,receita_outros=excluded.receita_outros,imposto_pct=excluded.imposto_pct,taxa_cartao_pct=excluded.taxa_cartao_pct,custo_insumos=excluded.custo_insumos,custo_pessoal=excluded.custo_pessoal,custo_ocupacao=excluded.custo_ocupacao,custo_marketing=excluded.custo_marketing,custo_outros=excluded.custo_outros""",(mes_sel,ano_sel,rc,rp,rr,ro,imp_d,tc_d,ins_d,pes_d,oc_d,mk_d,ou_d)); conn.commit();conn.close();st.success("DRE salvo!");st.rerun()
    if dre_r:
        rb=sum([dre_r[i] or 0 for i in [3,4,5,6]]); imp=dre_r[7] or 8.5; tc=dre_r[8] or 3.0
        ins=dre_r[9] or 0; pes=dre_r[10] or 0; oc=dre_r[11] or 0; mk=dre_r[12] or 0; ou=dre_r[13] or 0
        ded=rb*(imp+tc)/100; rl=rb-ded; mc=rl-ins; cf=pes+oc+mk+ou; ebitda=mc-cf; mg=pct_safe(ebitda,rb)
        pe=cf/(1-(imp+tc)/100) if (1-(imp+tc)/100)>0 else 0
        st.markdown(f"<div style='color:{AMBER};font-weight:700;font-size:12px;text-transform:uppercase;letter-spacing:0.08em;margin-bottom:14px'>DRE GERENCIAL — {mes_sel}/{ano_sel}</div>",unsafe_allow_html=True)
        for lbl_d,val_d,pct_d,cor_d,dest_d in [
            ("(+) Faturamento Bruto",rb,100.0,WHITE,False),
            (f"(-) Impostos e Taxas Cartão ({imp+tc:.1f}%)",ded,pct_safe(ded,rb),RED,False),
            ("(=) Receita Líquida Operacional",rl,pct_safe(rl,rb),WHITE,True),
            ("(-) Custos Variáveis — Insumos",ins,pct_safe(ins,rb),RED,False),
            ("(=) Margem de Contribuição",mc,pct_safe(mc,rb),AMBER,True),
            ("(-) Custos Fixos Totais",cf,pct_safe(cf,rb),RED,False),
            ("   Folha de Pessoal + Encargos",pes,pct_safe(pes,rb),GRAY,False),
            ("   Ocupação / Aluguel / IPTU",oc,pct_safe(oc,rb),GRAY,False),
            ("   Marketing e Aquisição de Leads",mk,pct_safe(mk,rb),GRAY,False),
            ("   Outros Custos Fixos",ou,pct_safe(ou,rb),GRAY,False),
            ("(=) EBITDA Operacional",ebitda,mg,GREEN if ebitda>0 else RED,True),
        ]: st.markdown(dre_linha(lbl_d,val_d,pct_d,cor_d,dest_d),unsafe_allow_html=True)
        c1,c2,c3=st.columns(3)
        with c1: st.metric("Ponto de Equilíbrio",fmt(pe),"Faturamento mínimo necessário")
        with c2: st.metric("Margem EBITDA",f"{mg:.1f}%","Saúde operacional real")
        with c3: st.metric("Margem Contribuição",f"{pct_safe(mc,rb):.1f}%","Após insumos variáveis")
        # Histórico comparativo com dados reais
        st.markdown("---")
        st.markdown(f"<div style='font-size:12px;font-weight:600;color:{WHITE};margin:16px 0 10px'>Crescimento Histórico Real (2024–2025)</div>",unsafe_allow_html=True)
        df_hist_dre=pd.DataFrame([{"Mês":k,"Real":v} for k,v in HISTORICO_FAT.items()])
        st.bar_chart(df_hist_dre.set_index("Mês")[["Real"]],color=AMBER,height=220)
        if not hist.empty:
            hist["período"]=hist["mes"]+"/"+hist["ano"].astype(str)
            st.dataframe(hist[["período","rb","cf","custo_insumos"]].rename(columns={"rb":"Receita Bruta","cf":"Custos Fixos","custo_insumos":"Insumos"}),hide_index=True,use_container_width=True)

elif aba == "📐  OKRs":
    st.markdown(titulo_secao("OKRs — Objectives & Key Results","A estrutura de execução estratégica que conecta visão à operação — revisão semanal obrigatória","📐"),unsafe_allow_html=True)
    conn=get_conn(); okdf=read_df("SELECT * FROM okrs WHERE ativo=1 ORDER BY trimestre,objetivo",conn); conn.close()
    with st.expander("➕ Adicionar OKR"):
        with st.form("form_okr"):
            c1,c2=st.columns(2)
            with c1: obj_o=st.text_input("Objetivo"); kr_o=st.text_input("Key Result (mensurável)"); resp_o=st.selectbox("DRI",EQUIPE)
            with c2: meta_o=st.number_input("Meta",min_value=0.0,step=1.0); atu_o=st.number_input("Atual",min_value=0.0,step=1.0); tri_o=st.selectbox("Trimestre",["Q1","Q2","Q3","Q4"])
            if st.form_submit_button("Salvar OKR",use_container_width=True):
                if obj_o:
                    conn=get_conn(); conn.execute("INSERT INTO okrs(objetivo,key_result,meta_val,atual_val,responsavel,trimestre,ano) VALUES(?,?,?,?,?,?,?)",(obj_o,kr_o,meta_o,atu_o,resp_o,tri_o,ano_sel)); conn.commit();conn.close();st.rerun()
    if okdf.empty: st.info("Sem OKRs cadastrados. Defina os objetivos do trimestre.")
    else:
        for tri in ["Q1","Q2","Q3","Q4"]:
            grupo=okdf[okdf["trimestre"]==tri]
            if grupo.empty: continue
            for obj in grupo["objetivo"].unique():
                krs=grupo[grupo["objetivo"]==obj]
                p_obj_list=[pct_safe(kr['atual_val'],kr['meta_val']) for _,kr in krs.iterrows()]
                p_obj=sum(p_obj_list)/len(p_obj_list) if p_obj_list else 0
                _,cor_obj=semaforo(p_obj)
                st.markdown(f'<div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {cor_obj};border-radius:12px;padding:18px 22px;margin-bottom:14px"><div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:14px"><div style="color:{AMBER};font-size:13px;font-weight:700">🎯 {obj}</div><div style="display:flex;align-items:center;gap:12px"><span style="font-size:11px;color:{GRAY}">{tri} / {ano_sel}</span><span style="font-size:14px;font-weight:700;color:{cor_obj}">{p_obj:.0f}%</span></div></div>',unsafe_allow_html=True)
                for _,kr in krs.iterrows():
                    p_kr=pct_safe(kr['atual_val'],kr['meta_val']); _,cor_kr=semaforo(p_kr)
                    st.markdown(f'<div style="background:{BG2};border:1px solid {BORDER};border-radius:8px;padding:12px 14px;margin-bottom:6px"><div style="display:flex;justify-content:space-between;margin-bottom:6px"><span style="color:{WHITE};font-size:12px">{kr["key_result"]}</span><span style="color:{GRAY};font-size:11px">DRI: {kr["responsavel"]}</span></div><div style="display:flex;justify-content:space-between;font-size:10px;color:{GRAY};margin-bottom:4px"><span>Atual: {kr["atual_val"]}</span><span style="color:{cor_kr};font-weight:600">{p_kr:.0f}%</span><span>Meta: {kr["meta_val"]}</span></div><div style="height:4px;background:{BORDER};border-radius:99px;overflow:hidden"><div style="height:4px;width:{min(int(p_kr),100)}%;background:{cor_kr};border-radius:99px"></div></div></div>',unsafe_allow_html=True)
                st.markdown("</div>",unsafe_allow_html=True)


elif aba == "🎓  Programa Integra":
    st.markdown(titulo_secao("Programa Integra","Sistema de desenvolvimento de equipe — MOD diário, pontuação semanal e onboarding 90 dias","🎓"),unsafe_allow_html=True)
    conn=get_conn(); colabs=read_df("SELECT * FROM colaboradores WHERE ativo=1",conn); tarefas_df=read_df("SELECT * FROM mod_tarefas WHERE ativo=1 ORDER BY cargo_key,bloco,horario",conn); conn.close()
    tab_mod,tab_pont,tab_on=st.tabs(["📋 MOD — MODO OPERACIONAL DIÁRIO","⭐ PONTUAÇÃO SEMANAL","🗺️ ONBOARDING 90 DIAS"])
    with tab_mod:
        col_c,col_m=st.columns([1,2])
        with col_c:
            if colabs.empty: st.info("Cadastre colaboradores."); colab_sel="Sem colaborador"
            else: colab_sel=st.selectbox("Colaborador:",colabs['nome'].tolist(),label_visibility="collapsed")
        with col_m:
            if not tarefas_df.empty and not colabs.empty:
                cargo_k=colabs[colabs['nome']==colab_sel]['cargo_key'].values[0] if not colabs[colabs['nome']==colab_sel].empty else ''
                tf=tarefas_df[tarefas_df['cargo_key']==cargo_k]
                score_t=0; max_score=0
                for bloco in ["Abertura","Durante","Fechamento"]:
                    tb=tf[tf['bloco']==bloco]
                    if tb.empty: continue
                    cor_bl=AMBER if bloco=="Abertura" else BLUE if bloco=="Durante" else GRAY
                    st.markdown(f"<div style='color:{cor_bl};font-size:10px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin:12px 0 6px'>{bloco}</div>",unsafe_allow_html=True)
                    for _,t in tb.iterrows():
                        conn=get_conn(); ex=conn.execute("SELECT concluida FROM mod_execucao WHERE tarefa_id=? AND colaborador=? AND data_exec=?",(t['id'],colab_sel,date.today().isoformat())).fetchone(); conn.close()
                        ja=bool(ex and ex[0]); max_score+=t['peso']
                        chk=st.checkbox(f"{t['titulo']} ({t['peso']}%)",value=ja,key=f"t_{t['id']}_{colab_sel}")
                        if chk: score_t+=t['peso']
                        if chk and not ja:
                            conn=get_conn(); conn.execute("INSERT OR REPLACE INTO mod_execucao(tarefa_id,colaborador,data_exec,concluida) VALUES(?,?,?,1)",(t['id'],colab_sel,date.today().isoformat())); conn.commit();conn.close()
                        st.markdown(f"<div style='font-size:10px;color:{GRAY2};margin:-6px 0 4px 22px'>📦 {t['dri']}</div>",unsafe_allow_html=True)
                sc=min(pct_safe(score_t,max_score),100) if max_score else 0; _,cor_sc=semaforo(sc)
                st.markdown(f"""<div style="background:{BG2};border:1px solid {BORDER};border-left:3px solid {cor_sc};border-radius:12px;padding:16px;text-align:center;margin-top:16px">
                    <div style="font-size:9px;color:{GRAY};text-transform:uppercase;letter-spacing:0.15em">Score MOD — Hoje</div>
                    <div style="font-size:2.5rem;font-weight:700;color:{cor_sc};letter-spacing:-0.03em">{sc:.0f}%</div>
                    <div style="font-size:11px;color:{GRAY}">{"✅ Meta atingida" if sc>=85 else "⚠️ Abaixo de 85%"}</div>
                </div>""",unsafe_allow_html=True)
        with st.expander("➕ Adicionar Tarefa ao MOD"):
            with st.form("form_mod_add"):
                c1,c2,c3,c4,c5=st.columns(5)
                with c1: tit_t=st.text_input("Tarefa")
                with c2: ck_t=st.selectbox("Função",list(CARGO_MAP.keys()),format_func=lambda x:CARGO_MAP[x])
                with c3: bl_t=st.selectbox("Bloco",["Abertura","Durante","Fechamento"])
                with c4: hr_t=st.text_input("Horário",value="09:00")
                with c5: peso_t=st.number_input("Peso %",value=10,min_value=1,max_value=40)
                dri_t=st.text_input("Entrega esperada")
                if st.form_submit_button("Adicionar",use_container_width=True):
                    if tit_t:
                        conn=get_conn(); conn.execute("INSERT INTO mod_tarefas(titulo,cargo_key,responsavel,dri,bloco,horario,frequencia,categoria,peso) VALUES(?,?,?,?,?,?,?,?,?)",(tit_t,ck_t,CARGO_MAP[ck_t],dri_t,bl_t,hr_t,"Diaria","Operacional",peso_t)); conn.commit();conn.close();st.rerun()
    with tab_pont:
        sw=f"S{date.today().isocalendar()[1]}"
        if not colabs.empty:
            for _,colab in colabs.iterrows():
                conn=get_conn(); pt=conn.execute("SELECT * FROM integra_pont WHERE colaborador_id=? AND semana=? AND ano=?",(colab['id'],sw,ano_sel)).fetchone(); conn.close()
                vp={k:pt[i+3] if pt else 0 for i,k in enumerate(['entregas','qualidade','cultura','indicadores','melhoria'])}
                total_p=sum(vp.values()); _,cor_p=semaforo(total_p)
                nivel_p="🏆 Excelência" if total_p>=85 else "⭐ Alta Performance" if total_p>=70 else "📈 Constante" if total_p>=50 else "🔧 Em Evolução"
                with st.expander(f"{colab['nome']} — {colab['funcao']} — {total_p}/100 — {nivel_p}"):
                    with st.form(f"pt_{colab['id']}"):
                        c1,c2,c3,c4,c5=st.columns(5)
                        nv={}
                        for col_d,lbl_d,key_d in [(c1,"Entregas","entregas"),(c2,"Qualidade","qualidade"),(c3,"Cultura","cultura"),(c4,"Indicadores","indicadores"),(c5,"Melhoria","melhoria")]:
                            with col_d: nv[key_d]=st.number_input(lbl_d,min_value=0,max_value=20,value=int(vp[key_d]),key=f"{key_d}_{colab['id']}")
                        obs_p=st.text_input("Observação",value=pt[8] if pt else "",key=f"obs_{colab['id']}")
                        if st.form_submit_button("Salvar",use_container_width=True):
                            conn=get_conn(); conn.execute("INSERT INTO integra_pont(colaborador_id,semana,ano,entregas,qualidade,cultura,indicadores,melhoria,obs) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(colaborador_id,semana,ano) DO UPDATE SET entregas=excluded.entregas,qualidade=excluded.qualidade,cultura=excluded.cultura,indicadores=excluded.indicadores,melhoria=excluded.melhoria,obs=excluded.obs",(colab['id'],sw,ano_sel,nv['entregas'],nv['qualidade'],nv['cultura'],nv['indicadores'],nv['melhoria'],obs_p)); conn.commit();conn.close();st.rerun()
    with tab_on:
        colab_on=st.selectbox("Colaborador",EQUIPE,key="on_sel2")
        conn=get_conn(); cid_r2=conn.execute("SELECT id FROM colaboradores WHERE nome=?",(colab_on,)).fetchone(); conn.close()
        cid2=cid_r2[0] if cid_r2 else 1
        for fn,nm_f,cor_f,tarefas_f in [
            (1,"ACOLHER — Dias 1 a 7",AMBER,["Apresentar equipe, espaço e Manifesto da Clínica","Leitura comentada dos valores e Golden Circle","Explicar Projeto Ponteiro e Programa Integra","Mostrar jornada completa do paciente","Apresentar os sistemas operacionais"]),
            (2,"APRENDER — Dias 8 a 30",BLUE,["Treinar MOD da função (abertura, meio e fechamento)","Treinar scripts SBAR e comunicação","Treinar uso do CRM com supervisão","Executar rotina com acompanhamento próximo"]),
            (3,"EXECUTAR — Dias 31 a 60",GREEN,["Executar MOD com autonomia supervisionada","Registrar evidências de execução diariamente","Atingir primeiros indicadores do cargo"]),
            (4,"MELHORAR — Dias 61 a 90",PURPLE,["Propor ao menos 1 melhoria de processo documentada","Assumir indicadores próprios","Reunião 1:1 com plano de metas"]),
            (5,"CRESCER — Após 90 dias",GRAY,["Assumir mais responsabilidade na função","Treinar colaboradores novos"])]:
            st.markdown(f"<div style='color:{cor_f};font-weight:700;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;margin:12px 0 6px'>{nm_f}</div>",unsafe_allow_html=True)
            for tf in tarefas_f:
                conn=get_conn(); on_r=conn.execute("SELECT concluido FROM onboarding WHERE colaborador_id=? AND modulo=? AND fase=?",(cid2,tf,fn)).fetchone(); conn.close()
                chk_f=st.checkbox(tf,value=bool(on_r and on_r[0]),key=f"on2_{fn}_{tf[:20]}_{cid2}")
                if chk_f and not (on_r and on_r[0]):
                    conn=get_conn(); conn.execute("INSERT OR REPLACE INTO onboarding(colaborador_id,modulo,fase,concluido,data_conclusao) VALUES(?,?,?,1,?)",(cid2,tf,fn,date.today().isoformat())); conn.commit();conn.close()

elif aba == "🩻  Segurança Assistencial":
    st.markdown(titulo_secao("Segurança Assistencial","Checklist clínico por paciente — evolução no dia, D+1 obrigatório, registro de intercorrências","🩻"),unsafe_allow_html=True)
    conn=get_conn(); sg_df=read_df("SELECT * FROM seguranca ORDER BY data_atend DESC LIMIT 20",conn); conn.close()
    if not sg_df.empty:
        sem_d1=sg_df[(sg_df['d1_enviado']==0)&(pd.to_datetime(sg_df['data_atend'])<pd.Timestamp(date.today().isoformat()))]
        if len(sem_d1)>0: st.error(f"🚨 {len(sem_d1)} paciente(s) sem D+1 enviado — Paloma, enviar até 10h!")
    with st.expander("➕ Registrar Atendimento"):
        with st.form("form_seg"):
            c1,c2,c3=st.columns(3)
            with c1: pac_s=st.text_input("Paciente"); dt_s=st.date_input("Data",value=date.today())
            with c2: resp_s=st.text_input("Responsável",value="Paloma")
            with c3: pass
            c1,c2=st.columns(2)
            with c1:
                ch1=st.checkbox("Injetáveis e materiais conferidos na bancada")
                ch2=st.checkbox("Nome, LOTE e VALIDADE conferidos NA FRENTE do paciente")
                ch3=st.checkbox("Protocolo preparado por ordem de pH")
                ch4=st.checkbox("Alergia verificada e protocolo explicado")
            with c2:
                ch5=st.checkbox("Assinatura do registro ANTES de iniciar")
                ch6=st.checkbox("Evolução técnica registrada no mesmo dia")
                ch7=st.checkbox("Próxima sessão sinalizada para Beatriz")
                inter=st.checkbox("🚨 Ocorreu intercorrência?")
            desc_inter=st.text_area("Descrever a intercorrência") if inter else ""
            if st.form_submit_button("Registrar",use_container_width=True):
                if pac_s:
                    conn=get_conn(); conn.execute("INSERT INTO seguranca(paciente,data_atend,responsavel,ch1,ch2,ch3,ch4,ch5,ch6,ch7,intercorrencia,desc_inter) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(pac_s,dt_s.isoformat(),resp_s,int(ch1),int(ch2),int(ch3),int(ch4),int(ch5),int(ch6),int(ch7),int(inter),desc_inter)); conn.commit();conn.close()
                    if inter: st.error("🚨 INTERCORRÊNCIA registrada! Notifique Dra. Bárbara via SBAR imediatamente.")
                    else: st.success("Atendimento registrado!");st.rerun()
    if not sg_df.empty: st.dataframe(sg_df[['paciente','data_atend','responsavel','ch1','ch2','ch6','ch7','intercorrencia','d1_enviado']],hide_index=True,use_container_width=True)

elif aba == "📓  Diário de Bordo":
    st.markdown(titulo_secao("Diário de Bordo — SBAR","Toda ocorrência relevante segue o padrão Situação · Background · Avaliação · Recomendação","📓"),unsafe_allow_html=True)
    with st.expander("➕ Criar Comunicado SBAR",expanded=True):
        with st.form("form_sbar"):
            c1,c2,c3=st.columns(3)
            with c1: tp_sb=st.selectbox("Tipo",["Resumo Diário","Evento Adverso","Problema Operacional","Alerta Comercial","Pedido de Apoio"])
            with c2: rem_sb=st.selectbox("Remetente",EQUIPE)
            with c3: dest_sb=st.selectbox("Destinatário",["Dr. Vinícius Mariano","Dra. Bárbara Mariano","Vanessa","Bianca"])
            sit_sb=st.text_area("S — SITUAÇÃO: O que está acontecendo agora?",height=80)
            bg_sb=st.text_area("B — BACKGROUND: Contexto e histórico",height=80)
            av_sb=st.text_area("A — AVALIAÇÃO: Sua leitura sobre o problema",height=80)
            c1,c2,c3=st.columns(3)
            with c1: rec_sb=st.text_area("R — RECOMENDAÇÃO",height=80)
            with c2: dri_sb=st.selectbox("DRI da ação",EQUIPE)
            with c3: prazo_sb=st.text_input("Prazo",value="Hoje até 18h")
            if st.form_submit_button("Enviar Comunicado",use_container_width=True):
                if sit_sb:
                    conn=get_conn(); conn.execute("INSERT INTO sbar(tipo,remetente,destinatario,situacao,background,avaliacao,recomendacao,dri_acao,prazo) VALUES(?,?,?,?,?,?,?,?,?)",(tp_sb,rem_sb,dest_sb,sit_sb,bg_sb,av_sb,rec_sb,dri_sb,prazo_sb)); conn.commit();conn.close();st.success(f"Comunicado enviado para {dest_sb}!");st.rerun()
    conn=get_conn(); sb_df=read_df("SELECT * FROM sbar ORDER BY data DESC LIMIT 20",conn); conn.close()
    if not sb_df.empty:
        pend=sb_df[sb_df['resolvido']==0]
        if len(pend)>0: st.warning(f"{len(pend)} comunicado(s) pendente(s) de resolução.")
        for _,sb in sb_df.iterrows():
            cor_s=AMBER if not sb['resolvido'] else GRAY2
            st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {cor_s};border-radius:12px;padding:14px;margin-bottom:8px">
                <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                    <strong style="color:{WHITE};font-size:12px">{sb['tipo']}</strong>
                    <span style="font-size:10px;color:{GRAY}">{sb['remetente']} → {sb['destinatario']} · {str(sb['data'])[:10]}</span>
                </div>
                <div style="font-size:11px;line-height:1.8;color:{GRAY}">
                    <strong style="color:{RED}">S:</strong> {sb['situacao']}<br>
                    <strong style="color:{BLUE}">A:</strong> {sb['avaliacao']}<br>
                    <strong style="color:{GREEN}">R:</strong> {sb['recomendacao']} — DRI: <strong style="color:{WHITE}">{sb['dri_acao']}</strong> · Prazo: {sb['prazo']}
                </div>
            </div>""",unsafe_allow_html=True)
            if not sb['resolvido']:
                if st.button("✅ Marcar como resolvido",key=f"res_{sb['id']}"):
                    conn=get_conn(); conn.execute("UPDATE sbar SET resolvido=1 WHERE id=?",(sb['id'],)); conn.commit();conn.close();st.rerun()


elif aba == "📚  Biblioteca":
    st.markdown(titulo_secao("Biblioteca Executiva","Manual operacional, glossário de termos e base de conhecimento da Integrative","📚"),unsafe_allow_html=True)
    tab_man,tab_glos,tab_cult=st.tabs(["📖 MANUAL OPERACIONAL","📘 GLOSSÁRIO EXECUTIVO","🎯 CULTURA & VALORES"])

    with tab_man:
        st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {AMBER};border-radius:12px;padding:20px;margin-bottom:20px">
            <div style="font-size:11px;color:{AMBER};font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">CLÍNICA INTEGRATIVE CAMPINAS</div>
            <div style="font-size:1.3rem;font-weight:700;color:{WHITE};margin-bottom:6px">Operational Excellence Manual 2026</div>
            <div style="font-size:12px;color:{GRAY}">A Architecture of Predictable Revenue Growth · Versão 2026 · Projeto Ponteiro · Método AME</div>
        </div>""",unsafe_allow_html=True)
        capitulos = {
            "CAPÍTULO 1 — Briefing Executivo": """A Ciência de Escalar Faturamento em Clínicas de Alta Performance

Clínicas de medicina funcional e integrativa operam num dos segmentos de maior valor percebido da saúde privada. O problema não está na demanda. Está na arquitetura interna.

**As Quatro Alavancas de Escala:**
1. **Capacidade de Atendimento** — ocupação de salas e agenda dos prescritores
2. **Conversão Comercial** — velocidade de resposta, follow-up e fechamento
3. **Retenção e LTV** — protocolo D+1, régua de acompanhamento e RFM
4. **Eficiência Operacional** — MOD, processos e gestão por indicadores

Organizações de saúde que operam sem método operacional estruturado perdem, em média, entre 20% e 35% do faturamento potencial por ineficiência operacional, não por falta de demanda.""",
            "CAPÍTULO 2 — Estrutura Organizacional": """Quem Decide. Quem Executa. Quem Responde.

A ausência de clareza sobre responsabilidades é a principal causa de retrabalho em organizações de serviço.

**Organograma Funcional:**
- **Dr. Vinícius Mariano** (CEO) — Estratégia, financeiro, RH e cultura
- **Dra. Bárbara Mariano** (Diretora Técnica) — Protocolos, qualidade assistencial
- **Vanessa** (Gerente Executiva) — Execução diária, agenda, indicadores e processos
- **Bianca** (Coord. Comercial) — Fechamento, orçamentos e conversão de alto valor
- **Aline** (Analista de Leads) — Qualificação e gestão de pipeline comercial
- **Beatriz** (Recepção Comercial) — Acolhimento, agenda, RFM e indicações
- **Paloma** (Enfermeira Assistencial) — Cuidado técnico, segurança e protocolos""",
            "CAPÍTULO 3 — Execução Prioritária": """As 3 Ações Diárias que Movem o Faturamento

Das dezenas de tarefas que compõem a operação de uma clínica, um número pequeno concentra a maior parte do impacto sobre o faturamento.

**Gerente (Vanessa):** Confirmar 100% da agenda do dia · Revisar pipeline com Bianca · Definir meta diária com DRI e prazo

**Analista de Leads (Aline):** Responder 100% dos leads em até 5min · Executar follow-up da cadência · Sinalizar leads quentes para Bianca fechar no mesmo dia

**Closer (Bianca):** Nunca deixar orçamento quente mais de 24h sem ação · Conduzir pelo valor, não pelo preço · Garantir próxima etapa definida em cada contato

**Recepção (Beatriz):** Confirmar agendamentos D-1 · Solicitar indicações ao final de cada atendimento · Executar RFM de 30 contatos por dia

**Enfermeira (Paloma):** Conferir insumos antes de cada paciente · Realizar evolução técnica no dia · Enviar D+1 até 10h do dia seguinte""",
            "CAPÍTULO 4 — MOD (Modo Operacional Diário)": """O MOD: Transformando Estratégia em Rotina

O Modo Operacional Diário é a estrutura que impede que a estratégia dependa de memória, humor ou urgência para acontecer. É a diferença entre uma clínica que funciona com o dono presente e uma que funciona com o dono ausente.

**Abertura — 08h30:** Abertura de caixa · Levantamento de leads · Verificação de agenda · Confirmações · Definição de prioridades com DRI

**Checkpoint — 09h00 (máx. 15 min):** Alinhamento de equipe · Meta do dia · Escala do almoço · Pendências da véspera

**Tarde — 14h00:** Revisão de orçamentos com Bianca · Atualização de indicadores · Pipeline comercial

**Fechamento — 17h30:** Conferência de caixa · Registro de pendências · SBAR diário para Dr. Vinícius""",
            "CAPÍTULO 5 — Controle Gerencial": """Rota de Conferência Diária da Gerente

A gerente não é avaliada pelo que planejou. É avaliada pelo que aconteceu.

**Evidências Obrigatórias ao Final de Cada Dia:**
- Caixa fechado e conciliado ✓
- DRE do dia atualizado ✓
- MOD com score acima de 85% ✓
- SBAR enviado para Dr. Vinícius ✓
- Orçamentos quentes com próxima ação ✓
- Leads respondidos dentro de 5 minutos ✓
- D+1 enviados pela Paloma ✓""",
        }
        cap_sel=st.selectbox("Selecionar capítulo",list(capitulos.keys()),label_visibility="visible")
        st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-radius:12px;padding:24px">
            <div style="font-size:12px;font-weight:700;color:{AMBER};margin-bottom:14px;text-transform:uppercase;letter-spacing:0.08em">{cap_sel}</div>
            <div style="font-size:13px;color:{GRAY};line-height:1.8;white-space:pre-line">{capitulos[cap_sel]}</div>
        </div>""",unsafe_allow_html=True)

    with tab_glos:
        st.markdown(titulo_secao("Glossário de Termos Gerenciais","Vocabulário executivo para liderança de alta performance em clínicas"),unsafe_allow_html=True)
        GLOSSARIO = {
            "AME (Ação · Movimento · Entrega)": "Método estrutural do Projeto Ponteiro. Toda estratégia deve especificar: O que precisa ser feito (Ação), Quem executa, quando e como acompanha (Movimento), e qual resultado mensurável deve acontecer (Entrega). Sem os três elementos, a estratégia existe apenas no campo das intenções.",
            "EBITDA (Earnings Before Interest, Taxes, Depreciation and Amortization)": "Lucro operacional antes de juros, impostos, depreciação e amortização. É o principal indicador de saúde operacional de uma clínica. EBITDA acima de 20% indica operação saudável; acima de 30%, operação de alta performance.",
            "DRE (Demonstrativo de Resultado do Exercício)": "Documento que apresenta receitas, custos e resultado líquido de um período. Na gestão de clínicas, o DRE gerencial simplificado permite tomar decisões em tempo real sem depender do contador.",
            "DRI (Direct Responsible Individual)": "Conceito da Apple. O responsável direto por uma tarefa, meta ou processo. Sem DRI, não existe responsabilidade. Toda tarefa no LAB Metrics tem um DRI — o sistema não aceita tarefas sem dono.",
            "MOD (Modo Operacional Diário)": "Estrutura de rotinas que transforma estratégia em execução diária. O MOD define o que cada colaborador faz, quando faz, como acompanha e qual entrega gera. É a operacionalização do Projeto Ponteiro.",
            "Margem de Contribuição (MC)": "Receita menos custos variáveis. Indica quanto cada serviço ou procedimento efetivamente contribui para cobrir os custos fixos e gerar lucro. MC abaixo de 40% exige revisão de precificação ou redução de custos variáveis.",
            "Ponto de Equilíbrio (PE)": "Faturamento mínimo necessário para cobrir todos os custos. Qualquer receita acima do PE gera EBITDA real. Para a Integrative, o PE referência é R$ 81.208/mês, calculado com base nos custos fixos de R$ 60.500 e índice de MC de 74,5%.",
            "RFM (Recência · Frequência · Monetização)": "Metodologia de segmentação de base de pacientes. Recência: quando foi a última visita. Frequência: quantas vezes retornou. Monetização: quanto investiu. Pacientes de alto valor RFM são os mais rentáveis de reativar.",
            "SBAR (Situação · Background · Avaliação · Recomendação)": "Protocolo de comunicação estruturada desenvolvido pela Marinha dos EUA, adotado em saúde. Elimina ambiguidade em comunicações críticas. Toda intercorrência, problema ou comunicado relevante na Integrative segue o padrão SBAR.",
            "SPIN Selling": "Metodologia de vendas consultivas de Neil Rackham. S: Situação (entender o contexto). P: Problema (identificar a dor). I: Implicação (mostrar o custo de não resolver). N: Necessidade (apresentar a solução). Leads trabalhados com SPIN convertem 3,2x mais.",
            "LTV (Lifetime Value)": "Valor total que um paciente gera ao longo de toda a sua jornada com a clínica. Aumentar LTV é mais barato do que captar novos pacientes. Clínicas de alta performance têm LTV médio 4-6x superior ao ticket da primeira consulta.",
            "CAC (Custo de Aquisição de Cliente)": "Investimento total em marketing e vendas dividido pelo número de novos pacientes captados. Paciente de indicação tem CAC 5x menor que paciente de tráfego pago. Por isso o programa de indicações é uma das alavancas mais rentáveis.",
            "OKR (Objective & Key Results)": "Framework de gestão de objetivos popularizado pelo Google. O (Objective): o que queremos alcançar — qualitativo e inspirador. KR (Key Results): como mediremos o sucesso — quantitativos e mensuráveis. OKRs revisados semanalmente têm 4x mais chance de serem alcançados.",
            "FIFO (First In, First Out)": "Princípio de gestão de estoque e fila: o primeiro que entra é o primeiro que sai. Aplicado na gestão de leads: o lead mais antigo sem resposta é o prioritário. Aplicado em insumos: o material com validade mais próxima é usado primeiro.",
            "KPI (Key Performance Indicator)": "Indicador-chave de desempenho. Métrica que sinaliza se a operação está no caminho certo. Na Integrative, os KPIs mais críticos são: taxa de ocupação de sala (meta: 85%), conversão de leads (meta: 30%), tempo de resposta (meta: <5min) e EBITDA (meta: >25%).",
            "Taxa de Churn": "Percentual de pacientes que abandonam o acompanhamento em um período. Alta taxa de churn indica problema na experiência clínica ou na régua de relacionamento. O protocolo D+1 é o principal redutor de churn da Integrative.",
            "Funil Comercial": "Representação das etapas que um lead percorre até se tornar paciente ativo. Lead → Qualificação → Agendamento → Comparecimento → Conversão → Retenção. Identificar onde o funil vaza é o passo para aumentar conversão sem aumentar CAC.",
            "Ticket Médio": "Valor médio por atendimento ou procedimento. Aumentar ticket médio é uma das alavancas mais eficientes de crescimento de faturamento sem aumento de estrutura. A Integrative monitora ticket médio por prescritor e por categoria de serviço.",
            "MRR (Monthly Recurring Revenue)": "Receita mensal recorrente — valor gerado por protocolos, assinaturas ou acompanhamentos com frequência previsível. MRR é o componente mais valioso do faturamento porque elimina a dependência de novos leads para manter o resultado.",
            "Break-even": "Equivalente em inglês ao Ponto de Equilíbrio. Momento em que a receita cobre exatamente todos os custos. Empresas com break-even baixo têm mais resiliência financeira e mais rápido acesso ao lucro real.",
        }
        busca_g = st.text_input("🔍 Buscar termo", placeholder="Digite para filtrar...")
        for termo, definicao in GLOSSARIO.items():
            if busca_g.lower() in termo.lower() or busca_g.lower() in definicao.lower() or not busca_g:
                with st.expander(termo):
                    st.markdown(f"<div style='font-size:13px;color:{GRAY};line-height:1.8'>{definicao}</div>",unsafe_allow_html=True)

    with tab_cult:
        st.markdown(titulo_secao("Cultura & Valores","O DNA operacional da Integrative Campinas — o que acreditamos define como operamos"),unsafe_allow_html=True)
        valores = [
            ("🎯","Execução é o padrão","Ideias sem execução são apenas intenções bem-intencionadas. Na Integrative, o que conta é o que foi entregue, não o que foi planejado. Toda reunião termina com ação, DRI e prazo."),
            ("🤝","O paciente no centro","Cada decisão operacional passa pelo filtro: isso melhora a experiência do paciente? Se não, não vale o esforço. A Integrative não vende consultas — entrega rotas de cuidado."),
            ("📊","Dados antes de opiniões","Crescimento sustentável é construído sobre indicadores reais, não sobre percepções. Quando há divergência, os dados decidem. Quando não há dados, criamos a métrica antes de agir."),
            ("🔁","Melhoria contínua como hábito","Cada processo pode ser melhorado. Cada script pode ser aprimorado. Cada resultado pode ser superado. A Integrative não tolera 'sempre foi assim' como resposta."),
            ("💎","Alto padrão em tudo","Premium não é apenas o preço. É a qualidade do acolhimento, da prescrição, do follow-up, do espaço e da comunicação. Qualquer ponto de contato com o paciente é uma oportunidade de surpreender."),
        ]
        for icon, titulo_v, desc_v in valores:
            st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {AMBER};border-radius:12px;padding:18px 22px;margin-bottom:12px">
                <div style="display:flex;align-items:flex-start;gap:14px">
                    <div style="font-size:1.5rem;flex-shrink:0">{icon}</div>
                    <div>
                        <div style="font-size:14px;font-weight:700;color:{WHITE};margin-bottom:6px">{titulo_v}</div>
                        <div style="font-size:12px;color:{GRAY};line-height:1.7">{desc_v}</div>
                    </div>
                </div>
            </div>""",unsafe_allow_html=True)


elif aba == "🧬  Importar Dados":
    st.markdown(titulo_secao("Importar Dados","Ingestão de relatórios do Support Clinic — extração automática por IA com diagnóstico AME","🧬"),unsafe_allow_html=True)
    st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-radius:12px;padding:18px 22px;margin-bottom:20px">
        <div style="font-size:10px;color:{AMBER};text-transform:uppercase;letter-spacing:0.1em;font-weight:700;margin-bottom:14px">COMO EXPORTAR DO SUPPORT CLINIC</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px">
            {''.join([f'<div style="display:flex;gap:10px;align-items:flex-start"><div style="width:24px;height:24px;background:{AMBER};border-radius:50%;display:flex;align-items:center;justify-content:center;color:#000;font-weight:700;font-size:12px;flex-shrink:0">{n}</div><div><div style="font-size:12px;font-weight:600;color:{WHITE}">{t}</div><div style="font-size:10px;color:{GRAY}">{d}</div></div></div>' for n,t,d in [(1,"Support Clinic","app.supportclinic.com.br"),(2,"Relatórios","Menu lateral"),(3,"Filtrar período","Selecione o mês"),(4,"Exportar CSV","Formato ideal")]])}
        </div>
    </div>""",unsafe_allow_html=True)
    arquivo=st.file_uploader("Arraste o arquivo",type=["csv","txt","pdf","xlsx"])
    if arquivo:
        st.success(f"Arquivo recebido: **{arquivo.name}**")
        conteudo=""; df_prev=None
        try:
            if arquivo.name.endswith((".csv",".txt")):
                raw=arquivo.read()
                for enc in ["utf-8","latin-1","cp1252"]:
                    try: conteudo=raw.decode(enc); break
                    except: continue
                try: df_prev=pd.read_csv(io.StringIO(conteudo),sep=None,engine='python',nrows=20); st.dataframe(df_prev,use_container_width=True)
                except: st.code(conteudo[:600])
            elif arquivo.name.endswith(".xlsx"):
                df_prev=pd.read_excel(arquivo,nrows=20); conteudo=df_prev.to_csv(index=False); st.dataframe(df_prev,use_container_width=True)
        except Exception as e: st.error(f"Erro ao ler: {e}")
        if conteudo and st.button("🧬 Processar com IA — Diagnóstico AME",use_container_width=True):
            try:
                import streamlit as _st
                api_key=_st.secrets.get("ANTHROPIC_API_KEY",os.environ.get("ANTHROPIC_API_KEY",""))
            except: api_key=os.environ.get("ANTHROPIC_API_KEY","")
            if not api_key: st.error("Configure ANTHROPIC_API_KEY nos Secrets.")
            else:
                with st.spinner("IA analisando com Método AME..."):
                    try:
                        client=anthropic.Anthropic(api_key=api_key)
                        msg=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=1800,messages=[{"role":"user","content":f"""Você é o consultor executivo do LAB Metrics. Analise o relatório do SupportClinic e aplique o Método AME.
RELATÓRIO: {conteudo[:8000]}
Responda APENAS em JSON sem markdown:
{{"indicadores":{{"faturamento_bruto":null,"consultas_realizadas":null,"ticket_medio":null,"no_show":null,"taxa_conversao_pct":null}},"estagio_maturidade":"Caótico|Intuitivo|Documentado|Previsível","diagnostico_executivo":"máx 120 palavras","pontos_positivos":["p1","p2","p3"],"gargalos_identificados":["g1","g2","g3"],"plano_ame":[{{"acao":"...","movimento":"...","entrega":"...","dri":"...","prazo":"..."}}]}}"""}])
                        raw=msg.content[0].text.strip().replace("```json","").replace("```","").strip()
                        res=json.loads(raw)
                        conn=get_conn(); conn.execute("INSERT INTO relatorios(nome_arquivo,conteudo,analise_ia,mes,ano) VALUES(?,?,?,?,?)",(arquivo.name,conteudo[:20000],json.dumps(res,ensure_ascii=False),mes_sel,ano_sel)); conn.commit();conn.close()
                        st.markdown(f"""<div style="background:{BG3};border:1px solid {AMBER}33;border-radius:12px;padding:22px;margin:16px 0">
                            <div style="color:{AMBER};font-size:10px;text-transform:uppercase;letter-spacing:0.1em;font-weight:700;margin-bottom:12px">DIAGNÓSTICO EXECUTIVO</div>
                            <div style="color:{WHITE};font-size:13px;line-height:1.8">{res.get('diagnostico_executivo','')}</div>
                        </div>""",unsafe_allow_html=True)
                        col_pos,col_gar=st.columns(2)
                        with col_pos:
                            st.markdown(f"<div style='color:{GREEN};font-weight:700;font-size:12px;margin-bottom:8px'>✅ Pontos Positivos</div>",unsafe_allow_html=True)
                            for p in res.get("pontos_positivos",[]): st.markdown(f"<div style='color:{GRAY};font-size:12px;margin-bottom:4px'>→ {p}</div>",unsafe_allow_html=True)
                        with col_gar:
                            st.markdown(f"<div style='color:{RED};font-weight:700;font-size:12px;margin-bottom:8px'>⚠️ Gargalos</div>",unsafe_allow_html=True)
                            for g in res.get("gargalos_identificados",[]): st.markdown(f"<div style='color:{GRAY};font-size:12px;margin-bottom:4px'>→ {g}</div>",unsafe_allow_html=True)
                        st.markdown(f"<div style='color:{AMBER};font-weight:700;font-size:13px;margin:20px 0 12px;text-transform:uppercase;letter-spacing:0.05em'>PLANO AME — AÇÕES PRIORITÁRIAS</div>",unsafe_allow_html=True)
                        for i,ame in enumerate(res.get("plano_ame",[]),1):
                            st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-left:3px solid {AMBER};border-radius:10px;padding:14px;margin-bottom:8px">
                                <div style="display:flex;gap:12px">
                                    <div style="width:28px;height:28px;background:{AMBER};border-radius:50%;display:flex;align-items:center;justify-content:center;color:#000;font-weight:700;font-size:12px;flex-shrink:0">{i}</div>
                                    <div>
                                        <div style="color:{WHITE};font-weight:600;font-size:13px;margin-bottom:4px">AÇÃO: {ame.get('acao','')}</div>
                                        <div style="color:{GRAY};font-size:11px;margin-bottom:2px"><strong style="color:{BLUE}">MOVIMENTO:</strong> {ame.get('movimento','')}</div>
                                        <div style="color:{GREEN};font-size:11px;margin-bottom:4px">📦 ENTREGA: {ame.get('entrega','')}</div>
                                        <div style="display:flex;gap:14px;font-size:10px"><span style="color:{GRAY}">DRI: <strong style="color:{WHITE}">{ame.get('dri','')}</strong></span><span style="color:{GRAY}">Prazo: <strong style="color:{AMBER}">{ame.get('prazo','')}</strong></span></div>
                                    </div>
                                </div>
                            </div>""",unsafe_allow_html=True)
                    except json.JSONDecodeError: st.markdown(f"<div style='color:{WHITE};font-size:13px;line-height:1.8'>{raw}</div>",unsafe_allow_html=True)
                    except Exception as e: st.error(f"Erro: {e}")

elif aba == "🤖  Assistente IA":
    st.markdown(titulo_secao("Assistente LAB Metrics","Consultor executivo digital — análise estratégica, diagnóstico operacional e recomendações baseadas em dados reais","🤖"),unsafe_allow_html=True)
    SYSTEM_PROMPT_ASSISTENTE = f"""Você é o LAB Metrics, consultor executivo digital da Clínica Integrative Campinas.
Especialista em medicina funcional, gestão de clínicas de alta performance e metodologia Projeto Ponteiro.

IDENTIDADE E POSTURA:
- Comunicação direta, sem rodeios, sem travessões
- Nível executivo — como um artigo da Harvard Business Review, mas em português claro
- Toda resposta termina com ação concreta: DRI, prazo e indicador
- Foco no que move o ponteiro do faturamento

CONTEXTO DA CLÍNICA:
- Faturamento 2024: R$ 1.291.485 (média mensal R$ 107.624)
- Faturamento 2025: R$ 2.484.690 (média mensal R$ 207.057)
- Crescimento 2024→2025: +92%
- Meta 2026: R$ 280.000/mês
- Ponto de equilíbrio: R$ 81.208/mês
- Margem de segurança atual: 18,8%

EQUIPE:
Dr. Vinícius Mariano (CEO) · Dra. Bárbara Mariano (Diretora Técnica)
Vanessa (Gerente) · Bianca (Closer) · Aline (Leads) · Beatriz (Recepção/RFM) · Paloma (Enfermagem)

METODOLOGIA:
Projeto Ponteiro + Método AME (Ação, Movimento, Entrega) + MOD + Programa Integra
4 Motores: Leads Novos · RFM · Indicações · Recorrência Terapêutica

REGRA DE OURO: Nenhuma análise sem ação. Nenhuma ação sem DRI. Nenhum DRI sem prazo."""

    try:
        import streamlit as _st
        api_key=_st.secrets.get("ANTHROPIC_API_KEY",os.environ.get("ANTHROPIC_API_KEY",""))
    except: api_key=os.environ.get("ANTHROPIC_API_KEY","")

    conn=get_conn()
    dre_ctx=conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone()
    clin_ctx=conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    leads_ctx=conn.execute("SELECT COUNT(*),SUM(convertido),AVG(tempo_resp) FROM leads WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone()
    conn.close()
    rb_ctx=sum([(dre_ctx[i] or 0) for i in [3,4,5,6]]) if dre_ctx else 0
    meta_ctx=clin_ctx[2] if clin_ctx else 280000
    l_tot_ctx=leads_ctx[0] or 0; l_conv_ctx=leads_ctx[1] or 0
    tx_conv_ctx=pct_safe(int(l_conv_ctx or 0),int(l_tot_ctx or 1))

    st.markdown(kpi_grid([
        ("Faturamento",fmt(rb_ctx),f"{pct_safe(rb_ctx,meta_ctx):.0f}% da meta",GREEN if pct_safe(rb_ctx,meta_ctx)>=80 else AMBER),
        ("Meta",fmt(meta_ctx),"mensal",AMBER),
        ("Conv. Leads",f"{tx_conv_ctx:.1f}%",f"{int(l_conv_ctx or 0)} de {l_tot_ctx}",GREEN if tx_conv_ctx>=30 else RED),
        ("Período",f"{mes_sel}/{ano_sel}","dados atuais",GRAY),
    ]),unsafe_allow_html=True)

    if "chat_history" not in st.session_state: st.session_state.chat_history=[]

    sugestoes=["Qual meu principal gargalo agora?","Como fechar a meta do mês?","Analise meu EBITDA e dê 3 ações.","Como precificar um novo protocolo?","Qual motor de crescimento priorizar?","Como reduzir meu custo fixo sem demitir?","Como aumentar ticket médio sem perder pacientes?","Qual o plano para dobrar faturamento em 6 meses?"]
    sc=st.columns(4)
    for i,sug in enumerate(sugestoes):
        with sc[i%4]:
            if st.button(sug,key=f"sug_{i}",use_container_width=True):
                st.session_state.chat_history.append({"role":"user","content":sug}); st.rerun()

    st.markdown("---")
    for msg in st.session_state.chat_history:
        if msg["role"]=="user":
            st.markdown(f'<div style="display:flex;justify-content:flex-end;margin-bottom:10px"><div style="background:{BG2};border:1px solid {BORDER};border-radius:16px 16px 2px 16px;padding:12px 16px;max-width:75%"><div style="color:{WHITE};font-size:13px;line-height:1.6">{msg["content"]}</div></div></div>',unsafe_allow_html=True)
        else:
            st.markdown(f'<div style="display:flex;gap:10px;margin-bottom:14px"><div style="width:32px;height:32px;background:{AMBER};border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0">🩺</div><div style="background:{BG3};border:1px solid {BORDER};border-radius:2px 16px 16px 16px;padding:14px 18px;max-width:80%"><div style="color:{AMBER};font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">LAB METRICS</div><div style="color:{WHITE};font-size:13px;line-height:1.8;white-space:pre-wrap">{msg["content"]}</div></div></div>',unsafe_allow_html=True)

    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"]=="user":
        if not api_key: st.error("Configure ANTHROPIC_API_KEY nos Secrets do Streamlit.")
        else:
            with st.spinner("LAB Metrics analisando..."):
                try:
                    client=anthropic.Anthropic(api_key=api_key)
                    ctx=f"\nDados {mes_sel}/{ano_sel}: Faturamento R$ {rb_ctx:,.2f} | Meta R$ {meta_ctx:,.2f} | Atingimento {pct_safe(rb_ctx,meta_ctx):.1f}% | Leads {l_tot_ctx} | Convertidos {int(l_conv_ctx or 0)} | Taxa {tx_conv_ctx:.1f}%"
                    msgs_api=[]
                    for msg in st.session_state.chat_history:
                        if msg["role"]=="user" and msg==st.session_state.chat_history[-1]:
                            msgs_api.append({"role":"user","content":f"{ctx}\n\nPergunta: {msg['content']}"})
                        else: msgs_api.append(msg)
                    resp=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=1000,system=SYSTEM_PROMPT_ASSISTENTE,messages=msgs_api)
                    st.session_state.chat_history.append({"role":"assistant","content":resp.content[0].text}); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")

    ci,cb,cc=st.columns([6,1,1])
    with ci: perg=st.text_input("Assistente",placeholder="Digite sua pergunta estratégica...",label_visibility="collapsed",key="inp_chat")
    with cb:
        if st.button("→",use_container_width=True,key="btn_chat") and perg.strip():
            st.session_state.chat_history.append({"role":"user","content":perg.strip()}); st.rerun()
    with cc:
        if st.button("✕",use_container_width=True,key="btn_clear"): st.session_state.chat_history=[]; st.rerun()

    if not st.session_state.chat_history:
        st.markdown(f"""<div style="background:{BG3};border:1px solid {BORDER};border-radius:16px;padding:32px;text-align:center;margin-top:20px">
            <div style="font-size:2rem;margin-bottom:12px">🩺</div>
            <div style="font-size:1.1rem;font-weight:700;color:{WHITE};letter-spacing:-0.02em;margin-bottom:8px">LAB Metrics — Consultor Executivo Digital</div>
            <div style="font-size:12px;color:{GRAY};line-height:1.8;max-width:480px;margin:0 auto">Pergunte sobre precificação, crescimento, custos, equipe ou estratégia. Cada resposta termina em ação com DRI e prazo.</div>
            <div style="font-size:11px;color:{GRAY2};margin-top:16px;font-style:italic">"Nenhuma análise sem ação. Nenhuma ação sem responsável."</div>
        </div>""",unsafe_allow_html=True)

elif aba == "⚙️  Configurações":
    st.markdown(titulo_secao("Configurações","Clínica, equipe e integrações","⚙️"),unsafe_allow_html=True)
    tab1,tab2,tab3=st.tabs(["CLÍNICA & METAS","COLABORADORES","API KEY"])
    with tab1:
        conn=get_conn(); cr=conn.execute("SELECT * FROM clinica WHERE id=1").fetchone(); conn.close()
        with st.form("form_cl"):
            c1,c2=st.columns(2)
            with c1: nm_c=st.text_input("Nome da clínica",value=cr[1] if cr else ""); meta_c=st.number_input("Meta mensal R$",value=float(cr[2] if cr else 280000),step=1000.0)
            with c2: cf_c=st.number_input("Custo fixo total R$",value=float(cr[3] if cr else 81000),step=1000.0); est_c=st.selectbox("Estágio",["Caótico","Intuitivo","Documentado","Previsível"],index=["Caótico","Intuitivo","Documentado","Previsível"].index(cr[4] if cr and len(cr)>4 else "Previsível"))
            if st.form_submit_button("Salvar",use_container_width=True):
                conn=get_conn(); conn.execute("UPDATE clinica SET nome=?,meta_mensal=?,custo_fixo_total=?,estagio=? WHERE id=1",(nm_c,meta_c,cf_c,est_c)); conn.commit();conn.close();st.success("Salvo!");st.rerun()
    with tab2:
        conn=get_conn(); cdf=read_df("SELECT * FROM colaboradores WHERE ativo=1",conn); conn.close()
        if not cdf.empty: st.dataframe(cdf[['nome','funcao','cargo_key','nivel_acesso','zona_genialidade']],hide_index=True,use_container_width=True)
        with st.expander("➕ Adicionar Colaborador"):
            with st.form("form_col"):
                c1,c2,c3=st.columns(3)
                with c1: nm_cb=st.text_input("Nome")
                with c2: fc_cb=st.text_input("Função"); ck_cb=st.text_input("Cargo Key")
                with c3: na_cb=st.selectbox("Nível",["CEO / Proprietário","Gerente Executiva","Operacional"]); zg_cb=st.text_input("Zona de genialidade")
                if st.form_submit_button("Adicionar",use_container_width=True):
                    if nm_cb:
                        conn=get_conn(); conn.execute("INSERT INTO colaboradores(nome,funcao,cargo_key,nivel_acesso,zona_genialidade) VALUES(?,?,?,?,?)",(nm_cb,fc_cb,ck_cb,na_cb,zg_cb)); conn.commit();conn.close();st.rerun()
    with tab3:
        st.markdown(f"""**Streamlit Cloud → seu app → ⋮ → Settings → Secrets:**
```toml
ANTHROPIC_API_KEY = "sk-ant-..."
DATABASE_URL      = "postgresql://..."
```
→ https://console.anthropic.com/keys
→ https://supabase.com (banco persistente)""")
        kt=st.text_input("Testar API Key",type="password")
        if st.button("Testar",use_container_width=True) and kt:
            try:
                client=anthropic.Anthropic(api_key=kt); client.messages.create(model="claude-sonnet-4-20250514",max_tokens=5,messages=[{"role":"user","content":"ok"}]); st.success("API Key válida!")
            except Exception as e: st.error(f"Inválida: {e}")
