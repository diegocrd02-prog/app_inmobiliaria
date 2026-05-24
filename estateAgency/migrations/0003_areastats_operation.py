# Generated manually for AreaStats operation cache

from django.db import migrations, models


def clear_old_area_stats(apps, schema_editor):
    AreaStats = apps.get_model('estateAgency', 'AreaStats')
    AreaStats.objects.all().delete()


class Migration(migrations.Migration):

    dependencies = [
        ('estateAgency', '0002_property_rental_type'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='areastats',
            unique_together=set(),
        ),
        migrations.AddField(
            model_name='areastats',
            name='operation_type',
            field=models.CharField(
                choices=[('sale', 'Sale'), ('rent', 'Rent')],
                default='sale',
                max_length=10,
            ),
        ),
        migrations.AddField(
            model_name='areastats',
            name='rental_type',
            field=models.CharField(
                blank=True,
                choices=[('', 'No rental'), ('short', 'Short Term'), ('long', 'Long Term')],
                default='',
                max_length=10,
            ),
        ),
        migrations.RunPython(clear_old_area_stats, migrations.RunPython.noop),
        migrations.AlterUniqueTogether(
            name='areastats',
            unique_together={('location', 'date', 'operation_type', 'rental_type')},
        ),
    ]
