import requests
import pandas as pd
import seaborn as sns
import pprint
import argparse
argparser = argparse.ArgumentParser()
argparser.add_argument('--buildno', type=str, default=3079)
args = argparser.parse_args()

def getResponse():
    buildno = args.buildno
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
        precision = 'undefined'
    return precision


def recall(cm):
    '''
    recall = True Positive/Predicted Results
    recall = TP/TP+FN
    '''
    predicted_result = cm['tp'] + cm['fn']
    try:
        recall = cm['tp'] / predicted_result
    except:
        recall = 'undefined'
    return recall

def plot(json_results):
    data = (json_results['results'])
    df = pd.DataFrame(data)
    kfdb = sns.catplot(x='kfdb_status', kind='count', palette='ch:0.95', data=df, hue='cycle')
    eval = sns.catplot(x='evaluation_status', kind='count', palette='ch:0.95', data=df, hue='cycle')
    kfdb.savefig("kfdb.png")
    eval.savefig("eval.png")

def extractMode(build):
    buildid = build.split()
    mode = buildid[-3].split('-')
    return(mode[-3])

def extractVersion(suite):
    version = ''.join([n for n in suite if n.isdigit()])
    return version

def latest_jsonResults_buildarray(json_results):
    a = [(result['config']['name'], result['buildURL'], result['build']) for result in json_results['results']]
    a = list(set(a))
    a.sort()
    df = pd.DataFrame(a)
    df.sort_values([0,2], inplace=True)
    df.drop_duplicates(keep='last', subset=[0, 2], inplace=True)
    latest_array  = df[1].to_list()
    return latest_array

json_results = getResponse()
# print(json_results)
confusion_matrix_gold = {'tp': 0,
                    'tn': 0,
                    'fp': 0,
                    'fn': 0,
                    'unaccounted': 0}
confusion_matrix_silver = {'tp': 0,
                    'tn': 0,
                    'fp': 0,
                    'fn': 0,
                    'unaccounted': 0}

if json_results['ok'] == 1:
    latest_array = latest_jsonResults_buildarray(json_results)
    #
    # silver_configs = []
    # silver_versions = []
    # silver_modes = []
    #
    # gold_configs = []
    # gold_versions = []
    # gold_modes = []
    #
    # for result in json_results['results']:
    #     if result['buildURL'] in latest_array:
    #         if result['cycle'].lower() == 'silver':
    #             silver_configs.append((result['config']['name']))
    #             silver_modes.append(extractMode(result['build']))
    #             silver_versions.append(extractVersion(result['suite']))
    #         elif result['cycle'].lower() == 'gold':
    #             gold_configs.append((result['config']['name']))
    #             gold_modes.append(extractMode(result['build']))
    #             gold_versions.append(extractVersion(result['suite']))
    #
    #
    # silver_configs = ((list(set(silver_configs))))
    # silver_modes = ((list(set(silver_modes))))
    # silver_versions = ((list(set(silver_versions))))
    #
    # gold_configs = ((list(set(gold_configs))))
    # gold_modes = ((list(set(gold_modes))))
    # gold_versions = ((list(set(gold_versions))))
    # silver = []
    finalResult = []
    for test in latest_array:
        try:
            status = []
            a = {}
            for result in json_results['results']:
                if result['buildURL'] == test:
                    matrix_status = confusionMatrix(result["kfdb_status"], result["evaluation_status"])
                    # status.append({result['_id']['$oid']: matrix_status})
                    status.append({
                        "oid": result['_id']['$oid'],
                        "matrixStatus": matrix_status,
                        "kfdb_status": result['kfdb_status'],
                        "eval_status": result["evaluation_status"],
                        "test": result['test']
                    })
                    a = {'config': result['config']['name'],
                          'mode': extractMode(result['build']),
                          'version': extractVersion(result['suite']),
                          'cycle': result['cycle'],
                          'buildURL': test,
                          'matrixStatus': status,
                          'total_tests': len(status)
                    }
            finalResult.append(a)
        except:
            pass

    pprint.pprint(finalResult)

