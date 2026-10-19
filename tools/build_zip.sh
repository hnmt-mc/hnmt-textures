#!/bin/sh
# 配布用 zip を build/ に作る。  使い方: sh tools/build_zip.sh [flat]
#   引数なし: 3D版（hnmt-textures.zip）。サーバーが参加した人へ送るのは、これ。モデルは models3d にあるので、Blender は要らない
#             （モデルを作り直すときだけ、blender_fish3d.py・blender_bait3d.py・blender_coolers.py などを実行する）
#   flat    : 平らなアイコン版（hnmt-textures-flat.zip）
set -e
cd "$(dirname "$0")/.."
ROOT=$(pwd)
B=$ROOT/build
mkdir -p "$B"
if [ "$1" = "flat" ]; then
  OUT=hnmt-textures-flat.zip; SRC=$ROOT
else
  rm -rf "$B/stage3d" && mkdir -p "$B/stage3d"
  cp -R pack.mcmeta assets "$B/stage3d/"
  cp -R models3d/. "$B/stage3d/assets/hnmt/models/item/"
  OUT=hnmt-textures.zip; SRC=$B/stage3d
fi
rm -f "$B/$OUT"
(cd "$SRC" && zip -qr -X "$B/$OUT" pack.mcmeta assets)
shasum -a 1 "$B/$OUT"
