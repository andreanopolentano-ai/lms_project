# Generated manually for the Celery homework.

import django.utils.timezone
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("materials", "0002_course_owner_lesson_owner"),
    ]

    operations = [
        migrations.AddField(
            model_name="course",
            name="updated_at",
            field=models.DateTimeField(
                default=django.utils.timezone.now,
                verbose_name="Дата обновления",
            ),
            preserve_default=False,
        ),
        migrations.AlterField(
            model_name="course",
            name="updated_at",
            field=models.DateTimeField(
                auto_now=True,
                verbose_name="Дата обновления",
            ),
        ),
    ]
