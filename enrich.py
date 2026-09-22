"""Turn a rendered report into a cross-linked document.

The agent writes plain Markdown with three conventions:

    ### G1 · etiket                      a development, in GELİŞMELER
    - **G3 · Firma** — …                 a development, in RAKİP HAREKETLERİ
    - **G6 · etiket** — *durum.* …       a development, in İZLEME LİSTESİ
    - [K1] başlık — yayın, tarih — URL   a source

Everything here is derived from those: anchors (#g1, #k1), copy-link buttons,
citation links for G#, [K#], "bkz. EK" and "bkz. ALARMLAR", badges in the
opportunity/risk tables, a collapsed appendix and clickable source URLs.

Reports written before this convention simply have nothing to match, so every
step is a no-op and they keep rendering as they always did.
"""

import html
import json
import re
import urllib.parse as up

COPY = (
    '<button class="copylink" type="button" data-anchor="{aid}"'
    ' title="Bağlantıyı kopyala" aria-label="Bağlantıyı kopyala">#</button>'
)
URL = re.compile(r"https?://[^\s<>\"]+")
SKIP_TAGS = {"a", "code", "pre", "button", "h3"}


TR_SLUG = str.maketrans("çğıöşüÇĞİÖŞÜâîû", "cgiosucgiosuaiu")

# Şeritteki ad, başlığın kendisi değil kısası: "RAKİP HAREKETLERİ" bir çipte
# satırı yiyor. Listede olmayan bölüm başlığından türetilir.
SECTION_CHIP = {
    "alarmlar": "Alarmlar",
    "gelismeler": "Gelişmeler",
    "firsatlar": "Fırsatlar",
    "riskler": "Riskler",
    "rakip-hareketleri": "Rakipler",
    "izleme-listesi": "İzleme",
    "kaynaklar": "Kaynaklar",
    "ek": "EK",
}
# Özet zaten belgenin başında ve ilk okunan şey; kendine giden bir çip,
# okuyucuyu bulunduğu yere götüren bir düğmedir.
CHIP_SKIP = {"ozet"}


def section_id(heading_text):
    t = heading_text.upper()
    if t.startswith("EK"):
        return "ek"
    if "ALARM" in t:
        return "alarmlar"
    if "ÖZET" in t:
        return "ozet"
    slug = re.sub(r"[^a-z0-9]+", "-", heading_text.translate(TR_SLUG).lower()).strip("-")
    return slug or None


def add_heading_anchors(text):
    """### G1 · etiket  ->  <h3 id="g1"> + copy button, plus ids for EK/ALARMLAR."""

    def h3(m):
        gid = m.group(1).lower()
        # Numara yazımda kalır, çıktıda silinir: kimlik yalnızca id ve href'te
        # yaşar. Ekranda okunması gereken şey gelişmenin adı.
        return f'<h3 id="{gid}">{m.group(2).strip()}{COPY.format(aid=gid)}</h3>'

    text = re.sub(r"<h3>(G\d+)\s*·\s*([^<]*)</h3>", h3, text)

    def h2(m):
        sid = section_id(re.sub(r"<[^>]+>", "", m.group(1)))
        return f'<h2 id="{sid}">{m.group(1)}</h2>' if sid else m.group(0)

    return re.sub(r"<h2>(.*?)</h2>", h2, text, flags=re.S)


def add_item_anchors(text):
    """- **G3 · Firma** — …  ->  <li id="g3"> + copy button."""

    def li(m):
        gid = m.group(1).lower()
        return (
            # Rev 11: ne numara ne de ondan artakalan " · " basılır. Varış
            # teyidi artık gelişmenin adının kendisi — R6-P0-1 yürürlükten kalktı.
            f'<li id="{gid}"><strong class="ganchor">{m.group(2).strip()}</strong>'
            f"{COPY.format(aid=gid)}"
        )

    return re.sub(r"<li>\s*<strong>(G\d+)\s*·\s*([^<]*)</strong>", li, text)


def _build():
    """Geç içe aktarma: build zaten enrich'i alıyor, tepede olsa döngü olurdu."""
    import build
    return build


def build_flags():
    """(vekil açık mı, {alan adı: geçiyor mu}) — dosya yoksa boş sözlük."""
    b = _build()
    try:
        known = json.loads(b.TRANSLATE_HOSTS.read_text(encoding="utf-8"))
    except Exception:
        known = {}
    return b.TRANSLATE_PROXY, known


def build_proxy(url):
    return _build().proxy_url(url)


def add_source_anchors(text):
    """- [K1] …  ->  <li id="k1">, links live, background sources dimmed."""

    def li(m):
        kid = "k" + m.group(1)
        return f'<li id="{kid}" class="source">[K{m.group(1)}]'

    text = re.sub(r"<li>\s*\[K(\d+)\]", li, text)

    def link(m):
        url = m.group(0).rstrip(".,;")
        tail = m.group(0)[len(url):]
        return (
            f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">'
            f"{html.escape(url)}</a>{tail}"
        )

    text = URL.sub(link, text)
    # Çip linkifikasyondan SONRA ekleniyor: önce eklenseydi kendi translate.goog
    # adresi URL.sub tarafından ikinci kez linkifiye edilip bozulurdu.
    text = add_source_tr(text)
    return text.replace("(arka plan)", '<span class="background-tag">(arka plan)</span>')


def add_source_tr(text):
    """Kaynakça girdisinin sonuna "Türkçe oku" — atıf kanonik kalır, okuma yolu açılır.

    Kupürde birincil vekil / ikincil özgün; kaynakçada birincil özgün / ikincil
    vekil. Aynı şekil, ters öncelik — ters çevrilmiş olması "bu delildir, o
    okumadır" ayrımının kendisi.

    Kaynakçada varsayım kötümserdir, kupürdekinin tersine: orada yanlış
    iyimserin bedeli bir geri dokunuş, burada güven. Alan adı listesi yoksa
    ya da adres engelliyse çip değil jeton basılır.
    """
    if not build_flags()[0]:
        return text

    def chip(m):
        li, url = m.group(1), m.group(2)
        host = up.urlsplit(url).hostname or ""
        # Çip yalnızca geçtiği ÖLÇÜLMÜŞ alan adına basılır. Kupürde bilinmeyen
        # alan adı geçer sayılıyor; orada yanlış iyimserin bedeli bir geri
        # dokunuş, burada güven. Yoklayıcı kaynakçanın alan adlarını da tarıyor,
        # o yüzden bu katılık kimseyi haksız yere jetona düşürmüyor.
        if build_flags()[1].get(host) is not True:
            return f'{li}<span class="tr-blocked">çeviri engelli</span>'
        proxied = html.escape(build_proxy(url), quote=True)
        return (f'{li}<a class="tr-read" href="{proxied}" target="_blank" '
                f'rel="noopener">Türkçe oku ↗</a>')

    # Girdinin en sonu: "ne — kim — ne zaman — nerede", okuma yardımı kayıt tamamlanınca.
    return re.sub(
        r'(<li id="k\d+" class="source">(?![^<]*Erişilemeyen).*?<a href="([^"]+)"[^>]*>[^<]*</a>)(?=\s*</li>)',
        chip, text, flags=re.S,
    )


def tr_upper_first(text):
    """Cümlenin ilk harfini büyüt — Türkçe kurallarıyla.

    Python'un capitalize()/upper()'ı 'i'yi 'I' yapar; Türkçede 'İ' olmalı.
    Zaten büyükse ya da harf değilse (rakam, tırnak) metin olduğu gibi kalır.
    """
    if not text:
        return text
    first = text[0]
    if not first.isalpha() or first.isupper():
        return text
    return ("İ" if first == "i" else first.upper()) + text[1:]


def link_cut(gid, body):
    """Metni bağlantıya çevir ama içindeki başka bir atfın öncesinde kes.

    Atıf bağlantının içinde kalırsa link_citations onu atlar (bağ içinde bağ
    kurmaz) ve ekranda çıplak numara olarak durur.
    """
    cut = re.search(r"\s*\(?bkz\.|\s*\(?\bG\d+\b", body)
    head, tail = (body[: cut.start()], body[cut.start():]) if cut else (body, "")
    return f'<a class="xref" href="#{gid}">{head}</a>{tail}'


def add_summary_links(text, dev_ids):
    """YÖNETİCİ ÖZETİ maddesi: "G1 — cümle" -> cümlenin kendisi bağlantı olur.

    Buradaki G# bir atıf değil, maddenin kendi kimliğiydi. Etiketle değiştirmek
    "Ad — aynı şeyi söyleyen cümle" gibi bir tekrar üretiyordu; öneki tamamen
    düşürüp cümleyi bağlantı yapmak hem tekrarı kaldırıyor hem de gelişmeye
    giden yolu koruyor.
    """

    def item(m):
        gid = m.group(1).lower()
        body = m.group(2).strip()
        if gid not in dev_ids:
            return f"<li>{body}"
        return f"<li>{link_cut(gid, body)}"

    return re.sub(r"<li>\s*(G\d+)\s*—\s*([^<]*)", item, text)


def add_table_badges(text, dev_ids):
    """İlk hücredeki "G1 — " öneki düşer; hücrenin kendi metni bağlantı olur.

    Rozet, okunması gereken bir numara basıyordu. Hücrenin metni zaten
    gelişmeyi adıyla söylüyor — bağlantıyı ona vermek hem çıplak kimliği
    kaldırıyor hem de dokunma hedefini büyütüyor.
    """

    def cell(m):
        gid = m.group(2).lower()
        # Tire kalkınca ardındaki sözcük satır başına geçiyor; ajan onu
        # tireden sonra geldiği için küçük harfle yazmıştı.
        cell = tr_upper_first(m.group(3).strip())
        if gid not in dev_ids:
            return f"{m.group(1)}{cell}"
        # Hücre içinde başka bir gelişmeye atıf olabilir; bağlantı oraya kadar
        # kesilir. Yoksa atıf bağlantının içinde kalır, link_citations onu
        # atlar (bağ içinde bağ kurmaz) ve ekranda çıplak numara olarak durur.
        return f"{m.group(1)}{link_cut(gid, cell)}"

    return re.sub(r"(<td[^>]*>)\s*(G\d+)\s*—\s*([^<]*)", cell, text)


def link_citations(text, dev_ids, has_alarms=True, dev_labels=None):
    """Link G# and [K#] mentions in running text only.

    Walks the markup instead of blind-replacing so that ids inside headings,
    anchors, badges and code are left alone.
    """
    dev_labels = dev_labels or {}
    out = []
    depth = {t: 0 for t in SKIP_TAGS}
    skip_anchor_label = False

    for token in re.split(r"(<[^>]+>)", text):
        if token.startswith("<") and token.endswith(">"):
            name = re.match(r"</?\s*([a-zA-Z0-9]+)", token)
            tag = name.group(1).lower() if name else ""
            if tag in SKIP_TAGS:
                depth[tag] += -1 if token.startswith("</") else 1
            if 'class="ganchor"' in token:
                skip_anchor_label = True
            elif token == "</strong>" and skip_anchor_label:
                skip_anchor_label = False
            out.append(token)
            continue

        if not token.strip() or any(depth.values()) or skip_anchor_label:
            out.append(token)
            continue

        def g(m):
            gid = m.group(0).lower()
            # Hiçbir atıf yalnızca bir kimlikten ibaret olamaz: atıf işaret
            # ettiği şeyin adını taşır. "(G5)" okuyucunun çözemediği bir
            # jetondu; "(Ukrayna önleyici dron denemeleri)" kendini çözüyor
            # ve çoğu zaman takip etmek zorunda kalmadığın bir atıf oluyor.
            label = dev_labels.get(gid)
            if not label:
                return m.group(0)
            return f'<a class="xref" href="#{gid}">{html.escape(label)}</a>'

        token = re.sub(r"\bG\d+\b", g, token)
        token = re.sub(
            r"\[K(\d+)\]",
            lambda m: f'<a class="xref" href="#k{m.group(1)}">[K{m.group(1)}]</a>',
            token,
        )
        token = re.sub(
            r"(bkz\. EK|EK'te|EK'de|EK'e)",
            lambda m: f'<a class="xref" href="#ek">{m.group(1)}</a>',
            token,
        )
        # Alarm yoksa bölüm hiç yazılmıyor; o zaman çapa da yok. Var olmayan
        # bir yere giden bağlantı, bağlantı olmamasından kötüdür.
        if has_alarms:
            token = token.replace(
                "bkz. ALARMLAR", '<a class="xref" href="#alarmlar">bkz. ALARMLAR</a>'
            )
        out.append(token)

    return "".join(out)


def fold_watchlist(text):
    """İZLEME LİSTESİ: kımıldayan okuma yolunda, kımıldamayan katlamada.

    Bölümün iki işi var ve yalnızca biri günlük: "izlediğin bir iplik kımıldadı"
    günlüktür, "hâlâ açık olan her şey" referanstır — referans danışılır,
    ezbere okunmaz. 29 satırın 3'ü üründü; okuyucudan değişeni bulmak için
    hafızanın tamamını okuması isteniyordu.

    Katlamada "bekliyor" da yazılmaz: oradaki her kalem tanımı gereği bekliyor,
    durumu satır satır tekrarlamak normal bir hâli N kez duyurmak olur. Yapı
    durumu zaten kodluyor.
    """
    def section(m):
        head, body = m.group(1), m.group(2)
        items = re.findall(r"<li\b.*?</li>", body, re.S)
        if not items:
            return m.group(0)
        moved, waiting = [], []
        for li in items:
            plain = re.sub(r"<[^>]+>", " ", li)
            (waiting if re.search(r"\bbekliyor\b", plain, re.I) else moved).append(li)
        if not waiting:
            return m.group(0)

        rest = re.sub(r"<(?:p|ul|ol)\b.*?</(?:p|ul|ol)>", "", body, flags=re.S).strip()
        out = [head]
        if moved:
            out.append("<ul>" + "".join(moved) + "</ul>")
        out.append(
            f'<details class="watch"><summary>Bekleyen başlıklar '
            f'<span class="num">{len(waiting)}</span></summary><ul>'
            + "".join(strip_waiting(li) for li in waiting)
            + "</ul></details>"
        )
        return "".join(out) + rest

    return re.sub(r'(<h2[^>]*>İZLEME LİSTESİ</h2>)(.*?)(?=<h2|\Z)', section, text, flags=re.S)


def strip_waiting(li):
    """Katlanan satırdan yalnızca durum kelimesini at.

    Katlamadaki her kalem tanımı gereği bekliyor; durumu satır satır
    tekrarlamak normal bir hâli N kez duyurmaktır. Ama yalnızca o kelime:
    "hangi kalibreler anıldı" gibi cümleleri regexle silmeye kalkmak,
    ajanın yazdığı gerçek bilgiyi kör bir kuralla çöpe atmak olurdu.
    """
    return re.sub(r"\s*—\s*(?:<em>)?\s*bekliyor\.?\s*(?:</em>)?", " ", li, flags=re.I)


def fold_appendix(text):
    """EK: Katılımcı listeleri — collapsed, with the count taken from its first (n)."""
    m = re.search(r'<h2 id="ek">(.*?)</h2>', text, re.S)
    if not m:
        return text
    rest = text[m.end():]
    label = re.sub(r"<[^>]+>", "", m.group(1)).strip()
    count = re.search(r"\((\d+)\)", rest)
    summary = f"{label} ({count.group(1)})" if count and "(" not in label else label
    return (
        text[: m.start()]
        + f'<details class="appendix" id="ek"><summary>{html.escape(summary)}</summary>'
        + rest
        + "</details>"
    )


# The agent writes "MKE portföyü…" in the table headers. The site is MKE's but
# does not need to shout it on every row; renaming at render keeps the prompt
# untouched and is reversible.
HEADER_RENAMES = {
    "MKE portföyü için ne ifade ediyor": "Ürün portföyü için ne ifade ediyor",
    "MKE portföyüne etkisi": "Ürün portföyüne etkisi",
}


# "Alarm yok", "Alarm bulunmuyor", "**Alarm yok.**" — hepsi aynı boş kanal.
ALARM_EMPTY = re.compile(r"^\s*alarm\s+(?:yok|bulunmuyor)", re.I)


def drop_empty_alarms(text, alarm):
    """alarm: false ise boş ALARMLAR bloğunu kaldır — isteme değil, alana bakarak.

    Bunu prompta bırakmak kararı olasılıklı yapardı: ajan her sabah yeniden
    hatırlamak zorunda kalırdı. alarm alanı zaten makine okunur, karar da
    burada deterministik olarak veriliyor — HEADER_RENAMES'te olduğu gibi.

    Blok dolu görünüyorsa dokunulmuyor: ajan alarm alanını yanlış işaretlemişse
    doğru davranış metni sessizce silmek değil, göstermektir.
    """
    if alarm:
        return text

    dropped = [False]

    def cut(m):
        body = re.sub(r"<[^>]+>", " ", m.group(2)).strip()
        if not ALARM_EMPTY.match(body):
            return m.group(0)
        dropped[0] = True
        return ""

    text = re.sub(r'(<h2 id="alarmlar">.*?</h2>)(.*?)(?=<h2|\Z)', cut, text, flags=re.S)
    if dropped[0]:
        # Bölüm gidince "Yanıt süresi için bkz. ALARMLAR." hedefi olmayan bir
        # cümleye dönüşüyor. Bağlantısız bırakmak yetmez: okuyucuyu olmayan bir
        # yere yolluyor. Cümlenin tamamı kalkar — taşıdığı olgu zaten dokuz
        # gündür donmuş olan son tarihti.
        text = re.sub(r"\s*[^.<>]*\bbkz\.\s*ALARMLAR\s*\.?", "", text)
    return text


def drop_mke_agenda(text):
    """MKE GÜNDEMİ bölümünü gövdeden düşür — sayı artık rayda, build üretiyor.

    Ajanın ürettiği şey yargıdır; sayılabilen şeyi build sayar. Bu bölümün tek
    içeriği aday listesinden elle kopyalanan bir sayıydı: yanlış kopyalasa kimse
    çapraz kontrol etmezdi ve bağlantıyı da güvenilir üretemiyordu. İstem de
    sadeleşiyor, ama gövdeden düşmesi isteme bağlı kalmıyor.
    """
    return re.sub(r'<h2[^>]*>\s*MKE\s+GÜNDEM[İI].*?</h2>.*?(?=<h2|\Z)', "", text, flags=re.S)


def rename_headers(text):
    for old, new in HEADER_RENAMES.items():
        text = text.replace(f"<th>{old}</th>", f"<th>{new}</th>")
        text = text.replace(f'data-label="{old}"', f'data-label="{new}"')
    return text


def enrich(text, developments, alarm=False):
    dev_ids = {str(d.get("id", "")).lower() for d in developments if d.get("id")}
    # Düzyazı atfının tek doğruluk kaynağı: frontmatter'daki kısa ad.
    dev_labels = {
        str(d["id"]).lower(): str(d.get("label", "")).strip()
        for d in developments if d.get("id") and str(d.get("label", "")).strip()
    }
    text = add_heading_anchors(text)
    # Çapalar kurulduktan hemen sonra: silinen blokla birlikte ona giden
    # atıflar da kendiliğinden bağlantısız kalıyor (link_citations bunu
    # metinde id var mı diye okuyor).
    text = drop_empty_alarms(text, alarm)
    text = drop_mke_agenda(text)
    text = add_item_anchors(text)
    text = add_source_anchors(text)
    text = add_summary_links(text, dev_ids)
    text = add_table_badges(text, dev_ids)
    text = link_citations(text, dev_ids, 'id="alarmlar"' in text, dev_labels)
    return fold_appendix(fold_watchlist(rename_headers(text)))


def nav(body_html):
    """Başlığın altındaki şerit: belgenin bölümleri.

    Eskiden tek tek gelişmeleri listeliyordu; 14 çip bir şeride sığmayınca
    kaydırmalı bir raya ve "Rakipler +4" gibi açılır gruplara dönüşmüştü. O
    hâlde şerit belgenin haritası değil ikinci bir içindekiler listesiydi:
    okuyucu hangi gelişmenin nerede olduğunu bilmeden çipe basıyordu.

    Bölümler sabit, az ve okuyucunun zaten bildiği şeyler; ne kaydırma ne
    gruplama gerekiyor, sığmazsa alt satıra geçer.
    """
    ids = re.findall(r'<h2 id="([^"]+)"', body_html)
    chips = [
        f'<a class="chip" href="#{i}">'
        f'{html.escape(SECTION_CHIP.get(i, i.replace("-", " ").title()))}</a>'
        for i in ids if i not in CHIP_SKIP
    ]
    if len(chips) < 2:
        return ""
    return ('<nav class="devnav" id="devnav" aria-label="Bölümler">'
            + "".join(chips) + "</nav>")
