import requests
import matplotlib.pyplot as plt
import io
from matplotlib.backends.backend_agg import FigureCanvasAgg as FigureCanvas
from matplotlib.figure import Figure
from flask import Flask, Response
import pandas as pd

app = Flask(__name__)

def getResponse(buildno):
    build = f'"build":"{buildno}"'
    files = {
        'docs': (None, '[{'+build+', "suite":".*JCK.*"}]'),
    }
    try:
        response = requests.post('http://onega:8083/AutoRedGreen/_getstaticresults', files=files)
        return response.json()
    except:
        response = {'ok': 0}
        return response

def confusionMatrix(kfdb_status, evaluation_status):
    df_matrix = pd.read_pickle('variousStates.pkl')
    for _, row in df_matrix.iterrows():
        if row['kfdb'] == kfdb_status and row['eval'] == evaluation_status:
            return row['finalStatus']

def precision(cm):
    '''
    precision = True Positive/Actual Results
    precision = TP/TP+FP
    '''
    actual_result = cm['tp'] + cm['fp']
    try:
        precision = cm['tp'] / actual_result
    except:
        precision = 0
    return format(precision, '.3f')


def recall(cm):
    '''
    recall = True Positive/Predicted Results
    recall = TP/TP+FN
    '''
    predicted_result = cm['tp'] + cm['fn']
    try:
        recall = cm['tp'] / predicted_result
    except:
        recall = 0
    return format(recall, '.3f')

def extractMode(build):
    buildid = build.split()
    mode = buildid[-3].split('-')
    return(mode[-3])

def extractVersion(suite):
    version = ''.join([n for n in suite if n.isdigit()])
    return version

def latest_jsonResults_buildarray(json_results):
    latest_array = []
    try:
        a = [(result['config']['name'], result['buildURL'], result['build']) for result in json_results['results']]
        a = list(set(a))
        a.sort()
        df = pd.DataFrame(a)
        df.sort_values([0,2], inplace=True)
        df.drop_duplicates(keep='last', subset=[0, 2], inplace=True)
        latest_array = df[1].to_list()
    except:
        pass
    return latest_array

def cal(json_results):
    gold = {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0, 'unaccounted': 0}
    silver = {'tp': 0, 'tn': 0, 'fp': 0, 'fn': 0, 'unaccounted': 0}

    if json_results['ok'] == 1:
        latest_array = latest_jsonResults_buildarray(json_results)
        for result in json_results['results']:
            if result['buildURL'] in latest_array:
                try:
                    matrix_status = confusionMatrix(result["kfdb_status"], result["evaluation_status"])
                    if matrix_status == 'tp':
                        if result["cycle"] == 'Silver':
                            silver['tp'] += 1
                        elif result["cycle"] == 'Gold':
                            gold['tp'] += 1
                    elif matrix_status == 'tn':
                        if result["cycle"] == 'Silver':
                            silver['tn'] += 1
                        elif result["cycle"] == 'Gold':
                            gold['tn'] += 1
                    elif matrix_status == 'fp':
                        if result["cycle"] == 'Silver':
                            silver['fp'] += 1
                        elif result["cycle"] == 'Gold':
                            gold['fp'] += 1
                    elif matrix_status == 'fn':
                        if result["cycle"] == 'Silver':
                            silver['fn'] += 1
                        elif result["cycle"] == 'Gold':
                            gold['fn'] += 1
                    else:
                        if result["cycle"] == 'Silver':
                            silver['unaccounted'] += 1
                        elif result["cycle"] == 'Gold':
                            gold['unaccounted'] += 1
                except:
                    pass
    else:
        pass

    precision_gold = precision(gold)
    recall_gold = recall(gold)


    precision_silver = precision(silver)
    recall_silver = recall(silver)

    return {'gold': {'precision' : precision_gold,
                     'recall': recall_gold,
                     'confusionMatrix': gold},
            'silver': {'precision': precision_silver,
                     'recall': recall_silver,
                     'confusionMatrix': silver},
            }

def create_figure(builds, gold_precision, gold_recall, silver_precision, silver_recall):
    fig = Figure(figsize=(20, 20))
    fig.suptitle('Precision Recall Martix', fontsize=16)
    grid = plt.GridSpec(4, 1, hspace=0.8, wspace=5)

    axis = fig.add_subplot(grid[0:1, :])
    axis2 = fig.add_subplot(grid[1:2, :])
    axis3 = fig.add_subplot(grid[2:3, :])
    axis4 = fig.add_subplot(grid[3:4, :])

    axis.grid()
    axis2.grid()
    axis3.grid()
    axis4.grid()

    axis.title.set_text('Gold Precision')
    axis2.title.set_text('Gold Recall')
    axis3.title.set_text('Silver Precision')
    axis4.title.set_text('Silver Recall')

    axis.plot(builds, gold_precision)
    axis2.plot(builds, gold_recall)
    axis3.plot(builds, silver_precision)
    axis4.plot(builds, silver_recall)

    return fig

def getArray(results):
    # return {'rr':results}
    builds = []
    gold_precision = []
    gold_recall = []
    silver_precision = []
    silver_recall = []
    for result in results:
        builds.append(list(result.keys())[0])
        gold_precision.append((result[builds[-1]]['gold']['precision']))
        gold_recall.append((result[builds[-1]]['gold']['recall']))
        silver_precision.append((result[builds[-1]]['silver']['precision']))
        silver_recall.append((result[builds[-1]]['silver']['recall']))
    return (builds, gold_precision, gold_recall, silver_precision, silver_recall)

def getArrayOf_CM(results):
    builds = []
    gold_tp = []
    gold_tn = []
    gold_fp = []
    gold_fn = []
    silver_tp = []
    silver_tn = []
    silver_fp = []
    silver_fn = []
    for result in results:
        builds.append(list(result.keys())[0])

        gold_confusionMatrix = (result[builds[-1]]['gold']['confusionMatrix'])
        silver_confusioMatrix = (result[builds[-1]]['silver']['confusionMatrix'])

        gold_tp.append(gold_confusionMatrix['tp'])
        gold_tn.append(gold_confusionMatrix['tn'])
        gold_fp.append(gold_confusionMatrix['fp'])
        gold_fn.append(gold_confusionMatrix['fn'])

        silver_tp.append(silver_confusioMatrix['tp'])
        silver_tn.append(silver_confusioMatrix['tn'])
        silver_fp.append(silver_confusioMatrix['fp'])
        silver_fn.append(silver_confusioMatrix['fn'])

    return (builds, gold_tp, gold_tn, gold_fp, gold_fn, silver_tp, silver_tn, silver_fp, silver_fn)

def calGrid(json_results):
    if json_results['ok'] == 1:
        latest_array = latest_jsonResults_buildarray(json_results)
        finalResult = []
        for test in latest_array:
            try:
                status = []
                a = {}
                for result in json_results['results']:
                    if result['buildURL'] == test:
                        matrix_status = confusionMatrix(result["kfdb_status"], result["evaluation_status"])
                        status.append({
                            "oid": result['_id']['$oid'],
                            "matrixStatus": matrix_status,
                            "test": result['test'],
                            "kfdb_status": result['kfdb_status'],
                            "eval_status": result["evaluation_status"]
                        })
                        a = {'config': result['config']['name'],
                             'mode': extractMode(result['build']),
                             'version': extractVersion(result['suite']),
                             'cycle': result['cycle'],
                             'matrixStatus': status,
                             'buildURL': test,
                             'total_tests': len(status),
                             }
                finalResult.append(a)
            except:
                pass

        return finalResult

@app.route('/', defaults={'str1': '0', 'str2': '0'}, methods=['GET', 'POST'])
@app.route('/matrix', defaults={'str1': '0', 'str2': '0'}, methods=['GET', 'POST'])
@app.route('/matrix/', defaults={'str1': '0', 'str2': '0'}, methods=['GET', 'POST'])
@app.route('/matrix/<str1>/<str2>/', methods=['GET', 'POST'])
def matrix(str1, str2):
    results = []

    for build in range(int(str1), int(str2)):
        json_results = getResponse(build)
        result = cal(json_results)
        results.append({build: result})
    return {'result': results}

@app.route('/matrix/grid', defaults={'str1': '3092'}, methods=['GET', 'POST'])
@app.route('/matrix/grid/', defaults={'str1': '3092'}, methods=['GET', 'POST'])
@app.route('/matrix/grid/<str1>/', methods=['GET', 'POST'])
def grid(str1):
    build = int(str1)
    json_results = getResponse(build)
    result = calGrid(json_results)
    return {'result': result}

@app.route('/aggregate', defaults={'str1': '0', 'str2': '0'}, methods=['GET', 'POST'])
@app.route('/aggregate/', defaults={'str1': '0', 'str2': '0'}, methods=['GET', 'POST'])
@app.route('/aggregate/<str1>/<str2>/', methods=['GET', 'POST'])
def aggregate(str1, str2):
    results = []
    for build in range(int(str1), int(str2)):
        json_results = getResponse(build)
        result = cal(json_results)
        results.append({build: result})
    (builds, gold_tp, gold_tn, gold_fp, gold_fn, silver_tp, silver_tn, silver_fp, silver_fn) = getArrayOf_CM(results)

    gold_tps = sum(gold_tp)
    gold_tns = sum(gold_tn)
    gold_fps = sum(gold_fp)
    gold_fns = sum(gold_fn)

    silver_tps = sum(silver_tp)
    silver_tns = sum(silver_tn)
    silver_fps = sum(silver_fp)
    silver_fns = sum(silver_fn)

    gold_actual_result = gold_tps + gold_fps
    silver_actual_result = silver_tps + silver_fps

    gold_pred_result = gold_tps + gold_fns
    silver_pred_result = silver_tps + silver_fns
    gold_agg_precision = silver_agg_precision = gold_agg_recall = silver_agg_recall = 0
    try:
        gold_agg_precision = gold_tps/gold_actual_result
        silver_agg_precision = silver_tps / silver_actual_result

        gold_agg_recall = gold_tps / gold_pred_result
        silver_agg_recall = silver_tps / silver_pred_result

    except:
        pass

    return {'gold_agg_precision': format(gold_agg_precision, '.3f'),
            'silver_agg_precision': format(silver_agg_precision, '.3f'),
            'gold_agg_recall': format(gold_agg_recall, '.3f'),
            'silver_agg_recall': format(silver_agg_recall, '.3f'),

            'gold_tps': format(gold_tps, '.3f'),
            'gold_tns': format(gold_tns, '.3f'),
            'gold_fps': format(gold_fps, '.3f'),
            'gold_fns': format(gold_fns, '.3f'),

            'silver_tps': format(silver_tps, '.3f'),
            'silver_tns': format(silver_tns, '.3f'),
            'silver_fps': format(silver_fps, '.3f'),
            'silver_fns': format(silver_fns, '.3f'),

            }

@app.route('/matrix/plot', defaults={'str1': '0', 'str2': '0'}, methods=['GET', 'POST'])
@app.route('/matrix/plot/', defaults={'str1': '0', 'str2': '0'}, methods=['GET', 'POST'])
@app.route('/matrix/plot/<str1>/<str2>/', methods=['GET', 'POST'])
def plot(str1, str2):
    results =[]
    for build in range(int(str1), int(str2)):
        json_results = getResponse(build)
        result = cal(json_results)
        results.append({build: result})
    (builds, gold_precision, gold_recall, silver_precision, silver_recall) = getArray(results)

    fig = create_figure(builds, gold_precision, gold_recall, silver_precision, silver_recall)
    output = io.BytesIO()
    FigureCanvas(fig).print_png(output)
    return Response(output.getvalue(), mimetype='image/png')

if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5002)