"""Oyuncu eşleştiricisi (Rev 21): izlenen 64 oyuncunun alias'lı, sözcük sınırlı başlık eşleşmesi.

build.py'den taşındı (Rev 25) — collect_news.py'nin S4 kuralı ("Oyuncu Duyuruları": öznesi
izlenen bir oyuncu olan eylem) aynı eşleştiriciyi kullanır. Toplama yolu (ağsız sınama dahil)
markdown/pyyaml olmadan koşar; build.py'yi içe aktaramaz, bu modülü aktarır. Yalnızca stdlib.
build.py bu adları olduğu gibi yeniden dışa verir.
"""
import functools
import json
import pathlib
import re

RIVALS_JSON = pathlib.Path(__file__).resolve().parent / "data" / "rakipler.json"


def rivals_config():
    """İzlenen rakipler — dosya yoksa boş: bilinmiyor, sıfır değil."""
    try:
        data = json.loads(RIVALS_JSON.read_text(encoding="utf-8"))
    except Exception:
        return []
    return [r for r in data.get("rakipler", []) if r.get("name")]


def tr_fold(text):
    """Eşleştirme için Türkçe-duyarlı küçültme: İ/I/ı hepsi i'ye iner.

    str.lower() "NORINCO"yu "norinco" yaparken "NORİNCO"yu başka bir şeye
    çeviriyor; iki taraf da aynı fonksiyondan geçmezse marka adı eşleşmiyor.
    """
    return text.translate(str.maketrans("İIı", "iii")).lower()


SHORT_NAME = 4


def _word(pattern):
    return re.compile(r"(?<!\w)" + re.escape(pattern) + r"(?!\w)")


@functools.lru_cache(maxsize=None)
def rival_patterns(rid):
    """{"loose", "short", "tr_disi", "haric"} — bir oyuncunun eşleşme kalıpları.

    Dört karakter ve altındaki her dizi — kanonik ad ya da takma ad, ayrımı
    yok — yalnız başlıkta ve harf duyarlı aranır. "MIL", "FN", "STM", "TAI"
    gibi diziler Türkçe gövde metninde tesadüfen geçiyor ve sözcük sınırı
    bunu durdurmuyor; başlık kısa ve özenle yazılmış, tesadüf çok daha zor.

    `tr_disi` Türkçe metinde hiç aranmayan diziler: Türkçe başlıkta "BAE"
    Birleşik Arap Emirlikleri demek (Rev 21'de gerçek bir satır BAE
    Systems'e yazılıyordu). `haric` eşleşmeden önce metinden silinen
    kalıplar: "Rafael Grossi" bir UAEA başkanı, "POF-USA" bir tüfek üreticisi.
    """
    rival = next((r for r in rivals_config() if r["id"] == rid), None)
    if not rival:
        return {"loose": (), "short": (), "tr_disi": frozenset(), "haric": ()}
    strings = [rival["name"]] + [a for a in (rival.get("aliases") or []) if a.strip()]
    tr_disi = frozenset(rival.get("tr_disi") or ())
    return {
        "loose": tuple((n, _word(tr_fold(n))) for n in strings if len(n) > SHORT_NAME),
        "short": tuple((n, _word(n)) for n in strings if len(n) <= SHORT_NAME),
        "tr_disi": tr_disi,
        "haric": tuple(re.compile(h) for h in (rival.get("haric") or ())),
    }


def _haric(pats, text):
    for h in pats["haric"]:
        text = h.sub(" ", text)
    return text


def rival_in_title(rid, title, tr=False):
    """Başlıkta geçiyor mu? `tr`: metin Türkçe (çeviri, Türkçe kaynak, rapor)."""
    pats = rival_patterns(rid)
    title = _haric(pats, title)
    folded = tr_fold(title)
    skip = pats["tr_disi"] if tr else frozenset()
    return (any(p.search(folded) for n, p in pats["loose"] if n not in skip)
            or any(p.search(title) for n, p in pats["short"] if n not in skip))


def rival_in_body(rid, body, tr=True):
    """Gövdede yalnız uzun diziler aranır — kısa olanlar başlığa ait."""
    pats = rival_patterns(rid)
    folded = tr_fold(_haric(pats, body))
    skip = pats["tr_disi"] if tr else frozenset()
    return any(p.search(folded) for n, p in pats["loose"] if n not in skip)


def headline_has(rid, item):
    """Kupür satırı bu oyuncuyu anıyor mu — özgün başlık ve Türkçe çevirisi."""
    title, title_tr = item.get("title") or "", item.get("title_tr") or ""
    return bool((title and rival_in_title(rid, title, tr=item.get("lang") == "tr"))
                or (title_tr and rival_in_title(rid, title_tr, tr=True)))


def rival_start(rid, title, tr=False):
    """Başlıkta oyuncunun ilk geçtiği yerden önceki metin; geçmiyorsa None.

    Rev 25 S4 için: "öznesi oyuncu mu" sorusu, adın başlığın başında durup durmadığıdır.
    Eşleşme kuralı rival_in_title ile aynı (haric, tr_disi, kısa/uzun ayrımı).
    """
    pats = rival_patterns(rid)
    title = _haric(pats, title)
    folded = tr_fold(title)
    skip = pats["tr_disi"] if tr else frozenset()
    found = [(m.start(), folded) for n, p in pats["loose"] if n not in skip
             for m in [p.search(folded)] if m]
    found += [(m.start(), title) for n, p in pats["short"] if n not in skip
              for m in [p.search(title)] if m]
    if not found:
        return None
    start, text = min(found, key=lambda f: f[0])
    return text[:start]


def rival_surfaces(rid, text, tr=True, short=True):
    """[(konum, yapılandırmadaki dizi, metindeki yazım)] — eşleşen her dizinin ilk geçişi.

    K2: ray "brifingde geçen" der; ad metinde yazılı değilse (takma adla
    eşleştiyse: CSG ← "Excalibur Army") okuyucu kanıtı görebilsin diye
    metindeki yazım gerekiyor. Kural rival_in_title/rival_in_body ile aynı;
    `short` False ise kısa diziler aranmaz (gövde).
    """
    pats = rival_patterns(rid)
    text = _haric(pats, text)
    folded = tr_fold(text)
    same = len(folded) == len(text)
    skip = pats["tr_disi"] if tr else frozenset()
    found = []
    for n, p in pats["loose"]:
        m = None if n in skip else p.search(folded)
        if m:
            found.append((m.start(), n, text[m.start():m.end()] if same else n))
    if short:
        for n, p in pats["short"]:
            m = None if n in skip else p.search(text)
            if m:
                found.append((m.start(), n, m.group(0)))
    return sorted(found)
