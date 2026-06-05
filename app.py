import streamlit as st
import plotly.express as px

# Configuração da página idêntica à referência
st.set_page_config(page_title="World Cup Sweepstake", layout="wide")

# =========================================================
# 1. INTERNACIONALIZAÇÃO (i18n)
# =========================================================
LANGUAGES = {
    "English": {
        "title": "🏆 World Cup Hub - Sweepstake 2026",
        "subtitle": "Track your team's predictions and ranking dynamically",
        "filter_team": "Filter by Corporate Team",
        "ranking_title": "📊 General Standings",
        "evolution_title": "📈 Points Evolution along Rounds",
        "all": "All Teams",
        "table_section": "📋 Raw Data - Participant Metrics",
        "table": {
            "user_name": "Participant",
            "corporate_team": "Corporate Team",
            "total_pontos": "Total Points"
        }
    },
    "Português - BR": {
        "title": "🏆 Central da Copa - Bolão 2026",
        "subtitle": "Acompanhe os palpites e o ranking do seu time de forma dinâmica",
        "filter_team": "Filtrar por Time Corporativo",
        "ranking_title": "📊 Classificação Geral",
        "evolution_title": "📈 Evolução de Pontos ao Longo das Rodadas",
        "all": "Todos os Times",
        "table_section": "📋 Dados Brutos - Métricas dos Participantes",
        "table": {
            "user_name": "Participante",
            "corporate_team": "Time Corporativo",
            "total_pontos": "Pontuação Total"
        }
    },
    "Deutsch": {
        "title": "🏆 Weltmeisterschaft Hub - Tippspiel 2026",
        "subtitle": "Verfolgen Sie die Vorhersagen und das Ranking Ihres Teams",
        "filter_team": "Nach Firmenteam filtern",
        "ranking_title": "📊 Gesamtstand",
        "evolution_title": "📈 Punkteentwicklung nach Runden",
        "all": "Alle Teams",
        "table_section": "📋 Rohdaten - Teilnehmerkennzahlen",
        "table": {
            "user_name": "Teilnehmer",
            "corporate_team": "Firmenteam",
            "total_pontos": "Gesamtpunkte"
        }
    }
}

# =========================================================
# 2. BARRA LATERAL (SIDEBAR) - Filtros e Configurações
# =========================================================
with st.sidebar:
    st.header("⚙️ Settings / Configurações")

    # Seletor de Idioma
    language = st.selectbox("🌐 Language / Idioma", list(LANGUAGES.keys()))
    t = LANGUAGES[language]  # Atalho para o dicionário ativo

# =========================================================
# 3. CONEXÃO REAL COM O SUPABASE (POSTGRESQL NATIVO)
# =========================================================
# O Streamlit lê as credenciais direto de .streamlit/secrets.toml
conn = st.connection("supabase", type="sql")


# Função com cache para o Ranking Geral
@st.cache_data(ttl=300)  # Guarda por 5 minutos para poupar conexões
def get_ranking_data():
    return conn.query("SELECT user_name, corporate_team, total_pontos FROM gold.vw_ranking_bolao;")


# Função com cache para a Evolução por Rodada
@st.cache_data(ttl=300)
def get_evolution_data():
    return conn.query("SELECT user_name, corporate_team, round, points FROM gold.vw_evolucao_bolao;")


try:
    # Carga dos dados vindos das Views do Supabase
    df_ranking_raw = get_ranking_data()
    df_evolution_raw = get_evolution_data()

    # Coleta dinamicamente os times corporativos existentes no banco para o select
    available_teams = sorted(df_ranking_raw["corporate_team"].dropna().unique().tolist())
    corporate_team_options = [t["all"]] + available_teams

    with st.sidebar:
        st.divider()
        selected_team = st.selectbox(t["filter_team"], corporate_team_options)

    # Cria cópias dos DataFrames para manipulação/filtro
    df_ranking = df_ranking_raw.copy()
    df_evolution = df_evolution_raw.copy()

    # =========================================================
    # 4. APLICAÇÃO DA LÓGICA DE FILTRO (Hierarquia Corporativa)
    # =========================================================
    if selected_team != t["all"]:
        # Se filtrar por "FG-AM-1", traz sub-times ("FG-AM-11", "FG-AM-12"...) via prefixo
        df_ranking = df_ranking[df_ranking['corporate_team'].str.startswith(selected_team)]
        df_evolution = df_evolution[df_evolution['corporate_team'].str.startswith(selected_team)]

    # =========================================================
    # 5. CONSTRUÇÃO DOS GRÁFICOS (PLOTLY)
    # =========================================================

    # Gráfico 1: Ranking Geral (Barras com cores Ouro, Prata, Bronze)
    df_ranking = df_ranking.sort_values(by="total_pontos", ascending=False).reset_index(drop=True)
    bar_colors = []
    for i in range(len(df_ranking)):
        if i == 0:
            bar_colors.append("#FFD700")  # Ouro [cite: 477]
        elif i == 1:
            bar_colors.append("#C0C0C0")  # Prata [cite: 477]
        elif i == 2:
            bar_colors.append("#CD7F32")  # Bronze [cite: 477]
        else:
            bar_colors.append("#1F77B4")  # Azul corporativo [cite: 477]

    fig_ranking = px.bar(
        df_ranking,
        x="total_pontos",
        y="user_name",
        orientation='h',
        title=t["ranking_title"],
        text="total_pontos"
    )
    fig_ranking.update_traces(marker_color=bar_colors, textposition='outside')
    fig_ranking.update_layout(yaxis={'categoryorder': 'total ascending'}, showlegend=False)

    # Gráfico 2: Evolução ao Longo das Rodadas (Linhas baseadas na Fato do Banco)
    # Ordena as rodadas cronologicamente para garantir o sentido correto da linha
    df_evolution = df_evolution.sort_values(by=["user_name", "round"])
    fig_evolution = px.line(
        df_evolution,
        x="round",
        y="points",
        color="user_name",
        markers=True,
        title=t["evolution_title"],
        labels={"round": "Round", "points": "Points", "user_name": t["table"]["user_name"]}
    )

    # =========================================================
    # 6. RENDERIZAÇÃO DO DASHBOARD (FRONT-END)
    # =========================================================
    st.title(t["title"])
    st.subheader(t["subtitle"])
    st.divider()

    # Layout em duas colunas idêntico ao Stock Peer Analysis
    col_left, col_right = st.columns(2)

    with col_left:
        st.plotly_chart(fig_ranking, use_container_width=True)

    with col_right:
        st.plotly_chart(fig_evolution, use_container_width=True)

    # =========================================================
    # 7. RENDERIZAÇÃO DA TABELA DE DADOS BRUTOS (RAW DATA)
    # =========================================================
    st.divider()
    st.subheader(t["table_section"])

    # Criamos uma cópia limpa para aplicar os emojis de medalhas no pódio
    df_table = df_ranking[["user_name", "corporate_team", "total_pontos"]].copy()

    for i in range(len(df_table)):
        if i == 0:
            df_table.at[i, "user_name"] = f"🥇 {df_table.at[i, 'user_name']}"
        elif i == 1:
            df_table.at[i, "user_name"] = f"🥈 {df_table.at[i, 'user_name']}"
        elif i == 2:
            df_table.at[i, "user_name"] = f"🥉 {df_table.at[i, 'user_name']}"

    st.dataframe(
        df_table,
        column_config={
            "user_name": t["table"]["user_name"],
            "corporate_team": t["table"]["corporate_team"],
            "total_pontos": st.column_config.NumberColumn(
                t["table"]["total_pontos"],
                format="%d pts"
            )
        },
        hide_index=True,
        use_container_width=True
    )

except Exception as e:
    st.error(f"Error connecting to Supabase Gold Layer: {e}")