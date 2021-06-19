import re

import streamlit as st

from htbuilder import HtmlElement, div, span, styles
from htbuilder.units import em, px, rem

# colors from https://www.schemecolor.com/rainbow-pastels-color-scheme.php + yellow: FF0B9 FAFFBB
tuples = {
    "PERSON": ("Person", "#C7CEEA"),
    "ORG": ("Organization", "#B5EAD7"),
    "LOCATION": ("Location", "#E2F0CB"),
    "DATE": ("Date", "#FF9AA2"),
    "EMAIL": ("E-Mail", "#FFC5C1"),  # FFB7B2
    "PHONE": ("Phone", "#FFDAC1"),
    "NUMBER": ("Numeric ID", "#FAFFBB"),
}


def annotation(body, label="", background="#ddd", color="#333", **style):

    if "font_family" not in style:
        style["font_family"] = "sans-serif"

    return span(
        style=styles(
            background=background,
            border_radius=rem(0.33),
            color=color,
            padding=(rem(0.17), rem(0.67)),
            display="inline-flex",
            justify_content="center",
            align_items="center",
            **style,
        )
    )(
        body,
        span(
            style=styles(
                color=color,
                font_size=em(0.67),
                opacity=0.9,
                padding_left=rem(0.5),
                text_transform="uppercase",
                margin_bottom=px(-2),
            )
        )(label),
    )


def annotated_text(list_text, *args, **kwargs):
    out = div(style=styles(font_family="sans-serif", line_height="1.5", font_size=px(16)))
    for arg in list_text:
        if isinstance(arg, str):
            out(arg)
        elif isinstance(arg, HtmlElement):
            out(arg)
        elif isinstance(arg, tuple):
            out(annotation(*arg))
        else:
            raise Exception("Oh noes!")

    st.components.v1.html(str(out), width=None, height=800, **kwargs)


def highlight_text(text, mapping, with_label=True):

    text_array = re.split(
        "((?:PERSON|ORG|LOCATION|EMAIL|DATE|PHONE|NUMBER_[0-9]{1,2})_[0-9]+)", text
    )

    for index, elm in enumerate(text_array):

        match = re.match(r"^([A-Z_]+)(_[0-9]+)?_[0-9]+$", elm)

        if match:

            if mapping:
                orig_text = mapping.get(elm)
            else:
                orig_text = elm

            tuple = tuples.get(match.group(1))

            if with_label:
                tuple = (orig_text, tuple[0], tuple[1])
            else:
                tuple = (orig_text, "", tuple[1])

            text_array[index] = tuple

    annotated_text(text_array)
