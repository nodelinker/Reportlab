# -*- coding: utf-8 -*-

from reportlab.lib import colors
from reportlab.graphics.charts.barcharts import BarChart
from reportlab.lib.attrmap import AttrMap
from reportlab.lib.attrmap import AttrMapValue
from reportlab.lib.validators import isBoolean, OneOf, isListOfStringsOrNone, isListOfStrings, isNumber, isString, \
    isNumberInRange, isColor
from reportlab.graphics.shapes import Rect
from ReportLabLib import ChartsLegend, ALL_COLORS, XCategoryAxisWithDesc, YCategoryAxisWithDesc, \
    YValueAxisWithDesc, XValueAxisWithDesc, DefaultFontName
from reportlab.graphics.shapes import String, STATE_DEFAULTS


class ReportLabBarChart(BarChart):

    _flipXY = 0

    _attrMap = AttrMap(
        BASE=BarChart,
        drawLegend=AttrMapValue(isBoolean, desc='If true draw legend.', advancedUsage=1),
        legendPositionType=AttrMapValue(
            OneOf("null", "top-left", "top-mid", "top-right", "bottom-left", "bottom-mid", "bottom-right"),
            desc="The position of LinLegend."),
        legendAdjustX=AttrMapValue(isNumber, desc='xxx.'),
        legendAdjustY=AttrMapValue(isNumber, desc='xxx.'),
        legendCategoryNames=AttrMapValue(isListOfStringsOrNone, desc='List of legend category names.'),
        titleMain=AttrMapValue(isString, desc='main title text.'),
        titleMainFontName=AttrMapValue(isString, desc='main title font name.'),
        titleMainFontSize=AttrMapValue(isNumberInRange(0, 100), desc='main title font size.'),
        titleMainFontColor=AttrMapValue(isColor, desc='main title font color.')
    )

    def __init__(self, x, y, width, height, cat_names, data, step_count=4, style="parallel", label_format=None,
                 legend_names=None, legend_position="top-right", legend_adjust_x=0, legend_adjust_y=0,
                 main_title="", main_title_font_name=None, main_title_font_size=None, main_title_font_color=None,
                 x_desc=None, y_desc=None):
        BarChart.__init__(self)

        if self._flipXY:
            self.categoryAxis = YCategoryAxisWithDesc(desc=y_desc)
            self.valueAxis = XValueAxisWithDesc(desc=x_desc)
        else:
            self.categoryAxis = XCategoryAxisWithDesc(desc=x_desc)
            self.valueAxis = YValueAxisWithDesc(desc=y_desc)

        if style not in ["stacked", "parallel"]:
            style = "parallel"
        self.categoryAxis.style = style

        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.data = data
        self.strokeColor = colors.black
        self.categoryAxis.labels.boxAnchor = 'ne'
        self.categoryAxis.labels.dx = 0
        self.categoryAxis.labels.dy = 0
        self.categoryAxis.labels.angle = 30

        cat_names_num = len(cat_names)
        show_cat_num = 4
        if cat_names_num > show_cat_num:
            gap_num = int(cat_names_num / show_cat_num)
            for i in range(cat_names_num):
                if i % gap_num != 0:
                    cat_names[i] = ""
        self.categoryAxis.categoryNames = cat_names

        if label_format is not None:
            self.barLabelFormat = label_format
            self.barLabels.boxTarget = "mid"

        min_value, max_value, step = self.get_limit_value(step_count)

        self.valueAxis.valueMin = min_value
        self.valueAxis.valueMax = max_value
        self.valueAxis.valueStep = step

        self.drawLegend = False
        self.legendCategoryNames = None
        if legend_names is not None and isListOfStrings(legend_names) is True:
            self.drawLegend = True
            self.legendCategoryNames = legend_names
        self.legendPositionType = legend_position
        self.legendAdjustX = legend_adjust_x
        self.legendAdjustY = legend_adjust_y

        self.titleMain = main_title
        self.titleMainFontName = DefaultFontName
        self.titleMainFontSize = STATE_DEFAULTS['fontSize']
        self.titleMainFontColor = colors.gray
        if main_title_font_name is not None:
            self.titleMainFontName = main_title_font_name
        if main_title_font_size is not None:
            self.titleMainFontSize = main_title_font_size
        if main_title_font_color is not None:
            self.titleMainFontColor = main_title_font_color

    def get_limit_value(self, step_count):
        min_value = 0xffffffff
        max_value = 0 - min_value

        _data = []
        if self.categoryAxis.style == "stacked":
            flag = True
            for d in self.data:
                idx = 0
                for i in d:
                    if flag:
                        _data.append(i)
                    else:
                        _data[idx] += i
                    idx += 1
                flag = False

            for d in _data:
                if d > max_value:
                    max_value = d
            for d in self.data:
                for i in d:
                    if i < min_value:
                        min_value = i
        else:
            _data = self.data[:]

            for d in _data:
                for i in d:
                    if i > max_value:
                        max_value = i
                    if i < min_value:
                        min_value = i

        max_value += int(max_value / 10)
        max_value = int(max_value / 5) * 5
        min_value -= int(min_value / 10)
        min_value = int(min_value / 5) * 5

        step = int((max_value - min_value) / step_count)
        step = int(step / 5 + 1) * 5

        max_value = min_value + (step * step_count)

        return min_value, max_value, step

    def set_bar_color(self):
        if self.legendCategoryNames is None:
            self.legendCategoryNames = []
        legend_num = len(self.legendCategoryNames)
        data_num = len(self.data)
        for i in range(data_num):
            self.bars[i].strokeColor = ALL_COLORS[i]
            self.bars[i].fillColor = ALL_COLORS[i]
            if i >= legend_num:
                self.legendCategoryNames.append("unknown")

    def draw(self):
        self.set_bar_color()
        g = BarChart.draw(self)

        if self.drawLegend is True:
            legend = ChartsLegend()

            legend.positionType = self.legendPositionType
            if self.legendPositionType != "null":
                legend.backgroundRect = Rect(self.x, self.y, self.width, self.height)

            legend.adjustX = self.legendAdjustX
            legend.adjustY = self.legendAdjustY

            legend.colorNamePairs = []
            for i in range(len(self.legendCategoryNames)):
                legend.colorNamePairs.append((ALL_COLORS[i], self.legendCategoryNames[i]))

            g.add(legend)

        if self.titleMain != "":
            title = String(0, 0, self.titleMain)
            title.fontSize = self.titleMainFontSize
            title.fontName = self.titleMainFontName
            title.fillColor = self.titleMainFontColor
            title.textAnchor = 'start'
            title.x = self.x - 20
            title.y = self.y + self.height + 20

            g.add(title)

        return g


class ReportLabVerticalBarChart(ReportLabBarChart):

    _flipXY = 0


class ReportLabHorizontalBarChart(ReportLabBarChart):

    _flipXY = 1

    def __init__(self, *args, **kwargs):
        ReportLabBarChart.__init__(self, *args, **kwargs)

        self.categoryAxis.labels.labelPosFrac = 1


if __name__ == "__main__":
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics import renderPDF

    drawing = Drawing(500, 1000)

    bc_cats1 = ["liupan", "lijie", "longhui", "zijian", "gaofeng", "yilin", "heng", "xuesong"]
    bc_values1 = [(170, 165, 167, 172, 176, 180, 160, 166), (60, 65, 55, 58, 70, 72, 68, 80)]
    bc_cats2 = ["liupan", "lijie", "longhui", "zijian", "gaofeng", "yilin", "heng", "xuesong"]
    bc_values2 = [(170, 165, 167, 172, 176, 180, 160, 166), (60, 65, 55, 58, 70, 72, 68, 80)]

    my_bar_charts1 = ReportLabVerticalBarChart(50, 800, 150, 125, bc_cats1, bc_values1, label_format="%s",
                                               legend_names=["刘攀", "lijie"], legend_position="bottom-right",
                                               x_desc="姓名", y_desc="身高/体重")
    my_bar_charts2 = ReportLabHorizontalBarChart(275, 800, 150, 125, bc_cats2, bc_values2, style="stacked",
                                                 legend_names=["liupan", "lijie"], legend_position="top-right",
                                                 main_title="My First PDF Test.刘攀", main_title_font_color=colors.blue,
                                                 x_desc="身高/体重", y_desc="姓名")

    drawing.add(my_bar_charts1)
    drawing.add(my_bar_charts2)

    renderPDF.drawToFile(drawing, 'example_barcharts.pdf')
