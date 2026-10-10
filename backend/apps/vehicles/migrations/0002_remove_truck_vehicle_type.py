from django.db import migrations


def remove_truck_vehicle_type(apps, schema_editor):
    LoaiXe = apps.get_model("vehicles", "LoaiXe")
    PhuongTien = apps.get_model("vehicles", "PhuongTien")

    car_type = LoaiXe.objects.filter(ten_loai_xe="Oto").first()
    truck_types = LoaiXe.objects.filter(ten_loai_xe__in=["XeTai", "TRUCK"])
    if car_type:
        PhuongTien.objects.filter(loai_xe__in=truck_types).update(loai_xe=car_type)
    truck_types.delete()


class Migration(migrations.Migration):
    dependencies = [("vehicles", "0001_initial")]

    operations = [migrations.RunPython(remove_truck_vehicle_type, migrations.RunPython.noop)]
