"""Management command khởi tạo dữ liệu mẫu chuẩn hóa cho tất cả các bảng trong CSDL."""

from datetime import datetime, timedelta
from decimal import Decimal
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.parking.models import BangGia, KhuVuc, ParkingSpot
from apps.reports.models import BaoCaoThongKe
from apps.tickets.models import LuotGuiXe, VeThang, VeXe
from apps.users.models import NguoiDung, VaiTro
from apps.vehicles.models import LoaiXe, PhuongTien


class Command(BaseCommand):
    """Command nạp dữ liệu khởi tạo ban đầu cho hệ thống ParkAI (Users, Vehicles, Spots, Pricing, Tickets,...)."""

    help = "Nap du lieu mau khoi tao chuan hoa cho 10 bang CSDL ParkAI"

    def handle(self, *args, **options):
        """Thực thi khởi tạo dữ liệu mẫu cho 10 bảng CSDL."""

        self.stdout.write("[1/10] Khoi tao danh muc VaiTro...")

        # 1. Bảng VaiTro
        vt_admin, _ = VaiTro.objects.get_or_create(
            ten_vai_tro="QuanLy",
            defaults={"mo_ta": "Toan quyen he thong — thong ke, cai dat, quan ly nhan vien"}
        )
        vt_staff, _ = VaiTro.objects.get_or_create(
            ten_vai_tro="NhanVien",
            defaults={"mo_ta": "Ghi nhan xe vao/ra, tra cuu luot xe, quan ly ve thang"}
        )
        # 2. Bảng NguoiDung
        self.stdout.write("[2/10] Khoi tao NguoiDung (admin, mai, hung)...")
        u_admin, _ = NguoiDung.objects.get_or_create(
            ten_dang_nhap="admin",
            defaults={
                "ho_ten": "Nguyen Van Quan",
                "so_dien_thoai": "0901888999",
                "email": "admin@baidoxe.vn",
                "vai_tro": vt_admin,
                "trang_thai": "Hoạt động",
                "ca_lam_viec": "Ca hành chính (8h–17h) • Tất cả khu",
            }
        )
        u_admin.set_password("admin123")
        u_admin.save()

        u_mai, _ = NguoiDung.objects.get_or_create(
            ten_dang_nhap="mai",
            defaults={
                "ho_ten": "Tran Thi Mai",
                "so_dien_thoai": "0918222333",
                "email": "mai@baidoxe.vn",
                "vai_tro": vt_staff,
                "trang_thai": "Hoạt động",
                "ca_lam_viec": "Ca sáng (6h–14h) • Khu A, B",
            }
        )
        u_mai.set_password("123456")
        u_mai.save()

        u_hung, _ = NguoiDung.objects.get_or_create(
            ten_dang_nhap="hung",
            defaults={
                "ho_ten": "Le Van Hung",
                "so_dien_thoai": "0987333444",
                "email": "hung@baidoxe.vn",
                "vai_tro": vt_staff,
                "trang_thai": "Hoạt động",
                "ca_lam_viec": "Ca chiều (14h–22h) • Khu C, D",
            }
        )
        u_hung.set_password("123456")
        u_hung.save()

        """Removed legacy demo account.
            ten_dang_nhap="removed-legacy-account",
            defaults={
                "ho_ten": "Tran Thi Mai (Truc ca)",
                "so_dien_thoai": "0918222333",
                "email": "removed@example.invalid",
                "vai_tro": vt_staff,
                "trang_thai": "Hoạt động",
                "ca_lam_viec": "Ca sáng (6h–14h) • Khu A, B",
            }
        )
        removed_user.set_unusable_password()
        """

        # 3. Bảng KhuVuc
        self.stdout.write("[3/10] Khoi tao 4 KhuVuc (300 cho)...")
        zones_data = [
            ("Khu A", 120, "Khu vực chuyên dành cho xe máy"),
            ("Khu B", 80, "Khu vực xe máy và xe đạp"),
            ("Khu C", 60, "Khu vực bãi đỗ ô tô 4-7 chỗ"),
            ("Khu D", 40, "Khu vực ô tô ngoài trời & tải nhỏ"),
        ]
        zone_objs = {}
        for name, cap, desc in zones_data:
            z, _ = KhuVuc.objects.get_or_create(
                ten_khu_vuc=name,
                defaults={"suc_chua_toi_da": cap, "mo_ta": desc}
            )
            z.suc_chua_toi_da = cap
            z.mo_ta = desc
            z.save()
            zone_objs[name] = z

        # 4. Bảng LoaiXe
        self.stdout.write("[4/10] Khoi tao LoaiXe...")
        types_data = [
            ("XeMay", "Xe máy số & tay ga"),
            ("Oto", "Ô tô từ 4 đến 7 chỗ ngồi"),
            ("XeDap", "Xe đạp thể thao & xe đạp điện"),
            ("XeTai", "Xe tải nhẹ dưới 2.5 tấn"),
        ]
        type_objs = {}
        for code, desc in types_data:
            lx, _ = LoaiXe.objects.get_or_create(
                ten_loai_xe=code,
                defaults={"mo_ta": desc}
            )
            type_objs[code] = lx

        # 5. Bảng BangGia
        self.stdout.write("[5/10] Khoi tao BangGia...")
        prices = [
            (type_objs["XeMay"], "VeLuot", Decimal("5000"), 60, Decimal("5000")),
            (type_objs["XeMay"], "VeThang", Decimal("120000"), 43200, Decimal("0")),
            (type_objs["Oto"], "VeLuot", Decimal("20000"), 60, Decimal("20000")),
            (type_objs["Oto"], "VeThang", Decimal("1200000"), 43200, Decimal("0")),
            (type_objs["XeDap"], "VeLuot", Decimal("2000"), 60, Decimal("2000")),
            (type_objs["XeDap"], "VeThang", Decimal("50000"), 43200, Decimal("0")),
        ]
        for lx, apply_type, base, dur, inc in prices:
            BangGia.objects.get_or_create(
                loai_xe=lx,
                loai_ap_dung=apply_type,
                defaults={
                    "gia_co_ban": base,
                    "don_vi_thoi_gian_phut": dur,
                    "gia_tang_them": inc,
                }
            )

        # 6, 7, 8. Bảng PhuongTien, VeXe, LuotGuiXe
        self.stdout.write("[6,7,8/10] Khoi tao 12 luot xe dang gui va cac luot da hoan tat...")
        now = timezone.now()
        active_vehicles = [
            ("51A-12345", "XeMay", "Khu A", 120, Decimal("15000")),
            ("43B-23456", "XeMay", "Khu A", 180, Decimal("20000")),
            ("51C-11111", "XeMay", "Khu A", 60, Decimal("10000")),
            ("15C-34567", "XeMay", "Khu B", 35, Decimal("5000")),
            ("29C-33333", "XeMay", "Khu B", 60, Decimal("10000")),
            ("30A-56789", "Oto", "Khu C", 55, Decimal("20000")),
            ("51H-99999", "Oto", "Khu C", 130, Decimal("40000")),
            ("29A-44444", "Oto", "Khu C", 60, Decimal("20000")),
            ("51B-77831", "Oto", "Khu D", 70, Decimal("20000")),
            ("43A-88888", "Oto", "Khu D", 110, Decimal("40000")),
            ("ZE-123", "XeDap", "Khu B", 60, Decimal("2000")),
            ("ZE-567", "XeDap", "Khu B", 50, Decimal("2000")),
        ]

        LuotGuiXe.objects.filter(trang_thai_luot="Đang gửi").delete()

        for plate, v_type_code, zone_name, mins_ago, fee in active_vehicles:
            lx = type_objs[v_type_code]
            pt, _ = PhuongTien.objects.get_or_create(bien_so_xe=plate, defaults={"loai_xe": lx})
            card_code = f"CARD-{plate}"
            card, _ = VeXe.objects.get_or_create(
                ma_dinh_danh_the=card_code,
                defaults={"loai_the": "Vé lượt", "trang_thai_the": "Đang gửi"}
            )
            card.trang_thai_the = "Đang gửi"
            card.save()

            in_time = now - timedelta(minutes=mins_ago)
            LuotGuiXe.objects.create(
                ve_xe=card,
                phuong_tien=pt,
                bien_so_xe_kiem_tra=plate,
                loai_xe=lx,
                khu_vuc=zone_objs[zone_name],
                thoi_gian_vao=in_time,
                nguoi_dung_vao=u_mai,
                tong_tien_phi=fee,
                trang_thai_luot="Đang gửi"
            )

        past_completed = [
            ("29K-12399", "XeMay", "Khu A", 200, 80, Decimal("10000")),
            ("51A-99921", "Oto", "Khu C", 150, 60, Decimal("20000")),
            ("30E-88219", "Oto", "Khu C", 300, 120, Decimal("40000")),
            ("29B-44123", "XeMay", "Khu B", 240, 45, Decimal("5000")),
            ("59V-11234", "XeMay", "Khu A", 360, 90, Decimal("10000")),
            ("51G-55555", "Oto", "Khu D", 400, 150, Decimal("60000")),
            ("ZE-999", "XeDap", "Khu B", 180, 60, Decimal("2000")),
            ("29D-77712", "Oto", "Khu C", 420, 120, Decimal("40000")),
            ("43C-66123", "XeMay", "Khu B", 500, 100, Decimal("10000")),
            ("51F-12888", "Oto", "Khu C", 480, 200, Decimal("60000")),
            ("ZE-444", "XeDap", "Khu B", 210, 45, Decimal("2000")),
            ("29A-33112", "XeMay", "Khu A", 520, 90, Decimal("10000")),
            ("30F-99881", "Oto", "Khu D", 540, 180, Decimal("28000")),
        ]
        for plate, v_type_code, zone_name, in_mins, dur_mins, fee in past_completed:
            lx = type_objs[v_type_code]
            pt, _ = PhuongTien.objects.get_or_create(bien_so_xe=plate, defaults={"loai_xe": lx})
            card_code = f"HIST-{plate}"
            card, _ = VeXe.objects.get_or_create(
                ma_dinh_danh_the=card_code,
                defaults={"loai_the": "Vé lượt", "trang_thai_the": "Sẵn sàng"}
            )
            in_time = now - timedelta(minutes=in_mins)
            out_time = in_time + timedelta(minutes=dur_mins)
            LuotGuiXe.objects.create(
                ve_xe=card,
                phuong_tien=pt,
                bien_so_xe_kiem_tra=plate,
                loai_xe=lx,
                khu_vuc=zone_objs[zone_name],
                thoi_gian_vao=in_time,
                thoi_gian_ra=out_time,
                nguoi_dung_vao=u_mai,
                nguoi_dung_ra=u_hung,
                tong_tien_phi=fee,
                trang_thai_luot="Đã ra"
            )

        # 9. Bảng VeThang
        self.stdout.write("[9/10] Khoi tao VeThang...")
        monthly_data = [
            ("Nguyễn Văn An", "0901234567", "29A-88888", "Oto", now.date() - timedelta(days=60), now.date() + timedelta(days=60), "Còn hiệu lực"),
            ("Trần Thị Mai", "0918234567", "29B-12345", "XeMay", now.date() - timedelta(days=30), now.date() + timedelta(days=75), "Còn hiệu lực"),
            ("Lê Hùng Cường", "0981234567", "29C-99999", "XeMay", now.date() - timedelta(days=45), now.date() + timedelta(days=30), "Còn hiệu lực"),
            ("Vũ Đức Thành", "0933555777", "51A-67890", "Oto", now.date() - timedelta(days=15), now.date() + timedelta(days=105), "Còn hiệu lực"),
            ("Phạm Thị Huyền", "0971234567", "29D-78012", "Oto", now.date() - timedelta(days=90), now.date() - timedelta(days=10), "Đã hết hạn"),
        ]
        for name, phone, plate, v_type_code, start_d, end_d, status_str in monthly_data:
            lx = type_objs[v_type_code]
            pt, _ = PhuongTien.objects.get_or_create(bien_so_xe=plate, defaults={"loai_xe": lx})
            card_code = f"CARD-THANG-{plate}"
            card, _ = VeXe.objects.get_or_create(
                ma_dinh_danh_the=card_code,
                defaults={"loai_the": "Vé tháng", "trang_thai_the": "Sẵn sàng"}
            )
            VeThang.objects.update_or_create(
                the_xe=card,
                phuong_tien=pt,
                defaults={
                    "ho_ten_khach_hang": name,
                    "so_dien_thoai": phone,
                    "ngay_bat_dau": start_d,
                    "ngay_ket_thuc": end_d,
                    "trang_thai_ve": status_str,
                }
            )

        # 10. Bảng BaoCaoThongKe
        self.stdout.write("[10/10] Khoi tao BaoCaoThongKe...")
        BaoCaoThongKe.objects.get_or_create(
            loai_bao_cao="Tuan",
            ngay_bat_dau=now.date() - timedelta(days=7),
            ngay_ket_thuc=now.date(),
            defaults={
                "tong_luot_xe": 2555,
                "tong_doanh_thu": Decimal("57740000.00"),
                "ty_le_lap_day_trung_binh": Decimal("35.5"),
                "khung_gio_cao_diem": "17h–19h (95 xe/gio)",
            }
        )

        self.stdout.write("=== KHOI TAO DU LIEU MAU 10 BANG CSDL THANH CONG ===")
