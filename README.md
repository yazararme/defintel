# DEFINTEL

MKE stratejik pazar istihbaratı — günlük tarama arşivi.
Yayın: **https://defintel.shadovi.com** (GitHub Pages, `main` / kök dizin)

## Nasıl çalışıyor

```
zamanlanmış çalıştırma  →  source/YYYY-MM-DD.md  →  python3 build.py  →  git push
                                                                            ↓
                                                              GitHub Pages otomatik yayınlar
```

Tek kaynak `source/*.md`. Diğer her şey üretilir — elle düzenlenmez:

| Yol | Ne |
|---|---|
| `source/YYYY-MM-DD.md` | **Kaynak.** YAML frontmatter + Markdown gövde. Elle yazılan tek dosya. |
| `build.py` | Derleyici. `source/` → `reports/` + `index.html` + `data/reports.json` |
| `reports/YYYY-MM-DD.html` | Üretilir |
| `index.html` | Üretilir — arşiv listesi, arama, etiket filtresi |
| `data/reports.json` | Üretilir — makine okunur indeks (n8n / e-posta / başka tüketici için) |
| `assets/` | CSS + filtre JS |
| `CNAME` | Özel alan adı — **silme** |
| `.nojekyll` | Jekyll'i devre dışı bırakır — **silme** |

## Günlük çalıştırma

```bash
pip install markdown pyyaml --break-system-packages -q
git clone https://x-access-token:$GH_TOKEN@github.com/yazararme/defintel.git
cd defintel
# source/<bugünün tarihi>.md dosyasını yaz
python3 build.py
git add -A && git commit -m "rapor: YYYY-MM-DD" && git push
```

Yayına geçmesi ~1 dakika sürer.

## Frontmatter şeması

```yaml
---
date: 2026-09-14              # zorunlu, dosya adıyla aynı
title: "…"                    # zorunlu, tek cümle — günün özü
alarm: true                   # alarm var mı
alarm_title: "…"              # alarm varsa kısa başlık
decision_by: 2026-09-19        # bir karar tarihi varsa; yoksa alanı yaz
summary: "…"                  # arşiv listesinde görünen 1-2 cümle
tags: [C-UAS, ABD, TOLGA]     # filtre etiketleri
---
```

Gövde `## ⚠️ ALARM` ile başlarsa o bölüm otomatik olarak kırmızı uyarı kutusuna alınır.
Alarm yoksa ilk bölüm `## Yönetici özeti` olur ve `alarm: false` yazılır.

Bölüm sırası: Alarm → Yönetici özeti → Fırsatlar → Riskler → Rakip hareketleri →
İzleme listesi → Kaynaklar. Fırsat ve riskler tablo olarak yazılır.
Bir olgu yalnızca bir kez geçer; bölümler birbirini tekrar etmez.

## Notlar

- Sayfalar `noindex, nofollow` ile işaretli. Site yine de herkese açık —
  URL'yi bilen okuyabilir. Gerçek erişim kontrolü için Cloudflare Access gerekir.
- Erişim jetonu (fine-grained PAT, yalnızca bu repo, `contents: write`) süreli.
  Süresi dolduğunda zamanlanmış görevdeki değer yenilenmeli.
