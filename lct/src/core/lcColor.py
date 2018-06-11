import colorsys

class color():
        ''' '''
        def __init__(self, *args, **kwargs):
            ''' '''

        @classmethod
        def hex_to_rgba(cls, value, floatValues=True, *args, **kwargs):
            '''
            take an 8 pair hex and convert it to rgba values in float or 8 bit
            #AARRGGBB -> (R,G,B,A)
            '''
            value = value.lstrip('#')
            lv = len(value)
            mrgb = tuple(int(value[i:i + lv // 4], 16) for i in range(0, lv, lv // 4))
            rgba = (mrgb[1],mrgb[2],mrgb[3],mrgb[0])
            if floatValues:
                rgba = (rgba[0]/255.0, rgba[1]/255.0, rgba[2]/255.0, rgba[3]/255.0)
            return rgba

        @classmethod
        def rgba_to_hex(cls, rgba, floatValues=True, *args, **kwargs):
            '''
            will take the abs of float values to prevent negative numbers
            convert 8bit or float colors to 8 pair hex
            (R,G,B,A) -> #AARRGGBB
            '''
            if floatValues:
                rgba = (int(round(abs(rgba[0])*255.0)), int(round(abs(rgba[1])*255.0)), int(round(abs(rgba[2])*255.0)), int(round(abs(rgba[3])*255.0)))
                #print rgba
            mrgb = (rgba[3],rgba[0],rgba[1],rgba[2])
            return '%02x%02x%02x%02x' % mrgb

class ColorWheel(object):
    """
        creates a list of colors from equal divisions on the color wheel in hue
        You can specify a fixed saturation and value for the list
        List starts at hue 0 by default which is RED

    """
    def __init__(self, divisions=10, hueRange=[0.0,1.0], satRange=[0.5,0.5], valRange=[0.5,0.5], *args, **kwargs):
        self.black = (0.0,0.0,0.0)
        self.white = (1.0,1.0,1.0)
        self.grey = (0.5,0.5,0.5)
        self.darkgrey = (0.125,0.125,0.125)
        self.maya = (0.27,0.27,0.27)
        self.mayalight = (0.4,0.4,0.4)

        self.divisions = divisions

        self.hueRange = hueRange
        self.satRange = satRange
        self.valRange = valRange

        self.colorList = []
        self.index = 0

        #create the list . . .
        hueIncrement = (self.hueRange[1]-self.hueRange[0])/self.divisions
        satIncrement = (self.satRange[1]-self.satRange[0])/self.divisions
        valIncrement = (self.valRange[1]-self.valRange[0])/self.divisions
        h = self.hueRange[0]
        s = self.satRange[0]
        v = self.valRange[0]

        for i in range(0,self.divisions):
            self.colorList.append([round(h,3),round(s,3),round(v,3)])
            h = h+hueIncrement
            s = s+satIncrement
            v = v+valIncrement

        #print self.colorList

    def getColorHSV (self, colorIndex, *args, **kwargs):
        """ get the HSV color at an index value from the list """
        hsv = self.colorList[colorIndex]
        return hsv

    def getColorRGB (self, colorIndex, *args, **kwargs):
        """ get the RGB color at an index value from the list """
        hsv = self.colorList[colorIndex]
        return colorsys.hsv_to_rgb(hsv[0],hsv[1],hsv[2])

    def getColor(self, colorIndex, mode='rgb', *args, **kwargs):
        """ get the RGB color at an index value from the list """
        hsv = self.colorList[colorIndex]
        rgb = colorsys.hsv_to_rgb(hsv[0],hsv[1],hsv[2])

        if mode == 'rgb':
            return rgb
        else:
            return hsv

    def getNext(self, mode='rgb', *args, **kwargs):
        '''
        get the next color on the wheel
        '''
        rgb = self.getColor(self.index, mode)
        hsv = self.getColor(self.index, mode)

        #increment the wheel
        self.index = self.index+1
        if self.index >= len(self.colorList):
            self.index = 0

        if mode == 'rgb':
            return rgb
        else:
            return hsv

    def getPrev(self, mode='rgb', *args, **kwargs):
        '''
        get the previous color on the wheel
        '''
        #decriment the wheel
        self.index = self.index-1
        if self.index < 0:
            self.index = len(self.colorList)-1

        rgb = self.getColor(self.index, mode)
        hsv = self.getColor(self.index, mode)

        if mode == 'rgb':
            return rgb
        else:
            return hsv