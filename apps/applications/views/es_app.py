import datetime
import re
import pandas as pd

from django.http import HttpResponse
from django.views.generic import TemplateView
from django.db import connection, Error
from django.utils.translation import ugettext_lazy as _
from elasticsearch_dsl import A

from applications.models import LmtWallet
from applications.models.es_app import SlurmJob
from assets.models import FavoriteAsset, SystemUser, Asset
from common.permissions import PermissionsMixin, IsValidUser
from django.db.models import Subquery
import json

from perms.models import AssetPermission


class UserESAppView(TemplateView, PermissionsMixin):
    # do es query
    template_name = "applications/core_hour_v2.html"
    permission_classes = [IsValidUser]

    render_fields = ["job_name", "cpu_hours", "state", "total_cpus", "start", "end", "elapsed"]

    def make_line_chart_search(self, username, start, end):
        return {
            "query": {"bool": {"must": [{"match": {"username": username}},
                                        {"range": {"@end": {"gte": start, "lte": end}}}]}},
            "aggs": {"day_end": {
                "date_histogram": {
                    "field": "@end", "interval": "1d", "format": "8yyyy-MM-dd", "time_zone": "Asia/Shanghai"},
                "aggs": {"day_cpu_hours_sum": {"sum": {"field": "cpu_hours"}}}
            }}
        }

    def get_system_user(self):
        try:
            with connection.cursor() as cursor:
                cursor.execute(
                    "SELECT asu.username FROM perms_assetpermission_users pau, perms_assetpermission_system_users pasu,assets_systemuser asu WHERE pau.assetpermission_id = pasu.assetpermission_id AND pasu.systemuser_id = asu.id AND pau.user_id = '{}'   ;".format(
                        str(self.request.user.id).replace("-", "")))
                row = cursor.fetchone()
        except Error:
            return "", False
        if row is None:
            return "", False
        if len(row) > 0:
            return row[0], True
        else:
            return "", False

    def get_context_data(self, **kwargs):
        ssh_username, existed = self.get_system_user()

        # debug
        # ssh_username, existed = "luoyuhang", True

        if not existed:
            resp = {"lineChartData": [], "tableData": {}, "total_cpu_hours": 0, "queryStatus": 1}
            context = {
                'action': _('My Account'),
                "app": _('Application'),
                'account_data': json.dumps(resp)
            }
            kwargs.update(context)
            return super(UserESAppView, self).get_context_data(**kwargs)

        start = self.request.GET.get("start", "now-7d/d")
        end = self.request.GET.get("end", "now")
        start = "now-7d/d" if start == "" else start
        end = "now" if end == "" else end
        if re.match("\d{4}-\d{2}-\d{2}", start) and re.match("\d{4}-\d{2}-\d{2}", end):
            try:
                start_date = datetime.datetime.strptime(start, "%Y-%m-%d")
                end_date = datetime.datetime.strptime(end, "%Y-%m-%d")
            except ValueError:
                start_date = datetime.datetime.now() - datetime.timedelta(days=7)
                end_date = datetime.datetime.now()
        else:
            start_date = datetime.datetime.now() - datetime.timedelta(days=7)
            end_date = datetime.datetime.now()
        date_range_list = [datetime.datetime.strftime(d, '%Y-%m-%d')
                           for d in list(pd.date_range(start=start_date, end=end_date))]
        # 查询出折线图
        chart_searcher = SlurmJob.search()
        chart_searcher = chart_searcher.from_dict(self.make_line_chart_search(ssh_username, start, end))
        chart_resp = chart_searcher.execute()
        line_chart = []
        # 整理折线图
        day_cpu_map = {getattr(hit, "key_as_string").split("T")[0]:
                           round(getattr(hit, "day_cpu_hours_sum")['value'], 2)
                       for hit in chart_resp.aggregations.day_end.buckets}
        for d in date_range_list:
            line_chart.append({"date": d, "cpuHours": day_cpu_map.get(d, 0)})
        # 查询出表格
        curr_page = self.request.GET.get("currentPage", 1)
        curr_page = 1 if curr_page == "" else int(curr_page)
        table_searcher = SlurmJob.search()
        table_searcher = table_searcher.query("match", username=ssh_username)
        table_searcher = table_searcher.sort({"@end": {"order": "desc"}})
        table_searcher = table_searcher[(curr_page - 1) * 10: curr_page * 10]
        table_resp = table_searcher.execute()
        table_chart = []
        for hit in table_resp.hits:
            table_chart.append({
                "jobName": getattr(hit, "job_name"),
                "start": getattr(hit, "@start").replace(tzinfo=datetime.timezone.utc).
                    astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S'),
                "end": getattr(hit, "@end").replace(tzinfo=datetime.timezone.utc).
                    astimezone(datetime.timezone(datetime.timedelta(hours=8))).strftime('%Y-%m-%d %H:%M:%S'),
                "cpuHours": round(getattr(hit, "cpu_hours"), 2),
                "elapsed": getattr(hit, "elapsed")
            })
        # 整理出表格
        total_elem = table_resp.hits.total
        total_page = total_elem // 10 if total_elem % 10 == 0 else total_elem // 10 + 1
        table_resp_data = {"totalPage": total_page, "totalElem": total_elem, "tableData": table_chart}
        # 查询所用核时
        total_cpu_hours_searcher = SlurmJob.search()
        aggs_inner = A("filter", filter={"term": {"username": ssh_username}},
                       aggs={"total_cpu_hours": {"sum": {"field": "cpu_hours"}}})
        total_cpu_hours_searcher.aggs.bucket(name="agg_total_cpu_hours", agg_type=aggs_inner)
        total_cpu_hours_searcher = total_cpu_hours_searcher[:0]
        total_cpu_hours_resp = total_cpu_hours_searcher.execute()
        total_cpu_hours = round(total_cpu_hours_resp.aggregations.agg_total_cpu_hours.total_cpu_hours.value, 2)
        # 查询用户充值总的核时
        topup_total_core_hour = 0
        qs = LmtWallet.objects.filter(user=self.request.user)
        if qs.count() != 0:
            for item in qs:
                topup_total_core_hour += item.total_core_hour
        # 整理出最后的响应结构
        resp = {"lineChartData": line_chart, "tableData": table_resp_data, "total_cpu_hours": total_cpu_hours,
                "topup_total_core_hour": topup_total_core_hour, "queryStatus": 0}

        context = {
            'action': _('My Account'),
            "app": _('Application'),
            'account_data': json.dumps(resp)
        }
        kwargs.update(context)
        return super(UserESAppView, self).get_context_data(**kwargs)
