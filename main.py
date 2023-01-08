from fastapi import FastAPI, Request, Query, Response, Form
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.templating import Jinja2Templates
import pandas as pd
from fastapi.staticfiles import StaticFiles
from fastapi import Depends
import models
from database import SessionLocal, engine
from sqlalchemy.orm import load_only
from datetime import datetime
from typing import Optional
import json


models.Base.metadata.create_all(bind=engine)

app = FastAPI()

# Dependency


def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# startup event
""" @app.on_event("startup")
def startup_populate_db():
    db = SessionLocal()
    n_recs = db.query(models.Sales).count()
    if n_recs == 0:
        df = pd.read_csv('sales_data.csv')
        df1 = df.drop(['asp_index', 'units_index', 'low_growth', 'high_growth'], axis=1)
        data = df1.to_dict('records')        
        for rec in data:
            db.add(models.Sales(**rec))            
        db.commit()
    else:
        print("All Good")
    db.close() """


app.mount("/static", StaticFiles(directory='static'), name='static')

templates = Jinja2Templates(directory="templates")


@app.get("/index/")
async def index(request: Request):
    startbtnText = 'Show'
    input_names = [0, 1]
    context = {'request': request, 'startbtnText': startbtnText,
               'input_names': input_names}
    return templates.TemplateResponse("index.html", context)


@app.post("/form_example/")
async def form_example(request: Request):
    a = (await request.form())
    print(a)

    return templates.TemplateResponse("form_example.html", {'request': request})


@app.get("/txtchange/")
async def txtchange(request: Request):
    getbtnText = request.query_params.getlist('vis')[0]
    if getbtnText == 'Show':
        getbtnText = 'Hide'
        visibility = 'visible'
    else:
        getbtnText = 'Show'
        visibility = 'invisible'
    context = {'request': request,
               'getbtnText': getbtnText, 'visibility': visibility}
    return templates.TemplateResponse("txtchange.html", context)


@app.get("/main/")
async def index(request: Request, db: SessionLocal = Depends(get_db)):
    sales = db.query(models.Sales).limit(10)
    sls = pd.read_sql(sales.statement, engine, index_col='id')

    mydf = sls.to_dict('records')

    markets = db.query(models.Sales.market).distinct()
    product_line = db.query(models.Sales.product_line).distinct()
    brands = db.query(models.Sales.brand).distinct()
    sub_brands = db.query(models.Sales.sub_brand).distinct()
    components = db.query(models.Sales.component).distinct()
    context = {'request': request, 'df': mydf, 'markets': markets, 'product_line': product_line,
               'brands': brands, 'sub_brands': sub_brands, 'components': components}
    return templates.TemplateResponse("main.html", context)


@app.get("/opt/")
async def index(request: Request, db: SessionLocal = Depends(get_db)):
    cols = columns()['col_dict']
    markets = get_markets(db)
    product_line = get_product_line(db)
    brands = get_brands(db)
    sub_brands = get_sub_brands(db)
    components = get_components(db)
    context = {'request': request, 'array': cols, 'markets': markets, 'product_line': product_line,
               'brands': brands, 'sub_brands': sub_brands, 'components': components}
    return templates.TemplateResponse("opt.html", context)


@app.get("/skuselect/")
async def skuselect(request: Request, db: SessionLocal = Depends(get_db)):
    val = request.query_params.getlist('val')[0]
    yrs = columns()['col_data_only']
    yrs_x = columns()['graph_header_list']
    sales = db.query(models.Sales).filter(models.Sales.sku == val).options(load_only('y_2017', 'y_2018', 'y_2019',
                                                                                     'y_2020', 'y_2021', 'y_2022', 'y_2023', 'y_2024', 'y_2025', 'y_2026', 'y_2027', 'y_2028', 'y_2029', 'y_2030'))
    sls = pd.read_sql(sales.statement, engine, index_col='id')
    y_vals = sls.to_dict('records')

    arr = []

    for i in yrs:
        arr.append(y_vals[0][i])

    stock_dat = {
        'x0': yrs_x,
        'y0': arr}

    context = {'request': request, 'stock_dat': stock_dat, 'val': val}
    return templates.TemplateResponse("skuselect.html", context)


@app.get("/filter_comp_to_skus/")
def filter_comp_to_skus(request: Request, component: str, db: SessionLocal = Depends(get_db)):
    dd_params = request.query_params

    return table_refresh(request, 'table', dd_params, db, component, '')['response']


@app.get("/changed_records/")
def changed_record(request: Request, db: SessionLocal = Depends(get_db)):
    dd_params = request.query_params


@app.get("/editableEg/")
def editable(request: Request):
    component_id = request.query_params.getlist('component_id')[0]
    beforeVal = request.query_params.getlist('beforeVal')[0]
    id = request.query_params.getlist('id')[0]
    field = request.query_params.getlist('field')[0]

    return templates.TemplateResponse("editable.html", {'request': request, 'component_id': component_id, 'beforeVal': beforeVal, 'id': id, 'field': field})


@app.get("/change_editable/")
def change_editable(request: Request):
    component_id = request.query_params.getlist('component_id')[0]
    beforeVal = request.query_params.getlist('beforeVal')[0]
    id = request.query_params.getlist('id')[0]
    field = request.query_params.getlist('field')[0]
    return templates.TemplateResponse("change_editable.html", {'request': request, 'component_id': component_id, 'beforeVal': beforeVal, 'id': id, 'field': field})


@app.post("/noteditableEg/")
async def noteditable(request: Request, id: str, component_id: str, beforeVal: str, field: str, db: SessionLocal = Depends(get_db)):
    c2 = None
    a = (await request.form())
    afterVal = list(a.values())[0]
    update_dict = {'table_id': id, 'field_name': field, 'old_value': beforeVal,
                   'new_value': afterVal, 'changed_on': str(datetime.now())}
    if afterVal != beforeVal:
        db.add(models.Audit(**update_dict))
        db.query(models.Sales).filter(
            models.Sales.id == id).update({field: afterVal})
        db.commit()
        c2 = table_refresh(request, 'record', '', db, '', id)['context_oob']

    c1 = {'request': request, 'component_id': component_id,
          'afterVal': afterVal, 'id': id, 'field': field}
    if c2 != None:
        context = {**c1, **c2}
    else:
        context = c1
    a = (context['mydf_diff'][0])
    b = ([context['field']][0])

    response = templates.TemplateResponse("noteditable.html", context)
    return response


@app.post("/change_noteditable/")
async def change_noteditable(request: Request, id: str, component_id: str, beforeVal: str, field: str, db: SessionLocal = Depends(get_db)):
    c2 = None
    a = (await request.form())
    afterVal = list(a.values())[0]

    tab_row = get_table_row(db, id)
    table_content_df = pd.read_sql(tab_row.statement, engine)
    new_Value = table_content_df[field] + float(afterVal) - float(beforeVal)
    update_dict = {'table_id': id, 'field_name': field,
                   'old_value': table_content_df[field], 'new_value': new_Value, 'changed_on': str(datetime.now())}
    db.add(models.Audit(**update_dict))
    db.query(models.Sales).filter(
        models.Sales.id == id).update({field: new_Value})
    db.commit()
    c2 = table_refresh(request, 'record', '', db, '', id)['context_oob']

    c1 = {'request': request, 'component_id': component_id,
          'afterVal': afterVal, 'id': id, 'field': field}
    if c2 != None:
        context = {**c1, **c2}

    else:
        context = c1

    response = templates.TemplateResponse("change_noteditable.html", context)
    return response


def chart_func(table_content):
    table_content_df = pd.read_sql(
        table_content.statement, engine, index_col='id')
    yrs = columns()['col_data_only']
    yrs_x = columns()['graph_header_list']
    sls_all = table_content_df[columns()['col_data_only']]
    y_vals_all = sls_all.to_dict('records')
    arr_all = []
    arr_all_temp = []
    for i in y_vals_all:
        for j in yrs:
            arr_all_temp.append(i[j])
        arr_all.append(arr_all_temp)
        arr_all_temp = []
    sparkline = {
        'x0': yrs_x,
        'y0': arr_all
    }
    return sparkline


def columns():
    col_dict = {

        'sku': {
            'is_data': False,
            'is_user_gen': False,
            'header': 'SKU',
            'header_color': 'bg-white',
            'text_color': '',
            'bg_color': '',
            'width': 'w-14',
        },
        'sku_desc': {
            'is_data': False,
            'is_user_gen': False,
            'header': 'ID',
            'header_color': 'bg-white',
            'text_color': '',
            'bg_color': '',
            'width': 'w-14'
        },
        'cost': {
            'is_data': False,
            'is_user_gen': False,
            'header': 'Cost',
            'header_color': 'bg-white',
            'text_color': '',
            'bg_color': '',
            'width': 'w-14'
        },
        'asp': {
            'is_data': False,
            'is_user_gen': False,
            'header': 'ASP',
            'header_color': 'bg-white',
            'text_color': '',
            'bg_color': '',
            'width': 'w-14'
        },
        'margin': {
            'is_data': False,
            'is_user_gen': False,
            'header': 'Margin',
            'header_color': 'bg-white',
            'text_color': '',
            'bg_color': '',
            'width': 'w-14'
        },
        'y_2017': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2017',
            'header_color': 'bg-green-700',
            'text_color': 'text-white',
            'bg_color': 'bg-gray-200',
            'width': 'w-24'
        },
        'y_2018': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2018',
            'header_color': 'bg-green-700',
            'text_color': 'text-white',
            'bg_color': '',
            'width': 'w-24'
        },
        'y_2019': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2019',
            'header_color': 'bg-green-700',
            'text_color': 'text-white',
            'bg_color': 'bg-gray-200',
            'width': 'w-24'
        },
        'y_2020': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2020',
            'header_color': 'bg-green-700',
            'text_color': 'text-white',
            'bg_color': '',
            'width': 'w-24'
        },
        'y_2021': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2021',
            'header_color': 'bg-green-700',
            'text_color': 'text-white',
            'bg_color': 'bg-gray-200',
            'width': 'w-24'
        },
        'y_2022': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2022',
            'header_color': 'bg-purple-700',
            'text_color': 'text-white',
            'bg_color': '',
            'width': 'w-24'
        },
        'y_2023': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2023',
            'header_color': 'bg-red-900',
            'text_color': 'text-white',
            'bg_color': 'bg-gray-200',
            'width': 'w-24'
        },
        'y_2024': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2024',
            'header_color': 'bg-red-900',
            'text_color': 'text-white',
            'bg_color': '',
            'width': 'w-24'
        },
        'y_2025': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2025',
            'header_color': 'bg-red-900',
            'text_color': 'text-white',
            'bg_color': 'bg-gray-200',
            'width': 'w-24'
        },
        'y_2026': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2026',
            'header_color': 'bg-red-900',
            'text_color': 'text-white',
            'bg_color': '',
            'width': 'w-24'
        },
        'y_2027': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2027',
            'header_color': 'bg-red-900',
            'text_color': 'text-white',
            'bg_color': 'bg-gray-200',
            'width': 'w-24'
        },
        'y_2028': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2028',
            'header_color': 'bg-red-900',
            'text_color': 'text-white',
            'bg_color': '',
            'width': 'w-24'
        },
        'y_2029': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2029',
            'header_color': 'bg-red-900',
            'text_color': 'text-white',
            'bg_color': 'bg-gray-200',
            'width': 'w-24'
        },
        'y_2030': {
            'is_data': True,
            'is_user_gen': False,
            'header': '2030',
            'header_color': 'bg-red-900',
            'text_color': 'text-white',
            'bg_color': '',
            'width': 'w-24'
        },
        'trend': {
            'is_data': False,
            'is_user_gen': True,
            'header': 'Trend',
            'header_color': 'bg-white',
            'text_color': '',
            'bg_color': '',
            'width': ''
        },
        'cagr': {
            'is_data': False,
            'is_user_gen': True,
            'header': 'Select CAGR',
            'header_color': 'bg-white',
            'text_color': '',
            'bg_color': '',
            'width': 'w-64'
        },
    }

    col_table_show = ['id', 'sku', 'sku_desc', 'cost', 'asp', 'margin', 'y_2017', 'y_2018', 'y_2019', 'y_2020',
                      'y_2021', 'y_2022', 'y_2023', 'y_2024', 'y_2025', 'y_2026', 'y_2027', 'y_2028', 'y_2029', 'y_2030']
    col_data_only = ['y_2017', 'y_2018', 'y_2019', 'y_2020', 'y_2021', 'y_2022',
                     'y_2023', 'y_2024', 'y_2025', 'y_2026', 'y_2027', 'y_2028', 'y_2029', 'y_2030']
    graph_header_list = ['Y2017', 'Y2018', 'Y2019', 'Y2020', 'Y2021', 'Y2022',
                         'Y2023', 'Y2024', 'Y2025', 'Y2026', 'Y2027', 'Y2028', 'Y2029', 'Y2030']
    context = {'col_dict': col_dict, 'col_table_show': col_table_show,
               'col_data_only': col_data_only, 'graph_header_list': graph_header_list}
    return context


def get_markets(db):
    return db.query(models.Sales.market).distinct()


def get_product_line(db):
    return db.query(models.Sales.product_line).distinct()


def get_brands(db):
    return db.query(models.Sales.brand).distinct()


def get_sub_brands(db):
    return db.query(models.Sales.sub_brand).distinct()


def get_components(db):
    return db.query(models.Sales.component).distinct()


def get_table_data(db, component, params):
    return db.query(models.Sales).filter(models.Sales.component == component, models.Sales.sub_brand == params['sub_brand'], models.Sales.market == params['market'].replace("_", " "))


def get_table_row(db, id):
    return db.query(models.Sales).filter(models.Sales.id == id)


def table_refresh(request, req_type, params, db, component, id):
    if req_type == 'table':
        table_content = get_table_data(db, component, params)
    else:
        table_content = get_table_row(db, id)

    cols = columns()['col_dict']

    table_content_df = pd.read_sql(table_content.statement, engine)
    table_content_df = table_content_df[columns()['col_table_show']]

    table_data_only = table_content_df[columns()['col_data_only']]
    mydf_diff = table_data_only.diff(periods=1, axis=1)

    mydf_diff_color = pd.DataFrame().reindex_like(mydf_diff)
    mydf_diff_color.fillna('', inplace=True)
    mydf_diff_color[mydf_diff < 0] = 'bg-red-500'
    mydf_diff_color[mydf_diff >= 0] = 'bg-green-500'
    mydf_diff.fillna('', inplace=True)
    mydf_diff = mydf_diff.to_dict('records')
    mydf_diff_color = mydf_diff_color.to_dict('records')
    table_content_dict = table_content_df.to_dict('records')
    context = {'request': request, 'table_contents': table_content_dict, 'mydf_diff': mydf_diff,
               'mydf_diff_colors': mydf_diff_color, 'sparkline': chart_func(table_content), 'cols': cols}
    response = templates.TemplateResponse("showTable.html", context)
    context_oob = {'table_contents': table_content_dict, 'mydf_diff': mydf_diff,
                   'mydf_diff_colors': mydf_diff_color, 'sparkline': chart_func(table_content), 'cols': cols}

    return {'response': response, 'context_oob': context_oob}
