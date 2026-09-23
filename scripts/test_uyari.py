#!/usr/bin/env python3
"""OPERATÖR-YALNIZ testi (Rev 30): scripts/uyari.py sahte GitHub API'sine karşı.

    python3 scripts/test_uyari.py

Her senaryo gerçek iş akışı gibi ayrı süreçlerle koşar: `uyari.py ekle …` adımları, sonra
tek `uyari.py` boşaltması. Yerel bir HTTP sunucusu GitHub REST'i taklit eder ve her çağrıyı
kaydeder. Kırmızı koşullar:

  1. uyarılı çalıştırma → issue sayısı 1 değil, satır/atanan/etiket/başlık yanlış
  2. aynı gün tekrar (bir eski + bir yeni) → ikinci issue, tekrar satırı, yorum sayısı ≠ 1
  3. uyarısız çalıştırma → API çağrısı 0 değil
  9. `$`/`*`/`_` içeren metin → GitHub'a kaçışsız (LaTeX/italik) yazılıyor
  10. bugünün kaçışsız eski satırı, kaçışlı hâliyle yeniden yazılıyor
  + main dışı dal → API çağrısı 0 değil · kapalı issue yeniden açılmıyor · API hatası
    işi düşürüyor · okuyucu push'u (/notify) çağrılıyor · uyarı metni data/*.json'da

Yalnızca stdlib. Çıkış 1 = kırmızı. CI'da `$GITHUB_STEP_SUMMARY`'ye 🟢/🔴 satırı ekler.
"""
import json
import os
import pathlib
import re
import subprocess
import sys
import tempfile
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from urllib.parse import parse_qs, urlparse

ROOT = pathlib.Path(__file__).resolve().parents[1]
UYARI = ROOT / "scripts" / "uyari.py"
REPO = "defintel/test-repo"


class SahteGitHub:
    def __init__(self):
        self.issues, self.comments, self.labels, self.calls = [], [], set(), []
        self.tum_yollar = []   # hiç temizlenmez
        self.hata = False   # True: her çağrı 500 döner

    def handle(self, method, path, query, body):
        self.calls.append((method, path))
        self.tum_yollar.append(path)
        if self.hata:
            return 500, {"message": "sahte sunucu hatası"}
        base = f"/repos/{REPO}"
        if method == "GET" and path == f"{base}/issues":
            page = int(query.get("page", ["1"])[0])
            return 200, (list(reversed(self.issues)) if page == 1 else [])
        if method == "GET" and path.startswith(f"{base}/labels/"):
            name = path.rsplit("/", 1)[1]
            return (200, {"name": name}) if name in self.labels else (404, {"message": "Not Found"})
        if method == "POST" and path == f"{base}/labels":
            self.labels.add(body["name"])
            return 201, {"name": body["name"]}
        if method == "POST" and path == f"{base}/issues":
            n = len(self.issues) + 1
            it = {"number": n, "title": body["title"], "body": body.get("body", ""),
                  "state": "open", "html_url": f"https://github.com/{REPO}/issues/{n}",
                  "assignees": [{"login": a} for a in body.get("assignees", [])],
                  "labels": [{"name": l} for l in body.get("labels", [])],
                  "user": {"login": "github-actions[bot]"}}
            self.issues.append(it)
            return 201, it
        m = re.fullmatch(rf"{base}/issues/(\d+)(/comments)?", path)
        if m:
            it = self.issues[int(m[1]) - 1]
            if method == "PATCH" and not m[2]:
                it.update({k: v for k, v in body.items() if k in ("body", "state", "title")})
                return 200, it
            if method == "POST" and m[2]:
                self.comments.append((it["number"], body["body"]))
                return 201, {"id": len(self.comments), "body": body["body"]}
        return 404, {"message": f"sahte: {method} {path} tanımsız"}


def sunucu_baslat(gh):
    class H(BaseHTTPRequestHandler):
        def _do(self):
            u = urlparse(self.path)
            n = int(self.headers.get("Content-Length") or 0)
            body = json.loads(self.rfile.read(n)) if n else None
            code, out = gh.handle(self.command, u.path, parse_qs(u.query), body)
            raw = json.dumps(out).encode()
            self.send_response(code)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(raw)))
            self.end_headers()
            self.wfile.write(raw)

        do_GET = do_POST = do_PATCH = _do

        def log_message(self, *a):
            pass

    srv = ThreadingHTTPServer(("127.0.0.1", 0), H)
    threading.Thread(target=srv.serve_forever, daemon=True).start()
    return srv


def calistir(env, uyarilar):
    """Bir iş (job): her uyarı ayrı adım, sonra tek boşaltma. Döner: (boşaltma çıktısı, özet, çıkış)."""
    with tempfile.TemporaryDirectory() as tmp:
        e = dict(env, RUNNER_TEMP=tmp, GITHUB_STEP_SUMMARY=str(pathlib.Path(tmp) / "summary.md"))
        for kural, metin in uyarilar:
            subprocess.run([sys.executable, str(UYARI), "ekle", kural, metin], env=e,
                           check=True, capture_output=True, text=True)
        p = subprocess.run([sys.executable, str(UYARI)], env=e, capture_output=True, text=True)
        ozet = pathlib.Path(e["GITHUB_STEP_SUMMARY"]).read_text(encoding="utf-8")
        kalan = (pathlib.Path(tmp) / "defintel-uyari.jsonl").exists()
        return p.stdout + p.stderr, ozet, p.returncode, kalan


def main():
    gh = SahteGitHub()
    srv = sunucu_baslat(gh)
    env = {k: v for k, v in os.environ.items()
           if not k.startswith(("GITHUB_", "RUNNER_", "UYARI_"))}
    env.update({
        "GITHUB_API_URL": f"http://127.0.0.1:{srv.server_port}",
        "GITHUB_SERVER_URL": "https://github.com", "GITHUB_REPOSITORY": REPO,
        "GITHUB_TOKEN": "sahte-token", "GITHUB_REF": "refs/heads/main",
        "GITHUB_WORKFLOW": "build", "GITHUB_ACTIONS": "true", "PYTHONIOENCODING": "utf-8",
    })
    sonuc = []

    def kontrol(ad, kosul, ayrinti=""):
        sonuc.append(bool(kosul))
        print(f"{'ok  ' if kosul else 'FAIL'} {ad}" + (f"  ({ayrinti})" if ayrinti and not kosul else ""))

    def satirlar(it):
        return [l for l in it["body"].splitlines() if l.startswith("- **")]

    KUR = ("KUR", "sınama: 23 Eylül kur satırı eksik")
    H1 = ("H1-TEKRAR", "sınama: başlık iki kez h1")
    MANSET = ("TEKRAR-MANŞET", "sınama: manşet dünküyle aynı")

    # 1 — uyarılı çalıştırma: günün issue'su açılır
    out, ozet, rc, kalan = calistir(dict(env, GITHUB_RUN_ID="101"), [KUR, H1])
    kontrol("1 · çıkış 0", rc == 0, out)
    kontrol("1 · issue sayısı 1", len(gh.issues) == 1, len(gh.issues))
    it = gh.issues[0] if gh.issues else {"body": "", "title": "", "assignees": [], "labels": []}
    kontrol("1 · başlık 'DEFINTEL uyarıları · YYYY-MM-DD'",
            re.fullmatch(r"DEFINTEL uyarıları · \d{4}-\d{2}-\d{2}", it["title"]), it["title"])
    kontrol("1 · atanan yazararme", [a["login"] for a in it["assignees"]] == ["yazararme"])
    kontrol("1 · etiket uyari (oluşturuldu)", "uyari" in gh.labels and
            [l["name"] for l in it["labels"]] == ["uyari"])
    kontrol("1 · iki satır, kural adıyla başlıyor, çalıştırma bağlantılı", satirlar(it) == [
        "- **KUR** · sınama: 23 Eylül kur satırı eksik · "
        f"[çalıştırma](https://github.com/{REPO}/actions/runs/101)",
        "- **H1-TEKRAR** · sınama: başlık iki kez h1 · "
        f"[çalıştırma](https://github.com/{REPO}/actions/runs/101)"], it["body"])
    kontrol("1 · yorum yok (ilk açılış)", gh.comments == [])
    kontrol("1 · (A) OPERATÖR-YALNIZ yeşil", "🟢 OPERATÖR-YALNIZ: [issue #1]" in ozet
            and "+2 satır · okuyucu push 0" in ozet, ozet)
    kontrol("1 · RUNNER_TEMP dosyası boşaltmadan sonra silindi", not kalan)

    # 2 — aynı gün tekrar: bir eski + bir yeni
    gh.calls.clear()
    out, ozet, rc, _ = calistir(dict(env, GITHUB_RUN_ID="102", GITHUB_WORKFLOW="pull-drive"),
                                [KUR, MANSET, MANSET])
    kontrol("2 · çıkış 0", rc == 0, out)
    kontrol("2 · issue sayısı hâlâ 1", len(gh.issues) == 1, len(gh.issues))
    s = satirlar(gh.issues[0])
    issue_2, tekrar_2 = len(gh.issues), len(s) - len(set(l.split(" · [")[0] for l in s))
    kontrol("2 · +1 satır (toplam 3)", len(s) == 3, s)
    kontrol("2 · tekrar satırı 0 (KUR bir kez)", sum(l.startswith("- **KUR** ·") for l in s) == 1, s)
    kontrol("2 · yeni satır bu çalıştırmanın bağlantısıyla",
            s[-1].startswith("- **TEKRAR-MANŞET** · ") and s[-1].endswith("/runs/102)"), s[-1:])
    kontrol("2 · tek yorum '+1 uyarı · pull-drive'", gh.comments == [(1, "+1 uyarı · pull-drive")],
            gh.comments)
    kontrol("2 · (A) +1 satır", "[issue #1]" in ozet and "+1 satır · okuyucu push 0" in ozet, ozet)

    # 2b — aynı uyarılar yine: satır da yorum da yok
    out, ozet, rc, _ = calistir(dict(env, GITHUB_RUN_ID="103"), [KUR, MANSET])
    kontrol("2b · hepsi tekrar → satır 0, yorum 0", len(satirlar(gh.issues[0])) == 3
            and len(gh.comments) == 1 and "+0 satır" in ozet, ozet)

    # 3 — uyarısız çalıştırma: API'ye hiç dokunulmaz
    gh.calls.clear()
    out, ozet, rc, _ = calistir(dict(env, GITHUB_RUN_ID="104"), [])
    kontrol("3 · çıkış 0", rc == 0, out)
    api_3 = len(gh.calls)
    kontrol("3 · API çağrısı 0", api_3 == 0, gh.calls)
    kontrol("3 · (A) 'uyarı yok' + OPERATÖR-YALNIZ yeşil", "uyarı yok" in ozet and
            "🟢 OPERATÖR-YALNIZ: issue — · +0 satır · okuyucu push 0" in ozet, ozet)

    # 4 — main dışı dal, önek yok: issue yok, API çağrısı yok
    gh.calls.clear()
    out, ozet, rc, _ = calistir(dict(env, GITHUB_REF="refs/heads/rev21-33"), [KUR])
    kontrol("4 · dal: API çağrısı 0, (A)'da uyarı listeli", gh.calls == [] and "**KUR**" in ozet,
            gh.calls)

    # 5 — sınama öneki: ayrı başlık, dalda da açılır
    out, ozet, rc, _ = calistir(dict(env, GITHUB_REF="refs/heads/rev21-33",
                                     UYARI_TEST_ONEK="[TEST] "), [KUR])
    kontrol("5 · [TEST] önekli ayrı issue", len(gh.issues) == 2 and
            gh.issues[1]["title"].startswith("[TEST] DEFINTEL uyarıları · "),
            [i["title"] for i in gh.issues])

    # 6 — kapalı issue yeni satırla yeniden açılır
    gh.issues[0]["state"] = "closed"
    out, ozet, rc, _ = calistir(dict(env, GITHUB_RUN_ID="106"), [("SLUG", "sınama: slug çakıştı")])
    kontrol("6 · kapalı issue yeniden açıldı, yeni issue yok",
            gh.issues[0]["state"] == "open" and len(gh.issues) == 2)

    # 7 — API hatası işi düşürmez, (A)'da kırmızı
    gh.hata = True
    out, ozet, rc, _ = calistir(dict(env, GITHUB_RUN_ID="107"), [("SLUG", "sınama: başka")])
    gh.hata = False
    kontrol("7 · API 500 → çıkış 0, (A) kırmızı", rc == 0 and "🔴 OPERATÖR-YALNIZ" in ozet, ozet)

    # 8 — bilinmeyen kural adı yerelde patlar
    p = subprocess.run([sys.executable, str(UYARI), "ekle", "UYDURMA", "x"],
                       env=env, capture_output=True, text=True)
    kontrol("8 · bilinmeyen kural reddedildi", p.returncode != 0 and "bilinmeyen kural" in p.stderr)

    # 9 — Markdown kaçışı: iki `$` LaTeX'e dönmez, `*`/`_` italik yapmaz; (A) de kaçışlı
    DOLAR = ("KUR", "sınama: 1,5 milyar $ ↔ 20 $'i")
    YILDIZ = ("SLUG", "sınama: a*b*c_d_e `kod` <b> [x]|~#")
    n_yorum = len(gh.comments)
    out, ozet, rc, _ = calistir(dict(env, GITHUB_RUN_ID="109"), [DOLAR, YILDIZ])
    s = satirlar(gh.issues[0])
    kontrol("9 · iki `$` → <span>$</span> (GitHub belgesi, matematik dışı)",
            "- **KUR** · sınama: 1,5 milyar <span>$</span> ↔ 20 <span>$</span>'i · "
            f"[çalıştırma](https://github.com/{REPO}/actions/runs/109)" in s, s[-2:])
    kontrol("9 · `*` `_` ` < [ | ~ # ters eğik çizgiyle kaçışlı",
            "- **SLUG** · sınama: a\\*b\\*c\\_d\\_e \\`kod\\` \\<b\\> \\[x\\]\\|\\~\\# · "
            f"[çalıştırma](https://github.com/{REPO}/actions/runs/109)" in s, s[-2:])
    kontrol("9 · (A) özeti de kaçışlı", "<span>$</span>" in ozet and "a\\*b\\*c" in ozet
            and "milyar $ ↔" not in ozet, ozet)
    out, ozet, rc, _ = calistir(dict(env, GITHUB_RUN_ID="110"), [DOLAR, YILDIZ])
    kontrol("9 · kaçışlı satırlar tekrar yazılmaz", "+0 satır" in ozet
            and len(satirlar(gh.issues[0])) == len(s) and len(gh.comments) == n_yorum + 1, ozet)

    # 10 — bugünün issue'sunda eski (kaçışsız) satır: kaçışlı hâli tekrar sayılır
    ESKI = ("TİP-BELİRTECİ", "sınama: eski *düz* 3 $ ile 5 $ satırı")
    gh.issues[0]["body"] += (f"- **{ESKI[0]}** · {ESKI[1]} · "
                             f"[çalıştırma](https://github.com/{REPO}/actions/runs/99)\n")
    once = len(satirlar(gh.issues[0]))
    out, ozet, rc, _ = calistir(dict(env, GITHUB_RUN_ID="111"), [ESKI])
    kontrol("10 · eski kaçışsız satır → +0 satır, yorum yok", "+0 satır" in ozet
            and len(satirlar(gh.issues[0])) == once and len(gh.comments) == n_yorum + 1, ozet)

    # OPERATÖR-YALNIZ — okuyucu kanalı
    push = sum("notify" in p for p in gh.tum_yollar)
    kontrol("OY · okuyucu push (/notify) çağrısı 0", push == 0, gh.tum_yollar)
    sizan = [f.name for f in (ROOT / "data").glob("*.json")
             if "sınama:" in f.read_text(encoding="utf-8", errors="replace")]
    kontrol("OY · uyarı metni data/*.json'da yok", not sizan, sizan)
    kontrol("OY · uyari.py depo ağacına yazmıyor (yalnız RUNNER_TEMP)",
            "RUNNER_TEMP" in UYARI.read_text(encoding="utf-8")
            and "ROOT" not in UYARI.read_text(encoding="utf-8"))

    srv.shutdown()
    yesil = all(sonuc)
    satir = (f"{'🟢' if yesil else '🔴'} OPERATÖR-YALNIZ testi: {sum(sonuc)}/{len(sonuc)} kontrol · "
             f"issue {issue_2} · tekrar satırı {tekrar_2} · uyarısız çalıştırmada API {api_3} · "
             f"okuyucu push {push}")
    print("\n" + satir)
    if os.environ.get("GITHUB_STEP_SUMMARY"):
        with open(os.environ["GITHUB_STEP_SUMMARY"], "a", encoding="utf-8") as fh:
            fh.write(f"### uyari.py testi (sahte GitHub API)\n\n{satir}\n\n")
    return 0 if yesil else 1


if __name__ == "__main__":
    sys.exit(main())
