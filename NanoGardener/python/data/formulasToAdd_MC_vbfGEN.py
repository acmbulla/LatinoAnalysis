# formulas to be added, in python language
# call to branches have to be in the form event.branchName
# if you want to use logical operators, the have to be the python ones (i.e "and" not " and ")

from LatinoAnalysis.NanoGardener.data.LeptonSel_cfg import ElectronWP
from LatinoAnalysis.NanoGardener.data.LeptonSel_cfg import MuonWP

formulas = {}

# from https://twiki.cern.ch/twiki/bin/viewauth/CMS/MissingETOptionalFiltersRun2#2018_2017_data_and_MC_UL 


formulas['XSWeight'] = 'event.baseW*\
                        event.genWeight \
                        if hasattr(event, \'genWeight\') else event.baseW'

