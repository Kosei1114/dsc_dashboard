# このファイルの役割：
#   使うセンサーの一覧です。センサーを足すときは、ここに import と1行を足します。
#   collect.py は、この一覧にあるセンサーの read() だけを順番に呼びます（フォルダの中を自動では探しません）。
#   どちらの一覧を使うかは .env の HYDRO_USE_DUMMY で切り替えます。

# 開発用（ラズパイのないPC）。ダミーセンサー dummy.py ができたら import して入れる
DUMMY_SENSORS = []

# ラズパイ用。read() ができて、ラズパイで動作確認できたものから足す
# 例：
#   from apps.hydroponics.sensors import bh1750, bme280, water_level
#   PI_SENSORS = [bme280, bh1750, water_level]
PI_SENSORS = []
