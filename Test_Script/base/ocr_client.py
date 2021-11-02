import base64
import json
import os

from io import BytesIO

import requests
from PIL import Image, ImageOps

from Common.log import log

SERVER_ADDR: str = "http://15.83.248.240:5000/predict/"


def check_grayimg_main_color(img: Image) -> str:
    main_color = sorted(img.getcolors(),
                        key=lambda ret_val: ret_val[0], reverse=True)[0][-1]
    if abs(main_color - 0) <= abs(main_color - 255):
        return "black"
    else:
        return "white"


def get_results(server_addr: str = SERVER_ADDR, image_path: str = r"test.jpg", enable_proc: bool = True) -> dict:
    if not os.path.exists(image_path):
        raise FileExistsError(f"Cannot find this image: {image_path}")

    image = open(image_path, 'rb').read()

    if enable_proc:
        image = Image.open(image_path)
        image = image.convert("L")

        main_color = check_grayimg_main_color(image)
        if main_color == "black":
            image = ImageOps.invert(image)

        buffer = BytesIO()
        image.save(buffer, format="PNG")
        image = buffer.getvalue()

    base64_image = base64.b64encode(bytes(image)).decode('utf8')

    headers = {"Content-type": "application/json"}

    image_data = {
        "image name": image_path,
        "image data": base64_image
    }

    try:
        response = requests.post(url=server_addr, headers=headers, data=json.dumps(image_data))
        log.debug(response)
        if response.status_code == 200:
            return json.loads(response.text)
        else:
            log.debug(f"[ocr_client][get_results] {response}")
            raise ConnectionError(f"[{response.status_code}]Cannot connect this server:{server_addr}.")
    except Exception as e:
        raise e


if __name__ == "__main__":
    # res = get_results(server_addr=SERVER_ADDR, image_path=r"C:\Users\LiRengui\Work\Temp\proc_pic\EFI.jpg")
    # print(res)

    # res = get_results(server_addr=SERVER_ADDR, image_path=r"C:\Users\linlen\Desktop\settings in F10\efi.jpg")
    res = get_results(server_addr=SERVER_ADDR, image_path=r'C:\Users\Administrator\Desktop\view.jpg')
    for k, v in res.items():
        # print(k, v)
        if k == 'labels':
            print(v)
            break
