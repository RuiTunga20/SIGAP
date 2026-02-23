#!/usr/bin/env bash
# exit on error
set -o errexit

# Instalar dependências
pip install --upgrade pip setuptools wheel
pip install -r requirements.txt

# Coletar arquivos estáticos
python manage.py collectstatic --no-input

# Sincronizar banco de dados
if [ "$RESET_DB" == "1" ]; then
    echo "⚠️ HARD RESET: Apagando e recriando esquema público..."
    # Comando para limpar o banco (Postgres) - Corrigido para usar pipe
    echo "DROP SCHEMA public CASCADE; CREATE SCHEMA public;" | python manage.py dbshell
    python manage.py migrate --no-input
else
    # Sincronização normal
    python manage.py migrate --no-input
fi

# Arranque: gunicorn com uvicorn workers (definido no Procfile ou no Render dashboard)
# gunicorn SGA.asgi:application --worker-class uvicorn.workers.UvicornWorker --workers 4 --bind 0.0.0.0:$PORT

# Popular Banco de Dados (Ordem Importante)

# echo "--- Populando Municípios (LEGADO) ---"
# python manage.py populate_municipios # Removido em favor de popular_administracoes.py

echo "--- Populando MAT ---"
python popular_mat.py

echo "--- Populando Administrações ---"
python popular_administracoes.py
python popular_governos.py
python popular_seccoes_especiais.py

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
