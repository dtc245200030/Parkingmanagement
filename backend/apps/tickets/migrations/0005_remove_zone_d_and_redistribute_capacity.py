from django.db import migrations


def remove_zone_d_and_redistribute_capacity(apps, schema_editor):
    KhuVuc = apps.get_model("parking", "KhuVuc")
    LuotGuiXe = apps.get_model("tickets", "LuotGuiXe")
    ParkingSpot = apps.get_model("parking", "ParkingSpot")

    zone_a = KhuVuc.objects.filter(ten_khu_vuc="Khu A").first()
    zone_b = KhuVuc.objects.filter(ten_khu_vuc="Khu B").first()
    zone_c = KhuVuc.objects.filter(ten_khu_vuc="Khu C").first()
    zone_d = KhuVuc.objects.filter(ten_khu_vuc="Khu D").first()

    if not all([zone_a, zone_b, zone_c]):
        return

    zone_a.suc_chua_toi_da = 140
    zone_b.suc_chua_toi_da = 90
    zone_c.suc_chua_toi_da = 70
    zone_a.save(update_fields=["suc_chua_toi_da"])
    zone_b.save(update_fields=["suc_chua_toi_da"])
    zone_c.save(update_fields=["suc_chua_toi_da"])

    if zone_d:
        LuotGuiXe.objects.filter(khu_vuc=zone_d).update(khu_vuc=zone_a)
        ParkingSpot.objects.filter(khu_vuc=zone_d).update(khu_vuc=zone_a)
        zone_d.delete()


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0004_move_zone_d_sessions_to_zone_a"),
    ]

    operations = [
        migrations.RunPython(remove_zone_d_and_redistribute_capacity, migrations.RunPython.noop),
    ]
