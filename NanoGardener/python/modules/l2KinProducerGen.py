#
#
#     | ___ \   |  / _)        
#     |    ) |  ' /   |  __ \  
#     |   __/   . \   |  |   | 
#    _| _____| _|\_\ _| _|  _| 
#                                                         
#
#



import ROOT
ROOT.PyConfig.IgnoreCommandLineOptions = True

from PhysicsTools.NanoAODTools.postprocessing.framework.datamodel import Collection 
from PhysicsTools.NanoAODTools.postprocessing.framework.eventloop import Module
from PhysicsTools.NanoAODTools.postprocessing.modules.common.collectionMerger import collectionMerger
from LatinoAnalysis.NanoGardener.framework.BranchMapping import mappedOutputTree, mappedEvent

import os.path


class l2KinProducerGen(Module):
    def __init__(self, branch_map=''):

        # change this part into correct path structure... 
        cmssw_base = os.getenv('CMSSW_BASE')
        try:
            ROOT.gROOT.LoadMacro(cmssw_base+'/src/LatinoAnalysis/Gardener/python/variables/WWVar.C+g')
        except RuntimeError:
            ROOT.gROOT.LoadMacro(cmssw_base+'/src/LatinoAnalysis/Gardener/python/variables/WWVar.C++g')

        self._branch_map = branch_map
                
    def beginJob(self):
        pass

    def endJob(self):
        pass

    def beginFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        self.out = mappedOutputTree(wrappedOutputTree, mapname=self._branch_map)
        self.newbranches = [
           'mll_gen',
           'dphill_gen',
           'yll_gen',
           'ptll_gen',
           'pt1_gen',
           'pt2_gen',
           'mth_gen',
           'mcoll_gen',
           'mcollWW_gen',
           'mTi_gen',
           'mTe_gen',
           'choiMass_gen',
           'mR_gen',
           'mT2_gen',
           'channel_gen',


           'drll_gen',
           'dphilljet_gen',
           'dphilljetjet_gen',
           'dphilljetjet_cut_gen',
           'dphillmet_gen',
           'dphilmet_gen',
           'dphilmet1_gen',
           'dphilmet2_gen',
           'mtw1_gen',
           'mtw2_gen',
           
           'mjj_gen',
           'detajj_gen',
           'njet_gen',
          
           'mllWgSt_gen',
           'drllWgSt_gen',
           'mllThird_gen',
           'mllOneThree_gen',
           'mllTwoThree_gen',
           'drllOneThree_gen',
           'drllTwoThree_gen',
           
           'dphijet1met_gen',  
           'dphijet2met_gen',  
           'dphijjmet_gen',    
           'dphijjmet_cut_gen',    
           'dphilep1jet1_gen', 
           'dphilep1jet2_gen', 
           'dphilep2jet1_gen', 
           'dphilep2jet2_gen',
           'mindetajl_gen',
           'detall_gen',
           'dphijj_gen',
           'maxdphilepjj_gen',
           'dphilep1jj_gen',
           'dphilep2jj_gen',
          
           'ht_gen',
           'vht_pt_gen',
           'vht_phi_gen',
           
           'projpfmet_gen',
           'dphiltkmet_gen',
           'projtkmet_gen',
           'mpmet_gen',
           
           'pTWW_gen',
           'pTHjj_gen',

           'recoil_gen',
           'jetpt1_cut_gen',
           'jetpt2_cut_gen',
           'dphilljet_cut_gen',
           'dphijet1met_cut_gen',
           'dphijet2met_cut_gen',
           'PfMetDivSumMet_gen',
           'upara_gen',
           'uperp_gen',
           'm2ljj20_gen',
           'm2ljj30_gen',
# for VBF training
           'ptTOT_cut_gen',
           'mTOT_cut_gen',
           'OLV1_cut_gen',
           'OLV2_cut_gen',
           'Ceta_cut_gen',
#whss
           'mlljj20_whss_gen',
           'mlljj30_whss_gen',
           'WlepPt_whss_gen',
           'WlepMt_whss_gen'
          ]
        
        for nameBranches in self.newbranches :
          self.out.branch(nameBranches  ,  "F");

    def endFile(self, inputFile, outputFile, inputTree, wrappedOutputTree):
        pass

    def analyze(self, event):
        """process event, return True (go to next module) or False (fail, go to next event)"""

        event = mappedEvent(event, mapname=self._branch_map)

        #muons = Collection(event, "Muon")
        #electrons = Collection(event, "Electron")
        
        # order in pt the collection merging muons and electrons
        # lepMerger must be already called
        leptons = Collection(event, "DressedLepton")

        #leptons = electrons
        nLep = len(leptons)
        
        
        lep_pt      = ROOT.std.vector(float)(0)
        lep_eta     = ROOT.std.vector(float)(0)
        lep_phi     = ROOT.std.vector(float)(0)
        lep_flavour = ROOT.std.vector(float)(0)
        
        for lep in leptons :
          lep_pt. push_back(lep.pt)
          lep_eta.push_back(lep.eta)
          lep_phi.push_back(lep.phi)
          lep_flavour.push_back(lep.pdgId)
          # 11 = ele 
          # 13 = mu
          #if lep.tightId == 0 :
          #  lep_flavour.push_back(lep.charge *  11)
          #else: 
          #  lep_flavour.push_back(lep.charge *  13)
          
          # is this really doing its job?
        
           
          
        Jet   = Collection(event, "CleanGenJet")
        #auxiliary jet collection to access the mass
        OrigJet   = Collection(event, "GenJet")
        nJet = len(Jet)

        jet_pt    = ROOT.std.vector(float)(0)
        jet_eta   = ROOT.std.vector(float)(0)
        jet_phi   = ROOT.std.vector(float)(0)
        jet_mass  = ROOT.std.vector(float)(0)

        for jet in Jet :
          jet_pt. push_back(jet.pt)
          jet_eta.push_back(jet.eta)
          jet_phi.push_back(jet.phi)
          jet_mass.push_back(OrigJet[jet.jetIdx].mass)


        WW = ROOT.WW()
        
        WW.setLeptons(lep_pt, lep_eta, lep_phi, lep_flavour)
        WW.setJets   (jet_pt, jet_eta, jet_phi, jet_mass)
       

        #MET_sumEt = event.MET_sumEt
        #MET_phi   = event.MET_phi
        #MET_pt    = event.MET_pt
        MET_sumEt = event.PuppiMET_sumEt
        MET_phi   = event.PuppiMET_phi
        MET_pt    = event.PuppiMET_pt
        
        WW.setMET(MET_pt, MET_phi)
        WW.setSumET(MET_sumEt)
       
        WW.setTkMET(event.TkMET_pt, event.TkMET_phi) 
        
        
        WW.checkIfOk()
            
            
        for nameBranches in self.newbranches :
          self.out.fillBranch(nameBranches  ,  getattr(WW, nameBranches.split("_gen")[0])())

        return True






