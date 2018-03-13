# -*- coding: utf-8 -*-
"""
Created on Fri Dec 16 15:20:28 2016

@author: david
"""

import os
import sys
import time
import subprocess
import fileinput
from collections import defaultdict, Counter

def WriteGeneralOptions(filename, baseDir):
    x="""######## First, data files ########
BASEDIR=%s

RESULT=$(BASEDIR)phyldog/
PATH=$(RESULT)

genelist.file=$(RESULT)ListGenes.opt
init.species.tree=mrp
#species.tree.file=$(BASEDIR)Trees_ids/SpeciesTree_ids_0_rooted.txt
#species.tree.file=/home/david/projects/OrthoFinder/Development/phyldog/SpeciesTree_ids_0_rooted_from_elsewhere.txt
species.names.file=$(RESULT)ListSpecies.txt
starting.tree.file=$(RESULT)StartingTree.tree
output.tree.file=$(RESULT)OutputSpeciesTree.tree
output.duplications.tree.file=$(RESULT)OutputSpeciesTree_ConsensusDuplications.tree
output.losses.tree.file=$(RESULT)OutputSpeciesTree_ConsensusLosses.tree
output.numbered.tree.file=$(RESULT)OutputSpeciesTree_ConsensusNumbered.tree

######## Second, options ########
optimization.topology=no
branchProbabilities.optimization=average_then_branchwise
branch.expected.numbers.optimization=average_then_branchwise
spr.limit=5
time.limit=10000

### Added to remove warnings ###
reconciliation.model=DL
output.file.suffix=.txt
debug=0

# From specific file ... but required the variables

input.sequence.format=Fasta
output.reconciled.tree.file=$(RESULT)$(DATA).ReconciledTree
output.duplications.tree.file=$(RESULT)$(DATA).DuplicationTree
output.losses.tree.file=$(RESULT)$(DATA).LossTree
#output.numbered.tree.file=$(RESULT)OutputSpeciesTree_ConsensusNumbered.tree

use.quality.filters=false""" % baseDir
    with open(filename, 'wb') as outfile: outfile.write(x)

def WriteOGOptions(phyldogDir, nOGs, exclude):
    basedir = phyldogDir + "../"
    x = """######## First, data files ########

BASEDIR=%s
RESULT=$(BASEDIR)phyldog/Results/
DATA=%s

taxaseq.file=$(BASEDIR)phyldog/$(DATA).map.txt
input.sequence.file=$(BASEDIR)Alignments_ids/$(DATA).fa

input.sequence.sites_to_use=all
input.sequence.max_gap_allowed=66%%
init.gene.tree=bionj

######## Second, model options ########
alphabet=Protein
model=LG08

######## Output options #########
gene.tree.file=$(RESULT)$(DATA).GeneTree
output.reconciled.tree.file=$(RESULT)$(DATA).ReconciledTree
output.duplications.tree.file=$(RESULT)$(DATA).DuplicationTree
output.losses.tree.file=$(RESULT)$(DATA).LossTree
output.numbered.tree.file=$(RESULT)$(DATA).NumberedTree

######## Finally, optimization options ########
optimization.topology=yes
optimization.topology.algorithm_nni.method=fast
optimization.tolerance=0.01
optimization.method_DB.nstep=0
optimization.topology.numfirst=false
optimization.topology.tolerance.before=100
optimization.topology.tolerance.during=100
optimization.max_number_f_eval=1000000
optimization.final=none
optimization.verbose=0
optimization.message_handler=none
optimization.profiler=none
optimization.reparametrization=no"""
    exclude = set(exclude)
    for i in xrange(nOGs):
        if i in exclude: continue
        ogName = "OG%07d" % i
        with open(phyldogDir + ogName + ".opt", 'wb') as outfile: 
            outfile.write(x % (basedir, ogName))
    
def WriteListSpecies(filename, speciesToUse):
    with open(filename, 'wb') as outfile:
        for i in speciesToUse:
            outfile.write("%d\n" % i)

def WriteGeneMaps(outputDir, ogs, exclude):
    exclude = set(exclude)
    for i, og in enumerate(ogs):
        if i in exclude: continue
        genesForSpecies = defaultdict(list)
        for seq in og:
            name = seq.ToString()
            genesForSpecies[name.split("_")[0]].append(name)
        with open(outputDir + "OG%07d.map.txt" % i, 'wb') as outfile:
            for species, genes in genesForSpecies.items():
                outfile.write("%s:%s\n" % (species, ";".join(genes)))

#def WriteGeneMaps(phyldogDir, ogs):
#    for i, og in enumerate(ogs):
#        with open(          

def CleanAlignmentsForPhyldog(phyldogDir, ogs):
    """
    Remove * character
    Remove any orthogroups composed entierly of identical sequences
    Return alignments to be excluded
    """
    # 1. Remove * character
    for i, og in enumerate(ogs):
        for line in fileinput.FileInput(phyldogDir + "../Alignments_ids/OG%07d.fa" % i, inplace=True):
            if not line.startswith(">"): line=line.replace("*","-")
            sys.stdout.write(line)
    # 2. Remove any orthogroups composed entierly of identical sequences
    exclude = []
    for i, og in enumerate(ogs):
        with open(phyldogDir + "../Alignments_ids/OG%07d.fa" % i, 'rb') as infile:
            seqs = []
            for line in infile:
                if line.startswith(">"):
                    seqs.append("")
                else:
                    seqs[-1] += line.rstrip()
        # 2a. check at least 4 sequences are different
        c = Counter(seqs)
        if len(c) < 4: exclude.append(i)
    print("%d excluded alignments" % len(exclude))
    return set(exclude)
    
    
def WriteStandardFiles(phyldogDir, speciesToUse):
    WriteGeneralOptions(phyldogDir + "GeneralOptions.opt", phyldogDir + "../")
#    with open(phyldogDir + "listGenes_generic.txt", 'wb') as outfile: outfile.write(phyldogDir + "OG_generic.opt:1")
    WriteListSpecies(phyldogDir + "ListSpecies.txt", speciesToUse)

def WriteListGenes(phyldogDir, nOGs, exclude):
    with open(phyldogDir + "ListGenes.opt", 'wb') as outfile:
        for i in xrange(nOGs):
            if i in exclude: continue
            outfile.write(phyldogDir + "OG%07d.opt:%s\n" % (i, str(os.stat( phyldogDir + "../Alignments_ids/OG%07d.fa" % i )[6])))   # phyldog prepareData.py method
    
def Setup(phyldogDir, ogs, speciesToUse):
    if not os.path.exists(phyldogDir): os.mkdir(phyldogDir)
    if not os.path.exists(phyldogDir + "Results/"): os.mkdir(phyldogDir + "Results/")
    WriteStandardFiles(phyldogDir, speciesToUse)
    exclude = CleanAlignmentsForPhyldog(phyldogDir, ogs)
    nOGs = len(ogs)
    WriteOGOptions(phyldogDir, nOGs, exclude)
    WriteGeneMaps(phyldogDir, ogs, exclude)
    WriteListGenes(phyldogDir, nOGs, exclude)
    
def RunPhyldogAnalysis(phyldogDir, ogs, speciesToUse, nParallel):
    Setup(phyldogDir, ogs, speciesToUse)
    start = time.time()
    subprocess.call("mpirun -np %d phyldog param=GeneralOptions.opt" % nParallel, shell=True, cwd=phyldogDir)
    stop = time.time()
    print("%f seconds" % (stop-start))