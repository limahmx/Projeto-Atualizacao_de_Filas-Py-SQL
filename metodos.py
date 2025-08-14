"""
Metodos para gerar conexões com bancos de dados SQL, usuários fictícios e arquivos de logs.
Autor: Lucas Lima Damasceno
Descrição:
    Este script gera usuários fictícios, conexões com bancos de dados SQL e arquivos de logs.
"""


# metodos.py
import sqlite3
import os
from datetime import datetime as dt

def obter_usuario():
    """Retorna o nome fictício do usuário."""
    return "usuario_ficticio"

def testar_conexao(nome_conexao):
    """Simula teste de conexão com banco."""
    msg = f"[TESTE] Conexão {nome_conexao} OK"
    print(msg)
    return msg

def conectar(nome_conexao):
    """Retorna conexão SQLite para simulação."""
    print(f"[CONECTANDO] {nome_conexao}.db")
    return sqlite3.connect(f"{nome_conexao}.db")

def registrar_log_txt(caminho_arquivo, mensagem):
    """Escreve log em arquivo."""
    os.makedirs(os.path.dirname(caminho_arquivo), exist_ok=True)
    with open(caminho_arquivo, "a", encoding="utf-8") as f:
        f.write(f"{dt.now()} - {mensagem}\n")

def registrar_log_bd(tabela, mensagem, data_execucao, status, codigo):
    """Simula registro em log de banco."""
    print(f"[LOG BD] {tabela} | {mensagem} | {data_execucao} | {status} | {codigo}")