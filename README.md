# Tech Challenge 3 - Previsão de Chuva

## Descrição do Projeto

Este projeto foi desenvolvido para atender ao **Tech Challenge**, no qual o objetivo era criar uma **API** para coleta de dados climáticos em tempo real e usá-los para treinar um modelo de **Machine Learning**. O modelo foi utilizado para prever a **precipitação (chuva)** nos próximos dias com base em dados históricos e condições atuais.

## Objetivos

- Coletar dados climáticos históricos e atuais.
- Armazenar esses dados em um banco de dados PostgreSQL.
- Treinar um modelo de **Machine Learning** para prever a **precipitação**.
- Criar um **Dashboard** simples para visualizar as previsões.
- A solução foi desenvolvida usando **Python**, **Airflow**, **Prophet**, e **PostgreSQL**.

## Como Funciona

O pipeline foi desenvolvido com **Apache Airflow**, e ele é composto pelas seguintes etapas:

1. **Coleta de Dados**:
   - Dados históricos de clima são coletados de um banco de dados PostgreSQL.
   - Dados atuais são coletados em tempo real a partir da API **OpenWeatherMap** e inseridos no banco de dados PostgreSQL.

2. **Treinamento do Modelo de Previsão**:
   - O modelo de previsão utilizado é o **Prophet**, que é adequado para séries temporais e pode lidar bem com sazonalidades e tendências.
   - O modelo foi treinado com dados históricos de temperatura e precipitação.
   - As previsões de precipitação para os próximos **7 dias** foram geradas.

3. **Armazenamento das Previsões**:
   - As previsões geradas pelo modelo foram armazenadas novamente no banco de dados PostgreSQL para fácil acesso e visualização.

4. **Visualização**:
   - Um **Dashboard** interativo foi criado com **Dash** e **Plotly** para visualizar as previsões de precipitação, permitindo ao usuário ver as previsões para os próximos dias.

## Modelo Escolhido

O modelo de **séries temporais** escolhido foi o **Prophet**, que é altamente recomendado para prever séries temporais com sazonalidades diárias, semanais e anuais. Ele foi escolhido por ser simples de usar e por já ter uma boa implementação para lidar com dados climáticos e suas variações.

### Fórmula Geral do Modelo Prophet

A fórmula geral do modelo Prophet pode ser expressa como a soma dos três componentes:

\[
y(t) = g(t) + S(t) + H(t) + \epsilon_t
\]

Onde:
- `y(t)` é o valor da série temporal no tempo `t` (previsão de precipitação ou temperatura, por exemplo).
- `g(t)` é a tendência (trend) do modelo.
- `S(t)` é a sazonalidade (seasonality) no tempo `t`.
- `H(t)` é o efeito de feriados (holiday effects).
- `\epsilon_t` é o erro (ruído) no modelo.

### Explicação de Como o Prophet Faz a Previsão

1. **Estimativa da Tendência**:
   A primeira parte do modelo é a **tendência** dos dados, que é ajustada para capturar o crescimento ou declínio ao longo do tempo. A tendência é modelada de forma que seja flexível, permitindo mudanças ao longo do tempo. O Prophet usa um modelo **logístico** ou **linear** para estimar esse comportamento.

2. **Estimativa da Sazonalidade**:
   O Prophet calcula a sazonalidade dos dados, identificando padrões periódicos nos dados históricos. Para dados climáticos, por exemplo, a sazonalidade pode ser de **temperaturas mais baixas no inverno** e **mais altas no verão**, ou padrões de precipitação que ocorrem em certos períodos do ano.

3. **Adição de Efeitos de Feriados**:
   O modelo também pode incluir **efeitos de feriados** que influenciam os dados, como eventos climáticos extremos que podem ocorrer em determinadas datas, como tempestades ou mudanças climáticas ocasionais.

4. **Ajuste da Previsão**:
   O modelo gera a previsão ajustando-se a todos esses componentes. O modelo tenta prever as séries futuras, ajustando os parâmetros de tendência e sazonalidade para refletir a evolução dos dados.

5. **Erro (Ruído)**:
   Finalmente, o erro (\(\epsilon_t\)) reflete o ruído nos dados que não pode ser explicado pelos componentes anteriores. O Prophet assume que esse erro é **ruído branco** (não correlacionado), o que significa que ele não tem padrão e não pode ser modelado diretamente.

### Por que o Prophet?

- **Facilidade de Implementação**: O Prophet permite que você trabalhe facilmente com séries temporais sem a necessidade de tunar muitos parâmetros.
- **Boas Previsões com Poucos Dados**: O modelo foi desenvolvido para lidar bem com dados históricos e fazer boas previsões com um conjunto de dados pequeno, que é o caso da previsão climática diária.
- **Sazonalidades**: O Prophet lida bem com sazonalidades e eventos pontuais, como mudanças sazonais no clima, que são importantes para a previsão de precipitação.

## Como Rodar

1. **Requisitos**:
   - **Python 3.x**
   - **PostgreSQL** configurado localmente
   - **Airflow** instalado
   - **Bibliotecas Python**: `requests`, `psycopg2`, `pandas`, `prophet`, `airflow`, `plotly`, `dash`, `dotenv`

2. **Instalação**:
   - Clone o repositório:
     ```bash
     git clone <link-do-repositorio>
     cd <diretorio-do-repositorio>
     ```

   - Instale as dependências:
     ```bash
     pip install -r requirements.txt
     ```

   - Configure as variáveis de ambiente no arquivo `.env`:
     ```env
     API_KEY=<sua-api-key-openweathermap>
     DB_NAME=<nome-do-banco>
     DB_USER=<usuario-do-banco>
     DB_PASSWORD=<senha-do-banco>
     DB_HOST=<localhost-ou-ip>
     DB_PORT=5432
     DB_SCHEMA=<esquema-do-banco>
     ```

3. **Rodando o Pipeline**:
   - Execute o **Airflow** para rodar o pipeline de coleta de dados e treinamento do modelo.
     ```bash
     airflow scheduler
     airflow webserver
     ```

   - O pipeline será executado de acordo com a configuração do Airflow.

4. **Acessando o Dashboard**:
   - O **Dash** é configurado para rodar localmente no **port 8050**.
   - Acesse o dashboard em [http://localhost:8050](http://localhost:8050).

## Estrutura do Repositório

```
- /src
  - /scripts
    - dashboard.py          # Código do dashboard
    - collect_data.py       # Código de coleta de dados
    - train_model.py        # Código para treinar o modelo Prophet
  - /data
    - /processed            # Dados processados
- requirements.txt          # Dependências do projeto
- .env                      # Arquivo de variáveis de ambiente
- README.md                 # Documentação do projeto
```

## Link para Vídeo Explicativo

Por favor, adicione o link do vídeo explicativo do seu projeto aqui:

[Link para o vídeo explicativo](#)