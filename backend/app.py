from flask import Flask, render_template, request, redirect, session
import zcatalyst_sdk
import os,logging
from datetime import date
import ast


logger = logging.getLogger()

app = Flask(__name__)
today = date.today()

@app.route('/upDateOrderToComplete',methods=['PUT'])
def upDateAOrderToComplete():
    try:
        catalyst = zcatalyst_sdk.initialize(req=request)
        order_id = request.args.get('id')
        datastore_service = catalyst.datastore()
        table_service = datastore_service.table("Orders")
        row_data = {'order_status': 2, 'ROWID': order_id}
        row_response = table_service.update_row(row_data)
        row_response['status']=200
        return row_response
    except Exception as error:
        print(error)
        return {'status':400}


def updateUserDetailInReponse(item, catalyst):
    authentication_service = catalyst.authentication()
    for i in item:
        user_id = i['Orders']['order_took_by']
        user = authentication_service.get_user_details(user_id)
        user_name = user['first_name']+" "+user['last_name']
        i['Orders']['order_took_by_name'] = user_name
    return item

@app.route('/getAllOrders',methods=['GET'])
def getAllOrders():
    try:
        catalyst = zcatalyst_sdk.initialize(req=request)
        zcql_service = catalyst.zcql()
        query_to_get_all_uncooked_item = "select * from orders where createdtime >= '{today_date}' and order_status = 1 or order_status =  0 order by order_number".format(
            today_date=str(today) + (" 00:00:00"))
        uncooked_item = zcql_service.execute_query(query_to_get_all_uncooked_item)
        uncooked_item = updateUserDetailInReponse(uncooked_item, catalyst)
        query_to_get_all_cooked_item = "select * from orders where createdtime >= '{today_date}' and order_status = 2 order by order_number".format(
            today_date=str(today) + (" 00:00:00"))
        cooked_item = zcql_service.execute_query(query_to_get_all_cooked_item)
        cooked_item = updateUserDetailInReponse(cooked_item, catalyst)
        response = {'uncooked': uncooked_item, 'cooked': cooked_item, "code": 200}
        return response
    except Exception as error:
        print(error)
        return {"code":400}


@app.route('/addToOrders', methods=['POST'])
def addToOrders():

    try:
        data = request.form.get('data')
        data = ast.literal_eval(data)

        item = data['item']
        order_took_by = data['order_took_by']

        curr_order_number = 1
        catalyst = zcatalyst_sdk.initialize(req=request)

        datastore_service = catalyst.datastore()
        zcql_service = catalyst.zcql()

        query_to_get_last_order_number = "select * from Orders where CREATEDTIME >= '{today_data}' ORDER BY CREATEDTIME desc limit 1".format(
            today_data=str(today) + str(" 00:00:00:000"))
        query_res = zcql_service.execute_query(query_to_get_last_order_number)

        if (len(query_res) != 0):
            if (query_res[0]["Orders"]['order_number'] == None):
                query_res[0]["Orders"]['order_number'] = 0
            curr_order_number = int(query_res[0]["Orders"]['order_number']) + 1

        row_data = {'Orders': item, 'order_took_by': order_took_by, 'order_number': curr_order_number}

        table_service = datastore_service.table("Orders")

        row_response = table_service.insert_row(row_data)
        row_response["code"] = 200

        return row_response
    except Exception as error:
        print(error)
        return {"code":400}

listen_port = os.getenv('X_ZOHO_CATALYST_LISTEN_PORT', 9000)
app.run(host='0.0.0.0', port = listen_port)
