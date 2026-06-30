import streamlit as st
import pandas as pd
import numpy as np
import requests
import json
import time


def main():
    print("Hello from cost-of-getting-info-of-files!")
    """
    # PDF retrieval 
    Add pdf documents to calculate cost per query:
    """

    uploaded_files = st.file_uploader(
        " ",  # empty label due to styling purposes
        accept_multiple_files=True,
        type=["pdf"],
        key="file-uploader",
    )
    if uploaded_files == []:  #  if uploaded_files != []: # TODO
        number_of_files = st.select_slider(
            "How many similar files are expected?",
            options=(1, 10, 100, 1000, 10e3, 10e4, 10e5),
            format_func=format_number,
            on_change=enable_what_is_number_of_users,  # set_question_allowed(question_name="what_is_number_of_users"),
        )
        number_of_users = st.slider(
            "What is the number of users that need to use app?",
            # options=(1, 10, 100, 1000, 10e3, 10e4),
            # format_func=format_number,
            format="localized",
            on_change=enable_what_is_number_of_users,  # set_question_allowed(question_name="what_is_number_of_users"),
        )
        number_of_request_per_user = st.select_slider(
            "What is the average number of requests per user daily?",
            options=(1, 10, 50, 250),
            format_func=format_number,
            on_change=enable_what_is_number_of_users,  # set_question_allowed(question_name="what_is_number_of_users"),
        )
        # st.write(download_gemini_pricing_page())

    if st.checkbox("Show example"):
        """
        ## Example: NIST.SP.800-53r5
        Similar files (words per document): 10 \n
        Expected users: 10 \n
        """
        if st.checkbox("Show sources"):
            st.write(
                "https://cloud.google.com/gemini-enterprise-agent-platform/generative-ai/pricing"
            )


def format_number(number):
    "Format numbers as in PEP 378 https://peps.python.org/pep-0378/"
    return "{:,}".format(number)


def set_question_allowed(question_name):
    st.session_state[question_name] = True


def toggle_widget(widget_name):
    if not widget_name.enabled:
        widget_name.enabled = True
    elif widget_name.enabled:
        widget_name.enabled = False


def enable_what_is_number_of_users():
    # st.write("OK")
    pass


if __name__ == "__main__":
    main()
