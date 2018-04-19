import json
import requests
import sys
import base64
from copy import deepcopy

WIDGETS_PER_LINE = 10

x_offset = 155
y_offset = 160

host = ''
port = ''
user = ''
password = ''
account = ''
token = ''
cookies = ''
importacao = 0

def get_auth(host, port, user, password, account):
    url = 'https://{}:{}/controller/auth'.format(host, port)
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(user + "@" + account + ":" + password)  
    }
    params = (
        ('action', 'login'),
    )
    response = requests.get(url, headers=headers, params=params)
    global token
    global cookies
    cookies = response.cookies 
    token = response.cookies.get("X-CSRF-TOKEN")

    return 0

def get_dashboards(host, port, user, password, account):
    url = 'https://{}:{}/controller/restui/dashboards/getAllDashboardsByType/false'.format(host, port)
    params = {'output': 'json'}
    headers = {
        'Authorization': 'Basic ' + base64.b64encode(user + "@" + account + ":" + password),
        'X-CSRF-TOKEN' : token
    }
    r = requests.get(url, params=params, headers=headers, cookies=cookies)
    
    return sorted(r.json(), key=lambda k: k['name'])


def get_applications(host, port, user, password, account):
    url = 'https://{}:{}/controller/rest/applications'.format(host, port)
    auth = ('{}@{}'.format(user, account), password)
    print(auth)
    params = {'output': 'json'}

    print('Getting apps', url)
    r = requests.get(url, auth=auth, params=params)
    return sorted(r.json(), key=lambda k: k['name'])

def find_dashboard(dashboards, name):
    id = 0
    for i in dashboards:
        if i['name'] == name:
            id = i['id']
            break
    return id

def put_dashboard(host, port, user, password, account, dashboard):
    url = 'https://{}:{}/controller/CustomDashboardImportExportServlet'.format(host, port)
    auth = ('{}@{}'.format(user, account), password)
    files = {
        'file': (dashboard, open(dashboard, 'rb')),
    }
    print('import dashboard apps', dashboard)
    response = requests.post(url, files=files, auth=auth)
    print (response)

    return 0

def create_widgets_labels(APPS, widget_template, dashboards):
    print('Creating Labels')
    widgets = []
    start_x = 10
    start_y = 0
    current_y = start_y

    counter = 0
    for application in APPS:
        app = application['name'][:20]
        dash_id = find_dashboard(dashboards, application['name'])
        print('Creating label for', app)
        new_widget = widget_template
        line_position = counter % WIDGETS_PER_LINE

        if line_position == 0 and counter >= WIDGETS_PER_LINE:
            current_y += y_offset

        new_widget['width'] = len(app) * 10 + 10
        new_widget['y'] = current_y

        base_x = start_x + line_position * x_offset
        new_widget['x'] = base_x + ((130 - len(app) * 10) / 2)

        print('@', new_widget['x'], new_widget['y'])

        new_widget["text"] = app
        if dash_id != 0:
            new_widget["drillDownUrl"] = "https://{}:{}/controller/#/location=CDASHBOARD_DETAIL&timeRange=last_30_minutes.BEFORE_NOW.-1.-1.15&mode=MODE_DASHBOARD&dashboard={}".format(host, port, dash_id)
            new_widget["useMetricBrowserAsDrillDown"] = False
        
        widgets.append(new_widget.copy())
        counter += 1
    return widgets


def create_widgets_hrs(APPS, widget_template, dashboards):
    widgets = []
    start_x = 20
    start_y = 40
    current_y = start_y

    counter = 0
    for application in APPS:
        app = application['name']
        dash_id = find_dashboard(dashboards, application['name'])
        print('Creating widget for', app)
        new_widget = widget_template
        line_position = counter % WIDGETS_PER_LINE

        if line_position == 0 and counter >= WIDGETS_PER_LINE:
            current_y += y_offset

        new_widget['x'] = start_x + line_position * x_offset
        new_widget['y'] = current_y
        new_widget['fontSize'] = 12
        if dash_id != 0:
            new_widget["drillDownUrl"] = "https://{}:{}/controller/#/location=CDASHBOARD_DETAIL&timeRange=last_30_minutes.BEFORE_NOW.-1.-1.15&mode=MODE_DASHBOARD&dashboard={}".format(host, port, dash_id)
            new_widget["useMetricBrowserAsDrillDown"] = False
        
        print('@', new_widget['x'], new_widget['y'])

        new_widget["applicationReference"]["applicationName"] = app
        new_widget["applicationReference"]["entityName"] = app

        for entity in new_widget['entityReferences']:
            entity["applicationName"] = app

        print(new_widget['applicationReference'])
        widgets.append(deepcopy(new_widget))
        counter += 1
    return widgets


def create_widgets_metric(APPS, widget_template, start_x, start_y, dashboards):
    widgets = []
    current_y = start_y

    counter = 0
    for application in APPS:
        app = application['name']
        dash_id = find_dashboard(dashboards, application['name'])
        print('Creating metrics for', app)
        new_widget = widget_template
        line_position = counter % WIDGETS_PER_LINE

        if line_position == 0 and counter >= WIDGETS_PER_LINE:
            current_y += y_offset

        new_widget['x'] = start_x + line_position * x_offset
        new_widget['y'] = current_y
        if dash_id != 0:
            new_widget["drillDownUrl"] = "https://{}:{}/controller/#/location=CDASHBOARD_DETAIL&timeRange=last_30_minutes.BEFORE_NOW.-1.-1.15&mode=MODE_DASHBOARD&dashboard={}".format(host, port, dash_id)
            new_widget["useMetricBrowserAsDrillDown"] = False

        print('@', new_widget['x'], new_widget['y'])

        new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
            'applicationName'] = app
        new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
            'entityMatchCriteria']['entityNames'][0]['applicationName'] = app
        new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
            'entityMatchCriteria']['entityNames'][0]['entityName'] = app

        widgets.append(deepcopy(new_widget))
        counter += 1
    return widgets


def process(dash):
    get_auth(host, port, user, password, account)
    dashboards = get_dashboards(host, port, user, password, account)
    
    APPS = get_applications(host, port, user, password, account)
    new_dash = dash
    new_widgets = []
    for widget in new_dash['widgetTemplates']:
        if widget['widgetType'] == 'HealthListWidget':
            new_widgets += create_widgets_hrs(APPS, widget, dashboards)

        if widget['widgetType'] == 'TextWidget':
            new_widgets += create_widgets_labels(APPS, widget, dashboards)

        if widget['widgetType'] == 'MetricLabelWidget':

            new_widgets += create_widgets_metric(APPS,
                                                 widget, widget['x'], widget['y'], dashboards)

    new_dash['widgetTemplates'] = new_widgets

    # print(json.dumps(new_dash, indent=4, sort_keys=True))
    with open('new_dash_{}.json'.format(host), 'w') as outfile:
        json.dump(new_dash, outfile, indent=4, sort_keys=True)

    if importacao == '1':
        print("Importacao do Dashboard", 'new_dash_{}.json'.format(host))
        put_dashboard(host, port, user, password, account, 'new_dash_{}.json'.format(host))


def main():
    global host
    global port
    global user
    global password
    global account
    global importacao

    try:
        host = sys.argv[1] 
        port = sys.argv[2]
        user = sys.argv[3]
        password = sys.argv[4]
        account = sys.argv[5]

        if len(sys.argv) == 7 :
            importacao = sys.argv[6]

        with open('dashboard.json') as json_data:
            d = json.load(json_data)
            process(d)

    except:
        print 'dashboard.py <host> <port> <user> <password> <account> <importacao>'
        sys.exit(2)


if __name__ == '__main__':
    main()
