import bokeh.models

from os.path import basename

from bokeh.models import ColumnDataSource, Paragraph, Select
from bokeh.models.glyphs import Text
from bokeh.core.properties import value
from bokeh.models.tools import PolyDrawTool, PointDrawTool, ToolbarBox, FreehandDrawTool, ProxyToolbar, Toolbar
from bokeh.events import ButtonClick
from forest import wind, data, tools, redux
import forest.middlewares as mws
#from . import front
from .front_tool import FrontDrawTool


class BARC:
    '''
     A class for the BARC features.

     It is attached to to the main FOREST instance in the :py:func:`forest.main.main()` function of :py:mod:`forest.main`.
    '''
    barcTools = None
    source = {}

    def __init__(self, figures):
        self.figures = figures
        self.document = bokeh.plotting.curdoc()
        self.barcTools = bokeh.models.layouts.Column(name="barcTools")
        self.source['polyline'] = ColumnDataSource(data.EMPTY)
        self.source['barb'] = ColumnDataSource(data.EMPTY)
        self.source['fronts'] = ColumnDataSource(data.EMPTY)

        #self.source['text_stamp'] = {}
        self.starting_colour = "black"  # in CSS-type spec
        self.starting_width = 2
        self.widthPicker = bokeh.models.widgets.Slider(
            title='Select width', name="barc_width", width=350, end=10.0, start=1.0, value=self.starting_width)
        # colour bar picker
        self.colourPicker = bokeh.models.widgets.ColorPicker(
            title='Select stamp colour:', width=350, name="barc_colours", color=self.starting_colour)
        # Dropdown Menu of stamp categories
        self.stamp_categories=["group0", "group1", "group2", "group3",
                               "group4", "group5", "group6", "group7",
                               "group8", "group9", "typhoons"]
        self.dropDown = Select(title="Stamp Category to display:", width=350,
                               value="group0",
                               options=self.stamp_categories)
        self.dropDown.on_change("value", self.call)
        # Save area
        self.saveArea = bokeh.models.widgets.inputs.TextAreaInput(
            cols=20, max_length=20000)
        self.saveArea.js_on_change('value',
                                   bokeh.models.CustomJS(args=dict(sources=self.source, saveArea=self.saveArea, figure=self.figures[0]), code="""
                Object.entries(JSON.parse(saveArea.value)).forEach(([k,v]) => {
                    sources[k].data = v;
                    sources[k].change.emit();
                    if(k.substring(0,10) == 'text_stamp')
                    {
                        for(var g = 0; g < sources[k].data['fontsize'].length; g++)
                        {
                            sources[k].data['fontsize'][g] = (((sources[k].data['datasize'][g])/ (figure.y_range.end - figure.y_range.start))*figure.inner_height) + 'px';
                        }
                    }
                })
            """)
                                   )

        self.saveButton = bokeh.models.widgets.Button(
            name="barc_save", width=350, label="Save")
        self.saveButton.js_on_click(
            bokeh.models.CustomJS(args=dict(sources=self.source, saveArea=self.saveArea), code="""
                var outdict = {}
                Object.entries(sources).forEach(([k,v]) =>
                {
                    outdict[k] = v.data;
                })
                saveArea.value = JSON.stringify(outdict);
            """)
        )
        # from BARC.woff take the index
        # James's icons correspond pw-000 - pw-099 glyph index 2 to 101
        glyphIndexMap={"983040":2,"983041":3,"983042":4,"983043":5,"983044":6,"983045":7,"983046":8,"983047":9,"983048":10,
                       "983049":11,"983079":12,"983080":13,"983081":14,"983082":15,"983083":16,"983084":17,"983085":18,"983086":19,"983087":20,
                       "983088":21,"983118":22,"983119":23,"983120":24,"983121":25,"983122":26,"983123":27,"983124":28,"983125":29,"983126":30,
                       "983127":31,"983157":32,"983158":33,"983159":34,"983160":35,"983161":36,"983162":37,"983163":38,"983164":39,"983165":40,
                       "983166":41,"983196":42,"983197":43,"983198":44,"983199":45,"983200":46,"983201":47,"983202":48,"983203":49,"983204":50,
                       "983205":51,"983235":52,"983236":53,"983237":54,"983238":55,"983239":56,"983240":57,"983241":58,"983242":59,"983243":60,
                       "983244":61,"983274":62,"983275":63,"983276":64,"983277":65,"983278":66,"983279":67,"983280":68,"983281":69,"983282":70,
                       "983283":71,"983313":72,"983314":73,"983315":74,"983316":75,"983317":76,"983318":77,"983319":78,"983320":79,"983321":80,
                       "983322":81,"983352":82,"983353":83,"983354":84,"983355":85,"983356":86,"983357":87,"983358":88,"983359":89,"983360":90,
                       "983361":91,"983391":92,"983392":93,"983393":94,"983394":95,"983395":96,"983396":97,"983397":98,"983398":99,"983399":100,
                       "983400":101}
        glyphcodes = list(map(int, list(glyphIndexMap.keys())))
        self.allglyphs = glyphcodes
        self.set_glyphs()
        icons = ["pw-%03d" % i for i in range(100)]

        self.icons = dict(zip(self.allglyphs, icons))
        # Make one ColumnDataSource per glyph
        for glyph in self.allglyphs:
            self.source['text_stamp' +
                        chr(glyph)] = ColumnDataSource(data.EMPTY)
            self.source['text_stamp' + chr(glyph)].add([], "datasize")
            self.source['text_stamp' + chr(glyph)].add([], "fontsize")
            self.source['text_stamp' + chr(glyph)].add([], "colour")

    def set_glyphs(self):
        """Set Glyphs based on drop down selection
        """
        new = self.dropDown.value
        glyphcodes =self.allglyphs
        # Range of glyphs
        # Fonts and icon mapping to go here
        if str(new) == "group0":
            self.glyphs = glyphcodes[0:10]
        elif str(new) == "group1":
            self.glyphs = glyphcodes[10:19]
        elif str(new) == "group2":
            self.glyphs = glyphcodes[20:30]
        elif str(new) == "group3":
            self.glyphs = glyphcodes[30:40]
        elif str(new) == "group4":
            self.glyphs = glyphcodes[40:50]
        elif str(new) == "group5":
            self.glyphs = glyphcodes[50:60]
        elif str(new) == "group6":
            self.glyphs = glyphcodes[60:70]
        elif str(new) == "group7":
            self.glyphs = glyphcodes[70:80]
        elif str(new) == "group8":
            self.glyphs = glyphcodes[80:90]
        elif str(new) == "group9":
            self.glyphs = glyphcodes[90:100]
        elif str(new) == "typhoons":
            # coming soon
            self.glyphs =  glyphcodes[90:100]

    def call(self, attr, old, new):
        """Call back from dropdown click
        """
        self.barcTools.children.remove(self.glyphrow)
        self.set_glyphs()
        self.glyphrow = bokeh.layouts.grid(self.display_glyphs(), ncols=5)
        self.barcTools.children.insert(2, self.glyphrow)

    def polyLine(self):
        '''
            Creates a freehand tool for drawing on the Forest maps.

            :returns: a :py:class:`FreehandDrawTool <bokeh.models.tools.FreehandDrawTool>` instance
        '''
        # colour picker means no longer have separate colour line options
        render_lines = []
        self.source['polyline'].add([], "colour")
        self.source['polyline'].add([], "width")
        for figure in self.figures:
            render_lines.append(figure.multi_line(
                xs="xs",
                ys="ys",
                line_width="width",
                source=self.source['polyline'],
                alpha=0.3,
                color="colour", level="overlay")
            )
        #text = Text(x="xs", y="ys", text=value("abc"), text_color="red", text_font_size="12pt")
        #render_line1 = figure.add_glyph(self.source['polyline'],text)
        tool2 = FreehandDrawTool(
            renderers=[render_lines[0]],
            tags=['barcfreehand'],
            name="barcfreehand"
        )
        self.source['polyline'].js_on_change('data',
                                             bokeh.models.CustomJS(args=dict(datasource=self.source['polyline'], colourPicker=self.colourPicker, widthPicker=self.widthPicker, saveArea=self.saveArea, sources=self.source), code="""
                for(var g = 0; g < datasource.data['colour'].length; g++)
                {
                    if(!datasource.data['colour'][g])
                    {
                        datasource.data['colour'][g] = colourPicker.color;
                    }
                    if(!datasource.data['width'][g])
                    {
                        datasource.data['width'][g] = widthPicker.value;
                    }
                }
                """)
                                             )

        return tool2

    def textStamp(self, glyph=chr(0x0f0000)):
        '''Creates a tool that allows arbitrary Unicode text to be "stamped" on the map. Echos to all figures.

        :param glyph: Arbitrary unicode string, usually (but not required to be) a single character.

        :returns: :py:class:`PointDrawTool <bokeh.models.tools.PointDrawTool>` with textStamp functionality.
        '''
        #render_text_stamp = self.figure.circle(x="xs",y="ys",legend_label="X", source=source);
        starting_font_size = 15  # in pixels

        #render_text_stamp = self.figure.add_glyph(self.source['text_stamp'], glyph)
        render_lines = []
        for figure in self.figures:
            render_lines.append(figure.text_stamp(
                x="xs",
                y="ys",
                source=self.source['text_stamp' + glyph],
                text=value(glyph),
                text_font='BARC',
                text_color="colour",
                text_font_size="fontsize"
            )
            )

        self.source['text_stamp' + glyph].js_on_change('data',
                                                       bokeh.models.CustomJS(args=dict(datasource=self.source['text_stamp' + glyph], starting_font_size=starting_font_size, figure=self.figures[0], colourPicker=self.colourPicker, widthPicker=self.widthPicker, saveArea=self.saveArea), code="""
                for(var g = 0; g < datasource.data['xs'].length; g++)
                {
                    if(!datasource.data['colour'][g])
                    {
                        datasource.data['colour'][g] = colourPicker.color;
                    }

                    if(!datasource.data['fontsize'][g])
                    {
                        datasource.data['fontsize'][g] = (widthPicker.value * starting_font_size) +'px';
                    }

                    //calculate initial datasize
                    if(!datasource.data['datasize'][g])
                    {
                        var starting_font_proportion = (widthPicker.value * starting_font_size)/(figure.inner_height);
                        datasource.data['datasize'][g] = (starting_font_proportion * (figure.y_range.end - figure.y_range.start));
                    }
                }
                """)
                                                       )
        figure.y_range.js_on_change('start',
                                    bokeh.models.CustomJS(args=dict(render_text_stamp=render_lines[0], figure=self.figures[0]), code="""
            for(var g = 0; g < render_text_stamp.data_source.data['fontsize'].length; g++)
            {
                 render_text_stamp.data_source.data['fontsize'][g] = (((render_text_stamp.data_source.data['datasize'][g])/ (figure.y_range.end - figure.y_range.start))*figure.inner_height) + 'px';
            }
            render_text_stamp.glyph.change.emit();
            """)
                                    )
        #render_text_stamp = bokeh.models.renderers.GlyphRenderer(data_source=ColumnDataSource(dict(x=x, y=y, text="X")), glyph=bokeh.models.Text(x="xs", y="ys", text="text", angle=0.3, text_color="fuchsia"))
        tool3 = PointDrawTool(
            renderers=[render_lines[0]],
            tags=['barc' + glyph],
        )
        return tool3

    def windBarb(self):
        '''
            Draws a windbarb based on u and v values in ms¯¹. Currently fixed to 50ms¯¹.

        '''
        render_lines = []
        for figure in self.figures:
            render_lines.append(figure.barb(
                x="xs",
                y="ys",
                u=-50,
                v=-50,
                source=self.source['barb']
            ))

        tool4 = PointDrawTool(
            renderers=render_lines,
            tags=['barcwindbarb'],
            custom_icon=wind.__file__.replace('__init__.py', 'barb.png')
        )

        return tool4

    def weatherFront(self, name="warm", symbols=chr(983431), colour="red", text_baseline="bottom"):
        '''
        The weatherfront function of BARC. This draws a Beziér curve and repeats the symbol(s) along it. 

        The colours correspond to the symbols; if there are fewer colours than symbols, it cycles back to the start. 
        If there are more colours than symbols, then the excess are ignored.

        Baselines work the same way.

        Defaults correspond to a warm front.

        :param name: String. Name of front type
        :param colour: Valid Bokeh ColorSpec or Palette (list of colours) 
        :param symbols: Unicode text string or sequence of Unicode text strings. If it is a string with length > 1, 
                     the individual characters are spaced out, repeating as necessary. If it is a sequence, 
                     each one is treated as a "character", and spaced in the same way. They can be of
                     arbitrary length but long strings may produce undesirable results.
        :param text_baseline: Valid Bokeh TextBaseline or List of TextBaselines

        :returns: :py:class:`FrontDrawTool <forest.barc.front_tool.FrontDrawTool>` instance
        '''
        self.source['bezier'+name] = ColumnDataSource(data=dict(x0=[], y0=[], x1=[], y1=[], cx0=[], cy0=[], cx1=[], cy1=[]))
        self.source['text'+name] = {}
        self.source['fronts'+name] = ColumnDataSource(data=dict(xs=[], ys=[]))
        render_lines = []
        for figure in self.figures:
            render_lines.extend([
            #order matters! Typescript assumes multiline, bézier, text_stamp [, text_stamp, ...]
            figure.multi_line(xs='xs',ys='ys', color="#aaaaaa", line_width=1, source=self.source['fronts'+name], tags=['fronts'+name]),
            figure.bezier(x0='x0', y0='y0', x1='x1', y1='y1', cx0='cx0', cy0='cy0', cx1="cx1", cy1="cy1", source=self.source['bezier'+name], line_color="black", line_width=2, tags=['bezier'])
            ])
            for each in symbols:
                self.source['text' + name][each] = ColumnDataSource(data=dict(x=[], y=[], angle=[]))
                if isinstance(colour, type([])):
                    col = colour[symbols.index(each) % len(colour)]
                else:
                    col = colour
                if isinstance(text_baseline, type([])):
                    baseline = text_baseline[symbols.index(each) % len(colour)]
                else:
                    baseline = text_baseline
                render_lines.append(figure.text_stamp(x='x', y='y', angle='angle', text_font='BARC', text_baseline=baseline, color=value(col), text=value(each), source=self.source['text'+name][each], tags=['text_stamp']))
                
        frontTool = FrontDrawTool(
            renderers=render_lines,
            tags=['barc' + name],
            custom_icon=__file__.replace(basename(__file__),'icons/%s.png' % (name,))
        )

        return frontTool

    def display_glyphs(self):
        """Displays the selected glyph buttons
        """
        buttonspec = {}
        # self.gyphs is set by the dropDown menu, create a button for
        # each glyph
        for glyph in self.glyphs:
            buttonspec[chr(glyph)] = self.icons[glyph]
        buttons = []
        for each in buttonspec:
            button = bokeh.models.widgets.Button(
                label=buttonspec[each],
                css_classes=['barc-' + buttonspec[each] + '-button', 'barc-button'],
                aspect_ratio=1,
                margin=(0, 0, 0, 0)
            )

            button.js_on_event(ButtonClick, bokeh.models.CustomJS(args=dict(buttons=list(self.toolBarBoxes.select({'tags': ['barc' + each]}))), code="""
                var each;
                for(each of buttons) { each.active = true; }
            """))
            buttons.append(button)
        return buttons

#####################################
#####################################

    def ToolBar(self):
        toolBarList = []
        for i, figure in enumerate(self.figures):
            # label toolbars
            '''toolBarBoxes.append(
                Paragraph(
                text="""Toolbar: Figure %d"""%(i+1),
                width=200, height=18,
                css_classes=['barc_p','barc_g%d'%i],
                )
            )'''
        ''' For each figure supplied (if multiple) '''
        for figure in self.figures:
            barc_tools = []
            figure.add_tools(
                self.polyLine(),
                bokeh.models.tools.PanTool(tags=['barcpan']),
                bokeh.models.tools.WheelZoomTool(tags=['barcwheelzoom']),
                bokeh.models.tools.ResetTool(tags=['barcreset']),
                bokeh.models.tools.BoxZoomTool(tags=['barcboxzoom']),
                self.windBarb(),
                self.weatherFront(),
                self.weatherFront(name='cold', colour="blue", symbols=chr(983430)),
                self.weatherFront(name='occluded', colour="purple", symbols=chr(983431)+chr(983430)),
                self.weatherFront(name='dryintrusion', colour="#0000aa", symbols='▮'),
                self.weatherFront(name='stationary', text_baseline=['bottom','top'], colour=['#ff0000','#0000ff'], symbols=chr(983431)+chr(983432)),
            )

            for glyph in self.allglyphs:
                glyphtool = self.textStamp(chr(glyph))
                barc_tools.append(glyphtool)
            figure.add_tools(*barc_tools)

            toolBarList.append(
                ToolbarBox(
                    toolbar=figure.toolbar,
                    toolbar_location=None, visible=False,
                    css_classes=['barc_g%d' % i]
                )
            )
        #self.barcTools.children.extend( toolBarBoxes )
        # tools = sum([ toolbar.tools for toolbar in toolbars ], [])self.dropDown.on_change("value", self.call)
        # tools.append(self.polyLine())
        # standard buttons
        toolBarBoxes = bokeh.models.layouts.Column(children=toolBarList)
        self.toolBarBoxes = toolBarBoxes
        buttonspec = {
            'freehand': "freehand",
            'pan': "move",
            'boxzoom': "boxzoom",
            'wheelzoom': "wheelzoom",
            'reset': "undo",
            'windbarb': "windbarb",
            'cold': "cold",
            'warm': "warm",
            'occluded': "occluded",
            'stationary': "stationary",
            'dryintrusion': "dryintrusion",
        }
        buttons = []
        for each in buttonspec:
            button = bokeh.models.widgets.Button(
                label=buttonspec[each],
                css_classes=['barc-' + buttonspec[each] + '-button', 'barc-button'],
                aspect_ratio=1,
                margin=(0, 0, 0, 0)
            )
            button.js_on_event(ButtonClick, bokeh.models.CustomJS(args=dict(buttons=list(toolBarBoxes.select({'tags': ['barc' + each]}))), code="""
                var each;
                for(each of buttons) { each.active = true; }
            """))
            buttons.append(button)

        self.barcTools.children.append(bokeh.layouts.grid(buttons, ncols=5))
        self.barcTools.children.extend([self.dropDown])
        self.glyphrow = bokeh.layouts.grid(self.display_glyphs(), ncols=5)
        self.barcTools.children.append(self.glyphrow)
        self.barcTools.children.extend(
            [self.colourPicker, self.widthPicker, self.saveButton, self.saveArea])
        self.barcTools.children.append(toolBarBoxes)

        return self.barcTools
