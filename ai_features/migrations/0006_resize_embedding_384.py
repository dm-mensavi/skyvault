"""
Migration 0006: Resize DocumentChunk.embedding from 1536-dim (OpenAI) to 384-dim
(sentence-transformers all-MiniLM-L6-v2).

Steps:
  1. Drop existing HNSW index on the embedding column
  2. Clear all existing chunks (incompatible dimensions — must re-index)
  3. Alter the column type to vector(384)
  4. Recreate HNSW index for cosine distance
  5. Update the Django field definition on the model
"""
import pgvector.django.vector
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("ai_features", "0005_storageinsight_and_more"),
    ]

def forwards_func(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("DROP INDEX IF EXISTS ai_features_documentchunk_embedding_hnsw;")
            cursor.execute("DELETE FROM ai_features_documentchunk;")
            cursor.execute("ALTER TABLE ai_features_documentchunk ALTER COLUMN embedding TYPE vector(384);")
            cursor.execute(
                "CREATE INDEX ai_features_documentchunk_embedding_hnsw "
                "ON ai_features_documentchunk "
                "USING hnsw (embedding vector_cosine_ops) "
                "WITH (m = 16, ef_construction = 64);"
            )

def reverse_func(apps, schema_editor):
    if schema_editor.connection.vendor == 'postgresql':
        with schema_editor.connection.cursor() as cursor:
            cursor.execute("DROP INDEX IF EXISTS ai_features_documentchunk_embedding_hnsw;")
            cursor.execute("ALTER TABLE ai_features_documentchunk ALTER COLUMN embedding TYPE vector(1536);")


class Migration(migrations.Migration):

    dependencies = [
        ("ai_features", "0005_storageinsight_and_more"),
    ]

    operations = [
        migrations.RunPython(forwards_func, reverse_code=reverse_func),
        migrations.AlterField(
            model_name="documentchunk",
            name="embedding",
            field=pgvector.django.vector.VectorField(dimensions=384),
        ),
    ]
