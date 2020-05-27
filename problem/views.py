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
sqs = boto3.client('sqs')
queue_url = "https://sqs.ap-northeast-1.amazonaws.com/433403878829/JudgeDataQueue"


problemdb = dynamodb.Table('ProblemDB')
judgedb = dynamodb.Table('JudgeDB')
sequencedb = dynamodb.Table('sequences')
# Create your views here.

test = "# Welcome to SkyJudge!\n### このページは？\nこのページはサンプルの問題を表示しています！\n他の人の作成した問題を解く場合は、上のメニューバーにある**入力欄**に**ProblemID**を入力して、移動してください。\n\n### ProblemIDとは？\n例えば、この問題のProblemIDは`PAHello-World`です。\n問題を作成すると、それぞれに1つProblemIDが発行されます。\n基本的にProblemIDは`P`から始まります。\n\nもし、解きたい問題のProblemIDが解らない場合は、問題の作問者に問い合わせてください。\n\n### 問題を作るには？\n問題を作るには、アカウントを作成する必要があります。\nアカウント作成には、メニューバーの**User**から作成できます。\n\n詳しい作成方法は、ログイン後の問題作成ページに記載してあります。\n\n### 問題を解くには？\n問題を解くにはログインする必要はありません。\nただし、ログインしていない状態での提出は短期間のみ記録されます。\n\n問題を読んで、解答コード(or 解答文)が分ったら、問題ページの下部に移動しましょう。\n**Submit**と書かれた枠があります。\n自身のID(ログインしていない場合、Guestとなります)と、ProblemIDが正しいことを確認してください。\n解答コードを張り付けるか、ファイルを選択後、言語を選択して下さい。\n最後に、提出ボタンを押すとコードがサーバーに提出されます。\n\n提出後は、結果が出るまでしばらく待つ必要があります。\n結果に関しての詳しい説明はチュートリアルをご確認下さい。\n\nなお、作問者の設定により一部の言語が使用できない、又は提出を受け付けていない場合があります。\n提出を受け付けていない場合、**Submit**枠は表示されません。\n\n## Hello World!\nここで提出を試すことができます。\n\n### 問題\n標準出力に一行、`Hello World`と出力してください。\n\n"


def problem(request, problemID, cont_in={}):
    if request.method == 'POST' and 'post_disable' not in cont_in:
        return problem_submit(request, problemID)
    problemData = problemdb.get_item(
        Key={
            'ProblemID': problemID
        }
    )
    if 'Item' not in problemData:
        raise Http404('problem not found')
    problemData = problemData['Item']
    if problemData['AllowAccess'] is False:
        if request.user.username not in problemData['WhiteList'] and not request.user.is_superuser:
            raise Http404('problem not found.')
    try:
        md = markdown.Markdown()
        problemBody = md.convert(problemData['ProblemBody'])

        context = {'problemID': problemID,
                   'problemName': problemData['ProblemName'],
                   'userID': "Guest",
                   "problemBody": problemBody,
                   "langList": problemData['LangList'],
                   "allowSubmit": problemData['AllowSubmit'],
                   "TLE": problemData['Config_TL'],
                   "MLE": problemData['Config_ML'] * 1024,
                   "Case": problemData['Config_Case']
                   }
        context.update(cont_in)
        if request.user.is_authenticated:
            context['userID'] = request.user.username
    except:
        context = {'message_warning': "問題を読み込む際に問題が発生しました。想定されないエラー",
                   'allowSubmit': False
                   }
    return render(request, 'problem/problem.html', context)


def problem_index(request):
    return problem(request, 'PAHello-World')


def problem_submit(request, problemID):
    data = request.POST
    if 'LangSelect' not in data or 'Code' not in data:
        return problem(request, problemID, {
            "post_disable": True,
            "message_warning": "提出に不備があります。言語、コードが入力されている必要があります。",
            "default_lang": data['LangSelect'],
            "default_code": data['Code']
        })
    if data['problemID'] != problemID:
        return problem(request, problemID, {
            "post_disable": True,
            "message_warning": "提出に問題がありました。problemIDが一致しませんでした。想定されないエラー",
            "default_lang": data['LangSelect'],
            "default_code": data['Code']
        })
    if request.user.is_authenticated and data['userID'] != "Guest":
        if data['userID'] != request.user.username:
            return problem(request, problemID, {
                "post_disable": True,
                "message_warning": "提出に問題がありました。ユーザーIDが一致しませんでした。想定されないエラー",
                "default_lang": data['LangSelect'],
                "default_code": data['Code']
            })
    judge_sequence_q = sequencedb.update_item(
        Key={
            'name':"JudgeID"
        },
        UpdateExpression='ADD current_number :incr',
        ExpressionAttributeValues={
            ':incr': 1
        },
        ReturnValues="UPDATED_NEW"
    )
    judge_sequence=judge_sequence_q['Attributes']['current_number']
    judge_sequence %= 10000000
    judge_sequence=str(judge_sequence).zfill(6)
    judge_rand=str(random.randint(0,9999)).zfill(4)
    submitDate=int(datetime.now().timestamp())
    judgeID="JU"+str(int(datetime.now().timestamp()))+"-"+judge_sequence+judge_rand
    print(judgeID)
    item={
        "JudgeID": judgeID,
        "ProblemID": problemID,
        "Code": data['Code'],
        "Auther": data['userID'],
        "Language": data['LangSelect'],
        "SubmitDate": submitDate,
        "JudgeStatus": False
    }
    judgedb.put_item(Item=item)
    sqs_message={
        "judgeID": judgeID,
        "task": "submit"
    }
    sqs.send_message(QueueUrl=queue_url,MessageBody=json.dumps(sqs_message))
    return HttpResponseRedirect("/judge/"+judgeID)

def problem_create(request):
    if request.method == 'POST':
        return problem_create_submit(request)


def problem_create_submit(request):
    print()


def problem_edit(request, problemID):
    return
