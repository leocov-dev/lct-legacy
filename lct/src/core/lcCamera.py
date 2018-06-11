import pymel.core as pm

from lct.src.core import lcUtility


class Camera:

    def __init__(self):
        """ """

    @staticmethod
    def toggle_background():
        """ toggle maya's viewport background between solid color and gradient """
        if pm.displayPref(query=True, displayGradient=True):
            pm.displayPref(displayGradient=False)
        else:
            pm.displayPref(displayGradient=True)

    @staticmethod
    def get_current_camera():
        '''
        get the camera from the active viewport if able
        '''
        current_camera = None

        modelEditorList = []
        for modelEditor in pm.lsUI(editors=True):
            if modelEditor.find('modelPanel') != -1:
                modelEditorList.append(modelEditor)

        for modelEditor in [x for x in modelEditorList if x.getActiveView()]:
            try:
                current_camera = modelEditor.getCamera().getShape()
            except:
                lcUtility.Utility.lc_print_exception("Problem getting the current camera")

        return current_camera
