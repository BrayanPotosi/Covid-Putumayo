# Requests
from requests.exceptions import ConnectionError, Timeout, TooManyRedirects
from requests import Session

# Flask
from flask import Flask, request, make_response, redirect, render_template

# Bokeh
from bokeh.models import ColumnDataSource
from bokeh.transform import factor_cmap
from bokeh.io import output_file, show
from bokeh.plotting import figure
from bokeh.layouts import row

# Mysql Connector
import mysql.connector

import datetime
import json

app = Flask(__name__)


@app.route('/')
def generate_document():
    print_local_graph()
    return redirect('/graph')


@app.route('/graph')
def show_map():
    return render_template('Covid_map.html')


# Database connector
database = mysql.connector.connect(
    host='',
    user='',
    passwd='',
    database=''
)

# Endpoint variables
department_name = 'PUTUMAYO'
str_date = datetime.datetime.now().strftime('%d-%m-%Y')
url_base = 'https://www.datos.gov.co/resource/gt2j-8ykr.json?'
param = f'departamento_nom={department_name}&recuperado=Activo&$limit=5000'
full_url = url_base + param


def get_data_api(full_url):
    """receive a url and return a list of dictionaries with data"""
    try:
        session = Session()
        response = session.get(full_url)
        response.encoding = 'utf-8'
        data = json.loads(response.text)
        return data

    except (ConnectionError, Timeout, TooManyRedirects) as e:
        return e


def get_cities_list(url=full_url):
    """Returns an ordered list of cities in the department specified in the URL"""
    data = get_data_api(url)
    cities_list = sorted(list({name["ciudad_municipio_nom"] for name in data}))

    return cities_list


def get_total_cases_per_city(url=full_url):
    """Return a list with the total number of cases per each city"""
    data = get_data_api(url)
    cities_list = get_cities_list()
    active_cases_list = []

    for i in range(len(cities_list)):
        cases_in_city = len([patient for patient in data if patient["ciudad_municipio_nom"] == cities_list[i]])
        active_cases_list.append(cases_in_city)

    return active_cases_list


def perform_query_db(db, queries, fetch_registers=True):
    """Allow to make a query using the db connector as a parameter and the query as string format"""
    query = f"{queries}"
    cursor = db.cursor()
    cursor.execute(query)
    result = cursor.fetchall()
    db.commit()

    if fetch_registers:
        return result


def save_registers_db():
    """Use the date and total_cases variable to add a new register in the database"""
    active_cases_list = get_total_cases_per_city()
    total_cases = sum(active_cases_list)

    try:
        perform_query_db(database, f"INSERT INTO cases (date_casesx, numbercases) VALUES ('{str_date}', {total_cases})",
                         fetch_registers=False)
    except:
        print('\nError: El registro de hoy ya fue completado')


def print_local_graph():
    """generates an html document with graphics showing the cases of covid
    in the current date by municipalities and a historical graphic of the department"""

    active_cases_list = get_total_cases_per_city()
    cities_list = get_cities_list()
    dates = perform_query_db(database, 'SELECT date_casesx FROM cases ORDER BY id ASC')
    total_cases = perform_query_db(database, 'SELECT numbercases FROM cases ORDER BY id ASC')
    save_registers_db()

    output_file("./templates/Covid_map.html")
    color_list = ['#3288bd'] * len(cities_list)
    source = ColumnDataSource(data=dict(cities_list=cities_list, active_cases=active_cases_list))

    p = figure(x_range=cities_list, plot_height=500, plot_width=800, toolbar_location=None,
               title=f"Casos activos de Covid-19 en {department_name.capitalize()} para la fecha : {str_date}")

    p.vbar(x='cities_list', top='active_cases', width=0.9, source=source,
           line_color='white', fill_color=factor_cmap('cities_list',
                                                      palette=color_list, factors=cities_list))

    p.xaxis.major_label_orientation = 1
    p.xgrid.grid_line_color = None
    p.y_range.start = 0
    p.y_range.end = max(active_cases_list) + 30

    x = [element[0] for element in dates]
    y = [element[0] for element in total_cases]

    p1 = figure(title="Grafica historica Putumayo", x_axis_label="Fecha", y_axis_label="Numero de casos",
                plot_height=500, plot_width=450, x_range=x)

    p1.line(x, y, line_width=2)
    p1.xaxis.major_label_orientation = 1

    show(row(p, p1))
