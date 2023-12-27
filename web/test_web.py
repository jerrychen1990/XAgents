

def load_view():
    # return
    import streamlit as st

    import pandas as pd

    from st_aggrid import AgGrid
    st.info("load view")

    df = pd.read_csv('https://raw.githubusercontent.com/fivethirtyeight/data/master/airline-safety/airline-safety.csv')

    st.info("show table")
    st.table(df)

    st.info("show grid")
    AgGrid(data=df)
    st.write("fd")
