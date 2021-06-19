import base64
import io
import os

import numpy as np
import pandas as pd
import streamlit as st

os.environ["TOKENIZERS_PARALLELISM"] = "false"

# io helpers
def xls_to_df(filename):
    df = pd.read_excel(filename)
    return df


def csv_to_df(filename):
    df = pd.read_csv(filename)
    return df


def create_download_text(href, anon_cols):

    if len(anon_cols) > 1:
        helper = "columns"
    else:
        helper = "column"

    text = f"<br>The anonymized text is stored in the {helper}"
    count = 0
    for each in anon_cols:
        if count == 0:
            text += f" <i>{each}_anonymized</i>"
        else:
            text += f" and <i>{each}_anonymized</i>"
        count += 1

    text += "."

    return st.markdown(href + text, unsafe_allow_html=True)


# constants
entities_dict = {
    "PER": "Person",
    "LOC": "Location",
    "ORG": "Organization",
    "DATE": "Date",
    "EMAIL": "E-Mail",
    "PHONE": "Phone",
    "NUMBER": "Numeric ID",
}

selection_mode = ["Single Text", "File Upload"]

# helper function
def gen_entities(entities, input):
    """generates entities from inputlist"""
    all = list(entities.keys())
    result = [enty for enty, keep in zip(all, input) if keep]
    return result


###########################
## APP
###########################
st.set_page_config(page_title="🧰 Open Anonymizer - Anonymize German (Survey) Texts", layout="wide")

hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """

st.markdown(hide_streamlit_style, unsafe_allow_html=True)

with st.spinner(text="Initializing models..."):
    from src.anon import *
    from src.visual import *

st.sidebar.title("🧰 Open Anonymizer")
st.sidebar.text("  Anonymize German (Survey) Texts")
st.sidebar.markdown("---")

###########################
## SELECT
###########################
# col_1, _, _ = st.beta_columns(3)
# mode_select = col_1.selectbox("Select if you want to anonymize a single text or a file.", selection_mode)
# st.markdown("---")

mode_select = st.sidebar.selectbox(
    "Select if you want to anonymize a single text or a file.", selection_mode
)
st.sidebar.markdown("<br>", unsafe_allow_html=True)

###########################
## SIDEBAR
###########################
# st.sidebar.header("Options for anonymization")


def sidebar_a():
    with st.beta_expander("Entites for model-based anonymization", True):
        sidebar_col_1, sidebar_col_2 = st.beta_columns(2)

        a = [
            sidebar_col_1.checkbox(entities_dict["PER"], value=True, key=1, help=None),
            sidebar_col_1.checkbox(entities_dict["LOC"], value=True, key=2, help=None),
            sidebar_col_2.checkbox(entities_dict["ORG"], value=True, key=3, help=None),
        ]
    st.write("")
    return a


def sidebar_b():
    with st.beta_expander("Entities for rule-based anonymization", True):
        sidebar_col_1, sidebar_col_2 = st.beta_columns(2)

        b = [
            sidebar_col_1.checkbox(entities_dict["DATE"], value=True, key=4, help=None),
            sidebar_col_1.checkbox(entities_dict["EMAIL"], value=True, key=5, help=None),
            sidebar_col_2.checkbox(entities_dict["PHONE"], value=True, key=6, help=None),
            sidebar_col_2.checkbox(entities_dict["NUMBER"], value=True, key=7, help=None),
        ]
    st.write("")
    return b


def sidebar_c():
    with st.beta_expander("Additional options", True):
        no_context = not st.checkbox(
            "Preserve context",
            value=True,
            key=8,
            help="Should context be preserved? E.g. PERSON_1 instead of XXX",
        )
        keep_adresses = st.checkbox(
            "Preserve terms of adress",
            value=False,
            key=8,
            help="Should terms of adress (e.g. Frau/Herr) be preserved?",
        )
    st.write("")
    return (no_context, keep_adresses)


with st.sidebar:
    # st.write("Select entities to anonymize")
    a = sidebar_a()
    b = sidebar_b()
    c = sidebar_c()

# all inputs from sidebar
inputlist = a + b  # inputlist=[True,True,True,True,False,False,False]
no_context = c[0]
keep_adresses = c[1]


######################################
# MAIN
######################################
if mode_select == selection_mode[0]:

    # with st.beta_expander("Live-Demo", True):

    text = st.text_area(
        "Try Open Anonymizer by entering your text below",
        "Wegen der hohen Inzidenzrate von über 150 bleiben Kaufhäuser (z.B. Karstadt) weiterhin geschlossen, teilte Frau Henriette Reker dem Tagesspiegel am 01.05.2021 in Köln mit. Fragen beantwortet die Stadt Köln via E-Mail (info@stadt-koeln.de) und telefonisch unter 0211 556677. Weitere Informationen finden Sie unter dem Aktenzeichen 2021/0815",
        max_chars=1000,
        height=100,
    )

    sanitize_button = st.button("Anonymize")

    st.markdown("---")

    if sanitize_button:

        # get entities to anonimize, based on selection:
        entities = gen_entities(entities_dict, inputlist)

        cleaned_text, mapping = anon_pipeline(text, entities, keep_adresses)
        output_text = remove_context(cleaned_text) if no_context else cleaned_text

        ######################################
        # OUTPUT
        ######################################
        col1, col2 = st.beta_columns(2)
        with col1:
            st.header("Input")
            highlight_text(cleaned_text, mapping)

        with col2:
            st.header("Output")
            highlight_text(output_text, [], False)


if mode_select == selection_mode[1]:
    # with st.beta_expander("File upload for anonymization", False):

    # st.write(
    #     "**Please follow the three steps below to upload and anonymize your own data (xls, xlsx & csv-format are supported)**"
    # )

    uploaded_file = st.file_uploader(
        "Step 1: Upload the file you want to anonymize", type=["csv", "xls", "xlsx"]
    )

    st.markdown("---")

    if uploaded_file is not None:

        # Step1
        #######
        # transform file to pd

        filename, file_extension = os.path.splitext(uploaded_file.name.lower())

        if ".xls" in file_extension or ".xlsx" in file_extension:
            data = xls_to_df(filename=uploaded_file)
        elif ".csv" in file_extension:
            data = csv_to_df(filename=uploaded_file)
        else:
            print("Error - not supported filetype")

        if len(data.index) > 250:
            st.info(
                f"This Web-App only supports files with up to 250 rows. Your input data will be reduced from {len(data.index)} to 250 rows!"
            )

        # reduce input data - # limit! to 500 rows
        df2 = data.head(250)  

        # Step2
        #######
        # check if columns are are available in file

        if len(list(df2.columns)) < 1:
            st.error("Error: No columns found in input-file!")
        else:
            columns_to_anonymize = st.multiselect(
                "Step 2: Select column(s) that should be anonymized and submit with the button below",
                # ["<<please select>>"] + list(data.columns),
                list(data.columns),
            )

        batch_anon_button = st.button("Start anonymizing")
        st.markdown("---")

        # select relevant column:
        if batch_anon_button and columns_to_anonymize and len(list(data.columns)) > 0:

            # new columnname
            for each_anon_col in columns_to_anonymize:
                anonymized_column = f"{each_anon_col}_anonymized"

                # check if column is numbers-only
                if df2[each_anon_col].dtype == np.number:
                    st.error(f"Error: {each_anon_col} does not contain text!")

                else:
                    # actual anonimization
                    entities = gen_entities(entities_dict, inputlist)

                    with st.spinner(text="Applying models..."):
                        df2[anonymized_column] = [
                            anon_pipeline(txtrow, entities, keep_adresses)[0]
                            for txtrow in list(df2[each_anon_col])
                        ]
                        # st.success('Done')

                # write result to file
            new_filename = f"{filename}_anonymized{file_extension}"

            if ".xls" in file_extension or ".xlsx" in file_extension:
                # data = xls_to_df(filename=uploaded_file)
                towrite = io.BytesIO()
                xlsx = df2.to_excel(towrite, encoding="utf-8", index=False, header=True)
                towrite.seek(0)  # reset pointer
                b64 = base64.b64encode(towrite.read()).decode()
                href = f'Step 3: <a href="data:application/vnd.openxmlformats-officedocument.spreadsheetml.sheet;base64,{b64}" download="{new_filename}">Download anonymized excel file</a> (right-click and "save as")'

            elif ".csv" in file_extension:
                new_filename = f"{filename}_anonymized.csv"
                # data = csv_to_df(filename=uploaded_file)
                csv = df2.to_csv(index=False)
                b64 = base64.b64encode(
                    csv.encode()
                ).decode()  # some strings <-> bytes conversions necessary here
                href = f'Step 3: <a href="data:file/csv;base64,{b64}" download="{new_filename}">Download anonymized CSV file</a> (right-click and "save as"). '

            # Step3
            #######
            create_download_text(href, columns_to_anonymize)


###########################
## FOOTER
###########################

footer = """<style>
a:link , a:visited{
color: blue;
background-color: transparent;
text-decoration: underline;
}

a:hover,  a:active {
color: red;
background-color: transparent;
text-decoration: underline;
}

.footer {
position: fixed;
left: 0;
bottom: 0;
width: 100%;
background-color: white;
color: black;
text-align: center;
}
</style>
<div class="footer">
<p>Developed by <a href="mailto:dimiepp@gmail.com" target="_blank">Dimitri Epp</a> and <a href="mailto:Markus.Nutz@gmx.de" target="_blank">Markus Nutz</a> (2021)
<br>More about this <a href="https://github.com/open-anonymizer/" target="_blank">Project</a>.  Full code on <a href="https://github.com/open-anonymizer/">  <img alt="github" src="https://github.githubassets.com/images/modules/site/icons/footer/github-mark.svg"></a></p>
</div>
"""

st.markdown(footer, unsafe_allow_html=True)
