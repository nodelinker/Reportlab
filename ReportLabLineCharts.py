# -*- coding: utf-8 -*-

from reportlab.lib import colors
from reportlab.lib.attrmap import AttrMap
from reportlab.lib.attrmap import AttrMapValue
from reportlab.graphics.charts.linecharts import HorizontalLineChart
from reportlab.lib.validators import isBoolean, OneOf, isListOfStringsOrNone, isListOfStrings, isNumber, isString, \
    isNumberInRange, isColor
from reportlab.graphics.shapes import Rect
from reportlab.graphics.shapes import String, STATE_DEFAULTS
from ReportLabLib import ChartsLegend, ALL_COLORS, XCategoryAxisWithDesc, YValueAxisWithDesc, DefaultFontName
# from reportlab.pdfbase.pdfmetrics import stringWidth


class LegendedHorizontalLineChart(HorizontalLineChart):
    """A subclass of Legend for drawing legends with lines as the
    swatches rather than rectangles. Useful for lineCharts and
    linePlots. Should be similar in all other ways the the standard
    Legend class.
    """

    _attrMap = AttrMap(
        BASE=HorizontalLineChart,
        drawLegend=AttrMapValue(isBoolean, desc='If true draw legend.', advancedUsage=1),
        legendPositionType=AttrMapValue(
            OneOf(
                "null",
                "top-left", "top-mid", "top-right",
                "bottom-left", "bottom-mid", "bottom-right"
            ),
            desc="The position of LinLegend."),
        legendAdjustX=AttrMapValue(isNumber, desc='xxx.'),
        legendAdjustY=AttrMapValue(isNumber, desc='xxx.'),
        legendCategoryNames=AttrMapValue(isListOfStringsOrNone, desc='List of legend category names.'),
        titleMain=AttrMapValue(isString, desc='main title text.'),
        titleMainFontName=AttrMapValue(isString, desc='main title font name.'),
        titleMainFontSize=AttrMapValue(isNumberInRange(0, 100), desc='main title font size.'),
        titleMainFontColor=AttrMapValue(isColor, desc='main title font color.')
    )

    def __init__(self):
        HorizontalLineChart.__init__(self)

        self.drawLegend = False
        self.legendPositionType = "null"
        self.legendCategoryNames = None
        self.legendAdjustX = 0
        self.legendAdjustY = 0
        self.titleMain = ""
        self.titleMainFontColor = colors.gray
        self.titleMainFontName = DefaultFontName
        self.titleMainFontSize = STATE_DEFAULTS['fontSize']

    def set_line_color(self):
        if self.legendCategoryNames is None:
            self.legendCategoryNames = []
        legend_num = len(self.legendCategoryNames)
        data_num = len(self.data)
        for i in range(data_num):
            self.lines[i].strokeColor = ALL_COLORS[i]
            if i >= legend_num:
                self.legendCategoryNames.append("unknown")

    def draw(self):
        self.set_line_color()
        g = HorizontalLineChart.draw(self)

        if self.drawLegend:
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


class ReportLabHorizontalLineChart(LegendedHorizontalLineChart):

    def __init__(self,
                 x, y, width, height, cat_names, data,
                 step_count=4, legend_names=None, legend_position="top-right", legend_adjust_x=0, legend_adjust_y=0,
                 main_title="", main_title_font_name=None, main_title_font_size=None, main_title_font_color=None,
                 x_desc=None, y_desc=None):
        LegendedHorizontalLineChart.__init__(self)

        self.categoryAxis = XCategoryAxisWithDesc(desc=x_desc)
        self.valueAxis = YValueAxisWithDesc(desc=y_desc)

        self.x = x
        self.y = y
        self.height = height
        self.width = width
        self.data = data

        cat_names_num = len(cat_names)
        show_cat_num = 7
        if cat_names_num > show_cat_num:
            gap_num = int(cat_names_num / show_cat_num)
            for i in range(cat_names_num):
                if i % gap_num != 0:
                    cat_names[i] = ""

        self.categoryAxis.categoryNames = cat_names
        self.categoryAxis.labels.boxAnchor = 'n'

        min_value, max_value, step = self.get_limit_value(step_count)
        self.valueAxis.valueMin = min_value
        self.valueAxis.valueMax = max_value
        self.valueAxis.valueStep = step

        self.joinedLines = 1
        self.lines.strokeWidth = 2

        if legend_names is not None and isListOfStrings(legend_names) is True:
            self.drawLegend = True
            self.legendCategoryNames = legend_names
        self.legendPositionType = legend_position

        self.legendAdjustX = legend_adjust_x
        self.legendAdjustY = legend_adjust_y

        self.titleMain = main_title
        if main_title_font_name is not None:
            self.titleMainFontName = main_title_font_name
        if main_title_font_size is not None:
            self.titleMainFontSize = main_title_font_size
        if main_title_font_color is not None:
            self.titleMainFontColor = main_title_font_color

    def get_limit_value(self, step_count):
        min_value = 0xffffffff
        max_value = 0 - min_value

        for d in self.data:
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

        max_value = min_value + (step_count * step)

        return min_value, max_value, step


if __name__ == "__main__":
    from reportlab.graphics.shapes import Drawing
    from reportlab.graphics import renderPDF

    drawing = Drawing(500, 1000)

    lc_cats1 = ["一月", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug"]
    lc_values1 = [(13, 5, 20, 22, 37, 45, 19, 4), (5, 20, 46, 38, 23, 21, 6, 14), (67, 88, 98, 13, 68, 109, 110, 120),
                  (6, 9, 77, 88, 91, 130, 135, 125)]
    lc_cats2 = ["刘攀", "lijie", "longhui", "zijian", "gaofeng", "yilin", "heng", "xuesong"]
    lc_values2 = [(170, 165, 167, 172, 176, 180, 160, 166), (60, 65, 55, 58, 70, 72, 68, 80)]

    my_line_charts1 = ReportLabHorizontalLineChart(50, 800, 400, 125, lc_cats1, lc_values1,
                                                   legend_names=["刘攀", "lijie", "longhui", "gaofeng"],
                                                   legend_position="bottom-mid",
                                                   main_title="My first PDF Test.刘攀", main_title_font_color=colors.blue,
                                                   x_desc="月份", y_desc="数量")
    my_line_charts2 = ReportLabHorizontalLineChart(50, 600, 400, 125, lc_cats2, lc_values2,
                                                   legend_names=["刘攀", "lijie"],
                                                   legend_position="bottom-mid",
                                                   main_title="My second PDF Test.",
                                                   x_desc="Name", y_desc="身高/体重")

    drawing.add(my_line_charts1)
    drawing.add(my_line_charts2)

    renderPDF.drawToFile(drawing, 'example_linecharts.pdf')
