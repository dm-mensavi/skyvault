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

    operations = [
        # 1. Drop old HNSW index (was built for 1536-dim vectors)
        migrations.RunSQL(
            sql="DROP INDEX IF EXISTS ai_features_documentchunk_embedding_hnsw;",
            reverse_sql="",  # can't recreate the 1536-dim index in rollback — handled below
        ),

        # 2. Clear all existing chunk rows (old 1536-dim vectors are incompatible)
        migrations.RunSQL(
            sql="DELETE FROM ai_features_documentchunk;",
            reverse_sql="",
        ),

        # 3. Alter embedding column to vector(384)
        migrations.RunSQL(
            sql="ALTER TABLE ai_features_documentchunk ALTER COLUMN embedding TYPE vector(384);",
            reverse_sql="ALTER TABLE ai_features_documentchunk ALTER COLUMN embedding TYPE vector(1536);",
        ),

        # 4. Recreate HNSW index for cosine distance (384-dim)
        migrations.RunSQL(
            sql=(
                "CREATE INDEX ai_features_documentchunk_embedding_hnsw "
                "ON ai_features_documentchunk "
                "USING hnsw (embedding vector_cosine_ops) "
                "WITH (m = 16, ef_construction = 64);"
            ),
            reverse_sql="DROP INDEX IF EXISTS ai_features_documentchunk_embedding_hnsw;",
        ),

        # 5. Update Django model field definition so makemigrations stays in sync
        migrations.AlterField(
            model_name="documentchunk",
            name="embedding",
            field=pgvector.django.vector.VectorField(dimensions=384),
        ),
    ]
