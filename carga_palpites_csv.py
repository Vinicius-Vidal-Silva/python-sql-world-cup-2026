import os
import pandas as pd
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def extrair_e_normalizar_palpites(csv_path):
    # Lemos o arquivo disponibilizado
    df = pd.read_csv(csv_path)

    conn = psycopg2.connect(DATABASE_URL)
    cursor = conn.cursor()

    print("🚀 Iniciando processamento do CSV de Palpites...")

    # 1. Garante que os usuários do CSV existem na dim_users
    for nome in df['Seu nome'].unique():
        cursor.execute("""
            INSERT INTO silver.dim_users (user_name, corporate_team)
            VALUES (%s, 'FG-AM-1') ON CONFLICT (user_name) DO NOTHING;
        """, (nome,))
    conn.commit()

    # Mapeamento estático temporário relacionando a coluna do formulário ao ID Real da API
    # Substitua os IDs abaixo pelos IDs reais obtidos no seu mapeador utilitário!
    mapeamento_jogos = {
        ("Brasil gols", "Marrocos gols"): 1,
        ("México gols", "África do Sul gols"): 2,
        ("Canadá gols", "Bósnia e Herzegovina gols"): 3
        # Adicione os demais pares do cabeçalho do formulário aqui...
    }

    palpites_para_inserir = []

    for index, row in df.iterrows():
        nome_usuario = row['Seu nome']

        # Coleta o ID do usuário gerado no banco
        cursor.execute("SELECT user_id FROM silver.dim_users WHERE user_name = %s;", (nome_usuario,))
        user_id = cursor.fetchone()[0]

        # Varre o mapeamento de colunas extraindo os pares de palpites
        for (col_home, col_away), match_id in mapeamento_jogos.items():
            if col_home in df.columns and col_away in df.columns:
                pred_home = row[col_home]
                pred_away = row[col_away]

                if pd.notna(pred_home) and pd.notna(pred_away):
                    palpites_para_inserir.append((
                        user_id,
                        match_id,
                        int(pred_home),
                        int(pred_away)
                    ))

    # 2. Insere em lote na tabela de palpites garantindo a não-duplicação
    query_insert = """
        INSERT INTO silver.fact_predictions (user_id, match_id, predicted_home_goals, predicted_away_goals)
        VALUES (%s, %s, %s, %s)
        ON CONFLICT (user_id, match_id) DO UPDATE SET
            predicted_home_goals = EXCLUDED.predicted_home_goals,
            predicted_away_goals = EXCLUDED.predicted_away_goals;
    """

    if palpites_para_inserir:
        cursor.executemany(query_insert, palpites_para_inserir)
        conn.commit()
        print(f"✅ Sucesso! {len(palpites_para_inserir)} palpites processados e normalizados no Supabase.")

    cursor.close()
    conn.close()


# Executa o script passando o nome do seu arquivo
extrair_e_normalizar_palpites("palpites/BolãoCopaDoMundo2026.csv")