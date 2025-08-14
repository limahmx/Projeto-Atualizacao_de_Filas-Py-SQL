"""
Gerar bancos fictícios com tamanho customizável, com histórico de contatos e status.
Autor: Lucas Lima Damasceno
Descrição:
    Este script gera bancos de dados fictícios para simular um case real de
    análise de dados. O banco gerado contém uma tabela de contatos com
    informações de nome, status, datas e resultado do contato.
"""

# criar_bancos_ficticios.py (executar antes de "atualizar_filas.py")
import sqlite3
import pandas as pd
import random
from datetime import datetime, timedelta
from faker import Faker

fake = Faker("pt_BR")
random.seed(42)

def criar_conexao(nome):
    return sqlite3.connect(f"{nome}.db")

###################### Configurar tamanho dos bancos ######################

num_clientes = 15000
tam_snapshot = 10000
tam_bd_historico = tam_snapshot * 10

###################### 1 - Criar lista fixa de clientes ######################

clientes = []
for id_cliente in range(1, num_clientes + 1):
    nome = fake.name()
    estado = fake.state()
    clientes.append({
        "ID_CLIENTE": id_cliente,
        "NOME": nome,
        "ESTADO": estado
    })
df_clientes = pd.DataFrame(clientes)

###################### 2 - BANCO PRINCIPAL (Snapshot fev/2025) ######################
conn_principal = criar_conexao("conexao_principal")

id_filas_snapshot = list(range(1, tam_snapshot + 1))  # 10.000 registros
snapshot_data = []
for id_fila in id_filas_snapshot:
    cliente = df_clientes.sample(1).iloc[0]
    snapshot_data.append({
        "ID_FILA": id_fila,
        "ID_CLIENTE": cliente["ID_CLIENTE"],
        "NOME": cliente["NOME"],
        "ESTADO": cliente["ESTADO"]
    })
df_snapshot = pd.DataFrame(snapshot_data)
df_snapshot.to_sql("tb_imagem_fila_fev2025", conn_principal, index=False, if_exists="replace")
conn_principal.close()

###################### 3 - BANCO SECUNDÁRIO (Histórico completo) ######################
conn_secundaria = criar_conexao("conexao_secundaria")

# Status
df_status = pd.DataFrame({
    "STATUS_ID": [1, 2, 3],
    "DESCRICAO": ["Em andamento", "Pendente", "Finalizado"]
})
df_status.to_sql("tb_status", conn_secundaria, index=False, if_exists="replace")

# Motivos
df_motivos = pd.DataFrame({
    "ID_MOTIVO": [1, 2, 3],
    "DESCRICAO": ["Agendado", "Sem retorno", "Atendido"]
})
df_motivos.to_sql("tb_motivos", conn_secundaria, index=False, if_exists="replace")

# Fila e Histórico
historico_filas = []
historico_contatos = []
id_filas_hist = list(range(1, tam_bd_historico + 1))  # 100.000 registros

for id_fila in id_filas_hist:
    cliente = df_clientes.sample(1).iloc[0]
    status_id = random.choice([1, 2, 3])
    historico_filas.append({
        "ID_FILA": id_fila,
        "ID_CLIENTE": cliente["ID_CLIENTE"],
        "NOME": cliente["NOME"],
        "ESTADO": cliente["ESTADO"],
        "STATUS_ID": status_id
    })

    # Criar histórico de contatos
    num_contatos = random.randint(1, 6)
    sem_retorno_count = 0
    fechado = False

    for i in range(num_contatos):
        data_contato = datetime.today() - timedelta(days=random.randint(1, 300))

        if not fechado:
            motivo_id = random.choice([1, 2, 3])
            if motivo_id == 2:  # Sem retorno
                sem_retorno_count += 1
                if sem_retorno_count == 3:
                    fechado = True
            else:
                sem_retorno_count = 0
        else:
            motivo_id = random.choice([1, 3])  # Só Agendado ou Atendido após fechamento

        historico_contatos.append({
            "ID_FILA": id_fila,
            "DATA_CONTATO": data_contato.strftime("%Y-%m-%d"),
            "ID_MOTIVO": motivo_id
        })

df_fila = pd.DataFrame(historico_filas)
df_fila.to_sql("tb_fila", conn_secundaria, index=False, if_exists="replace")

df_historico = pd.DataFrame(historico_contatos)
df_historico.to_sql("tb_historico", conn_secundaria, index=False, if_exists="replace")

conn_secundaria.close()

print("✅ Bancos fictícios criados com sucesso!")