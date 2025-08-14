from scripts.queries.data_queries import contar_registros


def inserir_dados(conn, df, nome_tabela):
    """Insere DataFrame no DuckDB"""
    conn.register("temp_df", df)
    conn.execute(f"INSERT INTO {nome_tabela} SELECT * FROM temp_df")
    conn.unregister("temp_df")


def verificar_tabela_vazia(conn, nome_tabela):
    """Verifica se uma tabela está vazia"""
    return contar_registros(conn, nome_tabela) == 0


def popular_se_vazio(conn, nome_tabela, funcao_popular, *args, **kwargs):
    """Popula uma tabela apenas se ela estiver vazia"""
    if verificar_tabela_vazia(conn, nome_tabela):
        funcao_popular(conn, *args, **kwargs)
    else:
        print(f"{nome_tabela} já possui dados. Nenhuma inserção realizada.")