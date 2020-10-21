from phone_control import OperateAllPhone
import random
import re, os
import time

pattern_model = re.compile('(?<=model:)\w+')
pattern_wm = re.compile('(\d+)x(\d+)')


def get_phone_list():
    phone_model_list = os.popen('adb devices -l').read()
    phone_info_list = {}
    pattern_1 = re.compile('(.+?)device:')
    tmp = re.findall(pattern_1, phone_model_list)
    for item in tmp:
        phone_id = item.split('device usb')[0].strip()
        phone_info_list[phone_id] = re.findall(pattern_model, item)[0].lower()

    print(phone_info_list)

    operate_phone = []
    for phone in phone_info_list.keys():
        operate_phone.append(phone)
    return operate_phone


def get_device_wm(device_ser: str):
    result = os.popen('adb -s {} shell wm size'.format(device_ser)).read()
    return re.findall(pattern_wm, result)[0]


class Phone:
    ser_id: str
    width: int
    height: int
    phone_opt: OperateAllPhone


phone_list = []


def tap_cat(phone: Phone):
    half_width = phone.width / 2
    start_height = phone.height * 0.478
    pos = (half_width - 100, half_width + 100, start_height, start_height + phone.height * 0.2)
    phone.phone_opt.tap([int(item) for item in pos])


if __name__ == '__main__':

    for phone_ser in get_phone_list():
        n_phone = Phone()
        n_phone.ser_id = phone_ser
        wm = get_device_wm(phone_ser)
        n_phone.width = int(wm[0])
        n_phone.height = int(wm[1])
        n_phone.phone_opt = OperateAllPhone([phone_ser])
        phone_list.append(n_phone)

    for counter in range(1000):
        for phone in phone_list:
            tap_cat(phone)
            time.sleep(random.randint(1, 5))
