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
- **Devam noktası:** sıradaki Rev 25 (brief hazır: review/briefs/rev-25.md), sonra 27, 29, 28, 26.

## Açık (orkestratörün eklediği)

1. ~~(push kanalı için)~~ Kanal issue'ya döndü; müşteri issue'nun herkese açık olduğunu bilerek seçti — kapandı. Eski metin: Repo herkese açık → (A) Actions özet sayfası da herkese açık ve uyarı metnini listeliyor. Plan bildirime dokununca bu sayfayı açtırıyor, ama "uyarı metni herkese açık dosyaya yazılmaz" diyor. Özete yalnızca kural adı + sayı mı yazılsın?
2. **R22 kapsam satırı birimi.** Plan "{görünen} / 536 başlık" ve roketsan için "2 / 536" diyor; görünen = satır sayısı (aynı başlık iki bölümde iki satır). Payda benzersiz başlık. Sonuç: tümünü eşleyen süzgeçte "551 / 536" basılabilir. Pay benzersiz başlık mı olsun (roketsan "1 / 536", ölçütle çelişir), yoksa payda da satır mı? Deneme 2 plana harfiyen uydu.
3. **Brifing "Oyuncular" rayı ↔ /oyuncular.html.** Rev 21'den sonra oyuncular sayfası "Bugün 15" diyor (tüm başlıklar, 64 oyuncu), brifingin rayı hâlâ 9 ad sayıyor (yalnız brifing gövdesi; Thales yok). Plan R21.1 "ray adları olduğu gibi kalır" diyor. Ray da genişletilmiş eşleştiriciyi kullansın mı, yoksa iki yüzeyin farklı soruyu yanıtladığı (brifingde geçen / günün başlıklarında geçen) etiketle mi söylensin?
4. **KUR kuralı genişletildi (Rev 23).** Planın yazdığı hâliyle KUR 23 Eylül'de ateşlemiyor: atıflı [K3] özeti brifingin "1,5 milyar $ (16 milyar NOK)" ifadesini aynen içeriyor; 1,74 başka bir kaynağın ([K2]) özetinde. Kurucu ikinci tetik ekledi: atıflı özetler aynı para biriminde farklı değer veriyorsa uyarı. Kabul ölçütü ("KUR: SAN CUAS 1,5 milyar $ ↔ özet 1,74") ancak bununla karşılanıyor. Onay?
5. **23 Eylül'ün kayıp 92 kalemi (Rev 31).** 05:19 dosyasındaki 92 kalem, 11:04 yedek toplama üzerine yazınca kayboldu (Rev 0: hiçbir kalem silinmez). Geri getirilirse 23 Eylül'ün sayısı 536 → 628 olur. Geri getirilsin mi?
6. **İLK-EKRAN neredeyse her gün ateşliyor (Rev 24).** 375×812'de son 10 günün 7'sinde kural kırmızı: dört satırlık başlık, uzun özet maddeleri, alarm günleri (Rev 9 gereği ALARMLAR özetin üstünde, hiç geçemez). 23 Eylül h2'de 6px payla geçiyor. Rev 9: her gün ateşleyen kanal sıfır bilgi taşır. Alarm günleri kuraldan muaf mı olsun, eşik mi gevşesin, yoksa başlık/madde uzunluğu mu sınırlansın? Ayrıca planın `h2#yonetici-ozeti`'si sayfada `h2#ozet`.
