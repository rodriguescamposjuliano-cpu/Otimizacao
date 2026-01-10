# Trabalho Módulo 3 - Pesquisa Operacional

[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)](README.md)

O objetivo deste projeto é desenvolver uma ferramenta capaz de identificar a melhor rota de voo entre diversas alternativas obtidas do site Rome2Rio, 
considerando múltiplos critérios: tempo total, preço e número de conexões.

Objetivos Principais

- **Zoneamento Energético:** Identificar quais microrregiões de Goiás apresentam maior potencial para diferentes tipos de energia renovável.  
- **Sazonalidade Estratégica:** Apoiar a formulação de políticas que promovam a complementaridade energética ao longo do ano.  
- **Sinergia Hidro-Solar:** Otimizar a integração entre a geração hidrelétrica existente e o potencial solar e eólico do estado.  
- **Capacidade de Escoamento:** Avaliar como a infraestrutura atual de transmissão influencia o aproveitamento do potencial renovável.

---

## Índice

- [Descricao](#descricao)
- [Sequencia do processamento](#sequencia-do-processamento)
- [Fonte de Dados](#fonte-de-dados)
- [Requisitos](#requisitos)
- [Instalacao](#instalacao)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Como Rodar](#como-rodar)
- [Visualizacao](#visualizacao)

---

## Descricao

O projeto realiza as seguintes etapas:

1. Realiza a busca de todos os voos conforme a origem, destino e data de partida
2. Prepara os dados dos voos, preço, tempo e número de conexões
     
## Requisitos

- Python 3.11  
- Dependências listadas em `requirements.txt`

---

## Instalacao

    1. Instale o Python 3.11

        brew install python@3.11

    2. Crie o ambiente virtual

        python3.11 -m venv venv

    3. Ative o ambiente virtual

        Mac/Linux: source venv/bin/activate
        Windows (PowerShell): .\venv\Scripts\Activate.ps1
        Windows (CMD): .\venv\Scripts\activate.bat

    4. Instale as dependências

        pip install -r requirements.txt


## Estrutura do Projeto

```plaintext
Otimizacao/
│
├── Crawler/                   
│   ├── crawler_rome2rio.py        # Faz a busca no site Rome2Rio
│   └── 
│   
├── Domain/
│   └── models.py # Responsável por definir os objetos.        
│   ├── parsers.py # Classe utilitária, contém funções para formatações dos valores            
|
├── optimization                
│   └── nsga2_solver.py # Classe que contém o solver NSGA2
│
├── services                
│   └── optimization_service.py 
│   └── route_service.py 
│
├── ui                
│   └── layout.py
│   └── results_view.py
│   └── results_view.py
│   └── route_form.py
│   └── sidebar.py
|
├── .gitignore
├── app.py
├── README.md
├── requirements.txt        
└── .env           
```
## Como utilizar a aplicação

1. Execute o arquivo app.py para iniciar a aplicação
   ```plaintext
   python app.py
   ```
2. Após abrir a aplicação selecione as rotas e processe a otimização


 




