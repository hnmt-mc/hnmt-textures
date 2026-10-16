#!/bin/sh
# 配布用 zip を resourcepack-build/ に作る。  使い方: sh resourcepack/tools/build_zip.sh [3d]
#   引数なし: 平らなアイコン版（hnmt-resourcepack.zip）
#   3d      : 魚・釣竿・餌が 3D モデルの版（hnmt-resourcepack-3d.zip）。モデルは resourcepack/models3d にあるので、Blender は要らない
#             （モデルを作り直すときだけ、blender_fish3d.py・blender_rod3d.py・blender_bait3d.py を実行する）
set -e
cd "$(dirname "$0")/../.."
ROOT=$(pwd)
B=$ROOT/resourcepack-build
mkdir -p "$B"
if [ "$1" = "3d" ]; then
  rm -rf "$B/stage3d" && mkdir -p "$B/stage3d"
  cp -R resourcepack/pack.mcmeta resourcepack/assets "$B/stage3d/"
  cp -R resourcepack/models3d/. "$B/stage3d/assets/hnmt/models/item/"
  OUT=hnmt-resourcepack-3d.zip; SRC=$B/stage3d
else
  OUT=hnmt-resourcepack.zip; SRC=$ROOT/resourcepack
fi
rm -f "$B/$OUT"
(cd "$SRC" && zip -qr -X "$B/$OUT" pack.mcmeta assets)
shasum -a 1 "$B/$OUT"
