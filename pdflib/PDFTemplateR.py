# -*- coding: utf-8 -*-

import json
import xmltodict
from copy import deepcopy
from reportlab.graphics.shapes import Drawing, String, STATE_DEFAULTS, Line, Rect
# from reportlab.graphics import renderPDF
from reportlab.lib.validators import isListOfNumbers, isString, isNumber, isListOfStrings
from reportlab.lib.styles import getSampleStyleSheet  # , ParagraphStyle
from reportlab.platypus import Paragraph  # , SimpleDocTemplate  # , KeepTogether
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.lib.colors import Color
from reportlab.pdfbase.pdfmetrics import stringWidth

from pdflib.ReportLabLineCharts import ReportLabHorizontalLineChart
from pdflib.ReportLabBarCharts import ReportLabHorizontalBarChart, ReportLabVerticalBarChart
from pdflib.ReportLabPieCharts import ReportLabPieChart
from pdflib.ReportLabLib import DefaultFontName
from reportlab.platypus import Table, TableStyle

from abc import ABC, abstractmethod


class PDFTemplateItem(ABC):

    def __init__(self, item_content):
        self.item_content = deepcopy(item_content)

        self.format_content(self.item_content)
        self.args_check(self.item_content)

    @staticmethod
    def format_content(item_content):
        if "rect" in item_content and isinstance(item_content["rect"], str):
            item_content["rect"] = json.loads(item_content["rect"])

        if "margin-left" in item_content:
            item_content['margin-left'] = int(item_content['margin-left'])
        else:
            item_content['margin-left'] = 0
        if "margin-right" in item_content:
            item_content['margin-right'] = int(item_content['margin-right'])
        else:
            item_content['margin-right'] = 0
        if "margin-top" in item_content:
            item_content['margin-top'] = int(item_content['margin-top'])
        else:
            item_content['margin-top'] = 0
        if "margin-bottom" in item_content:
            item_content['margin-bottom'] = int(item_content['margin-bottom'])
        else:
            item_content['margin-bottom'] = 0
        if "invalid" not in item_content:
            item_content['invalid'] = False
        elif not isinstance(item_content['invalid'], bool):
            if item_content['invalid'] == "True":
                item_content['invalid'] = True
            elif item_content['invalid'] == "False":
                item_content['invalid'] = False
            else:
                item_content['invalid'] = False

    @staticmethod
    def args_check(item_content):
        if not isinstance(item_content, dict):
            raise ValueError("item content is not dict json.")

        if "rect" not in item_content or \
                not isListOfNumbers(item_content["rect"]) or \
                len(item_content["rect"]) != 4:
            raise ValueError("item rect format error.")

    def get_rect(self):
        return self.item_content['rect'][0], self.item_content['rect'][1], \
               self.item_content['rect'][2], self.item_content['rect'][3]

    def set_rect(self, x=None, y=None, width=None, height=None):
        if x:
            self.item_content['rect'][0] = x
        if y:
            self.item_content['rect'][1] = y
        if width:
            self.item_content['rect'][2] = width
        if height:
            self.item_content['rect'][3] = height

    @staticmethod
    def auto_set_height(item):
        pass

    @staticmethod
    def _draw_item_rect(d, x, y, width, height, format_json):
        r = Rect(x, y, width, height, fillColor=Color(0.95, 0.95, 0.95, 1))
        d.add(r)

        width += 40
        height += 40
        text_format = {"rect": [int(width / 2), int(height / 2), width, height],
                       "content": "暂无数据", "position": "middle",
                       "font_name": DefaultFontName, "font_size": 30, "font_color": Color(0.5, 0.5, 0.5, 1)}
        t = PDFTemplateText._draw_text(text_format)
        d.add(t)

        if "main_title" in format_json:
            text_format = {"rect": [0, height, width, height - 15],
                           "content": format_json['main_title'], "position": "start",
                           "font_name": DefaultFontName, "font_size": 15, "font_color": Color(0.5, 0.5, 0.5, 1)}
            if "main_title_font_name" in format_json:
                text_format['font_name'] = format_json['main_title_font_name']
            if "main_title_font_size" in format_json:
                text_format['font_size'] = format_json['main_title_font_size']
            if "main_title_font_color" in format_json:
                text_format['font_color'] = format_json['main_title_font_color']
            main_title = PDFTemplateText._draw_text(text_format)
            d.add(main_title)

    @staticmethod
    def _draw_border(cv, x, y, width, height, color, stroke_width=1):
        d = Drawing(width, height)
        r = Rect(0, 0, width, height, strokeWidth=stroke_width, strokeColor=color, fillColor=Color(0, 0, 0, 0))
        d.add(r)
        d.drawOn(cv, x, y)

    @abstractmethod
    def draw(self, cv, show_border=False):
        if show_border:
            self._draw_border(cv, self.item_content['rect'][0], self.item_content['rect'][1],
                              self.item_content['rect'][2], self.item_content['rect'][3], Color(1, 0, 0, 1))


class PDFTemplateLineChart(PDFTemplateItem):

    def __init__(self, item_content):
        PDFTemplateItem.__init__(self, item_content)

    @staticmethod
    def format_content(item_content):
        PDFTemplateItem.format_content(item_content)

        if "main_title_font_size" in item_content:
            item_content["main_title_font_size"] = int(item_content["main_title_font_size"])
        if "main_title_font_color" in item_content and isinstance(item_content["main_title_font_color"], str):
            item_content["main_title_font_color"] = eval(item_content["main_title_font_color"])
        if "category_names" in item_content and type(item_content['category_names']) is str:
            item_content['category_names'] = json.loads(item_content['category_names'])
        if "cat_label_angle" in item_content:
            item_content['cat_label_angle'] = int(item_content['cat_label_angle'])
        if "cat_label_all" in item_content and not isinstance(item_content['cat_label_all'], bool):
            if item_content['cat_label_all'] == "True":
                item_content['cat_label_all'] = True
            elif item_content['cat_label_all'] == "False":
                item_content['cat_label_all'] = False

    @staticmethod
    def args_check(item_content):
        PDFTemplateItem.args_check(item_content)

    @staticmethod
    def _draw_line_chart(format_json):
        width = format_json['rect'][2]
        height = format_json['rect'][3]

        d = Drawing(width, height, vAlign="TOP")

        if format_json['data'] is None or type(format_json['data']) is str:
            PDFTemplateItem._draw_item_rect(d, 20, 20, width - 40, height - 50, format_json)
        elif type(format_json['data']) is list:
            cat_names = format_json['category_names']
            data = format_json['data']

            step_count = 4
            if "step_count" in format_json and isNumber(format_json['step_count']) is True:
                step_count = format_json['step_count']
            legend_names = None
            if "legend_names" in format_json and isListOfStrings(format_json['legend_names']) is True:
                legend_names = format_json['legend_names']
            legend_position = "top-right"
            if "legend_position" in format_json and isString(format_json['legend_position']) is True:
                legend_position = format_json['legend_position']
            legend_adjust_x = 0
            if "legend_adjust_x" in format_json and isNumber(format_json['legend_adjust_x']) is True:
                legend_adjust_x = format_json['legend_adjust_x']
            legend_adjust_y = 0
            if "legend_adjust_y" in format_json and isNumber(format_json['legend_adjust_y']) is True:
                legend_adjust_y = format_json['legend_adjust_y']
            main_title = ""
            if "main_title" in format_json and isString(format_json['main_title']) is True:
                main_title = format_json['main_title']
            main_title_font_name = None
            if "main_title_font_name" in format_json and isString(format_json['main_title_font_name']) is True:
                main_title_font_name = format_json['main_title_font_name']
            main_title_font_size = None
            if "main_title_font_size" in format_json and isNumber(format_json['main_title_font_size']) is True:
                main_title_font_size = format_json['main_title_font_size']
            main_title_font_color = None
            if "main_title_font_color" in format_json:
                main_title_font_color = format_json['main_title_font_color']
            x_desc = None
            if "x_desc" in format_json and isString(format_json['x_desc']) is True:
                x_desc = format_json['x_desc']
            y_desc = None
            if "y_desc" in format_json and isString(format_json['y_desc']) is True:
                y_desc = format_json['y_desc']
            cat_label_all = False
            if "cat_label_all" in format_json:
                cat_label_all = format_json['cat_label_all']
            cat_label_angle = 30
            if "cat_label_angle" in format_json and isNumber(format_json['cat_label_angle']) is True:
                cat_label_angle = format_json['cat_label_angle']

            line_chart = ReportLabHorizontalLineChart(0, 0, width, height, cat_names, data, step_count=step_count,
                                                      legend_names=legend_names, legend_position=legend_position,
                                                      legend_adjust_x=legend_adjust_x, legend_adjust_y=legend_adjust_y,
                                                      main_title=main_title, main_title_font_name=main_title_font_name,
                                                      main_title_font_size=main_title_font_size,
                                                      main_title_font_color=main_title_font_color,
                                                      x_desc=x_desc, y_desc=y_desc,
                                                      cat_label_angle=cat_label_angle, cat_label_all=cat_label_all)
            d.add(line_chart)

        return d

    def draw(self, cv, show_border=False):
        PDFTemplateItem.draw(self, cv, show_border)

        d = self._draw_line_chart(self.item_content)

        d.wrapOn(cv, self.item_content['rect'][2], self.item_content['rect'][3])
        d.drawOn(cv, self.item_content['rect'][0], self.item_content['rect'][1])


class PDFTemplateBarChart(PDFTemplateItem):

    def __init__(self, item_content):
        PDFTemplateItem.__init__(self, item_content)

    @staticmethod
    def format_content(item_content):
        PDFTemplateItem.format_content(item_content)

        if "main_title_font_size" in item_content:
            item_content["main_title_font_size"] = int(item_content["main_title_font_size"])
        if "main_title_font_color" in item_content and isinstance(item_content["main_title_font_color"], str):
            item_content["main_title_font_color"] = eval(item_content["main_title_font_color"])
        if "category_names" in item_content and type(item_content['category_names']) is str:
            item_content['category_names'] = json.loads(item_content['category_names'])
        if "cat_label_angle" in item_content:
            item_content['cat_label_angle'] = int(item_content['cat_label_angle'])
        if "cat_label_all" in item_content and not isinstance(item_content['cat_label_all'], bool):
            if item_content['cat_label_all'] == "True":
                item_content['cat_label_all'] = True
            elif item_content['cat_label_all'] == "False":
                item_content['cat_label_all'] = False

    @staticmethod
    def args_check(item_content):
        PDFTemplateItem.args_check(item_content)

    @staticmethod
    def _draw_bar_chart(format_json):
        width = format_json['rect'][2]
        height = format_json['rect'][3]

        d = Drawing(width, height, vAlign="TOP")

        if format_json['data'] is None or type(format_json['data']) is str:
            PDFTemplateItem._draw_item_rect(d, 20, 20, width - 40, height - 50, format_json)
        elif type(format_json['data']) is list:
            cat_names = format_json['category_names']
            data = format_json['data']
            bar_style = format_json['bar_style']

            style = "parallel"
            if "style" in format_json and isString(format_json['style']) is True:
                style = format_json['style']
            label_format = None
            if "label_format" in format_json and isString(format_json['label_format']) is True:
                label_format = format_json['label_format']
            step_count = 4
            if "step_count" in format_json and isNumber(format_json['step_count']) is True:
                step_count = format_json['step_count']
            legend_names = None
            if "legend_names" in format_json and isListOfStrings(format_json['legend_names']) is True:
                legend_names = format_json['legend_names']
            legend_position = "top-right"
            if "legend_position" in format_json and isString(format_json['legend_position']) is True:
                legend_position = format_json['legend_position']
            legend_adjust_x = 0
            if "legend_adjust_x" in format_json and isNumber(format_json['legend_adjust_x']) is True:
                legend_adjust_x = format_json['legend_adjust_x']
            legend_adjust_y = 0
            if "legend_adjust_y" in format_json and isNumber(format_json['legend_adjust_y']) is True:
                legend_adjust_y = format_json['legend_adjust_y']
            main_title = ""
            if "main_title" in format_json and isString(format_json['main_title']) is True:
                main_title = format_json['main_title']
            main_title_font_name = None
            if "main_title_font_name" in format_json and isString(format_json['main_title_font_name']) is True:
                main_title_font_name = format_json['main_title_font_name']
            main_title_font_size = None
            if "main_title_font_size" in format_json and isNumber(format_json['main_title_font_size']) is True:
                main_title_font_size = format_json['main_title_font_size']
            main_title_font_color = None
            if "main_title_font_color" in format_json:
                main_title_font_color = format_json['main_title_font_color']
            x_desc = None
            if "x_desc" in format_json and isString(format_json['x_desc']) is True:
                x_desc = format_json['x_desc']
            y_desc = None
            if "y_desc" in format_json and isString(format_json['y_desc']) is True:
                y_desc = format_json['y_desc']
            cat_label_all = False
            if "cat_label_all" in format_json:
                cat_label_all = format_json['cat_label_all']
            cat_label_angle = 30
            if "cat_label_angle" in format_json and isNumber(format_json['cat_label_angle']) is True:
                cat_label_angle = format_json['cat_label_angle']

            bar_chart = None
            if bar_style == "horizontal":
                bar_chart = ReportLabHorizontalBarChart(
                    0, 0, width, height, cat_names, data, style=style,
                    label_format=label_format, step_count=step_count,
                    legend_names=legend_names, legend_position=legend_position,
                    legend_adjust_x=legend_adjust_x, legend_adjust_y=legend_adjust_y,
                    main_title=main_title, main_title_font_name=main_title_font_name,
                    main_title_font_size=main_title_font_size,
                    main_title_font_color=main_title_font_color, x_desc=x_desc, y_desc=y_desc,
                    cat_label_angle=cat_label_angle, cat_label_all=cat_label_all)
            elif bar_style == "vertical":
                bar_chart = ReportLabVerticalBarChart(
                    0, 0, width, height, cat_names, data, style=style,
                    label_format=label_format, step_count=step_count,
                    legend_names=legend_names, legend_position=legend_position,
                    legend_adjust_x=legend_adjust_x, legend_adjust_y=legend_adjust_y,
                    main_title=main_title, main_title_font_name=main_title_font_name,
                    main_title_font_size=main_title_font_size,
                    main_title_font_color=main_title_font_color, x_desc=x_desc, y_desc=y_desc,
                    cat_label_angle=cat_label_angle, cat_label_all=cat_label_all)
            if bar_chart is not None:
                d.add(bar_chart)

        return d

    def draw(self, cv, show_border=False):
        PDFTemplateItem.draw(self, cv, show_border)

        d = self._draw_bar_chart(self.item_content)

        d.wrapOn(cv, self.item_content['rect'][2], self.item_content['rect'][3])
        d.drawOn(cv, self.item_content['rect'][0], self.item_content['rect'][1])


class PDFTemplatePieChart(PDFTemplateItem):

    def __init__(self, item_content):
        PDFTemplateItem.__init__(self, item_content)

    @staticmethod
    def format_content(item_content):
        PDFTemplateItem.format_content(item_content)

        if "main_title_font_size" in item_content:
            item_content["main_title_font_size"] = int(item_content["main_title_font_size"])
        if "main_title_font_color" in item_content and isinstance(item_content["main_title_font_color"], str):
            item_content["main_title_font_color"] = eval(item_content["main_title_font_color"])
        if "category_names" in item_content and type(item_content['category_names']) is str:
            item_content['category_names'] = json.loads(item_content['category_names'])

    @staticmethod
    def args_check(item_content):
        PDFTemplateItem.args_check(item_content)

    @staticmethod
    def _draw_pie_chart(format_json):
        width = format_json['rect'][2]
        height = format_json['rect'][3]

        d = Drawing(width, height, vAlign="TOP")

        if format_json['data'] is None or type(format_json['data']) is str:
            PDFTemplateItem._draw_item_rect(d, 20, 20, width - 40, height - 50, format_json)
        elif type(format_json['data']) is list:
            cat_names = format_json['category_names']
            data = format_json['data']

            main_title = ""
            if "main_title" in format_json and isString(format_json['main_title']) is True:
                main_title = format_json['main_title']
            main_title_font_name = None
            if "main_title_font_name" in format_json and isString(format_json['main_title_font_name']) is True:
                main_title_font_name = format_json['main_title_font_name']
            main_title_font_size = None
            if "main_title_font_size" in format_json and isNumber(format_json['main_title_font_size']) is True:
                main_title_font_size = format_json['main_title_font_size']
            main_title_font_color = None
            if "main_title_font_color" in format_json:
                main_title_font_color = format_json['main_title_font_color']

            pie_chart = ReportLabPieChart(0, 0, width, height, cat_names, data, main_title=main_title,
                                          main_title_font_name=main_title_font_name,
                                          main_title_font_size=main_title_font_size,
                                          main_title_font_color=main_title_font_color,
                                          draw_legend=True)
            d.add(pie_chart)

        return d

    def draw(self, cv, show_border=False):
        PDFTemplateItem.draw(self, cv, show_border)

        d = self._draw_pie_chart(self.item_content)

        d.wrapOn(cv, self.item_content['rect'][2], self.item_content['rect'][3])
        d.drawOn(cv, self.item_content['rect'][0], self.item_content['rect'][1])


class PDFTemplateParagraph(PDFTemplateItem):

    paragraph_leading = 1.5

    def __init__(self, item_content):
        PDFTemplateItem.__init__(self, item_content)

    @staticmethod
    def format_content(item_content):
        PDFTemplateItem.format_content(item_content)

        if "content" not in item_content:
            item_content["content"] = ""
        if "style" not in item_content:
            item_content["style"] = "BodyText"
        if "font_size" in item_content:
            item_content["font_size"] = int(item_content["font_size"])
        if "indent_flag" in item_content:
            item_content["indent_flag"] = int(item_content["indent_flag"])
        if "font_color" in item_content and isinstance(item_content["font_color"], str):
            item_content["font_color"] = eval(item_content["font_color"])

    @staticmethod
    def args_check(item_content):
        PDFTemplateItem.args_check(item_content)

    @staticmethod
    def _draw_paragraph(format_json):
        content = format_json['content']
        style_name = format_json['style']
        font_name = DefaultFontName
        if "font_name" in format_json:
            font_name = format_json['font_name']

        stylesheet = getSampleStyleSheet()
        ss = stylesheet[style_name]
        ss.fontName = font_name

        if "font_size" in format_json:
            ss.fontSize = format_json['font_size']

        if "font_color" in format_json:
            ss.fillColor = format_json['font_color']

        word_width = stringWidth(" ", font_name, ss.fontSize) * 2
        ss.leading = word_width * PDFTemplateParagraph.paragraph_leading

        indent_flag = 0
        if "indent_flag" in format_json:
            indent_flag = format_json['indent_flag']
        if indent_flag:
            ss.firstLineIndent = word_width * 2

        paragraph = Paragraph(content, ss)
        if "force_top" in format_json and int(format_json['force_top']) == 1:
            _, h = paragraph.wrap(format_json['rect'][2], format_json['rect'][3])
            format_json['rect'][1] = format_json['rect'][1] + format_json['rect'][3] - h

        return paragraph

    @staticmethod
    def _calc_paragraph_height(item):
        p = PDFTemplateParagraph._draw_paragraph(item)
        _, h = p.wrap(item['rect'][2], 0)
        del p
        return h

    @staticmethod
    def auto_set_height(item):
        item['rect'][3] = PDFTemplateParagraph._calc_paragraph_height(item)

    @staticmethod
    def _split_paragraph_text_by_height(item, split_height):
        content = item['content']
        str_len = len(content)
        content_height = PDFTemplateParagraph._calc_paragraph_height(item)
        split_index = int(split_height / content_height * str_len)

        tmp_item = deepcopy(item)
        tmp_item['content'] = content[:split_index]
        content_height = PDFTemplateParagraph._calc_paragraph_height(tmp_item)
        del tmp_item

        if content_height > split_height:
            flag = 0
        else:
            flag = 1

        while split_index > 0 or split_index < str_len:
            if flag == 0:
                split_index -= 1
            else:
                split_index += 1

            tmp_item = deepcopy(item)
            tmp_item['content'] = content[:split_index]
            tmp_height = PDFTemplateParagraph._calc_paragraph_height(tmp_item)
            del tmp_item

            if flag == 0:
                if tmp_height <= split_height:
                    split_index -= 1
                    break
            else:
                if tmp_height >= split_height:
                    split_index -= 1
                    break

        return split_index

    @staticmethod
    def split_paragraph(items, index, page_height):
        item = items[index]
        if item['type'] != "paragraph":
            return False

        item_height = item['rect'][3]
        y = item['rect'][1]
        if item_height + y <= page_height:
            return True

        split_height = page_height - y
        split_index = PDFTemplateParagraph._split_paragraph_text_by_height(item, split_height)

        new_item = deepcopy(item)
        new_item['content'] = new_item['content'][split_index:]
        new_item['indent_flag'] = 0

        item['content'] = item['content'][:split_index]
        item['rect'][3] = split_height

        items.insert(index + 1, new_item)

        return True

    def draw(self, cv, show_border=False):
        PDFTemplateItem.draw(self, cv, show_border)

        d = self._draw_paragraph(self.item_content)

        d.wrapOn(cv, self.item_content['rect'][2], self.item_content['rect'][3])
        d.drawOn(cv, self.item_content['rect'][0], self.item_content['rect'][1])


class PDFTemplateText(PDFTemplateItem):

    def __init__(self, item_content):
        PDFTemplateItem.__init__(self, item_content)

    @staticmethod
    def format_content(item_content):
        PDFTemplateItem.format_content(item_content)

        if "font_size" in item_content:
            item_content["font_size"] = int(item_content["font_size"])
        if "font_color" in item_content and isinstance(item_content["font_color"], str):
            item_content["font_color"] = eval(item_content["font_color"])

    @staticmethod
    def args_check(item_content):
        PDFTemplateItem.args_check(item_content)

    @staticmethod
    def _draw_text(format_json, auto_calc=True):
        width = format_json['rect'][2]
        height = format_json['rect'][3]

        d = Drawing(width, height, vAlign="TOP")

        content = format_json['content']
        position = format_json['position']
        x = 0
        y = 0

        font_size = STATE_DEFAULTS['fontSize']
        if "font_size" in format_json:
            font_size = format_json['font_size']

        if auto_calc:
            if position == "middle":
                x = int(width / 2)
                y = int(height / 2) - int(font_size / 2)
            elif position == "start":
                y = height
        else:
            x = format_json['rect'][0]
            y = format_json['rect'][1]

        text = String(x, y, content)

        text.fontName = DefaultFontName
        if "font_name" in format_json:
            text.fontName = format_json['font_name']
        text.fontSize = font_size
        if "font_color" in format_json:
            text.fillColor = format_json['font_color']
        text.textAnchor = position

        d.add(text)

        return d

    def draw(self, cv, show_border=False):
        PDFTemplateItem.draw(self, cv, show_border)

        d = self._draw_text(self.item_content)

        d.wrapOn(cv, self.item_content['rect'][2], self.item_content['rect'][3])
        d.drawOn(cv, self.item_content['rect'][0], self.item_content['rect'][1])


class PDFTemplateTable(PDFTemplateItem):

    def __init__(self, item_content):
        PDFTemplateItem.__init__(self, item_content)

    @staticmethod
    def format_content(item_content):
        PDFTemplateItem.format_content(item_content)

        stylesheet = getSampleStyleSheet()
        ss = stylesheet['BodyText']
        ss.fontName = DefaultFontName

        # convert data to paragraph
        temp = []
        for d in item_content['content']:
            temp.append(tuple([Paragraph(str(i), ss) for i in d]))
        item_content['content'] = temp

    @staticmethod
    def args_check(item_content):
        PDFTemplateItem.args_check(item_content)

    @staticmethod
    def _calc_table_height(item):
        t = PDFTemplateTable._draw_table(item)
        _, h = t.wrap(1, 0)
        del t
        return h

    @staticmethod
    def auto_set_height(item):
        item['rect'][3] = PDFTemplateTable._calc_table_height(item)

    @staticmethod
    def _cut_table_rows(item, split_height):
        ret = 0
        t = PDFTemplateTable._draw_table(item)
        t.wrap(1, 0)

        curr_y = 0
        for idx, val in enumerate(t._rowHeights):
            curr_y += val
            if curr_y >= split_height:
                ret = idx
                break

        del t
        return ret - 1

    @staticmethod
    def split_table(items, index, page_height):
        item = items[index]

        item_height = item['rect'][3]
        y = item['rect'][1]
        if item_height + y <= page_height:
            return True

        split_height = page_height - y
        split_index = PDFTemplateTable._cut_table_rows(item, split_height)

        new_item = deepcopy(item)
        new_item['content'] = new_item['content'][split_index:]

        item['content'] = item['content'][:split_index]
        item['rect'][3] = split_height

        items.insert(index + 1, new_item)

        return True

    @staticmethod
    def _draw_table(format_json):
        """
        :param format_json:
        :return:
        """

        font_name = DefaultFontName
        if "font_name" in format_json:
            font_name = format_json['font_name']
        font_size = STATE_DEFAULTS['fontSize']
        if "font_size" in format_json:
            font_size = format_json['font_size']
        font_color = STATE_DEFAULTS['fontSize']
        if "font_color" in format_json:
            font_color = format_json['font_color']

        stylesheet = getSampleStyleSheet()
        ss = stylesheet['BodyText']
        ss.fontName = font_name
        ss.fontSize = font_size
        ss.fillColor = font_color

        if "columns" not in format_json:
            raise ValueError("don't have any columns infomation. ")

        cols = format_json["columns"]

        # columns names
        _cols = cols.items()
        data = [tuple([v for _, v in cols.items()])]

        # generate table style
        ts = TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.burlywood),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.red),
            ('INNERGRID', (0, 0), (-1, -1), 0.25, colors.black),
            ('BOX', (0, 0), (-1, -1), 0.25, colors.black),
        ])
        content = format_json["content"]

        # merage data
        data.extend(content)
        table = Table(data)
        table.setStyle(ts)

        return table

    def draw(self, cv, show_border=False):
        PDFTemplateItem.draw(self, cv, show_border)

        d = self._draw_table(self.item_content)

        d.wrapOn(cv, self.item_content['rect'][2], self.item_content['rect'][3])
        d.drawOn(cv, self.item_content['rect'][0], self.item_content['rect'][1])


class PDFTemplatePage(object):

    ItemClass = {
        "line_chart": PDFTemplateLineChart,
        "bar_chart": PDFTemplateBarChart,
        "pie_chart": PDFTemplatePieChart,
        "paragraph": PDFTemplateParagraph,
        "text": PDFTemplateText,
        "table": PDFTemplateTable
    }

    def __init__(self, page_content, page_num, page_size, **kw):
        self.items = []
        self.page_content = page_content
        if not isinstance(page_num, int):
            raise ValueError("page number is not int.")
        self.page_num = page_num
        if not isListOfNumbers(page_size):
            raise ValueError("page size is not a list of numbers.")
        self.page_size = page_size
        self.rect = None
        self.coordinate = "left-top"
        self.auto_position = False
        self.x_padding = 0
        self.y_padding = 0
        self.align_type = "middle"
        self.header_text = None

        for k, v in kw.items():
            setattr(self, k, v)

        self.format_content(self.page_content)
        self.args_check(self.page_content)

        if "rect" in self.page_content:
            self.rect = self.page_content['rect']
        if "coordinate" in self.page_content:
            self.coordinate = self.page_content['coordinate']
        if "auto_position" in self.page_content:
            self.auto_position = self.page_content['auto_position']
        if "x-padding" in self.page_content:
            self.x_padding = self.page_content['x-padding']
        if "y-padding" in self.page_content:
            self.y_padding = self.page_content['y-padding']
        if "align-type" in self.page_content:
            self.align_type = self.page_content['align-type']

        for item in self.page_content['items']:
            self.add_item(item)

    @staticmethod
    def format_content(page_content):
        if "rect" in page_content and isinstance(page_content['rect'], str):
            page_content['rect'] = json.loads(page_content['rect'])

        if "auto_position" not in page_content:
            page_content['auto_position'] = False
        elif not isinstance(page_content['auto_position'], bool):
            if page_content['auto_position'] == "True":
                page_content['auto_position'] = True
            elif page_content['auto_position'] == "False":
                page_content['auto_position'] = False
            else:
                page_content['auto_position'] = False

        if "x-padding" in page_content:
            page_content['x-padding'] = int(page_content['x-padding'])
        else:
            page_content['x-padding'] = 0

        if "y-padding" in page_content:
            page_content['y-padding'] = int(page_content['y-padding'])
        else:
            page_content['y-padding'] = 0

        if "align-type" not in page_content:
            page_content['align-type'] = "middle"

        if "invalid" not in page_content:
            page_content['invalid'] = False
        elif not isinstance(page_content['invalid'], bool):
            if page_content['invalid'] == "True":
                page_content['invalid'] = True
            elif page_content['invalid'] == "False":
                page_content['invalid'] = False
            else:
                page_content['invalid'] = False

        if "items" in page_content:
            for item in page_content['items']:
                if not isinstance(item, dict):
                    item = page_content['items'][item]
                item_type = item['type']

                PDFTemplatePage.ItemClass[item_type].format_content(item)

    @staticmethod
    def args_check(page_content):
        if "rect" not in page_content:
            raise ValueError("page no rect.")

        if not isListOfNumbers(page_content['rect']) or len(page_content['rect']) != 4:
            raise ValueError("page rect error.")

        if "items" not in page_content:
            raise ValueError("page no items.")

        for item in page_content['items']:
            if not isinstance(item, dict):
                item = page_content['items'][item]
            item_type = item['type']

            PDFTemplatePage.ItemClass[item_type].args_check(item)

    def add_item(self, item_content):
        if not isinstance(item_content, dict):
            raise ValueError("item format is error.")
        if "type" not in item_content:
            raise ValueError("item has not property: type.")

        item_ins = self.ItemClass[item_content['type']](item_content)
        self.items.append(item_ins)

    @staticmethod
    def _calc_position_align(page, page_width, x_padding, start_index, end_index, align_type):
        if align_type == "middle" or align_type == "right":
            items_width = (end_index - start_index - 1) * x_padding
            for i in range(end_index - start_index):
                item = page['items'][start_index + i]

                margin_left = item['margin-left']
                margin_right = item['margin-right']
                items_width += item['rect'][2] + margin_left + margin_right

            start_pos = 0
            if align_type == "middle":
                start_pos = int((page_width - items_width) / 2)
            elif align_type == "right":
                start_pos = page_width - items_width

            for i in range(end_index - start_index):
                item = page['items'][start_index + i]

                margin_left = item['margin-left']
                margin_right = item['margin-right']
                item['rect'][0] = start_pos + margin_left
                start_pos += item['rect'][2] + x_padding + margin_left + margin_right
        elif align_type == "left":
            pass

    @staticmethod
    def calc_position(page):
        next_page = deepcopy(page)
        next_page['items'] = []

        page_width = page['rect'][2]
        page_height = page['rect'][3]
        x_padding = page['x-padding']
        y_padding = page['y-padding']
        align_type = page['align-type']

        cur_x = 0
        cur_y = 0
        next_y = 0
        next_page_flag = False
        index = 0
        next_page_index = 0
        row_start = 0

        for item in page['items']:
            if item['type'] == "paragraph":
                PDFTemplateParagraph.auto_set_height(item)
            elif item['type'] == 'table':
                PDFTemplateTable.auto_set_height(item)

                table_width = item['rect'][2]
                if table_width > page_width:
                    raise ValueError("table width too long")

            item_width = item['rect'][2]
            item_height = item['rect'][3]

            margin_left = item['margin-left']
            margin_right = item['margin-right']
            margin_top = item['margin-top']
            margin_bottom = item['margin-bottom']

            if cur_x != 0 and cur_x + item_width + margin_left + margin_right > page_width:
                # 这一行放不下，需要换行
                PDFTemplatePage._calc_position_align(page, page_width, x_padding, row_start, index, align_type)

                next_page_index = index
                row_start = index
                item['rect'][0] = margin_left
                item['rect'][1] = next_y + margin_top
                cur_x = item_width + x_padding + margin_left + margin_right
                cur_y = next_y
                next_y = cur_y + item_height + y_padding + margin_top + margin_bottom
            else:
                item['rect'][0] = cur_x + margin_left
                item['rect'][1] = cur_y + margin_top
                cur_x += item_width + x_padding + margin_left + margin_right
                if cur_y + item_height + y_padding + margin_top + margin_bottom > next_y:
                    next_y = cur_y + item_height + y_padding + margin_top + margin_bottom

            if next_y > page_height:
                if cur_y != 0 or item['type'] == "paragraph" or item['type'] == "table":
                    split_flag = False
                    if item['type'] == "paragraph":
                        split_flag = PDFTemplateParagraph.split_paragraph(page['items'], index, page_height)
                    elif item['type'] == "table":
                        # split table to next page
                        split_flag = PDFTemplateTable.split_table(page['items'], index, page_height)

                    if split_flag:
                        next_page_index += 1
                        index += 1

                    next_page_flag = True
                    break

            index += 1
        PDFTemplatePage._calc_position_align(page, page_width, x_padding, row_start, index, align_type)

        if next_page_flag:
            next_page['items'] = page['items'][next_page_index:]
            page['items'] = page['items'][:next_page_index]
            return next_page

        return None

    def _compute_coord(self):
        for item_ins in self.items:
            x, y, _, h = item_ins.get_rect()
            x = x + self.rect[0]
            y = y + self.rect[1]
            if self.coordinate == "left-top":
                y = self.page_size[1] - y - h

            item_ins.set_rect(x=x, y=y)

    def _draw_header(self, cv):
        start_x = int(self.page_size[0] / 10)

        width = self.page_size[0]
        height = int(self.page_size[1] / 15)

        d = Drawing(width, height, vAlign="TOP")

        header_line = Line(start_x, 0, width - start_x, 0)
        d.add(header_line)

        if self.header_text:
            x = int(width / 2)
            y = 5

            text = String(x, y, self.header_text)
            text.fontName = DefaultFontName
            text.textAnchor = "middle"

            d.add(text)

        d.wrapOn(cv, width, height)
        d.drawOn(cv, 0, self.page_size[1] - height)

    def _draw_feet(self, cv):
        start_x = int(self.page_size[0] / 10)

        width = self.page_size[0]
        height = int(self.page_size[1] / 15)

        d = Drawing(width, height, vAlign="TOP")

        feet_line = Line(start_x, height, width - start_x, height)
        d.add(feet_line)

        if self.page_num is not None:
            x = int(width / 2)
            y = height - STATE_DEFAULTS['fontSize']

            text = String(x, y, str(self.page_num + 1))
            text.fontName = DefaultFontName
            text.textAnchor = "middle"

            d.add(text)

        d.wrapOn(cv, width, height)
        d.drawOn(cv, 0, 0)

    def draw(self, cv, show_border=False):
        self._compute_coord()

        self._draw_header(cv)
        self._draw_feet(cv)

        for item_ins in self.items:
            item_ins.draw(cv, show_border)

        if show_border:
            PDFTemplateItem._draw_border(cv, self.rect[0], self.rect[1], self.rect[2], self.rect[3],
                                         Color(0, 0, 1, 1), 2)


class PDFTemplateR(object):

    def __init__(self, template_file):
        self.template_file = template_file

        self.template_content = None
        self.pages = None
        self.valid_pages = None
        self.pdf_file = None
        self.author = None
        self.title = None
        self.page_size = None
        self.coordinate = "left-top"
        self.header_text = None
        self.show_border = False
        self.cv = None

        self._read_template_file()

    def _read_template_file(self):
        try:
            with open(self.template_file, "r", encoding='UTF-8') as f:
                template = f.read()

            template = xmltodict.parse(template)['pdf']

            if "pages" not in template:
                raise ValueError("template no pages.")
            if "file_name" not in template:
                raise ValueError("template no file_name.")
            if "page_size" not in template:
                raise ValueError("template no page_size.")

            template['page_size'] = json.loads(template['page_size'])

            for page in template['pages']:
                page = template['pages'][page]
                PDFTemplatePage.format_content(page)
                PDFTemplatePage.args_check(page)
        except Exception as err_info:
            import traceback
            traceback.print_exc()
            print(err_info)
            raise ValueError("PDF template file format error.")

        self.template_content = template
        self.pages = self.template_content['pages']
        self.pdf_file = self.template_content['file_name']
        self.page_size = self.template_content['page_size']

        if "author" in self.template_content:
            self.author = self.template_content['author']
        if "title" in self.template_content:
            self.title = self.template_content['title']
        if "coordinate" in self.template_content:
            self.coordinate = self.template_content['coordinate']
        if "header_text" in self.template_content:
            self.header_text = self.template_content['header_text']
        if "show_border" in self.template_content:
            self.show_border = self.template_content['show_border']

    def set_item_data(self, page_num, item_name, **kwargs):
        item = self.pages['page%d' % page_num]['items'][item_name]

        for k, v in kwargs.items():
            item[k] = v
        item['invalid'] = False

    def _set_pdf_info(self):
        if self.author is not None:
            self.cv.setAuthor(self.author)
        if self.title is not None:
            self.cv.setTitle(self.title)

    def _get_valid_pages(self):
        max_page_num = 0
        valid_count = []

        for page in self.pages:
            page_num = int(page.replace("page", ""))
            if page_num < 0:
                raise ValueError("page num must >= 0.")
            if int(page_num) > max_page_num:
                max_page_num = int(page_num)

            page = self.pages[page]
            if not page['invalid']:
                valid_count.append(page_num)
        if max_page_num != len(self.pages) - 1:
            raise ValueError("page num discontinuous.")

        valid_count = sorted(valid_count)

        _pages = {}
        index = 0
        for page_num in valid_count:
            _pages[index] = {}

            page = self.pages['page%d' % page_num]

            _pages[index] = deepcopy(page)
            _pages[index]['items'] = []
            for item_name in page['items']:
                item = page['items'][item_name]
                if item['invalid'] is True:
                    continue

                _pages[index]['items'].append(item)

            index += 1

        return _pages

    @staticmethod
    def _auto_calc_position(pages):
        add_count = 0

        _pages = {}
        for page_num in pages:
            page = pages[page_num]
            if page['auto_position'] is True:
                next_page = PDFTemplatePage.calc_position(page)
                _pages[page_num + add_count] = deepcopy(page)
                while next_page:
                    add_count += 1
                    _next_page = PDFTemplatePage.calc_position(next_page)
                    _pages[page_num + add_count] = deepcopy(next_page)

                    if _next_page:
                        next_page = deepcopy(_next_page)
                    else:
                        next_page = None
            else:
                _pages[page_num + add_count] = deepcopy(pages[page_num])
        pages = deepcopy(_pages)
        del _pages

        return pages

    def _create_page_object(self, pages):
        self.valid_pages = []
        for page_num in pages:
            page = pages[page_num]

            page_ins = PDFTemplatePage(page, page_num, self.page_size, coordinate=self.coordinate,
                                       header_text=self.header_text)

            self.valid_pages.append(page_ins)

    def draw(self):
        self.cv = canvas.Canvas(self.pdf_file, pagesize=self.page_size, bottomup=1)

        self._set_pdf_info()

        pages = self._get_valid_pages()
        pages = self._auto_calc_position(pages)
        self._create_page_object(pages)

        first_page = True
        for page_ins in self.valid_pages:
            if first_page is False:
                self.cv.showPage()
            if first_page is True:
                first_page = False

            page_ins.draw(self.cv, self.show_border)

        self.cv.save()
        self.cv = None