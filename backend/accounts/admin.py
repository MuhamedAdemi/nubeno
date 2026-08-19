from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.contrib.auth.models import User

from .models import AdminProfile


def _is_super_admin(user) -> bool:
    return AdminProfile.objects.filter(user=user, is_super_admin=True).exists()


class AdminProfileInline(admin.StackedInline):
    model = AdminProfile
    can_delete = False
    extra = 1

    def get_readonly_fields(self, request, obj=None):
        # Only an existing super admin can grant/revoke super-admin status —
        # nobody can promote themselves.
        if not _is_super_admin(request.user):
            return ["is_super_admin"]
        return []


class UserAdmin(DjangoUserAdmin):
    inlines = [*DjangoUserAdmin.inlines, AdminProfileInline]

    def has_change_permission(self, request, obj=None):
        if obj is not None and obj != request.user and _is_super_admin(obj) and not _is_super_admin(request.user):
            return False
        return super().has_change_permission(request, obj)

    def has_delete_permission(self, request, obj=None):
        if obj is not None and _is_super_admin(obj) and not _is_super_admin(request.user):
            return False
        return super().has_delete_permission(request, obj)


admin.site.unregister(User)
admin.site.register(User, UserAdmin)
