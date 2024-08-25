from rest_framework import permissions

class AccountPermissions(permissions.BasePermission):
    def has_permission(self, request, view):
        if view.action in ['create', 'retrieve', 'get_me_details', 'get_recent_submissions', 'get_user_stats', 'upload_profile_picture']:
            return request.user
        return True
    
    def has_object_permission(self, request, view, obj):
        if view.action in ['create', 'retrieve', 'get_me_details']:
            return request.user
        return False