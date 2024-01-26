import ROOT
import os
import re
import math
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from LatinoAnalysis.NanoGardener.data.CleanGenJetMaker_cfg import CleanGenJet_br, CleanGenJet_var 
from LatinoAnalysis.NanoGardener.data.common_cfg import Type_dict

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection

class GenJetSel(Module):
    '''
    Lepton selection module, 
    Still missing: 
                   - puppi jet
 		   - in electron var, dEtaIn and dPhiIn
                   - in muon var, track iso
    Requirement:   
                   - Input tree needs variables added by LeptonMaker
    ''' 

    def __init__(self, JC_maxdR = 0.3):
        self.JC_maxdR = JC_maxdR
        self.JC_minPtLep = 10.
        self.JC_minPtJet = 15.
        self.JC_absEta   = 5.0

        print('GenJetSel: keeping only GenJets(s) which do not have a genLepton inside a dR = 0.3 and saving them into CleanGenJet collection')


    def beginJob(self): 
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.initReaders(inputTree) # initReaders must be called in beginFile
        self.out = wrappedOutputTree
        
        # New Branches

        # Old branches to clean
        self.genjetBr_to_clean = CleanGenJet_var   

        for typ in CleanGenJet_br:
           for name in CleanGenJet_br[typ]:
              self.out.branch(name, typ, lenVar='nCleanGenJet')

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def initReaders(self,tree): # this function gets the pointers to Value and ArrayReaders and sets them in the C++ worker class
        self._ttreereaderversion = tree._ttreereaderversion # self._ttreereaderversion must be set AFTER all calls to tree.valueReader or tree.arrayReader
        pass

    #_____Help functions

    def jetIsLepton(self, jetEta, jetPhi, lepEta, lepPhi) :
        dPhi = ROOT.TMath.Abs(lepPhi - jetPhi)
        if dPhi > ROOT.TMath.Pi() :
          dPhi = 2*ROOT.TMath.Pi() - dPhi
        dR2 = (lepEta - jetEta) * (lepEta - jetEta) + dPhi * dPhi
        if dR2 < self.JC_maxdR*self.JC_maxdR:
            return True
        else:
            return False

    #_____Analyze
    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        if event._tree._ttreereaderversion > self._ttreereaderversion: # do this check at every event, as other modules might have read further branches
            self.initReaders(event._tree)
        # do NOT access other branches in python between the check/call to initReaders and the call to C++ worker code
       
        lepton_col   = Collection(event, 'LeptonGen')
        jet_col      = Collection(event, 'CleanGenJet')
        nLep = len(lepton_col) 
        nJet = len(jet_col)

        # Cleaning aid
        good_jet_idx = range(nJet)

        #------ Jet Loop
        for iJet in reversed(good_jet_idx):
            Eta_jet = jet_col[iJet]['eta']
            Phi_jet = jet_col[iJet]['phi']
            if abs(Eta_jet) > self.JC_absEta or jet_col[iJet]['pt'] < self.JC_minPtJet:
                good_jet_idx.remove(iJet)
                # print('Jet removed')
            else:
                for iLep in range(nLep):
                    if lepton_col[iLep]['isPrompt'] == 0 or lepton_col[iLep]['pt'] < self.JC_minPtLep:
                        continue
                    if self.jetIsLepton(Eta_jet, Phi_jet, lepton_col[iLep]['eta'], lepton_col[iLep]['phi']):
                        good_jet_idx.remove(iJet)
                        # print('Jet removed')
                        break  # Interrompe il loop interno dopo la rimozione di un jet

        # Cleaning and filling old branches
        for typ in CleanGenJet_br:
           for name in CleanGenJet_br[typ]:
              temp_v = []
              temp_v = [jet_col[idx][name[12:]] for idx in good_jet_idx]
              self.out.fillBranch(name, temp_v)
 
        return True

# define modules using the syntax 'name = lambda : constructor' to avoid having them loaded when not needed

genJetSl = lambda : GenJetSel()

