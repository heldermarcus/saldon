import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")
django.setup()

from django.apps import apps
from django.db import connection

models = apps.get_models()
tables = [model._meta.db_table for model in models]

success = 0
with connection.cursor() as cursor:
    for table in tables:
        try:
            cursor.execute(f'ALTER TABLE "{table}" ENABLE ROW LEVEL SECURITY;')
            success += 1
            print(f"OK: RLS ativado para a tabela: {table}")
        except Exception as e:
            print(f"ERRO na tabela {table}: {e}")

print(f"\nFinalizado! RLS ativado em {success} de {len(tables)} tabelas.")
