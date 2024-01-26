import ROOT
import os
import re
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from LatinoAnalysis.NanoGardener.data.CleanGenJetMaker_cfg import CleanGenJet_br, CleanGenJet_var 
from LatinoAnalysis.NanoGardener.data.common_cfg import Type_dict

class CleanGenJetMaker(Module): 
    '''
    put this file in LatinoAnalysis/NanoGardener/python/modules/
    Add extra variables to NANO tree
    '''
    def __init__(self, min_lep_pt = [10]):
        self.min_lep_pt = min_lep_pt
        self.min_lep_pt_idx = range(len(min_lep_pt))
      #   print_str = ''
      #   for idx in self.min_lep_pt_idx:
      #       print_str += 'Lepton_pt[' + str(idx) + '] > ' + str(min_lep_pt[idx])
      #       if not idx == self.min_lep_pt_idx[-1]: print_str += ', '
        print('CleanGenJetMaker: starting now!')

    def beginJob(self): 
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.initReaders(inputTree) # initReaders must be called in beginFile
        self.out = wrappedOutputTree

        # New branches
        for typ in CleanGenJet_br:
           for var in CleanGenJet_br[typ]:
              if 'CleanGenJet_' in var: self.out.branch(var, typ, lenVar='nCleanGenJet')

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def initReaders(self,tree): # this function gets the pointers to Value and ArrayReaders and sets them in the C++ worker class
        self.genjet_var = {}
        for br in tree.GetListOfBranches():
           bname = br.GetName()
           if re.match('\AGenJet_', bname):       self.genjet_var[bname] = tree.arrayReader(bname)

        self.nGenJet = tree.valueReader('nGenJet')
        self._ttreereaderversion = tree._ttreereaderversion # self._ttreereaderversion must be set AFTER all calls to tree.valueReader or tree.arrayReader

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        if event._tree._ttreereaderversion > self._ttreereaderversion: # do this check at every event, as other modules might have read further branches
            self.initReaders(event._tree)
        # do NOT access other branches in python between the check/call to initReaders and the call to C++ worker code
        
        #--- Set vars
        nJt = int(self.nGenJet)
        
        genjet_dict = {}
        for jv in CleanGenJet_var:
           genjet_dict[jv] = [0]*nJt
        genjet_dict['jetIdx'] = [0]*nJt
        
        #--- Jet Loops
        for iJ1 in range(nJt):
           pt_idx = 0
           pt1 = self.genjet_var['GenJet_pt'][iJ1]
           # Start comparing jets
           for iJ2 in range(nJt):
              if iJ2 == iJ1: continue
              pt2 = self.genjet_var['GenJet_pt'][iJ2]
              if pt1 < pt2 or (pt1==pt2 and iJ1>iJ2):
                 pt_idx += 1
           # Now index is set, fill the vars  
           for var in genjet_dict:
              if not 'Idx' in var:
                 genjet_dict[var][pt_idx] = self.genjet_var['GenJet_' + var][iJ1]
              else:
                 genjet_dict[var][pt_idx] = iJ1

        #--- Fill branches
        for var in genjet_dict:
           self.out.fillBranch( 'CleanGenJet_' + var, genjet_dict[var])

        return True


# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

cleanGenJetMkr = lambda : CleanGenJetMaker()
