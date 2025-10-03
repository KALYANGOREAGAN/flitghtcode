# Generated manually as a fallback

from django.db import migrations, models
import django.db.models.deletion
from django.conf import settings


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.CreateModel(
            name='FlightRoute',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('origin', models.CharField(max_length=100)),
                ('destination', models.CharField(max_length=100)),
                ('aircraft_type', models.CharField(max_length=100)),
                ('distance_km', models.FloatField()),
                ('fuel_consumption_kg', models.FloatField()),
            ],
            options={
                'unique_together': {('origin', 'destination', 'aircraft_type')},
            },
        ),
        migrations.CreateModel(
            name='EmissionRecord',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('calculation_date', models.DateTimeField(auto_now_add=True)),
                ('co2_kg', models.FloatField()),
                ('fuel_saved_kg', models.FloatField(default=0)),
                ('percent_improvement', models.FloatField(default=0)),
                ('route', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='emissions', to='optimiser.flightroute')),
            ],
        ),
        migrations.CreateModel(
            name='PassengerEcoScore',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('points', models.IntegerField(default=0)),
                ('flights_optimized', models.IntegerField(default=0)),
                ('total_co2_saved', models.FloatField(default=0)),
                ('current_badge', models.CharField(choices=[('NONE', 'No Badge'), ('BRONZE', 'Bronze Eco-Flyer'), ('SILVER', 'Silver Eco-Flyer'), ('GOLD', 'Gold Eco-Flyer'), ('PLATINUM', 'Platinum Eco-Flyer')], default='NONE', max_length=10)),
                ('user', models.OneToOneField(on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]
