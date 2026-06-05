# 🏆 Central da Copa — Bolão Analítico 2026

Uma plataforma analítica ponta a ponta (*End-to-End*) desenvolvida para gerenciar, normalizar e visualizar palpites de um bolão corporativo para a Copa do Mundo de 2026. O projeto se destaca por resolver um problema real de restrição orçamentária de APIs pagas através de uma **Arquitetura Híbrida Descentralizada (Edge/Cloud)** com custo zero de infraestrutura.

---

## 🏗️ Arquitetura de Dados & Fluxo do Ecossistema

O projeto adota o padrão de arquitetura **Medalhão** estruturado em um banco de dados relacional e um componente local de administração, garantindo desacoplamento e performance.

+-----------------------------------------------------------------------+
|                           MÁQUINA LOCAL (Edge)                        |
|                                                                       |
|  [ Form de Palpites ]        [ Painel Admin Local (Python + SQLite) ] |
|          |                                      |                     |
|          v                                      v                     |
|  Bolão_2026.csv (144 cols)             world_cup_2026.db (Matches)    |
|          |                                      |                     |
+----------|--------------------------------------|---------------------+
| (Pivoting & Bulk Insert)             | (UPSERT Incremental)
v                                      v
+-----------------------------------------------------------------------+
|                          SUPABASE CLOUD (PostgreSQL)                  |
|                                                                       |
|   🥈 CAMADA SILVER (Star Schema)                                      |
|      - silver.dim_users (Unique Constraint)                           |
|      - silver.dim_teams                                               |
|      - silver.fact_matches (Resultados Reais)                         |
|      - silver.fact_predictions (Palpites Verticalizados)              |
|                                                                       |
|   🥇 CAMADA GOLD (Views Analíticas Mutuamente Exclusivas)             |
|      - gold.vw_ranking_bolao                                          |
|      - gold.vw_evolucao_bolao (Janela Temporal: SUM OVER)             |
+-----------------------------------------------------------------------+
|
v
+-----------------------------------------------------------------------+
|                          STREAMLIT FRONT-END                          |
|                                                                       |
|   - Cache Ativo (@st.cache_data ttl=300)                              |
|   - Filtros Dinâmicos de Hierarquia Corporativa (.str.startswith)     |
|   - Internacionalização Nativa (i18n: EN, PT-BR, DE)                  |
+-----------------------------------------------------------------------+


---

## 🛠️ Destaques de Engenharia de Dados

### 1. Ingestão de Arquivo Único & Normalização Dinâmica (`carga_palpites_csv.py`)
Os palpites chegam em um arquivo `.csv` horizontalizado (padrão de exportação de formulários como Google Forms/Typeform), contendo **144 colunas de gols** para os 72 jogos da fase de grupos. 
* **Solução:** Desenvolvido um algoritmo em Python que realiza o *pivoting* (transformação de colunas em linhas) analisando os pares de colunas fisicamente por índice posicional. Isso elimina a necessidade de mapear manualmente 144 campos e associa cada palpite de forma automática ao ID de jogo oficial sequencial da FIFA.

### 2. O Workaround Híbrido de Custo Zero (`admin_local.py`)
Para contornar os planos pagos de APIs esportivas e mitigar custos de computação na nuvem:
* Um banco de dados local **SQLite** (`world_cup_2026.db`) gerencia e armazena os placares reais digitados pelo administrador após o fim das partidas.
* O script Python realiza um **UPSERT incremental** via rede para a tabela `silver.fact_matches` no Supabase utilizando o driver `psycopg2`. A operação é completamente **idempotente**, permitindo correções de placares sem duplicar registros.

### 3. Cérebro Relacional Nivo Pleno (Camada Gold)
O cálculo das pontuações complexas do bolão roda 100% nativo no motor SQL do PostgreSQL através de uma árvore lógica prioritária e **mutuamente exclusiva** (`CASE WHEN`), garantindo que o usuário pontue em apenas uma categoria por jogo:

| Tipo de Acerto | Descrição | Pontos |
| :--- | :--- | :--- |
| **Placar Exato** | Acertou o placar completo | `25` |
| **Vencedor + Gols do Vencedor** | Acertou quem venceu e quantos gols o vencedor fez | `18` |
| **Vencedor + Diferença de Gols**| Acertou quem venceu e a diferença exata de gols | `15` |
| **Vencedor + Gols do Perdedor** | Acertou quem venceu e quantos gols o perdedor fez | `12` |
| **Apenas o Vencedor** | Acertou apenas quem venceu ou que deu empate | `10` |
| **Nenhum acerto** | Errou todas as variáveis | `0` |

---

## 💻 Recursos do Front-End (Streamlit)

* **Performance Otimizada:** Implementação de cache de dados com tempo de vida (`ttl=300`), minimizando requisições desnecessárias ao banco de dados em nuvem a cada clique ou filtro aplicado pelo usuário.
* **Hierarquia Corporativa Dinâmica:** O dropdown de equipes é montado dinamicamente com base nas strings existentes no banco de dados. Filtros aplicados em sub-times (ex: `Time 1`) coletam de forma automática dados de sub-equipes inferiores (`Time 11`, `Time 12`) via lógica de prefixo `.str.startswith()`.
* **Módulo i18n:** Suporte completo de tradução e internacionalização em três idiomas: Inglês, Português (BR) e Alemão.

---

## 🚀 Como Executar o Projeto

### Pré-requisitos
* Python 3.10 ou superior instalado.
* Instância ativa do Supabase (PostgreSQL).

### Passos para Instalação

1. **Clone o repositório:**
   ```bash
   git clone [https://github.com/seu-usuario/copa-2026-bolao.git](https://github.com/seu-usuario/copa-2026-bolao.git)
   cd copa-2026-bolao

 2. **Instale as dependências:**
    Bash

    pip install -r requirements.txt

 3. **Configure as Variáveis de Ambiente (.env):**
    Crie um arquivo .env na raiz do projeto contendo as credenciais de conexão do seu Supabase Cloud:
    Snippet de código

    DATABASE_URL=postgresql://postgres.seu_id:senha@aws-0-sa-east-1.pooler.supabase.com:6543/postgres

 4. **Crie a Estrutura de Tabelas e Views:**
    Execute as DDLs contidas na pasta sql/ (ou os códigos disponibilizados de criação das tabelas e views) no Console SQL do seu Supabase.

 5. **Carregue os Palpites do CSV (Do Zero):**
    Coloque o arquivo exportado do formulário na pasta do projeto e execute:
    Bash

    python carga_palpites_csv.py

 6. **Atualize os Placares Reais do Dia (Interface de Terminal):**
    Bash

    python admin_local.py

 7. **Inicie o Painel Visual do Streamlit:**
    Bash

    streamlit run app.py

📄 Licença

Este projeto está sob a licença MIT. Veja o arquivo LICENSE para mais detalhes.
