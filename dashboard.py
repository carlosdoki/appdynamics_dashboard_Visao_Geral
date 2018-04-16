import json
import requests
import sys
from copy import deepcopy

WIDGETS_PER_LINE = 10

x_offset = 155
y_offset = 160

host = ''
port = ''
user = ''
password = ''
account = ''


def get_applications(host, port, user, password, account):
    url = 'https://{}:{}/controller/rest/applications'.format(host, port)
    auth = ('{}@{}'.format(user, account), password)
    print(auth)
    params = {'output': 'json'}

    print('Getting apps', url)
    r = requests.get(url, auth=auth, params=params)
    return sorted(r.json(), key=lambda k: k['name'])


def create_widgets_labels(APPS, widget_template):
    print('Creating Labels')
    widgets = []
    start_x = 10
    start_y = 0
    current_y = start_y

    counter = 0
    for application in APPS:
        app = application['name'][:20]
        app_id = application['id']
        print('Creating label for', app)
        new_widget = widget_template
        line_position = counter % WIDGETS_PER_LINE

        if line_position == 0 and counter >= WIDGETS_PER_LINE:
            current_y += y_offset

        new_widget['width'] = len(app) * 10
        new_widget['y'] = current_y

        base_x = start_x + line_position * x_offset
        new_widget['x'] = base_x + ((130 - len(app) * 10) / 2)

        print('@', new_widget['x'], new_widget['y'])

        new_widget["text"] = app

        widgets.append(new_widget.copy())
        counter += 1
    return widgets


def create_widgets_hrs(APPS, widget_template):
    widgets = []
    start_x = 20
    start_y = 40
    current_y = start_y

    counter = 0
    for application in APPS:
        app = application['name']
        app_id = application['id']
        print('Creating widget for', app)
        new_widget = widget_template
        line_position = counter % WIDGETS_PER_LINE

        if line_position == 0 and counter >= WIDGETS_PER_LINE:
            current_y += y_offset

        new_widget['x'] = start_x + line_position * x_offset
        new_widget['y'] = current_y
        new_widget['fontSize'] = 12

        print('@', new_widget['x'], new_widget['y'])

        new_widget["applicationReference"]["applicationName"] = app
        new_widget["applicationReference"]["entityName"] = app

        for entity in new_widget['entityReferences']:
            entity["applicationName"] = app

        print(new_widget['applicationReference'])
        widgets.append(deepcopy(new_widget))
        counter += 1
    return widgets


def create_widgets_metric(APPS, widget_template, start_x, start_y):
    widgets = []
    current_y = start_y

    counter = 0
    for application in APPS:
        app = application['name']
        app_id = application['id']
        print('Creating metrics for', app)
        new_widget = widget_template
        line_position = counter % WIDGETS_PER_LINE

        if line_position == 0 and counter >= WIDGETS_PER_LINE:
            current_y += y_offset

        new_widget['x'] = start_x + line_position * x_offset
        new_widget['y'] = current_y

        print('@', new_widget['x'], new_widget['y'])

        new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
            'applicationName'] = app

        # try:
        # new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
        #    'entityMatchCriteria']['metricMatchCriteriaTemplate'][0]['applicationName'] = app

        # new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
        #    'entityMatchCriteria']['metricMatchCriteriaTemplate'][0]['entityName'] = app

        # except KeyError:
        new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
            'entityMatchCriteria']['entityNames'][0]['applicationName'] = app
        new_widget['dataSeriesTemplates'][0]['metricMatchCriteriaTemplate'][
            'entityMatchCriteria']['entityNames'][0]['entityName'] = app

        widgets.append(deepcopy(new_widget))
        counter += 1
    return widgets


def process(dash):

    APPS = get_applications(host, port, user, password, account)
    new_dash = dash
    new_widgets = []
    for widget in new_dash['widgetTemplates']:
        if widget['widgetType'] == 'HealthListWidget':
            new_widgets += create_widgets_hrs(APPS, widget)

        if widget['widgetType'] == 'TextWidget':
            new_widgets += create_widgets_labels(APPS, widget)

        if widget['widgetType'] == 'MetricLabelWidget':

            new_widgets += create_widgets_metric(APPS,
                                                 widget, widget['x'], widget['y'])

    new_dash['widgetTemplates'] = new_widgets

    # print(json.dumps(new_dash, indent=4, sort_keys=True))
    with open('new_dash_{}.json'.format(host), 'w') as outfile:
        json.dump(new_dash, outfile, indent=4, sort_keys=True)


def main():
    global host
    global port
    global user
    global password
    global account

    try:
        host = sys.argv[1] 
        port = sys.argv[2]
        user = sys.argv[3]
        password = sys.argv[4]
        account = sys.argv[5]

        with open('dashboard.json') as json_data:
            d = json.load(json_data)
            process(d)

    except:
        print 'dashboard.py <host> <port> <user> <password> <account>'
        sys.exit(2)


if __name__ == '__main__':
    main()
