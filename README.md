# 🗓️ OptiSched: Smart Academic Scheduler (Akıllı Akademik Çizelgeleme Sistemi)

[![Python](https://img.shields.io/badge/Python-3.14-blue.svg)](https://www.python.org/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![OR-Tools](https://img.shields.io/badge/Solver-Google%20OR--Tools-green.svg)](https://developers.google.com/optimization)

[TR] OptiSched, üniversite düzeyindeki derslerin, hocaların ve sınıfların çakışmasız bir şekilde planlanmasını sağlayan, Google OR-Tools (CSP) tabanlı bir optimizasyon sistemidir. Bu versiyon, derslerin teorik ve laboratuvar bölümlerini otomatik olarak ayrıştırarak (2-2 veya 3-2 kuralı ile) blok halinde çizelgeleyen gelişmiş bir yapıya sahiptir.

[EN] OptiSched is an optimization system based on Google OR-Tools (CSP) that ensures conflict-free scheduling. This version includes an advanced engine that automatically splits course loads into theory and lab blocks (following 2-2 or 3-2 rules) and ensures they are scheduled in sequence.

---

## ✨ Features / Özellikler

- **[TR] Blok Çizelgeleme:** Teorik dersler ve laboratuvarlar, kurala uygun (2-2/3-2) şekilde ayrıştırılır ve peş peşe planlanır.
- **[EN] Block Scheduling:** Lectures and labs are automatically split (based on 2-2/3-2 rules) and scheduled sequentially.
- **[TR] Çakışma Yönetimi:** Hoca, departman, dönem ve oda çakışmaları %100 engellenir.
- **[EN] Conflict Management:** 100% prevention of lecturer, department, semester, and room conflicts.
- **[TR] Excel Entegrasyonu:** Veriler doğrudan Excel'den (`2.xls`) okunur ve biçimlendirilmiş Excel raporları üretilir.
- **[EN] Excel Integration:** Reads directly from Excel files and generates formatted Excel reports.

---

## 🚀 Setup & Run / Kurulum ve Çalıştırma

1. Python 3.14+ kullanılması önerilir.
2. Bağımlılıkları yükleyin: `pip install ortools pandas openpyxl xlrd`
3. Çalıştırın: `python3 OptiSched/optisched_scheduler.py`


