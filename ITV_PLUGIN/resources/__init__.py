from .main import ITVPluginMain

def classFactory(iface):
    return ITVPluginMain(iface)