### Her revizyonun taşıması gerekenler

Her revizyon dört şey taşır: **Hedef**, **Dosyalar**, adıyla bir **build kuralı** ve bir
inceleyicinin **yalnızca ekran görüntüsünden** kontrol edebileceği kabul ölçütleri.

Kabul edilen ekran görüntüsü yüzeyleri:

- **(S)** canlı sitenin sayfası, 375×812 ya da 1440×900
- **(P)** operatörün telefonuna gelen push uyarısı (Rev 30)
- **(A)** GitHub Actions çalıştırmasının özet sayfası (`$GITHUB_STEP_SUMMARY`)
- **(D)** sitenin tarayıcıda açılan herkese açık bir veri dosyası (`/data/…`)

Kaynak kod, JSON içeriği ya da terminal çıktısı kabul ölçütü olamaz.

---
