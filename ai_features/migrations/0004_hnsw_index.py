from django.db import migrations
from pgvector.django import HnswIndex


class Migration(migrations.Migration):

    dependencies = [
        ('ai_features', '0003_documentchunk'),
    ]

    operations = [
        migrations.AddIndex(
            model_name='documentchunk',
            index=HnswIndex(
                name='docchunk_embedding_hnsw_idx',
                fields=['embedding'],
                opclasses=['vector_cosine_ops'],
            ),
        ),
    ]
