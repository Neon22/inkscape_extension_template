#! /usr/bin/env python
# -*- coding: utf-8 -*-
'''
Example of extensions template for inkscape

'''

import inkex
import simplestyle # will be needed for styles support
import os # here for alt debug only

from math import cos, sin, radians

__version__ = '0.1'



### Your helper functions go here
def points_to_svgd(p, close=True):
    """ convert list of points (x,y) pairs
        into a closed SVG path list
    """
    f = p[0]
    p = p[1:]
    svgd = 'M%.4f,%.4f' % f
    for x in p:
        svgd += 'L%.4f,%.4f' % x
    if close:
        svgd += 'z'
    return svgd

def points_to_bbox(p):
    """ from a list of points (x,y pairs)
        - return the lower-left xy and upper-right xy
    """
    llx = urx = p[0][0]
    lly = ury = p[0][1]
    for x in p[1:]:
        if   x[0] < llx: llx = x[0]
        elif x[0] > urx: urx = x[0]
        if   x[1] < lly: lly = x[1]
        elif x[1] > ury: ury = x[1]
    return (llx, lly, urx, ury)

def points_to_bbox_center(p):
    """ from a list of points (x,y pairs)
        - find midpoint of bounding box around all points
        - return (x,y)
    """
    bbox = points_to_bbox(p)
    return ((bbox[0]+bbox[2])/2.0, (bbox[1]+bbox[3])/2.0)

def point_on_circle(radius, angle):
    " return xy coord of the point at distance radius from origin at angle "
    x = radius * cos(angle)
    y = radius * sin(angle)
    return (x, y)

def draw_SVG_circle(parent, r, cx, cy, name, style):
    " structre an SVG circle entity under parent "
    circ_attribs = {'style': simplestyle.formatStyle(style),
                    'cx': str(cx), 'cy': str(cy), 
                    'r': str(r),
                    inkex.addNS('label','inkscape'): name}
    circle = inkex.etree.SubElement(parent, inkex.addNS('circle','svg'), circ_attribs )



### Your main function subclasses the inkex.Effect class

class Myextension(inkex.Effect): # choose a better name
    
    def __init__(self):
        " define how the options are mapped from the inx file "
        inkex.Effect.__init__(self) # initialize the super class
        
        # Two ways to get debug info:
        # could just use inkex.debug(string) instead...
        try:
            self.tty = open("/dev/tty", 'w')
        except:
            self.tty = open(os.devnull, 'w')  # '/dev/null' for POSIX, 'nul' for Windows.
            # print >>self.tty, "gears-dev " + __version__
            
        # Define your list of parameters defined in the .inx file
        self.OptionParser.add_option("-t", "--param1",
                                     action="store", type="int",
                                     dest="param1", default=24,
                                     help="command line help")
        
        self.OptionParser.add_option("-d", "--param2",
                                     action="store", type="float",
                                     dest="param2", default=1.0,
                                     help="command line help")
        
        self.OptionParser.add_option("-s", "--param3",
                                     action="store", type="string", 
                                     dest="param3", default='choice1',
                                     help="command line help")

        self.OptionParser.add_option("-u", "--units",
                                     action="store", type="string",
                                     dest="units", default='mm',
                                     help="Units this dialog is using")

        self.OptionParser.add_option("", "--units2",
                                     action="store", type="string",
                                     dest="units2", default='mm',
                                     help="command line help")
        
        self.OptionParser.add_option("-x", "--achoice",
                                     action="store", type="inkbool", 
                                     dest="achoice", default=False,
                                     help="command line help")

        self.OptionParser.add_option("", "--accuracy", # note no cli shortcut
                                     action="store", type="int",
                                     dest="accuracy", default=0,
                                     help="command line help")
        # here so we can have tabs - but we do not use it directly - else error
        self.OptionParser.add_option("", "--active-tab",
                                     action="store", type="string",
                                     dest="active_tab", default='',
                                     help="Active tab. Not used now.")
        

    
    def add_text(self, node, text, position, text_height=12):
        """ Create and insert a single line of text into the svg under node.
        """
        line_style = {'font-size': '%dpx' % text_height, 'font-style':'normal', 'font-weight': 'normal',
                     'fill': '#F6921E', 'font-family': 'Bitstream Vera Sans,sans-serif',
                     'text-anchor': 'middle', 'text-align': 'center'}
        line_attribs = {inkex.addNS('label','inkscape'): 'Annotation',
                       'style': simplestyle.formatStyle(line_style),
                       'x': str(position[0]),
                       'y': str((position[1] + text_height) * 1.2)
                       }
        line = inkex.etree.SubElement(node, inkex.addNS('text','svg'), line_attribs)
        line.text = text

           
    def calc_unit_factor(self):
        """ return the scale factor for all dimension conversions.
            - The document units are always irrelevant as
              everything in inkscape is expected to be in 90dpi pixel units
        """
        # namedView = self.document.getroot().find(inkex.addNS('namedview', 'sodipodi'))
        # doc_units = inkex.uutounit(1.0, namedView.get(inkex.addNS('document-units', 'inkscape')))
        dialog_units = inkex.uutounit(1.0, self.options.units)
        unit_factor = 1.0 / dialog_units
        return unit_factor


### -------------------------------------------------------------------
### This is your main function and is called when the extension is run.
    
    def effect(self):
        """ Calculate Gear factors from inputs.
            - Make list of radii, angles, and centers for each tooth and 
              iterate through them
            - Turn on other visual features e.g. cross, rack, annotations, etc
        """
        path_stroke = '#000000'  # might expose one day
        path_fill   = 'none'     # no fill - just a line
        path_stroke_width  = 0.6 # might expose one day
        # gather incoming params and convert
        param1 = self.options.param1
        param2 = self.options.param2
        param3 = self.options.param3
        choice = self.options.achoice
        units2 = self.options.units2
        accuracy = self.options.accuracy # although a string in inx - option parser converts to int.
        # calculate unit factor for units defined in dialog. 
        unit_factor = self.calc_unit_factor()

        # Do your thing - create some points or a path or whatever...
        points = []
        points.extend( [ (i*2,i*2) for i in range(0, param1) ])
        points.append((param1, param1*2+5))
        #inkex.debug(points)
        path = points_to_svgd( points )
        #inkex.debug(path)
        bbox_center = points_to_bbox_center( points )
        # example debug
        # print >>self.tty, bbox_center
        # or
        # inkex.debug("bbox center %s" % bbox_center)

        
        # Embed the path in a group to make animation easier:
        # Be sure to examine the interanl structure by looking in the xml editor inside inkscape
        # This finds center of current view in inkscape
        t = 'translate(' + str( self.view_center[0] ) + ',' + str( self.view_center[1] ) + ')'
        # Make a nice useful name
        g_attribs = { inkex.addNS('label','inkscape'): 'useful name' + str( param1 ),
                      inkex.addNS('transform-center-x','inkscape'): str(-bbox_center[0]),
                      inkex.addNS('transform-center-y','inkscape'): str(-bbox_center[1]),
                      'transform': t,
                      'info':'N: '+str(param1)+'; with:'+ str(param2) }
        # add the group to the document's current layer
        g = inkex.etree.SubElement(self.current_layer, 'g', g_attribs )

        # Create SVG Path under this top level group
        # define style using basic dictionary
        style = { 'stroke': path_stroke, 'fill': path_fill, 'stroke-width': path_stroke_width }
        # convert style into svg form (see import at top of file)
        mypath_attribs = { 'style': simplestyle.formatStyle(style), 'd': path }
        # add path to scene
        gear = inkex.etree.SubElement(g, inkex.addNS('path','svg'), mypath_attribs )


        # Add another feature under it
        style = { 'stroke': path_stroke, 'fill': path_fill, 'stroke-width': path_stroke }
        cs = str(param1 / 3) # centercross length
        d = 'M-'+cs+',0L'+cs+',0M0,-'+cs+'L0,'+cs  # 'M-10,0L10,0M0,-10L0,10'
        cross_attribs = { inkex.addNS('label','inkscape'): 'Center cross',
                          'style': simplestyle.formatStyle(style), 'd': d }
        cross = inkex.etree.SubElement(g, inkex.addNS('path','svg'), cross_attribs )


        # Add a precalculated svg circle
        style = { 'stroke': path_stroke, 'fill': path_fill, 'stroke-width': path_stroke }
        draw_SVG_circle(g, param1*10/unit_factor, 0, 0, 'a circle', style)


        # Add some text
        if choice:
            notes = ['a label: %d (%s) ' % (param1/unit_factor, self.options.units),
                     'doc line'
                     ]
            text_height = 12
            # position above
            y = - 22
            for note in notes:
                self.add_text(g, note, [0,y], text_height)
                y += text_height * 1.2

if __name__ == '__main__':
    e = Myextension()
    e.affect()

# Notes

