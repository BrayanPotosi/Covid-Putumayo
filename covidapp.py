from flask import Flask, request, make_response, redirect, render_template
from bokeh.io import output_file, show
from bokeh.plotting import figure
from bokeh.models import ColumnDataSource
from bokeh.transform import factor_cmap
from bokeh.layouts import row
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
import numpy as np
import schedule
import time
import json


app = Flask(__name__)


@app.route('/')
def show_map_covid():
    user_ip = request.remote_addr
    url_api_ip = f'http://api.ipstack.com/{user_ip}?access_key=0d1fecb2deb0a75c7724b0ed4059b233'
    data = get_data_api(url_api_ip)
    get_positive_cases()

    return render_template('Covid_map.html')


department_name = 'PUTUMAYO'
str_date = datetime.now().strftime('%d-%m-%Y')
url_base = 'https://www.datos.gov.co/resource/gt2j-8ykr.json?'
param = f'departamento_nom={department_name}&recuperado=Activo&$limit=5000'
full_url = url_base + param

session = Session()


def get_data_api(full_url):
    try:
        response = session.get(full_url)
        response.encoding = 'utf-8'
        data = json.loads(response.text)
        return data

    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return e


def get_positive_cases():
    data = get_data_api(full_url)
    municipalities_list = list({name["ciudad_municipio_nom"] for name in data})
    active_cases_list = []
    for i in range(len(municipalities_list)):
        cases_in_municipality = len([patient for patient in data if patient["ciudad_municipio_nom"] == municipalities_list[i]])
        active_cases_list.append(cases_in_municipality)

    print_local_graph(active_cases_list, municipalities_list)


def print_local_graph(active_cases_list, municipalities_list):
    output_file("./templates/Covid_map.html")
    color_list = ['#3288bd'] * len(municipalities_list)
    source = ColumnDataSource(data=dict(municipalities_list=municipalities_list, active_cases=active_cases_list))

    p = figure(x_range=municipalities_list, plot_height=500, plot_width=800, toolbar_location=None,
               title=f"Casos activos de Covid-19 en {department_name.capitalize()} para la fecha : {str_date}")

    p.vbar(x='municipalities_list', top='active_cases', width=0.9, source=source,
           line_color='white', fill_color=factor_cmap('municipalities_list',
                                                      palette=color_list, factors=municipalities_list))

    p.xaxis.major_label_orientation = 1
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.y_range.end = max(active_cases_list) + 30

    total_cases_department = sum(active_cases_list)
    x = [1, 2, 3, 4, 5, 6, 7, *range(8, 90)]
    y = [total_cases_department, 100, 150, 70, 44, 120, 300, *range(90, 172)]

    p1 = figure(title="Grafica historica Putumayo", x_axis_label="Fecha", y_axis_label="Numero de casos",
                plot_height=500, plot_width=450,)

    p1.line(x, y, legend_label="Casos.", line_width=2)

    print(total_cases_department)
    show(row(p, p1))


get_positive_cases()

# schedule.every().day.at("12:00").do(get_positive_cases)
#
# while True:
#     schedule.run_pending()
