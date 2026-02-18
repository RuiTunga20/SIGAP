#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar dependências
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Coletar arquivos estáticos
python manage.py collectstatic --no-input

python manage.py makemigrations
# Aplicar migrações do banco de dados
python manage.py migrate

# Arranque: gunicorn com uvicorn workers (definido no Procfile ou no Render dashboard)
# gunicorn SGA.asgi:application --worker-class uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:$PORT

# Popular Banco de Dados (Ordem Importante)

echo "--- Populando Municípios ---"
python manage.py populate_municipios

echo "--- Populando MAT ---"
python popular_mat.py

echo "--- Populando Administrações ---"
python popular_administracoes.py
python popular_governos.py

echo "--- Populando Departamentos Base ---"
python popular.py

echo "--- Populando Departamentos e Secções (Decreto 270/24) ---"
python popular_departamentos.py

echo "--- Populando Tipos de Documentos ---"
python tipodocumentos.py

echo "--- Adicionando Adjuntos por Tipo ---"
python adicionar_adjuntos_tipo_a.py
python adicionar_adjuntos_tipo_b.py
python adicionar_adjuntos_tipo_c.py
python adicionar_adjuntos_tipo_d.py
python adicionar_adjuntos_tipo_e.py

echo "--- Criando Usuários Padrão das Administrações ---"
python criar_usuarios_padrao.py

echo "--- Criando Super Admin MAT ---"
python create_super_mat.py

echo "✅ Build concluído com sucesso!"
