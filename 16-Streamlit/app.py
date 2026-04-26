import streamlit as st
import pandas as pd
import numpy as np

## TITLE OF THE APLICATION
st.title("Hello Streamlit")

## DISPLAY A SIMPLE TEXT
st.write("This is a simple text")

## CREATE A SIMPLE DATAFRAME
df = pd.DataFrame({"first column": [1, 2, 3, 4], "second column": [10, 20, 30, 40]})


## DISPLAY THE DATAFRAME
st.write("Here is the dataframe")
st.write(df)


## CREATE A LINE CHART
chart_data = pd.DataFrame(np.random.randn(20, 3), columns=["a", "b", "c"])
st.line_chart(chart_data)

## TO RUN THIS APP, USE THE COMMAND IN INTEGRATED TERMINAL: streamlit run app.py
