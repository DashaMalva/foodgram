from rest_framework import permissions


class OwnerOrReadOnly(permissions.BasePermission):
    message = ('Разрешено изменение/удаление только своего контента! '
               'Доступные методы: PATCH, DELETE.')

    def has_permission(self, request, view):
        return (request.method in permissions.SAFE_METHODS
                or request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        return (request.user == obj.author and request.method != "PUT"
                or request.method in permissions.SAFE_METHODS)


class ReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        return request.method in permissions.SAFE_METHODS

    def has_object_permission(self, request, view, obj):
        return request.method in permissions.SAFE_METHODS
