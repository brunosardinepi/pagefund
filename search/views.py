from django.contrib.postgres.search import SearchRank, SearchQuery, SearchVector
from django.db.models.functions import Lower
from django.http import HttpResponse
from django.shortcuts import render

from collections import OrderedDict
from functools import reduce

import json
import operator

from page.models import Page


def search(request):
    categories = OrderedDict(Page._meta.get_field('category').choices)
    states = OrderedDict(Page._meta.get_field('state').choices)
    return render(request, 'search/search.html', {'categories': categories, 'states': states})

def filter_list(f, s=''):
    f = f.split(",")
    results = []
    sponsored = []
    for i in f:
        if s:
            query_objects = Page.objects.filter(category=i, state=s).order_by('name')
        else:
            query_objects = Page.objects.filter(category=i).order_by('name')
        if query_objects:
            for object in query_objects:
                if object.is_sponsored == True:
                    sponsored.append(object)
                else:
                    results.append(object)
    return (results, sponsored)

def query_list(q, s=''):
    q = q.split(",")
    queries = [SearchQuery(query) for query in q]
    query = reduce(operator.or_, queries)
    vector = SearchVector('name', weight='A') + SearchVector('description', weight='B')
    if s:
        results = Page.objects.annotate(rank=SearchRank(vector, query)).filter(rank__gte=0.2, is_sponsored=False, state=s).order_by('-rank')
        sponsored = Page.objects.annotate(rank=SearchRank(vector, query)).filter(rank__gte=0.2, is_sponsored=True, state=s).order_by('-rank')
    else:
        results = Page.objects.annotate(rank=SearchRank(vector, query)).filter(rank__gte=0.2, is_sponsored=False).order_by('-rank')
        sponsored = Page.objects.annotate(rank=SearchRank(vector, query)).filter(rank__gte=0.2, is_sponsored=True).order_by('-rank')
    return (results, sponsored)

def state_list(s):
    results = Page.objects.filter(is_sponsored=False, state=s).order_by('name')
    sponsored = Page.objects.filter(is_sponsored=True, state=s).order_by('name')
    return (results, sponsored)

def results(request):
    if request.method == "POST":
        q = request.POST.get('q')
        f = request.POST.get('f')
        s = request.POST.get('s')

        if f:
            f = f.replace('"', '')
            f = f.replace('[', '')
            f = f.replace(']', '')

        if q == "0":
            q = False
        elif f == "0":
            f = False

        if all([q, f]):
            results = []
            sponsored = []
            pages, sponsored_pages = query_list(q, s)
            f = f.split(",")
            for x in f:
                p = pages.filter(category=x)
                for y in p:
                    results.append(y)
                s = sponsored_pages.filter(category=x)
                for y in s:
                    sponsored.append(y)
        elif q:
            results, sponsored = query_list(q, s)
        elif f:
            results, sponsored = filter_list(f, s)
        elif s:
            results, sponsored = state_list(s)
        else:
            results = None
            sponsored = None

        response_data = OrderedDict()
        if results:
            for r in results:
                response_data[r.page_slug] = {'name': r.name, 'city': r.city, 'state': r.state, 'sponsored': "f"}
        if sponsored:
            for s in sponsored:
                response_data[s.page_slug] = {'name': s.name, 'city': s.city, 'state': s.state, 'sponsored': "t"}

        return HttpResponse(
            json.dumps(response_data),
            content_type="application/json"
        )
