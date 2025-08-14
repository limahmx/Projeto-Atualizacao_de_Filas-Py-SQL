"""
Consulta de histórico em lotes para grandes volumes de dados.
Autor: Lucas Lima Damasceno
Descrição:
    Este script otimiza a consulta de um grande conjunto de IDs (1M+)
    em uma base de histórico massiva (10M+ registros), evitando
    sobrecarga de memória, timeouts no banco de dados e ERROS de SQL Injection.
    Em seguida, realiza o tratamento dos dados retornados, aplica regras de negócio,
    atualiza o banco SQL e gera um arquivo ".csv" para exportação.
"""

# atualizar_filas.py (executar após "criar_bancos_ficticios.py")
import pandas as pd
import numpy as np
from datetime import datetime as dt
import metodos as mc

###################### 1 - PARÂMETROS E CONEXÕES ######################
data_atual = dt.today().strftime('%Y-%m-%d')
usuario = mc.obter_usuario()
arquivo_log = 'logs/acompanhamento_fila.txt'

mc.registrar_log_txt(arquivo_log, f"Iniciando rotina - {data_atual}")
mc.registrar_log_txt(arquivo_log, mc.testar_conexao("conexao_principal"))
mc.registrar_log_txt(arquivo_log, mc.testar_conexao("conexao_secundaria"))

###################### 2 - LEITURA DO SNAPSHOT criado por "criar_bancos_ficticios.py" ######################
try:
    conn_principal = mc.conectar("conexao_principal")
    df_snapshot = pd.read_sql("SELECT * FROM tb_imagem_fila_fev2025", conn_principal)
    conn_principal.close()
    mc.registrar_log_txt(arquivo_log, "BLOCO 2: Snapshot carregado com sucesso.")
except Exception as e:
    mc.registrar_log_txt(arquivo_log, f"BLOCO 2: ERRO ao carregar snapshot: {e}")

###################### 3 - FUNÇÃO DE DIVISÃO DE LOTES ######################
    
    """
    Gera sublistas (lotes) de tamanho definido a partir de uma lista original.
    
    Args:
        lista (list): Lista completa de elementos.
        tamanho (int): Número máximo de elementos por lote.
        
    Yields:
        list: Sublista (lote) de elementos.
    """

def dividir_lista(lista, tamanho):

    
    for i in range(0, len(lista), tamanho):
        yield lista[i:i + tamanho]

lista_ids = [int(i) for i in df_snapshot['ID_FILA']]
tamanho_lote = 1000
todos_resultados = []

###################### 4 - CONSULTA EM LOTE AO HISTÓRICO ######################
try:
    conn_secundaria = mc.conectar("conexao_secundaria")

    # ========================================================
    # Processamento em lotes
    # ========================================================

    for lote in dividir_lista(lista_ids, tamanho_lote):
        placeholders = ', '.join(['?'] * len(lote))
        
        query = f"""
            SELECT DISTINCT
                f.ID_FILA,
                s.DESCRICAO AS "STATUS_ATUAL",

                -- 1º contato
                (SELECT h.DATA_CONTATO
                 FROM tb_historico h
                 WHERE f.ID_FILA = h.ID_FILA
                 ORDER BY h.DATA_CONTATO ASC
                 LIMIT 1 OFFSET 0) AS "DT_CONTATO1",
                (SELECT m.DESCRICAO
                 FROM tb_historico h
                 INNER JOIN tb_motivos m ON m.ID_MOTIVO = h.ID_MOTIVO
                 WHERE f.ID_FILA = h.ID_FILA
                 ORDER BY h.DATA_CONTATO ASC
                 LIMIT 1 OFFSET 0) AS "RESULTADO_CONTATO1",

                -- 2º contato
                (SELECT h.DATA_CONTATO
                 FROM tb_historico h
                 WHERE f.ID_FILA = h.ID_FILA
                 ORDER BY h.DATA_CONTATO ASC
                 LIMIT 1 OFFSET 1) AS "DT_CONTATO2",
                (SELECT m.DESCRICAO
                 FROM tb_historico h
                 INNER JOIN tb_motivos m ON m.ID_MOTIVO = h.ID_MOTIVO
                 WHERE f.ID_FILA = h.ID_FILA
                 ORDER BY h.DATA_CONTATO ASC
                 LIMIT 1 OFFSET 1) AS "RESULTADO_CONTATO2",

                -- 3º contato
                (SELECT h.DATA_CONTATO
                 FROM tb_historico h
                 WHERE f.ID_FILA = h.ID_FILA
                 ORDER BY h.DATA_CONTATO ASC
                 LIMIT 1 OFFSET 2) AS "DT_CONTATO3",
                (SELECT m.DESCRICAO
                 FROM tb_historico h
                 INNER JOIN tb_motivos m ON m.ID_MOTIVO = h.ID_MOTIVO
                 WHERE f.ID_FILA = h.ID_FILA
                 ORDER BY h.DATA_CONTATO ASC
                 LIMIT 1 OFFSET 2) AS "RESULTADO_CONTATO3"

            FROM tb_fila f
            LEFT JOIN tb_status s ON f.STATUS_ID = s.STATUS_ID
            WHERE f.ID_FILA IN ({placeholders})
        """
        try:
            resultados = pd.read_sql(query, conn_secundaria, params=tuple(lote))
            todos_resultados.append(resultados)
        except Exception as e:
            mc.registrar_log_txt(arquivo_log, f"Bloco 4: ERRO no lote {lote[0]}-{lote[-1]}: {e}")
    conn_secundaria.close()
    
    # ========================================================
    # Unindo todos os resultados em um único DataFrame
    # ========================================================
    df_resultados = pd.concat(todos_resultados, ignore_index=True)
    mc.registrar_log_txt(arquivo_log, "Bloco 4: Histórico carregado com sucesso.")

except Exception as e:
    mc.registrar_log_txt(arquivo_log, f"Bloco 4: ERRO ao carregar histórico: {e}")

###################### 5 - MERGE SNAPSHOT + HISTÓRICO ######################
try:
    df_final = pd.merge(df_snapshot, df_resultados, on="ID_FILA", how="left")
    mc.registrar_log_txt(arquivo_log, "Bloco 5: Merge concluído com sucesso.")
except Exception as e:
    mc.registrar_log_txt(arquivo_log, f"Bloco 5: ERRO no merge: {e}")

###################### 6 - GARANTIA DE COLUNAS ######################
for col in ["RESULTADO_CONTATO1", "RESULTADO_CONTATO2", "RESULTADO_CONTATO3"]:
    if col not in df_final.columns:
        df_final[col] = None

###################### 7 - REGRAS DE NEGÓCIO (VETORIZADO) ######################

# Criar colunas iniciais
df_final["DATA_SAIDA"] = pd.NaT
df_final["HISTORICO_DESISTENTE"] = "N"

# Lista de contatos em colunas para facilitar
contato_cols = ["RESULTADO_CONTATO1", "RESULTADO_CONTATO2", "RESULTADO_CONTATO3"]

# --- Regra STATUS_ATUAL ---
# Finalizado se tem "Atendido"
df_final.loc[df_final[contato_cols].isin(["Atendido"]).any(axis=1), "STATUS_ATUAL"] = "Finalizado"

# --- Regra STATUS_ATUAL ---
# Confirmação Pendente se não tem "Atendido"
df_final.loc[~df_final[contato_cols].isin(["Atendido"]).any(axis=1), "STATUS_ATUAL"] = "Confirmação Pendente"

# --- Regra DATA_SAIDA ---
df_final.loc[df_final[contato_cols].isin(["Atendido"]).any(axis=1), "DATA_SAIDA"] = data_atual

# --- Regra HISTORICO_DESISTENTE ---
# Desistente se todas as 3 tentativas foram "Sem retorno" (não nulo) e não tem outro valor
mask_desistente = (
    df_final[contato_cols].apply(lambda x: all(c == "Sem retorno" for c in x if pd.notna(c)), axis=1) &
    (df_final[contato_cols].notna().sum(axis=1) == 3)
)

df_final.loc[mask_desistente, "HISTORICO_DESISTENTE"] = "S"
df_final.loc[mask_desistente, "STATUS_ATUAL"] = "DESISTENTE"

###################### 8 - TRATAMENTO DE TIPOS ######################
try:
    df_final["DATA_SAIDA"] = pd.to_datetime(df_final["DATA_SAIDA"], errors="coerce")
    for col in ["STATUS_ATUAL","RESULTADO_CONTATO1", "RESULTADO_CONTATO2", "RESULTADO_CONTATO3", "HISTORICO_DESISTENTE"]:
        df_final[col] = df_final[col].astype(str)
except Exception as e:
    mc.registrar_log_txt(arquivo_log, f"Bloco 8: ERRO no tratamento de tipos: {e}")

###################### 9 - ATUALIZAÇÃO NO BANCO ######################
try:
    conn_principal = mc.conectar("conexao_principal")
    df_final.to_sql("tb_imagem_fila_fev2025", conn_principal, index=False, if_exists="replace")
    df_final.to_csv("tb_imagem_fila_fev2025.csv",index=False)
    conn_principal.close()
    mc.registrar_log_txt(arquivo_log, "Bloco 9: Tabela atualizada com sucesso.")
except Exception as e:
    mc.registrar_log_txt(arquivo_log, f"Bloco 9: ERRO ao atualizar banco: {e}")
    mc.registrar_log_bd("atualizacao_fila", f"ERRO - {str(e)[:290]}", "GETDATE()", "ERRO", "102")