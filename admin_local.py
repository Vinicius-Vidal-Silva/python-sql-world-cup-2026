import os
import sqlite3
import psycopg2
from dotenv import load_dotenv

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")


def init_local_db():
    """Cria a tabela de controle de jogos localmente no seu computador"""
    local_conn = sqlite3.connect("C:\sqlite\database\world_cup_2026.db")
    local_cursor = local_conn.cursor()
    local_cursor.execute("""
        CREATE TABLE IF NOT EXISTS matches (
            match_id INTEGER PRIMARY KEY,
            confronto TEXT,
            tournament_round TEXT,
            home_goals INTEGER,
            away_goals INTEGER
        );
    """)
    local_conn.commit()
    local_conn.close()


def input_real_scores():
    """Interface de terminal para você digitar os placares de forma rápida"""
    init_local_db()
    local_conn = sqlite3.connect("C:\sqlite\database\world_cup_2026.db")
    local_cursor = local_conn.cursor()

    print("\n🏁 === PAINEL ADMINISTRATIVO LOCAL - COPA 2026 ===")
    print("Digite o ID do jogo para atualizar o placar (ou '0' para sair):")

    while True:
        try:
            # Exemplo de entrada: você olha no seu arquivo txt de mapeamento o ID do jogo do dia
            m_id = int(input("\nDigite o MATCH ID: "))
            if m_id == 0:
                break

            home = int(input("Gols do time Mandante: "))
            away = int(input("Gols do time Visitante: "))

            # Atualiza no seu banco de dados local
            local_cursor.execute("""
                INSERT INTO matches (match_id, home_goals, away_goals)
                VALUES (?, ?, ?)
                ON CONFLICT(match_id) DO UPDATE SET
                    home_goals = excluded.home_goals,
                    away_goals = excluded.away_goals;
            """, (m_id, home, away))
            local_conn.commit()
            print(f"✅ Placar salvo localmente para o jogo {m_id}!")

        except ValueError:
            print("❌ Por favor, insira números válidos.")

    local_conn.close()

    # Após coletar os dados do dia, dispara o sincronismo automático para a nuvem
    sync_to_supabase()


def sync_to_supabase():
    """Coleta as atualizações do SQLite local e injeta direto na Camada Silver do Supabase"""
    print("\n📡 Iniciando sincronização incremental com o Supabase Cloud...")

    local_conn = sqlite3.connect("C:\sqlite\database\world_cup_2026.db")
    local_cursor = local_conn.cursor()
    local_cursor.execute("SELECT match_id, home_goals, away_goals FROM matches;")
    jogos_locais = local_cursor.fetchall()
    local_conn.close()

    if not jogos_locais:
        print("⚠️ Nenhum dado local encontrado para sincronizar.")
        return

    try:
        supabase_conn = psycopg2.connect(DATABASE_URL)
        supabase_cursor = supabase_conn.cursor()

        # Faz o UPSERT cirúrgico direto na Fato da Silver, atualizando os placares reais
        query_upsert = """
            INSERT INTO silver.fact_matches (match_id, home_team_goals, away_team_goals, updated_at)
            VALUES (%s, %s, %s, CURRENT_TIMESTAMP)
            ON CONFLICT (match_id) DO UPDATE SET
                home_team_goals = EXCLUDED.home_team_goals,
                away_team_goals = EXCLUDED.away_team_goals,
                updated_at = EXCLUDED.updated_at;
        """

        supabase_cursor.executemany(query_upsert, jogos_locais)
        supabase_conn.commit()

        print(f"🚀 Sucesso! {len(jogos_locais)} jogos foram sincronizados e atualizados no Supabase.")
        supabase_cursor.close()
        supabase_conn.close()

    except Exception as e:
        print(f"❌ Erro ao sincronizar com a nuvem: {e}")


if __name__ == "__main__":
    input_real_scores()