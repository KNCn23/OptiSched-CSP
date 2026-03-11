# OptiSched

Üniversite ders programı planlama (scheduling) sistemi prototipi.

## Kurulum

1.  Python 3'ün yüklü olduğundan emin olun.
2.  Sanal ortamı aktif hale getirin:
    ```bash
    source venv/bin/activate
    ```
3.  Gerekli kütüphaneleri yükleyin:
    ```bash
    pip install ortools
    ```

## Çalıştırma

```bash
python3 optisched_scheduler.py
```

## Dosyalar

- `optisched_data.json`: Hoca, ders, sınıf ve zaman dilimi verilerini içerir.
- `optisched_scheduler.py`: Çizelgeleme algoritmasını (CP-SAT) çalıştıran ana script.
- `.vscode/settings.json`: VS Code için Python ortamı yapılandırması.
