import colorsys
import math
import random as rnd
from typing import Tuple

import numpy as np
from PIL import Image, ImageColor, ImageDraw, ImageFilter, ImageFont

from trdg.utils import get_text_height, get_text_width

# Thai Unicode reference: https://jrgraphix.net/r/Unicode/0E00-0E7F
TH_TONE_MARKS = [
    "0xe47",
    "0xe48",
    "0xe49",
    "0xe4a",
    "0xe4b",
    "0xe4c",
    "0xe4d",
    "0xe4e",
]
TH_UNDER_VOWELS = ["0xe38", "0xe39", "\0xe3A"]
TH_UPPER_VOWELS = ["0xe31", "0xe34", "0xe35", "0xe36", "0xe37"]


def generate(
    text,
    fonts,
    text_color,
    font_size,
    orientation,
    space_width,
    character_spacing,
    fit,
    word_split,
    stroke_width=0,
    stroke_fill="#282828",
    multi_line=False,
    line_max=32,
):
    if orientation == 0:
        return _generate_horizontal_text(
            text,
            fonts,
            text_color,
            font_size,
            space_width,
            character_spacing,
            fit,
            word_split,
            stroke_width,
            stroke_fill,
            multi_line,
            line_max,
        )
    elif orientation == 1:
        return _generate_vertical_text(
            text,
            font,
            text_color,
            font_size,
            space_width,
            character_spacing,
            fit,
            stroke_width,
            stroke_fill,
        )
    else:
        raise ValueError("Unknown orientation " + str(orientation))


def _compute_character_width(image_font, character):
    if len(character) == 1 and (
        "{0:#x}".format(ord(character))
        in TH_TONE_MARKS + TH_UNDER_VOWELS + TH_UNDER_VOWELS + TH_UPPER_VOWELS
    ):
        return 0
    # Casting as int to preserve the old behavior
    return round(image_font.getlength(character))


def split_integer_evenly(num, n):
    quotient = num // n  # Integer division to get the quotient
    remainder = num % n  # Modulo operator to get the remainder

    # Create a list with the quotient as the initial value for each part
    parts = [quotient] * n

    # Distribute the remainder across the parts
    for i in range(remainder):
        parts[i] += 1

    return parts


def _generate_horizontal_text(
    text,
    fonts,
    text_color,
    font_size,
    space_width,
    character_spacing,
    fit,
    word_split=False,
    stroke_width=0,
    stroke_fill="#282828",
    multi_line=False,
    line_max=32,
):
    choice_list = np.random.choice(
        len(fonts), len(text), replace=True
    )  # A font can be selected multiple times
    choice_set = set(choice_list)
    image_fonts = [ImageFont.truetype(font=font, size=font_size) for font in fonts]

    # Compute max space width for all fonts
    space_width = max(
        [
            get_text_width(image_fonts[choice], " ") * space_width
            for choice in choice_set
        ]
    )

    if word_split:
        splitted_text = []
        for w in text.split(" "):
            splitted_text.append(w)
            splitted_text.append(" ")
        splitted_text.pop()
    else:
        splitted_text = text

    # Compute text width for corresponding fonts
    piece_widths = [
        _compute_character_width(image_fonts[choice_list[i]], p)
        if p != " "
        else space_width
        for i, p in enumerate(splitted_text)
    ]

    # Compute width and height of the entire image
    if multi_line:
        line_num = rnd.randint(1, 4)  # random number of lines
        if len(text) / line_num >= line_max:
            line_num = math.ceil(len(text) / line_max)

        assert line_num <= 4

        if len(text) >= line_num and line_num != 1:
            text_nums = split_integer_evenly(len(text), line_num)
        else:
            text_nums = [len(text)]

        piece_heights = [
            get_text_height(image_fonts[choice_list[i]], p)
            for i, p in enumerate(splitted_text)
        ]

        index = 0
        text_widths = []
        text_heights = []
        x_indexes = []
        y_positions = []
        for i, text_num in enumerate(text_nums):
            count_width = 0
            piece_height = []

            # Compute the width of a line
            for _ in range(text_num):
                count_width += piece_widths[index]
                piece_height.append(piece_heights[index])
                index += 1
            if not word_split:
                count_width += character_spacing * (text_num - 1)

            max_line_height = max(piece_height)
            text_widths.append(count_width)
            text_heights.append(max_line_height)

            # Compute y of start point in each line
            for _ in range(text_num):
                x_indexes.append(sum(text_nums[:i]))
                y_positions.append(sum(text_heights[:i]))

        text_width = max(text_widths)
        text_height = sum(text_heights)
    else:
        line_num = 1
        x_indexes = [0 for _ in range(len(splitted_text))]
        y_positions = [0 for _ in range(len(splitted_text))]
        text_width = sum(piece_widths)
        if not word_split:
            text_width += character_spacing * (len(text) - 1)

        text_height = max(
            [
                get_text_height(image_fonts[choice_list[i]], p)
                for i, p in enumerate(splitted_text)
            ]
        )

    txt_img = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))
    txt_mask = Image.new("RGB", (text_width, text_height), (0, 0, 0))

    txt_img_draw = ImageDraw.Draw(txt_img)
    txt_mask_draw = ImageDraw.Draw(txt_mask, mode="RGB")
    txt_mask_draw.fontmode = "1"

    new_text = []
    prev_x = 0
    for i, (p, x, y) in enumerate(zip(splitted_text, x_indexes, y_positions)):
        if x != prev_x:
            prev_x = x
            new_text.append("\\\\")
        new_text.append(p)

        fill_colors = list(
            colorsys.hls_to_rgb(
                rnd.uniform(0, 1), rnd.uniform(0, 0.7), rnd.uniform(0, 1)
            )
        )
        fill = (
            int(fill_colors[0] * 255),
            int(fill_colors[1] * 255),
            int(fill_colors[2] * 255),
        )
        stroke_colors = list(
            colorsys.hls_to_rgb(
                rnd.uniform(0, 1), rnd.uniform(0, 0.7), rnd.uniform(0, 1)
            )
        )
        stroke_fill = (
            int(stroke_colors[0] * 255),
            int(stroke_colors[1] * 255),
            int(stroke_colors[2] * 255),
        )
        txt_img_draw.text(
            (
                sum(piece_widths[x:i])
                + (i - x) * character_spacing * int(not word_split),
                y,
            ),
            p,
            fill=fill,
            font=image_fonts[choice_list[i]],
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )
        txt_mask_draw.text(
            (
                sum(piece_widths[x:i])
                + (i - x) * character_spacing * int(not word_split),
                y,
            ),
            p,
            fill=((i + 1) // (255 * 255), (i + 1) // 255, (i + 1) % 255),
            font=image_fonts[choice_list[i]],
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )

    if "\\\\" in new_text:
        new_text = (
            "\\begin{matrix} "
            + " ".join(new_text).replace("   ", " ")
            + " \\end{matrix}"
        )
    else:
        new_text = text

    if fit:
        return (
            txt_img.crop(txt_img.getbbox()),
            txt_mask.crop(txt_img.getbbox()),
            line_num,
        )
    else:
        return txt_img, txt_mask, line_num, new_text


def _generate_vertical_text(
    text: str,
    font: str,
    text_color: str,
    font_size: int,
    space_width: int,
    character_spacing: int,
    fit: bool,
    stroke_width: int = 0,
    stroke_fill: str = "#282828",
) -> Tuple:
    image_font = ImageFont.truetype(font=font, size=font_size)

    space_height = int(get_text_height(image_font, " ") * space_width)

    char_heights = [
        get_text_height(image_font, c) if c != " " else space_height for c in text
    ]
    text_width = max([get_text_width(image_font, c) for c in text])
    text_height = sum(char_heights) + character_spacing * len(text)

    txt_img = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))
    txt_mask = Image.new("RGBA", (text_width, text_height), (0, 0, 0, 0))

    txt_img_draw = ImageDraw.Draw(txt_img)
    txt_mask_draw = ImageDraw.Draw(txt_mask)
    txt_mask_draw.fontmode = "1"

    colors = [ImageColor.getrgb(c) for c in text_color.split(",")]
    c1, c2 = colors[0], colors[-1]

    fill = (
        rnd.randint(c1[0], c2[0]),
        rnd.randint(c1[1], c2[1]),
        rnd.randint(c1[2], c2[2]),
    )

    stroke_colors = [ImageColor.getrgb(c) for c in stroke_fill.split(",")]
    stroke_c1, stroke_c2 = stroke_colors[0], stroke_colors[-1]

    stroke_fill = (
        rnd.randint(stroke_c1[0], stroke_c2[0]),
        rnd.randint(stroke_c1[1], stroke_c2[1]),
        rnd.randint(stroke_c1[2], stroke_c2[2]),
    )

    for i, c in enumerate(text):
        txt_img_draw.text(
            (0, sum(char_heights[0:i]) + i * character_spacing),
            c,
            fill=fill,
            font=image_font,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )
        txt_mask_draw.text(
            (0, sum(char_heights[0:i]) + i * character_spacing),
            c,
            fill=((i + 1) // (255 * 255), (i + 1) // 255, (i + 1) % 255),
            font=image_font,
            stroke_width=stroke_width,
            stroke_fill=stroke_fill,
        )

    if fit:
        return txt_img.crop(txt_img.getbbox()), txt_mask.crop(txt_img.getbbox())
    else:
        return txt_img, txt_mask
