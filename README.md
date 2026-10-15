# 日ノ本鯖 リソースパック（魚・釣竿・餌の見た目）

釣りの魚、カスタム釣竿、餌の見た目のリソースパックです。プラグイン（hnmt-core）は、アイテムの `item_model` で `hnmt:fish/<ID>`・`hnmt:rod/<ID>`・`hnmt:bait/<ID>` を指しているだけなので、**このパックを入れなければ、元のバニラの見た目で表示されます**（プラグインの動作は変わりません）。

- 対象: Minecraft 1.21.11（`pack.mcmeta` の `min_format`・`max_format` は 75）。サーバーのバージョンを上げたときは、公式情報で確認してください。
- **ゲーム内での見え方は、まだ確認していません**（特に、3D版の GUI の中の角度と、額縁の向き）。

## 中身
| 場所 | 内容 |
| --- | --- |
| `assets/hnmt/textures/item/fish/<ID>.png` | 魚12種のテクスチャ（32x32のドット絵） |
| `assets/hnmt/textures/item/rod/<ID>.png` | 釣竿7本のテクスチャ（16x16。`_cast` は投げた状態） |
| `assets/hnmt/textures/item/bait/<ID>.png` | 餌4種のテクスチャ（16x16。やわらかい色の、かわいい絵） |
| `assets/hnmt/models/item/…` | 平らなアイコン版のモデル |
| `assets/hnmt/items/…` | 見た目の定義（釣竿は、投げた状態への切り替え付き） |
| `models3d/fish`・`models3d/rod`・`models3d/bait` | 3D版のモデル（直方体の `elements`）。Blender で生成したもの |
| `tools/` | テクスチャとモデルを作るスクリプト、zip を作るスクリプト |

魚の ID: `unagi`・`salmon`・`kohada`・`konoshiro`・`tai`・`hirame`・`saba`・`hamachi`・`buri`・`ika`・`kanpachi`・`maguro`（出世魚は、若魚と成魚で別の見た目）。
釣竿の ID: `bamboo`・`keiryu_nami`・`keiryu_jo`・`iso_nami`・`iso_jo`・`fune_nami`・`fune_jo`。餌の ID: `mimizu`・`ebi`・`iwashi`・`ika_no_mi`。

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
1. テクスチャ: `python3 resourcepack/tools/make_textures.py`（魚）・`make_rods.py`（釣竿）・`make_baits.py`（餌）。
2. 3Dモデル: `/Applications/Blender.app/Contents/MacOS/Blender --background --python resourcepack/tools/blender_fish3d.py`（釣竿は `blender_rod3d.py`、餌は `blender_bait3d.py`）。`models3d/` に書き出します。プレビュー画像は `resourcepack-build/preview3d/` に出ます。
3. 見本の一覧画像: `make_3d_sheet.py`。
