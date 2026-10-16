# 日ノ本鯖 リソースパック（魚・釣竿・餌の見た目）

釣りの魚、カスタム釣竿、餌の見た目のリソースパックです。プラグイン（hnmt-core）は、アイテムの `item_model` で `hnmt:fish/<ID>`・`hnmt:rod/<ID>`・`hnmt:bait/<ID>` を指しているだけなので、**このパックを入れなければ、元のバニラの見た目で表示されます**（プラグインの動作は変わりません）。

- 対象: Minecraft 1.21.11（`pack.mcmeta` の `min_format`・`max_format` は 75）。サーバーのバージョンを上げたときは、公式情報で確認してください。
- **ゲーム内での見え方は、まだ確認していません**（特に、3D版の GUI の中の角度と、額縁の向き）。

## 中身
| 場所 | 内容 |
| --- | --- |
| `assets/hnmt/textures/item/fish/<ID>.png` | 魚12種のテクスチャ（32x32のドット絵） |
| `assets/hnmt/textures/item/rod/<ID>.png` | 釣竿7本のテクスチャ（32x32。`_cast` は投げた状態） |
| `assets/hnmt/textures/item/bait/<ID>.png` | 餌4種のテクスチャ（32x32。やわらかい色の、かわいい絵） |
| `assets/hnmt/models/item/…` | 平らなアイコン版のモデル |
| `assets/hnmt/items/…` | 見た目の定義（釣竿は、投げた状態への切り替え付き） |
| `models3d/fish`・`models3d/rod`・`models3d/bait` | 3D版のモデル（直方体の `elements`）。Blender で生成したもの |
| `tools/` | テクスチャとモデルを作るスクリプト、zip を作るスクリプト |

魚の ID: `unagi`・`salmon`・`kohada`・`konoshiro`・`tai`・`hirame`・`saba`・`hamachi`・`buri`・`ika`・`kanpachi`・`maguro`（出世魚は、若魚と成魚で別の見た目）。
釣竿の ID: `bamboo`・`keiryu_nami`・`keiryu_jo`・`iso_nami`・`iso_jo`・`fune_nami`・`fune_jo`。餌の ID: `mimizu`・`ebi`・`iwashi`・`ika_no_mi`。

## 料理・素材の追加分

全テクスチャは32×32・RGBA・透過PNGです。魚12・釣竿14状態・餌4・料理32・素材3の計65種類があります。
料理は`textures/item/dish/<ID>.png`・`items/dish/<ID>.json`・`models/item/dish/<ID>.json`、
米・いくら・まな板は`rice`・`ikura`・`board`として各ディレクトリの直下に置いています。
3Dモデルも`models3d/dish`および`models3d`直下へ収録しています。
料理と素材をJava側のitem_modelへ接続する変更は含めていません。

[絵の編集元・種類ごとの特徴・実物の釣竿の参考資料](art/README.md)も参照してください。

## 2つの版
- **平らなアイコン版**（`hnmt-resourcepack.zip`）: バニラの魚と同じ見せ方。
- **3D版**（`hnmt-resourcepack-3d.zip`）: テクスチャを列ごとに直方体にした立体のモデル。魚1匹あたり直方体は16〜32個で、テクスチャは1枚のままなので、将来 Geyser（Rainbow）で統合版へ変換しやすい作りです。

## zip を作る
```sh
sh resourcepack/tools/build_zip.sh      # 平らなアイコン版
sh resourcepack/tools/build_zip.sh 3d   # 3D版
```
`resourcepack-build/` に zip ができ（Git には入れません）、SHA-1 が表示されます。3D版のモデルは `models3d` にあるので、Blender は要りません。

## サーバーへ配る
zip を、サーバーから直接ダウンロードできる URL に置き、`server.properties` に設定します。
```properties
resource-pack=<zip の URL>
resource-pack-sha1=<build_zip.sh が表示した SHA-1>
require-resource-pack=false
```
パックを更新したら、SHA-1 も必ず更新してください（プレイヤーのキャッシュが古いままになります）。

## 作り直す（開発者向け）

Python 3とPillow、プレビューにはBlenderを使用します。検証環境はBlender 5.2.3です。

```sh
python3 -m venv resourcepack-build/venv
resourcepack-build/venv/bin/pip install -r resourcepack/tools/requirements.txt
resourcepack-build/venv/bin/python resourcepack/tools/make_textures.py
resourcepack-build/venv/bin/python resourcepack/tools/make_rods.py
resourcepack-build/venv/bin/python resourcepack/tools/make_baits.py
resourcepack-build/venv/bin/python resourcepack/tools/make_food.py
resourcepack-build/venv/bin/python resourcepack/tools/make_pack.py
resourcepack-build/venv/bin/python resourcepack/tools/make_models.py
/Applications/Blender.app/Contents/MacOS/Blender --background --python resourcepack/tools/blender_preview.py
resourcepack-build/venv/bin/python resourcepack/tools/make_3d_sheet.py
sh resourcepack/tools/build_zip.sh
sh resourcepack/tools/build_zip.sh 3d
resourcepack-build/venv/bin/python resourcepack/tools/verify_pack.py
```

`make_models.py`はBlenderを使わず、テクスチャ1枚と軸に沿った直方体だけでJSONを作ります。
魚は16〜32個以内に制限し、モデル座標・UV・参照先・通常と投げた状態の違いを`verify_pack.py`で検査します。
既存の`blender_fish3d.py`・`blender_rod3d.py`・`blender_bait3d.py`は分類ごとの再生成とプレビュー用です。
これらは`python3`からPillowを読み込める環境で実行してください。

一覧画像は`resourcepack-build/`、全65種類の個別プレビューは`resourcepack-build/preview3d/`へ出力します。
制作物とプレビューはゲーム内検証の代わりにはなりません。Geyser/Rainbowでの変換、
ゲーム内の手持ち角度・額縁・GUIでの表示、料理の機能との接続は未検証です。
