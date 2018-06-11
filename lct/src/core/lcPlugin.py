import pymel.core as pm

import lct.src.core.lcUtility as lcUtility


class Plugin:

    def __init__(self):
        """ """

    @classmethod
    def reload_plugin(cls, plugin='', autoload=False, *args, **kwargs):
        """ reloads a plugin by name and sets it to autoload if necessary """
        if not pm.pluginInfo(plugin, query=True, loaded=True) and not plugin == '':
            try:
                pm.loadPlugin(plugin)
                pm.pluginInfo(plugin, edit=True, autoload=autoload)
                return True
            except:
                lcUtility.Utility.lc_print('Something went wrong, does this plugin - {0} - exist?'.format(plugin))
                return False
        else:
            return True
