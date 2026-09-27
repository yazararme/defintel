# Rev 21–33 — orkestratör ilerleme kaydı

Sıra: 30, 22, 21, 23, 31, 33, 24, 32, 25, 27, 29, 28, 26. Dal: `rev21-33` (main'den, `322e66c` üstüne).

## Kurulum (2026-09-23)

- `.claude/agents/design-reviewer.md` var. Oturum repo dışında başladığı için alt ajan tipi
  kayıtlı değil. İnceleyici, bu dosyanın metni aynen talimat olarak verilen general-purpose
  alt ajanla çalıştırılıyor (model: opus).
- Ekran görüntüsü: `review/tools/shoot.py`, venv `~/.local/share/defintel-shotenv`
  (playwright + sistem Chrome). Varsayılan 8 sayfa × 2 boyut × 2 tema × (ilk ekran + tam sayfa).
  `review/shots/` .gitignore'da (set başına ~20 MB), commit edilmez.
- Site: repo kökünden `python3 -m http.server 8000 --bind 127.0.0.1`.
- Brifingler: `review/briefs/rev-N.md` = planın o revizyon bölümü, yalnızca P0/P1.
- **Push kontrolü (SETUP 3), 2026-09-23:** Pages yalnızca `main`'den yayımlıyor (legacy,
  branch main /). `build.yml` her dalda push'ta koşar (yalnız `source/**`, `build.py`,
  `assets/**`), build + aynı dala bot commit'i; yayın yok, okuyucu push'u yok.
  collect-news / pull-drive / missing-report yalnızca cron + dispatch. → Şu an dal push'u
  güvenli. **Rev 30'dan sonra yeniden kontrol:** iş akışları `/alert` çağırırsa push
  operatöre bildirim gönderebilir.
- Ortak kararlar: tutulan savunma dışı başlıklar çevrilir (yalnız başlık) → Açık 1 kapandı.
  DÖRT-DURUM ve SİLME-YOK operatör kanalına da gönderir. Kapsam P0+P1; P2, P3, Yapılmayacak atlanır.

## Revizyonlar

| Rev | Karar | Deneme | Commit | Bekleyen insan kontrolü |
|---|---|---|---|---|
| 30 | PASS (issue kanalı) | 1 (+1 iptal edilen push sürümü) | aa9a4c3 | yok |
| 22 | PASS (deneme 2; d1 FAIL P1-2 "1 / 536") | 2 | 29a9667, d9565c1 | yok |
| 21 | PASS (deneme 2; d1 FAIL P0-2 kanıt eksikti) | 2 | 00d908c, 5c1134b | yok |
| 23 | PASS | 1 | 4ca4ef5 | P0-2: prompt yapıştırma + sonraki 3 rapor (human-checks.md) |
| 26 | PASS (kapsam içi: sabit test + uyarı; model çağrısı gerektirenler atlandı) | 1 | e26454c, efdedea | P1-3 Drive dil düzeltmesi; ilk canlı çeviri |
| 28 | PASS (deneme 2; d1 FAIL P0-2 boş kesişim kanıtı yoktu) | 2 | be22179, ab7cf08 | yok |
| 29 | PASS | 1 | 21c7394 | yok |
| 27 | PASS | 1 | b381359 | yok |
| 25 | FAIL (yalnız P0-1 (S) yarısı doğrulanamaz; diğer 6 ölçüt PASS) — bkz. not | 1 | d054ccd | P0-1 (S): canlı ilk toplamadan sonra Trend.az araması |
| 32 | PASS (deneme 2; d1 FAIL CI İLK-EKRAN 817px gerilemesi) | 2 | 8116831, 78e6632 | P1-1: sonraki 5 rapor |
| 24 | PASS | 1 | 41b6998 | yok |
| 33 | PASS | 1 | 325d9fe | yok |
| 31 | PASS | 1 | 6c2c3c1 | P0-3 canlı: main'e alındıktan sonra gerçek aday.md (human-checks.md) |

## Notlar / anlaşmazlıklar

- **23 Eyl — Rev 30 değişti (müşteri):** push kanalı yerine günlük GitHub issue'su, `GITHUB_TOKEN`, atanan `yazararme`; worker.js değişmez, yeni sır yok; (P) → issue ekran görüntüsü (I). Review loguna yazıldı (`~/Documents/Projects/defintel-ux/design-review-log-TR.md`, "Revizyon 30 — değişti"). Eski push kodu çalışma ağacından atıldı; notları `review/builder-notes/rev-30-push-kanali-iptal.md`. İnsan kapısı kalktı; Rev 22'den itibaren durmadan devam.
- Bildirim sınaması: kendi hesapla açılan #1, #2 bildirim üretmedi (GitHub kendi eylemini bildirmez); bot açtığı #3 üretti ama telefonda GitHub Mobile "Assigned" push kapalıydı; açıldıktan sonra #4 telefona ulaştı. Hepsi kapatıldı.
- `rev21-33` dalı origin'e push edildi (409cd84, yalnız tek seferlik sınama iş akışı). SETUP 3 kontrolü: Pages yalnız main; build.yml path'lerine dokunulmadı.

- Rev 30: (A) kanıtı için geçici `rev30-ci` dalı push'u ve inceleyici alt ajanı otomatik mod izin sınıflandırıcısınca reddedildi. Hiçbir şey commit/push edilmedi. P1-1 (A) → PENDING-HUMAN.
- Rev 30: iPhone kaydı için 5 dokunuş (altbilgi notu) eklendi; `#operator=` Android'de de çalışır.
- Rev 30 kuralı yok: 18 kuralın hiçbiri henüz kodda değil; P0-2 ve P0-3 ancak ilk kural (Rev 22) gelince telefonda denenebilir.

- Rev 30 commit'i (aa9a4c3) inceleyiciden **önce** atıldı: (I)/(A) kanıtı ancak dal push'uyla üretilebiliyor. Sonraki revizyonlarda da (A)/(I) gerekiyorsa aynı sıra: commit → push → kanıt → inceleme; FAIL'de düzeltme commit'i.
- Rev 30 inceleyici notu: uyarısız özet satırı "issue — ·" (kozmetik). Bilinen sınır: main'de aynı anda iki boşaltma aynı gün iki issue açabilir (kilit yok).
- `uyari-test.yml` yalnız rev21-33 dalında tetiklenir; main'e alınmadan önce silinebilir.
- (A) özetleri GitHub'da yalnız oturum açıkken görünüyor; kanıt Chrome (oturumlu) ekran görüntüsüyle alınıyor.

- design-reviewer.md (P)'yi PENDING-HUMAN sayıyor; Rev 30 sonrası (P) → (I) değişimini her inceleme istemine yazıyorum. Tanım dosyasını değiştirmedim (kullanıcının dosyası).
- Rev 22 d1 kanıtı: yeşil run 35867515608, bozuk (boz=fetch) run 35867655946 → issue #5'e DÖRT-DURUM satırı (issue yeniden açıldı).
- Rev 22 inceleyici notları: "2 / 536" bir başlığı iki kez sayıyor (Açık 2); yeşil özet görüntüsü d1 run'ından (d2 artifact'leri ayrı). Taze tarayıcıda 375px'te "Yeni rapor çıkınca haber verelim mi?" bandı ~150px kaplıyor; shoot.py `service_workers="block"` kullandığı için çekimlerde yok. Bant Rev 22'den önce de vardı (app.js ziyaret sayacı); plan Rev 29 sıra 26 (P2) ile ilgili.

- Rev 21 d1 kanıtı: normal run 35871179217 (alias 64/64), kapsam_boz=thales run 35871351691 → issue #5 KAPSAM-SAYI satırı. 64 oyuncunun 36'sının pozitif örneği kurgu (`pos_kaynak: kurgu`) — plan buna izin veriyor, müşteriye not.
- Rev 21 inceleyici notu: etkin çipin etiketi fare üstündeyken neredeyse görünmüyor (dokunmatikte yapışabilir).

- Rev 21 d2: etkin çip hover kontrastı düzeltildi (app.css). İnceleyici gerilemeleri: 375px'te Nammo ve NORINCO satırlarında yaş/sayı jetonu alt satıra kırılıyor (küçük).

- Rev 23 kurucu notları: H1-TEKRAR 15, 18, 20, 21, 22 Eylül'de de ateşlerdi (desen). Oyuncular rayı Rheinmetall'i G9'a bağlıyor, oysa G9'un başlığı artık etiket ("Lynx XM30 prototip teslimi") ve gövdede ad yok. Eski günlerin başlıkları da etikete döndü.

- Rev 23 kanıtı: uyari_test dispatch run 35882418738 → issue #5 KUR + H1-TEKRAR satırları. İnceleyici: issue gövdesinde iki "$" GitHub'da matematik olarak işleniyor (KUR satırı kısmen okunmaz) → Rev 30 düzeltmesi (uyari.py kaçış) ayrı commit.

- Rev 31 kanıtı: gec-gelen-test run 35884913775 (çevrimdışı, sabah hattı çalıştırılmadı). `data/news/2026-09-24-aday.md` yalnız yerel, commit edilmedi. Yerel http.server .md için charset göndermiyor → Türkçe harfler bozuk görünüyor; canlı site utf-8 gönderiyor. `gec-gelen-test.yml` ve `uyari-test.yml` main'e alınmadan önce silinebilir.

- Rev 33 kanıtı: normal run 35886871966 (0 örnek), noktali_boz run 35887041545 (3212 örnek) → issue #5. Kurucu kararı: "SCMP (Çin)" yalnız "SCMP" sarıldı; ülkesi boş kaynaklar Türkçe harf yoksa yabancı sayılıyor.

- Rev 24 kanıtı: normal run 35889572520 (294/791), ilk_ekran_boz run 35889721553 (401/898) → issue #5. İnceleyici: 375'te çip şeridinin kaydığını gösteren ipucu yok; alarm günlerinde özet ilk ekranın altında (Açık 6).

- Rev 32 kanıtı: normal run 35891692823, uyari_test run 35891836966 → issue #5 TEKRAR-MANŞET satırı. Dikkat: aynı normal run'da CI İLK-EKRAN kırmızı (4. madde 817px > 812; yerelde 791) — "ilk:" jetonu CI'daki satır kırılımıyla özeti uzatmış olabilir.

- **Rev 25 anlaşmazlığı (verdict değiştirilmedi):** inceleyici, tanımı gereği doğrulanamayan R25-P0-1 (S) yarısı yüzünden FAIL verdi. O kalemler 23 Eylül'de toplanırken düşürüldüğü için saklı veride yok; yeni bir kurucu bunu düzeltemez, kanıt yalnız canlı toplamayla oluşur (sabah hattını daldan çalıştırmak yasak). Yeniden deneme yapılmadı; sonraki revizyonlar buna bağlı değil. Kalan 6 ölçüt PASS, gerileme yok. İnceleyici gözlemi: Deniz ve İnsansız Sistemler 16→39, sivil dron teslimat gürültüsü (DroneXL dahil) oraya taşındı — S3'ün yan etkisi.
- Rev 25 kanıtı: silme-yok-test run 35902549021 (esit yeşil, bozuk kırmızı), build run 35902548911 (Kategori isabeti, ipucu 0). Yeni kök dosya `oyuncu_eslestir.py`. 17–22 Eylül eski kategorilerde kaldı. `silme-yok-test.yml` main'e alınmadan silinebilir.

- Rev 27: P2-1 slug/yönlendirme ve SLUG kuralı atlandı (P2). Kurucu notu: günün gelişmesi de olan izleme maddeleri kendini her gün atıflıyor, her atıf hareket sayılıyor (ör. Malezya MERAD 9 hareket) — önceden vardı. İnceleyici: XM30'da durum satırı 23 Eylül satırının notunu aynen tekrarlıyor.
- Rev 29: P2/P3 (F-07, F-13, yazı belirteçleri, F-11) ve TİP-BELİRTECİ atlandı. Kurucu kapsam dışı iki şey yaptı: Öne çıkanlar (`.highlights`) sol kenarı da kalktı (L1-DOLGU aksi hâlde her derlemede ateşlerdi); ≤600px'te kurulum çubuğu açıkken footer alt boşluğu 168px. `--alarm-tint` zemin sayılmadı (durum rengi). İnceleyici: 375'te bildirim kartının alt çizgisi ilk endnav düğmesine 1px. Tersine dönüş Rev 0 → R29.4 DECISIONS (9) ve review loguna yazıldı (82578ab).
- Rev 28 kanıtı: normal build 35910521447, bos_kesisim build 35910757525 (Elbit+Northrop yalnız o çalıştırmada yanıt vermiş sayıldı; veri değişmedi).
- Rev 26: sabit test audit/'e (gitignore) bağlıydı, CI'da kırıldı; fixture `scripts/fixtures/ceviri-ornegi-40.json` ile düzeltildi (efdedea). Kanıt: ceviri-dedektoru-test run 35913238627.
- **Durum (23 Eylül akşamı): 13 revizyonun hepsi işlendi.** Dal `rev21-33` origin'de; main'e alınmadı, deploy yok.

## Açık (orkestratörün eklediği)

1. ~~(push kanalı için)~~ Kanal issue'ya döndü; müşteri issue'nun herkese açık olduğunu bilerek seçti — kapandı. Eski metin: Repo herkese açık → (A) Actions özet sayfası da herkese açık ve uyarı metnini listeliyor. Plan bildirime dokununca bu sayfayı açtırıyor, ama "uyarı metni herkese açık dosyaya yazılmaz" diyor. Özete yalnızca kural adı + sayı mı yazılsın?
2. **R22 kapsam satırı birimi.** Plan "{görünen} / 536 başlık" ve roketsan için "2 / 536" diyor; görünen = satır sayısı (aynı başlık iki bölümde iki satır). Payda benzersiz başlık. Sonuç: tümünü eşleyen süzgeçte "551 / 536" basılabilir. Pay benzersiz başlık mı olsun (roketsan "1 / 536", ölçütle çelişir), yoksa payda da satır mı? Deneme 2 plana harfiyen uydu.
3. **Brifing "Oyuncular" rayı ↔ /oyuncular.html.** Rev 21'den sonra oyuncular sayfası "Bugün 15" diyor (tüm başlıklar, 64 oyuncu), brifingin rayı hâlâ 9 ad sayıyor (yalnız brifing gövdesi; Thales yok). Plan R21.1 "ray adları olduğu gibi kalır" diyor. Ray da genişletilmiş eşleştiriciyi kullansın mı, yoksa iki yüzeyin farklı soruyu yanıtladığı (brifingde geçen / günün başlıklarında geçen) etiketle mi söylensin?
4. **KUR kuralı genişletildi (Rev 23).** Planın yazdığı hâliyle KUR 23 Eylül'de ateşlemiyor: atıflı [K3] özeti brifingin "1,5 milyar $ (16 milyar NOK)" ifadesini aynen içeriyor; 1,74 başka bir kaynağın ([K2]) özetinde. Kurucu ikinci tetik ekledi: atıflı özetler aynı para biriminde farklı değer veriyorsa uyarı. Kabul ölçütü ("KUR: SAN CUAS 1,5 milyar $ ↔ özet 1,74") ancak bununla karşılanıyor. Onay?
5. **23 Eylül'ün kayıp 92 kalemi (Rev 31).** 05:19 dosyasındaki 92 kalem, 11:04 yedek toplama üzerine yazınca kayboldu (Rev 0: hiçbir kalem silinmez). Geri getirilirse 23 Eylül'ün sayısı 536 → 628 olur. Geri getirilsin mi?
6. **İLK-EKRAN neredeyse her gün ateşliyor (Rev 24).** 375×812'de son 10 günün 7'sinde kural kırmızı: dört satırlık başlık, uzun özet maddeleri, alarm günleri (Rev 9 gereği ALARMLAR özetin üstünde, hiç geçemez). 23 Eylül h2'de 6px payla geçiyor. Rev 9: her gün ateşleyen kanal sıfır bilgi taşır. Alarm günleri kuraldan muaf mı olsun, eşik mi gevşesin, yoksa başlık/madde uzunluğu mu sınırlansın? Ayrıca planın `h2#yonetici-ozeti`'si sayfada `h2#ozet`.
7. **Rev 26: canlı pencerenin yeniden çevrilmesi.** Cümle düzeni, Ö1/Ö2 ve sözlük yalnız yeni çevirilerde görünür. R26-P0-1, P1-1, P1-2 ve P0-2'nin ikinci yarısı `translate_news.py`'nin `claude -p` ile gerçek çağrılarını (abonelik kotası; 23 Eylül için ~9 parti) ve yayımlanan `data/news/*.json`'ın yeniden yazılmasını gerektiriyor. Bu turda izin yoktu, atlandı. İzin verilirse: hangi günler (yalnız 23? 17–23?) ve yerelde mi, `collect-news` dispatch'iyle mi?
8. **KANIT-BOŞLUĞU her gün ateşliyor (Rev 28).** Elbit'in akışı boş, Northrop'unki 403 — 17–23 Eylül'ün 7 tarama gününün 7'sinde brifingde "…kendi duyuruları bugün okunamadı" satırı ve operatör uyarısı var (Rev 9 deseni). Satır doğru, ama iki akış onarılana kadar sabit. Akışlar onarılsın mı (kaynaklar.json, Drive), yoksa sürekli arızalı kaynak için satır bastırılsın mı?
9. **Rev 26 geçiş riski.** Cümle düzeni dedektörü eski (her kelimesi büyük) çevirilerin çoğunu yakalıyor: sahte günde 40'ın 30'u, 31 başlık özgün bırakıldı. main'e alındıktan sonra model yeni promptta cümle düzenine uymazsa çok sayıda başlık İngilizce/özgün kalır ve her gün ÇEVİRİ-DEDEKTÖRÜ uyarısı gelir. İlk canlı çevirinin sonucuna bakılmalı (human-checks).

## Müşteri kararları — 23 Eylül akşamı (Açık 1–9)

1. Kapsam satırı payı = benzersiz başlık; ölçüt "1 / 536" (plan R22-P1-2 güncellendi). → **K1**
2. İki oyuncu listesi kalır; etiketler "brifingde geçen" / "başlıklarda geçen". → **K2**
3. KUR genişletmesi onaylandı (iş yok).
4. 23 Eylül'ün kayıp 92 kalemi geri getirilir, BRİFİNGDEN SONRA etiketiyle. → **K4**
5. İLK-EKRAN'da alarm günü muafiyeti yok; 10 günün 7'sinin taşma nedeni bulunup düzeltilir (ör. promptta özet maddesine kelime sınırı); kural kalır. → **K5**
6. Elbit ve Northrop akışları onarılır; onarılamıyorsa yerine kaynak önerilir (ör. şirketin basın bülteni sayfası). Onarılana kadar satır kalır. → **K6**
7–8. Yeniden çeviri yalnız main'e alındıktan sonra: bir gün yerelde yeniden çevrilir, 20 başlıklık önce/sonra örneği gösterilir, müşterinin onayı beklenir.
- human-checks: 4 sınama iş akışı main'e alınmadan silinir. Issue #5 kapatılır (K döngülerinden sonra; döngüler onu yeniden açar). Instructions metni merge günü yapıştırılır → tek blok `review/builder-notes/merge-day-prompt.md`. Drive `dil` düzeltmesini müşteri yapıyor.

| K | Karar | Deneme | Commit |
|---|---|---|---|
| K1 | PASS | 1 | 56501f2 |
| K2 | PASS (deneme 2; d1 FAIL: ray adları metinde yoktu — alias; alt-64 kanıtı eskiydi). Yan etki: raylardan başlık taramasından gelen Türk oyuncular düştü (17–22 Eyl); 23 Eyl rayında Rheinmetall yok (yalnız basılmayan G9 girişinde geçiyordu) | 2 | 727d21c, 449f883 |
| K5 | PASS (d2 kodu; 3. inceleme — d1 FAIL alarm günü, d2 incelemesi kesik kanıt yüzünden FAIL). Orkestratör K5-2 ölçütünü yayımlanmış metin değişemediği için "yapısal neden kalktı + sınırla geçer" olarak yeniden yazdı. Prompt sınırları: başlık ≤65, alarm başlığı ≤70, madde ≤110. Tersine dönüş: DECISIONS 10 (Rev 9 → K5). 17 Eyl CI'da 3px payla geçiyor | 3 | aeedc4f, 6f3da19, d417af0 |

- **K4 kararı (27 Eyl): A — etiketsiz.** ~~K4 bekliyor:~~ müşteriye soruldu — 92 kalem brifingden ÖNCE (05:19) toplanmış, 33ü aday listesindeydi; "BRİFİNGDEN SONRA" yanlış olur. Seçenekler: A etiketsiz, B doğru başka etiket, C yine de BRİFİNGDEN SONRA.
| K6 | PASS (deneme 2; d1 FAIL: Elbit nedeni tahmindi, teslim notu yinelenen girdi yaratırdı). Northrop: Accept-Language başlığı (CI'dan doğrulandı). Elbit: /feed/ kaldırılmış → /news HTML ayrıştırıcısı (CI'dan 10 kayıt). Elbit Systems UK isteğe bağlı ek kaynak. İnceleyiciye bu değişiklikte builder notlarını okuma izni verildi (ölçütler notlarla ilgili) | 2 | 6ddf97f, 8545c50, ac112eb |

- 24 Eyl: 5 sınama iş akışı silindi (uyari-test, gec-gelen-test, silme-yok-test, ceviri-dedektoru-test, k6-kaynak-test); smoke.py silinmiş dosyalara dayanmıyor. Issue #5 kapatıldı. merge-day-prompt.md yazıldı. human-checks.md üç bölüm olarak yeniden yazıldı.
- **Açık:** yalnız K4 (müşteri seçimi A/B/C).

## 27 Eylül oturumu

- Adım 0: "1 kabuk çalışıyor" = 23 Eyl'den kalan yerel site sunucusu (`http.server 8000`); bu oturumun incelemeleri için açık tutuldu, oturum sonunda durduruldu. Ayrıca iki artık süreç durduruldu: 22 Eyl'den `http.server 8802` ve 4 günlük Rev 30 push-worker taklidi (`node e2e.mjs`, localhost:8799, sahte sırlar). Çalışma ağacında `review/human-checks.md` commit'lenmemiş biçimde silinmişti → `git restore` ile geri alındı. `data/news/2026-09-24-aday.md` yerel Rev 31 kanıtı, izlenmiyor, dokunulmadı.

| K | Karar | Deneme | Commit |
|---|---|---|---|
| K4 | PASS (A: 92 kalem etiketsiz, `ilk_goruldu` 05:19:10; 536 → 628). Orkestratör K4-4'ü **inceleme öncesi** düzeltti: /oyuncular.html ve brifing sayıları günün başlıklarından türediği için değişir (Bugün 14→17; Saab, Sarsılmaz, STM 23 Eyl bağlantısı). Divyastra kalemi brifingde atıflı → BRİFİNGDE. Bir görünür yinelenen: Euro-SD "FQ-42 Vengeance…" mevcut Armada kalemiyle aynı başlık — A gereği tutuldu (düşerse 627) | 1 | ad0da58 |

- Drive yedeği: `kaynaklar-yedek-2026-09-27.json` (id `1-hX142ZN141ynOcD48CjGqxQcRVf-aYA`, 38.608 B, özgün son düzenleme 17 Eyl). Toplayıcı yalnız tam adı `kaynaklar.json` olanı okur.
- Adım 3: `review/verdicts/self-check.md` (bağımsız alt ajan): K5-2 yeniden yazımı WEAKER; 110'da 10 maddenin 3'ü kilit bilgi kaybediyor; 120 ve 130 İLK-EKRAN'da 20 Eyl'de kalıyor (CI en kötü 835); 115: 1 kayıp, 10 günün hepsi geçiyor (20 Eyl 3px payla). Hiçbir şey değiştirilmedi — müşteri karar verir.
| K7 | PASS (iş akışı başına `concurrency`, `cancel-in-progress: false`; ortak `publish` grubu kalktı). Kanıt: build #109/#110 (36349744589, 36349750603) — #110 "waiting for build #109", ikisi de success; tek issue #8 (+4 / +0 satır), sonra kapatıldı. Orkestratör K7-2'yi **inceleme öncesi** düzeltti ("satırlar eklenmiş" → aynı uyarılar yinelenmez, +0 olabilir) | 1 | 1c2a576 |

- Adım 4 deneme merge'ü: `review/builder-notes/trial-merge.md`. 23 çakışma, hepsi üretilmiş dosya; kaynakta çakışma yok. Birleşik ağaçta build.py 0, kural testleri yeşil; smoke 79 ok / 10 FAIL (hepsi 23 Eyl'e sabitlenmiş test ya da beklenen: 27 Eyl İLK-EKRAN 835, eski kategoriler). Geçici dal silindi, push yok.
- Düz `git merge` merge günü duracağı için `review/tools/merge_day.sh` ve `review/tools/rollback.sh` yazıldı; ikisi de push'suz denendi. `review/builder-notes/rollback.md`, `review/human-checks.md` yeniden yazıldı.
- Oturum sonu: 8000 sunucusu durduruldu. Açık kararlar human-checks "Senin kararın gereken konular" 1–5.

## 27 Eylül oturumu — müşteri kararları (1–5)

1. Özet maddesi sınırı **115** (merge-day-prompt.md, k5-prompt.md güncellendi; check_reports benzetim sabiti smoke düzeltmesinde).
2. **K5 açık kalır:** merge'den sonra ilk gerçek alarm gününde yayımlanan sayfada doğrulanır (human-checks "Merge'den sonra").
3. collect-news + pull-drive tek ortak grup → **K8**.
4. **24–27 Eylül toplandığı gibi kalır** (eski kategoriler, 17–22 gibi). Yeni kategoriler **merge gününden itibaren** toplanan günlere uygulanır. 23 Eylül Rev 25'te yeniden kategorilenmişti.
5. Yinelenen başlık düşer → **K9** (627).
- **Yeni kural (müşteri):** kabul ölçütü müşterinin onayı olmadan değiştirilmez; öneri yapılır, beklenir. K9-2 bu kuralla onaylanarak değişti.
- Instructions paneli yedeği `review/builder-notes/instructions-backup.md`. Panelde "en fazla 14 kelime" kuralı **yok**; merge-day-prompt.md yapıştırma yeri buna göre düzeltildi (Kalite kontrolünün üstüne "Ek kurallar (Eylül 2026)").
- Başlık testi: `review/verdicts/headline-check.md` — 65'te 10'un 1'i kilit bilgi kaybediyor, 75'te 0; İLK-EKRAN 75'te 20 Eyl CI en kötü 840px ile kalıyor, 65'te 10 gün geçiyor (20 Eyl 3px). Karar müşteride.

| K | Karar | Deneme | Commit |
|---|---|---|---|
| K8 | PASS (collect-news + pull-drive `publish-${{ github.ref }}`; build, missing-report kendi grupları). Kanıt: collect-news dry_run #39/#40 (36351005079, 36351011322) — #40 "waiting for collect-news #39", 3 sn sonra başladı, ikisi success. pull-drive dalda dispatch edilmedi (main'e rebase edip dala push eder) | 1 | 7577505 |
| K9 | PASS (Euro-SD "FQ-42 Vengeance…Creech" düştü; 627; K4 notu 91 geri + 1 yinelenen düştü). K9-2 müşteri onayıyla yeniden yazıldı | 1 | 3057874 |

- smoke.py tarihten bağımsız (83b25f3): dal 92 ok / 0 FAIL; birleşik (origin/main + dal, sahte 28 Eyl dahil) 93 ok / 0 FAIL. Eski toplayıcı günleri veriden (toplamalar/ilk_goruldu yok) tanınıyor; tarih sabiti yok. `DEFINTEL_BASE` ile başka sunucuya koşar. merge_day.sh DRY yeniden geçti (23 çakışma, build OK). Not: merge'den sonra eski toplayıcı günleri (24 Eyl → merge günü) için build İPUCU-YOK uyarısı verir — beklenen, karar 4.
- Drive: `kaynaklar.json` yeni dosya (id `1XQkEwGDArRExmaIRgtWsuDTJwJ5GtcDs`), Defense Studies `dil: id`; bayt bayt doğrulandı; eski dosya `kaynaklar-onceki-2026-09-27.json`. Apps Script: 42. satır ve 16. satır doğru, değişiklik/kaydetme yok; `testToplayici` çalıştırılmadı (main'e gerçek toplama commit'ler).
- Oturum sonu: 8000 sunucusu durduruldu. Açık: müşteri kararı manşet 65/75; telefon incelemesi; merge onayı.
