from django.db import migrations


def expand_medium_parking_capacity(apps, schema_editor):
    KhuVuc = apps.get_model("parking", "KhuVuc")
    capacities = {
        "Khu A": 200,
        "Khu B": 200,
        "Khu C": 100,
    }

    for zone_name, capacity in capacities.items():
        KhuVuc.objects.filter(ten_khu_vuc=zone_name).update(
            suc_chua_toi_da=capacity
        )


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0007_normalize_vehicle_zones"),
    ]

    operations = [
        migrations.RunPython(
            expand_medium_parking_capacity,
            migrations.RunPython.noop,
        ),
    ]
