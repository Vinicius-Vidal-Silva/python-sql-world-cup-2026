import os
import requests
import json
from dotenv import load_dotenv

# ==================================
# CONFIGURAÇÃO E AUTENTICAÇÃO
# ==================================
load_dotenv()
API_KEY = os.getenv("API_KEY")

headers = {
    "x-rapidapi-key": API_KEY,
    "x-rapidapi-host": "v3.football.api-sports.io"
}

# ==================================
# PASSO 1: DESCOBRIR O LEAGUE ID CORRETO DE 2026
# ==================================
LEAGUES_URL = "https://v3.football.api-sports.io/leagues"
leagues_params = {
    "search": "World Cup",
    "season": "2026"
}

league_id_oficial = None

try:
    print("📡 Buscando IDs de ligas oficiais para 'World Cup' em 2026...")
    response = requests.get(LEAGUES_URL, headers=headers, params=leagues_params)
    response.raise_for_status()
    leagues_data = response.json().get("response", [])

    if not leagues_data:
        print("⚠️ Nenhuma liga encontrada com o termo 'World Cup' para 2026.")
        print("Tentando buscar a liga geral de ID 1 (Copa do Mundo)...")
        league_id_oficial = 1
    else:
        print("\n🏆 Ligas encontradas para 2026:")
        for lg in leagues_data:
            l_id = lg.get("league", {}).get("id")
            l_name = lg.get("league", {}).get("name")
            l_type = lg.get("league", {}).get("type")
            print(f"🔹 ID: {l_id} | Nome: {l_name} ({l_type})")

            # Seleciona preferencialmente o torneio principal ou o primeiro disponível
            if "Cup" in l_name and l_type == "Cup":
                league_id_oficial = l_id

        # Se não capturar no loop, pega o primeiro retornado
        if not league_id_oficial:
            league_id_oficial = leagues_data[0].get("league", {}).get("id")

except Exception as e:
    print(f"❌ Erro ao buscar as ligas: {e}")
    league_id_oficial = 1  # Fallback para o ID padrão da Copa do Mundo

# ==================================
# PASSO 2: MAPEAR OS JOGOS COM O ID ENCONTRADO
# ==================================
if league_id_oficial:
    print(f"\n🎯 Usando League ID oficial: {league_id_oficial} para mapear os confrontos...")

    FIXTURES_URL = "https://v3.football.api-sports.io/fixtures"
    fixtures_params = {
        "league": str(league_id_oficial),
        "season": "2026"
    }

    try:
        response = requests.get(FIXTURES_URL, headers=headers, params=fixtures_params)
        response.raise_for_status()
        fixtures_data = response.json().get("response", [])

        if not fixtures_data:
            print(f"⚠️ Calendário de confrontos ainda não disponível para a liga {league_id_oficial} na API.")
            print("Isso confirma que o schema de chaves será gerado na liberação do sorteio oficial!")
        else:
            print(f"✅ Sucesso! Encontrados {len(fixtures_data)} confrontos programados.")

            # Gravação do arquivo txt de mapeamento para consulta do Bolão
            with open("calendario_ids_2026.txt", "w", encoding="utf-8") as f:
                f.write(f"{'MATCH ID':<10} | {'CONFRONTO':<45} | {'RODADA'}\n")
                f.write("-" * 80 + "\n")

                for item in fixtures_data:
                    match_id = item.get("fixture", {}).get("id")
                    round_name = item.get("league", {}).get("round")
                    home_team = item.get("teams", {}).get("home", {}).get("name")
                    away_team = item.get("teams", {}).get("away", {}).get("name")
                    confronto = f"{home_team} x {away_team}"

                    f.write(f"{match_id:<10} | {confronto:<45} | {round_name}\n")

            print("💾 Arquivo 'calendario_ids_2026.txt' gerado com sucesso para controle de chaves!")

    except Exception as e:
        print(f"❌ Erro ao extrair os confrontos: {e}")