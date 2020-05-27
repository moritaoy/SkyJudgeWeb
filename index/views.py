from django.shortcuts import render
from django.http import Http404, HttpResponse, HttpResponseRedirect

# Create your views here.
def index(request):
    if 'ID' in request.GET:
        return redirect(request,request.GET['ID'])
    return render(request,"index.html",{})

def redirect(request,ID):
    if ID[0] == 'P':
        return HttpResponseRedirect("/problem/"+ID)
    if ID[0] == 'J':
        return HttpResponseRedirect("/judge/"+ID)
    raise Http404("ID not found")