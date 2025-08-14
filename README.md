# 📊 Projeto de Análise e Atualização de Filas de Atendimento

Este projeto simula um **case real de análise de dados** em saúde, onde um sistema gerencia filas de pacientes, contatos realizados e status de atendimento.  
O objetivo é demonstrar **boas práticas de ETL, consultas SQL, processamento em lotes e aplicação de regras de negócio**, usando **dados 100% fictícios**.

---

## 🗂 Arquitetura do Projeto

Fluxo geral:

1. **Geração de Bancos Fictícios** (`criar_bancos_ficticios.py`)
   - Cria dois bancos SQLite:
     - `conexao_principal.db` → Snapshot da fila em uma data específica.
     - `conexao_secundaria.db` → Histórico completo de contatos e status.
   - Garante regras de negócio como:
     - Um mesmo paciente (`ID_CLIENTE`) mantém sempre o mesmo nome e estado.
     - Após 3 tentativas de contato "Sem retorno", a solicitação é encerrada.
     - Caso reentre na fila, o paciente só pode ter status "Agendado" ou "Atendido".

2. **Atualização das Filas** (`atualizar_filas.py`)
   - Lê o snapshot.
   - Consulta o histórico **em lotes** para evitar sobrecarga.
   - Aplica regras de negócio para determinar:
     - Status atual.
     - Data de saída da fila.
     - Identificação de pacientes desistentes.
   - Salva os resultados no banco e em CSV.

3. **Funções Utilitárias** (`metodos.py`)
   - Conexão com bancos.
   - Escrita de logs em arquivo e simulação de log em banco.
   - Obtenção de usuário fictício.

---

## 📁 Estrutura dos Arquivos

├── criar_bancos_ficticios.py # Gera os bancos de dados fictícios

├── atualizar_filas.py # Atualiza o snapshot aplicando regras de negócio

├── metodos.py # Funções utilitárias de conexão e logs

├── logs/

│ └── acompanhamento_fila.txt # Logs de execução

├── conexao_principal.db # Banco gerado (snapshot)

├── conexao_secundaria.db # Banco gerado (histórico)

└── tb_imagem_fila_fev2025.csv # Exportação final

## ▶️ Como Executar

1° **Gerar os bancos fictícios:**

   - criar_bancos_ficticios.py


2° **Atualizar o snapshot:**

   - atualizar_filas.py


3° **Verificar resultados:**

   - Tabela tb_imagem_fila_fev2025 no conexao_principal.db

   - Arquivo tb_imagem_fila_fev2025.csv

   - Logs em logs/acompanhamento_fila.txt

## 📌 Lógica e Regras de Negócio

Identificação do 1º, 2º e 3º contato usando OFFSET no SQL.

Status Finalizado → quando há pelo menos um contato com "Atendido".

Status Confirmação Pendente → quando não há "Atendido".

Data de Saída → definida quando há "Atendido".

Paciente Desistente → quando as 3 primeiras tentativas foram "Sem retorno".

Reentrada → paciente pode ter múltiplos ID_FILA no histórico.

## 💡 Boas Práticas Utilizadas

Processamento em lotes para grandes volumes.

Consultas SQL realistas adaptadas ao contexto de negócio.

Separação clara entre geração de dados, processamento e utilitários.

Registro detalhado de logs para auditoria.

Uso de dados 100% fictícios com Faker.

## 📜 Aviso

Todos os dados utilizados neste projeto são fictícios, gerados por bibliotecas Python como Faker.
Não há qualquer vínculo com informações reais de pacientes ou empresas.
