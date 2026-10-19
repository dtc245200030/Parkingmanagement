from django.db import migrations


def normalize_vehicle_zones(apps, schema_editor):
    KhuVuc = apps.get_model("parking", "KhuVuc")
    LuotGuiXe = apps.get_model("tickets", "LuotGuiXe")

    zones = {
        zone.ten_khu_vuc: zone
        for zone in KhuVuc.objects.filter(ten_khu_vuc__in=["Khu A", "Khu B", "Khu C"])
    }
    if len(zones) != 3:
        return

    # Quy ước duy nhất: A = ô tô, B = xe máy, C = xe đạp.
    LuotGuiXe.objects.filter(loai_xe__ten_loai_xe__in=["Oto", "CAR", "Oto4Cho", "Oto7Cho"]).update(
        khu_vuc=zones["Khu A"]
    )
    LuotGuiXe.objects.filter(loai_xe__ten_loai_xe__in=["XeMay", "MOTORBIKE"]).update(
        khu_vuc=zones["Khu B"]
    )
    LuotGuiXe.objects.filter(loai_xe__ten_loai_xe__in=["XeDap", "BICYCLE"]).update(
        khu_vuc=zones["Khu C"]
    )


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0006_move_two_active_cars_to_zone_c"),
    ]

    operations = [
        migrations.RunPython(normalize_vehicle_zones, migrations.RunPython.noop),
    ]
