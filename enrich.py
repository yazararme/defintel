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

import datetime as dt
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
    "portfoy": "Portföy",
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


def add_source_anchors(text, report_iso=""):
    """- [K1] …  ->  <li id="k1">, adres iki çipe dönüşür, arka plan soluklaşır."""

    def li(m):
        kid = "k" + m.group(1)
        return f'<li id="{kid}" class="source">[K{m.group(1)}]'

    text = re.sub(r"<li>\s*\[K(\d+)\]", li, text)

    # Önce linkifikasyon, sonra çipler: ters sırada çipin kendi href'i bir kez
    # daha linkifiye edilip <a href="<a href=...">'e dönüşüyor.
    def link(m):
        url = m.group(0).rstrip(".,;")
        tail = m.group(0)[len(url):]
        return (
            f'<a href="{html.escape(url, quote=True)}" target="_blank" rel="noopener">'
            f"{html.escape(url)}</a>{tail}"
        )

    text = URL.sub(link, text)
    text = source_links(text, report_iso)
    # "(arka plan)" rol iddiası taşıyordu ("bu bulgu değil bağlam") ama yaş
    # kuralıyla uygulanıyordu; ölçüm ikisinin de yapılmadığını gösterdi. Yaş
    # artık türetiliyor, geriye hiç yapılmamış bir iş kalıyor.
    return text.replace(" (arka plan)", "").replace("(arka plan)", "")


UNPARSED_DATES = []


def age_token(src_date, report_iso):
    """'bugün' / 'dün' / '{n} gün önce' — kayıt değil ölçü.

    Tarih kaydın kendisi ve kalıyor; ama okuyucu hiçbir zaman "bu hangi
    tarihte yayımlandı" diye sormuyor, "bu delil güncel mi" diye soruyor —
    ve tarih o soruya ancak raporun kendi tarihinden çıkarma yaptıktan sonra
    cevap veriyor. İki iş varsa tek şeye ikisini birden yaptırmıyoruz.

    Eşik yok: "3 gün önce" ile "108 gün önce" ikisi de sıfır çabayla okunuyor,
    üstüne kategorik bir kelime koymak gereksiz.
    """
    try:
        report = dt.date.fromisoformat(report_iso)
    except (TypeError, ValueError):
        return ""
    days = (report - src_date).days
    if days < 0:
        return ""          # gelecek tarihli kaynak: sayı uydurmaktansa sus
    if days == 0:
        return "bugün"
    if days == 1:
        return "dün"
    return f"{days} gün önce"


def source_age(entry_text, report_iso):
    """Girdideki DD.MM.YYYY'yi bul. Ayrıştırılamıyorsa hiçbir şey basılmaz."""
    m = re.search(r"\b(\d{2})\.(\d{2})\.(\d{4})\b", entry_text)
    if not m:
        UNPARSED_DATES.append(entry_text[:60])
        return ""
    try:
        src = dt.date(int(m.group(3)), int(m.group(2)), int(m.group(1)))
    except ValueError:
        UNPARSED_DATES.append(entry_text[:60])
        return ""
    return age_token(src, report_iso)


def drop_self_links(text):
    """Kaynak girdisinin başındaki [K1] kendine bağlantı olmasın.

    Metin içindeki [K1] atfı okuyucuyu kaynağa götürür ve işe yarar; ama
    kaynağın kendi satırındaki [K1], okuyucuyu zaten durduğu yere götüren
    bir düğme — birkaç piksel kaydırıp bırakıyor.
    """
    return re.sub(
        r'(<li id="(k\d+)" class="source">)<a class="xref" href="#\2">(\[K\d+\])</a>',
        r"\1\3", text,
    )


def source_links(text, report_iso=""):
    """Kaynakça girdisindeki çıplak adresi iki çiple değiştir.

    Ekrandaki 120 karakterlik adres kimseye bir şey söylemiyordu: okunmuyor,
    hatırlanmıyor, yalnızca satırı taşırıyor. Kupürlerde çözüm çoktan bulunmuş
    durumda — başlık, altında iki çip — kaynakça da aynı şekli alıyor.

    Sıra kupürün tersi: orada birincil vekil / ikincil özgün, burada birincil
    özgün / ikincil vekil, çünkü kaynakça bir delil nesnesi. Ama ikisi de
    aynı iki kapıyı gösteriyor.
    """
    proxy_on = build_flags()[0]

    def entry(m, is_source):
        url = m.group(2)
        # Önce kayıt, sonra okuma yardımı: bu bir delil nesnesi, kanonik
        # adres başta durur.
        chips = [
            f'<a class="tr-read tr-read--plain" href="{html.escape(url, quote=True)}"'
            f' target="_blank" rel="noopener">Özgün metin ↗</a>'
        ]
        if proxy_on and is_source:
            host = up.urlsplit(url).hostname or ""
            if build_flags()[1].get(host) is True:
                chips.append(
                    f'<a class="tr-read" href="{html.escape(build_proxy(url), quote=True)}"'
                    f' target="_blank" rel="noopener">Türkçe oku ↗</a>'
                )
            else:
                chips.append('<span class="tr-blocked">çeviri engelli</span>')
        # Adresten önceki " — " ayracı da gider; başlık ve yayın kendi
        # noktalamalarıyla zaten tamamlanıyor.
        return f'<span class="source-go">{"".join(chips)}</span>'

    # Hem [K#] girdileri hem de "Erişilemeyen kaynaklar" listesi: ikisi de
    # kaynak satırı, ikisi de aynı uzun adres sorununu taşıyordu.
    def li_block(m):
        # Bir girdide birden çok kaynak olabiliyor (" · " ile ayrılmış); her
        # adres kendi iki kapısını alır, yoksa ilki ekranda çıplak kalıyordu.
        is_source = 'class="source"' in m.group(1)
        body = re.sub(
            r'(\s*[—-]?\s*)<a href="(https?://[^"]+)"[^>]*>[^<]*</a>',
            lambda a: entry(a, is_source), m.group(2), flags=re.S,
        )
        # Yaş yalnızca gerçek kaynak girdilerinde: "Erişilemeyen kaynaklar"
        # bloğu bir boşluk ilanı, oraya ölçü koymak bloğun işini bulandırır.
        if is_source and report_iso:
            age = source_age(re.sub(r"<[^>]+>", " ", m.group(2)), report_iso)
            if age:
                body = body.replace(
                    '<span class="source-go">',
                    f'<span class="source-age">{age}</span><span class="source-go">', 1,
                )
        return m.group(1) + body + m.group(3)

    return re.sub(r'(<li(?: id="k\d+" class="source")?>)((?:(?!</li>).)*)(</li>)',
                  li_block, text, flags=re.S)


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


def link_watch_items(text, slugs):
    """İzleme kalemlerinin adını kendi dosyasına bağla.

    Ad hem okuma yolunda hem katlamada geçiyor; ikisi de aynı yere gider.
    Eşleşme bulunamazsa satır düz metin kalır — var olmayan bir sayfaya
    bağlantı, bağlantı olmamasından kötü.
    """
    if not slugs:
        return text
    b = _build()

    def li(m):
        head, body = m.group(1), m.group(2)
        plain = re.sub(r"<[^>]+>", " ", body)
        slug = slugs.get(b.watch_key(plain))
        if not slug:
            return m.group(0)
        # Kendi kimliği olan kalem <strong class="ganchor"> taşıyor; olmayanın
        # adı satırın başında düz metin olarak duruyor.
        anchored = re.sub(
            r'(<strong class="ganchor">)([^<]+)(</strong>)',
            lambda a: f'{a.group(1)}<a class="thread-link" href="/izleme/{slug}.html">'
                      f'{a.group(2)}</a>{a.group(3)}',
            body, count=1)
        if anchored != body:
            return head + anchored
        # Ad, durum işaretinden önce biter. Sınır olarak yalnız "—" ve "<"
        # alınınca, işaretsiz yazılmış satırda ad açılış parantezini de
        # yutuyordu: "… yanıt süresi (" diye bir iplik adı bağlanıyordu.
        name = re.match(r"\s*([^<—(]+?)\s*(?=—|<|\(|$)", body)
        if not name or not name.group(1).strip():
            return m.group(0)
        return (head + body.replace(
            name.group(1),
            f'<a class="thread-link" href="/izleme/{slug}.html">{name.group(1)}</a>', 1))

    def section(m):
        return m.group(1) + re.sub(r"(<li\b[^>]*>)((?:(?!</li>).)*)", li, m.group(2), flags=re.S)

    return re.sub(r'(<h2[^>]*id="izleme-listesi">.*?</h2>)(.*?)(?=<h2|\Z)',
                  section, text, flags=re.S)


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
            # Bugünün bir gelişmesine bağlanan kalem kımıldamıştır — ajan
            # "ilerledi" yazsın ya da yazmasın. Kelimeyi aramak, olayı değil
            # olayın anlatılış biçimini ölçüyordu.
            if re.search(r'href="#g\d+"', li):
                moved.append(li)
            elif re.search(r"\bbekliyor\b", plain, re.I):
                waiting.append(li)
            else:
                moved.append(li)
        if not waiting:
            return m.group(0)
        moved = [reading_path_shape(li) for li in moved]

        rest = re.sub(r"<(?:p|ul|ol)\b.*?</(?:p|ul|ol)>", "", body, flags=re.S).strip()
        out = [head]
        if moved:
            out.append("<ul>" + "".join(moved) + "</ul>")
        out.append(
            f'<details class="watch"><summary>Açık konular · '
            f'<span class="num">{len(waiting)}</span></summary><ul>'
            + "".join(strip_waiting(li) for li in waiting)
            + "</ul></details>"
        )
        return "".join(out) + rest

    return re.sub(r'(<h2[^>]*>İZLEME LİSTESİ</h2>)(.*?)(?=<h2|\Z)', section, text, flags=re.S)


def reading_path_shape(li):
    """Okuma yolu satırı: <iplik> → bugün: <gelişme>. Gerisi düz cümle.

    Eski biçim ajanın durum kelimesini ekrana taşıyordu ("— *ilerledi (…)*").
    O kelime bir işaret, bilgi değil: satırın okuma yolunda olması zaten
    kımıldadığını söylüyor ve kararı veren şey kelime değil, bugünün bir
    gelişmesine giden bağlantı. Kelimeyi basmak, yapının söylediğini bir de
    metinle tekrar etmek — üstelik ajan onu bazen "bekliyor" yazdığında
    satır kendi konumuyla çelişiyordu.

    Kalan serbest metin atılmıyor: ajanın oraya yazdığı cümle çoğu zaman
    gelişmenin başlığında olmayan tek şey.
    """
    name = re.match(r"\s*<li\b[^>]*>\s*(<a class=\"thread-link\".*?</a>|[^<—(]+)", li, re.S)
    dev = re.search(r'<a class="xref" href="(#g\d+)"[^>]*>(.*?)</a>', li, re.S)
    if not (name and dev):
        return li
    head = name.group(1).strip()
    rest = li[name.end():]
    # Gelişme bağlantısını ve onu saran parantezi/durum kalıbını çıkar.
    rest = rest[:dev.start() - name.end()] + rest[dev.end() - name.end():]
    rest = re.sub(r"</?em>", "", rest)
    rest = re.sub(r"^\s*(?:\(\d{2}\.\d{2}\.\d{4}\s+raporu\))?\s*(?:—|–|-)?\s*", "", rest)
    rest = re.sub(r"\b(?:ilerledi|bekliyor)\b\.?", "", rest, flags=re.I)
    rest = re.sub(r"\(\s*\)|\(\s*\.\s*\)", "", rest)
    rest = re.sub(r"</li>\s*$", "", rest)
    rest = re.sub(r"\s+", " ", rest).strip(" .,;—–-")
    # Ayırıcı gerekli: gelişmenin başlığıyla serbest cümle birbirine
    # yapışınca tek bir uzun ad gibi okunuyor.
    tail = f". {tr_upper_first(rest)}." if rest else ""
    return (f'<li class="watch-move">{head}'
            f'<span class="watch-arrow"> → bugün: </span>'
            f'<a class="xref" href="{dev.group(1)}">{dev.group(2)}</a>{tail}</li>')


def strip_waiting(li):
    """Katlanan satırdan yalnızca durum kelimesini at.

    Katlamadaki her kalem tanımı gereği bekliyor; durumu satır satır
    tekrarlamak normal bir hâli N kez duyurmaktır. Ama yalnızca o kelime:
    "hangi kalibreler anıldı" gibi cümleleri regexle silmeye kalkmak,
    ajanın yazdığı gerçek bilgiyi kör bir kuralla çöpe atmak olurdu.
    """
    return re.sub(r"\s*—\s*(?:<em>)?\s*bekliyor\.?\s*(?:</em>)?", " ", li, flags=re.I)


def fold_sources(text):
    """KAYNAKLAR'ı katla: referans danışılır, okuma yolunu tıkamaz.

    On altı girdi, her biri tarih, yaş ve iki kapı taşıyor — belgenin en uzun
    ve en az okunan bölümü. [K#] atfı yine oraya götürüyor; kapalı bir katlama
    hedefi içeriyorsa açılıyor (app.js), yani yol kısalmıyor, yalnızca
    okuma çizgisi temizleniyor.
    """
    def wrap(m):
        head, body = m.group(1), m.group(2)
        count = len(re.findall(r'<li id="k\d+"', body))
        label = re.sub(r"<[^>]+>", "", head).strip()
        # Kimlik katlamanın kendisinde. Bir süre gizli bir <h2> üstünde
        # duruyordu — şerit çipini ondan türetiyordu — ama gizli öğenin
        # kutusu yok, scrollIntoView hiçbir şey yapmıyor ve çip ölü
        # görünüyordu. EK'te zaten böyle: kimlik <details>'te.
        return (f'<details class="refs" id="kaynaklar"><summary class="kicker">{label}'
                f' <span class="kicker-count num">{count}</span></summary>'
                f'{body}</details>')

    return re.sub(r'(<h2 id="kaynaklar">.*?</h2>)(.*?)(?=<h2|<details class="appendix"|\Z)',
                  wrap, text, flags=re.S)


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


# Okuma sırası: karar önce, gerekçe sonra. Yönetici özeti ne olduğunu söyler,
# Fırsatlar/Riskler ne anlama geldiğini; gelişmelerin tam anlatımı ikisinin
# ardından gelir. Ajan hâlâ kendi sırasıyla yazıyor, sıra burada kuruluyor.
SECTION_ORDER = ["alarmlar", "ozet", "portfoy", "gelismeler",
                 "izleme-listesi", "kaynaklar", "ek"]


def reorder_sections(text):
    """Bölümleri okuma sırasına diz; listede olmayan bölüm yerinde kalır."""
    parts = re.split(r'(?=<h2 id="[^"]+">)', text)
    if len(parts) < 3:
        return text
    lead, blocks = parts[0], parts[1:]
    keyed = []
    for b in blocks:
        m = re.match(r'<h2 id="([^"]+)">', b)
        sid = m.group(1) if m else ""
        keyed.append((SECTION_ORDER.index(sid) if sid in SECTION_ORDER else 99, sid, b))
    # Sıralama kararlı: listede olmayanlar özgün sıralarını korur.
    keyed.sort(key=lambda t: t[0])
    return lead + "".join(b for _r, _s, b in keyed)


def drop_unread_sources(text):
    """"Erişilemeyen kaynaklar" bloğunu düşür (Rev 14).

    Etiket kaynağın durumunu iddia ediyordu, kaydettiği şey ajanın
    deneyimiydi — ölçtük, "yönlendirme hatası" denen sayfa 200 dönüp 7.220
    karakter makale veriyordu. Okuyucuya kapı verip üstüne "kilitli"
    yazıyorduk. Ayrıca rapordaki hiçbir iddia onlara dayanmıyor.
    """
    return re.sub(
        r"<p>\s*<strong>\s*Erişilemeyen kaynaklar\s*</strong>\s*</p>\s*<ul>.*?</ul>",
        "", text, flags=re.S,
    )


def drop_scan_note(text):
    """Ajanın kapsam notunu sil.

    "Aday listesi üretilmedi; günün başlık taraması yapılamadı" okuyucunun
    varlığını bilmediği bir iç mekanizmayı adlandırıyordu. Yerine türetilmiş
    bir ölçüm koymayı denedim ("13 kaynağın 3'ü medya takibinde de var") —
    o da tutmadı: ürünü kuran kişi bile ne işe yaradığını çıkaramadı.
    Okuyucunun eyleme dönüştüremediği bir ölçüm, ölçüm olduğu için
    yayınlanmayı hak etmiyor.
    """
    return re.sub(
        r"<(blockquote|p)>\s*(?:<p>)?\s*Aday listesi üretilmedi.*?</\1>", "", text,
        count=1, flags=re.S,
    )


def rename_headers(text):
    for old, new in HEADER_RENAMES.items():
        text = text.replace(f"<th>{old}</th>", f"<th>{new}</th>")
        text = text.replace(f'data-label="{old}"', f'data-label="{new}"')
    return text


def enrich(text, developments, alarm=False, report_iso="", slugs=None):
    dev_ids = {str(d.get("id", "")).lower() for d in developments if d.get("id")}
    # Düzyazı atfının tek doğruluk kaynağı: frontmatter'daki kısa ad.
    dev_labels = {
        str(d["id"]).lower(): str(d.get("label", "")).strip()
        for d in developments if d.get("id") and str(d.get("label", "")).strip()
    }
    # Rakip maddeleri gelişmeye dönüşmeden çapa kurulmaz: h3 olarak doğup
    # sonra kimliklerini alıyorlar.
    text = fold_rivals(text)
    text = add_heading_anchors(text)
    # Çapalar kurulduktan hemen sonra: silinen blokla birlikte ona giden
    # atıflar da kendiliğinden bağlantısız kalıyor (link_citations bunu
    # metinde id var mı diye okuyor).
    text = drop_empty_alarms(text, alarm)
    text = drop_mke_agenda(text)
    text = add_item_anchors(text)
    text = add_source_anchors(text, report_iso)
    text = add_summary_links(text, dev_ids)
    # Birleşme rozetlerden önce: rozet ilk hücredeki "G1 — " önekini yiyor,
    # sıralama ise o öneki okuyor.
    text = merge_portfolio(text)
    text = add_table_badges(text, dev_ids)
    text = link_citations(text, dev_ids, 'id="alarmlar"' in text, dev_labels)
    text = drop_self_links(text)
    text = drop_unread_sources(rename_headers(text))
    text = link_watch_items(text, slugs)
    text = reorder_sections(fold_watchlist(drop_scan_note(text)))
    return fold_sources(fold_appendix(text))


def nav(body_html):
    """Başlığın altındaki şerit: belgenin bölümleri.

    Eskiden tek tek gelişmeleri listeliyordu; 14 çip bir şeride sığmayınca
    kaydırmalı bir raya ve "Rakipler +4" gibi açılır gruplara dönüşmüştü. O
    hâlde şerit belgenin haritası değil ikinci bir içindekiler listesiydi:
    okuyucu hangi gelişmenin nerede olduğunu bilmeden çipe basıyordu.

    Bölümler sabit, az ve okuyucunun zaten bildiği şeyler; ne kaydırma ne
    gruplama gerekiyor, sığmazsa alt satıra geçer.
    """
    # Katlanan bölümün kimliği <details>'te duruyor (KAYNAKLAR, EK). Yalnız
    # <h2> okununca o bölümlerin çipi hiç basılmıyordu: EK'i olan beş günün
    # hiçbirinde EK çipi yoktu ve kimse fark etmedi, çünkü eksik bir çip
    # bozuk görünmüyor — sadece yok.
    ids = [m.group(2) for m in re.finditer(
        r'<(h2|details)[^>]*\bid="([^"]+)"', body_html)
        if m.group(1) == "h2" or m.group(2) in SECTION_ORDER]
    chips = [
        f'<a class="chip" href="#{i}">'
        f'{html.escape(SECTION_CHIP.get(i, i.replace("-", " ").title()))}</a>'
        for i in ids if i not in CHIP_SKIP
    ]
    if len(chips) < 2:
        return ""
    return ('<nav class="devnav" id="devnav" aria-label="Bölümler">'
            + "".join(chips) + "</nav>")


# ---------- Rev 16: tek anlatı evi, hesaplanmış rakip şeridi ----------

def fold_rivals(text):
    """RAKİP HAREKETLERİ'ni GELİŞMELER'in içine al.

    22 Eylül'de tek bir gelişme beş yerde anlatılıyordu: özet satırı,
    Fırsatlar satırı, Riskler satırı, Rakip hareketleri maddesi ve
    Gelişmeler bloğu. Rakip maddeleri g1–g2'yi tutuyordu, yani özetin ilk
    iki satırı gelişmelerin olmadığı bir bölüme işaret ediyordu. Bir
    gelişmenin bir anlatı evi olur; rakip olması onu ayrı bir tür yapmıyor,
    sadece kimin yaptığını söylüyor.

    Başlıksız kapanış maddesi ("… tespit edilmedi") düşer: o cümle bir
    gözlem değil, bir yoklukla ilgili iddiaydı ve artık raydaki şerit
    aynı şeyi sayarak söylüyor.
    """
    sec = re.search(r"<h2>\s*RAKİP HAREKETLER[İI]\s*</h2>(.*?)(?=<h2|\Z)", text, flags=re.S)
    if not sec:
        return text
    blocks = []
    for li in re.findall(r"<li>(.*?)</li>", sec.group(1), flags=re.S):
        m = re.match(r"\s*<strong>\s*(G\d+)\s*·\s*([^<]+?)\s*</strong>\s*(?:—|–|-)?\s*(.*)",
                     li, flags=re.S)
        if not m:
            continue                      # başlıksız kapanış maddesi: düşer
        blocks.append((int(m.group(1)[1:]),
                       f"<h3>{m.group(1)} · {m.group(2).strip()}</h3>\n"
                       f"<p>{m.group(3).strip()}</p>"))
    text = text[:sec.start()] + text[sec.end():]
    if not blocks:
        return text

    def into_developments(m):
        return m.group(0).rstrip() + "\n" + "\n".join(b for _n, b in blocks)

    text, n = re.subn(r"<h2>\s*GELİŞMELER\s*</h2>", into_developments, text, count=1)
    if not n:                             # GELİŞMELER yoksa bölümü geri koy
        return text + "\n".join(b for _n, b in blocks)
    return sort_developments(text)


def sort_developments(text):
    """GELİŞMELER içindeki blokları g kimliğine göre diz.

    Özet g1'den başlıyor; gövdenin g3'ten başlaması okuyucuyu ilk satırda
    olmayan bir yere gönderiyordu.
    """
    sec = re.search(r"(<h2>\s*GELİŞMELER\s*</h2>)(.*?)(?=<h2|\Z)", text, flags=re.S)
    if not sec:
        return text
    body = sec.group(2)
    parts = re.split(r"(?=<h3>\s*G\d+\s*·)", body)
    lead = parts[0] if parts and not re.match(r"\s*<h3>\s*G\d+", parts[0]) else ""
    blocks = parts[1:] if lead else parts
    if len(blocks) < 2:
        return text
    def gid(b):
        m = re.match(r"\s*<h3>\s*G(\d+)", b)
        return int(m.group(1)) if m else 10**6
    return (text[:sec.start(2)] + lead + "".join(sorted(blocks, key=gid))
            + text[sec.end(2):])


IMPACT_TAG = '<span class="impact impact--{kind}">{label}</span>'


def merge_portfolio(text):
    """FIRSATLAR + RİSKLER → tek tablo: PORTFÖYE ETKİSİ.

    İki tablo aynı soruyu soruyordu — "bu gelişme portföy için ne demek" —
    ve aynı gelişme ikisinde birden görününce okuyucu iki ayrı yerde iki
    ayrı satır okuyup ilişkiyi kendi kuruyordu. Tek tabloda fırsat ve risk
    satırları yan yana duruyor; bir gelişmenin iki yönü olması onun iki
    gelişme olduğu anlamına gelmiyor.

    "Etki" renk değil metin: renk bir durum işareti ve bu üründe yalnız
    alarmın durumu var. Fırsatı yeşile boyamak, her gün yeşil gören bir
    okuyucuya hiçbir şey söylemez.
    """
    def grab(anchor, kind, label):
        m = re.search(rf'<h2 id="{anchor}">.*?</h2>\s*(<table>.*?</table>)', text, flags=re.S)
        if not m:
            return None, []
        rows = re.findall(r"<tr>\s*(<td.*?)</tr>", m.group(1), flags=re.S)
        tag = IMPACT_TAG.format(kind=kind, label=label)
        out = []
        for r in rows:
            cells = re.findall(r"<td[^>]*>.*?</td>", r, flags=re.S)
            if len(cells) < 3:
                continue
            gid = re.search(r"<td[^>]*>\s*G(\d+)", cells[0])
            out.append((int(gid.group(1)) if gid else 10**6,
                        f"<tr>{cells[0]}<td>{tag}</td>{cells[1]}{cells[2]}</tr>"))
        return m, out

    m_f, rows_f = grab("firsatlar", "firsat", "FIRSAT")
    m_r, rows_r = grab("riskler", "risk", "RİSK")
    if not (rows_f or rows_r):
        return text
    # Kararlı sıralama: aynı gelişmede önce fırsat, sonra risk.
    rows = sorted(rows_f + rows_r, key=lambda t: t[0])
    table = (
        '<h2 id="portfoy">PORTFÖYE ETKİSİ</h2>\n<table>\n<thead>\n<tr>'
        "<th>Gelişme</th><th>Etki</th><th>Ne ifade ediyor</th>"
        "<th>İzlenecek gösterge</th></tr>\n</thead>\n<tbody>\n"
        + "\n".join(r for _g, r in rows) + "\n</tbody>\n</table>"
    )
    # Eski iki bölümü tümüyle sil, birleşiği ilkinin durduğu yere koy.
    spans = [s for s in (re.search(rf'<h2 id="{a}">.*?(?=<h2|\Z)', text, flags=re.S)
                         for a in ("firsatlar", "riskler")) if s]
    spans.sort(key=lambda s: s.start())
    here = spans[0].start()
    out = text
    for s in reversed(spans):                 # sondan başa: ofsetler kaymasın
        out = out[:s.start()] + out[s.end():]
    return out[:here] + table + "\n" + out[here:]
