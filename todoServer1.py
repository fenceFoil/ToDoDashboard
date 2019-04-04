import CachedTodoQueries

from bokeh.layouts import column, widgetbox, row
from bokeh.models import Button
from bokeh.plotting import figure, curdoc
import numpy as np
import pandas as pd

session = CachedTodoQueries.authorize()

ids = None

def generateData(session):
    global ids 
    ids = CachedTodoQueries.query_todos(session)
    msgs = CachedTodoQueries.fetch_metadata(session, ids)
    CachedTodoQueries.calc_days_ago(msgs)
    ages = [msgs[id]['age'] for id in msgs.keys()]

    bins = list(range(max(ages)+1))
    hist, bins = np.histogram(ages, bins=bins)

    msgs_df = pd.DataFrame(msgs)
    msgs_df = msgs_df.transpose()

    # Enumerate the titles of to do emails under each bin
    msgs_df['ageRight'] = [age+1 for age in msgs_df['age']]
    msgs_df['formattedDate'] = [d.strftime('%a %b %d %Y %I:%M %p') for d in msgs_df['internalDate']]

    msgs_df = msgs_df.sort_values(by='internalDate')
    numberWithinDay = []
    currAge = 0
    ageCount = 0
    for i in range(len(msgs_df.index)):
        if msgs_df[i:i+1]['age'][0] != currAge:
            currAge = msgs_df[i:i+1]['age'][0]
            ageCount = 0
        numberWithinDay.append(ageCount)
        ageCount += 1
    msgs_df['numberWithinDay'] = numberWithinDay
    msgs_df['numberWithinDayPlusOne'] = [d+1 for d in msgs_df['numberWithinDay']]
    msgs_datasource = ColumnDataSource(msgs_df)

    return msgs_datasource

from bokeh.plotting import figure

from bokeh.models import ColumnDataSource, HoverTool, CategoricalColorMapper, TapTool, LassoSelectTool
from bokeh.models.callbacks import OpenURL
from bokeh.transform import linear_cmap, log_cmap
from bokeh.palettes import Purples9, Cividis256
from bokeh.models.widgets import Paragraph

# Download messages data
msgs_datasource = generateData(session)

# Set up the figure
p = figure(plot_width = 1000, plot_height = 500, title = 'Waiting To Do Notes by Age',
          x_axis_label = 'Age (Days)', x_range = [0, 31], y_axis_label = 'Notes', y_range = [0, max(msgs_datasource.data['numberWithinDay'])])
p.yaxis.bounds = [0, max(msgs_datasource.data['numberWithinDay'])]

# Add a quad glyph

colorMapper = linear_cmap(field_name='age', palette=list(reversed(Cividis256)), low=0, high=31)
p.quad(bottom='numberWithinDay', top='numberWithinDayPlusOne', left='age', right='ageRight', source=msgs_datasource, fill_color=colorMapper, line_color='black')

# Add a hover tool
hover = HoverTool(tooltips = [('Date', '@formattedDate'), ('Msg', '@subject')])
p.add_tools(hover)

p.add_tools(TapTool())
p.add_tools(LassoSelectTool())

selectedColumn = None

def showMessageWidgets(attr, old, new):
    #print("Callback run! {} {} {}".format(attr, old, new))
    global selectedColumn

    if selectedColumn != None:
        curdoc().remove_root(selectedColumn)

    if len(new) > 0:
        rows = []

        for index in new:
            global msgs_datasource
            msg_id = msgs_datasource.data['index'][index]
            msg_date = msgs_datasource.data['formattedDate'][index]
            msg_subject = msgs_datasource.data['subject'][index]
            print (msg_id)
            print (msg_subject)

            archiveButton = Button(label="Archive")
            archiveButton.width = 100
            def archiveCallback():
                global msgs_datasource
                print("Archiving {}".format(msg_id))
                CachedTodoQueries.archive(session, msg_id)
                # Refresh data
                msgs_datasource.data = generateData(session).data
                # Remove buttons and deselect
                #newIndex = np.where(msgs_datasource.data['index']==msg_id)
                #selectedCopy = msgs_datasource.selected
                #selectedCopy.indices = np.delete(selectedCopy.indices, [newIndex])
                #print("{}".format(selectedCopy.indices))
                #msgs_datasource.selected = selectedCopy
                msgs_datasource.selected.indices = []
                archiveButton.disabled = True
            archiveButton.on_click(archiveCallback)

            #deleteButton = Button(label="Delete")
            #deleteButton.width = 100

            label = Paragraph(text=msg_subject)
            label.width=1000-archiveButton.width#-deleteButton.width

            rows.append(row(archiveButton, label))

        #selectedColumn = column(*rows)
        curdoc().add_root(*rows)
        #curdoc().add_root(selectedColumn)
        #print(dir(curdoc()))
    
msgs_datasource.selected.on_change('indices', showMessageWidgets)

# Roulette button
rouletteButton = Button(label="Random")
rouletteButton.width = 100
def rouletteCallback():
    pass
rouletteButton.on_click(rouletteCallback)

# put the buttons, sum readout, and plot in a layout and add to the document
curdoc().add_root(column(p, row(rouletteButton, Paragraph(text="Sum: {}".format(len(ids))))))
curdoc().title = "ToDo List Dashboard"

# bokeh serve --show myapp.py