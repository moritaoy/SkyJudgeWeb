from django.shortcuts import render
import boto3
import markdown
from django.http import Http404, HttpResponse, HttpResponseRedirect
import os
from datetime import datetime
import random
import json

os.environ['AWS_DEFAULT_REGION'] = 'ap-northeast-1'
dynamodb = boto3.resource('dynamodb')
judgedb = dynamodb.Table('JudgeDB')


def judge_index(request):
    return render(request, "judge/index.html", {})


def judge(request, judgeID):
    judgeData = judgedb.get_item(
        Key={
            'JudgeID': judgeID
        }
    )
    if 'Item' not in judgeData:
        raise Http404('judge result not found')
    judgeresult = judgeData['Item']
    if 'Memory' in judgeresult:
        judgeresult['Memory'] *= 1024
    bg_color = "success"
    if judgeresult['JudgeStatus'] == False:
        bg_color = "secondary"
        judgeresult['ResultStatus'] = "WJ"
    elif judgeresult['Result'] == False:
        bg_color = "danger"
    else:
        bg_color = "success"
    if int(datetime.now().timestamp()) - judgeresult['SubmitDate'] < 300 and judgeresult['JudgeStatus'] == False:
        judgeresult['JudgeReload'] = True
    judgeresult['bg_color'] = bg_color
    return render(request, "judge/result.html", judgeresult)
