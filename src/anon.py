import os
import re
from copy import deepcopy

import streamlit as st

from transformers import pipeline


def concat_elements(tag, spacer, text, counter):
    searchpattern = tag + "_([0-9]{1,2})(" + spacer + ")" + tag + "_([0-9]{1,2})"
    check_wrong = re.search(searchpattern, text)
    if check_wrong:
        old_first = f"{tag}_{check_wrong[1]}"
        old_second = f"{tag}_{check_wrong[3]}"

        text = text.replace(check_wrong[0], old_first)

        check_wrong = re.search(old_second, text)
        if not check_wrong:
            counter -= 1

    return text, counter


def clean_entities(text: str, pipeline, entities: list, replace_address: bool = True, mapping={}):

    found = [
        e for e in pipeline(text) if e.get("entity_group") in entities and len(e.get("word")) > 1
    ]
    mapping = {}

    if not found:
        return text, mapping

    count_per = 0
    count_loc = 0
    count_org = 0

    for each in found:

        word = each.get("word")
        if not word in mapping.values():

            if each.get("entity_group") == "PER":
                count_per += 1
                name = f"PERSON_{count_per}"

                if replace_address:
                    matches = re.findall(
                        rf"(?:^|\s)(((?:Herrn|Herr|Frau|Doktor|Familie|Hr\.|Fr\.|Dr\.|[A-Z]\.)[\s]*)?{word}[\w]*)",
                        text,
                    )

                    for person_match in matches:
                        text = text.replace(person_match[0], name)
                        mapping.update({name: person_match[0]})

                else:
                    matches = re.findall(rf"({word}[\w]*)", text)

                    for person_match in matches:
                        text = text.replace(person_match, name)
                        mapping.update({name: person_match})

                # Concat multi word names: PERSON_1 PERSON_2 -> PERSON_1
                text, count_per = concat_elements("PERSON", "\s+|[a-z]+", text, count_per)

            elif each.get("entity_group") == "LOC":

                count_loc += 1
                name = f"LOCATION_{count_loc}"
                matches = re.findall(
                    rf"(?:^|\s)(((?:[0-9][0-9][0-9][0-9][0-9]|[0-9][0-9][0-9][0-9])[\s\,\.][\.]*)?{word}[\w]*)",
                    text,
                )

                for location_match in matches:
                    text = text.replace(location_match[0], name)
                    mapping.update({name: location_match[0]})

                # correcting some locations
                text, count_loc = concat_elements("LOCATION", "[a-z]+", text, count_loc)

            elif each.get("entity_group") == "ORG":
                count_org += 1
                name = f"ORG_{count_org}"

                matches = re.findall(rf"({word}[\w]*)", text)
                for org_match in matches:
                    text = text.replace(org_match, name)
                    mapping.update({name: org_match})

                text, count_org = concat_elements("ORG", "[a-z]+", text, count_org)

    return text, mapping


def clean_regex_helper(text, pattern, placeholder, show_length=False, mapping={}):

    mapping = {}

    matches = re.findall(pattern, text)
    matches = [m if isinstance(m, str) else m[0] for m in matches]

    if placeholder == "DATE":
        matches = [m for m in matches if 5 < len(m) < 11]

    if not matches:
        return text, mapping

    count_no = 0

    for match in matches:

        if not match in mapping.values():
            count_no += 1
            placeholder_num = placeholder + "_"

            placeholder_num += str(count_no)
            if show_length:
                placeholder_num += "_" + str(len(match))

            text = text.replace(match, placeholder_num)
            mapping[placeholder_num] = match

    return text, mapping


def regex_clean_email(text, mapping={}):
    return clean_regex_helper(
        text, r"([a-zA-Z0-9._%+-]+@[a-zA-Z0-9._%+-]+(\.[a-zA-Z]{2,})?)", "EMAIL", mapping
    )


def regex_clean_phone(text, mapping={}):
    return clean_regex_helper(
        text,
        r"(?:^|[^\d])((?:\+|0)[0-9]{2,6}(\-|\s|\/|\_|\:)?[0-9]{2,9}(\-|\s|\/|\_|\:)?[0-9]{2,14})",
        "PHONE",
        mapping,
    )


def regex_clean_date(text, mapping={}):
    return clean_regex_helper(
        text,
        r"([0-3]?[0-9]{1,4}[._%+-/][0-3]?[0-9]{1,4}([._%+-/])[0-3]?[0-9]{1,4})",
        "DATE",
        mapping,
    )


def regex_clean_number(text, mapping={}, count: bool = True):
    return clean_regex_helper(
        text, r"([0-9]{2}[0-9-\.\s\/\-\/\_\:]{3,}[0-9]{2})", "NUMBER", count, mapping
    )


@st.cache(allow_output_mutation=True)
def init_pipeline(model_name):
    """
    Load model and return pipeline
    """
    print(f"loading model: {model_name}")
    nlp = pipeline("ner", model=model_name, grouped_entities=True)
    return nlp


def remove_context(text):
    """
    remove entities
    """

    re1 = "PERSON_[0-9]{1,2}"
    re2 = "LOCATION_[0-9]{1,2}"
    re3 = "ORG_[0-9]{1,2}"
    re4 = "EMAIL_[0-9]{1,2}"
    re5 = "PHONE_[0-9]{1,2}"
    re6 = "DATE_[0-9]{1,2}"
    re7 = "NUMBER_[0-9]{1,2}"
    re8 = "XXX_[0-9]{1,2}"

    re_list = [re1, re2, re3, re4, re5, re6, re7]
    generic_re = re.compile("|".join(re_list))

    matches = re.findall(generic_re, text)
    for m in matches:
        text = text.replace(m, "XXX")

    # number check again
    matches = re.findall(re8, text)
    for m in matches:
        text = text.replace(m, "XXX")

    return text


def anonymize_regex(input_text, input_mapping, entities):
    """requires mapping - minimum requirement: mapping ={}"""
    cleaned_text = input_text
    mapping = input_mapping

    if "DATE" in entities:
        cleaned_text, date_mapping = regex_clean_date(cleaned_text)
        mapping.update(date_mapping)
    if "PHONE" in entities:
        cleaned_text, phone_mapping = regex_clean_phone(cleaned_text)
        mapping.update(phone_mapping)
    if "NUMBER" in entities:
        cleaned_text, num_mapping = regex_clean_number(cleaned_text, True)
        mapping.update(num_mapping)
    if "EMAIL" in entities:
        cleaned_text, mail_mapping = regex_clean_email(cleaned_text)
        mapping.update(mail_mapping)

    return cleaned_text, mapping

model_used = "/app/models/xlm-roberta-large-finetuned-conll03-german/" if os.getenv("DEPLOYMENT") else "xlm-roberta-large-finetuned-conll03-german"
def anonymize_with_model(
    input_text,
    input_mapping,
    entities,
    replace_address,
    nlp=init_pipeline(
        model_used
    ),
):
    """requires mapping - minimum requirement: mapping ={}"""
    cleaned_text = input_text
    mapping = input_mapping

    if any([e in ["PER", "LOC", "ORG"] for e in entities]):

        cleaned_text, ent_mappings = clean_entities(
            text=input_text, pipeline=nlp, entities=entities, replace_address=replace_address
        )
        mapping.update(ent_mappings)

    return cleaned_text, mapping


def anon_pipeline(text, entities, keep_adresses):

    mapping = {}

    try:
        cleaned_text = deepcopy(text)

        # run regex rules #####
        cleaned_text, mapping = anonymize_regex(
            input_text=cleaned_text, input_mapping=mapping, entities=entities
        )

        # run model-based rules #####
        if any([e in ["PER", "LOC", "ORG"] for e in entities]):
            cleaned_text, mapping = anonymize_with_model(
                input_text=cleaned_text,
                input_mapping=mapping,
                entities=entities,
                replace_address=not keep_adresses,
            )

    except Exception as e:
        print(e)
        cleaned_text = "error occured"

    return cleaned_text, mapping


def remove_context(text):
    """
    remove context preserving entities and make everyting into XXXXX
    """

    re1 = "PERSON_[0-9]{1,2}"
    re2 = "LOCATION_[0-9]{1,2}"
    re3 = "ORG_[0-9]{1,2}"
    re4 = "EMAIL_[0-9]{1,2}"
    re5 = "PHONE_[0-9]{1,2}"
    re6 = "DATE_[0-9]{1,2}"
    re7 = "NUMBER_[0-9]{1,2}"
    re8 = "XXX_[0-9]{1,2}"

    re_list = [re1, re2, re3, re4, re5, re6, re7]
    generic_re = re.compile("|".join(re_list))

    matches = re.findall(generic_re, text)
    for m in matches:
        text = text.replace(m, "XXX")

    # number check again
    matches = re.findall(re8, text)
    for m in matches:
        text = text.replace(m, "XXX")

    return text
