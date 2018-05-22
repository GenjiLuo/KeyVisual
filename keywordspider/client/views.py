# -*- coding: utf-8 -*-
# @Author: SHLLL
# @Email: shlll7347@gmail.com
# @Date:   2018-05-06 21:29:56
# @Last Modified by:   SHLLL
# @Last Modified time: 2018-05-22 15:50:05
# @License: MIT LICENSE

import queue
from multiprocessing import Queue
from django.core import serializers
from django.http import HttpResponse, JsonResponse
from django.views.generic import TemplateView, ListView
from .models import Content, Keyword, Frequent, Confidence
from . import spidermanage


class IndexView(TemplateView):
    template_name = "client/index.html"

    def get_context_data(self, **kwargs):
        # 将额外的数据添加到上下文数据中
        context = super().get_context_data(**kwargs)
        result_len = len(Content.objects.all())
        keyword_len = len(Keyword.objects.all())
        confid_len = len(Confidence.objects.all())
        context['result'] = {"res_len": result_len, "key_len": keyword_len,
                             "conf_len": confid_len}
        return context


class SpiderControlView(TemplateView):
    template_name = "client/control.html"

    def get_context_data(self, **kwargs):
        # 将额外的数据添加到上下文数据中
        context = super().get_context_data(**kwargs)
        result_len = len(Content.objects.all())
        keyword_len = len(Keyword.objects.all())
        confid_len = len(Confidence.objects.all())
        context['result'] = {"res_len": result_len, "key_len": keyword_len,
                             "conf_len": confid_len}
        return context


ctr_msg_queue = Queue(1)
spider_runner = None


def spider_control_post(request):
    global ctr_msg_queue, data, spider_runner

    # 首先检查上一次的进程是否存活
    if spider_runner and spider_runner.is_alive():
        spider_runner.terminate()

    # 判断是否为post请求
    if request.method == 'POST':
        # 在子进程中运行爬虫程序
        data = {"running": 0, "spider": 0, "keyword": 0, "assoword": 0}
        spider_runner = spidermanage.RunSpiderInServer(
            request.POST, ctr_msg_queue)
        spider_runner.daemon = True
        spider_runner.start()
    return HttpResponse()


data = {"running": 0, "spider": 0, "keyword": 0, "assoword": 0}


def spider_control_status_ajax(request):
    global ctr_msg_queue, data

    try:
        data = ctr_msg_queue.get_nowait()
    except queue.Empty:
        pass

    # 首先检查上一次的进程是否存活
    if spider_runner and not spider_runner.is_alive():
        data['running'] = 2

    return JsonResponse(data)


def spider_control_result_ajax(request):
    # 将额外的数据添加到上下文数据中
    result_len = len(Content.objects.all())
    keyword_len = len(Keyword.objects.all())
    confid_len = len(Confidence.objects.all())
    data = {"res_len": result_len, "key_len": keyword_len,
            "conf_len": confid_len}
    return JsonResponse(data)


class SpiderResultView(ListView):
    template_name = "client/result.html"
    model = Content   # 定义数据模型
    context_object_name = "result_list"  # 定义模板中的变量名

    def get_context_data(self, **kwargs):
        # 将额外的数据添加到上下文数据中
        context = super().get_context_data(**kwargs)
        title = ["#", "标题", "发布日期", "新闻"]
        width = ["5%", "20%", "15%", "60%"]
        length = len(Content.objects.all())
        context['result'] = {"title": title, "width": width, "len": length}
        return context


def spider_result_ajax(request, start_count, end_count):
    result = serializers.serialize(
        "json", Content.objects.all()[start_count:end_count])
    return JsonResponse(result, safe=False)


class KeywordView(ListView):
    template_name = "client/keyword.html"
    model = Keyword   # 定义数据模型
    context_object_name = "result_list"  # 定义模板中的变量名

    def get_context_data(self, **kwargs):
        # 将额外的数据添加到上下文数据中
        context = super().get_context_data(**kwargs)
        title = ["#", "标题", "关键词"]
        width = ["5%", "30%", "65%"]
        length = len(Keyword.objects.all())
        context['result'] = {"title": title, "width": width, "len": length}
        return context


def keyword_ajax(request, start_count, end_count):
    result = serializers.serialize(
        "json", Keyword.objects.all()[start_count:end_count])
    return JsonResponse(result, safe=False)


class AssocwordView(ListView):
    template_name = "client/assocword.html"
    model = Frequent   # 定义数据模型
    context_object_name = "result_list"  # 定义模板中的变量名
    display_count = 15

    def get_context_data(self, **kwargs):
        # 将额外的数据添加到上下文数据中
        context = super().get_context_data(**kwargs)
        result_len = len(Frequent.objects.all())
        display = ["itemsets", "support"]
        title = ["#", "关键词", "支持度"]
        width = ["15%", "50%", "35%"]
        length = result_len
        context['result'] = {"display": display,
                             "title": title, "width": width, "len": length}
        return context


def assocword_len_ajax(request, cur_tab):
    if cur_tab == "freq":
        length = len(Frequent.objects.all())
        title = ["#", "关键词", "支持度"]
        width = ["15%", "50%", "35%"]
        display = ["itemsets", "support"]
    elif cur_tab == "assoc":
        length = len(Confidence.objects.all())
        title = ["#", "后项规则", "前向规则", "置信度"]
        width = ["15%", "30%", "30%", "25%"]
        display = ["back_item", "front_item", "confidence"]
    return JsonResponse({"len": length, "title": title,
                         "display": display, "width": width})


def assocword_ajax(request, cur_tab, start_count, end_count):
    if cur_tab == "freq":
        model = Frequent
    elif cur_tab == "assoc":
        model = Confidence

    result = serializers.serialize(
        "json", model.objects.all()[start_count:end_count])
    return JsonResponse(result, safe=False)
