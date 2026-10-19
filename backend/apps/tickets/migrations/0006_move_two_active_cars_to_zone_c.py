from django.db import migrations


CAR_PLATES = ["51B-77831", "43A-88888"]


def move_two_active_cars_to_zone_c(apps, schema_editor):
    KhuVuc = apps.get_model("parking", "KhuVuc")
    LuotGuiXe = apps.get_model("tickets", "LuotGuiXe")

    zone_a = KhuVuc.objects.filter(ten_khu_vuc="Khu A").first()
    zone_c = KhuVuc.objects.filter(ten_khu_vuc="Khu C").first()
    if zone_a and zone_c:
        LuotGuiXe.objects.filter(
            khu_vuc=zone_a,
            trang_thai_luot="Đang gửi",
            bien_so_xe_kiem_tra__in=CAR_PLATES,
        ).update(khu_vuc=zone_c)


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0005_remove_zone_d_and_redistribute_capacity"),
    ]

    operations = [
        migrations.RunPython(move_two_active_cars_to_zone_c, migrations.RunPython.noop),
    ]
