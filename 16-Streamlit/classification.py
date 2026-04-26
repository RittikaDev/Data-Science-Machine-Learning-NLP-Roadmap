import streamlit as st
import pandas as pd
from sklearn.datasets import load_iris
from sklearn.ensemble import RandomForestClassifier


@st.cache_data  # CACHE THE DATA LOADING FUNCTION TO IMPROVE PERFORMANCE, EVERYTIME THE FUNCTION IS CALLED, IT WILL CHECK IF THE DATA HAS BEEN LOADED BEFORE AND RETURN THE CACHED VERSION IF AVAILABLE
def load_data():
    iris = load_iris()  # LOAD THE IRIS DATASET
    # CREATE A DATAFRAME WITH THE FEATURES
    df = pd.DataFrame(iris.data, columns=iris.feature_names)
    df["species"] = iris.target  # TARGET FEATURE
    return df, iris.target_names


df, target_names = load_data()

model = RandomForestClassifier()
# TRAIN THE MODEL USING THE FEATURES (ALL COLUMNS EXCEPT THE LAST ONE) AND THE TARGET (THE LAST COLUMN)
model.fit(df.iloc[:, :-1], df["species"])

st.sidebar.title("Input Features")
sepal_length = st.sidebar.slider(
    "Sepal length",
    float(df["sepal length (cm)"].min()),
    float(df["sepal length (cm)"].max()),
)
sepal_width = st.sidebar.slider(
    "Sepal width",
    float(df["sepal width (cm)"].min()),
    float(df["sepal width (cm)"].max()),
)
petal_length = st.sidebar.slider(
    "Petal length",
    float(df["petal length (cm)"].min()),
    float(df["petal length (cm)"].max()),
)
petal_width = st.sidebar.slider(
    "Petal width",
    float(df["petal width (cm)"].min()),
    float(df["petal width (cm)"].max()),
)

input_data = [[sepal_length, sepal_width, petal_length, petal_width]]

## PREDICTION
prediction = model.predict(input_data)
predicted_species = target_names[prediction[0]]

st.write("Prediction")
st.write(f"The predicted species is: {predicted_species}")
