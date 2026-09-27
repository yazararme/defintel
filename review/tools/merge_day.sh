#!/bin/bash
# Merge günü: rev21-33'ü main'e alır. Kullanım (repo kökünden, dosyayı önce kopyalayarak —
# betik çalışırken çalışma ağacı main'e döner ve bu dosya ağaçtan kalkar):
#   cp review/tools/merge_day.sh /tmp/merge_day.sh && bash /tmp/merge_day.sh
# DRY=1 → her şeyi yapar ama push etmez (deneme).
#
# main'deki günlük veri commit'leri yalnız üretilmiş sayfalarda çakışır (izleme/, index.html,
# oyuncular.html, data/oyuncular.json …). Bunlar dalın hâliyle alınır, sonra build.py hepsini
# birleşik kaynaktan yeniden üretir. Başka bir dosyada çakışma olursa betik hiçbir şey yapmadan durur.
set -uo pipefail
cd "${REPO:-$HOME/Documents/Projects/defintel-repo}" || exit 1
PUSH_URL=https://github.com/yazararme/defintel.git
start=$(git symbolic-ref -q --short HEAD || git rev-parse HEAD)
geri() { git switch -q "$start" 2>/dev/null || git switch -q --detach "$start"; }
dur() { echo "DUR: $*"; git merge --abort 2>/dev/null; geri; exit 1; }

git fetch -q origin || { echo "DUR: GitHub'a ulaşılamadı"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "DUR: kaydedilmemiş değişiklik var (git status)"; exit 1; }
# Rev 31'in yalnız yerel kanıtı; main'deki gerçek 24 Eylül dosyasıyla çakışır (yeniden üretilebilir).
rm -f data/news/2026-09-24-aday.md
git switch -q --detach origin/main || { echo "DUR: main'e geçilemedi"; exit 1; }

if ! git merge --no-ff --no-commit origin/rev21-33 >/dev/null 2>&1; then
  cakisan=$(git diff --name-only --diff-filter=U)
  [ -n "$cakisan" ] || dur "merge başarısız (çakışma yok): git merge çıktısına bak"
  beklenmeyen=$(echo "$cakisan" | grep -vE '^(izleme/|reports/|haberler/|index\.html$|arsiv\.html$|oyuncular\.html$|data/oyuncular\.json$|data/reports\.json$)' || true)
  [ -z "$beklenmeyen" ] || dur "beklenmeyen çakışma — karar gerekiyor:
$beklenmeyen"
  echo "$cakisan" | xargs git checkout --theirs --
  echo "üretilmiş $(echo "$cakisan" | wc -l | tr -d ' ') dosyada çakışma → dalın hâli alındı, yeniden derleniyor"
fi

python3 build.py > /tmp/defintel-merge-build.log 2>&1 || dur "build.py hata verdi (/tmp/defintel-merge-build.log)"
git add -A -- . ':(exclude).DS_Store' ':(exclude)**/.DS_Store'
git commit -q -m "Merge rev21-33 into main (Rev 21–33, K1–K7)" || dur "commit atılamadı"
echo "birleşik commit: $(git rev-parse --short HEAD) · $(grep -c '' /tmp/defintel-merge-build.log) satır build günlüğü"

if [ "${DRY:-0}" = 1 ]; then
  echo "DRY: push atlandı"; git reset -q --hard origin/main; geri; exit 0
fi
git -c credential.helper='!gh auth git-credential' push -q "$PUSH_URL" HEAD:main \
  || { echo "DUR: push reddedildi (büyük olasılıkla o sırada bir sabah çalıştırması main'e yazdı). Birkaç dakika sonra aynı komutu yeniden çalıştır."; git reset -q --hard origin/main; geri; exit 1; }
git fetch -q origin
echo "TAMAM: main'e alındı → $(git rev-parse --short HEAD). Site ~1–3 dk içinde yeni hâliyle açılır."
geri
