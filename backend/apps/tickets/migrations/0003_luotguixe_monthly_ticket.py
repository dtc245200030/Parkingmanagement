from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [("tickets", "0002_remove_vethang_the_xe_remove_luotguixe_ve_xe_and_more")]

    operations = [
        migrations.AddField(
            model_name="luotguixe",
            name="la_ve_thang",
            field=models.BooleanField(default=False, verbose_name="Lượt gửi sử dụng vé tháng"),
        ),
        migrations.AddField(
            model_name="luotguixe",
            name="ve_thang",
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name="luot_gui_list", to="tickets.vethang", verbose_name="Vé tháng áp dụng"),
        ),
    ]
