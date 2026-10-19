# 日ノ本鯖 リソースパック（魚・釣竿・餌の見た目）

釣りの魚、カスタム釣竿、餌の見た目のリソースパックです。プラグイン（hnmt-core）は、アイテムの `item_model` で `hnmt:fish/<ID>`・`hnmt:rod/<ID>`・`hnmt:bait/<ID>` を指しているだけなので、**このパックを入れなければ、元のバニラの見た目で表示されます**（プラグインの動作は変わりません）。

- 対象: Minecraft 1.21.11（`pack.mcmeta` の `min_format`・`max_format` は 75）。サーバーのバージョンを上げたときは、公式情報で確認してください。
- **ゲーム内での見え方は、まだ確認していません**（特に、3D版の GUI の中の角度と、額縁の向き）。

## 中身
| 場所 | 内容 |
| --- | --- |
| `assets/hnmt/textures/item/fish/<ID>.png` | 魚12種のテクスチャ（32x32のドット絵） |
| `assets/hnmt/textures/item/rod/<ID>.png` | 釣竿7本のテクスチャ（32x32。`_cast` は投げた状態） |
| `assets/hnmt/textures/item/bait/<ID>.png` | 餌4種のテクスチャ（32x32。`make_bait_art.py` で作る、輪郭のはっきりした絵） |
| `assets/hnmt/models/item/…` | 平らなアイコン版のモデル |
| `assets/hnmt/items/…` | 見た目の定義（釣竿は、投げた状態への切り替え付き） |
| `models3d/fish`・`models3d/bait` | 3D版のモデル（直方体の `elements`）。釣竿は、3D版も平らなので、ない |
| `models3d/dish` | 器と盛り付けを別々に組んだ料理32品の3Dモデル |
| `blockbench/dish` | 料理のBlockbench編集元。32×32テクスチャを埋め込み済み |
| `assets/hnmt/textures/item/dish3d` | 料理3D版専用の32×32 UVアトラス。2Dアイコンとは別に管理 |
| `tools/` | テクスチャとモデルを作るスクリプト、zip を作るスクリプト |

魚の ID: `unagi`・`salmon`・`kohada`・`konoshiro`・`tai`・`hirame`・`saba`・`hamachi`・`buri`・`ika`・`kanpachi`・`maguro`（出世魚は、若魚と成魚で別の見た目）。
釣竿の ID: `bamboo`・`keiryu_nami`・`keiryu_jo`・`iso_nami`・`iso_jo`・`fune_nami`・`fune_jo`。餌の ID: `mimizu`・`ebi`・`iwashi`・`ika_no_mi`。

## 料理・素材の追加分

元のアイコンは32×32・RGBA・透過PNGです。魚12・釣竿14状態・餌4・料理32・素材3の計65種類があります。
料理3D版には、別途32枚の32×32・RGBAのUVアトラスを用意しています。
料理は`textures/item/dish/<ID>.png`・`items/dish/<ID>.json`・`models/item/dish/<ID>.json`、
米・いくら・まな板は`rice`・`ikura`・`board`として各ディレクトリの直下に置いています。
3Dモデルも`models3d/dish`および`models3d`直下へ収録しています。
料理と素材をJava側のitem_modelへ接続する変更は含めていません。

[絵の編集元・種類ごとの特徴・実物の釣竿の参考資料](art/README.md)も参照してください。

## クーラーボックス
魚専用の持ち運び箱（`hnmt:cooler/small`・`medium`・`large`）の見た目です。テクスチャは32x32で、輪郭と本体・蓋・氷・留め具の8色だけで描いています。モデルは直方体6〜8個の3Dで、平らなアイコン版・3D版のどちらの zip にも同じものが入ります。パックがなければ、元の樽のまま表示されます。

作り直すとき（Blender 4以降。検証は5.2.3）:
```sh
blender --background --factory-startup --python resourcepack/tools/blender_coolers.py -- --render
python3 -m unittest discover -s resourcepack/tools -p 'test_blender_coolers.py'
```
`resourcepack-build/cooler/` に、プレビュー（`preview.png`）と、置き換え用のファイルが出ます。ゲーム内での見え方は未確認です。

## 2つの版
- **平らなアイコン版**（`hnmt-resourcepack.zip`）: バニラの魚と同じ見せ方。
- **3D版**（`hnmt-resourcepack-3d.zip`）: 魚は、胴の断面を楕円にして、背と腹に向かって薄くなる丸みを付けています（魚1匹あたり直方体は80〜120個）。餌・米・いくらは、正面が2Dの絵のままで、奥行きは後ろへ伸びる輪切りです。料理32品は、底・側面・縁のある器と、ご飯・具材・薬味を別々の直方体で組み、1品1枚の32×32テクスチャを使います。料理にはJava版で対応するY軸22.5度・45度の回転があり、統合版への変換は未検証です。釣竿は、3D版でも、平らなアイコンのままです（竿は細く、立体にすると不自然になるため）。上面・下面・端の面は、輪郭の暗い線を除いた中身の色です。

## 料理の3Dモデルを編集する

Blockbenchで `blockbench/dish/<ID>.bbmodel` を開きます。
形式は **Java Block/Item** です。器・料理・薬味は `Vessel`・`Food`・`Garnish` のグループに分けています。
テクスチャはプロジェクトに埋め込んでいるため、画像ファイルを探さずに編集を始められます。

PNGを書き出す先は `assets/hnmt/textures/item/dish3d/<ID>.png`、
Block/Item Modelを書き出す先は `models3d/dish/<ID>.json` です。
既存の `textures/item/dish` と `models/item/dish` は2D版なので、上書きしないでください。

制作と書き出しはBlockbench Web 5.2.2で確認しました。
丼は空洞のある八角形の器、皿は浅い縁と高台がある器です。
いくらは段差のある粒、握りはご飯の山と端の薄いネタ、刺身は重ねた切り身として作っています。
曲面メッシュは使わず、Minecraftの直方体と対応角度の回転で形を近づけています。

座標から再生成する場合は、次のコマンドを使います。生成済みファイルへの手動編集は上書きされるので、先に保存・コミットしてください。

```sh
python3 resourcepack/tools/make_food_models.py
```

Blockbench本体で編集元・JSON・プレビューを再書き出しする場合は、Node.jsとPlaywrightが必要です。
作業用の依存関係は配布パックに入りません。Web版に接続できる環境で実行してください。

```sh
npm install --prefix resourcepack-build/blockbench-tools playwright
resourcepack-build/blockbench-tools/node_modules/.bin/playwright install chromium
PLAYWRIGHT_MODULE="$(pwd)/resourcepack-build/blockbench-tools/node_modules/playwright" \
  node resourcepack/tools/blockbench_food.cjs
python3 resourcepack/tools/make_food_models.py --review
python3 -m unittest discover -s resourcepack/tools -p test_food_models.py
sh resourcepack/tools/build_zip.sh 3d
python3 resourcepack/tools/verify_pack.py
```

個別プレビューと32品の一覧は `resourcepack-build/food3d/` に出力します。
ゲーム内のGUI・手持ち表示と、Geyserでの表示は未検証です。

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
resourcepack-build/venv/bin/python resourcepack/tools/make_fish_art.py
resourcepack-build/venv/bin/python resourcepack/tools/make_textures.py
resourcepack-build/venv/bin/python resourcepack/tools/make_rods.py
resourcepack-build/venv/bin/python resourcepack/tools/make_bait_art.py
resourcepack-build/venv/bin/python resourcepack/tools/make_food_art.py
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
