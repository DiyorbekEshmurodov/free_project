from apps.accounts.services import get_user_profile


def user_profile_status(request):
    # get_user_profile keshlangan (15 daqiqa), shuning uchun har sahifada
    # qo'shimcha DB so'rovi yuborilmaydi.
    return {'has_profile': get_user_profile(request.user) is not None}
