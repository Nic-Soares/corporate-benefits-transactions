import yaml
import os

def load_config(file_path: str):
    """
    Carrega um arquivo de configuração YAML e retorna seu conteúdo.

    Args:
        file_path (str): O caminho completo ou relativo para o arquivo YAML.

    Returns:
        dict: O conteúdo do arquivo YAML em formato de dicionário.
              Retorna um dicionário vazio se o arquivo não for encontrado ou
              se houver um erro de leitura.
    """
    try:
        with open(file_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    except FileNotFoundError:
        print(f"Erro: O arquivo de configuração não foi encontrado em '{file_path}'.")
        return {}
    except yaml.YAMLError as exc:
        print(f"Erro ao analisar o arquivo YAML em '{file_path}': {exc}")
        return {}

# Exemplo de uso
base_dir = os.path.dirname(os.path.abspath(__file__))

data_volumes_config = load_config(os.path.join(base_dir, '../../config/data_volumes.yaml'))
business_rules = load_config(os.path.join(base_dir, '../../config/business_rules.yaml'))
database_config = load_config(os.path.join(base_dir, '../../config/database.yaml'))
