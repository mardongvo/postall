# -*- coding: utf-8 -*-

from reportlab.graphics.barcode import common
from reportlab.lib.units import mm
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import Paragraph
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib.enums import TA_LEFT, TA_CENTER
import os
import tempfile
from base64 import standard_b64decode
from io import BytesIO


def render_DL_letters(letter_iterator):
    """ Создает pdf файл во временной папке со страницами в виде конвертов DL

    :param letter_iterator: итератор, возвращающий кортеж (letter_info, from_info)
    :return: путь к файлу pdf
    """
    # грязно, но обычно этот шрифт есть
    pdfmetrics.registerFont(TTFont('TimesNewRoman', 'times.ttf'))
    #
    hndl, path = tempfile.mkstemp(suffix='.pdf')
    # закрываем хэндл, иначе получим ошибку при открытии pdf файла
    tmp = os.fdopen(hndl, 'w')
    tmp.close()
    # do draw
    c = canvas.Canvas(path, pagesize=(220 * mm, 110 * mm))
    for letter_info, from_info in letter_iterator:
        render_DL(c, letter_info, from_info)
        c.showPage()
    c.save()
    return path


def render_DL(canv, letter_info, from_info):
    barcode = letter_info["barcode"]
    from_name = from_info["name"]
    from_addr = from_info["addr"]
    from_index = from_info["index"]
    from_fio = from_info["fio"]
    no_return = "Возврату не подлежит" if letter_info["no-return"] else ""
    dst_name = letter_info["recipient-name"]
    dst_addr = ", ".join(map(lambda k: letter_info[k],
                             filter(lambda a: a in letter_info,
                                    ["region-to", "area-to", "place-to", "location-to", "street-to", "hotel-to",
                                     "house-to", "slash-to", "letter-to", "building-to", "corpus-to", "room-to"])
                             ))
    dst_index = "%06d" % letter_info["index-to"]

    textlines = [
        {"x": 20, "y": 100, "w": 65, "h": 15, "fontsize": 10, "font": "TimesNewRoman", "alignment": TA_LEFT,
         "text": from_name},
        {"x": 20, "y": 85, "w": 65, "h": 15, "fontsize": 10, "font": "TimesNewRoman", "alignment": TA_LEFT,
         "text": from_addr},
        {"x": 55, "y": 80, "w": 30, "h": 5, "fontsize": 10, "font": "TimesNewRoman", "alignment": TA_CENTER,
         "text": from_index},
        {"x": 20, "y": 80, "w": 30, "h": 5, "fontsize": 6, "font": "TimesNewRoman", "alignment": TA_LEFT,
         "text": from_fio},
        {"x": 20, "y": 70, "w": 30, "h": 7, "fontsize": 8, "font": "TimesNewRoman", "alignment": TA_LEFT,
         "text": no_return},
        {"x": 115, "y": 50, "w": 85, "h": 15, "fontsize": 10, "font": "TimesNewRoman", "alignment": TA_LEFT,
         "text": dst_name},
        {"x": 115, "y": 30, "w": 85, "h": 20, "fontsize": 10, "font": "TimesNewRoman", "alignment": TA_LEFT,
         "text": dst_addr},
        {"x": 105, "y": 18, "w": 30, "h": 5, "fontsize": 10, "font": "TimesNewRoman", "alignment": TA_CENTER,
         "text": dst_index},
        {"x": 95, "y": 84, "w": 45, "h": 5, "fontsize": 10, "font": "TimesNewRoman", "alignment": TA_CENTER,
         "text": "%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s&nbsp;&nbsp;%s" %
                 (barcode[0:6], barcode[6:8], barcode[8:13], barcode[13:14])},
    ]
    if "mail-category" in letter_info and letter_info["mail-category"] == "ORDERED":
        textlines.append({"x": 95, "y": 75, "w": 45, "h": 5, "fontsize": 10, "font": "TimesNewRoman",
                          "alignment": TA_CENTER, "text": u"Заказное"})
    for i in textlines:
        ps = getSampleStyleSheet()["Normal"]
        ps.fontName = i["font"]
        ps.alignment = i["alignment"]
        ps.fontSize = i["fontsize"]
        par = Paragraph(i["text"], ps)
        w, h = par.wrap(i["w"] * mm, i["h"] * mm)
        par.drawOn(canv, i["x"] * mm, i["y"] * mm)
    n = -1
    for ind in dst_index:
        n += 1
        if ind not in _INDEX_IMAGES:
            continue
        canv.drawImage(ImageReader(BytesIO(
            standard_b64decode(_INDEX_IMAGES[ind]))),
            (20 + 9 * n) * mm, 10 * mm)
    # barcode
    if barcode > "":
        ift = common.I2of5(value=barcode, checksum=False, bearers=0, barWidth=0.35 * mm, gap=1 * mm, barHeight=10 * mm)
        ift.drawOn(canv, 95 * mm, 90 * mm)


# изображения цифр индекса в формате jpg (base64)
_INDEX_IMAGES = {
    '0': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAALCAAtABgBAREA/8QAGAABAQEBAQAAAAAAAAAAAAAACQgHBgr/xAA3EAABAgUBBAUKBwEAAAAAAAAGBQcECAkWFxUAAxQYChMZJicBAholOWdpiam4KkVHWoaZ1uf/2gAIAQEAAD8ALyoT6SPz9Tw4L7b7CXN/Mth3E/PlizFmaDXH2NLP7pY/tLSLNtbu5bmm6J6s4XaQPxTXx/vqKbV/T29JH5+pHs6dt9hLm/lpzFlnnyxZizNAVkHJd4d0sf2lq95XT3ctzUtb9WcVt7/KhNVNrKdp3LS1pZLtN/Mw5s2GZcSN1J00Y48x3HYKRwoiPeMEVJwwkgieGHzaGXYe2U8j6lHQSdTWdIgkvd7+LkDt9Pgr1/v65P8Asm1f09qqbWVEjuZZrROXab+WdzZT8NZbbqcVoxxmTuBzqjmpEBcGIprhmxBDcSPhMSuxFzJ451yOvDCmjavBKm838JIFQ/26/R1fm5fZ4E7N9rqwSEeniKhokE37gaE6UMZNad7q70eNay5k9PacsU1MJH4nhiA2bpVUnSHYV4ATzbXctlN+mJjmw66stcENMQTFQKtd0gUFBRkfCwkLH6OgmHBwmjJw4KiYqOSVFqOPDIyPI8NBpCCPoSRBwaWjIyXBwqclp0LDQMDDbiG3G63Xm8/VnQlgorCUIBkdT9XICJv60iEhJWUjtjtTWFeRkbT0xPzW1qYtuaz/ABsbEbiGyk3SMrnbf9bdgimR5AkJ8LvX+1J07j4WzW/tLIGm63ksjuPFmLNXvK1sT6ZkDNvh7jS8LcxZ4xZYu3wL2AGkwa5KrCV33F41v1G/m/otmuoNOf5XayPuqRkkXeNbR0rcDslN/Fcf14af2iK3iOeemkVuIeo6ZC6BUP8Abr9HV+bl9ngTs33eMnI/1AbpMblwPdZHDj9jkc1n87LUdv0YtO/cu6e9dNl/zVklXxYEGnh7dfpFXyjfs8Nttgqr0qHMqHuZKS7rRTbD8qxtKsPzWCe73hZKm3s2wq4wrNs3oY1DiDJM3brmaC3cYPxjdoRUKrKMVCpsnL6cbRPl8kMkxKTDxEXj/Z4V1/3FX0jZPP8AbbUBTUpqPtJc+07ky8y87nO69s7vLZepry2B0tmi8tgcdgA53cADsqElHURIqQUn1SgifB2nx8frqmuxsbD/AP/Z',
    '1': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAALCAAtABgBAREA/8QAGQAAAgMBAAAAAAAAAAAAAAAACAkABgoL/8QANRAAAQMDAwMCAgYLAAAAAAAABgUHFwQIFgMJFQIUJwAmGCUBChMZGmcSJCo5RUdphompuP/aAAgBAQAAPwBXm4T+JH+Pq+GC/vvoS+L+5aHYn+PKLIsmg1j6NMP9pR/iXEYbi3tzHON4T5Z2voQP2pr+v9/sU9F/t7fiR/j6senT776Evi/tpmKWfjyiyLJoCpBkvMPaUf4ly+ZZT7cxzkub+Wd166fZqZEYr3vBNO4Dldq35+ZaGFKTWUHIkYdjmOtPRyK5YD+g4Dr84p4ApKHYNYnYcRyk5ba90I5VMyI8j4SJ3A4yQMNzDkmsxzHIskKWO1kvLY/y3wXxuLSnKfzeNIS8xegA29t221jcyO7lgC2ymcCorbUoao3OIyLRbqtBFIjeBHNa3qHG6NW4clxB9xI7IG7MAouNRitrWsJlhK0CNlj92myWx8/VTfWk9O1H9bRU1Uof1lejZ98E+hXKllCpdKk5OUjS3qoVEpGuMo6roCWrH1mpSUesJmUIaGoKn+UUETOg6qo0i2s60a7OE/z/ADy7/TyuFYTYS4RA1e1e1ZBrAu4fuHgutodCjcqo9GhT66/ZlZkv69PWJC6PrqRWaGg67r6GgrCq2Kq2ioKGissgshgZenf9nJgWata3c9+i3y3xvR9q2basf2hxkFBRnR1+hOSE7otDPa6sqamsrqisV10gXVesUSIsLCFRVioyKlZZKytZWSRZVFSrKDeQtDunvuhK123i59v2Bb9wm/uQ1bqgjVepxWzfa4JiUiF9T6WpalHQBpym/oG/MXAqgttbgLgClozwxYcOcxFSxRFcJv3cei2+4Zj7AsmnWtN63tudvjFs+1dtzVkGiEAqAMuKVdCikM10NnUEtYd1KFXNdWai68C7cHWKI+WIBC4CtrmQqrLNxpW+Sy6KyqNBVpg2mDWSt4TffcXvW/Uc+b/ZbNeQac/ldrK/KrGSRd71tHSxwOkpv6rv/tw0/wARFcxHOtNIscQ+R4ylf8pZHKYb2sgYlH7l83xsWRZkeRtPi2Zcv5tkDjMwjSPvFmOSzMXu2C/U9xk5H/MBukxuXA/KyuHH7HK5rP77LUdv0YtO/wAl3T1XTZf+Kskq+WEg7eH79f6xV/iN/wCPDb0396mVljmfk1v6rytv7+sr5qYKaPtZojj5Ms+RwTmLf1jBPPrBfqM99i3HkduY59z3/jXTyPusyb/EpA5LhI0I8jiyLOIw3KZY4yQJt8hSXh+ORZ4difLfOnoILS7Dyq3i8K/C8o6eofc42vxH7LaYxFRNo1FrhUEKrUGMUmiIVkZ+lYdp1levH3PV1asLUYZVK/qUW6TummFq4scSp0tUq1//2Q==',
    '2': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAALCAAtABgBAREA/8QAGQAAAwEBAQAAAAAAAAAAAAAACAkKBgcL/8QAORAAAgIBAwICBQYPAAAAAAAABQYEBwgDFhcJFQIYAAoUGSYBExolKGkkJyo0NTc4REdlZoWZqef/2gAIAQEAAD8AV51CfpI/n6zh4L999wl5v8luHeJ/PlxZxZzQ68fcabP+EuP9pdo2btb4c2523sn1Z7L6CB+VNff/AH+xT0L/AKe30kfz9YPc6e++4S83+NPMXLPny4s4s5oSuQeS94fCXH+0u77y3T8Obc7l3v6s9q9PQ8znz68jnF32K8/8wOUN7fsMY4+YDjvZW0f1o/GSltLdu7fgn9Id+2y3fmnZfwkAPf6fcr9f7/HJ/wBk9C/6e3VTqzqJPeS1WqeO2X+M9m4n8Nct11mLUa5TL3B51DurEhexqI2w3Zgje0r6TJOyNzD1z54OeWCYbu8Ipqa8Q3zQ8dqX7WhTVFL+sXh0/eA+Cck0o1HWocOJOmPUgoKDZGQ5XgSarXzMkSHmM1KMMGQ1X8RAqb0nSoYjGt60Z2g76YZGPt6iQ7JCr+wOxWlGcqte9Ld4ebVm5h4+p2wmTSV+T7MwO1dFSVpLsW4ETw7XsulNcYMs2OdM1ciHpiKaqhda71gVFRVlfS0lLX+joppycphhy4qqaquYVNodeWVleDxoYgCvghEOGLDBhcOKOFjosaDBjaEbQ0tLwt/vOFrsjVsUFqr5F2bsYMo4SqnScvLlxwamTX1CNGB/l1Qy9UQE8Xhr8MueAC2bLxahzrlxBIsSnBqACbk381aUbftj81IWgzOD1Cp9LptLYDJtxsxsuQiuaCnQS5TUlvYbYZo5ir4asBYAVrQ5ikZTSj3FSxdNRZN4Trh0GTQ1aQ8M8XQdvTznZ2dY/PlcVtr1LlR7vWLV+rKN/Pb28vVO3Bj/AGZYVfBWgQiW0Yx/MW0iOq/TtxP9P1XyVtRwXpiem21WNz1TWNDr82aCE1QnpwZmBLptLp+5GyzHE2ZppcoJT0FwjV5iOzWwwt8mHawFgBK0N7KJplSmRaaFpcW4Z14SdBk0KQ1fDNF+NP1ly0/4gUv0BKXsD+o65tPq1WnXLH/Z21ExARG0N/KmMqxiv3G/IP2IqXUFT0EJqmoqessCXTaXT9NqdZpwQNTS5QSnoLhG0A8hZqdeUI0O1gLACVoaILcgzbDi00LS4tPQaPjaDJoXfpeFUPWs6QT31dkSoq2Wcv8AyoqSPv7QseMPx/D22YuEO1GKqZl9RJtnhsyrG1cr9cbasDOx2uoxwsiWI9hKteWxdkNtI1iZBcfU+mJ1rkJVWUVF9YFX0tJS18Mppycp9HTCpcVVNVXB0YOvLKyvB22GIAr4IRDhiwwYXDijhY6LGgwY2hG0NLS8J/4H4l5hY8NV1PWZWeC/ni7Wcv1GpqrjGwtozFBqRFWriNtGPlWTLDURIsXs9fnl7WnlFkM2zPCOroj4mycrRtKTYjVq6/8A/9k=',
    '3': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAALCAAtABgBAREA/8QAGgAAAgIDAAAAAAAAAAAAAAAACAkACgYHC//EADoQAAICAgECAwMGDQUAAAAAAAYHBAUDCBcJFgIVGAAZJgoUGiUoaQETJCcqNDU3OERHZWZ1hZmp5//aAAgBAQAAPwBXnUJ+kj+vreHgv333CXq/2W4d4n9eXFnFnNBrx9xp2f8ACXH/AGl5R2b2t8OdueW+SfVnzX2ED9Ka+/8Av+xT2L/p7fSR/X1o9zp777hL1f608xcs+vLizizmgK5B5L7w+EuP+0vN+8u6fhztzzLzv6s+de3Q83n369DnF32K9/8AcDlDvb+BjXH1Acd9ldo/vR+MhLtLu3u34J/aHn3bJd+qeS/lIAe/0+5X6/3/AByf+yexP9K3q/oLq7irhOtc03s+vAlNEAmJ2hi/F4FiQqYlRPXXNxOGV6QgrMZdQQkANUV9HaMGmkTKuxGa4/Xk7NGkRiqHl8B/3VfXZH6tLTLVD+a3hp94V8G8kpQqvSqurrI016kWlVTbGQ5XgCVWP3Mmpp5hMlCGDIKn9Y0ImdB0qHUa1nWGdXCfz+cvX6crC0J0JYRAq+leqyDMC9Q/qHgubB4LHZWx8GCPnv8ATLTK/wA8eZUXo/e1EzBga7XwYLYVuxW2w2FhhuUhchgZum97WfXJE6q3ElI67qhfqVZLfX9EhQnQiKOMR+4wDlUd7GW0aERbL3NlPH3j+NICIoLc4B+HxzWmszszYrlbhGSzdrRmf4FgdeHUPfrfAEV2q2h2z+v+vk1nr9+w9hRxrup0Ls7byJx3CGh3Q4DBS0GmAPlC/wARBZ0FG7TW6BcZiM05kKqUeP6FZbBvAAa+gFarflBmjmuNEtltRfJwdd9Zdd1/Z540bPZ9QoZBF2CDMWwJiwuLiwmsP9cNmKxTa8l3F9cSyI5OSKyurK5uZOf9APqN7f8AUpuNxGztAM6/1YkJcMg+vhvrxN2AEgR3AlEd7Q0BC4xZG7DNkgLR9fkBaPzhwUdPjSKduGjcCRoqjS1LS3WyzBEq94+LMAEVQjowJiALTYWn3IWMwxu7lNDiCE8A5Yq+4jkzYIS+TDa1CQUQtDO7QNuRKZFTVWFxXDOeEnASYEhl8NaL86fylxp/1AS/QES7A/yNctPq1NNckf8As5aCagAhbTf2ojtSOq/kX5B+xFZdARPABFU0FDxkgC02Fp9NiazDqSmTQ4ghPAOWLQp5Aypx4QjQ2tQkFELQwSrMqYthxU1VhcVPQUfGwEmB34vCuHqt9KT3pPAo4RvrixSqzlGU0FfFV3cfqO7j46KFmvWEzBdiqxtDmv442lYFH7iToAajnOPbgfMhmCsbSsTDnWrHhMBKgLAMh4LNT4WmwsgpqQOWYmm7EcwCaCHE1GEB5TjMinaEMWoSCia0OGW0xlVgkULq01FjI+CnsBJgxO/wwBASqkKpp0dTU/fm1+n02AmJiApuxXRUTlS6sWhcEM2aQ3DQY9vlT+W3Y8y0TabtJlxYpixuGhOnNBmSWZlyjX//2Q==',
    '4': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAALCAAtABgBAREA/8QAGgAAAgIDAAAAAAAAAAAAAAAACAkABgcKC//EADYQAAECBAMFBAcJAAAAAAAAAAYFBwQIFhcDCRUAAhQYJwEKJSYZGjlniam4EyQqRUdaaYbW/9oACAEBAAA/AFeZhPrI/P1PDYv031kub+Zaztp+fK1lrL0GtvraUf5St/SWkUbS3lynNN0TwzhdhA/FNfz/AHzFNi/y9vWR+fqR6+npvrJc38tN4rs8+VrLWXoCrg3LrDylb+ktXrKqfLlOalrfhnFbdFyZKe9vZa5h5VZWlRtHgc55Jyx+aRZZBCbGDbPsTlJRlQaSEd8vEyBfcx0G0SB4gOUhQgRtuImMit4ViCqJ3dw6JgMbwoglwSfrIjqPRLTuBplwKNrDUmspynLWXCuxwty6tt/VvQvTaWundPxe2lkusWwwS2z3t7MpMPNVK0lto8DYvJJoPytrL3oTnQbZ9qcmqM17SRbviAmPr7Zug5aQQkAMkJ8cNuPEwcVuisOVQ29uApMeDeLDkuMuDMP9uv3dX4uX0eBOzvtdWCQj08RUNEgm/cDQnShjJrTvCq9HjWsqZPT2nLFNTCR+J4YgNm6VVJ0h2FeAE3aXctlMdMTHNh11Za5EOWIJioFnXd4FBQUZHwsJCx/J0Ew4OE0ZOHBUTFRySotRx4ZGR5HhoNIQR9CSIODS0ZGS4OFTktOhYaBgYbAhsDCwt2v50jTTYlE9mVK9cpstPNyQS/N/mXY5+xw5OQ20mDpqYI+jOsnL1GFwA5ZGajTmj9GRrkQihGuK0KUprDfkcQFQsQRApAZBS1i5A9Ifnr/t1fm5Sef4nYYMiF8HMmUzOM8t+HdZofYE2dIfymizEbATfZvZmRVNFY6Vtzt1uyYZfZqMLCbtxx9x27whVyUZZFezETodOLoZJ7YmLiU6IisbZdUqjumG8LcCkrfuXrem2stZUdRtPS1Zav1tuBplYW0t90spy7N4vNti9p5jJyP9QG6TG5cD3WRw4/Y5HNZ/ey1Hb9GLTv3Luniumy/5qySr1YSDl4e3X7xV8I36PDbZv71MrdjWfBpf1XVZf39ZXrUwV6Ptb0W48GWeo4JrEv6xQnX1gvuN++BbjqO3NufM9/0106j4qsm/pK4GpaJbQjqO1lrNIo2qbsaZcC9vUK5dH05azo7aereumwQSlyHlUvE4U+E5R09Q+5xtPiPyWwxiKibRqLXCoIVSoMYpNEQrIz2rDtOsrx4+56urRhajDKpH7yi3SduwwtHFjiROFilWP//Z',
    '5': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAALCAAtABgBAREA/8QAGAABAQEBAQAAAAAAAAAAAAAACAkABgr/xAA9EAABAgQDBAINDQAAAAAAAAAGBwgEBRYXAwkVABQYJgIZAQoTGiUnKjlnaYmpuCQoNDU3OEVHWoaZ1uf/2gAIAQEAAD8Al5mE98j8fT4bF9d9ZLi/ctZ20/Hlay1l6DW31tKP5St/SWkUbS3LlOabongzddiB5U16/wC94psv8vbvkfj6Y9fTrvrJcX7abxXZ48rWWsvQFXBuXWHKVv6S1esqp5cpzUtb8Gb1t7/MwnNTSzLtO20paWN2d+5hTXYXltInTOkjHFmO46xUnCiI93wRmShhJBE7sPm0NPYemZeR9xk8hJ5nOdIgpXh48WQOv09Svn/fxyf7Js/2MP6447o/Mrf+z+19E/fnbjw/3ErWrvsu5yLatpKkudvq/QamEfpetfJgBmH+fX7XV9rl8HgTtb7XZwSEeniMw0SCT9QNCVKGMktO8Kr5PGpZU0vl6TlkzmYSPxO7EBsnU1mSpDsKsAJ0aXUtFMeWSxTYeezlLuATgDBE9VMmGQAET8FHxdv7dQMclQU3ucJ/ogIFEa+S8KBINa4LpQyZGyfhMFExkMAN7CpNLJw27UyMsI+lij7jQCFl0gM4JmDv3Muxy61bZCprQBhbWzJ/mAY/TT10StOATCcGoI4VNkZQE0Lk1xmvw0AtsLbWWGPRw5oooOep1OEwOzVI5lLiLszOcwMP2d5U16gH3im2yfXuO/dI7HMVSR4ce0AmLW0J/l/44YoTFjFwBI3FRwRySbLMvwoXBmCrymFQlMdREioYxMVRQQCB5wcwvZgZaUEShiQWlcQNW+mVR3TDd1uBSVv1L1vTbWWsqOo0npastX8dtwNMrC2lvvFZTl2bxc22L23MZOR/mAnUsTlQPRZHDi9jkcln77LZOn8mLTv0Lqniqmi/4qiU18bEQcvDz6/bFXsjfg8Ntl/mOMfcw8S3XDe8pP2haKn66pOrdasUb29G86WLpa6oE0jb6xMLRyfx9tcOvw2T74OKzvA5W8tjKCGu5EDq8M9f9RV7o1nn922QGWplqLsy5dnuOXcu9zjdW17vDZWprw2BzbNF4bA47ABzlwAOyoSmOoiRVIZT4JkInudJ7/H67M57GxsP/9k=',
    '6': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAALCAAtABgBAREA/8QAGgAAAQUBAAAAAAAAAAAAAAAACAAGBwkKC//EADoQAAEDAgMEBAoLAQAAAAAAAAYEBQcDCAkWFwIUFRgAAQomGRolJzlHZ4mpuBIoKkRFWmVmaYWG1v/aAAgBAQAAPwCrzEJ8ZH5+r4dC/DfaJc39y2juk/PlpZpZrQa6faaZP7paf5S4Rk3K3dzLnDeCeTN16CB9qa/n++Ip0L/D28ZH5+rHtdPDfaJc39tOsWrPPlpZpZrQFag6l5w7paf5S4vnLNPdzLnEuN+TN66dPs1MiMV33gUTyBJW6x+fmVDJTlFiDiJGHZcy7E6PUWSwH6EgSvxxzyA5OG4RY3ZOI9UpLjXehHNTfLJeoAVAmfzoMIAuNgsgeaJjMJYVw0ORmJxmOQ0plkhn4md3iVEbuww+xO6NZEDyodGJLITXISVSSro9oQTQqzPsiBhn4lse4pUNPdwcM2/3PxDDaUg2hkMOrjRCMwtul5xba7khLVMVIweXJLdyEfBndv2B0kLHFuYxWuVV14oMPJGSB0htYeUEjvoIDSmMycfuEfiI/H9v9xT6Ryaaxa8UshAjcRwGQGrgtusWuaCMoOj+kiHURAfxaa7Oy8TVlcckccc2wftkP+pZnB86faXJT9YEL4AkLyB+445lPFqlOOSP+nLQS0AELWb9KI3UjavuM+IfqRaPo4AwSPZTJhkABI/BR8Xt/t1AxxqCre3iP+CAgURz43hQIjmtFtJoyNo/CUSlYmALewpmbHi27iZGWEe1VH7jQBK3Zoe0sw3creBdBhCWEwAfD7a0XRkF5bzJMOy5KE3x9a/O7dbWP27XAtIncO3wOtoGxGPpUwWR0BdSyUKJUNED51OAgTBDuo6ytsL8TE+04gQqMgoKM9nhCwkLH2YTDg4TZsQMcFRMVHG5MzjwyMjzOmRtDCPsTQjRtbMzNaNK3NbclTIUKagmoUqWy4MH29y7+6S7HEViS8NfaATFttEf4f8AXDJCsWMbgCS3GRwS5KNpmn4ULgyjL0mFQk48REioYqVZFBAIHeDlL1oW0oIpDEguK1A0sQ/06/Z1fe5fJ4E9Lvu8ZOR+sCOmyOZA9li4cnscXRZ/uy1nj9mLTv2LynVlOF/xWEnXzsUg4eHp1+0Ve6N+Tw26TBir4VEmYh8mWky7EV2w/asbWrD91gnTqFlqce3bCsjCt20ehkUSIMk0dyuZsMdrB9ZHbEVCryzFQqbNz+3Gynr6kzSpaU6hXD/g8Mdf8xV8I2zz/tuhAYamGpO1l07XuXL3L3uc7s23u8tmdTXlsDrbOC8tgcdgA53cADsqEnHiIkVMLT5JYRPc8p7+v465vq1an//Z',
    '7': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAALCAAtABgBAREA/8QAGQABAQEAAwAAAAAAAAAAAAAACAkABgoL/8QAOxAAAgEDAgQEAAcRAAAAAAAABgcFBAgXAxYCCRUYABQmJwETGRolZ2kKJCgqNDU3ODlFR4aJmam45//aAAgBAQAAPwCXnMJ+cj9/V8OC/lvsJd39y2HcT9+WLMWZoNcfY02f6Sx/tLpGzdrenNudN6J9GeV8ED8aa+3+/wAinhf8vb5yP39WPZ0+W+wl3f205iyz35YsxZmgKyDkveHpLH+0ur7y3T6c251Lrf0Z5rx6Hl89/XY5i78Cu/8AvAyhvb9Ri3HuAx3sraP6UfWQltLdu7fRP5w69tku/JOi/fIA+X0+xX5/39uT/snhP8q3m/oLm7irhOrc03c+vAlNEAmJyhi/F4FiQqYlRPHTMxXDK9IQVmMuIISAGiI+DlGDDVFZFyIzHH68rtamqKYqo9Xgf81Hx2o/VpKasUP60vRp94R9DOVKUKp0qjo6SNLeqiUioa4yjquAJVY/M1MTD1hMlCGhqCp/SMCJnQdVUcRbWdaNd1wn8/nLz+nKwrCbCWEQKvlXqsg1gXmH8w8F1tDgkblZHg0KfXn7MrMp/Xp6yInR+diKzQ0Gu19DQlhWbFZbRkJDRmUhMhgZend62e3JE2qzFSkbd1Qv1Kslvb+iQoTgRFHGI/MaA5FHdxktTURFcvMyVePvH40gIigt1wD4eOtaazOzNiuVuEZLW3WjNfwRg59ka/bibh+W3y0ky2yBOC3MHH79Rh4S4yemgLIsNZoFSK93VqEqZyO0zYJBh96VMFwL0sc8ih3IwloKyszQDA4XKk3fiEf1v0Ck461per23O3xFp9V23Ksg0QgFgBlilXBIxCa4FnUEtYd1MFXK6s1J1wTtwdZIj5ZAELAltcyFZaZuNK3lMtGZlFBV5GMWOZxVvHSIk/Ly5lbBa4xa6jT11JU9BXhjjyRecpFkQaC1giFhNKnyOp0JjSU91I8PDpVdfHQs3DmIiLxFvgLQ6soOYf8At1/udX+rl/p4E+Lfeoycj/iAuoxcsD6rK4cfY5XKz+ey2HX8MWnf1LtPVaaX/eqSlfdjRu48pmXmsgbSx+tOidSxZizce42zunZvSPe3IHTNn5LyD7WbcxPh31bnTwAL4OXH3iXMWa3IZFX8L2hL++sKxI2UVnRWOfvRt7pkV5Jlj+UVr59fh3lesGQB8ZUZZHKySCNxgXnNy6T/AOmtPcfmt5L/AGlkDqXRMaEe48WYs6Rs3dOWOmZAzb7hZL2ftzFns7ifdvvp44+AgJVCFVadHVan582n0+mwExMQFNyK6KicqXUi0Jghra0hmGgx5fVT+rLseslE2m5SsmJFMSMw0K6uaDMqWZq6o1//2Q==',
    '8': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAALCAAtABgBAREA/8QAFwABAQEBAAAAAAAAAAAAAAAACAkHCv/EADcQAAEDAgQDBAgEBwAAAAAAAAYEBQcICQMVFhcAFBgCChkmARMlOWmJqbgaJypnRUdahpnW5//aAAgBAQAAPwCXlwn8SP19Vw7F+N9sl1f1LbO7T9eW1m1m9Brt9tpo/wApbf6SyjRulvLmnMtyT2ZyvBA/VNfH++opwv7e34kfr6oe308b7ZLq/pp3i3Z68trNrN6ArcHcvWHlLb/SWb6y1T5c05mWd+zOa47/AC4TdTiy3ad00xaWU7Vf1MSbVhvLtJHVHURjkzHa7YpnCiI95wRcpDCSBTyw+bJn1PplvI/Us7CTubzlCJrw8dWQPH0+Cvf+/wAcn/ZOF/b2upxZcSO6lotE6dqv6Z5NpP2a3bjqsWIxyGTtDvqzmpEBcmItshmxAm5kfCVL6o1M3jnrmd+GHNmzdE6YmOkIFw/36/d1fm5fZ4E8W+z14JCPLxFwyRFH8gZFKSYyi07wtXs62LNTN7fE5Y5uYSPqeWIDaOnVylIdSzACdnS8lwpjtjZJqd9eYuhDbEExUCvXd4FBQUZHwsJCx+zoJhwcJszcOComKjlFRazjwyMjzOmRtDCPsTQjRtbMzNaNK3NbclTIUKbATYGFhdnAL7wzUqaXOLGgdSCph9HUGWD92UZCFk7lk3gUZpW59pbjFrkBS6HVNryOTsFkGBGyovxQAsi8hYiockLsizwjeWvDR4y7AT/6pr4AP1FODBYhLJ9PbnF8s6qcJqYDSZDQftNFj0Y0XvJoR0vlgqR0tyc8RYTRAQyCpWFL8PvsUrAl0WvKtYqbnQgVPC4dU443jtOL2k/cP9+v3dX5uX2eBPFvvMZOR/zAjpsjmQP2sXDk9ji6LP77LWeP2YtO/wBl5TxZThf+Kwk6/mxEG3h79fvFXyjfs8NuNgur2qJMuHyZSTLsRVbD9KxtSsP1WCeHiFlKce1bCsjCtW0ehkUSIMk0dyuZsMdrB9ZHbEVCryzFQqbNz+3Gyn0+hM0qWlOoV4/4eF9f+oq+kbR5/u3CAtqW1J2ounatypepetzrdm2t3ps1qa9NgdTZkvTYHHYAOeXAA7KhJxzESKmFp9ksInyek+fX565vq1an/9k=',
    '9': '/9j/4AAQSkZJRgABAQAAAQABAAD/2wBDAAEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQEBAQH/wAALCAAtABgBAREA/8QAGAAAAwEBAAAAAAAAAAAAAAAACAkKBgD/xAA2EAACAgAFAgQCBQ0AAAAAAAAGBwQFAwgJFhcVGAACChQZJhMaJSdpKCo5REdlZoWJmam45//aAAgBAQAAPwBXmoT9ZH7+s8PBfxvuEu7/ADLcO8T9+XFnFnNBrx9xps/5S4/2l0jZu1vlzbnTeifZntfAgfnTX4/3+RTwX+nt9ZH7+sj3OnxvuEu7/LTzFyz35cWcWc0BXIPJe8PlLj/aXV95bp+XNudS639me68X+ahOqmrNO07y0q0sy7Zv8zDNzYcy8SLrJ0oxxzHc7gqnCiI994I2TDCSCT7YfNo17H2zXkf0NPQk9nc9IhVeHjyxA+Pp+Cvr/f25P+yeC/09tVNWaiR3mWVonl2zf5Z2blP4a5bXWcVRjiZO4POtOakQF7MRrWGbEEb3I+Eyb2RuavHPpqe+GLOm6vCtMTHiCBqH/p1/Tq/1cv8ATwJ8O+67cEhH08RsOiQl+wOhNKMZK07wt3081Wbmr69TllnZhI/J9sQGy6tbJpDsVwAnl2uy0pj1lYzY97cq5EOmIJioFrXeoFBQUZHwsJCx/R0Ew4OE6auHBUTFRzJUW048MjI9TxodRQj9FUQ4dXTU1XDi11XXRY0GDGwI2BhYXlz+tIps2JRns0pXXlNy093JBl+X+pdjn6OHM5C2yYNOzBHonUnl6mFwAyyM1GmaP7MmsiJYTWKoaqzuF+RyAqLIIgUgMgq6xdAWanetcBCpMdHXp+h8LCQsfuSwxMSzWLyVDgqJio5XSbghJiYhuBKHUUI/RVEOZaXNzaTItdV10WTOnScCNgYuL5Rg9OXmVO8/ebHVy1HiZI9vglnD7CMdcL2wZNOfXEmnQK2eCBIC6sxvNQghbcL+4LQS5qKJiyVzRgl6djbSWQmRFJalmdHHqXT4swAIqhHRgTEAWmwtPuQsZhjd3KaHEEJ4A5Yq+4jkzYIS+TDa1CQUQtDO7QNuRKZFTVWFxXDOeEnAJMBIYvlmi+9P1LjT/aAl9ARLsD+I1y09Wpprkj/k5aCZQAQtpv3UR2pHVfqL8g/kRUugIngARVNBQ8ZIAtNhafTYmsw6kpk0OIITwByxaFPIGVOPCEaG1qEgohaGCVZlTFsOKmqsLip6Cj42ASYDvwvKuHVb0pPik8CjhG+uLFKrOUZTQV8VXbj7jtx8dFCzXrCZguxVY2hzL+ONpWBR+4k6AGo5zjtwPmQzBWNpWJhzrVjwmAlQFgDIeCzU+FpsLIKakDlmJpuxHMATQQ4mowgPKcZkU7Qhi1CQUTWhwy2mMqsEihdWmosZHwU9gEmBhO/y8AgJVSFU06Opqfvza/T6bATExAU3YroqJypdWLQuCGbNIbhoMe3xU/i27HmWibTdpMuLFMWNw0J05oMySzMXFGv/2Q==',
}
