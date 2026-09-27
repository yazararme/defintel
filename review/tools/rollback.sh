#!/bin/bash
# Merge'ü geri al: main'deki "Merge rev21-33" commit'ini revert eder, sayfaları eski build.py ile
# yeniden üretir, push eder. Kullanım (repo kökünden; önce kopyala — betik çalışırken ağaç değişir):
#   cp review/tools/rollback.sh /tmp/rollback.sh && bash /tmp/rollback.sh
# DRY=1 → push etmez.
#
# Merge'den sonra sabah çalıştırmaları üretilmiş sayfaları (izleme/, index.html …) yeniden yazmış
# olabilir; revert bunlarda çakışırsa merge öncesi hâli alınır ve build.py hepsini yeniden üretir.
# Başka bir dosyada çakışma olursa betik hiçbir şey yapmadan durur.
set -uo pipefail
cd "${REPO:-$HOME/Documents/Projects/defintel-repo}" || exit 1
PUSH_URL=https://github.com/yazararme/defintel.git
start=$(git symbolic-ref -q --short HEAD || git rev-parse HEAD)
geri() { git switch -q "$start" 2>/dev/null || git switch -q --detach "$start"; }
dur() { echo "DUR: $*"; git revert --abort 2>/dev/null; geri; exit 1; }

git fetch -q origin || { echo "DUR: GitHub'a ulaşılamadı"; exit 1; }
[ -z "$(git status --porcelain --untracked-files=no)" ] || { echo "DUR: kaydedilmemiş değişiklik var (git status)"; exit 1; }
git switch -q --detach "${BASE_REF:-origin/main}" || { echo "DUR: main'e geçilemedi"; exit 1; }
M=$(git log --merges -1 --format=%H --grep='rev21-33')
[ -n "$M" ] || dur "main'de rev21-33 merge commit'i bulunamadı"
echo "geri alınacak: $(git log -1 --format='%h %s' "$M")"

if ! git revert --no-commit -m 1 "$M" >/dev/null 2>&1; then
  cakisan=$(git diff --name-only --diff-filter=U)
  [ -n "$cakisan" ] || dur "revert başarısız (çakışma yok)"
  beklenmeyen=$(echo "$cakisan" | grep -vE '^(izleme/|reports/|haberler/|index\.html$|arsiv\.html$|oyuncular\.html$|data/oyuncular\.json$|data/reports\.json$)' || true)
  [ -z "$beklenmeyen" ] || dur "beklenmeyen çakışma — bana yaz:
$beklenmeyen"
  echo "$cakisan" | xargs git checkout --theirs --
fi
python3 build.py > /tmp/defintel-rollback-build.log 2>&1 || dur "build.py hata verdi (/tmp/defintel-rollback-build.log)"
git add -A -- . ':(exclude).DS_Store' ':(exclude)**/.DS_Store'
git commit -q -m "Revert rev21-33 merge ($(git rev-parse --short "$M"))" || dur "commit atılamadı"

if [ "${DRY:-0}" = 1 ]; then echo "DRY: push atlandı · $(git log --oneline -1)"; geri; exit 0; fi
git -c credential.helper='!gh auth git-credential' push -q "$PUSH_URL" HEAD:main \
  || { echo "DUR: push reddedildi (o sırada bir sabah çalıştırması yazmış olabilir). Birkaç dakika sonra aynı komutu yeniden çalıştır."; geri; exit 1; }
echo "TAMAM: merge geri alındı → $(git rev-parse --short HEAD). Site ~1–3 dk içinde eski hâline döner."
geri
