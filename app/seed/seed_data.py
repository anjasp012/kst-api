import os
import sys
import uuid
from sqlalchemy import text
from geoalchemy2.elements import WKTElement

# Ensure backend root is in sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from app.db.session import engine, Base, SessionLocal
from app.core.security import get_password_hash
from app.models.user import User
from app.models.lokasi import KSTLokasi
from app.models.jenis_kawasan import KSTJenisKawasan
from app.models.galeri import KSTGaleri
from app.models.field_location import LabelDataLokasi, NilaiDataLokasi
from app.models.tema_riset import KSTFokusRiset
from app.models.wilayah import WilayahProvinsi, WilayahKabupatenKota


def seed_database():
    print("[1/5] Ensuring database schema and migrations are up to date...")
    from app.db.auto_migrate import run_auto_migration
    run_auto_migration(engine)

    print("[2/5] Ensuring SQLAlchemy models are created...")
    Base.metadata.create_all(bind=engine)

    db = SessionLocal()
    try:
        # 1. Admin User
        print("[4/6] Checking / Seeding Admin User...")
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
            print("  -> Admin user created (admin / admin123).")
        else:
            print("  -> Admin user already exists.")

        # 2. Seed Jenis Kawasan Hierarchy
        print("[5/6] Seeding KST Jenis Kawasan Hierarchy...")
        
        # Utama 1: Kawasan
        kawasan_parent = db.query(KSTJenisKawasan).filter_by(slug="kawasan").first()
        if not kawasan_parent:
            kawasan_parent = KSTJenisKawasan(
                nama="Kawasan",
                slug="kawasan",
                deskripsi="Pilar Induk Kawasan Riset & Inovasi",
                parent_id=None,
                is_active=True
            )
            db.add(kawasan_parent)
            db.commit()
            db.refresh(kawasan_parent)

        # Utama 2: BRIDA
        brida_parent = db.query(KSTJenisKawasan).filter_by(slug="brida").first()
        if not brida_parent:
            brida_parent = KSTJenisKawasan(
                nama="BRIDA",
                slug="brida",
                deskripsi="Riset & Inovasi Daerah",
                parent_id=None,
                is_active=True
            )
            db.add(brida_parent)
            db.commit()
            db.refresh(brida_parent)
        else:
            brida_parent.parent_id = None
            brida_parent.deskripsi = "Riset & Inovasi Daerah"
            db.commit()

        # Utama 3: Kebun Raya
        kr_parent = db.query(KSTJenisKawasan).filter_by(slug="kebun-raya").first()
        if not kr_parent:
            kr_parent = KSTJenisKawasan(
                nama="Kebun Raya",
                slug="kebun-raya",
                deskripsi="Botani & Konservasi Ex-situ",
                parent_id=None,
                is_active=True
            )
            db.add(kr_parent)
            db.commit()
            db.refresh(kr_parent)
        else:
            kr_parent.parent_id = None
            kr_parent.deskripsi = "Botani & Konservasi Ex-situ"
            db.commit()

        # Children of Kawasan
        sub_kawasan_items = [
            {"nama": "Kawasan Sains dan Teknologi", "slug": "kawasan-sains-dan-teknologi", "deskripsi": "KST terpadu hilirisasi riset & kemitraan industri"},
            {"nama": "Kawasan Sains (KS)", "slug": "kawasan-sains-ks", "deskripsi": "Pusat riset sains dasar dan aplikasi laboratorium"},
            {"nama": "Kawasan Sains, Teknologi, dan Edukasi", "slug": "kawasan-sains-teknologi-edukasi", "deskripsi": "Pusat riset dan edukasi publik"},
            {"nama": "Kawasan Konservasi Ilmiah", "slug": "kawasan-konservasi-ilmiah", "deskripsi": "Konservasi ilmiah dan riset lingkungan"},
            {"nama": "Kawasan Stasiun Lapangan", "slug": "kawasan-stasiun-lapangan", "deskripsi": "Stasiun observasi dan penelitian lapangan"},
            {"nama": "Kawasan Kerja Bersama", "slug": "kawasan-kerja-bersama", "deskripsi": "Co-working space dan kolaborasi peneliti"},
            {"nama": "Kawasan Administrasi", "slug": "kawasan-administrasi", "deskripsi": "Layanan administrasi dan pendukung kawasan"}
        ]

        sub_kawasan_map = {}
        for sub in sub_kawasan_items:
            existing_sub = db.query(KSTJenisKawasan).filter_by(slug=sub["slug"]).first()
            if not existing_sub:
                existing_sub = KSTJenisKawasan(
                    nama=sub["nama"],
                    slug=sub["slug"],
                    deskripsi=sub["deskripsi"],
                    parent_id=kawasan_parent.id,
                    is_active=True
                )
                db.add(existing_sub)
                db.commit()
                db.refresh(existing_sub)
            else:
                existing_sub.parent_id = kawasan_parent.id
                existing_sub.deskripsi = sub["deskripsi"]
                db.commit()
            sub_kawasan_map[sub["nama"]] = existing_sub

        # 3. Seed Master Labels
        print("[+] Ensuring Master Labels in label_data_lokasi...")
        preset_labels = [
            {"nama": "Fokus Riset", "slug": "fokus-riset", "placeholder": "Contoh: Energi Terbarukan, Bioteknologi", "icon": "FlaskConical"},
            {"nama": "Fasilitas & Laboratorium", "slug": "fasilitas", "placeholder": "Laboratorium Uji, Pilot Plant, Cleanroom", "icon": "Building2"},
            {"nama": "Pemanfaatan & Layanan", "slug": "pemanfaatan-layanan", "placeholder": "Uji Kompatibilitas, Pengujian Material", "icon": "Handshake"},
            {"nama": "Saluran Komunikasi & Akses Digital", "slug": "saluran-digital", "placeholder": "Website, email, telepon, media sosial, atau kanal resmi...", "icon": "Globe"},
            {"nama": "Koleksi Unggulan", "slug": "koleksi-unggulan", "placeholder": "Contoh: Tumbuhan Kayu Kalimantan, Anggrek", "icon": "TreePine"},
            {"nama": "Yang Bisa Ditemui & Dilakukan", "slug": "yang-bisa-ditemui", "placeholder": "Edukasi botani, observasi antariksa", "icon": "Sparkles"},
            {"nama": "Tata Kelola & Legalitas", "slug": "tata-kelola", "placeholder": "SK Bupati No. 12/2022", "icon": "ShieldCheck"},
            {"nama": "Pendamping / PIC", "slug": "pendamping-pic", "placeholder": "Nama Pendamping / Satker BRIN", "icon": "Users"},
            {"nama": "Program Inovasi Daerah", "slug": "program-inovasi", "placeholder": "Fasilitasi HKI, Inkubasi Startup", "icon": "Award"},
            {"nama": "Organisasi Riset Terkait (OR)", "slug": "or-terkait", "placeholder": "OR Hayati & Lingkungan, OR Nanoteknologi", "icon": "Building2"},
            {"nama": "Pusat Riset Terkait (PR)", "slug": "pr-terkait", "placeholder": "Pusat Riset Mikrobiologi Terapan", "icon": "Atom"},
            {"nama": "Sumber & Catatan Tambahan", "slug": "catatan", "placeholder": "Catatan internal atau tautan sumber data", "icon": "FileText"}
        ]

        label_map = {}
        for pl in preset_labels:
            ex_lbl = db.query(LabelDataLokasi).filter((LabelDataLokasi.nama == pl["nama"]) | (LabelDataLokasi.slug == pl["slug"])).first()
            if not ex_lbl:
                ex_lbl = LabelDataLokasi(
                    nama=pl["nama"],
                    slug=pl["slug"],
                    placeholder=pl["placeholder"],
                    icon=pl["icon"]
                )
                db.add(ex_lbl)
                db.commit()
                db.refresh(ex_lbl)
            label_map[pl["nama"]] = ex_lbl

        # 3b. Seed Master Fokus Riset (kst_fokus_riset)
        print("[+] Ensuring Master Data in kst_fokus_riset...")
        fokus_riset_master = [
            {"nama": "Energi & Material", "slug": "energi-material"},
            {"nama": "Kesehatan & Obat", "slug": "kesehatan-obat"},
            {"nama": "Pangan & Pertanian", "slug": "pangan-pertanian"},
            {"nama": "Teknologi Digital & Robotika", "slug": "teknologi-digital"},
            {"nama": "Kemaritiman & Kelautan", "slug": "maritim"},
            {"nama": "Lingkungan & Kebencanaan", "slug": "lingkungan-kebencanaan"}
        ]
        fokus_map = {}
        for fr in fokus_riset_master:
            fr_obj = db.query(KSTFokusRiset).filter_by(slug=fr["slug"]).first()
            if not fr_obj:
                fr_obj = KSTFokusRiset(
                    nama=fr["nama"],
                    slug=fr["slug"],
                    is_active=True
                )
                db.add(fr_obj)
                db.commit()
                db.refresh(fr_obj)
            fokus_map[fr["nama"]] = fr_obj
            fokus_map[fr["slug"]] = fr_obj

        # 4. Seed Rich Sample Locations with Foreign Keys to kst_provinsi & kst_kabupaten_kota
        print("[6/6] Seeding Initial Locations across Indonesia (3 Pillars with Wilayah Relations)...")
        locations_data = [
            # --- PILAR 1: KAWASAN SAINS & TEKNOLOGI (KST) ---
            {
                "nama": "KST B.J. Habibie (Serpong)",
                "slug": "kst-bj-habibie-serpong",
                "jenis_id": sub_kawasan_map.get("Kawasan Sains dan Teknologi").id,
                "provinsi_kode": "36",       # Banten
                "kabupaten_kota_kode": "36.74", # Kota Tangerang Selatan
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 2019,
                "luas_ha": 600.0,
                "alamat": "Kawasan Puspiptek Serpong, Muncul, Kec. Setu, Kota Tangerang Selatan, Banten 15314",
                "latitude": -6.357500,
                "longitude": 106.666944,
                "deskripsi": "Kawasan terintegrasi sains dan rekayasa teknologi tinggi, energi nuklir terapan, pengujian material maju, aerodinamika, serta pengujian standar industri nasional.",
                "extra": {
                    "Nomor Telepon": "(021) 7560562",
                    "Website Resmi": "https://brin.go.id",
                    "Email Resmi": "humas_serpong@brin.go.id",
                    "Fokus Riset": "Energi Baru Terbarukan, Radiofarmaka, Material Komposit, Kecerdasan Buatan & Robotika Industri",
                    "Fasilitas & Laboratorium": "Reaktor Riset Serbaguna GA Siwabessy, Terowongan Angin Indonesia (Indonesian Low Speed Wind Tunnel), Laboratorium Uji Material Maju",
                    "Pemanfaatan & Layanan": "Uji Aerodinamika Kendaraan, Produksi Radioisotop Medis I-131, Kalibrasi Instrumentasi Radiasi"
                },
                "galeri": [
                    "/uploads/kst-serpong.jpg",
                    "/uploads/reaktor-siwabessy.jpg"
                ]
            },
            {
                "nama": "KST Soekarno (Cibinong)",
                "slug": "kst-soekarno-cibinong",
                "jenis_id": sub_kawasan_map.get("Kawasan Sains dan Teknologi").id,
                "provinsi_kode": "32",       # Jawa Barat
                "kabupaten_kota_kode": "32.01", # Kabupaten Bogor
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 2021,
                "luas_ha": 180.0,
                "alamat": "Jl. Raya Jakarta-Bogor KM. 46, Cibinong, Kec. Cibinong, Kabupaten Bogor, Jawa Barat 16911",
                "latitude": -6.494722,
                "longitude": 106.852778,
                "deskripsi": "Pusat riset genomik hayati terpadu Indonesia, repositori keanekaragaman hayati nasional (InaCC, Herbarium Bogoriense, Museum Zoologicum), serta inovasi bioteknologi kesehatan dan pangan.",
                "extra": {
                    "Nomor Telepon": "(021) 8754587",
                    "Website Resmi": "https://brin.go.id",
                    "Email Resmi": "cibinong@brin.go.id",
                    "Fokus Riset": "Genomik Tropis Hayati, Mikrobiologi Terapan, Biofarmaka, Konservasi Plasma Nutfah",
                    "Fasilitas & Laboratorium": "Gedung Genomik Hayati, Indonesian Culture Collection (InaCC), Laboratorium Cryopreservation",
                    "Pemanfaatan & Layanan": "Sequencing Next-Generation (NGS), Penyimpanan Isolat Mikroba, Identifikasi Spesies DNA Barcoding"
                },
                "galeri": [
                    "/uploads/kst-cibinong.jpg"
                ]
            },
            {
                "nama": "KST Samaun Samadikun (Bandung)",
                "slug": "kst-samaun-samadikun-bandung",
                "jenis_id": sub_kawasan_map.get("Kawasan Sains dan Teknologi").id,
                "provinsi_kode": "32",       # Jawa Barat
                "kabupaten_kota_kode": "32.73", # Kota Bandung
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 2020,
                "luas_ha": 25.0,
                "alamat": "Jl. Sangkuriang, Dago, Kec. Coblong, Kota Bandung, Jawa Barat 40135",
                "latitude": -6.890278,
                "longitude": 107.618611,
                "deskripsi": "Pusat keunggulan riset mikroelektronika, fotonika, telekomunikasi, sensor radar, serta teknologi informasi cerdas dan komputasi sains.",
                "extra": {
                    "Nomor Telepon": "(022) 2504660",
                    "Website Resmi": "https://brin.go.id",
                    "Email Resmi": "bandung@brin.go.id",
                    "Fokus Riset": "Desain IC Semikonduktor, Fotonika Terapan, Sensor Navigasi Maritim, IoT Cerdas",
                    "Fasilitas & Laboratorium": "Cleanroom Mikroelektronika Kelas 1000, Lab Pengujian Kompatibilitas Elektromagnetik (EMC)"
                },
                "galeri": [
                    "/uploads/kst-bandung.jpg"
                ]
            },
            {
                "nama": "KST Sriwijaya (Palembang)",
                "slug": "kst-sriwijaya-palembang",
                "jenis_id": sub_kawasan_map.get("Kawasan Sains dan Teknologi").id,
                "provinsi_kode": "16",       # Sumatera Selatan
                "kabupaten_kota_kode": "16.71", # Kota Palembang
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 2022,
                "luas_ha": 45.0,
                "alamat": "Kawasan Riset Terpadu Jakabaring, Kota Palembang, Sumatera Selatan",
                "latitude": -2.990934,
                "longitude": 104.756554,
                "deskripsi": "Simpul riset agrikultur tropis berkelanjutan, perkebunan sawit & karet, serta inovasi restorasi lahan gambut di Pulau Sumatera.",
                "extra": {
                    "Nomor Telepon": "(0711) 562145",
                    "Website Resmi": "https://brin.go.id",
                    "Email Resmi": "palembang@brin.go.id",
                    "Fokus Riset": "Hilirisasi Kelapa Sawit, Restorasi Gambut Berkelanjutan, Formulasi Pupuk Organik Hayati",
                    "Fasilitas & Laboratorium": "Laboratorium Uji Kimia Tanah & Gambut, Stasiun Riset Agroforestri"
                },
                "galeri": [
                    "/uploads/kst-palembang.jpg"
                ]
            },
            {
                "nama": "KST G.A. Siwabessy (Pasar Jumat)",
                "slug": "kst-ga-siwabessy-pasar-jumat",
                "jenis_id": sub_kawasan_map.get("Kawasan Sains (KS)").id,
                "provinsi_kode": "31",       # DKI Jakarta
                "kabupaten_kota_kode": "31.74", # Kota Administrasi Jakarta Selatan
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 2018,
                "luas_ha": 15.0,
                "alamat": "Jl. Lebak Bulus Raya No. 49, Pasar Jumat, Kota Jakarta Selatan 12440",
                "latitude": -6.299167,
                "longitude": 106.776667,
                "deskripsi": "Pusat riset aplikasi teknologi isotop dan radiasi untuk mutasi pemuliaan tanaman pangan, hidrologi air tanah, dan pengujian tak rusak (NDT) infrastruktur.",
                "extra": {
                    "Nomor Telepon": "(021) 7690709",
                    "Website Resmi": "https://brin.go.id",
                    "Email Resmi": "pasar_jumat@brin.go.id",
                    "Fokus Riset": "Pemuliaan Mutasi Radiasi Padi & Kedelai, Radioisotop Hidrologi, Iradiasi Pengawetan Pangan",
                    "Fasilitas & Laboratorium": "Iradiator Gamma Sel Berdaya Tinggi, Lab Analisis Hidrologi Isotop Alam"
                },
                "galeri": [
                    "/uploads/kst-pasarjumat.jpg"
                ]
            },

            # --- PILAR 2: KEBUN RAYA ---
            {
                "nama": "Kebun Raya Bogor",
                "slug": "kebun-raya-bogor",
                "jenis_id": kr_parent.id,
                "provinsi_kode": "32",       # Jawa Barat
                "kabupaten_kota_kode": "32.71", # Kota Bogor
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 1817,
                "luas_ha": 87.0,
                "alamat": "Jl. Ir. H. Juanda No. 13, Paledang, Kec. Bogor Tengah, Kota Bogor, Jawa Barat 16122",
                "latitude": -6.597700,
                "longitude": 106.799700,
                "deskripsi": "Pusat konservasi ex-situ tumbuhan tropika dataran rendah basah tertua di Asia Tenggara. Menyimpan lebih dari 15.000 spesimen pohon langka, koleksi anggrek liar, dan pohon bersejarah.",
                "extra": {
                    "Nomor Telepon": "(0251) 8311362",
                    "Website Resmi": "https://kebunraya.id/bogor",
                    "Email Resmi": "krbogor@brin.go.id",
                    "Koleksi Unggulan": "Bunga Bangkai (Amorphophallus titanum), Teratai Raksasa (Victoria amazonica), Rafflesia patma, Palem Raja Kuno",
                    "Yang Bisa Ditemui & Dilakukan": "Edukasi botani anak, wisata sejarah konservasi, observasi burung kota, riset perbanyakan benih langka"
                },
                "galeri": [
                    "/uploads/kr-bogor.jpg"
                ]
            },
            {
                "nama": "Kebun Raya Cibodas",
                "slug": "kebun-raya-cibodas",
                "jenis_id": kr_parent.id,
                "provinsi_kode": "32",       # Jawa Barat
                "kabupaten_kota_kode": "32.03", # Kabupaten Cianjur
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 1852,
                "luas_ha": 84.9,
                "alamat": "Jl. Kebun Raya Cibodas, Sindangjaya, Kec. Cipanas, Kabupaten Cianjur, Jawa Barat 43253",
                "latitude": -6.741100,
                "longitude": 107.006900,
                "deskripsi": "Pusat konservasi tumbuhan dataran tinggi basah subtropis di lereng Gunung Gede Pangrango. Terkenal dengan koleksi taman sakura, lumut, dan tanaman obat dataran tinggi.",
                "extra": {
                    "Nomor Telepon": "(0263) 512233",
                    "Website Resmi": "https://kebunraya.id/cibodas",
                    "Email Resmi": "krcibodas@brin.go.id",
                    "Koleksi Unggulan": "Taman Sakura (Prunus cerasoides), Koleksi Paku Pohon Raksasa (Cyathea), Koleksi Lumut Dunia (Bryophyta)",
                    "Yang Bisa Ditemui & Dilakukan": "Eksplorasi ekosistem hutan lumut, piknik keluarga, fotografi sakura tropis, riset taksonomi tumbuhan pegunungan"
                },
                "galeri": [
                    "/uploads/kr-cibodas.jpg"
                ]
            },
            {
                "nama": "Kebun Raya Purwodadi",
                "slug": "kebun-raya-purwodadi",
                "jenis_id": kr_parent.id,
                "provinsi_kode": "35",       # Jawa Timur
                "kabupaten_kota_kode": "35.14", # Kabupaten Pasuruan
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 1941,
                "luas_ha": 85.0,
                "alamat": "Jl. Raya Surabaya-Malang KM. 65, Purwodadi, Kabupaten Pasuruan, Jawa Timur 67163",
                "latitude": -7.798100,
                "longitude": 112.738100,
                "deskripsi": "Pusat konservasi ex-situ tumbuhan dataran rendah kering tropis di Jawa Timur. Memiliki koleksi unggulan legum, mangga liar, bambu, dan palem tropis kering.",
                "extra": {
                    "Nomor Telepon": "(0341) 426046",
                    "Website Resmi": "https://kebunraya.id/purwodadi",
                    "Email Resmi": "krpurwodadi@brin.go.id",
                    "Koleksi Unggulan": "Koleksi Polong-polongan (Fabaceae), Tanaman Obat Tropis Kering, Palem Kering, Koleksi Bambu Nusantara",
                    "Yang Bisa Ditemui & Dilakukan": "Tur sepeda keliling kebun, workshop edukasi perbanyakan bibit, wisata konservasi tanaman pangan lokal"
                },
                "galeri": [
                    "/uploads/kr-purwodadi.jpg"
                ]
            },
            {
                "nama": "Kebun Raya Bali (Eka Karya Bedugul)",
                "slug": "kebun-raya-bali-eka-karya",
                "jenis_id": kr_parent.id,
                "provinsi_kode": "51",       # Bali
                "kabupaten_kota_kode": "51.02", # Kabupaten Tabanan
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 1959,
                "luas_ha": 157.5,
                "alamat": "Candikuning, Kec. Baturiti, Kabupaten Tabanan, Bali 82191",
                "latitude": -8.283100,
                "longitude": 115.155800,
                "deskripsi": "Kebun raya pegunungan tropis terluas di Indonesia, mengoleksi tanaman upacara adat Bali, anggrek liar pegunungan, koleksi begonia, kaktus, dan tanaman bambu eksotis.",
                "extra": {
                    "Nomor Telepon": "(0368) 2033211",
                    "Website Resmi": "https://kebunraya.id/bali",
                    "Email Resmi": "krbali@brin.go.id",
                    "Koleksi Unggulan": "Rumah Kaca Kaktus, Konservatorium Begonia Terbesar di Asia Tenggara, Koleksi Tanaman Usadha (Pengobatan Tradisional Bali)",
                    "Yang Bisa Ditemui & Dilakukan": "Outbound edukasi alam, riset etnobotani Bali, rekreasi Danau Beratan, fotografi lanskap pegunungan"
                },
                "galeri": [
                    "/uploads/kr-bali.jpg"
                ]
            },
            {
                "nama": "Kebun Raya Balikpapan",
                "slug": "kebun-raya-balikpapan",
                "jenis_id": kr_parent.id,
                "provinsi_kode": "64",       # Kalimantan Timur
                "kabupaten_kota_kode": "64.71", # Kota Balikpapan
                "pengelola": "BRIN",
                "status": "Aktif",
                "tahun_operasi": 2014,
                "luas_ha": 309.2,
                "alamat": "Jl. Soekarno Hatta KM. 15, Karang Joang, Kec. Balikpapan Utara, Kota Balikpapan, Kalimantan Timur 76127",
                "latitude": -1.134200,
                "longitude": 116.861700,
                "deskripsi": "Pusat konservasi flora kayu tropis Kalimantan (Dipterocarpaceae) dan penyangga ekosistem Hutan Lindung Sungai Wain.",
                "extra": {
                    "Nomor Telepon": "(0542) 721200",
                    "Website Resmi": "https://kebunraya.balikpapan.go.id",
                    "Email Resmi": "krbalikpapan@brin.go.id",
                    "Koleksi Unggulan": "Pohon Ulin (Eusideroxylon zwageri), Meranti Tropis, Anggrek Hutan Kalimantan, Tumbuhan Pemakan Serangga (Kantong Semar)",
                    "Yang Bisa Ditemui & Dilakukan": "Jelajah canopy bridge, trekking hutan tropis Kalimantan, edukasi konservasi pohon kayu langka"
                },
                "galeri": [
                    "/uploads/kr-balikpapan.jpg"
                ]
            },

            # --- PILAR 3: BRIDA / MITRA DAERAH ---
            {
                "nama": "BRIDA Kota Medan",
                "slug": "brida-kota-medan",
                "jenis_id": brida_parent.id,
                "provinsi_kode": "12",       # Sumatera Utara
                "kabupaten_kota_kode": "12.71", # Kota Medan
                "pengelola": "Pemerintah Daerah",
                "status": "Aktif",
                "tahun_operasi": 2022,
                "luas_ha": 1.2,
                "alamat": "Jl. Jenderal Besar A.H. Nasution No. 32, Pangkalan Masyhur, Kota Medan 20143",
                "latitude": 3.543473,
                "longitude": 98.673736,
                "deskripsi": "Badan Riset dan Inovasi Daerah Kota Medan penggerak ekosistem riset terapan, tata kelola smart city, dan inkubasi UMKM perkotaan.",
                "extra": {
                    "Nomor Telepon": "(061) 7873439",
                    "Website Resmi": "http://brida.pemkomedan.go.id",
                    "Email Resmi": "brida@medan.go.id",
                    "Program Inovasi Daerah": "Digitalisasi Perizinan Terpadu, Fasilitasi HKI Produk Lokal, Pendampingan Riset Smart Green City",
                    "Pendamping / PIC": "Dr. Ir. Ahmad Lubis (Direktorat Kemitraan Riset BRIN)"
                },
                "galeri": [
                    "/uploads/brida-medan.jpg"
                ]
            },
            {
                "nama": "BRIDA Provinsi Jawa Timur",
                "slug": "brida-provinsi-jawa-timur",
                "jenis_id": brida_parent.id,
                "provinsi_kode": "35",       # Jawa Timur
                "kabupaten_kota_kode": "35.78", # Kota Surabaya
                "pengelola": "Pemerintah Daerah",
                "status": "Aktif",
                "tahun_operasi": 2023,
                "luas_ha": 2.5,
                "alamat": "Jl. Gayung Kebonsari No. 56, Gayungan, Kota Surabaya, Jawa Timur 60235",
                "latitude": -7.257500,
                "longitude": 112.752100,
                "deskripsi": "Perumus kebijakan riset dan fasilitasi hilirisasi inovasi agroindustri dan maritim tingkat provinsi Jawa Timur.",
                "extra": {
                    "Nomor Telepon": "(031) 8290123",
                    "Website Resmi": "https://brida.jatimprov.go.id",
                    "Email Resmi": "sekretariat@brida.jatimprov.go.id",
                    "Program Inovasi Daerah": "Jatim Inovatif Award, Klinik HKI Petani & Nelayan, Akselerasi Startup Sains Terapan",
                    "Pendamping / PIC": "Tim Fasilitasi BRIDA Wilayah Jawa BRIN"
                },
                "galeri": [
                    "/uploads/brida-jatim.jpg"
                ]
            },
            {
                "nama": "BRIDA Provinsi Bali",
                "slug": "brida-provinsi-bali",
                "jenis_id": brida_parent.id,
                "provinsi_kode": "51",       # Bali
                "kabupaten_kota_kode": "51.71", # Kota Denpasar
                "pengelola": "Pemerintah Daerah",
                "status": "Aktif",
                "tahun_operasi": 2022,
                "luas_ha": 1.8,
                "alamat": "Jl. D.I. Panjaitan No. 7, Renon, Kota Denpasar, Bali 80234",
                "latitude": -8.670500,
                "longitude": 115.212600,
                "deskripsi": "Badan Riset dan Inovasi Daerah Provinsi Bali fokus pada pelestarian kearifan lokal, pariwisata berkelanjutan, ekonomi hijau, dan pertanian organik Bali.",
                "extra": {
                    "Nomor Telepon": "(0361) 226210",
                    "Website Resmi": "https://brida.baliprov.go.id",
                    "Email Resmi": "brida@baliprov.go.id",
                    "Program Inovasi Daerah": "Inovasi Pertanian Organik Berbasis Subak, Perlindungan Indikasi Geografis Produk Tradisional Bali",
                    "Pendamping / PIC": "Kedeputian Riset dan Inovasi Daerah BRIN"
                },
                "galeri": [
                    "/uploads/brida-bali.jpg"
                ]
            },
            {
                "nama": "BRIDA Kota Makassar",
                "slug": "brida-kota-makassar",
                "jenis_id": brida_parent.id,
                "provinsi_kode": "73",       # Sulawesi Selatan
                "kabupaten_kota_kode": "73.71", # Kota Makassar
                "pengelola": "Pemerintah Daerah",
                "status": "Aktif",
                "tahun_operasi": 2023,
                "luas_ha": 1.0,
                "alamat": "Jl. Balaikota No. 1, Sawerigading, Kec. Ujung Pandang, Kota Makassar 90111",
                "latitude": -5.147700,
                "longitude": 119.432700,
                "deskripsi": "Pusat koordinasi riset kota pelabuhan, ketahanan logistik pangan maritim, dan inovasi pelayanan publik terpadu di Indonesia Timur.",
                "extra": {
                    "Nomor Telepon": "(0411) 3614002",
                    "Website Resmi": "https://brida.makassarkota.go.id",
                    "Email Resmi": "info@brida.makassarkota.go.id",
                    "Program Inovasi Daerah": "Lorong Wisata Inovatif, Sistem Manajemen Sampah Plastik Berbasis Sensor",
                    "Pendamping / PIC": "Satker Wilayah Sulawesi BRIN"
                },
                "galeri": [
                    "/uploads/brida-makassar.jpg"
                ]
            },
            {
                "nama": "BRIDA Provinsi Papua Barat Daya",
                "slug": "brida-provinsi-papua-barat-daya",
                "jenis_id": brida_parent.id,
                "provinsi_kode": "96",       # Papua Barat Daya
                "kabupaten_kota_kode": "96.71", # Kota Sorong
                "pengelola": "Pemerintah Daerah",
                "status": "Aktif",
                "tahun_operasi": 2024,
                "luas_ha": 1.5,
                "alamat": "Kompleks Perkantoran Pemerintah Provinsi Papua Barat Daya, Kota Sorong 98414",
                "latitude": -0.876200,
                "longitude": 131.255800,
                "deskripsi": "Inisiator riset pemanfaatan sumber daya hayati berkelanjutan, konservasi ekosistem bahari Raja Ampat, dan pemberdayaan masyarakat adat berbasis inovasi lokal.",
                "extra": {
                    "Nomor Telepon": "(0951) 321889",
                    "Website Resmi": "https://papuabaratdayaprov.go.id",
                    "Email Resmi": "brida@papuabaratdayaprov.go.id",
                    "Program Inovasi Daerah": "Pemetaan Biodiversitas Laut Pesisir, Sertifikasi Produk Hutan Bukan Kayu (Madu & Sagu)",
                    "Pendamping / PIC": "Direktorat Fasilitasi Riset Wilayah Timur BRIN"
                },
                "galeri": [
                    "/uploads/brida-sorong.jpg"
                ]
            }
        ]

        count_added = 0
        if db.query(KSTLokasi).count() > 0:
            print("[!] Locations already exist in kst_lokasi. Skipping sample location seeding.")
            return

        for l_data in locations_data:
            lat = l_data["latitude"]
            lon = l_data["longitude"]
            geom = WKTElement(f"POINT({lon} {lat})", srid=4326) if lat and lon else None

            lokasi_obj = KSTLokasi(
                nama=l_data["nama"],
                slug=l_data["slug"],
                jenis_kawasan_id=l_data["jenis_id"],
                provinsi_kode=l_data["provinsi_kode"],
                kabupaten_kota_kode=l_data["kabupaten_kota_kode"],
                pengelola=l_data["pengelola"],
                status=l_data["status"],
                tahun_operasi=l_data["tahun_operasi"],
                luas_ha=l_data.get("luas_ha"),
                alamat=l_data.get("alamat"),
                latitude=lat,
                longitude=lon,
                geom=geom,
                deskripsi=l_data.get("deskripsi", l_data.get("deskripsi_profil")),
                is_draft=False
            )
            db.add(lokasi_obj)
            db.flush()

            # Extra fields (includes Telepon, Website, Email, and relational Fokus Riset list)
            extra_dict = l_data.get("extra", {})
            for lbl_name, val in extra_dict.items():
                lbl_obj = label_map.get(lbl_name)
                if not lbl_obj:
                    continue

                if lbl_name == "Fokus Riset":
                    if isinstance(val, list):
                        items = val
                    else:
                        items = [x.strip() for x in str(val).split(",") if x.strip()]
                    
                    added_fr_ids = set()
                    for item_str in items:
                        matched_fr = None
                        s = item_str.lower()
                        if any(k in s for k in ["energi", "material", "komposit", "nuklir"]):
                            matched_fr = fokus_map.get("Energi & Material")
                        elif any(k in s for k in ["kesehatan", "obat", "radiofarmaka", "biomedis", "medis"]):
                            matched_fr = fokus_map.get("Kesehatan & Obat")
                        elif any(k in s for k in ["pangan", "pertanian", "hortikultura", "pascapanen"]):
                            matched_fr = fokus_map.get("Pangan & Pertanian")
                        elif any(k in s for k in ["digital", "robotika", "ai", "elektronika", "iot", "komputasi", "telekomunikasi", "mikroelektronika"]):
                            matched_fr = fokus_map.get("Teknologi Digital & Robotika")
                        elif any(k in s for k in ["maritim", "laut", "oseanografi", "perairan", "pesisir"]):
                            matched_fr = fokus_map.get("Kemaritiman & Kelautan")
                        elif any(k in s for k in ["lingkungan", "kebencanaan", "biodiversitas", "konservasi", "botani", "iklim", "genomik", "hayati"]):
                            matched_fr = fokus_map.get("Lingkungan & Kebencanaan")
                        
                        if matched_fr and matched_fr.id in added_fr_ids:
                            continue
                        if matched_fr:
                            added_fr_ids.add(matched_fr.id)

                        val_obj = NilaiDataLokasi(
                            lokasi_id=lokasi_obj.id,
                            field_label_id=lbl_obj.id,
                            value=str(matched_fr.id) if matched_fr else item_str
                        )
                        db.add(val_obj)
                else:
                    val_obj = NilaiDataLokasi(
                        lokasi_id=lokasi_obj.id,
                        field_label_id=lbl_obj.id,
                        value=val
                    )
                    db.add(val_obj)

            # Gallery (First image acts as thumbnail)
            for g_url in l_data.get("galeri", []):
                gal_obj = KSTGaleri(
                    lokasi_id=lokasi_obj.id,
                    tipe="foto",
                    url=g_url
                )
                db.add(gal_obj)

            count_added += 1

        db.commit()
        print(f"  -> SUCCESS: {count_added} sample locations seeded with genuine relational foreign keys to kst_provinsi & kst_kabupaten_kota!")
        print("\n[+] RE-MIGRATION AND SEEDING COMPLETED SUCCESSFULLY!")
        print("    kst_provinsi (38) and kst_kabupaten_kota (514) were kept 100% untouched.")

    finally:
        db.close()


if __name__ == "__main__":
    seed_database()
