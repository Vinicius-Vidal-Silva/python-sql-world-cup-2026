import os
import json
import requests
import psycopg2
import logging

from dotenv import load_dotenv
from datetime import datetime


# ==================================
# LOGGING
# ==================================

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(message)s"
)

logger = logging.getLogger(__name__)


# ==================================
# LOAD ENV
# ==================================

load_dotenv()

API_KEY = os.getenv("API_KEY")
DATABASE_URL = os.getenv("DATABASE_URL")


# ==================================
# API CONFIG
# ==================================

API_URL = "https://v3.football.api-sports.io/fixtures"

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}

params = {
    "league": "1",
    "season": "2022"
}


# ==================================
# SQL
# ==================================

insert_query = """
    INSERT INTO bronze.raw_world_cup
    (
        json_data,
        ingestion_timestamp,
        source_file
    )
    VALUES
    (
        %s,
        %s,
        %s
    )
"""


# ==================================
# EXECUÇÃO
# ==================================

conn = None
cursor = None

try:

    # ==================================
    # DATABASE CONNECTION
    # ==================================

    logger.info("Iniciando conexão com Supabase.")

    conn = psycopg2.connect(DATABASE_URL)

    cursor = conn.cursor()

    logger.info("Conexão com Supabase realizada com sucesso.")

    # 1. Limpa a tabela temporária (Bronze Staging)
    logger.info("Limpando a tabela temporária bronze.raw_world_cup.")

    cursor.execute("TRUNCATE TABLE bronze.raw_world_cup;")

    # ==================================
    # API REQUEST
    # ==================================

    logger.info("Iniciando request na API Football.")

    response = requests.get(
        API_URL,
        headers=headers,
        params=params
    )

    response.raise_for_status()

    data = response.json()

    fixtures = data.get("response", [])

    logger.info(f"API retornou {len(fixtures)} jogos.")


    # ==================================
    # VALIDATION
    # ==================================

    if not fixtures:

        logger.warning("Nenhum jogo encontrado na API.")

    else:

        # ==================================
        # INSERT
        # ==================================

        # ==================================
        # INSERT (Refatorado para todos os jogos)
        # ==================================

        logger.info(f"Iniciando insert de {len(fixtures)} registros na camada Bronze.")

        # Preparamos uma lista de tuplas com os dados
        data_to_insert = [
            (
                json.dumps(fixture),
                datetime.now(),
                "api_football_v3_fixtures"
            )
            for fixture in fixtures
        ]

        # Usamos executemany para inserir a lista toda
        cursor.executemany(insert_query, data_to_insert)

        # 3. Dispara a Procedure de HASH que distribui e atualiza o histórico
        logger.info("Disparando Procedure de controle HASH (CDC).")
        cursor.execute("CALL bronze.pr_cdc_world_cup_2026();")

        # 4. Dispara a atualização da Camada Silver
        logger.info("Disparando Procedure de carga da Camada Silver.")
        cursor.execute("CALL silver.pr_load_silver_world_cup_2026();")

        conn.commit()

        logger.info(f"{len(fixtures)} registros inseridos com sucesso no Supabase.")


except Exception as e:

    logger.exception(f"Erro durante execução do ETL: {e}")


finally:

    # ==================================
    # CLOSE CONNECTIONS
    # ==================================

    if cursor:

        cursor.close()

        logger.info("Cursor encerrado.")

    if conn:

        conn.close()

        logger.info("Conexão com banco encerrada.")