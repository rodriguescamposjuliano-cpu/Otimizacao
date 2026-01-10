# ✈️ Trabalho – Módulo 3
Pesquisa Operacional aplicada à Otimização de Rotas Aéreas

[![Python](https://img.shields.io/badge/python-3.11-blue)](https://www.python.org/)
[![Status](https://img.shields.io/badge/status-em%20desenvolvimento-yellow)](README.md)

Este projeto consiste no desenvolvimento de uma ferramenta computacional para apoio à decisão, baseada em Pesquisa Operacional e Otimização Multiobjetivo, capaz de identificar rotas aéreas eficientes a partir de múltiplas alternativas obtidas do site Rome2Rio.

---

## Índice

- [Descricao](#descricao)
- [Requisitos](#requisitos)
- [Instalacao](#instalacao)
- [Estrutura do Projeto](#estrutura-do-projeto)
- [Iniciar a Aplicacao](#Iniciar-a-aplicacao)
- [Sequencia do Processamento](#Sequencia-do-Processamento)

---

## Descricao

A solução considera simultaneamente critérios conflitantes, tais como:

⏱️ Tempo total de viagem

💰 Custo da passagem

🔁 Número de conexões

O problema é tratado como um problema de otimização multiobjetivo discreto, resolvido por meio do algoritmo evolutivo NSGA-II (Non-dominated Sorting Genetic Algorithm II)

🎯 Objetivos do Projeto

Desenvolver uma aplicação capaz de identificar soluções eficientes (ótimas de Pareto) para o problema de escolha de rotas aéreas, considerando múltiplos critérios simultaneamente.

Objetivos Específicos

✔️ Automatizar a extração de dados reais de rotas aéreas via web crawling

✔️ Estruturar e normalizar dados heterogêneos (preço, tempo, conexões)

✔️ Formular matematicamente o problema como uma otimização multiobjetivo

✔️ Implementar o NSGA-II como solver do problema

✔️ Visualizar e interpretar a Fronteira de Pareto

✔️ Disponibilizar uma interface interativa para apoio à decisão
     
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
│   ├── crawler_rome2rio.py        # Web crawler do Rome2Rio
│   └── 
│   
├── Domain/
│   └── models.py # Modelos de domínio      
│   ├── parsers.py # Normalização e formatação         
|
├── optimization                
│   └── nsga2_solver.py # Solver NSGA-II
│
├── services                
│   └── optimization_service.py # Orquestra a otimização
│   └── route_service.py # Lógica de rotas
│
├── ui                
│   └── layout.py
│   └── results_view.py
│   └── results_view.py
│   └── route_form.py
│   └── sidebar.py
|
├── .gitignore
├── app.py # Ponto de entrada da aplicação
├── README.md
├── requirements.txt        
└── .env           
```
## Iniciar a Aplicacao

Execute o arquivo app.py para iniciar a aplicação
   ```plaintext
   python app.py
   ```

## Sequencia do Processamento

📥 Entrada do usuário (origem, destino, data)

🕷️ Web Crawling no Rome2Rio

🧹 Tratamento e normalização dos dados

📊 Construção das variáveis de decisão

⚙️ Execução do NSGA-II

🟢 Identificação das soluções não-dominadas

📈 Visualização da Fronteira de Pareto

🧭 Exibição das melhores rotas ao usuário
 




