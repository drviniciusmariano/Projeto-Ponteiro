import streamlit as st
import pandas as pd
import sqlite3, os, json, io, hashlib, base64
from datetime import datetime, date, timedelta
try:
    from whatsapp_module import render_whatsapp_module
    HAS_WH = True
except ImportError:
    HAS_WH = False
import anthropic
try:
    from fpdf import FPDF
    HAS_PDF = True
except ImportError:
    HAS_PDF = False

st.set_page_config(
    page_title="LAB Metrics — Integrative Campinas",
    page_icon="🩺", layout="wide",
    initial_sidebar_state="collapsed"
)

# ══════════════════════════════════════════════════════════════
# DESIGN SYSTEM — BAUHAUS
# ══════════════════════════════════════════════════════════════
BG    = "#F0F0F0"   # off-white canvas
FG    = "#121212"   # stark black
RED_B = "#D02020"   # Bauhaus red
BLUE_B= "#1040C0"   # Bauhaus blue
YELL_B= "#F0C020"   # Bauhaus yellow
MUTED = "#E0E0E0"
WHITE = "#FFFFFF"
BLACK = "#121212"

# aliases funcionais (mantidos para compatibilidade com código das abas)
GREEN      = "#2A8A2A"    # verde funcional (semáforo)
RED_SOFT   = RED_B
YELL_SOFT  = YELL_B
ACCENT     = BLUE_B
ACCENT_BR  = "#1A50D0"
BG_BASE    = BG
BG_DEEP    = WHITE
BG_ELEV    = WHITE
SURF       = WHITE
SURF_HOV   = MUTED
BORDER     = BLACK
BORDER_HOV = BLACK
BORDER_ACC = RED_B
GOLD       = YELL_B
NAVY       = BLACK
CARD       = WHITE
MID        = MUTED
IVORY      = FG
GOLD_STR   = YELL_B
FG_MUTED   = "#444444"

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;700;900&display=swap');

*, *::before, *::after { box-sizing: border-box; }

html, body, [class*="css"] {
    font-family: 'Outfit', 'Arial Black', sans-serif !important;
    background-color: #F0F0F0 !important;
}

/* Canvas principal */
.main {
    background-color: #F0F0F0 !important;
    min-height: 100vh;
}

.block-container {
    padding: 2rem 2.5rem 4rem !important;
    max-width: 1400px;
}

/* Sidebar Bauhaus — coluna preta lateral */
div[data-testid="stSidebarContent"] {
    background-color: #121212 !important;
    border-right: 4px solid #121212 !important;
}

/* Radio da sidebar — links de navegação */
div[data-testid="stSidebarContent"] .stRadio > div {
    gap: 2px !important;
}
div[data-testid="stSidebarContent"] .stRadio > div > label {
    color: #E0E0E0 !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.78rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    padding: 10px 14px !important;
    border-radius: 0 !important;
    border-left: 4px solid transparent !important;
    transition: all 0.15s ease-out !important;
    cursor: pointer;
    display: block;
}
div[data-testid="stSidebarContent"] .stRadio > div > label:hover {
    background-color: #1F1F1F !important;
    border-left-color: #F0C020 !important;
    color: #F0C020 !important;
}
div[data-testid="stSidebarContent"] .stRadio [data-baseweb="radio"]:has(input:checked) + div {
    color: #F0C020 !important;
}
/* Selectbox e inputs na sidebar */
div[data-testid="stSidebarContent"] .stSelectbox > div > div,
div[data-testid="stSidebarContent"] .stNumberInput > div > div > input {
    background: #1F1F1F !important;
    border: 2px solid #444 !important;
    color: #F0F0F0 !important;
    border-radius: 0 !important;
}
div[data-testid="stSidebarContent"] p,
div[data-testid="stSidebarContent"] label,
div[data-testid="stSidebarContent"] div {
    color: #E0E0E0 !important;
}

/* Headings */
h1, h2, h3 {
    font-family: 'Outfit', sans-serif !important;
    font-weight: 900 !important;
    text-transform: uppercase !important;
    letter-spacing: -0.02em !important;
    color: #121212 !important;
}

/* Métricas nativas Streamlit */
div[data-testid="metric-container"] {
    background: #FFFFFF !important;
    border: 4px solid #121212 !important;
    border-radius: 0 !important;
    padding: 20px 22px !important;
    box-shadow: 6px 6px 0px 0px #121212 !important;
    transition: transform 0.15s ease-out, box-shadow 0.15s ease-out !important;
}
div[data-testid="metric-container"]:hover {
    transform: translateY(-3px) !important;
    box-shadow: 8px 8px 0px 0px #121212 !important;
}
div[data-testid="stMetricValue"] {
    font-size: 1.8rem !important;
    font-weight: 900 !important;
    color: #121212 !important;
    font-family: 'Outfit', sans-serif !important;
    letter-spacing: -0.02em !important;
}
div[data-testid="stMetricLabel"] {
    font-size: 0.65rem !important;
    color: #444 !important;
    text-transform: uppercase !important;
    letter-spacing: 0.15em !important;
    font-weight: 700 !important;
    font-family: 'Outfit', sans-serif !important;
}

/* Botões — estilo Bauhaus com press effect */
.stButton > button {
    background-color: #1040C0 !important;
    color: #FFFFFF !important;
    border: 3px solid #121212 !important;
    border-radius: 0 !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.8rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.1em !important;
    padding: 10px 22px !important;
    box-shadow: 4px 4px 0px 0px #121212 !important;
    transition: all 0.15s ease-out !important;
}
.stButton > button:hover {
    background-color: #0A30A0 !important;
    transform: translateY(-2px) !important;
    box-shadow: 6px 6px 0px 0px #121212 !important;
}
.stButton > button:active {
    transform: translate(3px, 3px) !important;
    box-shadow: 1px 1px 0px 0px #121212 !important;
}

/* Tabs */
.stTabs [data-baseweb="tab-list"] {
    background: #121212 !important;
    border: 3px solid #121212 !important;
    border-radius: 0 !important;
    padding: 4px !important;
    gap: 3px !important;
}
.stTabs [data-baseweb="tab"] {
    border-radius: 0 !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.72rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.08em !important;
    color: #E0E0E0 !important;
    padding: 8px 16px !important;
    border: none !important;
    transition: all 0.15s ease-out !important;
}
.stTabs [data-baseweb="tab"]:hover {
    background-color: #F0C020 !important;
    color: #121212 !important;
}
.stTabs [aria-selected="true"] {
    background-color: #F0C020 !important;
    color: #121212 !important;
}

/* Inputs */
.stTextInput > div > div > input,
.stNumberInput > div > div > input,
.stTextArea textarea {
    background: #FFFFFF !important;
    border: 3px solid #121212 !important;
    border-radius: 0 !important;
    color: #121212 !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.9rem !important;
    transition: border-color 0.15s, box-shadow 0.15s !important;
}
.stTextInput > div > div > input:focus,
.stNumberInput > div > div > input:focus,
.stTextArea textarea:focus {
    border-color: #1040C0 !important;
    box-shadow: 3px 3px 0px 0px #1040C0 !important;
    outline: none !important;
}

/* Selectbox */
.stSelectbox > div > div {
    background: #FFFFFF !important;
    border: 3px solid #121212 !important;
    border-radius: 0 !important;
    color: #121212 !important;
    font-family: 'Outfit', sans-serif !important;
}

/* Checkbox */
.stCheckbox > label {
    color: #121212 !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
    font-size: 0.875rem !important;
}

/* Radio (no main content) */
.stRadio > div > label {
    color: #121212 !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 500 !important;
}

/* Expander */
.stExpander {
    background: #FFFFFF !important;
    border: 3px solid #121212 !important;
    border-radius: 0 !important;
    box-shadow: 4px 4px 0px 0px #121212 !important;
    overflow: hidden !important;
}
.stExpander summary {
    color: #121212 !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
    font-size: 0.875rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.05em !important;
    padding: 14px 18px !important;
    background: #FFFFFF !important;
}
.stExpander summary:hover {
    background: #F0C020 !important;
}

/* Progress bar */
.stProgress > div > div > div > div {
    background: #1040C0 !important;
    border-radius: 0 !important;
}
.stProgress > div > div {
    background: #E0E0E0 !important;
    border-radius: 0 !important;
    border: 2px solid #121212 !important;
}

/* DataFrame */
.stDataFrame {
    border: 3px solid #121212 !important;
    border-radius: 0 !important;
    box-shadow: 4px 4px 0px 0px #121212 !important;
    overflow: hidden !important;
}
.stDataFrame th {
    background: #121212 !important;
    color: #F0C020 !important;
    font-size: 0.65rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 700 !important;
}
.stDataFrame td {
    color: #121212 !important;
    font-size: 0.85rem !important;
    background: #FFFFFF !important;
    border-bottom: 2px solid #E0E0E0 !important;
    font-family: 'Outfit', sans-serif !important;
}

/* Alertas Bauhaus */
.stSuccess {
    background: #2A8A2A !important;
    color: white !important;
    border: 3px solid #121212 !important;
    border-radius: 0 !important;
    box-shadow: 3px 3px 0px 0px #121212 !important;
}
.stWarning {
    background: #F0C020 !important;
    color: #121212 !important;
    border: 3px solid #121212 !important;
    border-radius: 0 !important;
    box-shadow: 3px 3px 0px 0px #121212 !important;
}
.stError {
    background: #D02020 !important;
    color: white !important;
    border: 3px solid #121212 !important;
    border-radius: 0 !important;
    box-shadow: 3px 3px 0px 0px #121212 !important;
}
.stInfo {
    background: #1040C0 !important;
    color: white !important;
    border: 3px solid #121212 !important;
    border-radius: 0 !important;
    box-shadow: 3px 3px 0px 0px #121212 !important;
}

/* Scrollbar Bauhaus */
::-webkit-scrollbar { width: 6px; height: 6px; }
::-webkit-scrollbar-track { background: #E0E0E0; }
::-webkit-scrollbar-thumb { background: #121212; border-radius: 0; }

/* Markdown paragraphs */
.stMarkdown p {
    color: #444444;
    line-height: 1.65;
    font-size: 0.9rem;
    font-family: 'Outfit', sans-serif;
    font-weight: 500;
}

/* Separator */
hr { border: none; border-top: 3px solid #121212; margin: 24px 0; }

/* Form submit button especial */
.stFormSubmitButton > button {
    background-color: #D02020 !important;
    color: #FFFFFF !important;
    border: 3px solid #121212 !important;
    border-radius: 0 !important;
    font-family: 'Outfit', sans-serif !important;
    font-weight: 900 !important;
    font-size: 0.85rem !important;
    text-transform: uppercase !important;
    letter-spacing: 0.12em !important;
    padding: 12px 28px !important;
    box-shadow: 5px 5px 0px 0px #121212 !important;
    transition: all 0.15s ease-out !important;
    width: 100% !important;
}
.stFormSubmitButton > button:hover {
    background-color: #B01A1A !important;
    transform: translateY(-2px) !important;
    box-shadow: 7px 7px 0px 0px #121212 !important;
}
.stFormSubmitButton > button:active {
    transform: translate(4px, 4px) !important;
    box-shadow: 1px 1px 0px 0px #121212 !important;
}
</style>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# BANCO DE DADOS — schema completo
# ══════════════════════════════════════════════════════════════
DB="lab_metrics.db"
def get_conn(): return sqlite3.connect(DB,check_same_thread=False)

def init_db():
    conn=get_conn()
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS clinica(id INTEGER PRIMARY KEY DEFAULT 1,nome TEXT DEFAULT 'Integrative Campinas',meta_mensal REAL DEFAULT 0,custo_fixo_total REAL DEFAULT 0,estagio TEXT DEFAULT 'Intuitivo',modelo_tributario TEXT DEFAULT 'Simples Nacional');
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
    CREATE TABLE IF NOT EXISTS orcamentos(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente TEXT,valor REAL DEFAULT 0,data_envio TEXT,temperatura TEXT DEFAULT 'Morno',objecao TEXT DEFAULT '',proxima_acao TEXT DEFAULT '',dri TEXT DEFAULT 'Bianca',prazo TEXT DEFAULT '',status TEXT DEFAULT 'Aberto',criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS rfm(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente TEXT,ultima_visita TEXT,frequencia INTEGER DEFAULT 0,valor_total REAL DEFAULT 0,segmento TEXT DEFAULT 'Inativo recente',status_contato TEXT DEFAULT 'Nao contatado',proxima_acao TEXT DEFAULT '',dri TEXT DEFAULT 'Beatriz',resultado TEXT DEFAULT '',criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS indicacoes(id INTEGER PRIMARY KEY AUTOINCREMENT,pac_indicador TEXT,pac_indicado TEXT,contato TEXT DEFAULT '',data_ind TEXT,status TEXT DEFAULT 'Novo',dri TEXT DEFAULT 'Aline',convertido INTEGER DEFAULT 0,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
    CREATE TABLE IF NOT EXISTS sbar(id INTEGER PRIMARY KEY AUTOINCREMENT,tipo TEXT,remetente TEXT,destinatario TEXT,situacao TEXT,background TEXT,avaliacao TEXT,recomendacao TEXT,dri_acao TEXT,prazo TEXT,data TEXT DEFAULT CURRENT_TIMESTAMP,resolvido INTEGER DEFAULT 0);
    CREATE TABLE IF NOT EXISTS seguranca(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente TEXT,data_atend TEXT,responsavel TEXT DEFAULT 'Paloma',ch1 INTEGER DEFAULT 0,ch2 INTEGER DEFAULT 0,ch3 INTEGER DEFAULT 0,ch4 INTEGER DEFAULT 0,ch5 INTEGER DEFAULT 0,ch6 INTEGER DEFAULT 0,ch7 INTEGER DEFAULT 0,intercorrencia INTEGER DEFAULT 0,desc_inter TEXT DEFAULT '',d1_enviado INTEGER DEFAULT 0,d1_resposta TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS regua(id INTEGER PRIMARY KEY AUTOINCREMENT,paciente TEXT,tipo TEXT DEFAULT 'Primeira Consulta',data_cons TEXT,st_dm1 TEXT DEFAULT 'Pendente',st_dp1 TEXT DEFAULT 'Pendente',st_dp3 TEXT DEFAULT 'Pendente',st_dp7 TEXT DEFAULT 'Pendente',st_dp14 TEXT DEFAULT 'Pendente',ticket REAL DEFAULT 0.0,fechou INTEGER DEFAULT 0,obs TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS briefing(id INTEGER PRIMARY KEY AUTOINCREMENT,data TEXT UNIQUE,responsavel TEXT DEFAULT '',cons_ag INTEGER DEFAULT 0,proc_ag INTEGER DEFAULT 0,conf INTEGER DEFAULT 0,gaps INTEGER DEFAULT 0,val_ag REAL DEFAULT 0,leads_pend INTEGER DEFAULT 0,orc_ab INTEGER DEFAULT 0,val_orc REAL DEFAULT 0,rfm_meta INTEGER DEFAULT 30,ind_meta INTEGER DEFAULT 5,ret_hoje INTEGER DEFAULT 0,cob_12h TEXT DEFAULT 'Beatriz',cob_13h TEXT DEFAULT 'Aline',dm1_pc INTEGER DEFAULT 0,dm1_ret INTEGER DEFAULT 0,dp1_pc INTEGER DEFAULT 0,dp1_ret INTEGER DEFAULT 0,fw3 INTEGER DEFAULT 0,fw7 INTEGER DEFAULT 0,fw14 INTEGER DEFAULT 0,pr1 TEXT DEFAULT '',pr2 TEXT DEFAULT '',pr3 TEXT DEFAULT '',dr1 TEXT DEFAULT '',dr2 TEXT DEFAULT '',dr3 TEXT DEFAULT '',obs TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS debriefing(id INTEGER PRIMARY KEY AUTOINCREMENT,data TEXT UNIQUE,responsavel TEXT DEFAULT '',rc REAL DEFAULT 0,rp REAL DEFAULT 0,rr REAL DEFAULT 0,ro REAL DEFAULT 0,di REAL DEFAULT 0,do_ REAL DEFAULT 0,da REAL DEFAULT 0,cons_r INTEGER DEFAULT 0,proc_r INTEGER DEFAULT 0,ns INTEGER DEFAULT 0,canc INTEGER DEFAULT 0,perda_ns REAL DEFAULT 0,leads_r INTEGER DEFAULT 0,tempo_r INTEGER DEFAULT 0,ag_g INTEGER DEFAULT 0,orc_f INTEGER DEFAULT 0,val_of REAL DEFAULT 0,rfm_r INTEGER DEFAULT 0,ind_s INTEGER DEFAULT 0,ind_r INTEGER DEFAULT 0,av_g INTEGER DEFAULT 0,dm1_ex INTEGER DEFAULT 0,dp1_ex INTEGER DEFAULT 0,fw_ex INTEGER DEFAULT 0,meta_bat INTEGER DEFAULT 0,conquista TEXT DEFAULT '',gargalo TEXT DEFAULT '',acao_am TEXT DEFAULT '',dri_am TEXT DEFAULT '',obs TEXT DEFAULT '');
    CREATE TABLE IF NOT EXISTS okrs(id INTEGER PRIMARY KEY AUTOINCREMENT,objetivo TEXT,key_result TEXT,meta_val REAL DEFAULT 0,atual_val REAL DEFAULT 0,responsavel TEXT,trimestre TEXT,ano INTEGER,ativo INTEGER DEFAULT 1);
    CREATE TABLE IF NOT EXISTS relatorios(id INTEGER PRIMARY KEY AUTOINCREMENT,nome_arquivo TEXT,conteudo TEXT,analise_ia TEXT,mes TEXT,ano INTEGER,criado_em TEXT DEFAULT CURRENT_TIMESTAMP);
    """)
    conn.commit()
    if conn.execute("SELECT COUNT(*) FROM colaboradores").fetchone()[0]==0:
        for n,f,k,na,zg in [("Dr. Vinícius Mariano","CEO","ceo","CEO / Proprietário","Estratégia e decisão"),("Dra. Bárbara Mariano","Diretora Técnica","barbara","CEO / Proprietário","Protocolos e qualidade"),("Vanessa","Gerente Executiva","gerente","Gerente Executiva","Execução e indicadores"),("Bianca","Coord. Comercial e Closer","bianca","Gerente Executiva","Fechamento e conversão"),("Aline","Analista de Leads","aline","Operacional","Qualificação e follow-up"),("Beatriz","Recepção Comercial + RFM","beatriz","Operacional","Acolhimento e relacionamento"),("Paloma","Enfermeira Assistencial","paloma","Operacional","Cuidado técnico e segurança")]:
            conn.execute("INSERT INTO colaboradores(nome,funcao,cargo_key,nivel_acesso,zona_genialidade) VALUES(?,?,?,?,?)",(n,f,k,na,zg))
    if conn.execute("SELECT COUNT(*) FROM mod_tarefas").fetchone()[0]==0:
        for t,ck,resp,dri,bloco,hr,cat,peso in [
            ("Abrir caixa e conferir saldo","gerente","Gerente","Caixa aberto","Abertura","08:30","Financeiro",10),
            ("Levantar leads recebidos desde ontem no CRM","gerente","Gerente","Lista atualizada","Abertura","08:30","Comercial",15),
            ("Verificar agenda 7 dias e mapear gaps","gerente","Gerente","Gaps comunicados","Abertura","08:30","Operacional",15),
            ("Confirmar 100% dos agendamentos de hoje","gerente","Gerente","100% confirmados","Abertura","08:30","Operacional",10),
            ("Definir 3 prioridades do dia com DRI e prazo","gerente","Gerente","Painel AME atualizado","Abertura","08:30","Liderança",15),
            ("Registrar meta do dia e gap em relação à meta mensal","gerente","Gerente","Gap registrado","Abertura","08:30","Comercial",10),
            ("Definir escala de cobertura do almoço e comunicar","gerente","Gerente","Escala comunicada","Abertura","08:30","Operacional",5),
            ("Conduzir checkpoint com a equipe (máx 15 min)","gerente","Gerente","Pauta registrada","Durante","09:00","Liderança",15),
            ("Acompanhar indicadores: leads, orçamentos, agenda","gerente","Gerente","Painel atualizado","Durante","14:00","Comercial",10),
            ("Revisar orçamentos quentes com Bianca","gerente","Gerente","Status registrado","Durante","14:00","Comercial",10),
            ("Conferir caixa do dia","gerente","Gerente","Caixa fechado","Fechamento","17:30","Financeiro",10),
            ("Registrar pendências para amanhã no painel AME","gerente","Gerente","AME atualizado","Fechamento","17:30","Operacional",10),
            ("Enviar resumo SBAR ao Dr. Vinícius","gerente","Gerente","SBAR enviado","Fechamento","17:30","Liderança",20),
            ("Ligar computadores e ar-condicionado","beatriz","Beatriz","Ambiente pronto","Abertura","07:45","Operacional",5),
            ("Verificar agenda e confirmar agendamentos","beatriz","Beatriz","100% confirmados","Abertura","07:45","Operacional",15),
            ("Responder WhatsApp pendente da noite","beatriz","Beatriz","Zero pendentes","Abertura","07:45","Comercial",10),
            ("Enviar lembretes para pacientes de amanhã","beatriz","Beatriz","Lembretes enviados","Abertura","07:45","Comercial",10),
            ("Receber paciente de pé, pelo nome e contato visual","beatriz","Beatriz","Padrão 100%","Durante","09:00","Operacional",10),
            ("Garantir que todo paciente saia com próxima etapa agendada","beatriz","Beatriz","100% agendados","Durante","09:00","Comercial",20),
            ("Enviar vídeo de boas-vindas para novos pacientes","beatriz","Beatriz","Vídeo enviado no dia","Durante","09:00","Comercial",10),
            ("Registrar indicações recebidas imediatamente","beatriz","Beatriz","Planilha atualizada","Durante","09:00","Comercial",10),
            ("Fechar caixa com registro correto","beatriz","Beatriz","Caixa fechado","Fechamento","17:45","Financeiro",10),
            ("Confirmar todos os agendamentos de amanhã","beatriz","Beatriz","100% confirmados","Fechamento","17:45","Operacional",10),
            ("Abrir CRM e identificar leads novos desde ontem","aline","Aline","Lista levantada","Abertura","08:00","Comercial",15),
            ("Responder 100% dos leads novos em até 5 minutos","aline","Aline","Zero sem resposta","Abertura","08:00","Comercial",35),
            ("Qualificar leads pela dor, nunca pelo preço","aline","Aline","Status no CRM","Abertura","08:00","Comercial",20),
            ("Executar follow-up da cadência D+1/D+3/D+7/D+9/D+30","aline","Aline","Zero fora da cadência","Durante","09:00","Comercial",35),
            ("Sinalizar leads quentes para Bianca fechar no mesmo dia","aline","Aline","Bianca notificada","Durante","09:00","Comercial",15),
            ("Zero leads sem follow-up dentro da cadência","aline","Aline","CRM 100% atualizado","Fechamento","17:30","Comercial",35),
            ("Ligar computador e ar-condicionado sala técnica","paloma","Paloma","Ambiente preparado","Abertura","07:30","Operacional",5),
            ("Verificar temperatura da geladeira (2 a 8 graus)","paloma","Paloma","Temperatura registrada","Abertura","07:30","Operacional",20),
            ("Conferir injetáveis e materiais antes de cada paciente","paloma","Paloma","Checklist preenchido","Durante","09:00","Operacional",15),
            ("Conferir nome, LOTE e VALIDADE NA FRENTE do paciente","paloma","Paloma","Conferência registrada","Durante","09:00","Operacional",20),
            ("Fazer evolução técnica no mesmo dia","paloma","Paloma","Evolução registrada","Durante","09:00","Operacional",15),
            ("Sinalizar para Beatriz agendar próxima sessão","paloma","Paloma","Próxima sessão agendada","Durante","09:00","Operacional",15),
            ("Enviar D+1 para todos pacientes atendidos ontem","paloma","Paloma","100% enviados até 10h","Abertura","08:00","Operacional",20),
        ]:
            conn.execute("INSERT INTO mod_tarefas(titulo,cargo_key,responsavel,dri,bloco,horario,frequencia,categoria,peso) VALUES(?,?,?,?,?,?,?,?,?)",(t,ck,resp,dri,bloco,hr,"Diaria",cat,peso))
    conn.commit(); conn.close()

init_db()

# ══════════════════════════════════════════════════════════════
# AUTENTICAÇÃO — tabela de usuários
# ══════════════════════════════════════════════════════════════
def hash_pw(pw): return hashlib.sha256(pw.encode()).hexdigest()

def init_users(conn):
    conn.executescript("""
    CREATE TABLE IF NOT EXISTS usuarios(
        id              INTEGER PRIMARY KEY AUTOINCREMENT,
        nome            TEXT NOT NULL,
        login           TEXT UNIQUE NOT NULL,
        senha_hash      TEXT NOT NULL,
        nivel           TEXT DEFAULT 'Operacional',
        cargo_key       TEXT DEFAULT '',
        ativo           INTEGER DEFAULT 1,
        primeiro_acesso INTEGER DEFAULT 1,
        ultimo_acesso   TEXT DEFAULT ''
    );
    """)
    # Migração: adicionar coluna se não existir (banco antigo)
    try:
        conn.execute("ALTER TABLE usuarios ADD COLUMN primeiro_acesso INTEGER DEFAULT 1")
        conn.commit()
    except Exception:
        pass
    conn.commit()
    if conn.execute("SELECT COUNT(*) FROM usuarios").fetchone()[0] == 0:
        for nome,login,pw,nivel,ck in [
            ("Dr. Vinícius Mariano","vinicius","integrative2026","CEO","ceo"),
            ("Dra. Bárbara Mariano","barbara","barbara2026","CEO","barbara"),
            ("Vanessa","gerente","gerente2026","Gerente","gerente"),
            ("Bianca","bianca","bianca2026","Operacional","bianca"),
            ("Aline","aline","aline2026","Operacional","aline"),
            ("Beatriz","beatriz","beatriz2026","Operacional","beatriz"),
            ("Paloma","paloma","paloma2026","Operacional","paloma"),
        ]:
            conn.execute(
                "INSERT INTO usuarios(nome,login,senha_hash,nivel,cargo_key,primeiro_acesso) VALUES(?,?,?,?,?,1)",
                (nome,login,hash_pw(pw),nivel,ck))
        conn.commit()

def autenticar(login, pw):
    conn = get_conn()
    init_users(conn)
    r = conn.execute(
        "SELECT id,nome,nivel,cargo_key,primeiro_acesso FROM usuarios WHERE login=? AND senha_hash=? AND ativo=1",
        (login.strip().lower(), hash_pw(pw))).fetchone()
    if r:
        conn.execute("UPDATE usuarios SET ultimo_acesso=? WHERE id=?",
            (datetime.now().isoformat(), r[0]))
        conn.commit()
    conn.close()
    return r  # (id, nome, nivel, cargo_key, primeiro_acesso) ou None

def trocar_senha(user_id, nova_senha):
    conn = get_conn()
    conn.execute(
        "UPDATE usuarios SET senha_hash=?, primeiro_acesso=0 WHERE id=?",
        (hash_pw(nova_senha), user_id))
    conn.commit()
    conn.close()

# ══════════════════════════════════════════════════════════════
# TELA DE TROCA DE SENHA — exibida obrigatoriamente no 1º acesso
# ══════════════════════════════════════════════════════════════
def tela_trocar_senha():
    st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;700;900&display=swap');
    html,body,[class*="css"]{font-family:'Outfit',sans-serif!important;background:#F0F0F0!important;}
    .main{background:#F0F0F0!important;}
    .block-container{padding:0!important;max-width:100%!important;}
    section[data-testid="stSidebar"]{display:none!important;width:0!important;}
    header{display:none!important;}
    .stTextInput>div>div>input{background:#FFFFFF!important;border:3px solid #121212!important;
        border-radius:0!important;color:#121212!important;font-family:'Outfit',sans-serif!important;
        font-size:1rem!important;padding:14px 16px!important;}
    .stTextInput>div>div>input:focus{border-color:#1040C0!important;
        box-shadow:4px 4px 0 #1040C0!important;outline:none!important;}
    .stButton>button{background:#D02020!important;color:#FFFFFF!important;border:3px solid #121212!important;
        border-radius:0!important;font-family:'Outfit',sans-serif!important;font-weight:900!important;
        font-size:1rem!important;text-transform:uppercase!important;letter-spacing:0.12em!important;
        padding:14px 28px!important;box-shadow:5px 5px 0 #121212!important;width:100%!important;
        transition:all 0.15s ease-out!important;}
    .stButton>button:hover{transform:translateY(-2px)!important;box-shadow:7px 7px 0 #121212!important;}
    </style>""", unsafe_allow_html=True)

    col_l, col_r = st.columns([1, 1])

    with col_l:
        _hts = (
            '<div style="background:#D02020;min-height:100vh;padding:60px 50px;'
            'display:flex;flex-direction:column;justify-content:center;'
            'border-right:4px solid #121212">'
            '<div style="font-size:2.8rem;font-weight:900;color:#FFFFFF;'
            'text-transform:uppercase;letter-spacing:-0.03em;line-height:1;'
            'font-family:Outfit,sans-serif;margin-bottom:20px">'
            'PRIMEIRO<br>ACESSO</div>'
            '<div style="height:4px;background:#F0C020;margin-bottom:28px"></div>'
            '<div style="font-size:1rem;color:rgba(255,255,255,0.8);'
            'font-weight:500;line-height:1.7">'
            'Por seguran\u00e7a, voc\u00ea precisa criar uma senha pessoal antes de continuar. '
            'Ela substitui a senha padr\u00e3o e fica registrada apenas para voc\u00ea.'
            '</div>'
            '<div style="margin-top:40px;padding:18px;'
            'background:rgba(255,255,255,0.1);border-left:4px solid #F0C020">'
            '<div style="font-size:9px;color:rgba(255,255,255,0.6);'
            'text-transform:uppercase;letter-spacing:0.15em;'
            'font-weight:700;margin-bottom:8px">Regras da senha</div>'
            '<div style="font-size:12px;color:rgba(255,255,255,0.8);line-height:2">'
            '\u2713 M\u00ednimo 6 caracteres<br>'
            '\u2713 Diferente da senha padr\u00e3o<br>'
            '\u2713 Confirme duas vezes'
            '</div></div></div>'
        )
        st.markdown(_hts, unsafe_allow_html=True)

    with col_r:
        _nome_prim = st.session_state.get("user_nome","").split()[0]
        _hr2 = (
            '<div style="min-height:100vh;background:#F0F0F0;padding:60px 50px;'
            'display:flex;flex-direction:column;justify-content:center">'
            '<div style="max-width:380px;margin:0 auto;width:100%">'
            f'<div style="font-size:9px;color:#888;text-transform:uppercase;'
            f'letter-spacing:0.2em;font-weight:700;margin-bottom:8px">Bem-vindo(a), {_nome_prim}</div>'
            '<div style="font-size:2rem;font-weight:900;color:#121212;'
            'text-transform:uppercase;letter-spacing:-0.02em;'
            'line-height:1;margin-bottom:4px">CRIE SUA<br>SENHA</div>'
            '<div style="height:4px;background:#D02020;width:60px;margin:12px 0 32px"></div>'
        )
        st.markdown(_hr2, unsafe_allow_html=True)

        nova1 = st.text_input("NOVA SENHA", type="password",
            placeholder="mínimo 6 caracteres", key="nova_pw1")
        nova2 = st.text_input("CONFIRMAR SENHA", type="password",
            placeholder="repita a senha", key="nova_pw2")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

        if st.button("SALVAR E ENTRAR →", use_container_width=True, key="btn_trocar"):
            if not nova1 or not nova2:
                st.error("Preencha os dois campos.")
            elif len(nova1) < 6:
                st.error("A senha precisa ter no mínimo 6 caracteres.")
            elif nova1 != nova2:
                st.error("As senhas não coincidem.")
            elif nova1 in ("integrative2026","barbara2026","gerente2026",
                           "bianca2026","aline2026","beatriz2026","paloma2026"):
                st.error("Use uma senha diferente da senha padrão.")
            else:
                trocar_senha(st.session_state.user_id, nova1)
                st.session_state.primeiro_acesso = False
                st.success("Senha criada! Entrando no sistema...")
                st.rerun()

        st.markdown("</div></div>", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# HELPERS & COMPONENTES BAUHAUS
# ══════════════════════════════════════════════════════════════
MESES=["Jan","Fev","Mar","Abr","Mai","Jun","Jul","Ago","Set","Out","Nov","Dez"]
EQUIPE=["Vanessa","Bianca","Aline","Beatriz","Paloma","Dr. Vinícius Mariano","Dra. Bárbara Mariano"]
CARGO_MAP={"gerente":"Vanessa","bianca":"Bianca","aline":"Aline","beatriz":"Beatriz","paloma":"Paloma","ceo":"Dr. Vinícius Mariano","barbara":"Dra. Bárbara Mariano"}

def fmt(v):
    if v is None: return "R$ 0,00"
    return f"R$ {v:,.2f}".replace(",","X").replace(".",",").replace("X",".")

def pct_safe(a,b): return round((a/b)*100,1) if b else 0.0

def semaforo(p,limiar=85):
    if p>=100: return "🟢",GREEN
    if p>=limiar: return "🟡",YELL_B
    return "🔴",RED_B

# ── Componentes Bauhaus ────────────────────────────────────────

def card(titulo, valor, sub="", cor=BLUE_B, grande=False):
    """Card Bauhaus: fundo branco, borda grossa preta, shadow offset, décor geométrico."""
    fs = "2.2rem" if grande else "1.7rem"
    # Décor: quadrado colorido no canto superior direito
    decor_cor = cor
    return f"""<div style="background:#FFFFFF;border:4px solid #121212;border-radius:0;
        padding:20px 22px;margin-bottom:12px;
        box-shadow:6px 6px 0px 0px #121212;
        transition:transform 0.15s ease-out,box-shadow 0.15s ease-out;
        position:relative;overflow:hidden">
        <div style="position:absolute;top:0;right:0;width:12px;height:100%;background:{decor_cor};opacity:0.8"></div>
        <div style="font-size:9px;color:#444;text-transform:uppercase;letter-spacing:0.15em;
                    font-weight:700;margin-bottom:10px;font-family:'Outfit',sans-serif">{titulo}</div>
        <div style="font-size:{fs};font-weight:900;color:{cor};letter-spacing:-0.02em;
                    line-height:1;font-family:'Outfit',sans-serif">{valor}</div>
        {f'<div style="font-size:12px;color:#444;margin-top:8px;font-weight:500;font-family:Outfit,sans-serif">{sub}</div>' if sub else ''}
    </div>"""

def barra(p, label="", cor=None, bg=None):
    """Barra de progresso Bauhaus: retangular, borda preta, sem arredondamento."""
    c = cor or (RED_B if p<70 else YELL_B if p<100 else GREEN)
    txt_cor = "#121212" if c == YELL_B else "#FFFFFF"
    return f"""<div style="margin-bottom:14px">
        <div style="display:flex;justify-content:space-between;font-size:11px;
                    font-weight:700;color:#121212;margin-bottom:5px;
                    text-transform:uppercase;letter-spacing:0.08em;font-family:'Outfit',sans-serif">
            <span>{label}</span>
            <span style="color:{c}">{min(int(p),100)}%</span>
        </div>
        <div style="height:14px;background:#E0E0E0;border:2px solid #121212;
                    border-radius:0;overflow:hidden;position:relative">
            <div style="height:100%;width:{min(int(p),100)}%;background:{c};
                        border-radius:0;transition:width 0.4s ease-out;
                        border-right:{('2px solid #121212' if p<99 else 'none')}"></div>
        </div>
    </div>"""

def badge(texto, cor=BLUE_B):
    """Badge Bauhaus: retangular, uppercase, borda preta."""
    txt = "#121212" if cor == YELL_B else "#FFFFFF"
    return f'<span style="background:{cor};color:{txt};border:2px solid #121212;border-radius:0;padding:3px 10px;font-size:9px;font-weight:700;text-transform:uppercase;letter-spacing:0.12em;font-family:Outfit,sans-serif;box-shadow:2px 2px 0px 0px #121212">{texto}</span>'

def titulo_secao(t, sub=""):
    """Título Bauhaus: uppercase preto com linha horizontal e décor geométrico."""
    return f"""<div style="margin-bottom:{'8px' if sub else '24px'}">
        <div style="display:flex;align-items:center;gap:0;margin-bottom:0">
            <div style="width:8px;height:40px;background:{RED_B};margin-right:14px;flex-shrink:0"></div>
            <h2 style="margin:0;font-size:1.5rem;font-weight:900;color:#121212;
                       text-transform:uppercase;letter-spacing:-0.01em;
                       font-family:'Outfit',sans-serif;line-height:1">{t}</h2>
        </div>
        <div style="height:3px;background:#121212;margin:10px 0 {'6px' if sub else '0'}"></div>
        {f'<p style="margin:4px 0 16px 22px;font-size:12px;color:#444;font-weight:500;font-family:Outfit,sans-serif">{sub}</p>' if sub else '<div style="margin-bottom:18px"></div>'}
    </div>"""

def kpi_grid(items):
    """Grid de KPIs Bauhaus: cards brancos com bordas pretas, shadow offset."""
    n = len(items)
    cols_html = ""
    cores_decor = [RED_B, BLUE_B, YELL_B, RED_B, BLUE_B, YELL_B]
    for i,(lbl,val,sub,cor) in enumerate(items):
        dec = cores_decor[i % len(cores_decor)]
        txt_dec = "#121212" if dec == YELL_B else "#FFFFFF"
        cols_html += f"""<div style="background:#FFFFFF;border:4px solid #121212;
            border-radius:0;padding:18px 20px;
            box-shadow:5px 5px 0px 0px #121212;
            transition:transform 0.15s ease-out;
            position:relative;overflow:hidden">
            <div style="position:absolute;top:0;left:0;width:6px;height:100%;background:{dec}"></div>
            <div style="padding-left:10px">
                <div style="font-size:9px;color:#444;text-transform:uppercase;letter-spacing:0.15em;
                            font-weight:700;margin-bottom:10px;font-family:'Outfit',sans-serif">{lbl}</div>
                <div style="font-size:1.7rem;font-weight:900;color:{cor};letter-spacing:-0.02em;
                            line-height:1;font-family:'Outfit',sans-serif">{val}</div>
                {f'<div style="font-size:11px;color:#444;margin-top:6px;font-weight:500;font-family:Outfit,sans-serif">{sub}</div>' if sub else ''}
            </div>
        </div>"""
    return f'<div style="display:grid;grid-template-columns:repeat({n},1fr);gap:12px;margin-bottom:20px">{cols_html}</div>'

def dre_linha(label, valor, pct_val, cor, destaque=False):
    """Linha DRE Bauhaus: destaque com fundo colorido e borda grossa."""
    if destaque:
        bg = "#121212"; txt_cor = "#F0C020"; val_cor = "#F0C020"; fw = "900"; fs = "14px"; pad = "12px 16px"
        bd = f"3px solid #121212"; shdw = ""
    else:
        bg = "#FFFFFF"; txt_cor = "#444"; val_cor = cor; fw = "500"; fs = "12px"; pad = "9px 16px"
        bd = f"1px solid #E0E0E0"; shdw = ""
    return f"""<div style="background:{bg};border:{bd};
        padding:{pad};margin-bottom:3px;
        display:flex;justify-content:space-between;align-items:center">
        <span style="font-size:{fs};font-weight:{fw};color:{txt_cor};
                     font-family:'Outfit',sans-serif;text-transform:{'uppercase' if destaque else 'none'};
                     letter-spacing:{'.05em' if destaque else '0'}">{label}</span>
        <div style="display:flex;gap:20px;align-items:center">
            <span style="font-size:10px;color:#888;font-family:Outfit,sans-serif">{pct_val:.1f}%</span>
            <span style="font-size:{'16' if destaque else '13'}px;font-weight:{fw};
                         color:{val_cor};font-family:'Outfit',sans-serif">{fmt(valor)}</span>
        </div>
    </div>"""


SCRIPTS_PADRAO={
    "Script 1 — Primeiro contato lead novo (Aline | 5 min)":
"""Oi, tudo bem? Vi que você entrou em contato com a gente.
Antes de te responder de qualquer forma, quero entender melhor o seu momento para não te dar uma resposta genérica.
Hoje o que mais está te incomodando: cansaço, peso, sono ruim, intestino, falta de energia, hormônios ou sensação de não estar performando como antes?""",
    "Script 2 — Follow-up D+1 sem resposta (Aline)":
"""Oi [nome], tudo bem? Ontem você entrou em contato e quero garantir que você receba uma resposta de verdade.
Sei que às vezes a rotina atrasa a gente. Se fizer sentido, me conta rapidinho: o que mais está te incomodando hoje em relação à sua saúde?""",
    "Script 3 — Reativação RFM (Beatriz)":
"""Oi [nome], tudo bem? Estava revisando alguns acompanhamentos aqui e lembrei de você.
Queria saber como você está hoje em relação à [energia / sono / peso / intestino / disposição].
Muitas vezes, quando o acompanhamento fica parado, o corpo começa a dar sinais antes de piorar. Se fizer sentido, podemos agendar uma reavaliação.""",
    "Script 4 — Pedido de indicação":
"""Fico muito feliz em ver sua evolução, [nome].
Normalmente, quem passa por esse processo lembra de alguém próximo que também está cansado, acima do peso, sem energia ou tentando recuperar a saúde.
Se você pensar em alguém, pode indicar com tranquilidade. Vamos acolher essa pessoa com cuidado.""",
    "Script 5 — Cobertura do almoço (Beatriz respondendo leads)":
"""Oi, tudo bem! Sou a [nome] da Clínica Integrative.
Recebi sua mensagem e já anotei tudo aqui. Nossa especialista em atendimento retorna em alguns minutos e vai te dar uma resposta completa.
Pode me dizer rapidinho: o que mais está te incomodando hoje?""",
    "Script 6 — Confirmação de agendamento (Beatriz)":
"""Oi [nome]! Passando para confirmar sua consulta amanhã às [horário] com [profissional].
Está tudo certo por aí? Qualquer dúvida pode me chamar. A clínica fica em [endereço]. Estamos te esperando!""",
    "Script 7 — Boas-vindas paciente novo (Beatriz)":
"""Oi [nome], que bom ter você aqui! Preparamos um vídeo rápido para você se sentir em casa antes mesmo de chegar.
[link do vídeo]
Qualquer dúvida, estou por aqui. Até [dia]!""",
    "Script 8 — Aniversário do paciente (Beatriz)":
"""Oi [nome]! Hoje é um dia especial e a gente não poderia deixar passar sem te lembrar.
Feliz aniversário! Que esse novo ciclo traga muito mais saúde, energia e leveza.
Se quiser comemorar cuidando de você, estamos aqui com muito carinho.""",
    "Script 9 — SBAR diário (Gerente → Dr. Vinícius | até 18h)":
"""S — SITUAÇÃO: [o que aconteceu de relevante hoje]
B — BACKGROUND: [contexto: meta do mês, situação atual, histórico]
A — AVALIAÇÃO: [leitura da gerente sobre o dia]
R — RECOMENDAÇÃO: [o que precisa ser feito amanhã, com DRI e prazo]""",
}

# ══════════════════════════════════════════════════════════════
# TELA DE LOGIN
# ══════════════════════════════════════════════════════════════
def tela_login():
    st.markdown(f"""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;700;900&display=swap');
    * {{ box-sizing: border-box; }}
    html, body, [class*="css"] {{
        font-family: 'Outfit', sans-serif !important;
        background-color: #F0F0F0 !important;
    }}
    .main {{ background-color: #F0F0F0 !important; }}
    .block-container {{ padding: 0 !important; max-width: 100% !important; }}
    div[data-testid="stSidebarContent"] {{ display: none !important; }}
    section[data-testid="stSidebar"] {{ display: none !important; width: 0 !important; }}
    button[kind="header"] {{ display: none !important; }}
    header {{ display: none !important; }}
    .stTextInput > div > div > input {{
        background: #FFFFFF !important;
        border: 3px solid #121212 !important;
        border-radius: 0 !important;
        color: #121212 !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        padding: 14px 16px !important;
    }}
    .stTextInput > div > div > input:focus {{
        border-color: #1040C0 !important;
        box-shadow: 4px 4px 0px 0px #1040C0 !important;
        outline: none !important;
    }}
    .stButton > button {{
        background-color: #D02020 !important;
        color: #FFFFFF !important;
        border: 3px solid #121212 !important;
        border-radius: 0 !important;
        font-family: 'Outfit', sans-serif !important;
        font-weight: 900 !important;
        font-size: 1rem !important;
        text-transform: uppercase !important;
        letter-spacing: 0.12em !important;
        padding: 14px 28px !important;
        box-shadow: 5px 5px 0px 0px #121212 !important;
        width: 100% !important;
        transition: all 0.15s ease-out !important;
    }}
    .stButton > button:hover {{
        background-color: #B01A1A !important;
        transform: translateY(-2px) !important;
        box-shadow: 7px 7px 0px 0px #121212 !important;
    }}
    .stButton > button:active {{
        transform: translate(4px, 4px) !important;
        box-shadow: 1px 1px 0px 0px #121212 !important;
    }}
    </style>""", unsafe_allow_html=True)

    # Layout: painel esquerdo colorido + formulário direito
    col_left, col_right = st.columns([5, 4])

    with col_left:
        _hl = (
            '<div style="background:#1040C0;min-height:100vh;padding:60px 50px;'
            'display:flex;flex-direction:column;justify-content:space-between;'
            'border-right:4px solid #121212">'
            '<div>'
            '<div style="display:flex;gap:8px;align-items:center;margin-bottom:28px">'
            '<div style="width:14px;height:14px;background:#D02020;border-radius:50%"></div>'
            '<div style="width:14px;height:14px;background:#F0C020"></div>'
            '<div style="width:0;height:0;border-left:7px solid transparent;'
            'border-right:7px solid transparent;border-bottom:14px solid #F0F0F0"></div>'
            '<span style="font-size:1.1rem;font-weight:900;color:#FFFFFF;'
            'text-transform:uppercase;font-family:Outfit,sans-serif;margin-left:6px">'
            'LAB Metrics</span></div>'
            '<div style="height:4px;background:#F0C020;margin-bottom:36px"></div>'
            '<div style="font-size:3rem;font-weight:900;color:#FFFFFF;'
            'text-transform:uppercase;letter-spacing:-0.03em;'
            'line-height:0.95;font-family:Outfit,sans-serif;margin-bottom:20px">'
            'GEST\u00c3O<br>'
            '<span style="color:#F0C020">EXECUTIVA</span><br>'
            'INTEGRATIVA</div>'
            '<div style="font-size:0.9rem;color:rgba(255,255,255,0.75);'
            'font-weight:500;line-height:1.65;max-width:340px">'
            'Sistema de controle operacional, financeiro e comercial'
            ' da Cl\u00ednica Integrative Campinas.</div>'
            '</div>'
            '<div style="display:grid;grid-template-columns:1fr 1fr;gap:10px;margin:36px 0">'
            '<div style="background:rgba(255,255,255,0.1);padding:14px;'
            'border-left:4px solid #F0C020">'
            '<div style="font-size:8px;color:rgba(255,255,255,0.6);'
            'text-transform:uppercase;letter-spacing:0.15em;'
            'font-weight:700;margin-bottom:4px">M\u00f3dulos</div>'
            '<div style="font-size:1.8rem;font-weight:900;color:#F0C020">18</div></div>'
            '<div style="background:rgba(255,255,255,0.1);padding:14px;'
            'border-left:4px solid #D02020">'
            '<div style="font-size:8px;color:rgba(255,255,255,0.6);'
            'text-transform:uppercase;letter-spacing:0.15em;'
            'font-weight:700;margin-bottom:4px">Equipe</div>'
            '<div style="font-size:1.8rem;font-weight:900;color:#FFFFFF">7</div></div>'
            '<div style="background:rgba(255,255,255,0.1);padding:14px;'
            'border-left:4px solid rgba(255,255,255,0.4)">'
            '<div style="font-size:8px;color:rgba(255,255,255,0.6);'
            'text-transform:uppercase;letter-spacing:0.15em;'
            'font-weight:700;margin-bottom:4px">KPIs</div>'
            '<div style="font-size:1.8rem;font-weight:900;color:#FFFFFF">40+</div></div>'
            '<div style="background:rgba(255,255,255,0.1);padding:14px;'
            'border-left:4px solid #F0C020">'
            '<div style="font-size:8px;color:rgba(255,255,255,0.6);'
            'text-transform:uppercase;letter-spacing:0.15em;'
            'font-weight:700;margin-bottom:4px">M\u00e9todo</div>'
            '<div style="font-size:1.1rem;font-weight:900;color:#F0C020">AME</div></div>'
            '</div>'
            '<div style="border-top:2px solid rgba(255,255,255,0.2);padding-top:16px">'
            '<div style="font-size:9px;color:rgba(255,255,255,0.5);font-style:italic">'
            '\u201cIdeia \u00e9 prata. Mentalidade \u00e9 ouro. '
            '<strong style="color:#F0C020;font-style:normal">'
            'Execu\u00e7\u00e3o \u00e9 diamante.</strong>\u201d</div>'
            '<div style="font-size:8px;color:rgba(255,255,255,0.3);margin-top:6px;'
            'text-transform:uppercase;letter-spacing:0.1em">'
            'Powered by Projeto Ponteiro</div>'
            '</div></div>'
        )
        st.markdown(_hl, unsafe_allow_html=True)

    with col_right:
        _hr = (
            '<div style="min-height:100vh;background:#F0F0F0;padding:60px 50px;'
            'display:flex;flex-direction:column;justify-content:center">'
            '<div style="max-width:360px;margin:0 auto;width:100%">'
            '<div style="margin-bottom:40px">'
            '<div style="font-size:9px;color:#888;text-transform:uppercase;'
            'letter-spacing:0.2em;font-weight:700;margin-bottom:8px">Acesso Restrito</div>'
            '<div style="font-size:2rem;font-weight:900;color:#121212;'
            'text-transform:uppercase;letter-spacing:-0.02em;line-height:1;margin-bottom:4px">'
            'ENTRAR NO<br>SISTEMA</div>'
            '<div style="height:4px;background:#D02020;width:60px;margin-top:12px"></div>'
            '</div>'
        )
        st.markdown(_hr, unsafe_allow_html=True)

        # Formulário dentro da coluna direita
        st.markdown("<div style='max-width:360px;margin:0 auto'>", unsafe_allow_html=True)
        login_input = st.text_input("USUÁRIO", placeholder="seu.login", key="login_input")
        pw_input = st.text_input("SENHA", type="password", placeholder="••••••••", key="pw_input")

        st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
        entrar = st.button("ENTRAR →", use_container_width=True, key="btn_login")

        if entrar:
            if not login_input or not pw_input:
                st.error("Preencha usuário e senha.")
            else:
                user = autenticar(login_input, pw_input)
                if user:
                    st.session_state.user_id         = user[0]
                    st.session_state.user_nome       = user[1]
                    st.session_state.user_nivel      = user[2]
                    st.session_state.user_cargo      = user[3]
                    st.session_state.primeiro_acesso = bool(user[4]) if len(user) > 4 else False
                    st.session_state.logado          = True
                    st.session_state.aba             = "🏠  Dashboard"
                    st.rerun()
                else:
                    st.error("Usuário ou senha incorretos.")

        st.markdown('<div></div>', unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# GERADOR DE RELATÓRIO PDF + WHATSAPP
# ══════════════════════════════════════════════════════════════
def gerar_pdf_relatorio(titulo, secoes):
    """secoes = list of (titulo_sec, list_of_linhas_str)"""
    if not HAS_PDF:
        return None
    pdf = FPDF()
    pdf.add_page()
    pdf.set_margins(15, 15, 15)
    # Cabeçalho
    pdf.set_fill_color(16, 64, 192)
    pdf.rect(0, 0, 210, 28, 'F')
    pdf.set_font("Helvetica", "B", 16)
    pdf.set_text_color(255, 255, 255)
    pdf.set_xy(15, 8)
    pdf.cell(0, 10, "LAB METRICS — INTEGRATIVE CAMPINAS", ln=True)
    pdf.set_font("Helvetica", "", 9)
    pdf.set_xy(15, 19)
    pdf.cell(0, 6, f"{titulo}   |   Gerado em: {datetime.now().strftime('%d/%m/%Y %H:%M')}", ln=True)
    # Linha amarela
    pdf.set_fill_color(240, 192, 32)
    pdf.rect(0, 28, 210, 3, 'F')
    pdf.set_y(38)
    pdf.set_text_color(18, 18, 18)
    for sec_titulo, linhas in secoes:
        # Título da seção
        pdf.set_fill_color(18, 18, 18)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 10)
        pdf.cell(0, 8, f"  {sec_titulo.upper()}", ln=True, fill=True)
        pdf.set_text_color(18, 18, 18)
        pdf.set_font("Helvetica", "", 9)
        for i, linha in enumerate(linhas):
            fill = i % 2 == 0
            if fill:
                pdf.set_fill_color(240, 240, 240)
            else:
                pdf.set_fill_color(255, 255, 255)
            pdf.cell(0, 7, f"  {linha}", ln=True, fill=True)
        pdf.ln(4)
    # Rodapé
    pdf.set_y(-20)
    pdf.set_fill_color(208, 32, 32)
    pdf.rect(0, pdf.get_y(), 210, 20, 'F')
    pdf.set_text_color(255, 255, 255)
    pdf.set_font("Helvetica", "I", 8)
    pdf.cell(0, 8, "Projeto Ponteiro — Metodo AME — Execucao e diamante.", ln=True, align="C")
    buf = io.BytesIO()
    pdf.output(buf)
    return buf.getvalue()

def bloco_exportar(nome_modulo, secoes_texto, texto_whats):
    """Renderiza botões de PDF + copiar para WhatsApp ao final de cada módulo."""
    st.markdown(f"""
    <div style="background:#121212;border:3px solid #121212;padding:16px 20px;
                margin-top:32px;display:flex;align-items:center;gap:12px">
        <div style="height:4px;width:32px;background:#F0C020;flex-shrink:0"></div>
        <div style="font-size:10px;color:#F0C020;text-transform:uppercase;
                    letter-spacing:0.15em;font-weight:700;font-family:'Outfit',sans-serif">
            Exportar Relatório — {nome_modulo}
        </div>
    </div>""", unsafe_allow_html=True)

    c1, c2, c3 = st.columns(3)
    with c1:
        if HAS_PDF:
            pdf_bytes = gerar_pdf_relatorio(nome_modulo, secoes_texto)
            if pdf_bytes:
                st.download_button(
                    label="⬇ BAIXAR PDF",
                    data=pdf_bytes,
                    file_name=f"relatorio_{nome_modulo.lower().replace(' ','_')}_{date.today()}.pdf",
                    mime="application/pdf",
                    use_container_width=True,
                    key=f"pdf_{nome_modulo}"
                )
        else:
            st.warning("Instale fpdf2 para PDF.")
    with c2:
        st.download_button(
            label="⬇ BAIXAR TXT",
            data=texto_whats.encode("utf-8"),
            file_name=f"relatorio_{nome_modulo.lower().replace(' ','_')}_{date.today()}.txt",
            mime="text/plain",
            use_container_width=True,
            key=f"txt_{nome_modulo}"
        )
    with c3:
        # Copiar para clipboard via textarea + instrução
        st.text_area("📋 Copiar para WhatsApp",
            value=texto_whats, height=120,
            key=f"wa_{nome_modulo}",
            help="Selecione tudo (Ctrl+A) e copie (Ctrl+C) para colar no WhatsApp")


# ══════════════════════════════════════════════════════════════
# DASHBOARD PRINCIPAL
# ══════════════════════════════════════════════════════════════
MODULOS = [
    ("🩺","Cockpit CEO","Decisão em 30 segundos","#1040C0","🩺  Cockpit CEO"),
    ("☀️","Briefing","Abertura do dia","#2A8A2A","☀️  Briefing — Abertura do Dia"),
    ("🌙","Debriefing","Fechamento do dia","#121212","🌙  Debriefing — Fechamento do Dia"),
    ("📊","Painel DNA","Metas semanais","#D02020","📊  Painel DNA Semanal"),
    ("🏥","Auditoria Salas","Ocupação e no-show","#1040C0","🏥  Auditoria de Salas"),
    ("📈","Comercial","Funil e SDR","#2A8A2A","📈  Comercial & SDR"),
    ("💰","Orçamentos","Pipeline de fechamento","#D02020","💰  Orçamentos"),
    ("🔄","RFM","Reativação e indicações","#1040C0","🔄  RFM & Indicações"),
    ("📋","Réguas","D-1 / D+1 / Follow-up","#F0C020","📋  Réguas D-1 / D+1"),
    ("🎓","Programa Integra","MOD e onboarding","#2A8A2A","🎓  Programa Integra"),
    ("🩻","Segurança","Checklist assistencial","#D02020","🩻  Segurança Assistencial"),
    ("📣","SBAR","Comunicação estruturada","#121212","📣  SBAR"),
    ("💰","Financeiro","DRE e EBITDA","#1040C0","💰  Financeiro & EBITDA"),
    ("📐","OKRs","Objectives e KRs","#2A8A2A","📐  OKRs"),
    ("🧬","Importar","Support Clinic","#D02020","🧬  Importar Support Clinic"),
    ("🤖","Assistente","LAB Metrics IA","#1040C0","🤖  Assistente LAB Metrics"),
    ("📱","WhatsApp","Lançamentos automáticos","#25D366","📱  WhatsApp"),
    ("⚙️","Config","Configurações","#121212","⚙️  Configurações"),
]

def tela_dashboard():
    conn = get_conn()
    clin_r  = conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    dre_r   = conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?",
        (MESES[datetime.now().month-1], datetime.now().year)).fetchone()
    leads_r = conn.execute("SELECT COUNT(*),SUM(convertido),AVG(tempo_resp) FROM leads WHERE mes=? AND ano=?",
        (MESES[datetime.now().month-1], datetime.now().year)).fetchone()
    salas_r = conn.execute("SELECT AVG(horas_ocup*100.0/NULLIF(horas_disp,0)),SUM(perda) FROM salas WHERE mes=? AND ano=?",
        (MESES[datetime.now().month-1], datetime.now().year)).fetchone()
    exec_h  = conn.execute("SELECT COUNT(*),SUM(concluida) FROM mod_execucao WHERE data_exec=?",
        (date.today().isoformat(),)).fetchone()
    # MOD por colaborador
    colabs_df = pd.read_sql("SELECT * FROM colaboradores WHERE ativo=1", conn)
    tarefas_n = conn.execute("SELECT COUNT(*) FROM mod_tarefas WHERE ativo=1").fetchone()[0]
    conn.close()

    rb  = sum([(dre_r[i] or 0) for i in [3,4,5,6]]) if dre_r else 0
    meta = clin_r[2] if clin_r else 0
    imp  = dre_r[7] if dre_r else 8.5; tc = dre_r[8] if dre_r else 3.0
    ins  = dre_r[9] if dre_r else 0
    cf   = sum([(dre_r[i] or 0) for i in [10,11,12,13]]) if dre_r else 0
    ebitda = rb*(1-(imp+tc)/100) - ins - cf
    l_tot = leads_r[0] or 0; l_conv = leads_r[1] or 0
    tx_conv = pct_safe(int(l_conv or 0), int(l_tot or 1))
    tx_ocup = salas_r[0] if salas_r and salas_r[0] else 0
    score_mod = min(round((exec_h[1] or 0)/max(exec_h[0] or 1,1)*100,1),100) if exec_h else 0
    pct_meta = pct_safe(rb, meta)

    # ── Barra de topo ────────────────────────────────────────
    st.markdown(f"""
    <div style="background:#121212;border-bottom:4px solid #F0C020;
                padding:12px 28px;display:flex;justify-content:space-between;
                align-items:center;margin:-2rem -2.5rem 28px;position:sticky;top:0;z-index:100">
        <div style="display:flex;align-items:center;gap:10px">
            <div style="display:flex;gap:4px;align-items:center">
                <div style="width:10px;height:10px;background:#D02020;border-radius:50%"></div>
                <div style="width:10px;height:10px;background:#F0C020"></div>
                <div style="width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:10px solid #1040C0"></div>
            </div>
            <div style="font-size:0.9rem;font-weight:900;color:#F0F0F0;
                        text-transform:uppercase;letter-spacing:0.05em;
                        font-family:'Outfit',sans-serif">LAB Metrics</div>
            <div style="font-size:10px;color:#888;border-left:2px solid #333;
                        padding-left:10px;font-family:'Outfit',sans-serif;font-weight:500">
                Integrative Campinas
            </div>
        </div>
        <div style="display:flex;align-items:center;gap:16px">
            <div style="font-size:10px;color:#888;font-family:'Outfit',sans-serif">
                {date.today().strftime('%d/%m/%Y')}
            </div>
            <div style="background:#1040C0;padding:6px 14px;border:2px solid #444">
                <span style="font-size:10px;color:#F0F0F0;font-weight:700;
                             text-transform:uppercase;letter-spacing:0.1em;
                             font-family:'Outfit',sans-serif">
                    {st.session_state.get('user_nome','Usuário')}
                </span>
            </div>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── Título ────────────────────────────────────────────────
    st.markdown(f"""
    <div style="margin-bottom:24px">
        <div style="display:flex;align-items:center;gap:0;margin-bottom:0">
            <div style="width:8px;height:40px;background:{RED_B};margin-right:14px;flex-shrink:0"></div>
            <div>
                <div style="font-size:9px;color:#888;text-transform:uppercase;letter-spacing:0.2em;
                            font-weight:700;font-family:'Outfit',sans-serif">Dashboard Executivo</div>
                <div style="font-size:1.4rem;font-weight:900;color:#121212;text-transform:uppercase;
                            letter-spacing:-0.02em;font-family:'Outfit',sans-serif;line-height:1">
                    Painel de Controle — {date.today().strftime('%d/%m/%Y')}
                </div>
            </div>
        </div>
        <div style="height:3px;background:#121212;margin-top:10px"></div>
    </div>""", unsafe_allow_html=True)

    # ── KPIs principais (linha 1) ─────────────────────────────
    kpis = [
        ("Faturamento Realizado", fmt(rb), f"{pct_meta:.0f}% da meta", RED_B if pct_meta<60 else YELL_B if pct_meta<85 else GREEN, RED_B),
        ("Meta Mensal", fmt(meta), f"Falta {fmt(max(meta-rb,0))}", BLUE_B, BLUE_B),
        ("EBITDA Operacional", fmt(ebitda), f"{pct_safe(ebitda,rb):.1f}% de margem", GREEN if ebitda>0 else RED_B, GREEN if ebitda>0 else RED_B),
        ("Conversão de Leads", f"{tx_conv:.1f}%", f"{int(l_conv or 0)} de {l_tot} leads", GREEN if tx_conv>=30 else RED_B, YELL_B),
        ("Ocupação das Salas", f"{tx_ocup:.1f}%", "meta: 85%", GREEN if tx_ocup>=85 else YELL_B if tx_ocup>=60 else RED_B, BLUE_B),
        ("Score MOD Equipe", f"{score_mod:.1f}%", "meta: 85%", GREEN if score_mod>=85 else RED_B, RED_B),
    ]
    cols_kpi = st.columns(6)
    for col, (lbl, val, sub, cor_val, cor_dec) in zip(cols_kpi, kpis):
        with col:
            st.markdown(f"""
            <div style="background:#FFFFFF;border:4px solid #121212;border-radius:0;
                        padding:16px 18px;box-shadow:5px 5px 0px 0px #121212;
                        position:relative;overflow:hidden;margin-bottom:4px">
                <div style="position:absolute;top:0;left:0;width:6px;height:100%;background:{cor_dec}"></div>
                <div style="padding-left:8px">
                    <div style="font-size:8px;color:#888;text-transform:uppercase;letter-spacing:0.15em;
                                font-weight:700;margin-bottom:8px;font-family:'Outfit',sans-serif">{lbl}</div>
                    <div style="font-size:1.5rem;font-weight:900;color:{cor_val};letter-spacing:-0.02em;
                                line-height:1;font-family:'Outfit',sans-serif">{val}</div>
                    <div style="font-size:10px;color:#888;margin-top:6px;
                                font-weight:500;font-family:'Outfit',sans-serif">{sub}</div>
                </div>
            </div>""", unsafe_allow_html=True)

    # ── Barra de progresso da meta mensal ────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    cor_barra = RED_B if pct_meta<60 else YELL_B if pct_meta<85 else GREEN
    st.markdown(f"""
    <div style="background:#FFFFFF;border:3px solid #121212;padding:14px 18px;
                margin-bottom:28px;box-shadow:4px 4px 0 #121212">
        <div style="display:flex;justify-content:space-between;margin-bottom:8px">
            <span style="font-size:9px;font-weight:700;text-transform:uppercase;
                         letter-spacing:0.15em;color:#121212;font-family:'Outfit',sans-serif">
                PROGRESSO DA META MENSAL
            </span>
            <span style="font-size:14px;font-weight:900;color:{cor_barra};
                         font-family:'Outfit',sans-serif">{pct_meta:.1f}%</span>
        </div>
        <div style="height:16px;background:#E0E0E0;border:2px solid #121212;overflow:hidden">
            <div style="height:100%;width:{min(pct_meta,100):.1f}%;background:{cor_barra};
                        transition:width 0.6s ease-out"></div>
        </div>
        <div style="display:flex;justify-content:space-between;margin-top:6px;
                    font-size:10px;color:#888;font-family:'Outfit',sans-serif">
            <span>Realizado: {fmt(rb)}</span>
            <span>Meta: {fmt(meta)}</span>
        </div>
    </div>""", unsafe_allow_html=True)

    # ── KPIs de equipe (MOD por colaborador) ─────────────────
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0;margin-bottom:16px">
        <div style="width:8px;height:28px;background:{BLUE_B};margin-right:12px;flex-shrink:0"></div>
        <div style="font-size:1rem;font-weight:900;color:#121212;text-transform:uppercase;
                    letter-spacing:-0.01em;font-family:'Outfit',sans-serif">Tarefas da Equipe — Hoje</div>
    </div>""", unsafe_allow_html=True)

    if not colabs_df.empty:
        conn2 = get_conn()
        cols_eq = st.columns(min(len(colabs_df), 7))
        for i, (_, colab) in enumerate(colabs_df.iterrows()):
            if i >= 7: break
            tarefas_colab = conn2.execute("SELECT COUNT(*) FROM mod_tarefas WHERE cargo_key=? AND ativo=1",
                (colab['cargo_key'],)).fetchone()[0]
            feitas = conn2.execute("SELECT COUNT(*) FROM mod_execucao me JOIN mod_tarefas mt ON me.tarefa_id=mt.id WHERE mt.cargo_key=? AND me.data_exec=? AND me.concluida=1",
                (colab['cargo_key'], date.today().isoformat())).fetchone()[0]
            sc = pct_safe(feitas, tarefas_colab) if tarefas_colab else 0
            cor_sc = GREEN if sc>=85 else YELL_B if sc>=50 else RED_B
            emoji_nivel = "🏆" if sc>=85 else "📈" if sc>=50 else "⚠️"
            with cols_eq[i]:
                st.markdown(f"""
                <div style="background:#FFFFFF;border:3px solid #121212;padding:12px 10px;
                            text-align:center;box-shadow:3px 3px 0 #121212;margin-bottom:8px">
                    <div style="font-size:18px;margin-bottom:4px">{emoji_nivel}</div>
                    <div style="font-size:9px;font-weight:700;text-transform:uppercase;
                                letter-spacing:0.08em;color:#121212;font-family:'Outfit',sans-serif;
                                margin-bottom:6px;line-height:1.2">{colab['nome'].split()[0]}</div>
                    <div style="font-size:1.3rem;font-weight:900;color:{cor_sc};
                                font-family:'Outfit',sans-serif">{sc:.0f}%</div>
                    <div style="font-size:8px;color:#888;font-family:'Outfit',sans-serif">{feitas}/{tarefas_colab}</div>
                    <div style="height:6px;background:#E0E0E0;border:1px solid #121212;
                                margin-top:6px;overflow:hidden">
                        <div style="height:100%;width:{min(sc,100):.0f}%;background:{cor_sc}"></div>
                    </div>
                </div>""", unsafe_allow_html=True)
        conn2.close()

    # ── Grade de módulos ──────────────────────────────────────
    st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style="display:flex;align-items:center;gap:0;margin-bottom:16px">
        <div style="width:8px;height:28px;background:{YELL_B};margin-right:12px;flex-shrink:0;border:1px solid #121212"></div>
        <div style="font-size:1rem;font-weight:900;color:#121212;text-transform:uppercase;
                    letter-spacing:-0.01em;font-family:'Outfit',sans-serif">Módulos do Sistema</div>
    </div>""", unsafe_allow_html=True)

    # Grid 6 colunas com cards clicáveis
    linhas = [MODULOS[i:i+6] for i in range(0, len(MODULOS), 6)]
    for linha in linhas:
        cols_mod = st.columns(6)
        for col, (emoji, nome, desc, cor, aba_key) in zip(cols_mod, linha):
            with col:
                txt_cor = "#121212" if cor == YELL_B else "#FFFFFF"
                if st.button(f"{emoji}\n{nome}", key=f"mod_{aba_key}", use_container_width=True,
                             help=desc):
                    st.session_state.aba = aba_key
                    st.rerun()
                st.markdown(f"""
                <div style="font-size:9px;color:#888;text-align:center;
                            margin-top:-4px;margin-bottom:8px;font-family:'Outfit',sans-serif">
                    {desc}
                </div>""", unsafe_allow_html=True)

    # ── Alertas rápidos ───────────────────────────────────────
    conn3 = get_conn()
    orc_quentes = conn3.execute("SELECT COUNT(*) FROM orcamentos WHERE temperatura='Quente' AND status='Aberto' AND proxima_acao=''").fetchone()[0]
    seg_d1 = conn3.execute("SELECT COUNT(*) FROM seguranca WHERE d1_enviado=0").fetchone()[0]
    sbar_pend = conn3.execute("SELECT COUNT(*) FROM sbar WHERE resolvido=0").fetchone()[0]
    conn3.close()

    alertas = []
    if orc_quentes > 0: alertas.append((RED_B, f"🔥 {orc_quentes} orçamento(s) QUENTE sem ação — Bianca, ligar agora!"))
    if seg_d1 > 0:      alertas.append((YELL_B, f"⚠️ {seg_d1} paciente(s) sem D+1 enviado — Paloma, enviar até 10h!"))
    if sbar_pend > 0:   alertas.append((BLUE_B, f"📣 {sbar_pend} SBAR(s) pendente(s) de resolução"))
    if score_mod < 85:  alertas.append((RED_B, f"📋 Score MOD abaixo de 85% — verificar tarefas da equipe"))

    if alertas:
        st.markdown(f"""
        <div style="display:flex;align-items:center;gap:0;margin:24px 0 12px">
            <div style="width:8px;height:28px;background:{RED_B};margin-right:12px;flex-shrink:0"></div>
            <div style="font-size:1rem;font-weight:900;color:#121212;text-transform:uppercase;
                        letter-spacing:-0.01em;font-family:'Outfit',sans-serif">Alertas Críticos</div>
        </div>""", unsafe_allow_html=True)
        for cor_a, msg_a in alertas:
            txt_a = "#121212" if cor_a == YELL_B else "#FFFFFF"
            st.markdown(f"""
            <div style="background:{cor_a};border:3px solid #121212;padding:12px 18px;
                        margin-bottom:6px;box-shadow:3px 3px 0 #121212">
                <span style="font-size:13px;font-weight:700;color:{txt_a};
                             font-family:'Outfit',sans-serif">{msg_a}</span>
            </div>""", unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# CONTROLE DE FLUXO — LOGIN → DASHBOARD → MÓDULOS
# ══════════════════════════════════════════════════════════════
# Inicializar session state
if "logado" not in st.session_state:
    st.session_state.logado          = False
    st.session_state.user_nome       = ""
    st.session_state.user_nivel      = ""
    st.session_state.user_cargo      = ""
    st.session_state.primeiro_acesso = False
    st.session_state.aba             = "🏠  Dashboard"

# Se não logado → mostrar tela de login
if not st.session_state.logado:
    tela_login()
    st.stop()

# Se é o primeiro acesso → exigir troca de senha antes de tudo
if st.session_state.get("primeiro_acesso", False):
    tela_trocar_senha()
    st.stop()

# ── Sidebar (só aparece quando logado, colapsável) ────────────
with st.sidebar:
    st.markdown(f"""
    <div style="padding:16px 14px 8px">
        <div style="display:flex;gap:4px;align-items:center;margin-bottom:8px">
            <div style="width:10px;height:10px;background:{RED_B};border-radius:50%;border:1px solid #555"></div>
            <div style="width:10px;height:10px;background:{YELL_B};border:1px solid #555"></div>
            <div style="width:0;height:0;border-left:5px solid transparent;border-right:5px solid transparent;border-bottom:10px solid {BLUE_B}"></div>
            <div style="font-size:0.8rem;font-weight:900;color:#F0F0F0;
                        text-transform:uppercase;letter-spacing:0.05em;
                        font-family:'Outfit',sans-serif;margin-left:6px">LAB Metrics</div>
        </div>
        <div style="height:2px;background:{YELL_B};margin-bottom:10px"></div>
        <div style="background:#1040C0;padding:8px 10px;margin-bottom:12px;border:1px solid #333">
            <div style="font-size:8px;color:rgba(255,255,255,0.6);text-transform:uppercase;
                        letter-spacing:0.1em;font-weight:700;margin-bottom:2px">Logado como</div>
            <div style="font-size:11px;color:#F0F0F0;font-weight:700;
                        font-family:'Outfit',sans-serif">{st.session_state.user_nome}</div>
            <div style="font-size:9px;color:#888">{st.session_state.user_nivel}</div>
        </div>
    </div>""", unsafe_allow_html=True)

    conn_sb = get_conn()
    clin_sb = conn_sb.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    conn_sb.close()
    estagio_sb = clin_sb[4] if clin_sb and len(clin_sb)>4 else "Intuitivo"
    cor_est = {"Caótico":RED_B,"Intuitivo":YELL_B,"Documentado":BLUE_B,"Previsível":GREEN}.get(estagio_sb,BLUE_B)
    txt_est = "#121212" if cor_est==YELL_B else "#FFFFFF"

    # Período
    c1sb,c2sb = st.columns([3,2])
    with c1sb: mes_sel = st.selectbox("M",MESES,index=datetime.now().month-1,label_visibility="collapsed")
    with c2sb: ano_sel = st.number_input("A",value=datetime.now().year,min_value=2020,max_value=2030,label_visibility="collapsed")

    st.markdown(f'<div style="height:2px;background:{YELL_B};margin:8px 0 4px"></div>',unsafe_allow_html=True)

    # Navegação
    opcoes_nav = ["🏠  Dashboard"] + [m[4] for m in MODULOS]
    aba = st.radio("", opcoes_nav, label_visibility="collapsed",
        index=opcoes_nav.index(st.session_state.aba) if st.session_state.aba in opcoes_nav else 0)
    st.session_state.aba = aba

    st.markdown(f'<div style="height:2px;background:#333;margin:12px 0 8px"></div>',unsafe_allow_html=True)
    if st.button("↩ SAIR", use_container_width=True):
        for k in ["logado","user_nome","user_nivel","user_cargo","user_id","aba"]:
            if k in st.session_state: del st.session_state[k]
        st.rerun()

# Recuperar aba do session state
aba = st.session_state.aba

# ══════════════════════════════════════════════════════════════
# 1. COCKPIT CEO
# ══════════════════════════════════════════════════════════════
if aba=="🏠  Dashboard":
    tela_dashboard()

elif aba=="🩺  Cockpit CEO":
    st.markdown(titulo_secao("Cockpit de Decisão Executiva","Tudo que você precisa saber em 30 segundos"),unsafe_allow_html=True)
    conn=get_conn()
    dre_r=conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone()
    salas_r=pd.read_sql("SELECT * FROM salas WHERE mes=? AND ano=?",conn,params=(mes_sel,ano_sel))
    leads_r=conn.execute("SELECT COUNT(*),SUM(convertido),SUM(ticket) FROM leads WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone()
    clin_r=conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    exec_hoje=conn.execute("SELECT COUNT(*),SUM(concluida) FROM mod_execucao WHERE data_exec=?",(date.today().isoformat(),)).fetchone()
    leads_df_all=pd.read_sql("SELECT * FROM leads WHERE mes=? AND ano=?",conn,params=(mes_sel,ano_sel))
    conn.close()
    rb=sum([(dre_r[i] or 0) for i in [3,4,5,6]]) if dre_r else 0
    imp=dre_r[7] if dre_r else 8.5; tc=dre_r[8] if dre_r else 3.0
    ins=dre_r[9] if dre_r else 0; pes=dre_r[10] if dre_r else 0
    oc=dre_r[11] if dre_r else 0; mk=dre_r[12] if dre_r else 0; ou=dre_r[13] if dre_r else 0
    ded=rb*(imp+tc)/100; rl=rb-ded; mc=rl-ins; cf=pes+oc+mk+ou; ebitda=mc-cf
    margem_ebitda=pct_safe(ebitda,rb)
    perda_ns=float(salas_r['perda'].sum()) if not salas_r.empty else 0.0
    meta_fat=clin_r[2] if clin_r else 0; custo_fx=clin_r[3] if clin_r else cf or 1
    l_tot=leads_r[0] or 0; l_conv=leads_r[1] or 0; pipeline=leads_r[2] or 0
    tot_tarefas=exec_hoje[0] or 1; ok_tarefas=exec_hoje[1] or 0
    score_mod=min(round(ok_tarefas/tot_tarefas*100,1),100) if tot_tarefas else 0
    # KPIs
    st.markdown(kpi_grid([
        ("Receita Realizada",fmt(rb),f"{pct_safe(rb,meta_fat):.0f}% da meta mensal",GREEN),
        ("EBITDA Operacional",fmt(ebitda),f"{margem_ebitda:.1f}% de margem",GREEN if ebitda>0 else RED_SOFT),
        ("Prejuízo Oculto — No-Show",fmt(perda_ns),"Faturamento que saiu pela porta",RED_SOFT),
        ("Score MOD da Equipe",f"{score_mod:.1f}%","Meta: acima de 85%",GREEN if score_mod>=85 else RED_SOFT),
    ]),unsafe_allow_html=True)
    col_esq,col_dir=st.columns([3,2])
    with col_esq:
        st.markdown(f"<div style='color:{FG};font-weight:600;margin-bottom:10px;font-size:13px'>Faturamento por Prescritor</div>",unsafe_allow_html=True)
        if not leads_df_all.empty and leads_df_all['convertido'].any():
            fat_sdr=leads_df_all[leads_df_all['convertido']==1].groupby('sdr')['ticket'].sum()
            if not fat_sdr.empty: st.bar_chart(fat_sdr)
            else: st.info("Lance leads convertidos com ticket para ver o gráfico.")
        else: st.info("Sem dados de leads convertidos neste período.")
        st.markdown(f"<div style='color:{FG};font-weight:600;margin:16px 0 8px;font-size:13px'>Ponto de Equilíbrio</div>",unsafe_allow_html=True)
        prog_be=pct_safe(rb,custo_fx)
        st.progress(min(prog_be/100,1.0),text=f"Progresso: {prog_be:.1f}%")
        if rb>=custo_fx: st.success(f"Break-even batido! Lucro real: {fmt(ebitda)}")
        else: st.warning(f"Faltam {fmt(custo_fx-rb)} para cobrir os custos fixos.")
    with col_dir:
        st.markdown(f"<div style='color:{FG};font-weight:600;margin-bottom:10px;font-size:13px'>DRE Rápido</div>",unsafe_allow_html=True)
        for lbl_d,val_d,pct_d,cor_d,dest_d in [
            ("Receita Bruta",rb,100.0,GREEN,False),
            (f"Impostos + Taxas ({imp+tc:.1f}%)",ded,pct_safe(ded,rb),RED_SOFT,False),
            ("Receita Líquida",rl,pct_safe(rl,rb),FG,False),
            ("Insumos Médicos",ins,pct_safe(ins,rb),RED_SOFT,False),
            ("Margem de Contribuição",mc,pct_safe(mc,rb),YELL_SOFT,True),
            ("Custos Fixos",cf,pct_safe(cf,rb),RED_SOFT,False),
            ("EBITDA OPERACIONAL",ebitda,margem_ebitda,GREEN if ebitda>0 else RED_SOFT,True),
        ]: st.markdown(dre_linha(lbl_d,val_d,pct_d,cor_d,dest_d),unsafe_allow_html=True)
        st.markdown(f"<div style='color:{FG};font-weight:600;margin:16px 0 8px;font-size:13px'>Pipeline Comercial</div>",unsafe_allow_html=True)
        st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:12px;padding:14px 18px">
            <div style="display:flex;justify-content:space-between;margin-bottom:10px">
                <span style="color:{FG_MUTED};font-size:12px">Leads totais</span>
                <span style="color:{FG};font-weight:600">{l_tot}</span>
            </div>
            <div style="display:flex;justify-content:space-between;margin-bottom:10px">
                <span style="color:{FG_MUTED};font-size:12px">Convertidos</span>
                <span style="color:{GREEN};font-weight:600">{int(l_conv or 0)}</span>
            </div>
            <div style="display:flex;justify-content:space-between">
                <span style="color:{FG_MUTED};font-size:12px">Pipeline aberto</span>
                <span style="color:{YELL_SOFT};font-weight:600">{fmt(pipeline)}</span>
            </div>
        </div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 2. BRIEFING
# ══════════════════════════════════════════════════════════════
    # ── Exportar relatório ───────────────────────────────────────
    try:
        _secoes_cockpit_ceo = [("Cockpit CEO", ["Meta mensal: " + fmt(meta_fat), "Receita: " + fmt(rb), "EBITDA: " + fmt(ebitda), "Score MOD: " + str(score_mod) + "%"])]
        _txt_cockpit_ceo = "\n".join([f"{l}" for _,ls in _secoes_cockpit_ceo for l in ls])
        bloco_exportar("Cockpit CEO", _secoes_cockpit_ceo, _txt_cockpit_ceo)
    except Exception as _ex:
        st.caption(f"Exportar: {_ex}")


elif aba=="☀️  Briefing — Abertura do Dia":
    hj=date.today().isoformat(); hj_fmt=date.today().strftime("%d/%m/%Y")
    st.markdown(titulo_secao(f"Briefing de Abertura — {hj_fmt}","Rituais de 10 minutos. Agenda, oportunidades e prioridades definidas antes do primeiro atendimento."),unsafe_allow_html=True)
    conn=get_conn()
    bf=conn.execute("SELECT * FROM briefing WHERE data=?",(hj,)).fetchone()
    dre_bf=conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone()
    clin_bf=conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    db_ont=conn.execute("SELECT * FROM debriefing WHERE data=?",((date.today()-timedelta(days=1)).isoformat(),)).fetchone()
    conn.close()
    meta_m=clin_bf[2] if clin_bf else 0
    rb_mes=sum([(dre_bf[i] or 0) for i in [3,4,5,6]]) if dre_bf else 0
    falta_meta=max(meta_m-rb_mes,0); meta_dia=meta_m/22 if meta_m else 0
    if db_ont:
        rec_ont=(db_ont[3] or 0)+(db_ont[4] or 0)+(db_ont[5] or 0)+(db_ont[6] or 0)
        st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER_ACC};border-radius:12px;padding:14px 20px;margin-bottom:20px">
            <div style="color:{ACCENT};font-size:10px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px">ONTEM — RESUMO RÁPIDO</div>
            <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:10px;font-size:12px">
                <div><span style="color:{FG_MUTED}">Receita</span><br><strong style="color:{FG}">{fmt(rec_ont)}</strong></div>
                <div><span style="color:{FG_MUTED}">Consultas</span><br><strong style="color:{FG}">{db_ont[10] or 0}</strong></div>
                <div><span style="color:{FG_MUTED}">No-shows</span><br><strong style="color:{RED_SOFT}">{db_ont[12] or 0}</strong></div>
                <div><span style="color:{FG_MUTED}">Leads resp.</span><br><strong style="color:{FG}">{db_ont[15] or 0}</strong></div>
                <div><span style="color:{FG_MUTED}">Ação de hoje</span><br><strong style="color:{YELL_SOFT}">{db_ont[29] or "—"}</strong></div>
            </div>
        </div>""",unsafe_allow_html=True)
    p_meta=pct_safe(rb_mes,meta_m); _,cor_meta=semaforo(p_meta,80)
    st.markdown(barra(p_meta,f"Meta mensal: {fmt(rb_mes)} de {fmt(meta_m)} — falta {fmt(falta_meta)}",cor_meta),unsafe_allow_html=True)
    # Alerta cobertura almoço
    st.markdown(f"""<div style="background:rgba(94,106,210,0.08);border:1px solid {BORDER_ACC};border-radius:10px;padding:10px 16px;margin:12px 0">
        <span style="color:{ACCENT};font-size:11px;font-weight:600">⚠️ REGRA DO ALMOÇO: O lead não sabe que é hora do almoço. A meta não para. Nunca simultâneo.</span>
    </div>""",unsafe_allow_html=True)
    st.markdown("---")
    with st.form("form_briefing"):
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;font-size:13px;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:14px'>☀️ BRIEFING — {hj_fmt}</div>",unsafe_allow_html=True)
        resp_bf=st.text_input("Responsável pelo briefing (DRI)",value=bf[2] if bf else "",placeholder="Nome de quem conduz")
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:16px 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>01 — AGENDA DO DIA</div>",unsafe_allow_html=True)
        c1,c2,c3,c4,c5=st.columns(5)
        with c1: ca=st.number_input("Consultas ag.",value=int(bf[3] if bf else 0),min_value=0)
        with c2: pa=st.number_input("Procedimentos ag.",value=int(bf[4] if bf else 0),min_value=0)
        with c3: conf=st.number_input("Confirmações",value=int(bf[5] if bf else 0),min_value=0)
        with c4: gaps=st.number_input("Gaps na agenda",value=int(bf[6] if bf else 0),min_value=0)
        with c5: val_ag=st.number_input("Valor projetado R$",value=float(bf[7] if bf else 0),step=100.0)
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:16px 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>02 — OPORTUNIDADES COMERCIAIS</div>",unsafe_allow_html=True)
        c1,c2,c3,c4,c5,c6=st.columns(6)
        with c1: lp=st.number_input("Leads pendentes",value=int(bf[8] if bf else 0),min_value=0)
        with c2: oa=st.number_input("Orç. abertos",value=int(bf[9] if bf else 0),min_value=0)
        with c3: vo=st.number_input("Valor pipeline R$",value=float(bf[10] if bf else 0),step=100.0)
        with c4: rm=st.number_input("Meta RFM",value=int(bf[11] if bf else 30),min_value=0)
        with c5: im=st.number_input("Meta indicações",value=int(bf[12] if bf else 5),min_value=0)
        with c6: rh=st.number_input("Retornos hoje",value=int(bf[13] if bf else 0),min_value=0)
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:16px 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>03 — COBERTURA DO ALMOÇO</div>",unsafe_allow_html=True)
        c1,c2=st.columns(2)
        ops12=["Bianca","Beatriz","Gerente"]; ops13=["Aline","Beatriz","Gerente"]
        with c1: cob12=st.selectbox("Cobertura 12h-13h (Aline almoça)",ops12,index=ops12.index(bf[14]) if bf and bf[14] in ops12 else 0)
        with c2: cob13=st.selectbox("Cobertura 13h-14h (Bianca almoça)",ops13,index=ops13.index(bf[15]) if bf and bf[15] in ops13 else 0)
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:16px 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>04 — RÉGUA D-1 / D+1 E FOLLOW-UP</div>",unsafe_allow_html=True)
        c1,c2,c3,c4,c5,c6,c7=st.columns(7)
        with c1: dm1pc=st.number_input("D-1 Prim.Cons.",value=int(bf[16] if bf else 0),min_value=0)
        with c2: dm1r=st.number_input("D-1 Retorno",value=int(bf[17] if bf else 0),min_value=0)
        with c3: dp1pc=st.number_input("D+1 Prim.Cons.",value=int(bf[18] if bf else 0),min_value=0)
        with c4: dp1r=st.number_input("D+1 Retorno",value=int(bf[19] if bf else 0),min_value=0)
        with c5: fw3=st.number_input("Follow D+3",value=int(bf[20] if bf else 0),min_value=0)
        with c6: fw7=st.number_input("Follow D+7",value=int(bf[21] if bf else 0),min_value=0)
        with c7: fw14=st.number_input("Follow D+14",value=int(bf[22] if bf else 0),min_value=0)
        total_c=dm1pc+dm1r+dp1pc+dp1r+fw3+fw7+fw14
        st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:8px;padding:10px 14px;display:flex;justify-content:space-between;align-items:center;margin-top:4px">
            <span style="color:{FG_MUTED};font-size:12px">Total de contatos planejados hoje</span>
            <span style="color:{ACCENT};font-size:18px;font-weight:600">{total_c} contatos</span>
        </div>""",unsafe_allow_html=True)
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:16px 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>05 — PRIORIDADES DO DIA (AME)</div>",unsafe_allow_html=True)
        c1,c2=st.columns([3,1])
        with c1: pr1=st.text_input("Prioridade 1",value=bf[23] if bf else "",placeholder="Ação principal do dia")
        with c2: dr1=st.text_input("DRI 1",value=bf[26] if bf else "")
        c1,c2=st.columns([3,1])
        with c1: pr2=st.text_input("Prioridade 2",value=bf[24] if bf else "",placeholder="Segunda ação")
        with c2: dr2=st.text_input("DRI 2",value=bf[27] if bf else "")
        c1,c2=st.columns([3,1])
        with c1: pr3=st.text_input("Prioridade 3",value=bf[25] if bf else "",placeholder="Terceira ação")
        with c2: dr3=st.text_input("DRI 3",value=bf[28] if bf else "")
        obs_bf=st.text_area("Observações do briefing",value=bf[29] if bf else "",placeholder="Alertas, contextos, decisões...",height=70)
        if st.form_submit_button("✅ Registrar Briefing",use_container_width=True):
            conn=get_conn()
            conn.execute("""INSERT INTO briefing(data,responsavel,cons_ag,proc_ag,conf,gaps,val_ag,leads_pend,orc_ab,val_orc,rfm_meta,ind_meta,ret_hoje,cob_12h,cob_13h,dm1_pc,dm1_ret,dp1_pc,dp1_ret,fw3,fw7,fw14,pr1,pr2,pr3,dr1,dr2,dr3,obs)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(data) DO UPDATE SET responsavel=excluded.responsavel,cons_ag=excluded.cons_ag,proc_ag=excluded.proc_ag,conf=excluded.conf,gaps=excluded.gaps,val_ag=excluded.val_ag,leads_pend=excluded.leads_pend,orc_ab=excluded.orc_ab,val_orc=excluded.val_orc,rfm_meta=excluded.rfm_meta,ind_meta=excluded.ind_meta,ret_hoje=excluded.ret_hoje,cob_12h=excluded.cob_12h,cob_13h=excluded.cob_13h,dm1_pc=excluded.dm1_pc,dm1_ret=excluded.dm1_ret,dp1_pc=excluded.dp1_pc,dp1_ret=excluded.dp1_ret,fw3=excluded.fw3,fw7=excluded.fw7,fw14=excluded.fw14,pr1=excluded.pr1,pr2=excluded.pr2,pr3=excluded.pr3,dr1=excluded.dr1,dr2=excluded.dr2,dr3=excluded.dr3,obs=excluded.obs""",
            (hj,resp_bf,ca,pa,conf,gaps,val_ag,lp,oa,vo,rm,im,rh,cob12,cob13,dm1pc,dm1r,dp1pc,dp1r,fw3,fw7,fw14,pr1,pr2,pr3,dr1,dr2,dr3,obs_bf))
            conn.commit();conn.close();st.success("Briefing registrado!");st.rerun()
    # Painel visual
    if bf:
        st.markdown("---")
        st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:16px;padding:20px 24px">
            <div style="color:{ACCENT};font-size:11px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:16px">PAINEL DO DIA — {hj_fmt}</div>
            <div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px">
                <div>
                    <div style="color:{FG_MUTED};font-size:10px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">Agenda</div>
                    <div style="background:{BG_DEEP};border:1px solid {BORDER};border-radius:10px;padding:12px;font-size:12px;line-height:2.2">
                        <div style="display:flex;justify-content:space-between"><span style="color:{FG_MUTED}">Consultas</span><strong style="color:{FG}">{bf[3]}</strong></div>
                        <div style="display:flex;justify-content:space-between"><span style="color:{FG_MUTED}">Procedimentos</span><strong style="color:{FG}">{bf[4]}</strong></div>
                        <div style="display:flex;justify-content:space-between"><span style="color:{FG_MUTED}">Confirmações</span><strong style="color:{GREEN}">{bf[5]}</strong></div>
                        <div style="display:flex;justify-content:space-between"><span style="color:{FG_MUTED}">Gaps</span><strong style="color:{RED_SOFT if (bf[6] or 0)>0 else FG}">{bf[6]}</strong></div>
                        <div style="display:flex;justify-content:space-between"><span style="color:{FG_MUTED}">Valor projetado</span><strong style="color:{YELL_SOFT}">{fmt(bf[7])}</strong></div>
                    </div>
                </div>
                <div>
                    <div style="color:{FG_MUTED};font-size:10px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">Oportunidades</div>
                    <div style="background:{BG_DEEP};border:1px solid {BORDER};border-radius:10px;padding:12px;font-size:12px;line-height:2.2">
                        <div style="display:flex;justify-content:space-between"><span style="color:{FG_MUTED}">Leads pendentes</span><strong style="color:{RED_SOFT if (bf[8] or 0)>0 else FG}">{bf[8]}</strong></div>
                        <div style="display:flex;justify-content:space-between"><span style="color:{FG_MUTED}">Orçamentos abertos</span><strong style="color:{YELL_SOFT}">{bf[9]}</strong></div>
                        <div style="display:flex;justify-content:space-between"><span style="color:{FG_MUTED}">Valor pipeline</span><strong style="color:{YELL_SOFT}">{fmt(bf[10])}</strong></div>
                        <div style="display:flex;justify-content:space-between"><span style="color:{FG_MUTED}">Meta RFM</span><strong style="color:{FG}">{bf[11]} contatos</strong></div>
                        <div style="display:flex;justify-content:space-between"><span style="color:{FG_MUTED}">Meta indicações</span><strong style="color:{FG}">{bf[12]} pedidos</strong></div>
                    </div>
                </div>
                <div>
                    <div style="color:{FG_MUTED};font-size:10px;text-transform:uppercase;letter-spacing:0.1em;margin-bottom:8px">Prioridades AME</div>
                    <div style="background:{BG_DEEP};border:1px solid {BORDER};border-radius:10px;padding:12px;font-size:12px">
                        {f'<div style="display:flex;gap:8px;margin-bottom:8px;align-items:flex-start"><div style="width:20px;height:20px;background:{ACCENT};border-radius:50%;display:flex;align-items:center;justify-content:center;color:{FG};font-weight:700;font-size:10px;flex-shrink:0">1</div><div><div style="color:{FG};font-weight:500">{bf[23] or "—"}</div><div style="color:{FG_MUTED};font-size:10px">DRI: {bf[26] or "—"}</div></div></div>' if bf[23] else ""}
                        {f'<div style="display:flex;gap:8px;margin-bottom:8px;align-items:flex-start"><div style="width:20px;height:20px;background:{ACCENT}88;border-radius:50%;display:flex;align-items:center;justify-content:center;color:{FG};font-weight:700;font-size:10px;flex-shrink:0">2</div><div><div style="color:{FG};font-weight:500">{bf[24] or "—"}</div><div style="color:{FG_MUTED};font-size:10px">DRI: {bf[27] or "—"}</div></div></div>' if bf[24] else ""}
                        {f'<div style="display:flex;gap:8px;align-items:flex-start"><div style="width:20px;height:20px;background:{ACCENT}44;border-radius:50%;display:flex;align-items:center;justify-content:center;color:{FG};font-weight:700;font-size:10px;flex-shrink:0">3</div><div><div style="color:{FG};font-weight:500">{bf[25] or "—"}</div><div style="color:{FG_MUTED};font-size:10px">DRI: {bf[28] or "—"}</div></div></div>' if bf[25] else ""}
                    </div>
                </div>
            </div>
        </div>""",unsafe_allow_html=True)
    st.markdown("---")
    st.markdown(f"<div style='color:{FG};font-weight:600;margin-bottom:10px;font-size:13px'>Últimos 7 Briefings</div>",unsafe_allow_html=True)
    conn=get_conn(); hist_bf=pd.read_sql("SELECT data,responsavel,cons_ag,proc_ag,gaps,val_ag,orc_ab,val_orc,pr1 FROM briefing ORDER BY data DESC LIMIT 7",conn); conn.close()
    if not hist_bf.empty:
        hist_bf.columns=["Data","DRI","Consultas","Proced.","Gaps","Valor Agenda","Orç. Abertos","Valor Pipeline","Prioridade 1"]
        hist_bf["Valor Agenda"]=hist_bf["Valor Agenda"].apply(fmt); hist_bf["Valor Pipeline"]=hist_bf["Valor Pipeline"].apply(fmt)
        st.dataframe(hist_bf,hide_index=True,use_container_width=True)
    else: st.info("Nenhum briefing registrado ainda.")

# ══════════════════════════════════════════════════════════════
# 3. DEBRIEFING
# ══════════════════════════════════════════════════════════════
    # ── Exportar relatório ───────────────────────────────────────
    try:
        _secoes_briefing_diário = [("Briefing Diário", [f"Data: {hj_fmt}", f"Responsável: {resp_bf if bf else '-'}", f"Consultas: {bf[3] if bf else 0}", f"Procedimentos: {bf[4] if bf else 0}"])]
        _txt_briefing_diário = "\n".join([f"{l}" for _,ls in _secoes_briefing_diário for l in ls])
        bloco_exportar("Briefing Diário", _secoes_briefing_diário, _txt_briefing_diário)
    except Exception as _ex:
        st.caption(f"Exportar: {_ex}")


elif aba=="🌙  Debriefing — Fechamento do Dia":
    hj=date.today().isoformat(); hj_fmt=date.today().strftime("%d/%m/%Y")
    st.markdown(titulo_secao(f"Debriefing de Fechamento — {hj_fmt}","Caixa do dia, agenda realizada e ações comerciais concretizadas. Feche o dia com clareza."),unsafe_allow_html=True)
    conn=get_conn()
    db=conn.execute("SELECT * FROM debriefing WHERE data=?",(hj,)).fetchone()
    bf_h=conn.execute("SELECT * FROM briefing WHERE data=?",(hj,)).fetchone()
    clin_db=conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    conn.close()
    meta_m=clin_db[2] if clin_db else 0; meta_dia=meta_m/22 if meta_m else 0
    if bf_h:
        st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER_ACC};border-radius:12px;padding:14px 20px;margin-bottom:20px">
            <div style="color:{ACCENT};font-size:10px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:10px">PLANEJADO NO BRIEFING × REALIZADO</div>
            <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:12px;font-size:12px">
                <div><div style="color:{FG_MUTED}">Consultas plan.</div><div style="color:{YELL_SOFT};font-size:18px;font-weight:600">{bf_h[3] or 0}</div></div>
                <div><div style="color:{FG_MUTED}">Procedimentos plan.</div><div style="color:{YELL_SOFT};font-size:18px;font-weight:600">{bf_h[4] or 0}</div></div>
                <div><div style="color:{FG_MUTED}">Valor projetado</div><div style="color:{YELL_SOFT};font-size:18px;font-weight:600">{fmt(bf_h[7])}</div></div>
                <div><div style="color:{FG_MUTED}">Prioridade 1</div><div style="color:{FG};font-size:13px;font-weight:500">{bf_h[23] or "não definida"}</div></div>
            </div>
        </div>""",unsafe_allow_html=True)
    with st.form("form_debriefing"):
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;font-size:13px;letter-spacing:0.05em;text-transform:uppercase;margin-bottom:14px'>🌙 DEBRIEFING — {hj_fmt}</div>",unsafe_allow_html=True)
        resp_db=st.text_input("Responsável pelo fechamento",value=db[2] if db else "",placeholder="Nome de quem fecha o dia")
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:16px 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>01 — CAIXA DO DIA</div>",unsafe_allow_html=True)
        c1,c2,c3,c4=st.columns(4)
        with c1: rc_db=st.number_input("Receita Consultas R$",value=float(db[3] if db else 0),step=100.0)
        with c2: rp_db=st.number_input("Receita Procedimentos R$",value=float(db[4] if db else 0),step=100.0)
        with c3: rr_db=st.number_input("Recorrência LTV R$",value=float(db[5] if db else 0),step=100.0)
        with c4: ro_db=st.number_input("Outros R$",value=float(db[6] if db else 0),step=100.0)
        receita_d=rc_db+rp_db+rr_db+ro_db
        cor_rec=GREEN if receita_d>=meta_dia else RED_SOFT
        st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:8px;padding:10px 16px;display:flex;justify-content:space-between;margin:4px 0 12px">
            <span style="color:{FG_MUTED};font-size:12px">Receita total do dia</span>
            <span style="color:{cor_rec};font-size:20px;font-weight:600">{fmt(receita_d)}</span>
        </div>""",unsafe_allow_html=True)
        c1,c2,c3=st.columns(3)
        with c1: di_db=st.number_input("Despesas Insumos R$",value=float(db[7] if db else 0),step=10.0)
        with c2: do_db=st.number_input("Despesas Operacionais R$",value=float(db[8] if db else 0),step=10.0)
        with c3: da_db=st.number_input("Outras Despesas R$",value=float(db[9] if db else 0),step=10.0)
        total_desp=di_db+do_db+da_db; saldo_d=receita_d-total_desp
        cor_s=GREEN if saldo_d>=0 else RED_SOFT
        st.markdown(f"""<div style="background:{BG_DEEP};border:1px solid {BORDER};border-radius:8px;padding:10px 16px;display:flex;justify-content:space-between;align-items:center;margin:4px 0 12px">
            <div><span style="color:{FG_MUTED};font-size:12px">Despesas: </span><span style="color:{RED_SOFT};font-weight:600">{fmt(total_desp)}</span>
                <span style="color:{FG_MUTED};font-size:12px;margin-left:16px">Saldo: </span><span style="color:{cor_s};font-size:18px;font-weight:600">{fmt(saldo_d)}</span></div>
            <div style="color:{GREEN if receita_d>=meta_dia else RED_SOFT};font-size:11px;font-weight:600">
                {"✅ Meta diária batida" if receita_d>=meta_dia else f"⚠️ Abaixo da meta ({fmt(meta_dia)})"}
            </div>
        </div>""",unsafe_allow_html=True)
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:16px 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>02 — AGENDA REALIZADA</div>",unsafe_allow_html=True)
        c1,c2,c3,c4,c5=st.columns(5)
        with c1: cons_r=st.number_input("Consultas",value=int(db[10] if db else 0),min_value=0)
        with c2: proc_r=st.number_input("Procedimentos",value=int(db[11] if db else 0),min_value=0)
        with c3: ns_db=st.number_input("No-shows",value=int(db[12] if db else 0),min_value=0)
        with c4: canc_db=st.number_input("Cancelamentos",value=int(db[13] if db else 0),min_value=0)
        with c5: perda_db=st.number_input("Perda no-show R$",value=float(db[14] if db else 0),step=100.0)
        if bf_h:
            delta_c=cons_r-(bf_h[3] or 0); cor_dc=GREEN if delta_c>=0 else RED_SOFT
            st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:8px;padding:8px 14px;display:flex;gap:20px;font-size:12px;margin-top:4px">
                <span style="color:{FG_MUTED}">Planejado: <strong style="color:{YELL_SOFT}">{bf_h[3] or 0}</strong></span>
                <span style="color:{FG_MUTED}">Realizado: <strong style="color:{FG}">{cons_r}</strong></span>
                <span style="color:{FG_MUTED}">Variação: <strong style="color:{cor_dc}">{'+'+str(delta_c) if delta_c>=0 else delta_c}</strong></span>
            </div>""",unsafe_allow_html=True)
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:16px 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>03 — COMERCIAL REALIZADO</div>",unsafe_allow_html=True)
        c1,c2,c3,c4=st.columns(4)
        with c1: lr_db=st.number_input("Leads respondidos",value=int(db[15] if db else 0),min_value=0)
        with c2: trm_db=st.number_input("Tempo resp. médio min",value=int(db[16] if db else 0),min_value=0)
        with c3: ag_db=st.number_input("Agendamentos gerados",value=int(db[17] if db else 0),min_value=0)
        with c4: of_db=st.number_input("Orçamentos fechados",value=int(db[18] if db else 0),min_value=0)
        c1,c2,c3,c4,c5=st.columns(5)
        with c1: vof_db=st.number_input("Valor fechado R$",value=float(db[19] if db else 0),step=100.0)
        with c2: rfm_db=st.number_input("Contatos RFM",value=int(db[20] if db else 0),min_value=0)
        with c3: ind_s=st.number_input("Indicações solic.",value=int(db[21] if db else 0),min_value=0)
        with c4: ind_r=st.number_input("Indicações receb.",value=int(db[22] if db else 0),min_value=0)
        with c5: av_db=st.number_input("Avaliações Google",value=int(db[23] if db else 0),min_value=0)
        rfm_meta=bf_h[11] if bf_h else 30; ind_meta=bf_h[12] if bf_h else 5
        cols_s=st.columns(5)
        for col_s,(lbl_s,val_s,meta_s) in zip(cols_s,[("RFM",rfm_db,rfm_meta),("Indicações",ind_s,ind_meta),("Av.Google",av_db,5),("Resp<5min",100 if trm_db<=5 else 0,100),("Agendamentos",ag_db,2)]):
            p_s=pct_safe(val_s,meta_s); em_s,cor_s=semaforo(p_s)
            with col_s:
                st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:10px;padding:10px;text-align:center;font-size:11px">
                    <div style="color:{FG_MUTED}">{lbl_s}</div><div style="font-size:20px">{em_s}</div>
                    <div style="color:{cor_s};font-weight:600">{val_s}/{meta_s}</div>
                </div>""",unsafe_allow_html=True)
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:16px 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>04 — RÉGUA D-1/D+1 EXECUTADA</div>",unsafe_allow_html=True)
        c1,c2,c3=st.columns(3)
        with c1: dm1_ex=st.number_input("D-1 executados",value=int(db[24] if db else 0),min_value=0)
        with c2: dp1_ex=st.number_input("D+1 executados",value=int(db[25] if db else 0),min_value=0)
        with c3: fw_ex=st.number_input("Follow-ups executados",value=int(db[26] if db else 0),min_value=0)
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:16px 0 10px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>05 — ANÁLISE E PRÓXIMO DIA</div>",unsafe_allow_html=True)
        meta_bat=st.checkbox("Meta diária batida?",value=bool(db[27] if db else receita_d>=meta_dia))
        c1,c2=st.columns(2)
        with c1: conquista=st.text_input("Principal conquista",value=db[28] if db else "",placeholder="O que funcionou bem?")
        with c2: gargalo=st.text_input("Principal gargalo",value=db[29] if db else "",placeholder="O que travou ou desperdiçou?")
        c1,c2=st.columns([3,1])
        with c1: acao_am=st.text_input("Ação prioritária de amanhã",value=db[30] if db else "",placeholder="Já defina o próximo passo")
        with c2: dri_am=st.text_input("DRI de amanhã",value=db[31] if db else "")
        obs_db=st.text_area("Observações",value=db[32] if db else "",height=60)
        if st.form_submit_button("🌙 Registrar Fechamento do Dia",use_container_width=True):
            conn=get_conn()
            conn.execute("""INSERT INTO debriefing(data,responsavel,rc,rp,rr,ro,di,do_,da,cons_r,proc_r,ns,canc,perda_ns,leads_r,tempo_r,ag_g,orc_f,val_of,rfm_r,ind_s,ind_r,av_g,dm1_ex,dp1_ex,fw_ex,meta_bat,conquista,gargalo,acao_am,dri_am,obs)
                VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                ON CONFLICT(data) DO UPDATE SET responsavel=excluded.responsavel,rc=excluded.rc,rp=excluded.rp,rr=excluded.rr,ro=excluded.ro,di=excluded.di,do_=excluded.do_,da=excluded.da,cons_r=excluded.cons_r,proc_r=excluded.proc_r,ns=excluded.ns,canc=excluded.canc,perda_ns=excluded.perda_ns,leads_r=excluded.leads_r,tempo_r=excluded.tempo_r,ag_g=excluded.ag_g,orc_f=excluded.orc_f,val_of=excluded.val_of,rfm_r=excluded.rfm_r,ind_s=excluded.ind_s,ind_r=excluded.ind_r,av_g=excluded.av_g,dm1_ex=excluded.dm1_ex,dp1_ex=excluded.dp1_ex,fw_ex=excluded.fw_ex,meta_bat=excluded.meta_bat,conquista=excluded.conquista,gargalo=excluded.gargalo,acao_am=excluded.acao_am,dri_am=excluded.dri_am,obs=excluded.obs""",
            (hj,resp_db,rc_db,rp_db,rr_db,ro_db,di_db,do_db,da_db,cons_r,proc_r,ns_db,canc_db,perda_db,lr_db,trm_db,ag_db,of_db,vof_db,rfm_db,ind_s,ind_r,av_db,dm1_ex,dp1_ex,fw_ex,1 if meta_bat else 0,conquista,gargalo,acao_am,dri_am,obs_db))
            conn.execute("""INSERT INTO dre(mes,ano,receita_consultas,receita_procedimentos,receita_recorrencia,receita_outros,custo_insumos)
                VALUES(?,?,?,?,?,?,?) ON CONFLICT(mes,ano) DO UPDATE SET receita_consultas=receita_consultas+?,receita_procedimentos=receita_procedimentos+?,receita_recorrencia=receita_recorrencia+?,receita_outros=receita_outros+?,custo_insumos=custo_insumos+?""",
            (mes_sel,ano_sel,rc_db,rp_db,rr_db,ro_db,di_db,rc_db,rp_db,rr_db,ro_db,di_db))
            conn.commit();conn.close();st.success("Fechamento registrado! DRE mensal atualizado.");st.rerun()
    st.markdown("---")
    conn=get_conn(); hist_db=pd.read_sql("SELECT data,responsavel,(rc+rp+rr+ro) as receita,(di+do_+da) as despesas,cons_r,ns,rfm_r,ind_s,av_g,meta_bat,conquista,gargalo FROM debriefing ORDER BY data DESC LIMIT 7",conn); conn.close()
    if not hist_db.empty:
        hist_db["receita"]=hist_db["receita"].apply(fmt); hist_db["despesas"]=hist_db["despesas"].apply(fmt)
        hist_db["meta_bat"]=hist_db["meta_bat"].apply(lambda x:"✅" if x else "⚠️")
        hist_db.columns=["Data","DRI","Receita","Despesas","Consultas","No-show","RFM","Indicações","Av.Google","Meta","Conquista","Gargalo"]
        st.dataframe(hist_db,hide_index=True,use_container_width=True)
    else: st.info("Nenhum debriefing registrado ainda.")

# ══════════════════════════════════════════════════════════════
# 4. PAINEL DNA SEMANAL
# ══════════════════════════════════════════════════════════════
    # ── Exportar relatório ───────────────────────────────────────
    try:
        _secoes_debriefing = [("Debriefing", [f"Data: {hj_fmt}", "Caixa registrado com sucesso"])]
        _txt_debriefing = "\n".join([f"{l}" for _,ls in _secoes_debriefing for l in ls])
        bloco_exportar("Debriefing", _secoes_debriefing, _txt_debriefing)
    except Exception as _ex:
        st.caption(f"Exportar: {_ex}")


elif aba=="📊  Painel DNA Semanal":
    sw=f"S{date.today().isocalendar()[1]}"
    st.markdown(titulo_secao("Painel de Metas Semanais DNA","Quem sabe o número fecha o número. Preencha toda segunda-feira."),unsafe_allow_html=True)
    conn=get_conn(); dna=conn.execute("SELECT * FROM painel_dna WHERE semana=? AND ano=?",(sw,ano_sel)).fetchone(); clin_r=conn.execute("SELECT * FROM clinica WHERE id=1").fetchone(); conn.close()
    meta_m_d=clin_r[2] if clin_r else 0
    with st.expander("✏️ Preencher Painel da Semana",expanded=not bool(dna)):
        with st.form("form_dna"):
            st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin-bottom:12px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>A LÓGICA QUE MUDA O JOGO</div>",unsafe_allow_html=True)
            c1,c2,c3=st.columns(3)
            with c1: meta_d=st.number_input("Meta Mensal R$",value=float(dna[3] if dna else meta_m_d),step=1000.0); realiz=st.number_input("Já realizado R$",value=float(dna[4] if dna else 0),step=100.0); dias_r=st.number_input("Dias úteis restantes",value=int(dna[5] if dna else 5),min_value=1,max_value=25)
            with c2: cv=st.number_input("01 Consultas ag. R$",value=float(dna[6] if dna else 0),step=100.0); pv=st.number_input("02 Procedimentos ag. R$",value=float(dna[7] if dna else 0),step=100.0)
            with c3: nv=st.number_input("03 Negociações R$",value=float(dna[8] if dna else 0),step=100.0); ov=st.number_input("04 Orçamentos R$",value=float(dna[9] if dna else 0),step=100.0)
            st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:16px 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>ACOMPANHAMENTO DIÁRIO</div>",unsafe_allow_html=True)
            dcols=st.columns(5); vd=[]
            for i,(dc,dn) in enumerate(zip(dcols,["SEG","TER","QUA","QUI","SEX"])):
                with dc:
                    st.markdown(f"<div style='color:{FG};font-weight:600;text-align:center;font-size:11px;margin-bottom:4px'>{dn}</div>",unsafe_allow_html=True)
                    b=10+(i*3)
                    c_=st.number_input(f"C{dn}",value=float(dna[b] if dna else 0),step=100.0,key=f"dc{i}",label_visibility="collapsed")
                    p_=st.number_input(f"P{dn}",value=float(dna[b+1] if dna else 0),step=100.0,key=f"dp{i}",label_visibility="collapsed")
                    n_=st.number_input(f"N{dn}",value=float(dna[b+2] if dna else 0),step=100.0,key=f"dn{i}",label_visibility="collapsed")
                    vd.extend([c_,p_,n_])
            if st.form_submit_button("💾 Salvar Painel da Semana"):
                conn=get_conn()
                conn.execute("""INSERT INTO painel_dna(semana,ano,meta_mensal,realizado_mes,dias_uteis_restantes,consultas_v,procedimentos_v,negociacoes_v,orcamentos_v,seg_c,seg_p,seg_n,ter_c,ter_p,ter_n,qua_c,qua_p,qua_n,qui_c,qui_p,qui_n,sex_c,sex_p,sex_n)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?,?)
                    ON CONFLICT(semana,ano) DO UPDATE SET meta_mensal=excluded.meta_mensal,realizado_mes=excluded.realizado_mes,dias_uteis_restantes=excluded.dias_uteis_restantes,consultas_v=excluded.consultas_v,procedimentos_v=excluded.procedimentos_v,negociacoes_v=excluded.negociacoes_v,orcamentos_v=excluded.orcamentos_v,seg_c=excluded.seg_c,seg_p=excluded.seg_p,seg_n=excluded.seg_n,ter_c=excluded.ter_c,ter_p=excluded.ter_p,ter_n=excluded.ter_n,qua_c=excluded.qua_c,qua_p=excluded.qua_p,qua_n=excluded.qua_n,qui_c=excluded.qui_c,qui_p=excluded.qui_p,qui_n=excluded.qui_n,sex_c=excluded.sex_c,sex_p=excluded.sex_p,sex_n=excluded.sex_n""",
                (sw,ano_sel,meta_d,realiz,dias_r,cv,pv,nv,ov,*vd))
                conn.commit();conn.close();st.success("Painel salvo!");st.rerun()
    if dna:
        meta_m_d=dna[3] or 0; realiz=dna[4] or 0; dias_r=dna[5] or 5
        cv=dna[6] or 0; pv=dna[7] or 0; nv=dna[8] or 0; ov=dna[9] or 0
        total_prev=cv+pv+nv+ov; falta_buscar=(meta_m_d/4)-total_prev
        meta_diaria=max((meta_m_d-realiz)/max(dias_r,1),0)
        st.markdown("---")
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;font-size:14px;margin-bottom:14px'>AS 3 PERGUNTAS QUE REVELAM ONDE VOCÊ ESTÁ DE VERDADE</div>",unsafe_allow_html=True)
        c1,c2,c3=st.columns(3)
        with c1: st.markdown(card("01 — Receita travada esta semana",fmt(total_prev),"Consultas+Procedimentos+Neg.+Orç.",GREEN),unsafe_allow_html=True)
        with c2: st.markdown(card("02 — Pode entrar com follow-up hoje",fmt(nv+ov),"Negociações quentes + Orçamentos",YELL_SOFT),unsafe_allow_html=True)
        with c3: st.markdown(card("03 — Ainda precisa gerar do zero",fmt(max(falta_buscar,0)),f"Meta semanal menos previsto",RED_SOFT if falta_buscar>0 else GREEN,grande=True),unsafe_allow_html=True)
        st.markdown(f"""<div style="background:{BG_DEEP};border:1px solid {BORDER_ACC};border-radius:16px;padding:22px 28px;text-align:center;margin:16px 0">
            <div style="color:{FG_MUTED};font-size:11px;letter-spacing:0.15em;text-transform:uppercase;margin-bottom:8px">O ÚNICO NÚMERO QUE VOCÊ CONTROLA AGORA</div>
            <div style="color:{ACCENT};font-size:3rem;font-weight:600;letter-spacing:-0.03em">{fmt(meta_diaria)}</div>
            <div style="color:{FG_MUTED};font-size:12px;margin-top:6px">Meta Diária de Ritmo — {dias_r} dias úteis restantes</div>
        </div>""",unsafe_allow_html=True)
        st.markdown(f"<div style='color:{FG};font-weight:600;margin:16px 0 8px;font-size:13px'>Acompanhamento Diário</div>",unsafe_allow_html=True)
        dias_data=[]
        for i,dia in enumerate(["SEG","TER","QUA","QUI","SEX"]):
            b=10+(i*3); c_v=dna[b] or 0; p_v=dna[b+1] or 0; n_v=dna[b+2] or 0; tot_dia=c_v+p_v+n_v
            dias_data.append({"Dia":dia,"Consultas":fmt(c_v),"Procedimentos":fmt(p_v),"Negociações":fmt(n_v),"Total":fmt(tot_dia)})
        st.dataframe(pd.DataFrame(dias_data),hide_index=True,use_container_width=True)

# ══════════════════════════════════════════════════════════════
# 5. AUDITORIA DE SALAS
# ══════════════════════════════════════════════════════════════
    # ── Exportar relatório ───────────────────────────────────────
    try:
        _secoes_painel_dna = [("Painel DNA", [f"Meta mensal: {fmt(meta_m_d)}", f"Total previsto: {fmt(total_prev)}", f"Meta diária: {fmt(meta_diaria)}"])]
        _txt_painel_dna = "\n".join([f"{l}" for _,ls in _secoes_painel_dna for l in ls])
        bloco_exportar("Painel DNA", _secoes_painel_dna, _txt_painel_dna)
    except Exception as _ex:
        st.caption(f"Exportar: {_ex}")


elif aba=="🏥  Auditoria de Salas":
    st.markdown(titulo_secao("Auditoria de Eficiência das Salas","Inventário de tempo perecível. Hora não vendida não volta."),unsafe_allow_html=True)
    conn=get_conn(); salas_df=pd.read_sql("SELECT * FROM salas WHERE mes=? AND ano=?",conn,params=(mes_sel,ano_sel)); conn.close()
    with st.expander("➕ Registrar Ocupação de Sala"):
        with st.form("form_sala"):
            c1,c2,c3=st.columns(3)
            with c1: nome_s=st.text_input("Nome da sala"); medico_s=st.text_input("Médico responsável")
            with c2: hd_s=st.number_input("Horas disponíveis",value=8.0,step=0.5); ho_s=st.number_input("Horas ocupadas",value=0.0,step=0.5)
            with c3: ns_s=st.number_input("No-shows",value=0,min_value=0); tk_s=st.number_input("Ticket/hora R$",value=0.0,step=10.0)
            if st.form_submit_button("Salvar"):
                if nome_s:
                    conn=get_conn(); conn.execute("INSERT INTO salas(nome,medico,horas_disp,horas_ocup,no_show,perda,ticket_hora,mes,ano) VALUES(?,?,?,?,?,?,?,?,?)",(nome_s,medico_s,hd_s,ho_s,ns_s,ns_s*tk_s,tk_s,mes_sel,ano_sel)); conn.commit();conn.close();st.rerun()
    if salas_df.empty: st.info("Nenhuma sala registrada para este período.")
    else:
        salas_df['tx_ocup']=(salas_df['horas_ocup']/salas_df['horas_disp']*100).round(1).fillna(0)
        for _,s in salas_df.iterrows():
            tx=s['tx_ocup']; cor_s=GREEN if tx>=85 else YELL_SOFT if tx>=50 else RED_SOFT
            alerta="⚡ Ocupação crítica: considere subir preço ou contratar assistente." if tx>=85 else ("💡 Alta ociosidade: acionar base RFM para protocolos nesta sala." if (100-tx)>=50 else "")
            st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:16px;padding:18px 22px;margin-bottom:14px;box-shadow:0 0 0 1px rgba(255,255,255,0.04),0 4px 24px rgba(0,0,0,0.4)">
                <div style="display:flex;justify-content:space-between;align-items:flex-start">
                    <div><div style="font-weight:600;color:{FG};font-size:15px">{s['nome']}</div>
                        <div style="font-size:12px;color:{FG_MUTED}">{s['medico']} · Ticket/hora: {fmt(s['ticket_hora'])}</div></div>
                    <div style="text-align:right"><div style="font-size:28px;font-weight:600;color:{cor_s}">{tx:.1f}%</div>
                        <div style="font-size:11px;color:{FG_MUTED}">ocupação</div></div>
                </div>
                <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px;margin:12px 0">
                    {''.join([f'<div style="background:{BG_DEEP};border:1px solid {BORDER};border-radius:10px;padding:10px;text-align:center"><div style="font-size:10px;color:{FG_MUTED};text-transform:uppercase;letter-spacing:0.1em">{lb_c}</div><div style="font-size:18px;font-weight:600;color:{cr_c}">{vl_c}</div></div>' for lb_c,vl_c,cr_c in [("Disponíveis",f"{s['horas_disp']}h",FG),("Ocupadas",f"{s['horas_ocup']}h",GREEN),("No-Shows",str(int(s['no_show'])),RED_SOFT),("Perda",fmt(s['perda']),RED_SOFT)]])}
                </div>
                <div style="height:4px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden;margin-bottom:8px">
                    <div style="height:4px;width:{min(int(tx),100)}%;background:{cor_s};border-radius:99px"></div>
                </div>
                {f'<div style="background:{cor_s}11;border:1px solid {cor_s}33;border-radius:8px;padding:8px 12px;font-size:12px;color:{cor_s}">{alerta}</div>' if alerta else ''}
            </div>""",unsafe_allow_html=True)
        total_perda=salas_df['perda'].sum()
        if total_perda>0:
            st.markdown(f"""<div style="background:rgba(248,113,113,0.08);border:1px solid rgba(248,113,113,0.25);border-radius:10px;padding:14px 18px;margin-top:8px">
                <span style="color:{RED_SOFT};font-weight:600">Total prejuízo oculto no período: {fmt(total_perda)}</span>
                <span style="color:{FG_MUTED};font-size:12px"> — dinheiro que saiu pela porta sem atendimento</span>
            </div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 6. COMERCIAL & SDR
# ══════════════════════════════════════════════════════════════
    # ── Exportar relatório ───────────────────────────────────────
    try:
        _secoes_auditoria_de_salas = [("Auditoria de Salas", [f"Total salas: {len(salas_df)}", f"Perda no-show: {fmt(total_perda) if not salas_df.empty else 'R$ 0,00'}"])]
        _txt_auditoria_de_salas = "\n".join([f"{l}" for _,ls in _secoes_auditoria_de_salas for l in ls])
        bloco_exportar("Auditoria de Salas", _secoes_auditoria_de_salas, _txt_auditoria_de_salas)
    except Exception as _ex:
        st.caption(f"Exportar: {_ex}")


elif aba=="📈  Comercial & SDR":
    st.markdown(titulo_secao("Comercial & SDR","Os 9 Gargalos das Vendas Médicas — funil com método"),unsafe_allow_html=True)
    conn=get_conn(); leads_df=pd.read_sql("SELECT * FROM leads WHERE mes=? AND ano=? ORDER BY id DESC",conn,params=(mes_sel,ano_sel)); conn.close()
    tot=len(leads_df); ag=int(leads_df[leads_df['status'].isin(['Agendado','Compareceu','Convertido'])].shape[0]) if not leads_df.empty else 0
    comp=int(leads_df['compareceu'].sum()) if not leads_df.empty else 0
    conv=int(leads_df['convertido'].sum()) if not leads_df.empty else 0
    resp5=int((leads_df['tempo_resp']<=5).sum()) if not leads_df.empty else 0
    tx_vel=pct_safe(resp5,tot)
    st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:16px;padding:20px 24px;margin-bottom:20px;box-shadow:0 0 0 1px rgba(255,255,255,0.04),0 4px 24px rgba(0,0,0,0.4)">
        <div style="color:{ACCENT};font-size:11px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:14px">FUNIL SPIN — DA CAPTAÇÃO À CONVERSÃO</div>
        <div style="display:grid;grid-template-columns:repeat(5,1fr);gap:1px;background:{BORDER};border-radius:8px;overflow:hidden">
            {''.join([f'<div style="background:{BG_ELEV};padding:16px;text-align:center"><div style="color:{FG_MUTED};font-size:9px;text-transform:uppercase;letter-spacing:0.1em">{lb}</div><div style="color:{cr};font-size:26px;font-weight:600;margin:4px 0">{vl}</div><div style="color:{cr};font-size:12px;font-weight:500">{tx}</div></div>' for lb,vl,tx,cr in [("Leads",tot,"100%",FG_MUTED),("Agendados",ag,f"{pct_safe(ag,tot):.0f}%",YELL_SOFT),("Compareceram",comp,f"{pct_safe(comp,ag):.0f}%",YELL_SOFT),("Convertidos",conv,f"{pct_safe(conv,tot):.0f}% final",GREEN),("Resp.<5min",resp5,f"{tx_vel:.0f}%",GREEN if tx_vel>=80 else RED_SOFT)]])}
        </div>
    </div>""",unsafe_allow_html=True)
    col_orig,col_mot=st.columns(2)
    with col_orig:
        st.markdown(f"<div style='color:{FG};font-weight:600;margin-bottom:10px;font-size:13px'>Origem dos Leads</div>",unsafe_allow_html=True)
        if not leads_df.empty:
            for _,row in leads_df.groupby('canal').size().reset_index(name='n').sort_values('n',ascending=False).iterrows():
                st.markdown(barra(pct_safe(row['n'],tot),f"{row['canal']}: {row['n']} leads",ACCENT),unsafe_allow_html=True)
        else: st.info("Sem leads neste período.")
    with col_mot:
        st.markdown(f"<div style='color:{FG};font-weight:600;margin-bottom:10px;font-size:13px'>Motivos de Perda</div>",unsafe_allow_html=True)
        if not leads_df.empty and leads_df['motivo'].any():
            perdas=leads_df[leads_df['motivo']!=''].groupby('motivo').size().reset_index(name='qtd')
            if not perdas.empty:
                for _,row in perdas.iterrows(): st.markdown(barra(pct_safe(row['qtd'],tot),f"{row['motivo']}: {row['qtd']}",RED_SOFT),unsafe_allow_html=True)
            else: st.info("Registre motivos de perda nos leads.")
        else: st.info("Sem motivos de perda registrados.")
    with st.expander("📋 Scripts Padrão da Clínica"):
        sc_sel=st.selectbox("Script",list(SCRIPTS_PADRAO.keys())); st.code(SCRIPTS_PADRAO[sc_sel],language=None)
    with st.expander("➕ Adicionar Lead"):
        with st.form("form_lead"):
            c1,c2,c3,c4=st.columns(4)
            with c1: nome_l=st.text_input("Nome")
            with c2: canal_l=st.selectbox("Canal",["Instagram","Indicação","Google","WhatsApp","Tráfego Pago","Offline","Outro"])
            with c3: sdr_l=st.selectbox("SDR",["Aline","Bianca","Beatriz"])
            with c4: tk_l=st.number_input("Ticket R$",min_value=0.0,step=50.0)
            c5,c6,c7,c8=st.columns(4)
            with c5: status_l=st.selectbox("Status",["Novo","Qualificado","Agendado","Compareceu","Convertido","Descartado"])
            with c6: temp_l=st.selectbox("Temperatura",["Quente","Morno","Frio"])
            with c7: resp_l=st.number_input("Tempo resp. min",min_value=0,value=0)
            with c8: conv_l=st.checkbox("Convertido")
            c1,c2=st.columns(2)
            with c1: comp_l=st.checkbox("Compareceu")
            with c2: motivo_l=st.text_input("Motivo de perda")
            if st.form_submit_button("➕ Adicionar"):
                if nome_l:
                    conn=get_conn(); conn.execute("INSERT INTO leads(nome,canal,sdr,status,temperatura,tempo_resp,compareceu,convertido,ticket,motivo,mes,ano) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(nome_l,canal_l,sdr_l,status_l,temp_l,resp_l,1 if comp_l else 0,1 if conv_l else 0,tk_l,motivo_l or '',mes_sel,ano_sel)); conn.commit();conn.close();st.success(f"Lead '{nome_l}' adicionado!");st.rerun()
    if not leads_df.empty:
        st.markdown(f"<div style='color:{FG};font-weight:600;margin:12px 0 8px;font-size:13px'>Leads — {mes_sel}/{ano_sel}</div>",unsafe_allow_html=True)
        st.dataframe(leads_df[['nome','canal','sdr','status','temperatura','tempo_resp','compareceu','convertido','ticket']],hide_index=True,use_container_width=True,column_config={"ticket":st.column_config.NumberColumn("Ticket",format="R$ %.2f"),"compareceu":st.column_config.CheckboxColumn("Comp."),"convertido":st.column_config.CheckboxColumn("Conv.")})

# ══════════════════════════════════════════════════════════════
# 7. ORÇAMENTOS
# ══════════════════════════════════════════════════════════════
    # ── Exportar Comercial ──────────────────────────────────────
    try:
        _sec_com=[("Comercial e SDR",[f"Total leads: {tot}",f"Agendados: {ag} ({pct_safe(ag,tot):.0f}%)",f"Convertidos: {conv} ({pct_safe(conv,tot):.0f}%)",f"Resp <5min: {resp5} ({tx_vel:.0f}%)"])]
        _txt_com="\n".join([l for _,ls in _sec_com for l in ls])
        bloco_exportar("Comercial e SDR",_sec_com,_txt_com)
    except Exception as _ex:
        st.caption(f"Exportar: {_ex}")


elif aba=="💰  Orçamentos":
    st.markdown(titulo_secao("Controle de Orçamentos","Orçamento quente sem ação em 24h gera alerta. (DRI: Bianca)"),unsafe_allow_html=True)
    conn=get_conn(); odf=pd.read_sql("SELECT * FROM orcamentos ORDER BY criado_em DESC",conn); conn.close()
    if not odf.empty:
        qt=odf[(odf['temperatura']=='Quente')&(odf['status']=='Aberto')&(odf['proxima_acao']=='')]
        if len(qt)>0: st.error(f"🚨 {len(qt)} orçamento(s) QUENTE(S) sem próxima ação — Bianca, ligar agora!")
    with st.expander("➕ Adicionar Orçamento"):
        with st.form("form_orc"):
            c1,c2,c3,c4=st.columns(4)
            with c1: pac_o=st.text_input("Paciente")
            with c2: val_o=st.number_input("Valor R$",min_value=0.0,step=100.0)
            with c3: temp_o=st.selectbox("Temperatura",["Quente","Morno","Frio","Perdido"])
            with c4: dri_o=st.selectbox("DRI",["Bianca","Gerente"])
            c1,c2,c3=st.columns(3)
            with c1: data_e=st.date_input("Data envio",value=date.today())
            with c2: prox_a=st.text_input("Próxima ação")
            with c3: prazo_o=st.date_input("Prazo",value=date.today()+timedelta(days=1))
            obj_o=st.text_input("Objeção principal")
            if st.form_submit_button("Salvar"):
                if pac_o:
                    conn=get_conn(); conn.execute("INSERT INTO orcamentos(paciente,valor,data_envio,temperatura,objecao,proxima_acao,dri,prazo) VALUES(?,?,?,?,?,?,?,?)",(pac_o,val_o,data_e.isoformat(),temp_o,obj_o,prox_a,dri_o,prazo_o.isoformat())); conn.commit();conn.close();st.rerun()
    if not odf.empty:
        c1,c2,c3,c4=st.columns(4)
        for col_t,temp_t,cor_t in [(c1,"Quente",RED_SOFT),(c2,"Morno",YELL_SOFT),(c3,"Frio",FG_MUTED),(c4,"Perdido","rgba(255,255,255,0.3)")]:
            with col_t:
                sub_df=odf[odf['temperatura']==temp_t]
                st.markdown(card(temp_t,fmt(sub_df['valor'].sum()),f"{len(sub_df)} orçamentos",cor_t),unsafe_allow_html=True)
        st.dataframe(odf[['paciente','valor','data_envio','temperatura','objecao','proxima_acao','dri','prazo','status']],hide_index=True,use_container_width=True,column_config={"valor":st.column_config.NumberColumn("Valor",format="R$ %.2f")})
        with st.form("form_upd_orc"):
            orc_id=st.selectbox("Atualizar",odf['id'].tolist(),format_func=lambda x:odf[odf['id']==x]['paciente'].values[0])
            c1,c2,c3=st.columns(3)
            with c1: nt=st.selectbox("Temperatura",["Quente","Morno","Frio","Perdido"])
            with c2: ns_o=st.selectbox("Status",["Aberto","Fechado","Perdido"])
            with c3: npa=st.text_input("Nova próxima ação")
            if st.form_submit_button("Atualizar"):
                conn=get_conn(); conn.execute("UPDATE orcamentos SET temperatura=?,status=?,proxima_acao=? WHERE id=?",(nt,ns_o,npa,orc_id)); conn.commit();conn.close();st.rerun()

# ══════════════════════════════════════════════════════════════
# 8. RFM & INDICAÇÕES
# ══════════════════════════════════════════════════════════════
elif aba=="🔄  RFM & Indicações":
    st.markdown(titulo_secao("RFM & Indicações","30 contatos RFM/dia · 5 indicações solicitadas/dia. (DRI: Beatriz + Bianca)"),unsafe_allow_html=True)
    tab_rfm,tab_ind=st.tabs(["MATRIZ RFM","INDICAÇÕES"])
    with tab_rfm:
        conn=get_conn(); rdf=pd.read_sql("SELECT * FROM rfm ORDER BY criado_em DESC",conn); conn.close()
        st.markdown(kpi_grid([("Meta Diária RFM","30 contatos","Paciente reativado custa 5x menos que lead novo",ACCENT),("Meta Indicações","5 pedidos/dia","Lead de indicação converte 3x mais",GREEN)]),unsafe_allow_html=True)
        with st.expander("➕ Adicionar Paciente RFM"):
            with st.form("form_rfm"):
                c1,c2,c3,c4=st.columns(4)
                with c1: pac_r=st.text_input("Paciente")
                with c2: uv_r=st.date_input("Última visita",value=date.today()-timedelta(days=90))
                with c3: freq_r=st.number_input("Frequência",min_value=0,value=0)
                with c4: val_r=st.number_input("Total investido R$",min_value=0.0,step=100.0)
                c1,c2,c3=st.columns(3)
                with c1: seg_r=st.selectbox("Segmento",["Alto valor","Médio","Inativo recente","Inativo antigo"])
                with c2: dri_r=st.selectbox("DRI",["Beatriz","Bianca"])
                with c3: prox_r=st.text_input("Próxima ação")
                if st.form_submit_button("Salvar"):
                    if pac_r:
                        conn=get_conn(); conn.execute("INSERT INTO rfm(paciente,ultima_visita,frequencia,valor_total,segmento,dri,proxima_acao) VALUES(?,?,?,?,?,?,?)",(pac_r,uv_r.isoformat(),freq_r,val_r,seg_r,dri_r,prox_r)); conn.commit();conn.close();st.rerun()
        if not rdf.empty:
            for seg,cor_sg in [("Alto valor",GREEN),("Médio",YELL_SOFT),("Inativo recente",ACCENT),("Inativo antigo",FG_MUTED)]:
                g=rdf[rdf['segmento']==seg]
                if g.empty: continue
                st.markdown(f"<div style='color:{cor_sg};font-weight:600;font-size:12px;text-transform:uppercase;letter-spacing:0.05em;margin:12px 0 6px'>{seg} — {len(g)} pacientes</div>",unsafe_allow_html=True)
                for _,rw in g.iterrows():
                    st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:10px;padding:10px 14px;margin-bottom:6px;display:flex;justify-content:space-between;align-items:center">
                        <div><strong style="color:{FG}">{rw['paciente']}</strong> <span style="font-size:11px;color:{FG_MUTED}">· Última: {rw['ultima_visita']} · {rw['frequencia']}x · {fmt(rw['valor_total'])}</span></div>
                        <div style="text-align:right"><div style="font-size:11px;color:{FG_MUTED}">DRI: {rw['dri']}</div><div style="font-size:12px;font-weight:500;color:{ACCENT}">{rw['proxima_acao'] or '—'}</div></div>
                    </div>""",unsafe_allow_html=True)
    with tab_ind:
        conn=get_conn(); idf=pd.read_sql("SELECT * FROM indicacoes ORDER BY criado_em DESC",conn); conn.close()
        with st.expander("➕ Registrar Indicação"):
            with st.form("form_ind"):
                c1,c2,c3,c4=st.columns(4)
                with c1: ir=st.text_input("Paciente indicador")
                with c2: id_=st.text_input("Paciente indicado")
                with c3: ct=st.text_input("Contato")
                with c4: di=st.selectbox("DRI",["Aline","Bianca"])
                if st.form_submit_button("Registrar"):
                    if ir and id_:
                        conn=get_conn(); conn.execute("INSERT INTO indicacoes(pac_indicador,pac_indicado,contato,data_ind,dri) VALUES(?,?,?,?,?)",(ir,id_,ct,date.today().isoformat(),di)); conn.commit();conn.close();st.rerun()
        if not idf.empty:
            conv_i=int(idf['convertido'].sum()); tx_i=pct_safe(conv_i,len(idf))
            st.markdown(kpi_grid([("Total Indicações",str(len(idf)),"todos os tempos",FG),("Convertidas",str(conv_i),f"{tx_i:.0f}% de conversão",GREEN),("Pendentes",str(len(idf)-conv_i),"aguardando contato",YELL_SOFT)]),unsafe_allow_html=True)
            st.dataframe(idf[['pac_indicador','pac_indicado','data_ind','status','dri','convertido']],hide_index=True,use_container_width=True,column_config={"convertido":st.column_config.CheckboxColumn("Conv.")})

# ══════════════════════════════════════════════════════════════
# 9. RÉGUAS D-1 / D+1
# ══════════════════════════════════════════════════════════════
elif aba=="📋  Réguas D-1 / D+1":
    st.markdown(titulo_secao("Réguas D-1 / D+1","A entrega começa um dia antes e segue um dia depois. (DRI: Beatriz + Paloma)"),unsafe_allow_html=True)
    st.markdown(f"""<div style="display:grid;grid-template-columns:1fr 1fr;gap:14px;margin-bottom:20px">
        <div style="background:{SURF};border:1px solid {BORDER_ACC};border-radius:16px;padding:18px;box-shadow:0 0 0 1px rgba(255,255,255,0.04),0 4px 24px rgba(0,0,0,0.4)">
            <div style="color:{ACCENT};font-size:11px;font-weight:600;letter-spacing:0.1em;margin-bottom:8px;text-transform:uppercase">D-1 — A VÉSPERA</div>
            <div style="color:{FG};font-size:13px;font-weight:600;margin-bottom:6px">Primeira Consulta</div>
            <div style="color:{FG_MUTED};font-size:12px;line-height:1.8">① Mensagem de boas-vindas com assinatura da clínica<br>② Alinhamento de expectativas (tempo, preparo)<br>③ Envio do questionário pré-consulta<br>④ Convocação do decisor (cônjuge/acompanhante)<br>⑤ Geração de expectativas positivas</div>
            <div style="color:{ACCENT};font-size:11px;font-weight:600;margin-top:10px;letter-spacing:0.1em;text-transform:uppercase">Retorno</div>
            <div style="color:{FG_MUTED};font-size:12px;line-height:1.8;margin-top:4px">① Reativar vínculo pelo nome<br>② Alinhar expectativas do retorno<br>③ Confirmar realização dos exames<br>④ Convocar decisor (foco em fechamento)<br>⑤ Sinalizar clareza do plano de conduta</div>
        </div>
        <div style="background:{SURF};border:1px solid rgba(74,222,128,0.2);border-radius:16px;padding:18px;box-shadow:0 0 0 1px rgba(255,255,255,0.04),0 4px 24px rgba(0,0,0,0.4)">
            <div style="color:{GREEN};font-size:11px;font-weight:600;letter-spacing:0.1em;margin-bottom:8px;text-transform:uppercase">D+1 — O DIA SEGUINTE</div>
            <div style="color:{FG};font-size:13px;font-weight:600;margin-bottom:6px">Primeira Consulta (Beatriz)</div>
            <div style="color:{FG_MUTED};font-size:12px;line-height:1.8">① Mensagem de direcionamento e agradecimento<br>② Importância dos exames solicitados<br>③ Alinhamento do tempo de retorno<br>④ Repetir exames e especificidades<br>⑤ Retorno já agendado (regra, não exceção)</div>
            <div style="color:{GREEN};font-size:11px;font-weight:600;margin-top:10px;letter-spacing:0.1em;text-transform:uppercase">Retorno (Beatriz)</div>
            <div style="color:{FG_MUTED};font-size:12px;line-height:1.8;margin-top:4px">① Mensagem de direcionamento<br>② Reforçar importância do protocolo<br>③ Reexplicar tratamentos propostos<br>④ Retorno agendado confirmado<br>⑤ 2 vouchers para indicação ativa</div>
        </div>
    </div>""",unsafe_allow_html=True)
    st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:16px;padding:16px 20px;margin-bottom:20px">
        <div style="color:{ACCENT};font-size:11px;font-weight:600;letter-spacing:0.1em;margin-bottom:10px;text-transform:uppercase">RÉGUA DE FOLLOW-UP — ORÇAMENTOS ABERTOS (DRI: Bianca)</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:10px">
            {''.join([f'<div style="background:{BG_DEEP};border:1px solid {BORDER};border-radius:10px;padding:12px;text-align:center"><div style="color:{ACCENT};font-size:18px;font-weight:600">{d}</div><div style="color:{FG_MUTED};font-size:11px">{ds}</div></div>' for d,ds in [("D+1","Primeiro contato"),("D+3","Esclarecer dúvidas"),("D+7","Reforço de valor"),("D+14","Reativação final")]])}
        </div>
    </div>""",unsafe_allow_html=True)
    conn=get_conn(); rg_df=pd.read_sql("SELECT * FROM regua ORDER BY data_cons DESC",conn); conn.close()
    with st.expander("➕ Adicionar Paciente na Régua"):
        with st.form("form_regua"):
            c1,c2,c3,c4=st.columns(4)
            with c1: nm_rg=st.text_input("Paciente")
            with c2: tp_rg=st.selectbox("Tipo",["Primeira Consulta","Retorno"])
            with c3: dt_rg=st.date_input("Data",value=date.today())
            with c4: tk_rg=st.number_input("Ticket R$",min_value=0.0,step=50.0)
            if st.form_submit_button("Adicionar"):
                if nm_rg:
                    conn=get_conn(); conn.execute("INSERT INTO regua(paciente,tipo,data_cons,ticket) VALUES(?,?,?,?)",(nm_rg,tp_rg,dt_rg.isoformat(),tk_rg)); conn.commit();conn.close();st.rerun()
    if not rg_df.empty:
        st.dataframe(rg_df[['paciente','tipo','data_cons','st_dm1','st_dp1','st_dp3','st_dp7','st_dp14','ticket','fechou']],hide_index=True,use_container_width=True,column_config={"ticket":st.column_config.NumberColumn("Ticket",format="R$ %.2f"),"fechou":st.column_config.CheckboxColumn("Fechou")})
        pend=rg_df[rg_df['fechou']==0]
        if not pend.empty:
            st.markdown(f"""<div style="background:rgba(94,106,210,0.08);border:1px solid {BORDER_ACC};border-radius:8px;padding:10px 14px;margin-top:8px">
                <span style="color:{ACCENT};font-weight:600">Pipeline na régua: {fmt(pend['ticket'].sum())}</span>
                <span style="color:{FG_MUTED};font-size:12px"> em {len(pend)} pacientes aguardando follow-up</span>
            </div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 10. PROGRAMA INTEGRA
# ══════════════════════════════════════════════════════════════
elif aba=="🎓  Programa Integra":
    st.markdown(titulo_secao("Programa Integra — MOD & Onboarding","Score de execução diária por colaborador. Meta: acima de 85%."),unsafe_allow_html=True)
    conn=get_conn(); colabs=pd.read_sql("SELECT * FROM colaboradores WHERE ativo=1",conn); tarefas_df=pd.read_sql("SELECT * FROM mod_tarefas WHERE ativo=1 ORDER BY cargo_key,bloco,horario",conn); conn.close()
    tab_mod,tab_pont,tab_on=st.tabs(["MOD POR FUNÇÃO","PONTUAÇÃO SEMANAL","ONBOARDING 90 DIAS"])
    with tab_mod:
        col_colab,col_mod=st.columns([1,2])
        with col_colab:
            st.markdown(f"<div style='color:{FG};font-weight:600;margin-bottom:12px;font-size:13px'>Equipe Ativa</div>",unsafe_allow_html=True)
            if colabs.empty: st.info("Cadastre colaboradores em Configurações."); colab_sel="Sem colaborador"
            else: colab_sel=st.selectbox("Colaborador:",colabs['nome'].tolist(),label_visibility="collapsed")
            # Onboarding rápido
            st.markdown(f"<div style='color:{FG};font-weight:600;margin:16px 0 10px;font-size:13px'>Trilha de Onboarding</div>",unsafe_allow_html=True)
            modulos=[("Módulo 1","Cultura & Posicionamento Premium"),("Módulo 2","Métricas de Sala & Sistemas"),("Módulo 3","Scripts D-1/D+1 & Follow-up"),("Módulo 4","Vendas High-Ticket & Objeções")]
            concl=0
            for i,(cod,desc) in enumerate(modulos):
                conn=get_conn(); on_r=conn.execute("SELECT concluido FROM onboarding WHERE colaborador_id=(SELECT id FROM colaboradores WHERE nome=? LIMIT 1) AND modulo=?",(colab_sel,cod)).fetchone(); conn.close()
                chk=st.checkbox(f"{cod}: {desc}",value=bool(on_r and on_r[0]),key=f"on_{i}")
                if chk: concl+=1
                if chk and not (on_r and on_r[0]):
                    conn=get_conn(); cid_r=conn.execute("SELECT id FROM colaboradores WHERE nome=?",(colab_sel,)).fetchone()
                    if cid_r: conn.execute("INSERT OR REPLACE INTO onboarding(colaborador_id,modulo,fase,concluido,data_conclusao) VALUES(?,?,1,1,?)",(cid_r[0],cod,date.today().isoformat())); conn.commit()
                    conn.close()
            prog_on=concl/len(modulos); st.progress(prog_on,text=f"Progresso: {int(prog_on*100)}%")
            if prog_on<1.0: st.warning("Bônus travado. Onboarding incompleto.")
            else: st.success("Onboarding completo. Bônus liberado.")
        with col_mod:
            st.markdown(f"<div style='color:{FG};font-weight:600;margin-bottom:12px;font-size:13px'>Auditoria MOD — {colab_sel}</div>",unsafe_allow_html=True)
            if tarefas_df.empty: st.info("Nenhuma tarefa no MOD.")
            else:
                cargo_key_sel=colabs[colabs['nome']==colab_sel]['cargo_key'].values[0] if not colabs[colabs['nome']==colab_sel].empty else ''
                tf=tarefas_df[tarefas_df['cargo_key']==cargo_key_sel] if cargo_key_sel else tarefas_df
                score_total=0
                for bloco in ["Abertura","Durante","Fechamento"]:
                    tb=tf[tf['bloco']==bloco]
                    if tb.empty: continue
                    cor_bl={("Abertura",ACCENT),("Durante",YELL_SOFT),("Fechamento",FG_MUTED)}.pop() if False else (ACCENT if bloco=="Abertura" else YELL_SOFT if bloco=="Durante" else FG_MUTED)
                    st.markdown(f"<div style='color:{cor_bl};font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;margin:12px 0 6px'>{bloco} · {tb.iloc[0]['horario']}</div>",unsafe_allow_html=True)
                    for _,t in tb.iterrows():
                        conn=get_conn(); ex=conn.execute("SELECT concluida FROM mod_execucao WHERE tarefa_id=? AND colaborador=? AND data_exec=?",(t['id'],colab_sel,date.today().isoformat())).fetchone(); conn.close()
                        ja=bool(ex and ex[0])
                        chk_t=st.checkbox(f"{t['titulo']} (Peso: {t['peso']}%)",value=ja,key=f"t_{t['id']}_{colab_sel}")
                        if chk_t: score_total+=t['peso']
                        if chk_t and not ja:
                            conn=get_conn(); conn.execute("INSERT OR REPLACE INTO mod_execucao(tarefa_id,colaborador,data_exec,concluida) VALUES(?,?,?,1)",(t['id'],colab_sel,date.today().isoformat())); conn.commit();conn.close()
                        st.markdown(f"<div style='font-size:10px;color:{FG_MUTED};margin:-6px 0 4px 20px'>📦 {t['dri']}</div>",unsafe_allow_html=True)
                score_total=min(score_total,100); _,cor_sc=semaforo(score_total)
                st.markdown(f"""<div style="background:{BG_DEEP};border:1px solid {BORDER_ACC};border-radius:16px;padding:20px;text-align:center;margin-top:16px">
                    <div style="color:{FG_MUTED};font-size:10px;letter-spacing:0.15em;text-transform:uppercase">SCORE DE EXECUÇÃO DIÁRIA</div>
                    <div style="font-size:3rem;font-weight:600;color:{cor_sc};margin:4px 0;letter-spacing:-0.03em">{score_total}%</div>
                    <div style="color:{FG_MUTED};font-size:12px">{"✅ Zona de Genialidade — meta batida" if score_total>=85 else "⚠️ Abaixo da meta crítica de 85%"}</div>
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
                if st.form_submit_button("Adicionar"):
                    if tit_t:
                        conn=get_conn(); conn.execute("INSERT INTO mod_tarefas(titulo,cargo_key,responsavel,dri,bloco,horario,frequencia,categoria,peso) VALUES(?,?,?,?,?,?,?,?,?)",(tit_t,ck_t,CARGO_MAP[ck_t],dri_t,bl_t,hr_t,"Diaria","Operacional",peso_t)); conn.commit();conn.close();st.rerun()
    with tab_pont:
        sw=f"S{date.today().isocalendar()[1]}"
        st.markdown(f"<div style='font-size:12px;color:{FG_MUTED};margin-bottom:12px'>{sw}/{ano_sel} — Pontuação máxima: 100 pontos</div>",unsafe_allow_html=True)
        if colabs.empty: st.info("Cadastre colaboradores primeiro.")
        else:
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
                        if st.form_submit_button("Salvar"):
                            conn=get_conn(); conn.execute("INSERT INTO integra_pont(colaborador_id,semana,ano,entregas,qualidade,cultura,indicadores,melhoria,obs) VALUES(?,?,?,?,?,?,?,?,?) ON CONFLICT(colaborador_id,semana,ano) DO UPDATE SET entregas=excluded.entregas,qualidade=excluded.qualidade,cultura=excluded.cultura,indicadores=excluded.indicadores,melhoria=excluded.melhoria,obs=excluded.obs",(colab['id'],sw,ano_sel,nv['entregas'],nv['qualidade'],nv['cultura'],nv['indicadores'],nv['melhoria'],obs_p)); conn.commit();conn.close();st.rerun()
                    tn=sum(nv.values()) if nv else total_p
                    acao=("Reconhecimento público e expansão de responsabilidades." if tn>=85 else "Colaborador sólido. Reforçar pontos fortes." if tn>=70 else "Identificar 1 ponto de melhoria para esta semana." if tn>=50 else "Apoio intensivo. Plano de ação imediato. Reunião 1:1 esta semana.")
                    _,cor_tn=semaforo(tn)
                    st.markdown(f"<div style='background:{cor_tn}11;border:1px solid {cor_tn}33;border-radius:8px;padding:10px 14px;margin-top:8px;font-size:12px;color:{cor_tn}'>{nivel_p} — {tn}/100 — {acao}</div>",unsafe_allow_html=True)
    with tab_on:
        colab_on=st.selectbox("Colaborador",EQUIPE,key="on_sel2")
        conn=get_conn(); cid_r2=conn.execute("SELECT id FROM colaboradores WHERE nome=?",(colab_on,)).fetchone(); conn.close()
        cid2=cid_r2[0] if cid_r2 else 1
        fases=[(1,"ACOLHER — Dias 1 a 7",ACCENT,["Apresentar equipe, espaço e manifesto da clínica","Leitura comentada dos valores","Explicar Projeto Ponteiro e Programa Integra","Mostrar jornada completa do paciente","Apresentar sistemas: Support Health, Kommo, Galileu"]),
               (2,"APRENDER — Dias 8 a 30",YELL_SOFT,["Treinar MOD da função (abertura, meio e fechamento)","Treinar scripts SBAR e comunicação","Treinar uso do CRM com supervisão","Executar rotina com acompanhamento próximo"]),
               (3,"EXECUTAR — Dias 31 a 60",GREEN,["Executar MOD com autonomia supervisionada","Registrar evidências de execução diariamente","Atingir primeiros indicadores do cargo","Participar ativamente do checkpoint diário"]),
               (4,"MELHORAR — Dias 61 a 90",FG_MUTED,["Propor ao menos 1 melhoria de processo documentada","Reduzir retrabalho na função","Assumir indicadores próprios","Reunião 1:1 com plano de metas da semana"]),
               (5,"CRESCER — Após 90 dias",FG,["Assumir mais responsabilidade na função","Treinar colaboradores novos","Propor melhorias estratégicas"])]
        for fn,nm_f,cor_f,tarefas_f in fases:
            st.markdown(f"<div style='color:{cor_f};font-weight:600;font-size:11px;text-transform:uppercase;letter-spacing:0.05em;margin:12px 0 6px'>{nm_f}</div>",unsafe_allow_html=True)
            for tf in tarefas_f:
                conn=get_conn(); on_r=conn.execute("SELECT concluido FROM onboarding WHERE colaborador_id=? AND modulo=? AND fase=?",(cid2,tf,fn)).fetchone(); conn.close()
                chk_f=st.checkbox(tf,value=bool(on_r and on_r[0]),key=f"on2_{fn}_{tf[:20]}_{cid2}")
                if chk_f and not (on_r and on_r[0]):
                    conn=get_conn(); conn.execute("INSERT OR REPLACE INTO onboarding(colaborador_id,modulo,fase,concluido,data_conclusao) VALUES(?,?,?,1,?)",(cid2,tf,fn,date.today().isoformat())); conn.commit();conn.close()

# ══════════════════════════════════════════════════════════════
# 11. SEGURANÇA ASSISTENCIAL
# ══════════════════════════════════════════════════════════════
elif aba=="🩻  Segurança Assistencial":
    st.markdown(titulo_secao("Segurança Assistencial","Checklist por paciente. Evolução no dia. D+1 obrigatório. (DRI: Paloma)"),unsafe_allow_html=True)
    conn=get_conn(); sg_df=pd.read_sql("SELECT * FROM seguranca ORDER BY data_atend DESC LIMIT 20",conn); conn.close()
    if not sg_df.empty:
        sem_d1=sg_df[(sg_df['d1_enviado']==0)&(pd.to_datetime(sg_df['data_atend'])<pd.Timestamp(date.today().isoformat()))]
        if len(sem_d1)>0: st.error(f"🚨 {len(sem_d1)} paciente(s) sem D+1 enviado — Paloma, enviar agora até 10h!")
    with st.expander("➕ Registrar Atendimento"):
        with st.form("form_seg"):
            c1,c2,c3=st.columns(3)
            with c1: pac_s=st.text_input("Paciente")
            with c2: dt_s=st.date_input("Data",value=date.today())
            with c3: resp_s=st.text_input("Responsável",value="Paloma")
            st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:12px 0 6px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>Checklist de Segurança</div>",unsafe_allow_html=True)
            c1,c2=st.columns(2)
            with c1:
                ch1=st.checkbox("Injetáveis e materiais conferidos na bancada")
                ch2=st.checkbox("Nome, LOTE e VALIDADE conferidos NA FRENTE do paciente")
                ch3=st.checkbox("Protocolo preparado por ordem de pH")
                ch4=st.checkbox("Alergia verificada e protocolo explicado")
            with c2:
                ch5=st.checkbox("Assinatura do registro ANTES de iniciar")
                ch6=st.checkbox("Evolução técnica registrada no mesmo dia")
                ch7=st.checkbox("Sinalização para Beatriz agendar próxima sessão")
                inter=st.checkbox("🚨 Ocorreu intercorrência?")
            desc_inter=""
            if inter: desc_inter=st.text_area("Descreva a intercorrência")
            if st.form_submit_button("Registrar"):
                if pac_s:
                    conn=get_conn(); conn.execute("INSERT INTO seguranca(paciente,data_atend,responsavel,ch1,ch2,ch3,ch4,ch5,ch6,ch7,intercorrencia,desc_inter) VALUES(?,?,?,?,?,?,?,?,?,?,?,?)",(pac_s,dt_s.isoformat(),resp_s,1 if ch1 else 0,1 if ch2 else 0,1 if ch3 else 0,1 if ch4 else 0,1 if ch5 else 0,1 if ch6 else 0,1 if ch7 else 0,1 if inter else 0,desc_inter)); conn.commit();conn.close()
                    if inter: st.error("🚨 INTERCORRÊNCIA registrada! Vá ao módulo SBAR e notifique Dra. Bárbara imediatamente.")
                    else: st.success("Atendimento registrado!");st.rerun()
    with st.expander("✅ Registrar D+1"):
        with st.form("form_d1"):
            conn=get_conn(); psD1=pd.read_sql("SELECT * FROM seguranca WHERE d1_enviado=0 ORDER BY data_atend DESC LIMIT 20",conn); conn.close()
            if not psD1.empty:
                pid=st.selectbox("Paciente",psD1['id'].tolist(),format_func=lambda x:psD1[psD1['id']==x]['paciente'].values[0])
                resp_d1=st.text_area("Resposta do paciente")
                if st.form_submit_button("Marcar D+1 enviado"):
                    conn=get_conn(); conn.execute("UPDATE seguranca SET d1_enviado=1,d1_resposta=? WHERE id=?",(resp_d1,pid)); conn.commit();conn.close();st.success("D+1 registrado!");st.rerun()
            else: st.success("Todos os D+1 enviados! ✅")
    if not sg_df.empty:
        st.markdown("---")
        st.dataframe(sg_df[['paciente','data_atend','responsavel','ch1','ch2','ch6','ch7','intercorrencia','d1_enviado']],hide_index=True,use_container_width=True,column_config={k:st.column_config.CheckboxColumn(k) for k in ['ch1','ch2','ch6','ch7','intercorrencia','d1_enviado']})

# ══════════════════════════════════════════════════════════════
# 12. SBAR
# ══════════════════════════════════════════════════════════════
elif aba=="📣  SBAR":
    st.markdown(titulo_secao("SBAR — Comunicação Estruturada","Toda ocorrência relevante segue esse padrão. Sem SBAR, é rumor."),unsafe_allow_html=True)
    st.markdown(f"""<div style="display:grid;grid-template-columns:repeat(4,1fr);gap:1px;background:{BORDER};border-radius:12px;overflow:hidden;margin-bottom:20px">
        {''.join([f'<div style="background:{BG_ELEV};padding:16px"><div style="font-size:1.2rem;font-weight:600;color:{cor_s}">{lt}</div><div style="font-size:10px;font-weight:600;text-transform:uppercase;letter-spacing:0.1em;color:{cor_s};margin:4px 0">{nm}</div><div style="font-size:11px;color:{FG_MUTED}">{ds}</div></div>' for lt,nm,ds,cor_s in [("S","SITUAÇÃO","O que está acontecendo agora?",RED_SOFT),("B","BACKGROUND","Contexto e histórico",ACCENT),("A","AVALIAÇÃO","Sua leitura do problema",YELL_SOFT),("R","RECOMENDAÇÃO","Próximo passo com DRI e prazo",GREEN)]])}
    </div>""",unsafe_allow_html=True)
    with st.expander("➕ Criar SBAR",expanded=True):
        with st.form("form_sbar"):
            c1,c2,c3=st.columns(3)
            with c1: tp_sb=st.selectbox("Tipo",["Resumo Diário (Gerente→CEO)","Evento Adverso Clínico","Problema Operacional","Pedido de Apoio","Alerta Comercial"])
            with c2: rem_sb=st.selectbox("Remetente",EQUIPE)
            with c3: dest_sb=st.selectbox("Destinatário",["Dr. Vinícius Mariano","Dra. Bárbara Mariano","Vanessa","Bianca"])
            sit_sb=st.text_area("S — SITUAÇÃO: O que está acontecendo agora?",height=80)
            bg_sb=st.text_area("B — BACKGROUND: Contexto e histórico",height=80)
            av_sb=st.text_area("A — AVALIAÇÃO: Sua leitura do problema",height=80)
            c1,c2,c3=st.columns(3)
            with c1: rec_sb=st.text_area("R — RECOMENDAÇÃO",height=80)
            with c2: dri_sb=st.selectbox("DRI da ação",EQUIPE)
            with c3: prazo_sb=st.text_input("Prazo",value="Hoje até 18h")
            if st.form_submit_button("Enviar SBAR"):
                if sit_sb:
                    conn=get_conn(); conn.execute("INSERT INTO sbar(tipo,remetente,destinatario,situacao,background,avaliacao,recomendacao,dri_acao,prazo) VALUES(?,?,?,?,?,?,?,?,?)",(tp_sb,rem_sb,dest_sb,sit_sb,bg_sb,av_sb,rec_sb,dri_sb,prazo_sb)); conn.commit();conn.close();st.success(f"SBAR enviado para {dest_sb}!");st.rerun()
    with st.expander("📋 Template SBAR Diário"):
        st.code(SCRIPTS_PADRAO["Script 9 — SBAR diário (Gerente → Dr. Vinícius | até 18h)"],language=None)
    conn=get_conn(); sb_df=pd.read_sql("SELECT * FROM sbar ORDER BY data DESC LIMIT 20",conn); conn.close()
    if not sb_df.empty:
        st.markdown("---")
        pend_sb=sb_df[sb_df['resolvido']==0]
        if len(pend_sb)>0: st.warning(f"{len(pend_sb)} SBAR(s) pendente(s) de resolução.")
        for _,sb in sb_df.iterrows():
            bg_sb2="rgba(251,191,36,0.04)" if not sb['resolvido'] else "transparent"
            st.markdown(f"""<div style="background:{bg_sb2};border:1px solid {BORDER};border-radius:12px;padding:14px;margin-bottom:8px">
                <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                    <strong style="color:{FG};font-size:13px">{sb['tipo']}</strong>
                    <span style="font-size:11px;color:{FG_MUTED}">{sb['remetente']} → {sb['destinatario']} · {sb['data'][:10]}</span>
                </div>
                <div style="font-size:12px;line-height:1.8;color:{FG_MUTED}">
                    <strong style="color:{RED_SOFT}">S:</strong> {sb['situacao']}<br>
                    <strong style="color:{ACCENT}">B:</strong> {sb['background']}<br>
                    <strong style="color:{YELL_SOFT}">A:</strong> {sb['avaliacao']}<br>
                    <strong style="color:{GREEN}">R:</strong> {sb['recomendacao']} — DRI: <strong style="color:{FG}">{sb['dri_acao']}</strong> · Prazo: {sb['prazo']}
                </div>
                {'<div style="color:'+GREEN+';font-size:11px;font-weight:500;margin-top:6px">✅ Resolvido</div>' if sb['resolvido'] else ''}
            </div>""",unsafe_allow_html=True)
            if not sb['resolvido']:
                if st.button("Marcar como resolvido",key=f"res_{sb['id']}"):
                    conn=get_conn(); conn.execute("UPDATE sbar SET resolvido=1 WHERE id=?",(sb['id'],)); conn.commit();conn.close();st.rerun()

# ══════════════════════════════════════════════════════════════
# 13. FINANCEIRO & EBITDA
# ══════════════════════════════════════════════════════════════
elif aba=="💰  Financeiro & EBITDA":
    st.markdown(titulo_secao("Financeiro & EBITDA","DRE Gerencial completo. Faturamento sem margem é ilusão."),unsafe_allow_html=True)
    conn=get_conn(); dre_r=conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone(); hist=pd.read_sql("SELECT mes,ano,(receita_consultas+receita_procedimentos+receita_recorrencia+receita_outros) as receita_bruta,(custo_pessoal+custo_ocupacao+custo_marketing+custo_outros) as custos_fixos,custo_insumos FROM dre ORDER BY ano,mes LIMIT 12",conn); conn.close()
    with st.expander("✏️ Lançar DRE do Mês",expanded=not bool(dre_r)):
        with st.form("form_dre"):
            st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin-bottom:12px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>RECEITAS</div>",unsafe_allow_html=True)
            c1,c2,c3,c4=st.columns(4)
            with c1: rc=st.number_input("Consultas R$",value=float(dre_r[3] if dre_r else 0),step=100.0)
            with c2: rp=st.number_input("Procedimentos R$",value=float(dre_r[4] if dre_r else 0),step=100.0)
            with c3: rr=st.number_input("Recorrência LTV R$",value=float(dre_r[5] if dre_r else 0),step=100.0)
            with c4: ro=st.number_input("Outros R$",value=float(dre_r[6] if dre_r else 0),step=100.0)
            st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:12px 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>DEDUÇÕES</div>",unsafe_allow_html=True)
            c1,c2=st.columns(2)
            with c1: imp_d=st.number_input("Impostos %",value=float(dre_r[7] if dre_r else 8.5),step=0.1)
            with c2: tc_d=st.number_input("Taxa Cartão %",value=float(dre_r[8] if dre_r else 3.0),step=0.1)
            st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin:12px 0 8px;font-size:12px;text-transform:uppercase;letter-spacing:0.05em'>CUSTOS</div>",unsafe_allow_html=True)
            c1,c2,c3,c4,c5=st.columns(5)
            with c1: ins_d=st.number_input("Insumos R$",value=float(dre_r[9] if dre_r else 0),step=100.0)
            with c2: pes_d=st.number_input("Pessoal R$",value=float(dre_r[10] if dre_r else 0),step=100.0)
            with c3: oc_d=st.number_input("Ocupação R$",value=float(dre_r[11] if dre_r else 0),step=100.0)
            with c4: mk_d=st.number_input("Marketing R$",value=float(dre_r[12] if dre_r else 0),step=100.0)
            with c5: ou_d=st.number_input("Outros R$",value=float(dre_r[13] if dre_r else 0),step=100.0)
            if st.form_submit_button("💾 Salvar DRE"):
                conn=get_conn(); conn.execute("""INSERT INTO dre(mes,ano,receita_consultas,receita_procedimentos,receita_recorrencia,receita_outros,imposto_pct,taxa_cartao_pct,custo_insumos,custo_pessoal,custo_ocupacao,custo_marketing,custo_outros)
                    VALUES(?,?,?,?,?,?,?,?,?,?,?,?,?) ON CONFLICT(mes,ano) DO UPDATE SET receita_consultas=excluded.receita_consultas,receita_procedimentos=excluded.receita_procedimentos,receita_recorrencia=excluded.receita_recorrencia,receita_outros=excluded.receita_outros,imposto_pct=excluded.imposto_pct,taxa_cartao_pct=excluded.taxa_cartao_pct,custo_insumos=excluded.custo_insumos,custo_pessoal=excluded.custo_pessoal,custo_ocupacao=excluded.custo_ocupacao,custo_marketing=excluded.custo_marketing,custo_outros=excluded.custo_outros""",
                (mes_sel,ano_sel,rc,rp,rr,ro,imp_d,tc_d,ins_d,pes_d,oc_d,mk_d,ou_d)); conn.commit();conn.close();st.success("DRE salvo!");st.rerun()
    if dre_r:
        rb=sum([dre_r[i] or 0 for i in [3,4,5,6]]); imp=dre_r[7] or 8.5; tc=dre_r[8] or 3.0
        ins=dre_r[9] or 0; pes=dre_r[10] or 0; oc=dre_r[11] or 0; mk=dre_r[12] or 0; ou=dre_r[13] or 0
        ded=rb*(imp+tc)/100; rl=rb-ded; mc=rl-ins; cf=pes+oc+mk+ou; ebitda=mc-cf; mg_eb=pct_safe(ebitda,rb)
        pe=cf/(1-(imp+tc)/100) if (1-(imp+tc)/100)>0 else 0
        st.markdown("---")
        st.markdown(f"<div style='color:{ACCENT};font-weight:600;font-size:13px;letter-spacing:0.05em;margin-bottom:14px;text-transform:uppercase'>DRE GERENCIAL CONSOLIDADO — {mes_sel}/{ano_sel}</div>",unsafe_allow_html=True)
        for lbl_d,val_d,pct_d,cor_d,dest_d in [
            ("(+) FATURAMENTO BRUTO",rb,100.0,GREEN,False),
            (f"   Consultas",dre_r[3] or 0,pct_safe(dre_r[3] or 0,rb),FG_MUTED,False),
            (f"   Procedimentos",dre_r[4] or 0,pct_safe(dre_r[4] or 0,rb),FG_MUTED,False),
            (f"   Recorrência LTV",dre_r[5] or 0,pct_safe(dre_r[5] or 0,rb),FG_MUTED,False),
            (f"(-) Impostos + Taxas Cartão",ded,pct_safe(ded,rb),RED_SOFT,False),
            ("(=) RECEITA LÍQUIDA OPERACIONAL",rl,pct_safe(rl,rb),FG,True),
            ("(-) Custos Variáveis (Insumos)",ins,pct_safe(ins,rb),RED_SOFT,False),
            ("(=) MARGEM DE CONTRIBUIÇÃO",mc,pct_safe(mc,rb),YELL_SOFT,True),
            ("(-) Custos Fixos Totais",cf,pct_safe(cf,rb),RED_SOFT,False),
            ("   Folha de Pessoal",pes,pct_safe(pes,rb),FG_MUTED,False),
            ("   Ocupação / Aluguel",oc,pct_safe(oc,rb),FG_MUTED,False),
            ("   Marketing / Leads",mk,pct_safe(mk,rb),FG_MUTED,False),
            ("(=) EBITDA OPERACIONAL REAL",ebitda,mg_eb,GREEN if ebitda>0 else RED_SOFT,True),
        ]: st.markdown(dre_linha(lbl_d,val_d,pct_d,cor_d,dest_d),unsafe_allow_html=True)
        c1,c2,c3=st.columns(3)
        with c1: st.metric("Ponto de Equilíbrio",fmt(pe),"Faturamento mínimo")
        with c2: st.metric("Margem EBITDA",f"{mg_eb:.1f}%","Saúde operacional real")
        with c3: st.metric("Margem de Contribuição",f"{pct_safe(mc,rb):.1f}%","Após insumos variáveis")
        if not hist.empty:
            st.markdown(f"<div style='color:{FG};font-weight:600;margin:20px 0 10px;font-size:13px'>Evolução do EBITDA</div>",unsafe_allow_html=True)
            hist["período"]=hist["mes"]+"/"+hist["ano"].astype(str)
            st.bar_chart(hist.set_index("período")[["receita_bruta","custos_fixos","custo_insumos"]])

# ══════════════════════════════════════════════════════════════
# 14. OKRs
# ══════════════════════════════════════════════════════════════
    # ── Exportar Financeiro ──────────────────────────────────────
    try:
        if dre_r:
            _sec_fin=[("Financeiro e EBITDA",[f"Receita Bruta: {fmt(rb)}",f"EBITDA: {fmt(ebitda)}",f"Margem EBITDA: {margem_ebitda:.1f}%",f"Ponto Equilíbrio: {fmt(pe)}"])]
            _txt_fin="\n".join([l for _,ls in _sec_fin for l in ls])
            bloco_exportar("Financeiro e EBITDA",_sec_fin,_txt_fin)
    except Exception as _ex:
        st.caption(f"Exportar: {_ex}")


elif aba=="📐  OKRs":
    st.markdown(titulo_secao("OKRs — Objetivos e Resultados-Chave","Objectives conectados à execução diária. Sem OKR, sem direção."),unsafe_allow_html=True)
    conn=get_conn(); okdf=pd.read_sql("SELECT * FROM okrs WHERE ativo=1 ORDER BY trimestre,objetivo",conn); conn.close()
    with st.expander("➕ Adicionar OKR"):
        with st.form("form_okr"):
            c1,c2=st.columns(2)
            with c1: obj_o=st.text_input("Objetivo (O que queremos alcançar?)"); kr_o=st.text_input("Key Result (Como medimos?)"); resp_o=st.selectbox("DRI",EQUIPE)
            with c2: meta_o=st.number_input("Meta",min_value=0.0,step=1.0); atu_o=st.number_input("Atual",min_value=0.0,step=1.0); tri_o=st.selectbox("Trimestre",["Q1","Q2","Q3","Q4"])
            if st.form_submit_button("Salvar OKR"):
                if obj_o:
                    conn=get_conn(); conn.execute("INSERT INTO okrs(objetivo,key_result,meta_val,atual_val,responsavel,trimestre,ano) VALUES(?,?,?,?,?,?,?)",(obj_o,kr_o,meta_o,atu_o,resp_o,tri_o,ano_sel)); conn.commit();conn.close();st.rerun()
    if okdf.empty: st.info("Sem OKRs cadastrados. Defina os objetivos do trimestre.")
    else:
        for tri in ["Q1","Q2","Q3","Q4"]:
            grupo=okdf[okdf["trimestre"]==tri]
            if grupo.empty: continue
            for obj in grupo["objetivo"].unique():
                krs=grupo[grupo["objetivo"]==obj]
                st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:16px;padding:18px 22px;margin-bottom:14px;box-shadow:0 0 0 1px rgba(255,255,255,0.04),0 4px 24px rgba(0,0,0,0.4)">
                    <div style="display:flex;justify-content:space-between;margin-bottom:14px">
                        <div style="color:{ACCENT};font-size:13px;font-weight:600">🎯 {obj}</div>
                        <div style="color:{FG_MUTED};font-size:11px">{tri} / {ano_sel}</div>
                    </div>""",unsafe_allow_html=True)
                for _,kr in krs.iterrows():
                    p_kr=pct_safe(kr['atual_val'],kr['meta_val']); _,cor_kr=semaforo(p_kr)
                    st.markdown(f"""<div style="background:{BG_DEEP};border:1px solid {BORDER};border-radius:10px;padding:12px 14px;margin-bottom:8px">
                        <div style="display:flex;justify-content:space-between;margin-bottom:8px">
                            <span style="color:{FG};font-size:13px">{kr['key_result']}</span>
                            <span style="color:{FG_MUTED};font-size:11px">DRI: {kr['responsavel']}</span>
                        </div>
                        <div style="display:flex;justify-content:space-between;font-size:11px;color:{FG_MUTED};margin-bottom:5px">
                            <span>Atual: {kr['atual_val']}</span><span style="color:{cor_kr};font-weight:600">{p_kr:.0f}%</span><span>Meta: {kr['meta_val']}</span>
                        </div>
                        <div style="height:4px;background:rgba(255,255,255,0.06);border-radius:99px;overflow:hidden">
                            <div style="height:4px;width:{min(int(p_kr),100)}%;background:{cor_kr};border-radius:99px"></div>
                        </div>
                    </div>""",unsafe_allow_html=True)
                st.markdown("</div>",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 15. IMPORTAR SUPPORT CLINIC
# ══════════════════════════════════════════════════════════════
    # ── Exportar OKRs ───────────────────────────────────────────
    try:
        if not okdf.empty:
            _sec_okr=[("OKRs Ativos",[f"{r['objetivo'][:40]} | KR: {r['key_result'][:30]} | {pct_safe(r['atual_val'],r['meta_val']):.0f}%" for _,r in okdf.iterrows()])]
            _txt_okr="\n".join([l for _,ls in _sec_okr for l in ls])
            bloco_exportar("OKRs",_sec_okr,_txt_okr)
    except Exception as _ex:
        st.caption(f"Exportar: {_ex}")


elif aba=="🧬  Importar Support Clinic":
    st.markdown(titulo_secao("Ingestão — Support Clinic","Arraste o relatório exportado. A IA lê, extrai e gera diagnóstico AME."),unsafe_allow_html=True)
    st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:16px;padding:18px 22px;margin-bottom:20px;box-shadow:0 0 0 1px rgba(255,255,255,0.04),0 4px 24px rgba(0,0,0,0.4)">
        <div style="color:{ACCENT};font-size:11px;font-weight:600;letter-spacing:0.1em;margin-bottom:14px;text-transform:uppercase">COMO EXPORTAR DO SUPPORT CLINIC</div>
        <div style="display:grid;grid-template-columns:repeat(4,1fr);gap:14px">
            {''.join([f'<div style="display:flex;gap:10px;align-items:flex-start"><div style="width:26px;height:26px;background:{ACCENT};border-radius:50%;display:flex;align-items:center;justify-content:center;color:{FG};font-weight:600;font-size:12px;flex-shrink:0">{n}</div><div><div style="font-size:13px;font-weight:500;color:{FG}">{t}</div><div style="font-size:11px;color:{FG_MUTED}">{d}</div></div></div>' for n,t,d in [(1,"Support Clinic","app.supportclinic.com.br"),(2,"Relatórios","Menu lateral → Relatórios"),(3,"Filtrar período","Selecione o mês desejado"),(4,"Exportar CSV","Exportar → CSV (formato ideal)")]])}
        </div>
    </div>""",unsafe_allow_html=True)
    arquivo=st.file_uploader("Arraste o arquivo do SupportClinic",type=["csv","txt","pdf","xlsx"])
    if arquivo:
        st.success(f"Arquivo recebido: **{arquivo.name}**")
        conteudo=""; df_prev=None
        try:
            if arquivo.name.endswith((".csv",".txt")):
                raw=arquivo.read()
                for enc in ["utf-8","latin-1","cp1252"]:
                    try: conteudo=raw.decode(enc); break
                    except: continue
                try:
                    df_prev=pd.read_csv(io.StringIO(conteudo),sep=None,engine='python',nrows=20)
                    st.dataframe(df_prev,use_container_width=True)
                except: st.code(conteudo[:600])
            elif arquivo.name.endswith(".xlsx"):
                df_prev=pd.read_excel(arquivo,nrows=20); conteudo=df_prev.to_csv(index=False); st.dataframe(df_prev,use_container_width=True)
            elif arquivo.name.endswith(".pdf"):
                conteudo=f"[PDF: {arquivo.name}]"; st.warning("PDF recebido. A IA vai analisar o conteúdo extraível.")
        except Exception as e: st.error(f"Erro ao ler arquivo: {e}")
        if conteudo and st.button("🧬 Processar com IA — Gerar Diagnóstico AME",use_container_width=True):
            api_key=st.secrets.get("ANTHROPIC_API_KEY",os.environ.get("ANTHROPIC_API_KEY",""))
            if not api_key: st.error("Configure ANTHROPIC_API_KEY nos Secrets do Streamlit.")
            else:
                with st.spinner("IA processando relatório e aplicando Método AME..."):
                    try:
                        client=anthropic.Anthropic(api_key=api_key)
                        msg=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=1800,messages=[{"role":"user","content":f"""Você é o consultor executivo do LAB Metrics — Método Ponteiro. Especialista em gestão de clínicas médicas premium.
Analise o relatório abaixo exportado do SupportClinic. Aplique o Método AME: Ação, Movimento e Entrega em cada recomendação.
RELATÓRIO ({arquivo.name}): {conteudo[:9000]}
Responda APENAS em JSON sem markdown:
{{"indicadores":{{"faturamento_bruto":null,"consultas_realizadas":null,"ticket_medio":null,"novos_pacientes":null,"procedimentos":null,"no_show":null,"taxa_conversao_pct":null}},"estagio_maturidade":"Caótico|Intuitivo|Documentado|Previsível","diagnostico_executivo":"texto direto máx 150 palavras","pontos_positivos":["p1","p2","p3"],"gargalos_identificados":["g1","g2","g3"],"plano_ame":[{{"acao":"...","movimento":"...","entrega":"...","dri":"...","prazo":"..."}}],"alerta_noshow":"texto sobre impacto financeiro do no-show se identificado"}}"""}])
                        raw=msg.content[0].text.strip().replace("```json","").replace("```","").strip()
                        res=json.loads(raw)
                        conn=get_conn()
                        conn.execute("INSERT INTO relatorios(nome_arquivo,conteudo,analise_ia,mes,ano) VALUES(?,?,?,?,?)",(arquivo.name,conteudo[:20000],json.dumps(res,ensure_ascii=False),mes_sel,ano_sel))
                        if res.get("indicadores",{}).get("faturamento_bruto"):
                            conn.execute("INSERT INTO dre(mes,ano,receita_outros) VALUES(?,?,?) ON CONFLICT(mes,ano) DO UPDATE SET receita_outros=excluded.receita_outros",(mes_sel,ano_sel,res["indicadores"]["faturamento_bruto"]))
                        if res.get("estagio_maturidade"):
                            conn.execute("UPDATE clinica SET estagio=? WHERE id=1",(res["estagio_maturidade"],))
                        conn.commit();conn.close()
                        # Indicadores
                        st.markdown("---")
                        st.markdown(f"<div style='color:{ACCENT};font-weight:600;margin-bottom:12px;font-size:13px;text-transform:uppercase;letter-spacing:0.05em'>INDICADORES EXTRAÍDOS</div>",unsafe_allow_html=True)
                        inds=res.get("indicadores",{})
                        cols_i=st.columns(7)
                        for i,(k,lbl) in enumerate(zip(["faturamento_bruto","consultas_realizadas","ticket_medio","novos_pacientes","procedimentos","no_show","taxa_conversao_pct"],["Faturamento","Consultas","Ticket Médio","Novos Pac.","Proced.","No-Show","Conversão %"])):
                            v=inds.get(k)
                            if v is not None:
                                with cols_i[i]: st.metric(lbl,fmt(v) if k in ["faturamento_bruto","ticket_medio"] else (f"{v}%" if "pct" in k else v))
                        # Diagnóstico
                        st.markdown(f"""<div style="background:{BG_DEEP};border:1px solid {BORDER_ACC};border-radius:16px;padding:22px 26px;margin:16px 0;box-shadow:0 0 0 1px rgba(255,255,255,0.04),0 4px 24px rgba(0,0,0,0.4)">
                            <div style="color:{ACCENT};font-size:11px;font-weight:600;letter-spacing:0.1em;margin-bottom:12px;text-transform:uppercase">DIAGNÓSTICO EXECUTIVO</div>
                            <div style="color:{FG};font-size:14px;line-height:1.85">{res.get('diagnostico_executivo','')}</div>
                        </div>""",unsafe_allow_html=True)
                        col_pos,col_gar=st.columns(2)
                        with col_pos:
                            st.markdown(f"<div style='color:{GREEN};font-weight:600;margin-bottom:8px;font-size:13px'>✅ Pontos Positivos</div>",unsafe_allow_html=True)
                            for p in res.get("pontos_positivos",[]): st.markdown(f"<div style='color:{FG_MUTED};font-size:13px;margin-bottom:5px'>→ {p}</div>",unsafe_allow_html=True)
                        with col_gar:
                            st.markdown(f"<div style='color:{RED_SOFT};font-weight:600;margin-bottom:8px;font-size:13px'>⚠️ Gargalos Identificados</div>",unsafe_allow_html=True)
                            for g in res.get("gargalos_identificados",[]): st.markdown(f"<div style='color:{FG_MUTED};font-size:13px;margin-bottom:5px'>→ {g}</div>",unsafe_allow_html=True)
                        st.markdown(f"<div style='color:{ACCENT};font-weight:600;font-size:14px;margin:20px 0 12px;text-transform:uppercase;letter-spacing:0.05em'>PLANO AME — 3 AÇÕES PRIORITÁRIAS</div>",unsafe_allow_html=True)
                        for i,ame in enumerate(res.get("plano_ame",[]),1):
                            st.markdown(f"""<div style="background:{SURF};border:1px solid {BORDER};border-radius:12px;padding:16px 20px;margin-bottom:10px;border-left:3px solid {ACCENT}">
                                <div style="display:flex;gap:12px">
                                    <div style="width:32px;height:32px;background:{ACCENT};border-radius:50%;display:flex;align-items:center;justify-content:center;color:{FG};font-weight:600;font-size:14px;flex-shrink:0">{i}</div>
                                    <div style="flex:1">
                                        <div style="color:{FG};font-weight:600;margin-bottom:6px;font-size:14px">AÇÃO: {ame.get('acao','')}</div>
                                        <div style="color:{FG_MUTED};font-size:12px;margin-bottom:4px"><strong style="color:{ACCENT}">MOVIMENTO:</strong> {ame.get('movimento','')}</div>
                                        <div style="color:{GREEN};font-size:12px;font-weight:500;margin-bottom:4px">📦 ENTREGA: {ame.get('entrega','')}</div>
                                        <div style="display:flex;gap:16px;font-size:11px"><span style="color:{FG_MUTED}">DRI: <strong style="color:{FG}">{ame.get('dri','')}</strong></span><span style="color:{FG_MUTED}">Prazo: <strong style="color:{YELL_SOFT}">{ame.get('prazo','')}</strong></span></div>
                                    </div>
                                </div>
                            </div>""",unsafe_allow_html=True)
                        if res.get("alerta_noshow"): st.warning(f"🚨 No-Show: {res['alerta_noshow']}")
                    except json.JSONDecodeError: st.markdown(f"<div style='color:{FG};font-size:14px;line-height:1.8'>{raw}</div>",unsafe_allow_html=True)
                    except Exception as e: st.error(f"Erro: {e}")
    st.markdown("---")
    st.markdown(f"<div style='color:{FG};font-weight:600;margin-bottom:10px;font-size:13px'>Histórico de Importações</div>",unsafe_allow_html=True)
    conn=get_conn(); hist_r=pd.read_sql("SELECT id,nome_arquivo,mes,ano,criado_em FROM relatorios ORDER BY criado_em DESC LIMIT 10",conn); conn.close()
    if not hist_r.empty: st.dataframe(hist_r,hide_index=True,use_container_width=True)
    else: st.info("Nenhum relatório importado ainda.")

# ══════════════════════════════════════════════════════════════
# 16. ASSISTENTE LAB METRICS — System Prompt completo
# ══════════════════════════════════════════════════════════════
elif aba=="🤖  Assistente LAB Metrics":
    st.markdown(titulo_secao("Assistente LAB Metrics","Consultor executivo digital da clínica. Powered by Projeto Ponteiro."),unsafe_allow_html=True)
    SYSTEM_PROMPT="""# IDENTIDADE DO AGENTE — LAB METRICS

## Quem você é
Você é o LAB Metrics, o assistente de gestão integrada de clínicas médicas. Você combina inteligência de dados com metodologia executiva para ajudar médicos gestores a tomar decisões mais rápidas, mais claras e mais lucrativas.

Você não é um chatbot genérico de saúde. Você é o consultor executivo digital da clínica, com visão simultânea de todos os setores: agenda, comercial, financeiro, equipe, marketing e indicadores.

Você conhece profundamente o Projeto Ponteiro, o Método AME, o MOD, o Programa Integra e o DNA Painel de Metas. Toda orientação que você oferece está baseada nessa metodologia.

Propósito da clínica que guia cada resposta: Despertar a Saúde Original em cada paciente através da medicina funcional e integrativa, com foco no ambiente microfuncional celular e no preparo do terreno metabólico. Nossa entrega não é consulta. É rota de cuidado.

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

## Equipe da Integrative Campinas
- Dr. Vinícius Mariano: CEO, estratégia, financeiro, RH e cultura
- Dra. Bárbara Mariano: Diretora Técnica, protocolos, qualidade e equipe assistencial
- Vanessa (Gerente Executiva): execução diária, agenda, indicadores e processos
- Bianca: Coordenadora Comercial e Closer, fechamento e orçamentos
- Aline: Analista de Leads, qualificação e follow-up (D+1/D+3/D+7/D+9/D+30)
- Beatriz: Recepção Comercial + RFM, agenda, confirmações, indicações e reativação
- Paloma: Enfermeira Assistencial, procedimentos, checklist de segurança e D+1 clínico

## Padrão mínimo de execução diária
- 1 reel + 1 post + mínimo 5 stories por dia
- 30 contatos RFM por dia (Beatriz)
- 5 solicitações de indicação por dia (toda equipe)
- 2 conversões lead em agendamento por dia (Aline)
- 100% dos leads respondidos em até 5 minutos (horário comercial)
- 5 avaliações Google por dia (Beatriz)
- SBAR diário da gerente para Dr. Vinícius até 18h

## Regra do almoço
O almoço da equipe comercial nunca acontece simultaneamente. Escala definida todo dia no checkpoint das 09h. O lead não sabe que é hora do almoço. A meta não para.

## Quatro motores de crescimento
Motor 1: Leads Novos. Tráfego pago, outdoor, conteúdo orgânico.
Motor 2: RFM. 30 contatos por dia. Paciente reativado custa 5x menos que lead novo.
Motor 3: Indicações. 5 solicitações por dia. Lead de indicação converte 3x mais.
Motor 4: Recorrência Terapêutica. Próxima etapa sempre definida na consulta.

## Princípios inegociáveis
1. Organizar antes de acelerar.
2. Fechar os furos do balde antes de aumentar o volume.
3. Faturamento sem margem vira ilusão.
4. Crescimento sem gestão vira ansiedade.
5. Equipe sem clareza vira retrabalho.
6. Estratégia sem execução vira palestra.
7. Pessoas certas nas funções certas.
8. Nenhuma tarefa sem dono. Nenhum indicador sem responsável.

## Regra de ouro
Nenhuma análise sem ação prática. Nenhuma ação sem responsável. Nenhum responsável sem prazo. Nenhum prazo sem indicador. Nenhum indicador sem revisão."""
    conn=get_conn()
    dre_ctx=conn.execute("SELECT * FROM dre WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone()
    clin_ctx=conn.execute("SELECT * FROM clinica WHERE id=1").fetchone()
    leads_ctx=conn.execute("SELECT COUNT(*),SUM(convertido),AVG(tempo_resp) FROM leads WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone()
    salas_ctx=conn.execute("SELECT AVG(horas_ocup*100.0/NULLIF(horas_disp,0)),SUM(perda) FROM salas WHERE mes=? AND ano=?",(mes_sel,ano_sel)).fetchone()
    conn.close()
    rb_ctx=sum([(dre_ctx[i] or 0) for i in [3,4,5,6]]) if dre_ctx else 0
    ebitda_ctx=0
    if dre_ctx:
        imp_c=dre_ctx[7] or 8.5; tc_c=dre_ctx[8] or 3.0
        rl_c=rb_ctx*(1-(imp_c+tc_c)/100); ins_c=dre_ctx[9] or 0
        cf_c=sum([(dre_ctx[i] or 0) for i in [10,11,12,13]]); ebitda_ctx=rl_c-ins_c-cf_c
    meta_ctx=clin_ctx[2] if clin_ctx else 0; estagio_ctx=clin_ctx[4] if clin_ctx and len(clin_ctx)>4 else "Intuitivo"
    l_tot_ctx=leads_ctx[0] or 0; l_conv_ctx=leads_ctx[1] or 0; resp_med=leads_ctx[2] or 0
    tx_conv_ctx=pct_safe(int(l_conv_ctx or 0),int(l_tot_ctx or 1))
    tx_ocup_ctx=salas_ctx[0] if salas_ctx and salas_ctx[0] else 0
    perda_ns_ctx=salas_ctx[1] if salas_ctx and salas_ctx[1] else 0
    contexto=f"""
DADOS ATUAIS DA CLÍNICA ({mes_sel}/{ano_sel}):
Nome: {clin_ctx[1] if clin_ctx else 'Integrative Campinas'} | Estágio: {estagio_ctx}
Faturamento: R$ {rb_ctx:,.2f} | Meta: R$ {meta_ctx:,.2f} | Atingimento: {pct_safe(rb_ctx,meta_ctx):.1f}%
EBITDA: R$ {ebitda_ctx:,.2f} | Margem: {pct_safe(ebitda_ctx,rb_ctx):.1f}%
Leads: {l_tot_ctx} | Convertidos: {int(l_conv_ctx or 0)} | Conversão: {tx_conv_ctx:.1f}%
Tempo médio resposta: {resp_med:.0f} min | Ocupação média salas: {tx_ocup_ctx:.1f}%
Prejuízo no-show: R$ {perda_ns_ctx:,.2f}
"""
    if "chat_history" not in st.session_state: st.session_state.chat_history=[]
    # KPIs do assistente
    st.markdown(kpi_grid([
        ("Faturamento",fmt(rb_ctx),f"{pct_safe(rb_ctx,meta_ctx):.0f}% da meta",GREEN if pct_safe(rb_ctx,meta_ctx)>=80 else YELL_SOFT),
        ("EBITDA",fmt(ebitda_ctx),f"{pct_safe(ebitda_ctx,rb_ctx):.1f}% margem",GREEN if ebitda_ctx>0 else RED_SOFT),
        ("Conv. Leads",f"{tx_conv_ctx:.1f}%",f"{int(l_conv_ctx or 0)} de {l_tot_ctx}",GREEN if tx_conv_ctx>=30 else RED_SOFT),
        ("Ocupação Salas",f"{tx_ocup_ctx:.1f}%","meta: 85%",GREEN if tx_ocup_ctx>=85 else YELL_SOFT if tx_ocup_ctx>=60 else RED_SOFT),
    ]),unsafe_allow_html=True)
    # Sugestões
    st.markdown(f"<div style='color:{FG_MUTED};font-size:11px;margin-bottom:10px;letter-spacing:0.1em;text-transform:uppercase'>Consultas rápidas</div>",unsafe_allow_html=True)
    sugestoes=["Qual meu principal gargalo agora?","Como fechar a meta do mês?","O que a equipe precisa fazer hoje?","Como melhorar minha conversão de leads?","Analise meu EBITDA e dê 3 ações.","Minha ocupação está baixa. O que fazer?","Como estruturar meu MOD semanal?","Qual motor de crescimento precisa de atenção?"]
    cols_s=st.columns(4)
    for i,sug in enumerate(sugestoes):
        with cols_s[i%4]:
            if st.button(sug,key=f"sug_{i}",use_container_width=True):
                st.session_state.chat_history.append({"role":"user","content":sug}); st.rerun()
    st.markdown("---")
    # Histórico visual
    for msg in st.session_state.chat_history:
        if msg["role"]=="user":
            st.markdown(f"""<div style="display:flex;justify-content:flex-end;margin-bottom:12px">
                <div style="background:{SURF};border:1px solid {BORDER};border-radius:16px 16px 2px 16px;padding:12px 16px;max-width:75%">
                    <div style="color:{FG};font-size:13px;line-height:1.6">{msg['content']}</div>
                </div>
            </div>""",unsafe_allow_html=True)
        else:
            st.markdown(f"""<div style="display:flex;justify-content:flex-start;margin-bottom:16px;gap:10px">
                <div style="width:32px;height:32px;background:linear-gradient(135deg,{ACCENT} 0%,{ACCENT_BR} 100%);border-radius:50%;display:flex;align-items:center;justify-content:center;font-size:14px;flex-shrink:0;margin-top:2px;box-shadow:0 0 10px rgba(94,106,210,0.3)">🩺</div>
                <div style="background:{SURF};border:1px solid {BORDER};border-radius:2px 16px 16px 16px;padding:14px 18px;max-width:80%;box-shadow:0 0 0 1px rgba(255,255,255,0.04),0 4px 24px rgba(0,0,0,0.4)">
                    <div style="color:{ACCENT};font-size:10px;font-weight:600;letter-spacing:0.1em;text-transform:uppercase;margin-bottom:8px">LAB METRICS</div>
                    <div style="color:{FG};font-size:13px;line-height:1.8;white-space:pre-wrap">{msg['content']}</div>
                </div>
            </div>""",unsafe_allow_html=True)
    if st.session_state.chat_history and st.session_state.chat_history[-1]["role"]=="user":
        api_key=st.secrets.get("ANTHROPIC_API_KEY",os.environ.get("ANTHROPIC_API_KEY",""))
        if not api_key: st.error("Configure ANTHROPIC_API_KEY nos Secrets.")
        else:
            with st.spinner("LAB Metrics analisando..."):
                try:
                    client=anthropic.Anthropic(api_key=api_key)
                    msgs_api=[]
                    for msg in st.session_state.chat_history:
                        if msg["role"]=="user" and msg==st.session_state.chat_history[-1]:
                            msgs_api.append({"role":"user","content":f"{contexto}\nPERGUNTA DO GESTOR:\n{msg['content']}"})
                        else: msgs_api.append(msg)
                    resp=client.messages.create(model="claude-sonnet-4-20250514",max_tokens=1000,system=SYSTEM_PROMPT,messages=msgs_api)
                    st.session_state.chat_history.append({"role":"assistant","content":resp.content[0].text}); st.rerun()
                except Exception as e: st.error(f"Erro: {e}")
    col_i,col_b,col_c=st.columns([6,1,1])
    with col_i: perg=st.text_input("Consultor",placeholder="Digite sua pergunta para o LAB Metrics...",label_visibility="collapsed",key="inp_chat")
    with col_b:
        if st.button("→",use_container_width=True) and perg.strip():
            st.session_state.chat_history.append({"role":"user","content":perg.strip()}); st.rerun()
    with col_c:
        if st.button("✕",use_container_width=True): st.session_state.chat_history=[]; st.rerun()
    if not st.session_state.chat_history:
        st.markdown(f"""<div style="background:{BG_DEEP};border:1px solid {BORDER};border-radius:16px;padding:32px;text-align:center;margin-top:20px;box-shadow:0 0 0 1px rgba(255,255,255,0.04),0 4px 24px rgba(0,0,0,0.4)">
            <div style="font-size:36px;margin-bottom:12px">🩺</div>
            <div style="color:{FG};font-size:16px;font-weight:600;letter-spacing:-0.02em;margin-bottom:8px">LAB Metrics — Consultor Executivo Digital</div>
            <div style="color:{FG_MUTED};font-size:13px;line-height:1.8;max-width:500px;margin:0 auto">Pergunte sobre agenda, faturamento, leads, equipe, marketing ou estratégia. Cada resposta termina em ação prática com responsável e prazo.</div>
            <div style="color:rgba(255,255,255,0.2);font-size:11px;margin-top:16px;font-style:italic">"Nenhuma análise sem ação prática. Nenhuma ação sem responsável."</div>
        </div>""",unsafe_allow_html=True)

# ══════════════════════════════════════════════════════════════
# 17. CONFIGURAÇÕES
# ══════════════════════════════════════════════════════════════
elif aba=="📱  WhatsApp":
    if HAS_WH:
        render_whatsapp_module()
    else:
        st.error("Módulo whatsapp_module.py não encontrado. Certifique-se que está na mesma pasta do app.py")

elif aba=="⚙️  Configurações":
    st.markdown(titulo_secao("Configurações","Clínica, equipe e integração com IA."),unsafe_allow_html=True)
    tab1,tab2,tab3,tab4=st.tabs(["CLÍNICA & METAS","COLABORADORES","API KEY","🔑 MINHA CONTA"])
    with tab1:
        conn=get_conn(); cr=conn.execute("SELECT * FROM clinica WHERE id=1").fetchone(); conn.close()
        with st.form("form_cl"):
            c1,c2=st.columns(2)
            with c1: nm_c=st.text_input("Nome da clínica",value=cr[1] if cr else ""); meta_c=st.number_input("Meta mensal R$",value=float(cr[2] if cr else 0),step=1000.0)
            with c2: cf_c=st.number_input("Custo fixo total R$",value=float(cr[3] if cr else 0),step=1000.0); est_c=st.selectbox("Estágio",["Caótico","Intuitivo","Documentado","Previsível"],index=["Caótico","Intuitivo","Documentado","Previsível"].index(cr[4] if cr and len(cr)>4 else "Intuitivo")); trib_c=st.selectbox("Regime tributário",["Simples Nacional","Lucro Presumido","Lucro Real"])
            if st.form_submit_button("Salvar"):
                conn=get_conn(); conn.execute("UPDATE clinica SET nome=?,meta_mensal=?,custo_fixo_total=?,estagio=?,modelo_tributario=? WHERE id=1",(nm_c,meta_c,cf_c,est_c,trib_c)); conn.commit();conn.close();st.success("Salvo!");st.rerun()
    with tab2:
        conn=get_conn(); cdf=pd.read_sql("SELECT * FROM colaboradores WHERE ativo=1",conn); conn.close()
        if not cdf.empty: st.dataframe(cdf[['nome','funcao','cargo_key','nivel_acesso','zona_genialidade']],hide_index=True,use_container_width=True)
        with st.expander("➕ Adicionar Colaborador"):
            with st.form("form_col"):
                c1,c2,c3=st.columns(3)
                with c1: nm_cb=st.text_input("Nome")
                with c2: fc_cb=st.text_input("Função")
                with c3: ck_cb=st.text_input("Cargo Key (ex: gerente)")
                na_cb=st.selectbox("Nível",["CEO / Proprietário","Gerente Executiva","Operacional"]); zg_cb=st.text_input("Zona de genialidade")
                if st.form_submit_button("Adicionar"):
                    if nm_cb:
                        conn=get_conn(); conn.execute("INSERT INTO colaboradores(nome,funcao,cargo_key,nivel_acesso,zona_genialidade) VALUES(?,?,?,?,?)",(nm_cb,fc_cb,ck_cb,na_cb,zg_cb)); conn.commit();conn.close();st.rerun()
    with tab3:
        st.markdown(f"""**Configure a chave Anthropic para análise por IA.**\n\nStreamlit Cloud → seu app → ⋮ → **Settings → Secrets**:\n```toml\nANTHROPIC_API_KEY = "sk-ant-sua-chave-aqui"\n```\nhttps://console.anthropic.com/keys""")
        kt=st.text_input("Testar chave",type="password")
        if st.button("Testar") and kt:
            try:
                client=anthropic.Anthropic(api_key=kt); client.messages.create(model="claude-sonnet-4-20250514",max_tokens=5,messages=[{"role":"user","content":"ok"}]); st.success("Chave válida!")
            except Exception as e: st.error(f"Inválida: {e}")
        st.markdown(f"""<div style="background:{BG_DEEP};border:1px solid {BORDER};border-radius:16px;padding:22px 26px;margin-top:20px;box-shadow:0 0 0 1px rgba(255,255,255,0.04),0 4px 24px rgba(0,0,0,0.4)">
            <div style="color:{FG};font-size:15px;font-weight:600;letter-spacing:-0.02em;margin-bottom:10px">LAB Metrics — Método Ponteiro</div>
            <div style="color:{FG_MUTED};font-size:13px;line-height:1.9;margin-bottom:14px">O Projeto Ponteiro organiza pessoas, processos e oportunidades para transformar esforço em execução, execução em faturamento e faturamento em previsibilidade.</div>
            <div style="display:grid;grid-template-columns:1fr 1fr;gap:6px;font-size:12px;color:{FG_MUTED}">
                {''.join([f'<div>→ {p}</div>' for p in ["Cockpit CEO (30 segundos)","Painel DNA Semanal","Auditoria de Salas","Comercial & SDR + Scripts","Réguas D-1/D+1","Programa Integra (MOD + Pontuação)","EBITDA Operacional Real","OKRs conectados à operação","Ingestão Support Clinic","Diagnóstico AME por IA","Segurança Assistencial","SBAR Estruturado","RFM & Indicações","Orçamentos com Alertas"]])}
            </div>
            <div style="margin-top:14px;font-size:11px;color:rgba(255,255,255,0.2);font-style:italic">"Ideia é prata. Mentalidade é ouro. Execução é diamante."</div>
        </div>""",unsafe_allow_html=True)

    # ── Minha Conta ──────────────────────────────────────────────
    with tab4:
        _uid = st.session_state.get("user_id")
        _nome_u = st.session_state.get("user_nome","")
        _nivel_u = st.session_state.get("user_nivel","")

        # Card de perfil
        st.markdown(f"""
        <div style="background:#FFFFFF;border:4px solid #121212;padding:24px 28px;
                    box-shadow:6px 6px 0 #121212;margin-bottom:24px;display:flex;
                    align-items:center;gap:20px">
            <div style="width:56px;height:56px;background:#1040C0;border:3px solid #121212;
                        display:flex;align-items:center;justify-content:center;
                        font-size:1.4rem;font-weight:900;color:#F0C020;
                        font-family:'Outfit',sans-serif;flex-shrink:0">
                {_nome_u[0].upper() if _nome_u else '?'}
            </div>
            <div>
                <div style="font-size:1.1rem;font-weight:900;color:#121212;text-transform:uppercase;
                            letter-spacing:-0.01em;font-family:'Outfit',sans-serif">{_nome_u}</div>
                <div style="font-size:11px;color:#888;font-weight:500;margin-top:2px">{_nivel_u}</div>
            </div>
        </div>""", unsafe_allow_html=True)

        # Trocar senha
        st.markdown(f"""
        <div style="background:#121212;border:3px solid #121212;padding:12px 18px;margin-bottom:16px">
            <span style="font-size:10px;color:#F0C020;font-weight:700;text-transform:uppercase;
                         letter-spacing:0.12em;font-family:'Outfit',sans-serif">
                🔑 ALTERAR SENHA
            </span>
        </div>""", unsafe_allow_html=True)

        with st.form("form_trocar_senha_config"):
            c1, c2, c3 = st.columns(3)
            with c1:
                pw_atual = st.text_input("Senha atual", type="password",
                    placeholder="••••••••", key="pw_atual_cfg")
            with c2:
                pw_nova1 = st.text_input("Nova senha", type="password",
                    placeholder="mínimo 6 caracteres", key="pw_nova1_cfg")
            with c3:
                pw_nova2 = st.text_input("Confirmar nova senha", type="password",
                    placeholder="repita a nova senha", key="pw_nova2_cfg")

            if st.form_submit_button("🔑 SALVAR NOVA SENHA", use_container_width=True):
                if not pw_atual or not pw_nova1 or not pw_nova2:
                    st.error("Preencha todos os campos.")
                elif len(pw_nova1) < 6:
                    st.error("A nova senha precisa ter no mínimo 6 caracteres.")
                elif pw_nova1 != pw_nova2:
                    st.error("A nova senha e a confirmação não coincidem.")
                elif pw_nova1 == pw_atual:
                    st.error("A nova senha precisa ser diferente da senha atual.")
                elif pw_nova1 in ("integrative2026","barbara2026","gerente2026",
                                  "bianca2026","aline2026","beatriz2026","paloma2026"):
                    st.error("Use uma senha diferente da senha padrão do sistema.")
                else:
                    # Verificar senha atual
                    conn_pw = get_conn()
                    ok_atual = conn_pw.execute(
                        "SELECT id FROM usuarios WHERE id=? AND senha_hash=?",
                        (_uid, hash_pw(pw_atual))).fetchone()
                    conn_pw.close()
                    if not ok_atual:
                        st.error("Senha atual incorreta.")
                    else:
                        trocar_senha(_uid, pw_nova1)
                        st.success("Senha alterada com sucesso!")

        # Seção: usuários do sistema (somente CEO/Gerente)
        _nivel_atual = st.session_state.get("user_nivel","")
        if _nivel_atual in ("CEO","Gerente"):
            st.markdown("---")
            st.markdown(f"""
            <div style="background:#121212;border:3px solid #121212;padding:12px 18px;margin-bottom:16px">
                <span style="font-size:10px;color:#F0C020;font-weight:700;text-transform:uppercase;
                             letter-spacing:0.12em;font-family:'Outfit',sans-serif">
                    👥 GERENCIAR USUÁRIOS DO SISTEMA
                </span>
            </div>""", unsafe_allow_html=True)

            conn_u = get_conn()
            users_df = pd.read_sql(
                "SELECT id,nome,login,nivel,cargo_key,ativo,primeiro_acesso,ultimo_acesso FROM usuarios",
                conn_u)
            conn_u.close()

            if not users_df.empty:
                for _, row in users_df.iterrows():
                    cor_u = "#2A8A2A" if row['ativo'] else "#D02020"
                    tag_pa = " · ⚠️ Senha padrão" if row['primeiro_acesso'] else ""
                    st.markdown(f"""
                    <div style="background:#FFFFFF;border:3px solid #121212;padding:12px 16px;
                                margin-bottom:6px;box-shadow:3px 3px 0 #121212;
                                display:flex;justify-content:space-between;align-items:center">
                        <div>
                            <div style="font-size:13px;font-weight:700;color:#121212">
                                {row['nome']}
                                <span style="font-size:10px;color:#D02020;font-weight:500">{tag_pa}</span>
                            </div>
                            <div style="font-size:10px;color:#888">
                                {row['login']} · {row['nivel']}
                                {f" · Último acesso: {row['ultimo_acesso'][:10]}" if row['ultimo_acesso'] else ""}
                            </div>
                        </div>
                        <div style="background:{cor_u};padding:4px 10px;border:2px solid #121212">
                            <span style="font-size:9px;font-weight:700;color:#FFFFFF;text-transform:uppercase">
                                {"ATIVO" if row['ativo'] else "INATIVO"}
                            </span>
                        </div>
                    </div>""", unsafe_allow_html=True)

            # Resetar senha de um usuário
            with st.expander("🔄 Resetar Senha de Usuário"):
                with st.form("form_reset_pw"):
                    c1, c2 = st.columns(2)
                    with c1:
                        user_reset = st.selectbox("Usuário",
                            users_df['login'].tolist() if not users_df.empty else [],
                            format_func=lambda x: f"{x} — {users_df[users_df['login']==x]['nome'].values[0]}" if not users_df.empty else x)
                    with c2:
                        nova_pw_reset = st.text_input("Nova senha temporária", type="password",
                            placeholder="mínimo 6 caracteres")
                    if st.form_submit_button("RESETAR SENHA", use_container_width=True):
                        if not nova_pw_reset or len(nova_pw_reset) < 6:
                            st.error("Senha precisa ter no mínimo 6 caracteres.")
                        else:
                            uid_reset = users_df[users_df['login']==user_reset]['id'].values[0]
                            conn_r = get_conn()
                            # Resetar senha E marcar como primeiro_acesso para forçar troca
                            conn_r.execute(
                                "UPDATE usuarios SET senha_hash=?, primeiro_acesso=1 WHERE id=?",
                                (hash_pw(nova_pw_reset), int(uid_reset)))
                            conn_r.commit(); conn_r.close()
                            st.success(f"Senha de '{user_reset}' resetada! Usuário precisará criar nova senha no próximo acesso.")
