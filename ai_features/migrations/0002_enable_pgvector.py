from django.db import migrations
from pgvector.django import VectorExtension


class Migration(migrations.Migration):

    dependencies = [
        ('ai_features', '0001_initial'),
    ]

    operations = [
        VectorExtension(),
    ]
