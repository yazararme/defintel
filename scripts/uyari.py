#!/usr/bin/env python3
"""Operatör uyarı kanalı (Rev 30): günün tek GitHub issue'su.

Bir build kuralı uyarı verince:

    from scripts import uyari      # build.py
    import uyari                   # scripts/*.py
    uyari.ekle("KUR", "…")

Uyarılar aynı iş (job) içindeki adımlar boyunca `$RUNNER_TEMP/defintel-uyari.jsonl`
dosyasında birikir (depo ağacının dışında; yerelde yalnızca bellekte). İşin son adımı
tek boşaltmadır:

    python3 scripts/uyari.py                 # boşalt: issue aç / güncelle, (A) özeti yaz
    python3 scripts/uyari.py ekle KURAL METİN   # kabuk adımından uyarı ekle

Boşaltma yalnızca `GITHUB_REF == refs/heads/main` iken ya da `UYARI_TEST_ONEK` verilmişse
(başlık o önekle başlar) GitHub'a yazar. Başlık `DEFINTEL uyarıları · YYYY-MM-DD`
(Türkiye günü), gövde satırı `- **KURAL** · metin · [çalıştırma](<run URL>)`. Aynı gün aynı
kural + metin tekrar yazılmaz; yeni satır eklenince tek kısa yorum düşülür, kapalı issue
yeniden açılır. Uyarı yoksa hiçbir API çağrısı yapılmaz.

OPERATÖR-YALNIZ: uyarı metni yalnızca issue'ya, iş kaydına ve (A) özetine gider — sitenin
hiçbir dosyasına yazılmaz, okuyucu push'u (/notify) çağrılmaz. Boşaltma işi asla
düşürmez (çıkış kodu hep 0); API hatası kayda ve (A)'ya kırmızı satır olarak düşer.

Yalnızca stdlib.
"""
import datetime
import json
import os
import pathlib
import re
import sys
import urllib.error
import urllib.parse
import urllib.request

KURALLAR = (
    "KAPSAM-SAYI", "DÖRT-DURUM", "ETİKET-BAŞLIK", "KUR", "H1-TEKRAR", "İLK-EKRAN",
    "SİLME-YOK", "İPUCU-YOK", "ÇEVİRİ-DEDEKTÖRÜ", "İPLİK-DURUM", "SLUG", "KANIT-BOŞLUĞU",
    "L1-DOLGU", "ÇİZGİ-KONTRAST", "TİP-BELİRTECİ", "GEÇ-GELEN", "TEKRAR-MANŞET", "NOKTALI-İ",
)
BLOKLAYICI = ("DÖRT-DURUM", "SİLME-YOK")   # iş kırmızı biter ama uyarı yine buraya yazılır

ATANAN = "yazararme"
ETIKET = "uyari"
DOSYA_ADI = "defintel-uyari.jsonl"
SATIR_RE = re.compile(r"^- \*\*(?P<kural>.+?)\*\* · (?P<metin>.*) · \[çalıştırma\]\([^)]*\)\s*$")

_BELLEK = []   # yerelde (RUNNER_TEMP yok) uyarılar burada kalır


# ── toplama ──────────────────────────────────────────────────────────────────

def _dosya():
    rt = os.environ.get("RUNNER_TEMP")
    return pathlib.Path(rt) / DOSYA_ADI if rt else None


def _tek_satir(metin):
    return re.sub(r"\s+", " ", str(metin)).strip()


def ekle(kural, metin):
    """Bir uyarı kaydet. Kural adı sabit listeden olmalı (yazım hatası yerelde patlar)."""
    if kural not in KURALLAR:
        raise ValueError(f"uyari.ekle: bilinmeyen kural {kural!r} (KURALLAR'a bak)")
    metin = _tek_satir(metin)
    print(f"  ! {kural} · {metin}")
    if os.environ.get("GITHUB_ACTIONS") == "true":
        print(f"::warning title={kural}::{metin}")
    kayit = {"kural": kural, "metin": metin}
    f = _dosya()
    if f is None:
        _BELLEK.append(kayit)
        return
    with f.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def topla():
    """Bu işte birikmiş uyarılar, sırası korunmuş ve tekilleştirilmiş."""
    kayitlar = list(_BELLEK)
    f = _dosya()
    if f and f.exists():
        for line in f.read_text(encoding="utf-8").splitlines():
            if line.strip():
                try:
                    kayitlar.append(json.loads(line))
                except ValueError:
                    print(f"::error::uyari: bozuk satır atlandı: {line[:120]}")
    gorulen, sonuc = set(), []
    for k in kayitlar:
        anahtar = (k.get("kural", ""), k.get("metin", ""))
        if anahtar not in gorulen:
            gorulen.add(anahtar)
            sonuc.append(anahtar)
    return sonuc


# ── GitHub REST ──────────────────────────────────────────────────────────────

class ApiHatasi(Exception):
    pass


class _Api:
    def __init__(self, token, repo, base):
        self.token, self.repo, self.base = token, repo, base.rstrip("/")
        self.cagri = 0

    def __call__(self, method, path, body=None, query=None):
        url = f"{self.base}{path}"
        if query:
            url += "?" + urllib.parse.urlencode(query)
        data = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(url, data=data, method=method, headers={
            "Authorization": f"Bearer {self.token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28",
            "Content-Type": "application/json",
            "User-Agent": "defintel-uyari",
        })
        self.cagri += 1
        try:
            with urllib.request.urlopen(req, timeout=20) as r:
                raw = r.read()
                return r.status, (json.loads(raw) if raw else None)
        except urllib.error.HTTPError as e:
            raw = e.read()[:500].decode("utf-8", "replace")
            return e.code, raw
        except (urllib.error.URLError, OSError) as e:
            raise ApiHatasi(f"{method} {path}: {e}") from e


def _beklenen(durum, beklenen, ne, yanit):
    if durum not in beklenen:
        raise ApiHatasi(f"{ne}: HTTP {durum} {str(yanit)[:200]}")


def turkiye_gunu():
    try:
        from zoneinfo import ZoneInfo
        tz = ZoneInfo("Europe/Istanbul")
    except Exception:   # tzdata yoksa: Türkiye 2016'dan beri sabit UTC+3
        tz = datetime.timezone(datetime.timedelta(hours=3))
    return datetime.datetime.now(tz).date().isoformat()


def satir(kural, metin, run_url):
    return f"- **{kural}** · {metin} · [çalıştırma]({run_url})"


def mevcut_anahtarlar(govde):
    anahtarlar = set()
    for line in (govde or "").splitlines():
        m = SATIR_RE.match(line.strip())
        if m:
            anahtarlar.add((m["kural"], m["metin"]))
    return anahtarlar


def _issue_bul(api, baslik):
    """Başlığı tam eşleşen issue (açık ya da kapalı). Arama API'si gecikmeli
    indekslediği için kullanılmaz: son 2 günde güncellenen issue'lar taranır."""
    since = (datetime.datetime.now(datetime.timezone.utc) - datetime.timedelta(days=2))
    for sayfa in range(1, 6):
        durum, liste = api("GET", f"/repos/{api.repo}/issues", query={
            "state": "all", "since": since.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "per_page": 100, "page": sayfa})
        _beklenen(durum, (200,), "issue listesi", liste)
        for it in liste:
            if it.get("title") == baslik and "pull_request" not in it:
                return it
        if len(liste) < 100:
            return None
    return None


def _etiket_hazirla(api):
    """`uyari` etiketi yoksa oluştur. Olmazsa False — issue etiketsiz açılır."""
    try:
        durum, _ = api("GET", f"/repos/{api.repo}/labels/{ETIKET}")
        if durum == 200:
            return True
        durum, yanit = api("POST", f"/repos/{api.repo}/labels", {
            "name": ETIKET, "color": "b60205",
            "description": "DEFINTEL operatör uyarıları (günde tek issue)"})
        if durum in (201, 422):   # 422: bu arada başkası oluşturdu
            return True
        print(f"::warning::uyari: etiket oluşturulamadı: HTTP {durum} {str(yanit)[:200]}")
    except ApiHatasi as e:
        print(f"::warning::uyari: etiket oluşturulamadı: {e}")
    return False


def gonder(uyarilar, env):
    """Issue'yu aç ya da güncelle. Döner: (issue numarası, url, eklenen satır, API çağrısı)."""
    repo = env["GITHUB_REPOSITORY"]
    api = _Api(env.get("GITHUB_TOKEN", ""), repo, env.get("GITHUB_API_URL") or "https://api.github.com")
    server = env.get("GITHUB_SERVER_URL") or "https://github.com"
    run_url = f"{server}/{repo}/actions/runs/{env.get('GITHUB_RUN_ID', '')}"
    baslik = env.get("UYARI_TEST_ONEK", "") + f"DEFINTEL uyarıları · {turkiye_gunu()}"
    issue = _issue_bul(api, baslik)
    if issue is None:
        yeni = [satir(k, m, run_url) for k, m in uyarilar]
        govde = {"title": baslik, "body": "\n".join(yeni) + "\n", "assignees": [ATANAN]}
        if _etiket_hazirla(api):
            govde["labels"] = [ETIKET]
        durum, yanit = api("POST", f"/repos/{repo}/issues", govde)
        for alan in ("labels", "assignees"):   # 422: önce etiketsiz, sonra atamasız dene
            if durum == 422 and alan in govde:
                print(f"::warning::uyari: issue '{alan}' ile açılamadı: {str(yanit)[:200]}")
                govde.pop(alan)
                durum, yanit = api("POST", f"/repos/{repo}/issues", govde)
        _beklenen(durum, (201,), "issue açma", yanit)
        if not any(a.get("login") == ATANAN for a in yanit.get("assignees") or []):
            print(f"::warning::uyari: issue #{yanit['number']} {ATANAN} hesabına atanamadı")
        return yanit["number"], yanit.get("html_url", ""), len(yeni), api.cagri

    var = mevcut_anahtarlar(issue.get("body"))
    yeni = [satir(k, m, run_url) for k, m in uyarilar if (k, m) not in var]
    if not yeni:
        return issue["number"], issue.get("html_url", ""), 0, api.cagri
    guncel = {"body": (issue.get("body") or "").rstrip("\n") + "\n" + "\n".join(yeni) + "\n"}
    if issue.get("state") == "closed":
        guncel["state"] = "open"
    durum, yanit = api("PATCH", f"/repos/{repo}/issues/{issue['number']}", guncel)
    _beklenen(durum, (200,), "issue güncelleme", yanit)
    is_akisi = env.get("GITHUB_WORKFLOW") or "iş akışı"
    durum, yanit = api("POST", f"/repos/{repo}/issues/{issue['number']}/comments",
                       {"body": f"+{len(yeni)} uyarı · {is_akisi}"})
    _beklenen(durum, (201,), "yorum", yanit)
    return issue["number"], issue.get("html_url", ""), len(yeni), api.cagri


# ── boşaltma ─────────────────────────────────────────────────────────────────

def _ozet_yaz(satirlar, env):
    yol = env.get("GITHUB_STEP_SUMMARY")
    metin = "\n".join(satirlar) + "\n"
    print(metin)
    if yol:
        try:
            with open(yol, "a", encoding="utf-8") as fh:
                fh.write(metin)
        except OSError as e:
            print(f"::error::uyari: özet yazılamadı: {e}")


def bosalt(env=None):
    """Tek boşaltma. Hiçbir durumda istisna fırlatmaz; özet satırlarını döndürür."""
    env = dict(os.environ if env is None else env)
    ozet = ["### Operatör uyarıları", ""]
    try:
        uyarilar = topla()
    except Exception as e:   # noqa: BLE001 — boşaltma işi düşürmez
        uyarilar = []
        ozet.append(f"🔴 uyarılar okunamadı: {e}")
    push = 0   # bu modülün okuyucu push'una (/notify) giden hiçbir yolu yok

    if not uyarilar:
        ozet += ["uyarı yok", "",
                 f"🟢 OPERATÖR-YALNIZ: issue — · +0 satır · okuyucu push {push}"]
        _ozet_yaz(ozet, env)
        _temizle()
        return ozet

    ozet += [f"- **{k}** · {m}" for k, m in uyarilar] + [""]
    onek = env.get("UYARI_TEST_ONEK", "")
    ref = env.get("GITHUB_REF", "")
    if ref != "refs/heads/main" and not onek:
        ozet.append(f"🟢 OPERATÖR-YALNIZ: issue — (dal `{ref or 'yerel'}`, yalnızca main issue açar)"
                    f" · +0 satır · okuyucu push {push}")
    elif not env.get("GITHUB_TOKEN") or not env.get("GITHUB_REPOSITORY"):
        ozet.append("🔴 OPERATÖR-YALNIZ: GITHUB_TOKEN / GITHUB_REPOSITORY yok, issue yazılamadı"
                    f" · +0 satır · okuyucu push {push}")
    else:
        try:
            no, url, eklenen, _ = gonder(uyarilar, env)
            bag = f"[issue #{no}]({url})" if url else f"issue #{no}"
            ozet.append(f"🟢 OPERATÖR-YALNIZ: {bag} · +{eklenen} satır · okuyucu push {push}")
        except Exception as e:   # noqa: BLE001 — API hatası işi düşürmez
            print(f"::error::uyari: issue yazılamadı: {e}")
            ozet.append(f"🔴 OPERATÖR-YALNIZ: issue yazılamadı ({_tek_satir(e)[:200]})"
                        f" · +0 satır · okuyucu push {push}")
    _ozet_yaz(ozet, env)
    _temizle()
    return ozet


def _temizle():
    _BELLEK.clear()
    f = _dosya()
    if f:
        try:
            f.unlink(missing_ok=True)
        except OSError:
            pass


def main(argv):
    if len(argv) >= 1 and argv[0] == "ekle":
        if len(argv) != 3:
            print("kullanım: python3 scripts/uyari.py ekle KURAL METİN")
            return 2
        ekle(argv[1], argv[2])
        return 0
    try:
        bosalt()
    except Exception as e:   # noqa: BLE001 — son savunma: iş asla düşmez
        print(f"::error::uyari: {e}")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
