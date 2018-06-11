import os
import json
from collections import OrderedDict
import pymel.core as pm

import lct.src.core.lcUtility as lcUtility

import lct.src.core.lcPath as lcPath


class Conf():
    @classmethod
    def load_conf_file(cls, conf_file=None):
        ''''''
        conf = {}
        if not conf_file:
            currentLocation = os.path.dirname(__file__)
            conf_file = os.path.join(currentLocation, os.pardir, os.pardir, 'settings', 'lct.conf')
        execfile(conf_file, conf)
        return conf

    @classmethod
    def load_configuration_json(cls, json_file):
        ''''''
        configuration = {}

        # check if the directory for the file exists, if not make it
        directory = os.path.dirname(json_file)
        if not os.path.exists(directory):
            try:
                os.makedirs(directory)
            except:
                lcUtility.Utility.lc_print_exception("Problem creating {}".format(directory))

        # check if the file exists, if not make it
        if not os.path.exists(json_file):
            try:
                open(json_file, 'w+').close()
            except:
                lcUtility.Utility.lc_print_exception("Problem creating {}".format(json_file))

        # open the file and pase json
        with open(json_file, 'r') as infile:
            try:
                configuration = json.loads(infile.read())
            except ValueError as ve:
                if "No JSON object could be decoded" in ve:
                    lcUtility.Utility.lc_print("Creating settings file: {}".format(json_file))
                else:
                    lcUtility.Utility.lc_print_exception("There was a problem loading the file {}".format(json_file))
            except:
                lcUtility.Utility.lc_print_exception("There was a problem loading the file {}".format(json_file))

        return configuration

    @classmethod
    def save_configuration_json(cls, json_dict, json_file):
        '''
        save the given json dictionary to a json file
        '''
        if json_dict:
            if os.path.exists(json_file):
                with open(json_file, 'w') as outfile:
                    try:
                        json.dump(json_dict, outfile, indent=4)
                    except:
                        lcUtility.Utility.lc_print_exception(
                            "There was a problem saving the configuration.json file\nData:\n{}".format(json_dict))
            else:
                lcUtility.Utility.lc_print("The location does not exist {}".format(json_file))

        else:
            lcUtility.Utility.lc_print("Could not save {} to {}".format(json_dict, json_file))


class SettingsDictionary(object):

    def __init__(self, json_file, verbose=False):
        self.json_file = json_file
        self.verbose = verbose
        self.settings_json_dict = Conf.load_configuration_json(self.json_file)

    def dict(self):
        '''
        return the dictionary
        '''
        return self.settings_json_dict

    def sorted(self):
        '''
        return an OrderedDict that is sorted alphabetically
        '''
        return OrderedDict(sorted(self.settings_json_dict.items()))

    def human_readable(self):
        '''
        return a string in a human readable format
        '''
        return json.dumps(self.sorted(), indent=4)

    def update(self):
        '''
        save the dict to a json file
        and reload the values
        '''
        try:
            Conf.save_configuration_json(self.sorted(), self.json_file)
            self.settings_json_dict = Conf.load_configuration_json(self.json_file)
        except:
            lcUtility.Utility.lc_print_exception("There was a problem updating the SettingsDictionary")

    def add(self, key, value):
        '''
        add an item to the dict only if the item does not exist
        '''
        if key:
            if not key in self.settings_json_dict:
                try:
                    self.settings_json_dict.update({key: value})
                    self.update()
                except:
                    lcUtility.Utility.lc_print_exception("Failed to add [ {} : {} ] to dictionary".format(key, value))

    def set(self, key, value):
        '''
        set an item in the dict or add it if it does not exist
        '''
        if key:
            try:
                self.settings_json_dict.update({key: value})
                self.update()
            except:
                lcUtility.Utility.lc_print_exception(
                    "Failed to set or add [ {} : {} ] to dictionary".format(key, value))

    def get(self, key):
        '''
        get an items value from the dict
        '''
        if key in self.settings_json_dict:
            try:
                value = self.settings_json_dict[key]
            except:
                lcUtility.Utility.lc_print_exception("Failed to get value for {}".format(key))
            if self.verbose:
                lcUtility.Utility.lc_print("Get: [ {} : {} ]".format(key, value))
            return value
        else:
            if self.verbose:
                lcUtility.Utility.lc_print("Attribute: {} does not exist in the dictionary".format(key))
            return None

    def remove(self, key):
        '''
        remove an item from the dict
        '''
        if key in self.settings_json_dict:
            try:
                self.settings_json_dict.pop(key, None)
                self.update()
                if self.verbose:
                    lcUtility.Utility.lc_print("Deleted attr: {}".format(key))
            except:
                lcUtility.Utility.lc_print_exception("Could not delete attr: {}".format(key))


class GlobalSettingsDictionary(SettingsDictionary):
    def __init__(self, verbose=False):
        '''
        '''
        json_file = lcPath.Path.get_global_settings_file()
        SettingsDictionary.__init__(self, json_file, verbose)

        global_defaults = {
            'g_first_launch': True,
            'g_send_errors': False,
            'g_scene_settings': False,
            'g_update_check': False,
        }

        for key in global_defaults.keys():
            if key not in self.settings_json_dict.keys():
                try:
                    self.settings_json_dict.update({key: global_defaults[key]})
                except:
                    lcUtility.Utility.lc_print_exception("Could not add {} to dictionary".format(key))

        # have to call like this because of reload()
        super(self.__class__, self).update()


class ConfigurationNode(SettingsDictionary):
    def __init__(self, json_file, global_cfg, node_name='lct_configuration', verbose=False):
        '''
        '''
        SettingsDictionary.__init__(self, json_file, verbose)

        self.node_name = node_name
        self.scene_settings = global_cfg.get('g_scene_settings')

        if self.scene_settings:
            self.make_node()
            self.settings_json_dict = self.get_node_dict()

        self.delete_all_nodes()
        self.delete_old_configuration_nodes()

    def update(self):
        '''
        update the scene node and dict
        '''
        # have to call like this because of reload()
        super(self.__class__, self).update()

        if self.scene_settings:

            if self.node_exists():
                node = pm.PyNode(self.node_name)
                node.configuration.set(json.dumps(self.sorted()))
            else:
                self.make_node()

    def node_exists(self):
        '''
        does a node named node_name exist?
        '''
        if pm.objExists(self.node_name):
            if pm.nodeType(self.node_name) == 'script':
                return True
        else:
            return False

    def make_node(self):
        ''' '''
        if self.scene_settings:
            if self.node_exists():
                if self.verbose:
                    lcUtility.Utility.lc_print("{} node already exists".format(self.node_name))
            else:
                pm.scriptNode(n=self.node_name, scriptType=2, stp='python',
                              afterScript='''try:\n    import lct.src.core.lcUtility as lcUtility\n    lcUtility.Utility.close_all_open_tools()\nexcept:\n    Pass''')
                node = pm.PyNode(self.node_name)
                node.addAttr('configuration', dataType='string')
                self.update()
                if self.verbose:
                    lcUtility.Utility.lc_print("created {} node".format(self.node_name))

    def get_node_dict(self):
        '''
        get the dictionary stored in the node
        '''
        config = {}
        if self.node_exists():
            node = pm.PyNode(self.node_name)
            dict_string = node.configuration.get()
            if dict_string:
                try:
                    config = json.loads(node.configuration.get())
                except:
                    lcUtility.Utility.lc_print_exception("could not get configuration")
        if len(config) == 0:
            config = self.settings_json_dict
        return config

    def delete_all_nodes(self):
        '''
        delete all config nodes found in the scene
        '''
        if not self.scene_settings:
            script_nodes = pm.ls(type='script')
            for node in script_nodes:
                if self.node_name in str(node):
                    try:
                        pm.delete(node)
                    except:
                        lcUtility.Utility.lc_print_exception("Could not delete: {}".format(node))

    def delete_old_configuration_nodes(self):
        '''
        delete old script nodes with tool configurations
        '''
        nodes = pm.ls(type='script')
        for node in nodes:
            if 'lctools_configuration' in str(node):
                try:
                    pm.delete(node)
                except:
                    lcUtility.Utility.lc_print_exception("Failed to delete old node: {}".format(node))

    def delete_tool_attrs(self, tool_name):
        '''
        delete all the attributes associated with a particular tool via tool_name
        '''
        for key in self.settings_json_dict.keys():
            if tool_name in key:
                try:
                    self.settings_json_dict.pop(key, None)
                except:
                    lcUtility.Utility.lc_print_exception("Could not remove {}".format(key))
        self.update()

    def reset_tool_config(self, tool_name):
        '''
        delete the attrs for a given tool and relaunch the tool to reinitialize
        '''
        self.delete_tool_attrs(tool_name)
        lcUtility.Utility.exec_tool(tool_name)

    def reset_all_config(self):
        '''
        delete all the settings for all tools and restart
        '''
        global_json = lcPath.Path.get_global_settings_file()
        if os.path.exists(global_json):
            os.remove(global_json)
        settings_json = lcPath.Path.get_tools_settings_file()
        if os.path.exists(settings_json):
            os.remove(settings_json)
        self.delete_all_nodes()

        lcUtility.Utility.lc_print("Deleted all lcToolbox settings and preferences.")

        lcUtility.Utility.close_all_open_tools(silent=False)

        lcUtility.Utility.exec_tool('lcToolbox')
