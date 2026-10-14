# このファイルの役割：
#   アナログ水位センサーで水位（タンクの底からの高さ、cm）を測ります。
#   センサーの出力は ADS1115 の A1 で読み、センサーの電源は GPIO17 で測るときだけ入れます。
#   書き方と約束ごとは、同じフォルダの README.md を見てください。
#   動作確認：bushitsu-dashboard/ で `python -m hydroponics.sensors.water_level` を実行すると結果が表示されます。


def read():
    """水位を測って、値のリストを返す。読み取りに失敗したら例外を投げる。"""
    # TODO：ここに次の処理を書き、下の raise の行を消す。
    #   1. GPIO17 でセンサーの電源を入れる（電極の腐食を防ぐため、測るときだけ入れる）
    #   2. ADS1115 の A1 の電圧を読む
    #   3. 電源を切る（読み取りに失敗しても必ず切れるように try / finally を使う）
    #   4. 電圧を cm に換算する（換算表は水位を何段階か変えて実測して作る。仕様書の第5章）
    #   センサー用ライブラリの import も、この関数の中に書く。
    raise NotImplementedError("water_level.read() はまだ書かれていません")
    # 読めたら、次の形で返す：
    # return [
    #     {"metric": "water_level", "label": "水位", "value": level_cm, "unit": "cm"},
    # ]


if __name__ == "__main__":
    print(read())
