import numpy as np
import pandas as pd
from flask import Flask, render_template, url_for, request, redirect
from collections import Collection

np.random.seed(0)


def basic_stuff():
    """
    https://stackoverflow.com/questions/41470817/edit-pandas-dataframe-in-flask-html-page
    """
    df = pd.DataFrame(np.random.randint(0, 100, (3, 3)))
    print(df)

    rndr = df.style.format('<input name="df" value="{}" />').render()
    print('\n\n')
    print(rndr)

    # re-create the data frame using
    # df = pd.DataFrame(np.asarray(request.values.getlist('df'), dtype=np.int).reshape(df.shape))
    print('\n\n')
    print(df)


# class DFTable(pd.DataFrame):
#     """
#
#     https://stackoverflow.com/questions/41470817/edit-pandas-dataframe-in-flask-html-page
#     """
#     def __init__(self, data=None, index:Collection=None, columns:Collection=None, dtype=None,
#                  copy:bool=False, table_name='cell'):
#         super(DFTable, self).__init__(data=data, index=index, columns=columns, dtype=dtype,
#                                      copy=copy)
#         self.table_name = table_name
#
#     def to_html_inputs(self):
#         # return super().style.format(f'<input name="{self.table_name}" ' + 'value="{}" />').render()
#         def html_input(c):
#             return '<input name="{}" value="{{}}" />'.format(c)
#         return super().style.format({c: html_input(c) for c in super().columns}).render()
#
#     def from_html(self):
#         # return pd.DataFrame(request.values.lists())
#         self.from_dict(data=dict(request.values.lists()))


class DFTable():
    """

    https://stackoverflow.com/questions/41470817/edit-pandas-dataframe-in-flask-html-page
    """
    def __init__(self, df:pd.DataFrame=pd.DataFrame(), table_name='cell'):
        self.df = df
        if not isinstance(df, pd.DataFrame):
            self.df = pd.DataFrame(df)
        self.table_name = table_name

    def to_html_inputs(self, df = None):
        df = df or self.df
        # return super().style.format(f'<input name="{self.table_name}" ' + 'value="{}" />').render()
        def html_input(c):
            return '<input name="{}" value="{{}}" />'.format(c)
        return df.style.format({c: html_input(c) for c in df.columns}).render()

    def from_form(self):
        self.df =  pd.DataFrame(request.values.lists())
        return self.df

def dftable_example():
    df= DFTable(df=[[1,2,3],[4,5,6]])
    print(df)
    print(df.to_html_inputs())

dftable_example()