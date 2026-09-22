# İzleme kimlikleri — göreve eklenecek paragraf

Aşağıdaki blok, günlük görevin **Instructions** panelinde `## İZLEME LİSTESİ`
kurallarının hemen altına yapıştırılacak. Tek işi, aynı dosyanın her gün yeni bir
adla yazılıp iki ayrı iplik sayfasına bölünmesini durdurmak.

---

**İzleme kalemlerinin kalıcı kimliği.** Raporu yazmaya başlamadan önce
`https://defintel.shadovi.com/data/threads.json` adresini oku: bu, hâlâ açık olan
izleme dosyalarının `{id, name, son_hareket}` listesidir ve her gece yeniden
üretilir. Bugünkü İZLEME LİSTESİ'ne aldığın bir kalem bu listede varsa —
ifadeyi değiştirmiş olsan bile — **onun `id`'sini aynen kullan**; yeni kimlik
uydurma. Listede yoksa yeni bir kimlik türet: küçük harf, yalnız a-z 0-9 ve
tire, Türkçe harfler sadeleştirilmiş, en çok 48 karakter
(`abd-deniz-piyadeleri-drone-round` gibi). Kimlikleri önbelleğinden değil, her
gün bu adresten oku; ezberlediğin liste ikinci günde eskimiş olur. Bu listeyi
rapora yazma, hiçbir yerde gösterme — yalnız kimlik seçmek için kullan.

Kimlikleri ön bilgi bloğuna `watch:` alanında bildir; `name`, İZLEME LİSTESİ
satırındaki kalın başlığın `G# · ` kısmından sonraki hâliyle **birebir aynı**
olsun:

```yaml
watch:
  - {id: abd-deniz-piyadeleri-drone-round, name: "ABD Deniz Piyadeleri Drone Round"}
  - {id: malezya-merad-rmk-13, name: "Malezya MERAD (RMK-13)"}
  - {id: 665-milyon-lik-c-uas-test-siparisine-itiraz, name: "665 milyon $'lık C-UAS test siparişine itiraz", closed: true}
```

**Bir dosya yalnız açıkça kapanır.** Bir kalem sonuçlandıysa — ihale verildi,
program iptal edildi, karar açıklandı — o kalemi son bir kez İZLEME LİSTESİ'ne
sonucuyla yaz ve `watch:` girdisine `closed: true` ekle. Bunun dışında hiçbir şey
kapanma sayılmaz: bir kalemi bugün listeye almaman onun bittiği anlamına gelmez,
yalnız bugün hareket olmadığı anlamına gelir. Site bu farkı zaten gösteriyor
(kapanan dosya "kapandı", düşen dosya "listede görünmüyor" olur), o yüzden emin
olmadığın hiçbir kalemi `closed` işaretleme — unutmakla bitirmek aynı şey değil.

---

## Neden böyle

- **Liste dosyadan geliyor, panele yapıştırılmıyor.** Panele yazılan bir kimlik
  listesi ikinci gün eskir ve kimse fark etmez; `threads.json` her yayından sonra
  yeniden yazılıyor.
- **Kapanma açık bildirimle.** Ajanın o gün yazmayı unutması ile dosyanın
  gerçekten bitmesi ayrı olaylar; ikisini aynı saymak arşivde sessiz yalan üretir.
- **Eski bölünmeler `data/thread-aliases.json` ile onarılıyor.** Ajan kalıcı
  kimlik vermeye başlamadan önceki günler bulanık eşleşmeyle bağlandı; kaydığı
  yerler takma ad dosyasında elle birleştirildi. Ajanın bu dosyadan haberi olmasına
  gerek yok — kimlikleri o düzeltiyor, ajan yalnız doğru kimliği taşıyor.
