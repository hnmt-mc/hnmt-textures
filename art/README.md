# テクスチャの制作元と仕上げ

全65バリエーションを32×32・RGBA・二値透過に統一しています。
IDと既存ファイル名は変えていません。魚の元絵には組み込みimage_genを使用し、
縮小後に色数・輪郭・成魚と若魚の体格・模様を整えています。
手描きであるとは表記しません。道具・餌・料理は座標と配色を指定したピクセル描画です。

## 魚の編集元

`fish.json`は32行×32列のインデックス形式です。`.`は透過、それ以外は`palette`の色です。
`make_textures.py`はこの編集元をそのままPNGへ書き出します。
再生成に画像生成APIや元の大きな画像は必要ありません。
輪郭は青みのある灰色、陰影は少ない段階に留めています。
目・口・血・内臓は描いていません。

画像生成の共通指定は以下です。

> One isolated Japanese fish sprite, side view with head left and tail right; cozy Japanese pixel art; soft muted palette, clear silhouette and clustered shading; transparent background; no eyes, mouth, wounds, organs, text, water, props, shadows or glow; readable at 32×32.

個別に指定した特徴:

| ID | 元絵の指定と最終調整 |
| --- | --- |
| unagi | 紺灰色の背、淡い腹、S字の細長い体。厚みは一定で薄く |
| salmon | 青緑の背と銀色の腹、淡い杏色のひれ。胴の高さを調整 |
| kohada | 小さな銀色の若魚、細身の体と控えめな斑点。成魚より小さく |
| konoshiro | 銀色の成魚、青緑の背、整列した斑点。若魚より胴を高く |
| tai | 丸みのある菱形の体、珊瑚色の背とクリーム色の腹 |
| hirame | 上から見た平たい菱形、砂色の斑模様、薄いひれ |
| saba | 流線形、青灰色の背と銀色の腹、背の模様 |
| hamachi | すっきりした若魚、細い金色の帯、小さめの体 |
| buri | 厚みのある成魚、幅広い金色の帯、若魚より高い胴 |
| ika | 真珠色の胴と淡い紫の陰影、簡略化した触腕。吸盤は描かない |
| kanpachi | オリーブ色の背と金色の帯、丸みのある額 |
| maguro | 紡錘形の大きな体、藍色の背、三日月形の尾 |

## 釣竿の実物資料

メーカー公式の構造・握り・リール位置を参考にしています。
商品画像やロゴはパックへコピーしていません。
ブランド品の完全なレプリカではなく、ゲーム内の区分を読み取れるように描いています。

- 渓流: [DAIWA 小継 渓流 X](https://www.daiwa.com/jp/product/t72ir1t)、[SHIMANO 渓流テンカラ](https://fish.shimano.com/ja-JP/product/rod/keiryu/tenkara/a075f000045cf1bqau.html)
- 磯: [SHIMANO ホリデー イソ](https://fish.shimano.com/ja-JP/product/rod/isobouhatei/other/a075f00002ltl7gqaq.html)
- 船: [SHIMANO ライトゲーム BB](https://fish.shimano.com/ja-JP/product/rod/funehanyou/lightgame/a075f00003rgsqmqak.html)

渓流はリールなし、磯はスピニングリール、船は両軸リールです。
通常と投げた状態は同じ竿を描き、通常側だけに糸と針を追加します。

## 料理

刺身・握り・丼・焼き物・煮物・汁物で盛り付けを分けています。
白身は繊維と皮の色、サーモンは脂の筋、マグロは艶、うなぎは焼き目を描き分けています。
いくら丼は小粒のいくらを密に並べ、握りは小ぶりなシャリに長いネタを被せています。
料理のIDをJava側で有効にする変更は、この作業には含めていません。
