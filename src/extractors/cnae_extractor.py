import kagglehub
import shutil
import os

# Baixa a última versão do dataset
path = kagglehub.dataset_download("diovanimerlo/cnae-brazil-2024")
print("Path to dataset files:", path)

# Diretório de destino dentro do projeto
dest_dir = os.path.join(os.path.dirname(__file__), "../../data/raw")

# Copia todos os arquivos do dataset para o diretório 'data'
for filename in os.listdir(path):
    src_file = os.path.join(path, filename)
    dest_file = os.path.join(dest_dir, filename)
    shutil.copy2(src_file, dest_file)
    print(f"Arquivo copiado para: {dest_file}")
