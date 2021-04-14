from flask import Flask
from bokeh.io import output_file, show
from bokeh.models import ColumnDataSource
from bokeh.plotting import figure
from bokeh.transform import factor_cmap
from requests import Session
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from datetime import datetime
import json

app = Flask(__name__)

url_base = 'https://www.datos.gov.co/resource/gt2j-8ykr.json?'
param = 'departamento_nom=PUTUMAYO&recuperado=Activo&$limit=5000'
url = url_base + param

session = Session()


def get_data_api():
    try:
        response = session.get(url)
        response.encoding = 'utf-8'
        data = json.loads(response.text)
        return data

    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return e


def get_positive_cases():

    data = get_data_api()
    municipalities_list = list({name["ciudad_municipio_nom"] for name in data})
    active_cases_list = []

    for i in range(len(municipalities_list)):
        aux = len([patient for patient in data if patient["ciudad_municipio_nom"] == municipalities_list[i]])

        active_cases_list.append(aux)

    print_graph(active_cases_list, municipalities_list)


def print_graph(active_cases, municipalities_list):

    output_file("bar_colormapped.html")
    color_list = ['#3288bd'] * len(municipalities_list)
    str_date = datetime.now().strftime('%d-%m-%Y')

    source = ColumnDataSource(data=dict(municipalities_list=municipalities_list, active_cases=active_cases))

    p = figure(x_range=municipalities_list, plot_height=500, plot_width=800, toolbar_location=None,
               title=f"Casos activos de Covid-19 en Putumayo para la fecha : {str_date}")

    p.vbar(x='municipalities_list', top='active_cases', width=0.9, source=source,
           line_color='white', fill_color=factor_cmap('municipalities_list',
            palette=color_list, factors=municipalities_list))

    p.xaxis.major_label_orientation = 1
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.y_range.end = max(active_cases) + 20

    show(p)


get_positive_cases()


@app.route('/')
def hello_world():
    return url
