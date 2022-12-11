"""
1. 利用缓存机制减少字体实例化的次数
2. 利用延迟渲染减少渲染次数，只在实际用到图片的地方渲染图片
3. 各个元素自动标注
4. 各个元素的属性可以自由修改
"""
from functools import lru_cache
from typing import List

from PIL import ImageDraw, ImageFont, Image
from pyrect import Rect


class Element(Rect):
    """元素类"""

    def __init__(self, left=0, top=0, width=0, height=0):
        super().__init__(left, top, width, height,onChange=self.update_lines)

        self._left_line = Line(self.topleft, self.bottomleft)
        self._right_line = Line(self.topright, self.bottomleft)
        self._top_line = Line(self.topleft, self.topright)
        self._bottom_line = Line(self.bottomleft, self.bottomright)

    def update_lines(self,oldbox=None,newbox=None):
        self._left_line = Line(self.topleft, self.bottomleft)
        self._right_line = Line(self.topright, self.bottomleft)
        self._top_line = Line(self.topleft, self.topright)
        self._bottom_line = Line(self.bottomleft, self.bottomright)

    @property
    def left_line(self):
        return self._left_line

    @property
    def top_line(self):
        return self._top_line

    @property
    def right_line(self):
        return self._right_line

    @property
    def bottom_line(self):
        return self._bottom_line

    @property
    def lines(self):
        return self._left_line, self._top_line, self._right_line, self._bottom_line


@lru_cache
def load_font(font_path, font_size):
    return ImageFont.truetype(font_path, font_size)


def textbbox(pos, txt, font, anchor,stroke_width=0):
    bbox = font.getbbox(txt, anchor=anchor,stroke_width=stroke_width)
    return bbox[0] + pos[0], bbox[1] + pos[1], bbox[2] + pos[0], bbox[3] + pos[1]


class Label:
    """
    标签类
    """

    def __init__(self, content: str, rect: Rect, key: str):
        self.key = key
        self.content = content
        self.rect = rect

    @property
    def points(self):
        return [
            self.rect.topleft,
            self.rect.topright,
            self.rect.bottomright,
            self.rect.bottomleft,
        ]

    def __str__(self):
        return ";".join(
            map(
                str,
                [
                    *self.rect.topleft,
                    *self.rect.topright,
                    *self.rect.bottomright,
                    *self.rect.bottomleft,
                    f"{self.key}@{self.content}",
                ],
            )
        )


def draw_text(pos, txt, font_path, font_size, fill=(0, 0, 0, 255), anchor="lt",
        stroke_width=0,
        stroke_fill=None,
        underline=False,
        deleteline=False,):
    """
    将任何锚点的字符串转化成 lt 锚点，并且去除前后空格
    :param pos: 锚点位置(x,y)
    :param txt: str 文本
    :param font_path: str 字体
    :param font_size: int 字体像素高
    :param fill: 填充颜色
    :param anchor: str 锚点类型
    :return:
    """
    if txt == txt.strip():
        return Text(pos, txt, fill, font_path, font_size, anchor,stroke_width,stroke_fill,underline,deleteline)

    font = load_font(font_path, font_size)
    box = textbbox(pos, txt, font, anchor,stroke_width)

    if txt != txt.rstrip():  # 右边有空格
        txt = txt.rstrip()
        pos = box[0], (box[1] + box[3]) // 2
        box = textbbox(pos, txt, font, "lm",stroke_width)  # 左对齐的方式写字
        anchor = "lm"

    if txt != txt.lstrip():  # 左边有空格
        txt = txt.lstrip()
        pos = box[2], (box[1] + box[3]) // 2  # 右中点
        anchor = "rm"

    return Text(pos, txt.strip(), fill, font_path, font_size, anchor,stroke_width,stroke_fill,underline,deleteline)


class Text(Element):
    def __init__(
        self,
        xy,
        text,
        fill=None,
        font_path="simfang.ttf",
        font_size=20,
        anchor=None,
        stroke_width=0,
        stroke_fill=None,
        underline=False,
        deleteline=False,
    ):
        self._xy = xy
        self._text = text
        self._fill = fill
        self._font_path = font_path
        self._font_size = font_size
        self._anchor = anchor
        self._stroke_width = stroke_width
        self.stroke_fill = stroke_fill
        self._font = load_font(self._font_path, self._font_size)

        box = self.bbox
        super().__init__(box[0], box[1], box[2] - box[0], box[3] - box[1])
        self._underline = underline
        if underline:
            self._bottom_line.fill=self._fill
        if deleteline:
            self._deleteline = Line(self.midleft, self.midright, 1, self._fill)
        else:
            self._deleteline = False
        
    def copy(self):
        return Text(
            self._xy,
            self._text,
            self._fill,
            self._font_path,
            self._font_size,
            self._anchor,
            self._stroke_width,
            self._stroke_fill,
            self._underline,
            self._deleteline,
        )

    def move(self, dx, dy):
        self.xy = self.xy[0] + dx, self.xy[1] + dy
        self.update()
        
    def cmove(self, dx, dy):
        t = self.copy()
        t.move(dx, dy)
        return t

    def update_lines(self,oldbox=None,newbox=None):
        """如果改变位置，文字，字体式时，更新坐标"""
        box = self.bbox
        self.left = box[0]
        self.top = box[1]
        self.right = box[2]
        self.bottom = box[3]
        super().update_lines(oldbox,newbox)
        self._deleteline = Line(self.midleft, self.midright, 1, self._fill)

    @property
    def text(self):
        return self._text

    @text.setter
    def text(self, val):
        self._text = val
        self.update_lines()

    @property
    def xy(self):
        return self._xy

    @xy.setter
    def xy(self, val):
        self._xy = val
        self.update_lines()

    @property
    def fill(self):
        return self._fill

    @fill.setter
    def fill(self, val):
        self._fill = val
        if self._deleteline:
            self._deleteline.fill = self._fill
    
    @property
    def deleteline(self):
        return self._deleteline
    
    @deleteline.setter
    def deleteline(self,val):
        if val:
            self._deleteline = Line(self.midleft, self.midright, 1, self._fill)
        else:
            self._deleteline = None
    
    @property
    def underline(self):
        return self._bottom_line
    
    @underline.setter
    def underline(self,val):
        self._underline = val
        self._bottom_line.fill=self._fill
        
    @property
    def anchor(self):
        return self._anchor

    @anchor.setter
    def anchor(self, val):
        self._anchor = val
        self.update_lines()

    @property
    def font_path(self):
        return self._font_path

    @font_path.setter
    def font_path(self, val):  # 改变字体时候自动重新加载字体
        self._font_path = val
        self._font = load_font(self._font_path, self._font_size)
        self.update_lines()

    @property
    def font_size(self):
        return self._font_size

    @font_size.setter
    def font_size(self, val):  # 改变字号时候自动重新加载字体
        self._font_size = val
        self._font = load_font(self._font_path, self._font_size)
        self.update_lines()

    @property
    def stroke_width(self):
        return self._stroke_width

    @stroke_width.setter
    def stroke_width(self, val):
        self._stroke_width = val
        self.update_lines()

    @property
    def bbox(self):
        box = self._font.getbbox(
            self.text, anchor=self.anchor, stroke_width=self._stroke_width
        )
        return (
            box[0] + self.xy[0],
            box[1] + self.xy[1],
            box[2] + self.xy[0],
            box[3] + self.xy[1],
        )

    @property
    def label(self):
        return Label(self.text, self, key="text")

    def render(self, drawer: ImageDraw):
        drawer.text(
            self._xy,
            self._text,
            self.fill,
            self._font,
            self._anchor,
            stroke_width=self._stroke_width,
            stroke_fill=self.stroke_fill,
        )
        if self._deleteline:
            self._deleteline.render(drawer)
        if self._underline:
            self._bottom_line.render(drawer)
            
    def __contains__(self, item):
        return item in self._text

    def __str__(self):
        return self._text

    def show(self):
        im = Image.new("RGBA", self.bottomright, (255, 255, 255, 255))
        drawer = ImageDraw.Draw(im)
        self.render(drawer)
        im.crop(self.bbox).show(self._text)


def draw_dash_line(drawer, start, end, fill, width, dash=4, gap=2):
    if start[0] == end[0]:
        for y in range(start[1], end[1], dash + gap):
            _s = start[0], y
            _e = start[0], min(y + dash, end[1])

            drawer.line((_s, _e), fill, width)
    if start[1] == end[1]:
        for x in range(start[0], end[0], dash + gap):
            _s = x, start[1]
            _e = min(end[0], x + dash), start[1]
            drawer.line((_s, _e), fill, width)
    raise ValueError("The Line is neither vertical nor hor")


class Line:
    def __init__(self, start, end, width=1, fill=(0, 0, 0, 0), mode="s"):
        self.start = start
        self.end = end
        self.width = width
        self.fill = fill
        self.mode = mode

    @property
    def is_ver(self):
        return self.start[0] == self.end[0]

    @property
    def is_hor(self):
        return self.start[1] == self.end[1]

    def copy(self):
        return Line(self.start, self.end, self.width, self.fill)

    def move(self, x, y):
        self.start = self.start[0] + x, self.start[1] + y
        self.end = self.end[0] + x, self.end[1] + y

    def cmove(self, x, y):
        line = self.copy()
        line.move(x, y)
        return line

    def smove(self, dx, dy=0):  # 起点移动
        self.start = self.start[0] + dx, self.start[1] + dy

    def emove(self, dx, dy=0):  # 终点移动
        self.end = self.end[0] + dx, self.end[1] + dy

    def render(self, drawer: ImageDraw):
        if self.mode == "s":
            drawer.line((self.start, self.end), fill=self.fill, width=self.width)
        elif self.mode == "d":
            draw_dash_line(drawer, self.start, self.end, self.fill, self.width)
        elif self.mode[0] == "s" and "d" in self.mode:
            solid, gap = self.mode[1:].split("d")
            draw_dash_line(
                drawer,
                self.start,
                self.end,
                self.fill,
                self.width,
                int(solid),
                int(gap),
            )


class Cell(Element):
    """
    单元格内部的对齐方式需不需要
    """

    def __init__(
        self,
        left=0,
        top=0,
        width=0,
        height=0,
        fill=None,
        outline=(0, 0, 0, 0),
        line_width=1,
        visible=True,
        align = None,
        padding_width=0,
    ):
        super().__init__(left, top, width, height)
        self.fill = fill
        self.outline = outline
        self.line_width = line_width
        self.texts = []
        self.visible = visible
        self._align = align
        if align:
            self._do_align()
        self.padding_width = padding_width
        # self.update_lines()
        
    def _do_align(self):
        if self.align == 'mm':
            for text in self:
                text.xy = self.center
                text.anchor = 'mm'
                
        elif self.align == 'lm':
            for text in self:
                text.xy = self.left + self.padding_width,self.centery
                text.anchor = 'lm'
        
        elif self.align == 'rm':
            for text in self:
                text.xy = self.right - self.padding_width,self.centery
                text.anchor = 'rm'
                
        elif self.align == 'lt':
            for text in self:
                text.xy = self.left+self.padding_width,self.top+self.padding_width
                text.anchor = 'lt'
                
        elif self.align == 'rt':
            for text in self:
                text.xy = self.right-self.padding_width,self.top+self.padding_width
                text.anchor = 'rt'
        
        elif self.align == 'mt':
            for text in self:
                text.xy = self.centerx,self.top+self.padding_width
                text.anchor = 'mt'

        elif self.align == 'lb':
            for text in self:
                text.xy = self.left + self.padding_width, self.bottom - self.padding_width
                text.anchor = 'lb'

        elif self.align == 'rb':
            for text in self:
                text.xy = self.right - self.padding_width, self.bottom - self.padding_width
                text.anchor = 'rb'

        elif self.align == 'mb':
            for text in self:
                text.xy = self.centerx, self.bottom - self.padding_width
                text.anchor = 'mb'
    
    @property
    def align(self):
        return self._align
    
    @align.setter
    def align(self,val):
        assert len(val)==2
        self._align = val
        self._do_align()

    @property
    def is_empty(self):
        return not bool(self.texts)
    
    def append(self,item):
        self.texts.append(item)
    
    def clear(self):
        self.texts.clear()

    def update_lines(self,oldbox,newbox):
        self._left_line = Line(
            self.topleft, self.bottomleft, self.line_width, self.outline
        )
        self._top_line = Line(
            self.topleft, self.topright, self.line_width, self.outline
        )
        self._right_line = Line(
            self.topright, self.bottomright, self.line_width, self.outline
        )
        self._bottom_line = Line(
            self.bottomleft, self.bottomright, self.line_width, self.outline
        )
        self._do_align()
    
    def __iter__(self):
        yield from self.texts
        
    def __contains__(self, item):
        """是否存在匹配的文本"""
        for text in self.texts:
            if item in text:
                return True
        return False
    
    def __getitem__(self, item):
        """1.按序号返回单元格的文字
        2.按文本内容搜索返回单元格文字
        """
        if isinstance(item, int):
            return self.texts[item]

    def merge(self, other):
        """合并单元格"""
        self.union(other)
        self.texts.extend(other.texts)
        self.update()


    @property
    def label(self):
        return Label("", self, key="cell")

    def render(self, drawer):
        for line in self.lines:
            line.render(drawer)
        for text in self.texts:
            text.render(drawer)

    def show(self):
        im = Image.new('RGBA',self.bottomright,(0,0,0,0))
        drawer = ImageDraw.Draw(im)
        self.render(drawer)
        im.crop(self.topleft+self.bottomright).show()
        
class Table(Element):
    """表格不是基本元素，是容器元素"""

    def __init__(self, cells: List[Cell] = None, outline="black", line_width=1):
        super().__init__()
        self.cells = cells
        self.outline = outline
        self.line_width = line_width

        d = defaultdict(list)
        for cell in self.cells:
            d[cell.top].append(cell)
        self._rows = []
        for k in sorted(list(d.keys())):
            d[k].sort(key=lambda x: x.left)
            self._rows.append(d[k])

        self.topleft = self._rows[0][0].topleft
        self.bottomright = self._rows[-1][-1].bottomright

        self._left_line = Line(
            self.topleft, self.bottomleft, self.line_width, self.outline
        )
        self._top_line = Line(
            self.topleft, self.topright, self.line_width, self.outline
        )
        self._right_line = Line(
            self.topright, self.bottomright, self.line_width, self.outline
        )
        self._bottom_line = Line(
            self.bottomleft, self.bottomright, self.line_width, self.outline
        )


    def __iter__(self):
        for row in self._rows:
            for cell in row:
                yield cell

    def __getitem__(self, item):
        """可以取单元格或者某行
        table[0] 是第0行
        table[0][0] 是第0行第0列的cell
        """
        return self._rows[item]

    def merge(self, row_start, col_start, row_end, col_end):
        """合并单元格"""
        self._rows[row_start][row_start].merge(self._rows[row_end][col_end])
        self._rows[row_end][col_end].visible = False  # 不可以直接删除，标记为删除

    @property
    def label(self):
        labels = []
        for row in self._rows:
            for cell in row:
                if cell.visible:
                    labels.append(cell.label)
                    for text in cell.texts:
                        labels.append(text.label)
        return labels

    def render(self, drawer):
        for row in self._rows:
            for cell in row:
                if cell.visible:
                    cell.render(drawer)
        for line in self.lines:
            line.render(drawer)


class ImageInfo(Rect):
    def __init__(self, image: Image, box=None, mask=None):
        if not box:
            box = (0, 0)
        if len(box) == 2:
            super().__init__(box[0], box[1])
        elif len(box) == 4:
            super().__init__(box[0], box[1], box[2] - box[0], box[3] - box[1])

        self.image = image
        if mask:
            self.mask = mask
        else:
            if self.image.mode in ("L", "RGBA"):
                self.mask = self.image
            else:
                self.mask = None

    @property
    def label(self):
        return Label("", self, key="image")


class Layer(list):
    """图层容器"""

    def __init__(self, name="texts", index=0, size=None):
        super().__init__()
        self.index = index
        self.name = name
        self.size = size

    def render(self):
        im = Image.new("RGBA", self.size, (0, 0, 0, 0))
        drawer = ImageDraw.Draw(im)
        for obj in self:
            obj.render(drawer)
        return im


class ImageData:
    def __init__(
        self,
        background: Image,
        texts: List[Text] = None,
        images: List[ImageInfo] = None,
        lines: List[Line] = None,
        tables: List[Table] = None,
        **kwargs,
    ):
        self.background = background
        self.texts = texts or []
        self.lines = lines or []
        self.images = images or []
        self.tables = tables or []
        self.size = background.size

    @classmethod
    def new(cls, size, color=(0, 0, 0, 0)):
        background = Image.new("RGBA", size, color)
        return cls(background)

    @property
    def text_layer(self):
        layer = Layer("text", 1, self.size)
        for table in self.tables:
            for cell in table.cells:
                for text in cell.texts:
                    layer.append(text)
        layer.extend(self.texts)
        return layer

    @property
    def line_layer(self):
        layer = Layer("line", 2, self.size)
        for table in self.tables:
            for cell in table.cells:
                for line in cell.lines:
                    layer.append(line)
        layer.extend(self.lines)
        return layer

    @property
    def text_image(self):
        return self.text_layer.render()

    @property
    def line_image(self):
        return self.line_layer.render()

    @property
    def doc_image(self):
        text_image = self.text_image
        line_image = self.line_image
        text_image.paste(line_image, mask=line_image)
        return text_image

    @property
    def image(self):
        bg = self.background.copy()
        bg.paste(self.doc_image, mask=self.doc_image)
        for im in self.images:
            bg.paste(im.image, im.topleft, mask=im.mask)
        return bg

    @property
    def mask(self):
        return self.image.getchannel("A")

    def show(self):
        self.image.show()

    def save(self, filename):
        self.image.convert("RGB").save(filename)
        log_file = filename.split(".")[0] + ".txt"
        with open(log_file, "w", encoding="utf-8") as f:
            for label in self.label:
                f.write(f"{filename};{str(label)}\n")

    @property
    def label(self):
        labels = []
        for text in self.texts:
            labels.append(text.label)
        for table in self.tables:
            labels.extend(table.label)
        return labels

    def text(self, pos, txt, font_path, font_size, fill=(0, 0, 0, 255), anchor="lt"):
        self.texts.append(draw_text(pos, txt, font_path, font_size, fill, anchor))

    def line(self, start, end, width=1, fill="black", mode="s"):
        self.lines.append(Line(start, end, width, fill, mode))

    def paste(self, im, box=None, mask=None):
        self.images.append(ImageInfo(im, box, mask))

    def asdict(self):
        d = {}
        d["image"] = self.image
        d["label"] = [f"{label.key}@{label.text}" for label in self.label]
        points = []
        for label in self.label:
            points.extend(label.points)
        d["point"] = points
        return d


class TableGenerator:
    def build_table(self):
        """构建文本表格"""

    def load_template(self):
        """表格转imagedata"""

    def preprocess(self, template):
        """表格预处理
        1.添加、修改文字颜色，字体
        2.绘制可见线
        """

    def render(self, template):
        """
        渲染表格，生成image_dict
        """

    def postprocess(self, image_data):
        """
        处理图像相关的
        """


if __name__ == "__main__":
    im = Text((100, 100), "中国", (255, 0, 0, 255), "simfang.ttf", 50,underline=True,deleteline=True)
    cell = Cell(0,0,200,200,outline=(0,0,0,255),line_width=2,align='lm',padding_width=10)
    cell.append(im)
    cell.width *=2
    cell.height = cell.height//2
    # cell.do_align()
    cell.show()
