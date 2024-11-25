# Import necessary modules
from shiny import App, ui, render, Inputs  # Import everything directly from shiny
import pandas as pd
import joblib
import numpy as np
from ipyleaflet import Map, Choropleth, Marker, Popup
from ipywidgets.embed import embed_minimal_html
from branca.colormap import linear
from ipywidgets import HTML
import json
import tempfile
import os
import folium
from shiny.types import ImgData
import matplotlib
matplotlib.use('Agg')  # Set the backend before importing pyplot
import matplotlib.pyplot as plt

# Load the model and data
best_model = joblib.load("AppData/best_model.pkl")
best_columns = joblib.load("AppData/model_columns.pkl")
income_data = pd.read_csv("AppData/eda_processed_adult.csv")
scaler = joblib.load("AppData/best_scaler.pkl")

# Define the to_str_choices function
def to_str_choices(series, descending=False):
    values = series.unique()
    if descending:
        values = sorted(values, reverse=True)
    return [str(x) for x in values]

def ensure_numeric(df, columns):
    for col in columns:
        df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
    return df

def prepare_income_input(user_input):
    input_df = pd.DataFrame([user_input])
    input_df = ensure_numeric(input_df, best_columns)
    input_df = pd.get_dummies(input_df)
    input_df = input_df.reindex(columns=best_columns, fill_value=0)
    scaled_input_df = input_df.copy()
    scaled_input_df[scaler.feature_names_in_] = scaler.transform(input_df[scaler.feature_names_in_])
    return scaled_input_df



# Define the UI layout with custom styling
app_ui = ui.page_fluid(
    # CSS style with green theme
    ui.tags.style("""
        .value-box {
            height: 200px;
            background-color: #e8f5e9;
            border-left: 6px solid #2e7d32;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
        }
        .grid-map-container {
            height: 300px;
            background-color: #f1f8e9;
            border: 1px solid #81c784;
            border-radius: 4px;
        }
        .sidebar {
            background-color: #f1f8e9;
            padding: 20px;
            border-right: 2px solid #81c784;
        }
        .shiny-input-container {
            margin-bottom: 15px;
            background-color: #ffffff;
            padding: 10px;
            border-radius: 4px;
            border: 1px solid #a5d6a7;
        }
        h3 {
            color: #2e7d32;
            border-bottom: 2px solid #81c784;
            padding-bottom: 10px;
        }
    """),

    ui.layout_sidebar(
        ui.sidebar(
            ui.h3("Income Prediction Dashboard", width=1),
            ui.input_select("age", "Age:", choices=to_str_choices(income_data["age"], descending=True)),
            ui.input_select("education_num", "Education Level:",choices=to_str_choices(income_data["educational-num"], descending=True)),
             
            ui.input_select("hours_per_week", "Hours per Week:", 
                          choices=to_str_choices(income_data["hours-per-week"], descending=True)),
            ui.input_select("relationship", "Relationship:", choices=to_str_choices(income_data["relationship"])),              
            class_="sidebar"
        ),
        # Layout for the map and data grid with titles and fixed heights
        ui.layout_column_wrap(
            # Data Grid with title
            ui.div(
                ui.h3("Explore Income Data"),  # Title for the data grid
                ui.output_data_frame("income_data_grid"),
                class_="fixed-height-container"
            ),
            # Updated Map section
            ui.div(
                ui.h3("Income Distribution Map"),
                ui.output_plot("income_map"),  # Changed to output_plot
                class_="fixed-height-container"
            ),
                    
            width=1/2
        )
    )
)


# Define the server function
def server(input, output, session):
    @output
    @render.text
    def predicted_income():
        try:
            user_input = {
                "age": input.age(),
                "education-num": input.education_num(),
                "hours-per-week": input.hours_per_week(),
                "relationship": input.relationship(),
            }
            input_df = prepare_income_input(user_input)
            prediction = best_model.predict(input_df)[0]
            return f"Predicted Income: {'≤50K' if prediction == 0 else '>50K'}"
        except Exception as e:
            return f"Error: {str(e)}"

    @output
    @render.text
    def average_income():
        return f"Average Income in Dataset: {income_data['income'].value_counts().to_string()}"

    @output
    @render.data_frame
    def income_data_grid():
        return render.DataGrid(income_data,filters=True)

    
    @output
    @render.ui
    def income_data_chart():
        selected_column = input.INCOME_SELECT_INPUT()
        filtered_data = income_data[[selected_column]]
        chart = filtered_data.plot(kind='bar')
        return ui.output_plot(chart.get_figure())

    @output
    @render.plot
    def income_map():
        # Create a figure and axis objects with specific backend
        fig = plt.figure(figsize=(10, 6))
        ax = fig.add_subplot(111)
        
        # Create the visualization
        income_counts = income_data['income'].value_counts()
        bars = ax.bar(income_counts.index, income_counts.values, color=['#81c784', '#2e7d32'])
        
        # Add titles and labels
        ax.set_title('Income Distribution', pad=20)
        ax.set_xlabel('Income Category')
        ax.set_ylabel('Count')
        
        # Adjust layout to prevent cutting off
        fig.tight_layout()
        
        return fig

    

# Render the App
app = App(app_ui, server)

if __name__ == "__main__":
    app.run()
