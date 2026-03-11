# 🗓️ OptiSched: Smart Academic Scheduler (Akıllı Akademik Çizelgeleme Sistemi)

[![Python](https://img.shields.io/badge/Python-3.12%2B-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OR-Tools](https://img.shields.io/badge/Solver-Google%20OR--Tools-green.svg)](https://developers.google.com/optimization)

[TR] OptiSched, üniversite düzeyindeki derslerin, hocaların ve sınıfların çakışmasız bir şekilde planlanmasını sağlayan, Google OR-Tools (CSP) tabanlı bir optimizasyon sistemidir.

[EN] OptiSched is an optimization system based on Google OR-Tools (CSP) that ensures conflict-free scheduling of university courses, lecturers, and classrooms.

---

## ✨ Features / Özellikler

- **[TR] Akıllı Çizelgeleme:** Hoca, sınıf ve zaman çakışmalarını %100 engeller.
- **[EN] Smart Scheduling:** Prevents 100% of lecturer, classroom, and time conflicts.
- **[TR] Kapasite Kontrolü:** Öğrenci sayısını sınıfların fiziksel kapasitesiyle eşleştirir.
- **[EN] Capacity Management:** Matches student counts with physical classroom capacities.
- **[TR] Esnek Kısıtlamalar:** Öğle arası ve hoca müsaitliği gibi kuralları destekler.
- **[EN] Flexible Constraints:** Supports rules like mandatory lunch breaks and lecturer availability.
- **[TR] Görsel Çıktı:** Renklendirilmiş ve tablolanmış Excel raporları üretir.
- **[EN] Visual Reports:** Generates stylized and categorized Excel reports.

---

## 🚀 Setup & Run / Kurulum ve Çalıştırma

### [TR] Adımlar
1. Python 3'ün yüklü olduğundan emin olun.
2. Sanal ortamı kurun ve aktif edin: `python3 -m venv venv && source venv/bin/activate`
3. Bağımlılıkları yükleyin: `pip install ortools pandas openpyxl`
4. Çalıştırın: `python3 optisched_scheduler.py`

### [EN] Steps
1. Ensure Python 3 is installed.
2. Setup and activate virtual environment: `python3 -m venv venv && source venv/bin/activate`
3. Install dependencies: `pip install ortools pandas openpyxl`
4. Run the script: `python3 optisched_scheduler.py`

---

## 🗄️ Database Roadmap / Veritabanı Yol Haritası

[TR] Proje şu an JSON tabanlı çalışmaktadır ancak bir sonraki aşamada **PostgreSQL** ve **Öğrenci Bilgi Paketi (ÖBP)** entegrasyonu planlanmaktadır. Detaylar `DB_GELISTIRME_REHBERI.md` dosyasındadır.

[EN] The project currently operates on JSON; however, the next phase involves integration with **PostgreSQL** and **Student Information Systems (ÖBP)**. Details are available in `DB_GELISTIRME_REHBERI.md`.

### [TR] Planlanan DB Mimarisi / [EN] Planned DB Architecture
- **Lecturers:** Personel ID, Unavailable Slots (int[]).
- **Classrooms:** Room ID, Capacity, Features (JSONB).
- **Courses:** ÖBP Course Code, Student Count, Curriculum Year.

---

## 🛠️ Tech Stack / Teknolojiler
- **Core:** Python, Google OR-Tools (CP-SAT)
- **Data:** Pandas, JSON
- **Report:** OpenPyXL
- **Storage Plan:** PostgreSQL (Upcoming)

---

