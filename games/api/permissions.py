from rest_framework import permissions


class IsStaff(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        return user.is_staff


class IsOrderOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        user = request.user
        if user.is_staff:
            return True
        return obj.user.email == user.email
