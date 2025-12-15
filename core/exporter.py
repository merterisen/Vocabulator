import pandas as pd

class Exporter:
    """
    Handles saving dataframes to various file formats.
    """
    
    @staticmethod
    def to_csv(dataframe, filepath):
        dataframe.to_csv(filepath, index=False)

    @staticmethod
    def to_excel(dataframe, filepath):
        import openpyxl
        dataframe.to_excel(filepath, index=False)