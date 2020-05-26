from django.db import models
from django_elasticsearch_dsl import Document
from django_elasticsearch_dsl.registries import registry
from elasticsearch_dsl import Date, Text, Integer, Float


class SlurmData(models.Model):

    jobid = models.IntegerField()
    username = models.CharField(max_length=20)
    user_id = models.IntegerField()
    groupname = models.CharField(max_length=20)
    group_id = models.IntegerField()
    start = models.DateTimeField(name="@start", verbose_name="@start")
    end = models.DateTimeField(name="@end", verbose_name="@end")
    elapsed = models.IntegerField()
    partition = models.CharField(max_length=20)
    alloc_node = models.CharField(max_length=20)
    nodes = models.CharField(max_length=20)
    total_cpus = models.IntegerField()
    total_nodes = models.IntegerField()
    derived_ec = models.CharField(max_length=20)
    exit_code = models.CharField(max_length=20)
    state = models.CharField(max_length=20)
    cpu_hours = models.FloatField()
    pack_job_id = models.IntegerField()
    pack_job_offset = models.IntegerField()
    submit = models.DateTimeField(name="@submit", verbose_name="@submit")
    eligible = models.DateTimeField(name="@eligible", verbose_name="@eligible")
    queue_wait = models.IntegerField()
    work_dir = models.CharField(max_length=160)
    std_err = models.CharField(max_length=160)
    std_in = models.CharField(max_length=160)
    std_out = models.CharField(max_length=160)
    qos = models.CharField(max_length=20)
    ntasks = models.IntegerField()
    ntasks_per_node = models.IntegerField()
    cpus_per_task = models.IntegerField()
    time_limit = models.IntegerField()
    job_name = models.CharField(max_length=20)
    script = models.TextField()

    class Meta:
        abstract = True

@registry.register_document
class SlurmJob(Document):

    class Meta:
        doc_type = "jobcomp"

    class Index:
        name = "slurm"
        ignore_signals = True
        auto_refresh = False
        doc_type = ['jobcomp']
        settings = {'number_of_shards': 1,
                    'number_of_replicas': 0}

    class Django:
        model = SlurmData
        fields = [
            "jobid",
            "username",
            "user_id",
            "groupname",
            "group_id",
            "@start",
            "@end",
            "elapsed",
            "partition",
            "alloc_node",
            "nodes",
            "total_cpus",
            "total_nodes",
            "derived_ec",
            "exit_code",
            "state",
            "cpu_hours",
            "pack_job_id",
            "pack_job_offset",
            "@submit",
            "@eligible",
            "queue_wait",
            "work_dir",
            "std_err",
            "std_in",
            "std_out",
            "qos",
            "ntasks",
            "ntasks_per_node",
            "cpus_per_task",
            "time_limit",
            "job_name",
            "script",
        ]