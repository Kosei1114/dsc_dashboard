# このファイルの役割：
#   BH1750 で照度（窓からの日射）を測ります（I2C、アドレスは 0x23）。
#   書き方と約束ごとは、同じフォルダの README.md を見てください。
#   動作確認：bushitsu-dashboard/ で `python -m hydroponics.sensors.bh1750` を実行すると結果が表示されます。


def read():
    """照度を測って、値のリストを返す。読み取りに失敗したら例外を投げる。"""
    # TODO：ここに BH1750 から値を読む処理を書き、下の raise の行を消す。
    #       センサー用ライブラリの import も、この関数の中に書く。
    raise NotImplementedError("bh1750.read() はまだ書かれていません")
    # 読めたら、次の形で返す：
    # return [
    #     {"metric": "light", "label": "照度", "value": lux, "unit": "lx"},
    # ]


if __name__ == "__main__":
    print(read())
