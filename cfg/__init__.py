import yaml

__version__ = '1.0.4 beta'
__author__ = 'ShawnHu'

# Loading color configure.
with open('cfg/color.yml', 'r') as cf:
    color = yaml.safe_load(cf)

# Loading icon configure.
# NODE SORT/NAME.png
NODE_ICONx85_PATH = 'lib/icon/nodesx85/{}/{}.png'
NODE_ICONx120_PATH = 'lib/icon/nodesx120/{}/{}.png'
NODE_ICONx500_PATH = 'lib/icon/nodesx500/{}/{}.png'
with open('cfg/icon.yml', 'r') as icf:
    icon = yaml.safe_load(icf)

# Loading tips configure.
with open('cfg/tips.yml', 'r') as tf:
    tips = yaml.safe_load(tf)

# Loading configure for graphic path: edge.
EDGE_WIDTH = 4.0
EDGE_DIRECT = 1
EDGE_CURVES = 2

# Loading configure for scene
SCENE_WIDTH = 10000
SCENE_HEIGHT = 10000

# Loading configure for User Custom Pins.
UCP_LOC = 'user/'

# Loading support export type
EXPORT_SUPPORT = (
    'Python Code (*.py)',
    # 'Model Summary (*.png)',
)

# Loading configure for stylesheet
SS_ROOT = 'lib/skin/{}.css'
SS_COMMON = SS_ROOT.format('common')
SS_ARGBOX = SS_ROOT.format('argcombobox')
SS_SIDEBTN = SS_ROOT.format('sidebarbtn')
SS_SEARCH = SS_ROOT.format('searchbar')
SS_MINIBTN = SS_ROOT.format('minibtn')

# Loading configure for debug.
DEBUG = True
