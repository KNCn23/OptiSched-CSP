# 🐘 OptiSched: PostgreSQL & ÖBP (Öğrenci Bilgi Paketi) Entegrasyon Planı

Bu sayfa, OptiSched çizelgeleme motorunun (CSP) verileri doğrudan **Öğrenci Bilgi Paketi (ÖBP)** sisteminden çekmesi ve **PostgreSQL** üzerinde verimli bir şekilde işlemesi için hazırlanan mimari rehberdir.

---

## 🏗️ Veritabanı Mimarisi (PostgreSQL-Native)

PostgreSQL'in JSONB ve Array özelliklerini kullanarak ÖBP'den gelen ham veriyi yüksek performanslı bir çizelgeleme girdisine dönüştüreceğiz.

### 1. `lecturers` (Hocalar)
*   `id` (PK): ÖBP'den gelen benzersiz Personel ID.
*   `name`: Ad Soyad.
*   `title`: Unvan.
*   `unavailable_slots`: `int[]` (Array) - Hocanın ders veremeyeceği kesin saat dilimleri (ÖBP'deki ders yükü veya özel izinlere göre).

### 2. `classrooms` (Derslikler)
*   `id` (PK): Derslik kodu (Örn: A101, Lab-2).
*   `capacity`: Maksimum öğrenci kapasitesi (ÖBP fiziksel imkanlar tablosundan).
*   `features`: `JSONB` - (Örn: `{"projector": true, "os": "linux", "pc_count": 40}`).

### 3. `courses` (Dersler - ÖBP'den Çekilecek)
*   `id` (PK): ÖBP Ders Kodu (Örn: BLM201).
*   `name`: Ders adı.
*   `lecturer_id` (FK): Dersi veren hoca (ÖBP Ataması).
*   `weekly_hours`: Haftalık toplam ders saati (ÖBP Akts/Kredi tablosundan).
*   `student_count`: Derse kayıtlı aktif öğrenci sayısı (Kapasite kontrolü için canlı veri).
*   `curriculum_year`: Müfredat yılı (1. Sınıf, 2. Sınıf vb. - Öğrenci çakışmasını engellemek için kritik).
*   `is_lab`: `boolean` - Laboratuvar ihtiyacı olup olmadığı.

### 4. `schedule_output` (Çizelgeleme Sonuçları)
*   `id` (PK).
*   `course_id` (FK).
*   `classroom_id` (FK).
*   `day_of_week`: 1-5 arası gün kodu.
*   `start_slot`: Başlangıç saati.
*   `duration`: Ders süresi.

---

## 🚀 ÖBP Entegrasyonu & Geliştirme Yol Haritası

### Faz 1: ÖBP Veri Çekme (ETL Süreci)
- [ ] ÖBP sisteminden (muhtemelen Oracle veya MSSQL) verilerin PostgreSQL'e aktarılması için bir **ETL (Extract, Transform, Load)** scripti yazılması.
- [ ] **Data Cleaning:** ÖBP'deki hatalı veya eksik (kapasitesi girilmemiş sınıflar vb.) verilerin ayıklanması.

### Faz 2: PostgreSQL Optimizasyonu
- [ ] `curriculum_year` ve `lecturer_id` alanlarına **B-Tree Index** atılarak algoritmanın sorgu hızının artırılması.
- [ ] PostgreSQL'in **View** yapısı kullanılarak, algoritma için "temizlenmiş" ve "birleştirilmiş" hazır bir veri seti (Input View) oluşturulması.

### Faz 3: Motor Entegrasyonu (Python & SQLAlchemy)
- [ ] Python motorunun `psycopg2` veya `asyncpg` üzerinden PostgreSQL'e bağlanması.
- [ ] Algoritma bittiğinde sonuçların `schedule_output` tablosuna `Bulk Insert` ile saniyeler içinde yazılması.

---

## ⚠️ Kritik Uyarılar (Database Team İçin)
*   **Canlı Veri:** ÖBP'deki öğrenci sayıları dönem başında değişkendir; algoritma çalıştırılmadan hemen önce verinin güncelliği (Sync) kontrol edilmelidir.
*   **Conflict Resolution:** Eğer ÖBP'den gelen bir hoca ataması teknik olarak imkansızsa (Hocanın ders yükü haftalık saat diliminden fazlaysa), veritabanı bunu algoritmadan önce raporlamalıdır.
*   **PostgreSQL Role:** Uygulama için sadece `SELECT` ve `INSERT` yetkisi olan kısıtlı bir DB kullanıcısı oluşturulmalıdır.
