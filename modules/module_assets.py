import base64


def img_to_base64(path):

    with open(path, "rb") as f:
        return base64.b64encode(
            f.read()
        ).decode()


# ---- картинки ----

airduct = img_to_base64("assets/airduct.png")

fan_on_base64 = img_to_base64(
    "assets/Fan_Alarm.png"
)

fan_off_base64 = img_to_base64(
    "assets/fan_normal.png"
)

filter_pic_base64 = img_to_base64(
    "assets/filter_14x46.png"
)

fan_300x300_base64 = img_to_base64("assets/fan_300x300.png")
