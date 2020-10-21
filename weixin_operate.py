# from phone_operate.config import BTN, CROP_RANGE, UI_WORDS
import traceback

import os
import re
import time
import json
from random import randint

from application.managers import device_manager
from phone_operate.phone_control import OperateAllPhone
from phone_operate.vc import VC
from instance import redis_instance
from crawler_assist.tidy_req_data import TidyReqData
from pypinyin import lazy_pinyin
from instance.global_instance import xcx
from library.TfException import TfMongoException, TfException

from phone_operate.openid_phone import OPENID_PHONE


class WeixinOperate():
    """
    实现对所有在线手机进行操作 以获取微信请求参数
    """
    busy = 0

    def __init__(self, phone_list):

        phone_model_list = os.popen('adb devices -l').read()
        pattern = re.compile('(?<=model:)\w+')
        phone_info_list = {}
        pattern_1 = re.compile('(.+?)device:')
        tmp = re.findall(pattern_1, phone_model_list)
        for item in tmp:
            phone_id = item.split('device usb')[0].strip()
            phone_info_list[phone_id] = re.findall(pattern, item)[0].lower()

        operate_phone = []
        # print("设备列表", phone_list, type(phone_list))
        for phone in phone_list:
            print("手机查找")
            print(phone)
            print(phone_info_list.keys())
            if phone in list(phone_info_list.keys()):
                phone_json = phone_info_list[phone] + '.json'
                phone_json_path = os.path.join('./phone_operate/view_config_list', phone_json)
                print("config file path {}".format(phone_json_path))
                with open(phone_json_path) as file:
                    self.data = json.loads(file.read())
                operate_phone.append(phone)

        # 这里可以接受多台设备，
        if len(operate_phone) == 0:
            self.busy = 1
            return
        self.oap = OperateAllPhone(operate_phone)
        self.home_weixin = {}  # 桌面微信位置
        self.main_bottom = {}  # 微信主界面底部四大按钮位置
        self.gzh_folder = {}  # 公众号文件夹位置
        # 找一个手机的界面作为眼睛
        self.vc = VC(operate_phone[0])

    def back_to_weixin_home(self):
        print("回到微信首页")
        self.oap.back_to_wx_home()
        time.sleep(5)

    def home(self):
        """
        :return:通过多次点击BACK按键回到主界面 之所以不直接点击HOME按键 是需要层层返回微信到主界面
        """
        for i in range(6):
            self.oap.key(self.data['KEY']['BACK_KEYEVENT'])
            time.sleep(0.3)
        return self.data['KEY']['BACK_KEYEVENT']

    def home_to_gzh_search(self):
        """
        :return:从主界面到公众号搜索
        """
        # # 点击微信图标
        # self.oap.tap(BTN['EMU_WEIXIN_ICON'])
        # time.sleep(0.5)
        # 点击通信录
        print("点击入口")
        print(self.data)
        self.oap.tap(tuple(eval(self.data['BTN']['TONGXUNLU_BTN'])))
        time.sleep(1)
        # 点击公众号
        # self.oap.tap(self.data['BTN']['GZH_FOLDER'])
        self.oap.tap(tuple(eval(self.data['BTN']['GZH_FOLDER'])))
        time.sleep(0.5)
        # 点击搜索
        # self.oap.tap(self.data['BTN']['SEARCH_BTN'])
        self.oap.tap(tuple(eval(self.data['BTN']['SEARCH_BTN'])))
        time.sleep(1)
        return 0

    def home_to_search(self):
        """
        :return:从主界面搜索
        """
        # print("zhujiemiansousuo ")
        self.oap.tap(tuple(eval(self.data['BTN']['SEARCH_BTN'])))
        time.sleep(0.5)
        return 0

    def search_gzh(self, nickname):
        """
        :param nickname:待搜索公众号名称
        :return:
        """
        # 输入拼音
        # text_to_pinyin = "".join(lazy_pinyin(nickname))
        text_to_pinyin = "".join(nickname)
        # print(text_to_pinyin)
        self.oap.text(text_to_pinyin)
        time.sleep(0.5)
        # 进入账号
        # self.oap.tap(self.data['BTN']['FIRST_GZH_SEARCH_RESULT'])
        self.oap.tap(tuple(eval(self.data['BTN']['FIRST_GZH_SEARCH_RESULT'])))
        time.sleep(0.5)
        # 键入主界面
        # self.oap.tap(self.data['BTN']['PROFILE_BTN'])
        self.oap.tap(tuple(eval(self.data['BTN']['PROFILE_BTN'])))
        time.sleep(0.5)
        # 上拉
        self.oap.roll(0, 500)
        time.sleep(0.5)
        return 0

    def search_xcx(self, nickname):
        """
        :param nickname: 待搜索小程序名称
        :return:
        """
        # text_to_pinyin = "".join(lazy_pinyin(nickname))
        text_to_pinyin = "".join(nickname)
        self.oap.text(text_to_pinyin)
        time.sleep(0.5)
        print(self.data)
        self.oap.tap(tuple(eval(self.data['BTN']['FIRST_XCX_SEARCH_RESULT'])))
        time.sleep(1)
        return 0

    def all_message(self):
        """
        :return:从公众号主页下拉点击全部消息消息
        """
        # 全部消息
        try:
            all_message_pos = self.vc.click_by_words("全部消息", tap=False)
            self.oap.tap(all_message_pos)
            time.sleep(5)
            self.oap.roll(0, 500)
            time.sleep(8)
        except TfException as e:
            return TfException(-1, traceback.format_exc()).processer()
        return 0

    def click_a_message(self, args=2):
        """
        :return:来到历史列表之后随机点击一篇文章
        """
        # 获取界面文章标题消息
        if args == 1:
            # corp = self.data['CROP_RANGE']['PROFILE_MESSAGE_LIST']
            corp = tuple(eval(self.data['CROP_RANGE']['PROFILE_MESSAGE_LIST']))
        elif args == 2:
            # corp = self.data['CROP_RANGE']['MESSAGE_LIST']
            corp = tuple(eval(self.data['CROP_RANGE']['PROFILE_MESSAGE_LIST']))
        try:
            ui_words = self.vc.get_ui_words(location=True, crop=corp)
        except TfException as e:
            raise TfException(-1, traceback.format_exc()).processer()
        # 随便点一个标题
        random_index = randint(1, len(ui_words)) - 1
        loc = ui_words[random_index]['location']
        pos = [loc['left'], loc['top'], loc['left'] + loc['width'], loc['top'] + loc['height']]
        self.oap.tap(pos)
        # 等待页面加载完毕
        time.sleep(5)
        self.oap.roll(0, 500)
        time.sleep(1)

    def check_comments(self):
        """
        :return:成功打开一篇文章之后 拉到底检查评论信息
        """
        # 拉到底
        for i in range(2):
            self.oap.roll(0, 500)
            time.sleep(1)
        time.sleep(2)
        # 检查有无评论 有评论 无评论 有广告 三种情况
        ui_words_str = self.vc.get_ui_words(location=False, in_str=True, crop=tuple(eval(self.data['CROP_RANGE']['LEAVE_MSG_BOTTOM'])))
        # 如果暂无评论点击了留言按钮
        if self.data['UI_WORDS']['NO_LEAVING_MSG'] in ui_words_str:
            print('点击了留言信息。。。')
            # self.oap.tap(self.data['BTN']['LEAVE_MSG'])
            self.oap.tap(tuple(eval(self.data['BTN']['LEAVE_MSG'])))
            time.sleep(1)
            self.oap.key(self.data['KEY']['BACK_KEYEVENT'])

    def get_all_req_data(self, nickname, hand=False):
        """
        获取关于一个公众号的全部请求数据 当前程序使用baidu API受到网络和并发限制效果并十分理想
        :param nickname: 公众号昵称
        :return:最后成功与否取决在redis中是否找到有有效数据
        """
        TidyReqData.flush_data("*.req")
        redis_instance.set('current_nickname', nickname)
        self.home_to_gzh_search()
        self.search_gzh(nickname)
        if hand == False:
            self.all_message()
            self.click_a_message()
            # self.check_comments()
        else:
            input("请一一手动获取参数 回车退出")
        self.home()

    def get_part_req_data(self, nickname):
        """
        仅获取阅读量和评论的请求数据
        :param nickname:公众号昵称
        :return:最后成功与否取决在redis中是否找到有有效数据
        """
        TidyReqData.flush_data()
        redis_instance.set('current_nickname', nickname)
        self.home_to_gzh_search()
        self.search_gzh(nickname)
        self.click_a_message(args=1)
        self.check_comments()
        self.home()

    def get_xcx_item_list(self, nickname, hand = False):
        """
        获取小程序所有请求数据
        :param hand: 是否手动
        :param nickname: 小程序名称
        :return:
        """
        print(nickname)
        TidyReqData.flush_data("*.req")
        self.home_to_search()
        self.search_xcx(nickname)
        # 选中第一个结果后进入小程序，先选择第一个栏目
        self.oap.tap(tuple(eval(self.data['BTN']['JIU_QIAN_ZFJY'])))
        time.sleep(1)
        # self.oap.tap(tuple(eval(self.data['BTN']['JIU_QIAN_HWYJ'])))
        # 截图 与记录匹配获取相关信息

        # 方案一：先拉取全部文章列表，然后遍历获取每篇文章
        # 方案二：现截现获取信息
        get_list_slide_num = 0
        while redis_instance.get("xcx_get_list_stop") is None:
            self.oap.swap([60, 1000], [60, 250])
            get_list_slide_num = get_list_slide_num+1
            time.sleep(0.5)
        # 回退到首部
        if redis_instance.get("xcx_get_list_stop"):
            for i in range(get_list_slide_num):
                self.oap.swap([60, 250], [60, 1000])

        # 获取小程序信息列表
        xcx_item_list = TidyReqData.get_xcx_req_data("*._xcx")
        # xcx_item_list = []
        for item in xcx_item_list:
            print("当前文档", item['title'])
            if xcx.doc_exist("jqzt", item['id']):
                self.oap.swap([60, 500], [60, 250])
                continue
            # 遍历每一项，并截图处理
            item_pos = self.vc.click_by_words(item['title'], tap=False)
            print(item_pos, "", item['title'])
            self.oap.tap(item_pos)
            time.sleep(3)
            self.oap.key(self.data['KEY']['BACK_KEYEVENT'])

            # 到达限制次数，退出循环
            if redis_instance.get("xcx_get_detail_stop"):
                break

            self.oap.swap([60, 500], [60, 250])
            # 滑动拉取列表拉完停止
            time.sleep(1)

        self.oap.key(self.data['KEY']['BACK_KEYEVENT'])
        self.oap.key(self.data['KEY']['BACK_KEYEVENT'])
        print("原始数据进入mongo %s" % ("xcx_jqzt"))
        TidyReqData.insert_xcx_to_mongo("xcx_jqzt")
        print("原始数据进入mongo %s 完成" % ("xcx_jqzt"))
        print("正在为 %s 创建索引..." % ("jqzt"))
        index_result = xcx.index_db_docs("jqzt")
        print("索引完成", index_result)
        print("redis 相关数据设置缓存时间")
        ttl_result = TidyReqData.set_redis_ttl(60*60*5)
        print("redis 5小时失效时间设置完成")

    def get_xcx_item_list_mini_batch(self, nickname, cur_phone):
        """
        获取小程序所有请求数据
        :param cur_phone: 当前设备
        :param nickname: 小程序名称
        :return:
        """
        print(nickname)
        # TidyReqData.flush_data("*.req")
        self.back_to_weixin_home()
        self.home_to_search()
        self.search_xcx(nickname)
        time.sleep(3)
        # 在这里监听，设备的search_key是否需要更新
        # print("config data", OPENID_PHONE)
        open_id = OPENID_PHONE[cur_phone]
        task_device_list = device_manager.get_task_type_devices("wxzs")
        open_id_device = dict(zip(OPENID_PHONE.values(), OPENID_PHONE.keys()))
        #检查该账号对应search_key是否有效
        while True:
            need_update = TidyReqData.get_need_update_keys()
            # 校验待更新设备是否存在，不存在则去除该open_id
            if len(need_update) > 0:
                need_del_open_id_list = []
                for need_update_open_id in need_update:
                    need_update_device_num = open_id_device[need_update_open_id]
                    if need_update_device_num not in task_device_list:
                        need_del_open_id = OPENID_PHONE[need_update_device_num]
                        need_del_open_id_list.append(need_del_open_id)
                if need_del_open_id_list:
                    req_res = TidyReqData.set_offline_wechat_index_accounts(need_del_open_id_list)
                    print("清除不可用账号{},结果{}".format(need_del_open_id_list, req_res))
                    time.sleep(2)
                    need_update = TidyReqData.get_need_update_keys()

            # 校验是否有设备需要刷新
            if len(need_update) > 0:
                print("接收到更新内容", need_update)
                print("当前设备:{}, 当前open_id: {}".format(cur_phone, open_id))
                if open_id in need_update:
                    # 点击右上角
                    time.sleep(1)
                    self.back_to_weixin_home()
                    time.sleep(1)
                    try:
                        device_manager.push(cur_phone)
                        print("{} 设备释放成功".format(cur_phone))
                    except TfMongoException as e:
                        # device_manager.push(cur_phone)
                        print(TfMongoException(-2, "设备 {} --mongo设备释放操作出错，可能是链接超时".format(cur_phone),
                                                cur_phone).processer())
                    break
                # 这里有两种情况，1.另一线程设备进入，2.确实有设备不响应（暂不考虑）
                else:
                    # 链接设备不响应，操作后退出任务重新刷新设备
                    print("设备 {} 需要刷新或对应设备可能已断开连接，重新获取待更新记录".format(need_update))
                    # 刷新可用列表到服务器
                    self.oap.swap([60, 400], [60, 350])
                    time.sleep(randint(1, 3))
                    self.oap.swap([60, 350], [60, 400])
                    time.sleep(1)
                    # break

            else:
                print("设备{}重新获取待更新记录".format(cur_phone))
                self.oap.swap([60, 400], [60, 350])
                time.sleep(randint(3, 6))
                self.oap.swap([60, 350], [60, 400])