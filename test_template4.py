import collections
import itertools
import json
import os
from datetime import timedelta

import requests

from pdflib import PDFTemplate
from utils import utils

GROUP_SENSORS_MAPPING = {
    "无分组": [
        "WIN0001",
        "WIN0002",
        "WIN0004",
        "WIN0005",
        "WIN0006",
        "WIN0008",
        "WIN0011",
        "WIN0012",
        "WIN0013",
        "WIN0014",
        "WIN0015",
        "WIN0016",
        "WIN0017",
        "WIN0018",
        "WIN0019",
        "WIN0020",
        "WIN0021",
        "WIN0022",
        "WIN0023",
        "WIN0024",
        "WIN0025",
        "WIN0026",
        "WSR0001",
    ],
    "cnwang_laptop": ["WIN0010"],
    "FAE": ["WIN0003"],
    "demo": ["WIN0009"],
    "hjn-demo": ["WIN0007"],
}

SENSOR_GROUP_MAPPING = {
    "WIN0001": "无分组",
    "WIN0002": "无分组",
    "WIN0004": "无分组",
    "WIN0005": "无分组",
    "WIN0006": "无分组",
    "WIN0008": "无分组",
    "WIN0011": "无分组",
    "WIN0012": "无分组",
    "WIN0013": "无分组",
    "WIN0014": "无分组",
    "WIN0015": "无分组",
    "WIN0016": "无分组",
    "WIN0017": "无分组",
    "WIN0018": "无分组",
    "WIN0019": "无分组",
    "WIN0020": "无分组",
    "WIN0021": "无分组",
    "WIN0022": "无分组",
    "WIN0023": "无分组",
    "WIN0024": "无分组",
    "WIN0025": "无分组",
    "WIN0026": "无分组",
    "WSR0001": "无分组",
    "WIN0010": "cnwang_laptop",
    "WIN0003": "FAE",
    "WIN0009": "demo",
    "WIN0007": "hjn-demo"
}

BASE_PAYLOAD_MAPPING = {
    "start_time": None,
    "end_time": None,
    "page_name": None,
    "item_id": None,
    "rule_id": None,
    "search_index": None,
    "data_scope": {
        "FORMAT.raw": None,
        "SENSOR_ID.raw": None,
    }
}


class DrawSensorHostLogPDF(object):
    """
    1. 运行趋势与探针组无关，是LOG FORMAT 和 time 的对应关系
    """

    TITLE = "探针主机日志"

    def __init__(self, post_data: dict, url="http://192.168.8.60:8002"):
        self.start_time = post_data["start_time"]
        self.end_time = post_data["end_time"]
        self.start_time_of_datetime = utils.post_time_to_datetime(self.start_time)
        self.end_time_of_datetime = utils.post_time_to_datetime(self.end_time)
        self.days_interval = (self.end_time_of_datetime - self.start_time_of_datetime).days
        self.time_list = [
            (self.start_time_of_datetime + timedelta(hours=8, days=int(_))). \
                strftime("%Y%m%d")
            for _ in range(self.days_interval + 1)
        ]
        self.log_formats = post_data["log_formats"]
        self.group_sensor_mapping = post_data["group_sensor_mapping"]
        self.sensor_groups = list(self.group_sensor_mapping.keys())
        self.sensors = list(itertools.chain(*self.group_sensor_mapping.values()))
        self.url = url
        self.base_payload = collections.defaultdict(lambda: BASE_PAYLOAD_MAPPING)
        self.template = None
        self.items = None

    def init_template(self):
        # 初始化模板
        self.template = PDFTemplate.PDFTemplate.read_template(
            os.path.join(os.getcwd(), "templates", "template3.xml")
        )
        assert self.template, RuntimeError("读取模板文件失败！")

        self.items = self.template["items"]
        PDFTemplate.PDFTemplate.set_text_data(self.items["title"], self.TITLE)

    def post_payload_for_logs(self, payload: dict) -> tuple:
        # 从ES获取数据
        response = requests.post(self.url, data=json.dumps(payload))
        return response.status_code, json.loads(response.content)

    def set_trend(self):
        # 趋势图
        data_for_draw = self.get_trend_data()
        log_formats = list(data_for_draw.keys())
        value_lists = [data_for_draw[_] for _ in log_formats]

        description = (
            f"主机运行日志-运行趋势,"
            f"从{utils.datetime_to_str(self.start_time_of_datetime)} 至 "
            f"{utils.datetime_to_str(self.end_time_of_datetime)},"
            f"探针组: {list(self.group_sensor_mapping.keys())},"
            f"日志类型: {log_formats}"
        )

        PDFTemplate.PDFTemplate.set_paragraph_data(
            self.items["description"],
            description
        )

        PDFTemplate.PDFTemplate.set_line_chart_data(
            self.items["line_chart"],
            value_lists,
            self.time_list,
            legend_names=log_formats
        )

    def get_trend_data(self) -> dict:
        data_for_draw = utils.init_data_for_PDF(self.days_interval)
        payload = self.base_payload["trend"]
        payload["start_time"] = self.start_time
        payload["end_time"] = self.end_time
        payload["page_name"] = "log_classify"
        payload["item_id"] = 0
        payload["rule_id"] = "00",
        payload["search_index"] = "log*"
        payload["data_scope"] = {
            "FORMAT.raw": self.log_formats,
            "SENSOR_ID.raw": self.sensors,
        }

        status_code, content = self.post_payload_for_logs(payload)
        # TODO if status_code != 200

        for format_time_list, value, *_ in content["result"]:
            log_format = format_time_list[0]["FORMAT.raw"]
            log_time = utils.time_with_Z_to_datetime(format_time_list[1]["TIME"])
            value_index = (log_time - self.start_time_of_datetime).days + 1
            data_for_draw[log_format][value_index] += value

        # print(json.dumps(dict(data_for_draw), indent=4))

        return dict(data_for_draw)

    def run(self):
        self.init_template()
        self.set_trend()
        PDFTemplate.PDFTemplate.draw(self.template)


def main(post_data):
    draw_sensor_host_log = DrawSensorHostLogPDF(post_data)
    draw_sensor_host_log.run()


if __name__ == "__main__":

    base_test_case = {
        "start_time": None,
        "end_time": None,
        "category": None,
        "log_formats": [],
        "group_sensor_mapping": {}
    }

    test_cases = [
        {
            "start_time": "2019-06-26T00:00:00.000",
            "end_time": "2019-07-04T00:00:00.000",
            "category": "sensor_host_log",
            "log_formats": [
                "SENSOR_SAFEMODE_BOOT",
                "SENSOR_MULTIPLE_OS_BOOT",
                "SENSOR_VM_INSTALLED",
                "SENSOR_SERVICECHANGE",
                "SENSOR_HARDWARE_CHANGE"
            ],
            "group_sensor_mapping": {
                "无分组": [
                    "WIN0001",
                    "WIN0002",
                    "WIN0004",
                    "WIN0005",
                    "WIN0006",
                    "WIN0008",
                    "WIN0011",
                    "WIN0012",
                    "WIN0013",
                    "WIN0014",
                    "WIN0015",
                    "WIN0016",
                    "WIN0017",
                    "WIN0018",
                    "WIN0019",
                    "WIN0020",
                    "WIN0021",
                    "WIN0022",
                    "WIN0023",
                    "WIN0024",
                    "WIN0025",
                    "WIN0026",
                    "WSR0001",
                ],
                "cnwang_laptop": ["WIN0010"],
                "FAE": ["WIN0003"],
                "demo": ["WIN0009"],
                "hjn-demo": ["WIN0007"],
            }
        },
    ]

    for test_case in test_cases:
        main(test_case)
