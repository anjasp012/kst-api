import os
import sys
from sqlalchemy import text
from geoalchemy2.elements import WKTElement

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.session import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models import (
    User,
    KSTLocation,
    KSTInstansi,
)
from app.seed.seed_separate_tables import seed_separate_tables
from app.seed.seed_wilayah import seed_wilayah_data


def seed_database():
    print("[+] Ensuring PostGIS extension exists...")
    with engine.connect() as conn:
        conn.execute(text("CREATE EXTENSION IF NOT EXISTS postgis;"))
        conn.commit()

    print("[+] Initializing Database Tables...")
    Base.metadata.create_all(bind=engine)
    print("[+] Tables created successfully!")

    # 1. Seed Master Kategori KST & Instansi terlebih dahulu
    seed_separate_tables()

    db = SessionLocal()
    try:
        # 2. Admin User
        print("[+] Seeding Admin User...")
        existing_admin = db.query(User).filter((User.username == "admin") | (User.email == "admin@brin.go.id")).first()
        if not existing_admin:
            admin = User(
                username="admin",
                email="admin@brin.go.id",
                hashed_password=get_password_hash("admin123"),
                full_name="Administrator KST BRIN",
                role="superadmin",
                is_active=1
            )
            db.add(admin)
            db.commit()
            print("[+] Admin user seeded.")
        else:
            print("[+] Admin user already exists.")
        

        # 2. Seeding KST Locations (Wonderful BRIN Interactive Map & Modal)
        print("[+] Seeding Kawasan Sains dan Teknologi (KST) Locations...")
        kst_data = [
            {
                "nama": "KST Jawa Barat",
                "slug": "kst-jawa-barat",
                "wilayah": "Jawa",
                "kota_provinsi": "Bandung, Jawa Barat",
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 2021,
                "thumbnail_url": "/uploads/kst-jawa-barat.jpg",
                "latitude": -6.917464,
                "longitude": 107.619122,
                "deskripsi_profil": "Kawasan ini menjadi pusat riset, pengembangan, dan kolaborasi yang mendukung potensi unggulan wilayah serta kebutuhan strategis Indonesia. Kawasan ini menjadi pusat riset, inovasi, penerapan teknologi, dan simpul kolaborasi wilayah.",
                "peran_kawasan": "Mendukung pengembangan riset, inovasi, dan penerapan teknologi di wilayah ini.",
                "fokus_utama": ["Pangan", "Energi", "Laut", "Teknologi Digital"],
                "terhubung_dengan": "Peneliti, industri, pemerintah, komunitas, dan mitra pendidikan.",
                "fasilitas": [
                    {"nama": "Laboratorium Bioteknologi Terpadu", "tipe": "Laboratorium", "deskripsi": "Fasilitas pengujian genomik dan rekayasa biologi modern."},
                    {"nama": "Pilot Plant Pengolahan Pangan", "tipe": "Pilot Plant", "deskripsi": "Fasilitas hilirisasi dan prototyping produk pangan olahan lokal."},
                    {"nama": "Pusat Akses Data & Komputasi Awan", "tipe": "Akses Data & Koleksi", "deskripsi": "Infrastruktur supercomputing untuk riset kecerdasan buatan dan analisis big data."},
                    {"nama": "Observatorium Sains Terapan", "tipe": "Observatorium", "deskripsi": "Stasiun pengamatan atmosfer dan kondisi lingkungan mikro wilayah."}
                ],
                "riset": [
                    {"judul": "Pengembangan Pangan Fungsional Berbasis Hayati Lokal", "bidang": "Pangan & Pertanian", "deskripsi": "Riset ketahanan pangan dan formulasi nutrisi bernilai tambah tinggi."},
                    {"judul": "Inovasi Sel Bahan Bakar & Baterai Generasi Lanjut", "bidang": "Energi & Material", "deskripsi": "Riset material maju untuk mempercepat transisi energi bersih ramah lingkungan."},
                    {"judul": "Sistem Sensor Cerdas Maritim Berbasis AI", "bidang": "Maritim", "deskripsi": "Monitoring kualitas perairan dan pelacakan armada perikanan secara presisi."}
                ],
                "dampak": [
                    {"judul": "Pemberdayaan & Standardisasi UMKM Pangan", "keterangan": "Lebih dari 40 UKM lokal mendapatkan pendampingan sertifikasi dan uji kualitas pangan."},
                    {"judul": "Implementasi PLTS Microgrid Ramah Lingkungan", "keterangan": "Penerapan sistem pembangkit surya terdistribusi di kawasan pelosok Jawa Barat."}
                ],
                "potensi_kolaborasi": ["Industri", "Akademisi", "Pemerintah", "Komunitas"],
                "daftar_kolaborasi": [
                    {"mitra": "Institut Teknologi Bandung (ITB)", "tipe": "Akademisi", "deskripsi": "Joint-research bidang mikroelektronika dan material cerdas."},
                    {"mitra": "Dinas ESDM Provinsi Jawa Barat", "tipe": "Pemerintah", "deskripsi": "Program implementasi bauran energi baru terbarukan."},
                    {"mitra": "PT Bio Farma (Persero)", "tipe": "Industri", "deskripsi": "Kemitraan pengembangan vaksin dan terapi biologis."}
                ],
                "galeri": [
                    "/uploads/kst-jabar-1.jpg",
                    "/uploads/kst-jabar-2.jpg",
                    "/uploads/kst-jabar-3.jpg"
                ]
            },
            {
                "nama": "KST Soekarno (Cibinong)",
                "slug": "kst-soekarno-cibinong",
                "wilayah": "Jawa",
                "kota_provinsi": "Bogor, Jawa Barat",
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 2020,
                "thumbnail_url": "/uploads/kst-cibinong.jpg",
                "latitude": -6.491389,
                "longitude": 106.848889,
                "deskripsi_profil": "Pusat riset hayati, genomik, dan keanekaragaman hayati terbesar di Asia Tenggara, menaungi Indonesian Eling Library dan koleksi spesimen terlengkap.",
                "peran_kawasan": "Pusat konservasi hayati, riset biosains, rekayasa genetika, dan bioindustri berkelanjutan.",
                "fokus_utama": ["Pangan & Pertanian", "Kesehatan", "Lingkungan"],
                "terhubung_dengan": "Peneliti hayati dunia, industri farmasi, universitas, dan konservasionis.",
                "fasilitas": [
                    {"nama": "Cryo-EM & Genomic Sequencing Facility", "tipe": "Laboratorium", "deskripsi": "Fasilitas pemetaan genom presisi tinggi."},
                    {"nama": "Herbarium Bogoriense & Museum Zoologicum", "tipe": "Akses Data & Koleksi", "deskripsi": "Pusat spesimen flora fauna nasional."}
                ],
                "riset": [
                    {"judul": "Pemetaan Genomik Sumber Daya Genetik Nusantara", "bidang": "Lingkungan", "deskripsi": "Eksplorasi potensi senyawa bioaktif endemik Indonesia."}
                ],
                "dampak": [
                    {"judul": "Katalogisasi Digital Flora Nusantara", "keterangan": "Database terbuka jutaan spesimen hayati untuk riset biomedis dunia."}
                ],
                "potensi_kolaborasi": ["Akademisi", "Industri", "Pemerintah"],
                "daftar_kolaborasi": [
                    {"mitra": "IPB University", "tipe": "Akademisi", "deskripsi": "Kolaborasi riset agromaritim dan bioteknologi tanaman."}
                ],
                "galeri": []
            },
            {
                "nama": "KST B.J. Habibie (Serpong)",
                "slug": "kst-bj-habibie-serpong",
                "wilayah": "Jawa",
                "kota_provinsi": "Tangerang Selatan, Banten",
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 2019,
                "thumbnail_url": "/uploads/kst-serpong.jpg",
                "latitude": -6.357500,
                "longitude": 106.666944,
                "deskripsi_profil": "Kawasan terintegrasi sains dan rekayasa teknologi tinggi, energi, nuklir terapan, dan pengujian material maju nasional.",
                "peran_kawasan": "Pusat pengujian standar industri nasional dan rekayasa manufaktur cerdas.",
                "fokus_utama": ["Energi & Material", "Teknologi Digital", "Maritim"],
                "terhubung_dengan": "BUMN Strategis, industri manufaktur, kementerian teknis, dan asosiasi energi.",
                "fasilitas": [
                    {"nama": "Reaktor Riset Serbaguna GA Siwabessy", "tipe": "Laboratorium", "deskripsi": "Riset isotop nuklir kesehatan dan industri."},
                    {"nama": "Terowongan Angin Indonesia (Indonesian Low Speed Wind Tunnel)", "tipe": "Pilot Plant", "deskripsi": "Uji aerodinamika pesawat, kendaraan, dan struktur sipil."}
                ],
                "riset": [
                    {"judul": "Material Komposit Tahan Korosi Air Laut", "bidang": "Energi & Material", "deskripsi": "Aplikasi pelapisan lambung kapal dan turbin lepas pantai."}
                ],
                "dampak": [
                    {"judul": "Kemandirian Radiofarmaka Kanker", "keterangan": "Produksi isotop medis I-131 untuk kebutuhan rumah sakit nasional."}
                ],
                "potensi_kolaborasi": ["Industri", "Pemerintah", "Akademisi"],
                "daftar_kolaborasi": [
                    {"mitra": "PT Dirgantara Indonesia", "tipe": "Industri", "deskripsi": "Uji aerodinamika drone patroli maritim."}
                ],
                "galeri": []
            },
            {
                "nama": "KST Sriwijaya (Sumatera)",
                "slug": "kst-sriwijaya-sumatera",
                "wilayah": "Sumatera",
                "kota_provinsi": "Palembang, Sumatera Selatan",
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 2022,
                "thumbnail_url": "/uploads/kst-sumatera.jpg",
                "latitude": -2.990934,
                "longitude": 104.756554,
                "deskripsi_profil": "Simpul riset agrikultur berkelanjutan, perkebunan sawit & karet, serta restorasi lahan gambut di Pulau Sumatera.",
                "peran_kawasan": "Mengawal hilirisasi komoditas perkebunan dan konservasi ekosistem lahan basah.",
                "fokus_utama": ["Pangan & Pertanian", "Lingkungan", "Energi"],
                "terhubung_dengan": "Petani perkebunan, gabungan pengusaha kelapa sawit, dan Pemda se-Sumatera.",
                "fasilitas": [
                    {"nama": "Laboratorium Uji Mutu Tanah & Gambut", "tipe": "Laboratorium", "deskripsi": "Analisis biogeokimia tanah tropis."},
                    {"nama": "Stasiun Riset Agroforestri Terpadu", "tipe": "Observatorium", "deskripsi": "Pemantauan emisi karbon lahan gambut."}
                ],
                "riset": [
                    {"judul": "Pemanfaatan Limbah Sawit Menjadi Biopellet Energi", "bidang": "Energi & Material", "deskripsi": "Hilirisasi limbah padat kelapa sawit."}
                ],
                "dampak": [
                    {"judul": "Mitigasi Kebakaran Hutan dan Lahan Gambut", "keterangan": "Sistem peringatan dini kelembaban gambut terpasang di 5 kabupaten."}
                ],
                "potensi_kolaborasi": ["Industri", "Pemerintah", "Komunitas"],
                "daftar_kolaborasi": [],
                "galeri": []
            },
            {
                "nama": "KST Hasanuddin (Sulawesi)",
                "slug": "kst-hasanuddin-sulawesi",
                "wilayah": "Sulawesi",
                "kota_provinsi": "Makassar, Sulawesi Selatan",
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 2022,
                "thumbnail_url": "/uploads/kst-sulawesi.jpg",
                "latitude": -5.147665,
                "longitude": 119.432732,
                "deskripsi_profil": "Pusat keunggulan maritim, budidaya perikanan laut dalam, dan pengolahan hasil laut kawasan timur Indonesia.",
                "peran_kawasan": "Mendukung Indonesia sebagai poros maritim dunia melalui inovasi kelautan terdepan.",
                "fokus_utama": ["Kelautan / Maritim", "Pangan", "Teknologi Digital"],
                "terhubung_dengan": "Nelayan pesisir, industri rumput laut, dan otoritas pelabuhan perikanan.",
                "fasilitas": [
                    {"nama": "Hatchery Riset Biota Laut Tropis", "tipe": "Pilot Plant", "deskripsi": "Pemuliaan indukan unggul udang dan ikan laut."},
                    {"nama": "Laboratorium Bioprospeksi Rumput Laut", "tipe": "Laboratorium", "deskripsi": "Ekstraksi hydrocolloid untuk farmasi dan pangan."}
                ],
                "riset": [
                    {"judul": "Formula Bioplastik Ramah Lingkungan dari Rumput Laut", "bidang": "Kelautan", "deskripsi": "Material kemasan biodegradable laut."}
                ],
                "dampak": [
                    {"judul": "Peningkatan Ekspor Rumput Laut Olahan", "keterangan": "Kemitraan bersama koperasi nelayan lokal di Takalar dan Pangkep."}
                ],
                "potensi_kolaborasi": ["Industri", "Komunitas", "Akademisi"],
                "daftar_kolaborasi": [],
                "galeri": []
            },
            {
                "nama": "KST Nusantara (Kalimantan)",
                "slug": "kst-nusantara-kalimantan",
                "wilayah": "Kalimantan",
                "kota_provinsi": "Balikpapan - IKN, Kalimantan Timur",
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 2023,
                "thumbnail_url": "/uploads/kst-kalimantan.jpg",
                "latitude": -0.973056,
                "longitude": 116.708889,
                "deskripsi_profil": "Kawasan sains hutan hujan tropis (Smart Forest Research City) dan transisi teknologi hijau di Kawasan Ibu Kota Nusantara.",
                "peran_kawasan": "Mengawal pembangunan kota cerdas hijau berbasis sains dan konservasi hutan tropis Kalimantan.",
                "fokus_utama": ["Lingkungan", "Teknologi Digital", "Sosial Humaniora"],
                "terhubung_dengan": "Otorita IKN, masyarakat adat Dayak, dan lembaga konservasi internasional.",
                "fasilitas": [
                    {"nama": "Canopy Crane Research Tower", "tipe": "Observatorium", "deskripsi": "Menara riset kanopi hutan primer Kalimantan."},
                    {"nama": "Pusat Pemodelan Smart Forest City", "tipe": "Akses Data & Koleksi", "deskripsi": "Simulasi digital kembar (Digital Twin) tata ruang hijau."}
                ],
                "riset": [
                    {"judul": "Restorasi Koridor Satwa Liar Menggunakan Sensor IoT", "bidang": "Lingkungan", "deskripsi": "Pemantauan habitat orangutan dan satwa endemik."}
                ],
                "dampak": [
                    {"judul": "Rehabilitasi 1.000 Hektar Hutan Bekas Tambang", "keterangan": "Uji terap teknologi biochar dan fungi mikoriza lokal."}
                ],
                "potensi_kolaborasi": ["Pemerintah", "Komunitas", "Akademisi"],
                "daftar_kolaborasi": [],
                "galeri": []
            }
        ]

        kst_inst = db.query(KSTInstansi).filter(KSTInstansi.slug == "kawasan-sains-kst").first()
        kst_inst_id = kst_inst.id if kst_inst else None

        for k in kst_data:
            existing_kst = db.query(KSTLocation).filter_by(slug=k["slug"]).first()
            if existing_kst:
                continue
            lat = k["latitude"]
            lon = k["longitude"]
            geom = WKTElement(f"POINT({lon} {lat})", srid=4326) if lat and lon else None
            kst_obj = KSTLocation(
                nama=k["nama"],
                slug=k["slug"],
                wilayah=k["wilayah"],
                kota_provinsi=k["kota_provinsi"],
                pengelola=k["pengelola"],
                status=k["status"],
                instansi_id=kst_inst_id,
                tahun_operasi=k["tahun_operasi"],
                thumbnail_url=k["thumbnail_url"],
                latitude=lat,
                longitude=lon,
                geom=geom,
                deskripsi_profil=k["deskripsi_profil"],
                peran_kawasan=k["peran_kawasan"],
                fokus_utama=k["fokus_utama"],
                terhubung_dengan=k["terhubung_dengan"],
                fasilitas=k["fasilitas"],
                riset=k["riset"],
                dampak=k["dampak"],
                potensi_kolaborasi=k["potensi_kolaborasi"],
                daftar_kolaborasi=k["daftar_kolaborasi"],
                galeri=k["galeri"],
                is_active=True
            )
            db.add(kst_obj)
        db.commit()
        print(f"[+] {len(kst_data)} KST Locations seeded successfully!")

        # 3. Seeding Regional Partners (BAPPEDA / BAPPERIDA / BRIDA) from Spreadsheet
        print("[+] Seeding Regional Partners (BRIDA, BAPPERIDA, BAPPEDA)...")
        partners_data = [
            {
                "nama_organisasi": "BAPPEDA Kab. Bireuen",
                "jenis": "BAPPEDA",
                "wilayah": "Sumatera",
                "alamat": "6P5G+28M, Jl. Bireuen-Lhokseumawe, Aceh",
                "telepon": "081234567890",
                "website": "http://bappeda.bireuenkab.go.id/",
                "email": "bappeda@bireuenkab.go.id",
                "latitude": 5.20782638168213,
                "longitude": 96.725873968614
            },
            {
                "nama_organisasi": "BAPPEDA Kab. Aceh Barat Daya",
                "jenis": "BAPPEDA",
                "wilayah": "Sumatera",
                "alamat": "Jl. Bukit Hijau Kompleks Perkantoran Abdya",
                "telepon": "065991020",
                "website": "http://www.acehbaratdayakab.go.id",
                "email": "info@acehbaratdayakab.go.id",
                "latitude": 3.76604439115981,
                "longitude": 96.848955197027
            },
            {
                "nama_organisasi": "BAPPEDA Kab. Gayo Lues",
                "jenis": "BAPPEDA",
                "wilayah": "Sumatera",
                "alamat": "X8XG+V6X, Sentang, Kec. Blangkejeren, Aceh",
                "telepon": "-",
                "website": "https://bappeda.gayolueskab.go.id",
                "email": "bappeda@gayolueskab.go.id",
                "latitude": 3.99997335544762,
                "longitude": 97.325555879218
            },
            {
                "nama_organisasi": "BAPPEDA Kab. Aceh Tamiang",
                "jenis": "BAPPEDA",
                "wilayah": "Sumatera",
                "alamat": "72XV+5H8, Gampong Bundar, Kec. Karang Baru",
                "telepon": "-",
                "website": "https://data.acehtamiangkab.go.id",
                "email": "bappeda@acehtamiangkab.go.id",
                "latitude": 4.29809727297234,
                "longitude": 98.043992809905
            },
            {
                "nama_organisasi": "BAPPEDA Kab. Nagan Raya",
                "jenis": "BAPPEDA",
                "wilayah": "Sumatera",
                "alamat": "589F+P64, Lueng Baro, Kec. Suka Makmue",
                "telepon": "-",
                "website": "http://bappeda.naganrayakab.go.id",
                "email": "bappeda@naganrayakab.go.id",
                "latitude": 4.16950610597439,
                "longitude": 96.323124809905
            },
            {
                "nama_organisasi": "BAPPEDA Kab. Aceh Jaya",
                "jenis": "BAPPEDA",
                "wilayah": "Sumatera",
                "alamat": "JJF8+M88, Keutapang, Kec. Krueng Sabee",
                "telepon": "-",
                "website": "http://bappeda.acehjayakab.go.id",
                "email": "bappeda@acehjayakab.go.id",
                "latitude": 4.62424205274949,
                "longitude": 95.615833194563
            },
            {
                "nama_organisasi": "BAPPEDA Kab. Mandailing Natal",
                "jenis": "BAPPEDA",
                "wilayah": "Sumatera",
                "alamat": "QHWH+FQH, Parbangunan, Kec. Panyabungan",
                "telepon": "(0636) 326261",
                "website": "https://bappeda.madina.go.id",
                "email": "bappeda@madina.go.id",
                "latitude": 0.79647402820846,
                "longitude": 99.579457163342
            },
            {
                "nama_organisasi": "BAPPERIDA Kab. Asahan",
                "jenis": "BAPPERIDA",
                "wilayah": "Sumatera",
                "alamat": "Jl. Jenderal Sudirman No.05, Kisaran",
                "telepon": "0123456789",
                "website": "https://bapperida.asahankab.go.id",
                "email": "bapperida@asahankab.go.id",
                "latitude": 2.98831655319776,
                "longitude": 99.613629836888
            },
            {
                "nama_organisasi": "BAPPERIDA Kab. Simalungun",
                "jenis": "BAPPERIDA",
                "wilayah": "Sumatera",
                "alamat": "XV66+RPX, Unnamed Road, Bahapal Raya",
                "telepon": "-",
                "website": "https://bapperida.simalungunkab.go.id",
                "email": "bapperida@simalungunkab.go.id",
                "latitude": 2.96309478089266,
                "longitude": 98.862022064540
            },
            {
                "nama_organisasi": "BAPPERIDA Kab. Nias Selatan",
                "jenis": "BAPPERIDA",
                "wilayah": "Sumatera",
                "alamat": "JL. SAONIGEHO, Bawonahono, Kec. Teluk Dalam",
                "telepon": "-",
                "website": "https://bappeda.niasselatankab.go.id",
                "email": "bappedakabnisel@gmail.com",
                "latitude": 0.58436811096137,
                "longitude": 97.777161597604
            },
            {
                "nama_organisasi": "BAPPERIDA Kab. Samosir",
                "jenis": "BAPPERIDA",
                "wilayah": "Sumatera",
                "alamat": "HP6C+7J2, Jl. Simbolon Purba No.Km 5, Pangururan",
                "telepon": "-",
                "website": "https://samosirkab.go.id",
                "email": "bappedalitbangsamosir@gmail.com",
                "latitude": 2.56074793937968,
                "longitude": 98.721514037482
            },
            {
                "nama_organisasi": "BAPPERIDA Kab. Serdang Bedagai",
                "jenis": "BAPPERIDA",
                "wilayah": "Sumatera",
                "alamat": "F4RG+6P3, Jl. Negara, Firdaus, Kec. Sei Rampah",
                "telepon": "-",
                "website": "http://bappeda.serdangbedagaikab.go.id",
                "email": "bapperida@serdangbedagaikab.go.id",
                "latitude": 3.49067867950979,
                "longitude": 99.126796200000
            },
            {
                "nama_organisasi": "BAPPERIDA Kab. Padang Lawas",
                "jenis": "BAPPERIDA",
                "wilayah": "Sumatera",
                "alamat": "3Q4G+66P, Bulu Sonik, Kec. Barumun, Sibuhuan",
                "telepon": "-",
                "website": "https://padanglawaskab.go.id",
                "email": "bapperida@padanglawaskab.go.id",
                "latitude": 1.08031464367941,
                "longitude": 99.770760671575
            },
            {
                "nama_organisasi": "BAPPERIDA Kab. Nias Utara",
                "jenis": "BAPPERIDA",
                "wilayah": "Sumatera",
                "alamat": "Jl. Ki Hadjar Dewantara No. 2, Lotu",
                "telepon": "-",
                "website": "https://niasutarakab.go.id",
                "email": "bapperida@niasutarakab.go.id",
                "latitude": 1.41810072081972,
                "longitude": 97.431146194557
            },
            {
                "nama_organisasi": "BAPPERIDA Kota Tanjung Balai",
                "jenis": "BAPPERIDA",
                "wilayah": "Sumatera",
                "alamat": "WQX8+FH8, Sijambi, Kec. Datuk Bandar",
                "telepon": "-",
                "website": "https://bapperida.tanjungbalaikota.go.id",
                "email": "bappeda@tanjungbalaikota.go.id",
                "latitude": 2.94888272186395,
                "longitude": 99.766500493253
            },
            {
                "nama_organisasi": "BRIDA Kota Medan",
                "jenis": "BRIDA",
                "wilayah": "Sumatera",
                "alamat": "Jl. Jenderal Besar A.H. Nasution No.32, Pangkalan Masyhur",
                "telepon": "(061) 7873439",
                "website": "http://brida.pemkomedan.go.id/",
                "email": "brida@medan.go.id",
                "latitude": 3.54347304153207,
                "longitude": 98.673735962568
            },
            {
                "nama_organisasi": "BAPPERIDA Kota Binjai",
                "jenis": "BAPPERIDA",
                "wilayah": "Sumatera",
                "alamat": "Jl. Jenderal Gatot Subroto No.98, Limau Mungkur",
                "telepon": "(061) 8824618",
                "website": "https://binjaikota.go.id",
                "email": "bapperida@binjaikota.go.id",
                "latitude": 3.60740778118023,
                "longitude": 98.472922100000
            },
            {
                "nama_organisasi": "BAPPERIDA Kota Gunungsitoli",
                "jenis": "BAPPERIDA",
                "wilayah": "Sumatera",
                "alamat": "Jln. Pancasila No. 10 Desa Mudik Kecamatan Gunungsitoli",
                "telepon": "(0639) 22574",
                "website": "https://gunungsitolikota.go.id",
                "email": "bappedagusit@gmail.com",
                "latitude": 1.28376293365132,
                "longitude": 97.612933132880
            },
            {
                "nama_organisasi": "BAPPERIDA Kab. Kepulauan Mentawai",
                "jenis": "BAPPERIDA",
                "wilayah": "Sumatera",
                "alamat": "WHWG+G4F, Sipora Jaya, Sipora Utara, Tuapejat",
                "telepon": "+62 759 320 050",
                "website": "https://bapperida.mentawaikab.go.id",
                "email": "bappeda@mentawaikab.go.id",
                "latitude": -2.05263094908226,
                "longitude": 99.575477460534
            },
            {
                "nama_organisasi": "BAPPERIDA Kab. Pesisir Selatan",
                "jenis": "BAPPERIDA",
                "wilayah": "Sumatera",
                "alamat": "Jl. Jenderal Sudirman No. 532, Desa Sago Salido, Painan",
                "telepon": "(0756) 7464085",
                "website": "https://bapperida.pesisirselatankab.go.id",
                "email": "bappedalitbang@pesisirselatankab.go.id",
                "latitude": -1.30638308438617,
                "longitude": 100.544359505337
            }
        ]

        for p in partners_data:
            lat = p["latitude"]
            lon = p["longitude"]
            geom = WKTElement(f"POINT({lon} {lat})", srid=4326) if lat and lon else None
            
            slug = p["nama_organisasi"].lower().replace(' ', '-') + '-' + str(lat)[:4].replace('.','')
            
            existing_part = db.query(KSTLocation).filter_by(slug=slug).first()
            if existing_part:
                continue

            inst_match = db.query(KSTInstansi).filter(KSTInstansi.nama.ilike(p["jenis"])).first()
            part_obj = KSTLocation(
                nama=p["nama_organisasi"],
                slug=slug,
                kota_provinsi=p["wilayah"],
                pengelola="Mitra Daerah",
                instansi_id=inst_match.id if inst_match else None,
                alamat=p["alamat"],
                telepon=p["telepon"],
                website=p["website"],
                email=p["email"],
                latitude=lat,
                longitude=lon,
                geom=geom,
                is_active=True
            )
            db.add(part_obj)
        db.commit()
        print(f"[+] {len(partners_data)} Regional Partners seeded successfully as KSTLocations!")

        # 4. Seeding Wilayah Indonesia (38 Provinsi & 514 Kota/Kabupaten)
        try:
            seed_wilayah_data()
        except Exception as e:
            print(f"[!] Info seeding wilayah online: {e}")

        print("\n[+] ALL KST & POSTGIS SEEDING COMPLETED SUCCESSFULLY!")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
