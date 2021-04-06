#!/usr/bin/env python

import json
import sys
argv = sys.argv
sys.argv = argv[:1]
import ROOT
import optparse
import LatinoAnalysis.Gardener.hwwtools as hwwtools
import logging
import collections
import os.path
import shutil

# Common Tools & batch
from LatinoAnalysis.Tools.commonTools import *


# ----------------------------------------------------- BladeFactory --------------------------------------

class BladeFactory:
    _logger = logging.getLogger('BladeFactory')

    # _____________________________________________________________________________
    def __init__(self):
      
        self._fileIn = None
        self._skipMissingNuisance = False

    # _____________________________________________________________________________
    # _____________________________________________________________________________
    def makeBlade( self, inputFile, outputFile, variables, cuts, samples, structureFile, nuisances, removeNegativeBins):
    
        print "==================="
        print "==== makeBlade ===="
        print "==================="
        
        #
        # copied from mkdatacards.py
        #
        if os.path.isdir(inputFile):
          # ONLY COMPATIBLE WITH OUTPUTS MERGED TO SAMPLE LEVEL!!
          self._fileIn = {}
          for sampleName in samples:
            self._fileIn[sampleName] = ROOT.TFile.Open(inputFile+'/plots_%s_ALL_%s.root' % (self._tag, sampleName))
            if not self._fileIn[sampleName]:
              raise RuntimeError('Input file for sample ' + sampleName + ' missing')
        else:
          self._fileIn = ROOT.TFile(inputFile, "READ")

        #
        # the new output file with histograms
        #
                
        self._fileOut = ROOT.TFile(outputFile, "recreate")

        #
        # and prepare the structure of the output file as it is the input file
        #
        for cutName in cuts:
          self._fileOut.mkdir ( cutName )
          for variableName, variable in variables.iteritems():
            self._fileOut.mkdir ( cutName + "/" + variableName)

        #
        # loop over cuts
        #
        for cutName in cuts:
          
          #
          # prepare the signals and background list of samples
          # after removing the ones not to be used in this specific phase space
          #
  
          for sampleName in samples:
          
            # loop over variables
            for variableName, variable in variables.iteritems():
              
              self._fileOut.cd ( cutName + "/" + variableName)
              
              #
              # check if this variable is available only for a selected list of cuts
              #
              if 'cuts' in variable and cutName not in variable['cuts']:
                continue
                
              #print "  variableName = ", variableName
  
              histo = self._getHisto(cutName, variableName, sampleName)
              
              if structureFile[sampleName]['isData'] == 1 :
                pass
              else :
                #
                # only if not data!
                # now modify the histogram ...
                #
                #
                #       'splitbin' : {
                #                     'DY'     : { 'all'      : {16: [16,17]} },    # all stands for 'all cuts'
                #                     'Vg'     : { 'sr_highZ' : {16: [16,17]} },    # in this case it is applied only in this phase space
                #                     'VVV'    : { 'sr_highZ' : {16: [16,17]} },    # 
                #                     'VZ'     : { 'sr_highZ' : {16: [16,17]} },    # binning starts from 1!
                #                     'VgS_H'  : { 'sr_highZ' : {                   #
                #                                                16 : [16,17],      # more than one split can be applied: in this case 16 -> 16,17
                #                                                19 : [19,20,21],   #                                              and 19 -> 19,20,21
                #                                               }                   #            
                #                                },
                #                     'VgS_L'  : { 'sr_highZ' :                     #          
                #                                               {                   #            
                #                                                16 : [16,17],      #                         
                #                                                  19 : [19,20],    #                          
                #                                               },                  #            
                #                                 }                                 #
                #                    }  
                #                                     
                #                                     
                #                                     
                #                                     
                #      The content of bin '2' of DY is split between the bins '2,3,4,5' democratically
                #      The relative uncertainty of bin '2' is propagated to bin '3,4,5' too 
                #
                #
                
                if 'splitbin' in variable :
                  if sampleName in variable['splitbin'].keys() :
                    if 'all' in variable['splitbin'][sampleName].keys() or cutName in variable['splitbin'][sampleName].keys() : 
                      name_phasespace = cutName
                      if 'all' in variable['splitbin'][sampleName].keys():
                        name_phasespace = 'all'

                      for bin_to_split in variable['splitbin'][sampleName][name_phasespace].keys():
                    
                        value_to_share = histo.GetBinContent( bin_to_split )  # 19
                        uncertainty_on_value_to_share = histo.GetBinError( bin_to_split )
                        # you cannot share anything if it was already 0, com'on!
                        # set more properly the splitting in "variables.py"
                        if value_to_share > 0 :   # !=0 ?
                          print " I am splitting ", variableName, " , " , sampleName, " , ", cutName , " , [", bin_to_split, "] --> ", variable['splitbin'][sampleName][name_phasespace][bin_to_split]
                          relative_uncertainty_on_value_to_share = uncertainty_on_value_to_share/value_to_share
                          number_of_bins = len( variable['splitbin'][sampleName][name_phasespace][bin_to_split] )   # [19,20,21]
                          
                          print "    number_of_bins = " , number_of_bins 
                          print "    value_to_share (", value_to_share, ") --> " , value_to_share/number_of_bins
                          
                          for ibin in variable['splitbin'][sampleName][name_phasespace][bin_to_split] :
                            histo.SetBinContent( ibin, value_to_share/number_of_bins )
                            histo.SetBinError ( ibin, relative_uncertainty_on_value_to_share * value_to_share/number_of_bins ) #  = uncertainty_on_value_to_share / number_of_bins
                        else :
                          print " I am NOT splitting ", variableName, " , " , sampleName, " , ", cutName , " , [", bin_to_split, "] --> ", variable['splitbin'][sampleName][name_phasespace][bin_to_split]
                      
              histo.Write()
                
                    
      
              #
              # Now check the nuisances: 
              #     Nuisances
              #             
    
              for nuisanceName, nuisance in nuisances.iteritems():
                if 'type' not in nuisance:
                  raise RuntimeError('Nuisance ' + nuisanceName + ' is missing the type specification')
    
                if nuisanceName == 'stat' or nuisance['type'] == 'rateParam' or nuisance['type'] in ['lnN', 'lnU']:
                  # nothing to do ...
                  continue
    
                # check if a nuisance can be skipped because not in this particular cut
                if 'cuts' in nuisance and cutName not in nuisance['cuts']:
                  continue
    
                
                if nuisance['type'] == 'shape':
                  #
                  # 
                  histoUp = self._getHisto(cutName, variableName, sampleName, '_' + nuisance['name'] + 'Up')
                  #
                  # now modify the histogram ...
                  #
                  #print " histoUp = ", cutName, variableName, sampleName, '_' + nuisance['name'] + 'Up' + " => ", histoUp
                  if histoUp != None:

                    if 'splitbin' in variable :
                      if sampleName in variable['splitbin'].keys() :
                        if 'all' in variable['splitbin'][sampleName].keys() or cutName in variable['splitbin'][sampleName].keys() : 
                          name_phasespace = cutName
                          if 'all' in variable['splitbin'][sampleName].keys():
                            name_phasespace = 'all'
                        
                          for bin_to_split in variable['splitbin'][sampleName][name_phasespace].keys():
                        
                            value_to_share = histoUp.GetBinContent( bin_to_split )  # 19
                            uncertainty_on_value_to_share = histoUp.GetBinError( bin_to_split )
                            # you cannot share anything if it was already 0, com'on!
                            # set more properly the splitting in "variables.py"
                            if value_to_share > 0 :   # !=0 ?
                              relative_uncertainty_on_value_to_share = uncertainty_on_value_to_share/value_to_share
                              number_of_bins = len( variable['splitbin'][sampleName][name_phasespace][bin_to_split] )   # [19,20,21]
                              for ibin in variable['splitbin'][sampleName][name_phasespace][bin_to_split] :
                                histoUp.SetBinContent( ibin, value_to_share/number_of_bins )
                                histoUp.SetBinError ( ibin, relative_uncertainty_on_value_to_share * value_to_share/number_of_bins ) #  = uncertainty_on_value_to_share / number_of_bins
                            else :
                              pass 
        
                    histoUp.Write()


                  histoDown = self._getHisto(cutName, variableName, sampleName, '_' + nuisance['name'] + 'Down')
                  #
                  # now modify the histogram ...
                  #
                  if histoDown != None :
                    if 'splitbin' in variable :
                      if sampleName in variable['splitbin'].keys() :
                        if 'all' in variable['splitbin'][sampleName].keys() or cutName in variable['splitbin'][sampleName].keys() : 
                          name_phasespace = cutName
                          if 'all' in variable['splitbin'][sampleName].keys():
                            name_phasespace = 'all'
                        
                          for bin_to_split in variable['splitbin'][sampleName][name_phasespace].keys():
                        
                            value_to_share = histoDown.GetBinContent( bin_to_split )  # 19
                            uncertainty_on_value_to_share = histoDown.GetBinError( bin_to_split )
                            # you cannot share anything if it was already 0, com'on!
                            # set more properly the splitting in "variables.py"
                            if value_to_share > 0 :   # !=0 ?
                              relative_uncertainty_on_value_to_share = uncertainty_on_value_to_share/value_to_share
                              number_of_bins = len( variable['splitbin'][sampleName][name_phasespace][bin_to_split] )   # [19,20,21]
                              for ibin in variable['splitbin'][sampleName][name_phasespace][bin_to_split] :
                                histoDown.SetBinContent( ibin, value_to_share/number_of_bins )
                                histoDown.SetBinError ( ibin, relative_uncertainty_on_value_to_share * value_to_share/number_of_bins ) #  = uncertainty_on_value_to_share / number_of_bins
                            else :
                              pass 

                    histoDown.Write()


        #
        # Now check if I need to remove the negative bins
        #
        if removeNegativeBins : 

          for cutName in cuts:
            
            for sampleName in samples:
            
              # loop over variables
              for variableName, variable in variables.iteritems():
                
                self._fileOut.cd ( cutName + "/" + variableName)
                
                #
                # check if this variable is available only for a selected list of cuts
                #
                if 'cuts' in variable and cutName not in variable['cuts']:
                  continue
    
                histo = self._getHisto(cutName, variableName, sampleName)
                
                if structureFile[sampleName]['isData'] == 1 :
                  pass
                else :
                  #
                  # only if not data!
                  # now modify the histogram ...
                  #

                  for ibin in range(histo.GetBinsX()+2):
                    if histo.GetBinContent( ibin ) < 0 :
                      histo.SetBinContent ( ibin , 0 )
                        
                histo.Write()
                  
                #
                # Now check the nuisances: 
                #     Nuisances
                #             
      
                for nuisanceName, nuisance in nuisances.iteritems():
                  if 'type' not in nuisance:
                    raise RuntimeError('Nuisance ' + nuisanceName + ' is missing the type specification')
      
                  if nuisanceName == 'stat' or nuisance['type'] == 'rateParam' or nuisance['type'] in ['lnN', 'lnU']:
                    # nothing to do ...
                    continue
      
                  # check if a nuisance can be skipped because not in this particular cut
                  if 'cuts' in nuisance and cutName not in nuisance['cuts']:
                    continue
      
                  
                  if nuisance['type'] == 'shape':
                    #
                    # 
                    histoUp = self._getHisto(cutName, variableName, sampleName, '_' + nuisance['name'] + 'Up')
                    #
                    # now modify the histogram ...
                    #
                    if histoUp != None:
  
                      for ibin in range(histoUp.GetBinsX()+2):
                        if histoUp.GetBinContent( ibin ) < 0 :
                          histoUp.SetBinContent ( ibin , 0 )
          
                      histoUp.Write()
  
  
                    histoDown = self._getHisto(cutName, variableName, sampleName, '_' + nuisance['name'] + 'Down')
                    #
                    # now modify the histogram ...
                    #
                    if histoDown != None :

                      for ibin in range(histoDown.GetBinsX()+2):
                        if histoDown.GetBinContent( ibin ) < 0 :
                          histoDown.SetBinContent ( ibin , 0 )
  
                      histoDown.Write()

        self._fileOut.Close()
        print "-------------------------"
        print " outputFile written : " , outputFile
        print "-------------------------"
            

        if type(self._fileIn) is dict:
          for source in self._fileIn.values():
            source.Close()
        else:
          self._fileIn.Close()

    # _____________________________________________________________________________
    def _getHisto(self, cutName, variableName, sampleName, suffix = None):
        shapeName = '%s/%s/histo_%s' % (cutName, variableName, sampleName)
        if suffix:
            shapeName += suffix

        if type(self._fileIn) is dict:
            # by-sample ROOT file
            histo = self._fileIn[sampleName].Get(shapeName)
        else:
            # Merged single ROOT file
            histo = self._fileIn.Get(shapeName)

        #if not histo:
            #print shapeName, 'not found'
      
        return histo



if __name__ == '__main__':
    sys.argv = argv
    
    print '''
--------------------------------------------------------------------------------------------------
    
    
       \  | _)                    |            __ )   |             |       
      |\/ |  |   __|  _` |   __|  |   _ \      __ \   |   _` |   _` |   _ \ 
      |   |  |  |    (   |  (     |   __/      |   |  |  (   |  (   |   __/ 
     _|  _| _| _|   \__,_| \___| _| \___|     ____/  _| \__,_| \__,_| \___| 
                                                                            
                                                                           
--------------------------------------------------------------------------------------------------
'''   

#
#     This code is run between mkShape and mkDatacard/mkPlot
#     The idea is to massage the input histograms to deal with empty bins for selected samples
#

    usage = 'usage: %prog [options]'
    parser = optparse.OptionParser(usage)

    parser.add_option('--inputFile'          , dest='inputFile'           , help='input file '                                , default='./input.root')
    parser.add_option('--outputFile'         , dest='outputFile'          , help='output file. Copy of the input file with modified histograms'    , default='./output.root')
    parser.add_option('--structureFile'      , dest='structureFile'       , help='file with datacard configurations'          , default=None )
    parser.add_option('--nuisancesFile'      , dest='nuisancesFile'       , help='file with nuisances configurations'         , default=None )
    parser.add_option('--cardList'           , dest="cardList"            , help="List of cuts to produce datacards"          , default=[], type='string' , action='callback' , callback=list_maker('cardList',','))
    parser.add_option('--removeNegativeBins' , dest='removeNegativeBins'  , help='Remove negative bins'                       , action='store_true', default=False)
          
    # read default parsing options as well
    hwwtools.addOptions(parser)
    hwwtools.loadOptDefaults(parser)
    (opt, args) = parser.parse_args()

    sys.argv.append( '-b' )
    ROOT.gROOT.SetBatch()

    print " configuration file = ", opt.pycfg
    
    print " inputFile  =          ", opt.inputFile
    print " outputFile =          ", opt.outputFile
    print " removeNegativeBins =  ", opt.removeNegativeBins
 
    if not opt.debug:
      pass
    elif opt.debug == 2:
      print 'Logging level set to DEBUG (%d)' % opt.debug
      logging.basicConfig( level=logging.DEBUG )
    elif opt.debug == 1:
      print 'Logging level set to INFO (%d)' % opt.debug
      logging.basicConfig( level=logging.INFO )

    if opt.nuisancesFile == None :
      print " Please provide the nuisances structure if you want to add nuisances "

    if opt.structureFile == None :
      print " Please provide the datacard structure "
      exit ()

    ROOT.TH1.SetDefaultSumw2(True)
      
    factory = BladeFactory()
    
    ## load the samples
    samples = {}
    if os.path.exists(opt.samplesFile) :
      handle = open(opt.samplesFile,'r')
      exec(handle)
      handle.close()

    ## load the cuts
    cuts = {}
    if os.path.exists(opt.cutsFile) :
      handle = open(opt.cutsFile,'r')
      exec(handle)
      handle.close()

    ## load the variables
    variables = {}
    if os.path.exists(opt.variablesFile) :
      handle = open(opt.variablesFile,'r')
      exec(handle)
      handle.close()

    ## load the nuisances
    nuisances = collections.OrderedDict()
    if os.path.exists(opt.nuisancesFile) :
      handle = open(opt.nuisancesFile,'r')
      exec(handle)
      handle.close()

    import LatinoAnalysis.ShapeAnalysis.utils as utils

    subsamplesmap = utils.flatten_samples(samples)
    categoriesmap = utils.flatten_cuts(cuts)

    utils.update_variables_with_categories(variables, categoriesmap)
    utils.update_nuisances_with_subsamples(nuisances, subsamplesmap)
    utils.update_nuisances_with_categories(nuisances, categoriesmap)

    ## load the structure file (use flattened sample and cut names)
    structure = collections.OrderedDict()
    if os.path.exists(opt.structureFile) :
      handle = open(opt.structureFile,'r')
      exec(handle)
      handle.close()

    ## command-line cuts restrictions
    if len(opt.cardList)>0:
      try:
        newCuts = []
        for iCut in opt.cardList:
          for iOptim in optim:
            newCuts.append(iCut+'_'+iOptim)
        opt.cardList = newCuts
        print opt.cardList
      except:
        print "No optim dictionary"
      cut2del = []
      for iCut in cuts:
        if not iCut in opt.cardList : cut2del.append(iCut)
      for iCut in cut2del : del cuts[iCut]   
    
    factory.makeBlade( opt.inputFile ,opt.outputFile, variables, cuts, samples, structure, nuisances, opt.removeNegativeBins)
