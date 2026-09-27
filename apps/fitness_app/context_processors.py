def user_profile_status(request):
    from apps.accounts.services import user_has_profile
    return {
        'has_profile': user_has_profile(request.user)
    }