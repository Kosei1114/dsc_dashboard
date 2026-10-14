# このファイルの役割：
#   BME280 で気温と湿度を測ります（I2C、アドレスは 0x76。基板によっては 0x77）。
#   書き方と約束ごとは、同じフォルダの README.md を見てください。
#   動作確認：リポジトリのルート で `python -m apps.hydroponics.sensors.bme280` を実行すると結果が表示されます。


def read():
    """気温と湿度を測って、値のリストを返す。読み取りに失敗したら例外を投げる。"""
    # TODO：ここに BME280 から値を読む処理を書き、下の raise の行を消す。
    #       センサー用ライブラリの import も、この関数の中に書く。
    raise NotImplementedError("bme280.read() はまだ書かれていません")
    # 読めたら、次の形で返す：
    # return [
    #     {"metric": "air_temp", "label": "気温", "value": temp, "unit": "℃"},
    #     {"metric": "humidity", "label": "湿度", "value": humidity, "unit": "%"},
    # ]


if __name__ == "__main__":
    print(read())
