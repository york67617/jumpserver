from django.db.models import ForeignKey, DO_NOTHING, BigIntegerField, DateTimeField, Model
from django.utils import timezone

from assets.models import AdminUser
from users.models import User


class LmtWallet(Model):

    user = ForeignKey(to=User, on_delete=DO_NOTHING, verbose_name="用户", db_column='user_id', related_name="user_id")
    admin = ForeignKey(to=User, on_delete=DO_NOTHING, verbose_name="为其充值的管理员", db_column="admin_id",
                       related_name="admin_id")
    total_core_hour = BigIntegerField(default=0, verbose_name="总核时")
    create_time = DateTimeField(default=timezone.now, verbose_name="充值时间")
