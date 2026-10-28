# 📊 Dashboard de Análise - Reclame Aqui

Este projeto é uma aplicação web interativa desenvolvida em Python para analisar o histórico de atendimento e satisfação de clientes de seis grandes empresas brasileiras no portal Reclame Aqui. O foco principal foi criar um pipeline de ETL (Extração, Tratamento e Carregamento) e disponibilizar os insights através de um Dashboard de Business Intelligence.

## 🚀 Tecnologias Utilizadas
* **Python**: Linguagem principal para análise e automação.
* **Pandas**: Limpeza de dados (remoção de nulos/duplicados), transformações de datas e formatação de strings, e cálculos de métricas (taxa de resolução, volumetria, cruzamento de localidades).
* **Streamlit**: Construção de toda a interface visual web (filtros interativos, gráficos em barra e linha, tabelas consolidadas).

## 💻 Funcionalidades
* **Filtros Dinâmicos**: Permite filtrar a base de dados por Empresa, Período de tempo, Estado, Status do ticket e Categoria do problema.
* **Métricas de Negócio**: Cálculo automático da taxa de resolução e taxa de resposta.
* **Detalhamento Analítico**: Matriz cruzada (Empresa vs Status) e ranking das localidades com maior volume de tickets.

## ⚙️ Como executar o projeto na sua máquina
1. Clone este repositório.
2. Instale as bibliotecas necessárias: `pip install -r requirements.txt`
3. Execute o comando no terminal: `streamlit run dashboard_ra.py`
