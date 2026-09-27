# Merge günü — görev talimatına tek seferde yapıştırılacak blok

**Ne zaman:** dal `main`'e alındıktan hemen sonra (bir sabah çalıştırmasından sonra, ertesi 06:00'dan önce).
**Nereye:** Claude masaüstü uygulaması → "MKE Uluslararası Pazar İzleme Ajanı (Günlük)" görevi → **Instructions** paneli.
Drive'daki `task-prompt.md`'ye değil — o bir kopya, görev onu okumaz.

## Yapıştırılacak blok (7 cümle)

```
Tutarı kaynağın verdiği para biriminde yaz. Kaynak kendi çevirisini veriyorsa parantez içinde aynen aktar. Kendin kur çevirme.
Başlık günün tezidir, özet maddelerinden biri değildir.
Manşet en fazla 65 karakterdir, boşluklar dahil (yaklaşık 9 kelime).
Alarm günü alarm_title en fazla 70 karakterdir, boşluklar dahil; gelişmenin adını ve son tarihini taşır, açıklamayı değil.
Her özet maddesi kimin ne yaptığını söyler.
Önceki 7 raporda anlatılmış bir gelişme manşete ya da özete ancak neyin yeni olduğunu ilk cümlesinde söyleyerek girer ('resmîleşti', 'sözleşmeye döndü', 'bedel açıklandı').
Her özet maddesi en fazla 115 karakterdir, boşluklar dahil (yaklaşık 16 kelime); ayrıntı gelişmenin kendi bloğunda kalır.
```

## Nereye (27 Eylül'de panelin gerçek metnine göre düzeltildi)

Paneldeki talimatta **"en fazla 14 kelime" kuralı yok** (yedek: `instructions-backup.md`); manşet için
yalnız frontmatter şablonunda `title: "günün özünü veren tek cümle"` var. Bu yüzden bloğu tek yere koy:

3. bölümde (**Kalite kuralları**), **"Teslimden önce kalite kontrolü."** paragrafının hemen **üstüne**,
yeni bir satırda şu başlıkla:

```
**Ek kurallar (Eylül 2026).**
```

ve altına yukarıdaki 7 cümleyi olduğu gibi yapıştır. Başka hiçbir satırı silme ya da değiştirme.

Not: kalite kontrolündeki "YÖNETİCİ ÖZETİ'nde 8 kelimeden uzun bir gelişme anlatımı var mı?" maddesi
yerinde kalır; yeni sınır (madde başına 115 karakter) onunla çelişmez, ona üst sınır ekler.

## Bir ön şart

6. cümle, ajanın önceki 7 raporu görebilmesini varsayar. Görev bunları okumuyorsa (ör.
`https://defintel.shadovi.com/data/reports.json` ve rapor sayfaları), cümle uygulanamaz; build'in
"ilk:" jetonu ve TEKRAR-MANŞET uyarısı yine de çalışır.

## Sonra nasıl anlarsın

Sonraki raporların günlük uyarı issue'sunda (`DEFINTEL uyarıları · <tarih>`): **KUR**, **H1-TEKRAR**
ve **İLK-EKRAN** satırlarının seyrekleşmesi. Ayrıntı: `rev-23-prompt.md`, `rev-32-prompt.md`, `k5-prompt.md`.
