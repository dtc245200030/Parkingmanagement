from django.db import migrations


def move_zone_d_sessions_to_zone_a(apps, schema_editor):
    KhuVuc = apps.get_model("parking", "KhuVuc")
    LuotGuiXe = apps.get_model("tickets", "LuotGuiXe")

    zone_a = KhuVuc.objects.filter(ten_khu_vuc="Khu A").first()
    zone_d = KhuVuc.objects.filter(ten_khu_vuc="Khu D").first()
    if zone_a and zone_d:
        LuotGuiXe.objects.filter(khu_vuc=zone_d).update(khu_vuc=zone_a)


def move_zone_a_sessions_back_to_zone_d(apps, schema_editor):
    # Không thể xác định an toàn lượt nào vốn thuộc Khu D sau khi đã gộp.
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("tickets", "0003_luotguixe_monthly_ticket"),
    ]

    operations = [
        migrations.RunPython(
            move_zone_d_sessions_to_zone_a,
            move_zone_a_sessions_back_to_zone_d,
        ),
    ]
