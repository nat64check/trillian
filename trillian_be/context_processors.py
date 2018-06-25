# noinspection PyUnusedLocal
def app_version(request):
    from . import __version__ as app_version
    return {'APP_VERSION': app_version}
