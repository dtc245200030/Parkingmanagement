from django.db import migrations


def remove_stale_zone_d(apps, schema_editor):
    KhuVuc = apps.get_model("parking", "KhuVuc")
    ParkingSpot = apps.get_model("parking", "ParkingSpot")
    LuotGuiXe = apps.get_model("tickets", "LuotGuiXe")

    zone_a = KhuVuc.objects.filter(ten_khu_vuc="Khu A").first()
    zone_d = KhuVuc.objects.filter(ten_khu_vuc="Khu D").first()

    if not zone_d:
        return

    if zone_a:
        LuotGuiXe.objects.filter(khu_vuc=zone_d).update(khu_vuc=zone_a)
        ParkingSpot.objects.filter(khu_vuc=zone_d).update(khu_vuc=zone_a)

    zone_d.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0008_expand_medium_parking_capacity"),
    ]

    operations = [
        migrations.RunPython(remove_stale_zone_d, migrations.RunPython.noop),
    ]
