import os
import random as rnd
from typing import List, Tuple

from trdg.data_generator import FakeTextDataGenerator
from trdg.utils import load_fonts


def create_strings_from_font_dicts(
    length: int,
    allow_variable: bool,
    count: int,
    fonts: List[str],
) -> Tuple[List[str], List[List[str]]]:
    """
    每个字符从随机字体的对应字表中抽取，空格继承前一字符的字体。
    font_sequence 与 string 等长（含空格），与 _generate_horizontal_text
    中 splitted_text（非 word_split 模式）的索引严格对齐。
    """
    font_char_dict = {}
    for font in fonts:
        txt_path = os.path.splitext(font)[0] + ".txt"
        if not os.path.exists(txt_path):
            continue
        with open(txt_path, "r", encoding="utf-8") as f:
            chars = [line.strip() for line in f if line.strip()]
        if chars:
            font_char_dict[font] = chars

    valid_fonts = list(font_char_dict.keys())
    if not valid_fonts:
        raise ValueError("No valid font-associated .txt dictionaries found.")

    strings = []
    font_sequences = []

    for _ in range(count):
        token_count = rnd.randint(1, length) if allow_variable else length
        chars = []
        seq = []
        for i in range(token_count):
            font = rnd.choice(valid_fonts)
            char = rnd.choice(font_char_dict[font])
            chars.append(char)
            seq.append(font)
            if i < token_count - 1:
                chars.append(" ")
                seq.append(font)   # 空格沿用前字符字体，保证长度对齐
        strings.append("".join(chars))
        font_sequences.append(seq)

    return strings, font_sequences


class GeneratorFromFontDicts:
    """
    仿照 GeneratorFromDict，字符逐个从字体对应字表中随机抽取，
    并将 font_sequence 传入渲染层实现逐字符字体指定。
    """

    def __init__(
        self,
        count: int = -1,
        length: int = 1,
        allow_variable: bool = False,
        fonts: List[str] = [],
        language: str = "en",
        size: int = 32,
        skewing_angle: int = 0,
        random_skew: bool = False,
        blur: int = 0,
        random_blur: bool = False,
        background_type: int = 0,
        distorsion_type: int = 0,
        distorsion_orientation: int = 0,
        is_handwritten: bool = False,
        width: int = -1,
        alignment: int = 1,
        text_color: str = "#282828",
        orientation: int = 0,
        space_width: float = 1.0,
        character_spacing: int = 0,
        margins: Tuple[int, int, int, int] = (5, 5, 5, 5),
        fit: bool = False,
        output_mask: bool = False,
        word_split: bool = False,
        image_dir: str = os.path.join(
            "..", os.path.split(os.path.realpath(__file__))[0], "images"
        ),
        stroke_width: int = 0,
        stroke_fill: str = "#282828",
        image_mode: str = "RGB",
        output_bboxes: int = 0,
        rtl: bool = False,
        multi_line: bool = False,
        line_max: int = 32,
    ):
        self.count = count
        self.length = length
        self.allow_variable = allow_variable
        self.fonts = fonts if fonts else load_fonts(language)
        self.size = size
        self.skewing_angle = skewing_angle
        self.random_skew = random_skew
        self.blur = blur
        self.random_blur = random_blur
        self.background_type = background_type
        self.distorsion_type = distorsion_type
        self.distorsion_orientation = distorsion_orientation
        self.is_handwritten = is_handwritten
        self.width = width
        self.alignment = alignment
        self.text_color = text_color
        self.orientation = orientation
        self.space_width = space_width
        self.character_spacing = character_spacing
        self.margins = margins
        self.fit = fit
        self.output_mask = output_mask
        self.word_split = word_split
        self.image_dir = image_dir
        self.stroke_width = stroke_width
        self.stroke_fill = stroke_fill
        self.image_mode = image_mode
        self.output_bboxes = output_bboxes
        self.rtl = rtl
        self.multi_line = multi_line
        self.line_max = line_max

        self.generated_count = 0
        self.batch_size = min(max(count, 1), 1000)
        self.steps_until_regeneration = self.batch_size

        self.strings, self.font_sequences = create_strings_from_font_dicts(
            self.length, self.allow_variable, self.batch_size, self.fonts
        )

    def __iter__(self):
        return self

    def __next__(self):
        return self.next()

    def next(self):
        if self.generated_count == self.count:
            raise StopIteration

        if self.generated_count >= self.steps_until_regeneration:
            self.strings, self.font_sequences = create_strings_from_font_dicts(
                self.length, self.allow_variable, self.batch_size, self.fonts
            )
            self.steps_until_regeneration += self.batch_size

        self.generated_count += 1
        idx = (self.generated_count - 1) % len(self.strings)
        text = self.strings[idx]
        font_sequence = self.font_sequences[idx]

        # size 兼容 int 和 (min, max) 两种传参形式
        if isinstance(self.size, (list, tuple)):
            size = rnd.randint(self.size[0], self.size[1])
        else:
            size = self.size

        return (
            FakeTextDataGenerator.generate(
                self.generated_count,
                text,
                self.fonts,
                None,       # out_dir
                size,
                None,       # extension
                self.skewing_angle,
                self.random_skew,
                self.blur,
                self.random_blur,
                self.background_type,
                self.distorsion_type,
                self.distorsion_orientation,
                self.is_handwritten,
                0,          # name_format
                self.width,
                self.alignment,
                self.text_color,
                self.orientation,
                self.space_width,
                self.character_spacing,
                self.margins,
                self.fit,
                self.output_mask,
                self.word_split,
                self.image_dir,
                self.stroke_width,
                self.stroke_fill,
                self.image_mode,
                self.output_bboxes,
                self.multi_line,
                self.line_max,
                font_sequence,   # 新增
            ),
            font_sequence,
        )