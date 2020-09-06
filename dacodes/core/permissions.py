from rest_framework import permissions

class HasValidTeacherRole(permissions.BasePermission):
    message = 'Role not allowed'

    def has_permission(self, request, view):
        if not request.user.groups.filter(name__in=["TEACHER"]).exists():
            return False

        return True


class HasValidStudentRole(permissions.BasePermission):
    message = 'Role not allowed'

    def has_permission(self, request, view):
        if not request.user.groups.filter(name__in=["STUDENT"]).exists():
            return False

        return True