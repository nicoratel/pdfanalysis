"""
PDF Refinement module for full structure refinement using diffpy.srfit.
"""
import os
import numpy as np
import matplotlib as mpl
import matplotlib.pyplot as plt
from pathlib import Path
from scipy.optimize import least_squares
from diffpy.srfit.fitbase import FitRecipe, FitContribution, Profile, FitResults
from diffpy.srfit.pdf import PDFParser, DebyePDFGenerator
from diffpy.structure import Structure


class PDFRefinement():
    def __init__(self,
                 pdffile:str,
                 strufile:str,
                 qdamp:float=0.014,
                 qbroad:float=0.04,
                 refinement_tags:dict={'scale_factor': True, 'zoomscale': True, 'delta2': True, 'Uiso': True},
                 save_tag:bool=False,
                 RUN_PARALLEL:bool=True,
                 rmin=0.01,
                 rbins:int=1,
                 screening_tag:bool=False):

                 """
                 refinement_tags={'scale_factor': True, 'zoomscale': True, 'delta2': True, 'Uiso': True}
                 pdffile: path to pdf file
                 strufile path to structure file
                 qdamp qdamp value (default=0.014)
                 qbroad qbroad value (default==0.04)
                 save_tag: save refinement data (default=False)
                 RUN_PARALLEL=True
                 rbins: int, can be adjusted to increase rstep (default=1)
                 screening_tag=False
                 """
                # Check file formats
                 pdf_extension=os.path.basename(pdffile).split('.')[-1]
                 if pdf_extension == 'gr':
                     self.pdffile = pdffile
                 else:
                     print('PDF file should be a .gr file, extracted with pdfgtetx3')
                 stru_extension=os.path.basename(strufile).split('.')[-1]
                 if stru_extension == 'xyz':
                     self.strufile = strufile
                 else:
                     print('Structure files must adopt the xyz standard format')

                # Initialize attributes
                 self.path=os.path.dirname(self.strufile)
                 self.qdamp = qdamp
                 self.qbroad = qbroad
                 self.refinement_tags = refinement_tags
                 self.save_tag = save_tag
                 self.RUN_PARALLEL=RUN_PARALLEL
                 self.rbins=rbins
                 self.screening_tag=screening_tag
                 # Read metadata from pdffile
                 with open(self.pdffile, 'r') as f:
                     for line in f:
                         if "qmin" in line:
                             self.qmin = float(line.split(' = ')[1].strip())
                         if "qmax" in line:
                             self.qmax = float(line.split(' = ')[1].strip())
                 # Load data from the PDF file
                 r = np.loadtxt(self.pdffile, usecols=(0), skiprows=29)
                 self.rmin = rmin
                 self.rmax = np.max(r) 
                 self.rstep = ((self.rmax-self.rmin) / (len(r) - 1))*self.rbins

                 # Create fit recipe
                 self.recipe = self.make_recipe()
    
    def make_recipe(self):
        PDF_RMIN=self.rmin
        PDF_RMAX=self.rmax
        PDF_RSTEP=self.rstep
        QBROAD_I=self.qbroad
        QDAMP_I=self.qdamp
        QMIN=self.qmin
        QMAX=self.qmax
        ZOOMSCALE_I=1
        UISO_I=0.005
        stru1 = Structure(filename=self.strufile)

        profile = Profile()
        parser = PDFParser()
        parser.parseFile(self.pdffile)
        profile.loadParsedData(parser)
        profile.setCalculationRange(xmin=PDF_RMIN, xmax=PDF_RMAX, dx=PDF_RSTEP)

        # 10: Create a Debye PDF Generator object for the discrete structure model.
        generator_cluster1 = DebyePDFGenerator("G1")
        generator_cluster1.setStructure(stru1, periodic=False)

        # 11: Create a Fit Contribution object.
        contribution = FitContribution("cluster")
        contribution.addProfileGenerator(generator_cluster1)
                
        # If you have a multi-core computer (you probably do), run your refinement in parallel!
        if self.RUN_PARALLEL:
            try:
                import psutil
                import multiprocessing
                from multiprocessing import Pool
            except ImportError:
                print("\nYou don't appear to have the necessary packages for parallelization")
            syst_cores = multiprocessing.cpu_count()
            cpu_percent = psutil.cpu_percent()
            avail_cores = np.floor((100 - cpu_percent) / (100.0 / syst_cores))
            ncpu = int(np.max([1, avail_cores]))
            pool = Pool(processes=ncpu)
            generator_cluster1.parallel(ncpu=ncpu, mapfunc=pool.map)
            
        contribution.setProfile(profile, xname="r")

        # 13: Set an equation, based on your PDF generators. 
        contribution.setEquation("s1*G1")

        # 14: Create the Fit Recipe object that holds all the details of the fit.
        recipe = FitRecipe()
        recipe.addContribution(contribution)

        # 15: Initialize the instrument parameters, Q_damp and Q_broad, and
        # assign Q_max and Q_min.
        generator_cluster1.qdamp.value = QDAMP_I
        generator_cluster1.qbroad.value = QBROAD_I
        generator_cluster1.setQmax(QMAX)
        generator_cluster1.setQmin(QMIN)

        # 16: Add, initialize, and tag variables in the Fit Recipe object.
        # In this case we also add psize, which is the NP size.
        recipe.addVar(contribution.s1, float(1), tag="scale_factor")

        # 17: Define a phase and lattice from the Debye PDF Generator
        # object and assign an isotropic lattice expansion factor tagged
        # "zoomscale" to the structure. 
        phase_cluster1 = generator_cluster1.phase
        lattice1 = phase_cluster1.getLattice()
        recipe.newVar("zoomscale", ZOOMSCALE_I, tag="zoomscale")
        recipe.constrain(lattice1.a, 'zoomscale')
        recipe.constrain(lattice1.b, 'zoomscale')
        recipe.constrain(lattice1.c, 'zoomscale')
        # 18: Initialize an atoms object and constrain the isotropic
        # Atomic Displacement Paramaters (ADPs) per element. 
        atoms1 = phase_cluster1.getScatterers()
        recipe.newVar("Uiso", UISO_I, tag="Uiso")
        for atom in atoms1:
            recipe.constrain(atom.Uiso, "Uiso")
            recipe.restrain("Uiso",lb=0,ub=1,scaled=True,sig=0.00001)
        recipe.addVar(generator_cluster1.delta2, name="delta2", value=float(4), tag="delta2")
        recipe.restrain("delta2",lb=0,ub=12,scaled=True,sig=0.00001)
        return recipe
    
       
    def get_filename(self,file):
        filename=os.path.basename(file).split('/')[-1]
        return filename.split('.')[0]

    def refine(self):
        # Establish the location of the data and a name for our fit.
        gr_path = str(self.pdffile)
        FIT_ID=self.get_filename(self.pdffile)+'_'+self.get_filename(self.strufile)
        basename = FIT_ID        
        # Establish the full path of the structure file
        stru_path = self.strufile
        recipe = self.recipe
        # Amount of information to write to the terminal during fitting.
        if not self.screening_tag:
            recipe.fithooks[0].verbose = 3
        else:
            recipe.fithooks[0].verbose = 0


        recipe.fix("all")
        # Define values to refin from self.refinement_tags
        tags=[]
        for key in self.refinement_tags: 
            if self.refinement_tags[key]==True:
                tags.append(key)
        
        tags.append("all")
        for tag in tags:
            recipe.free(tag)
            
            least_squares(recipe.residual, recipe.values, x_scale="jac")

        # Write the fitted data to a file.
        profile = recipe.cluster.profile
        #profile.savetxt(fitdir / f"{basename}.fit")

        res = FitResults(recipe)
        if not self.screening_tag:
            res.printResults()
        
        #res.saveResults(resdir / f"{basename}.res", header=header)

        # Save refinement results        
        if self.save_tag:
            self.save_fitresults(profile,res)
        else: 
            pass
        return res.rw
    
    def save_fitresults(self,profile,res):
        basename=self.get_filename(self.pdffile)+'_'+self.get_filename(self.strufile)
        
        PWD=Path(self.path)
        # Make some folders to store our output files.
        resdir = PWD / "res"
        fitdir = PWD / "fit"
        figdir = PWD / "fig"
        folders = [resdir, fitdir, figdir]
        for folder in folders:
            if not folder.exists():
                folder.mkdir()
        # save exp and calc pdf
        profile.savetxt(fitdir / f"{basename}.fit")
        # Write the fit results to a file.
        header = "%s"%str(basename)+".\n"
        header+="data file:%s"%str(self.pdffile)+"\n"
        header+="structure file:%s"%str(self.strufile)+"\n"
        header+="Fitting parameters \n"
        header+="rmin=%f"%self.rmin+"\n"
        header+="rmax=%f"%self.rmax+"\n"
        header+="rstep=%f"%self.rstep+"\n"
        header+="QBROAD=%f"%self.qbroad+"\n"
        header+="QDAMP=%f"%self.qdamp+"\n"
        header+="QMIN=%f"%self.qmin+"\n"
        header+="QMAX=%f"%self.qmax+"\n"
        res.saveResults(resdir / f"{basename}.res", header=header)

        #Make plot
        fig_name= figdir / basename
        if not isinstance(fig_name, Path):
            fig_name = Path(fig_name)
        plt.clf()
        plt.close('all')
        r = self.recipe.cluster.profile.x
        g = self.recipe.cluster.profile.y
        gcalc = self.recipe.cluster.profile.ycalc
        # Make an array of identical shape as g which is offset from g.
        diff = g - gcalc
        diffzero = (min(g)-np.abs(max(diff))) * \
            np.ones_like(g)
        # Calculate the residual (difference) array and offset it vertically.
        diff = g - gcalc + diffzero
        # Change some style details of the plot
        mpl.rcParams.update(mpl.rcParamsDefault)
        # Create a figure and an axis on which to plot
        fig, ax1 = plt.subplots(1, 1)
        # Plot the difference offset line
        ax1.plot(r, diffzero, lw=1.0, ls="--", c="black")
        # Plot the measured data
        ax1.plot(r,g,ls="None",marker="o",ms=5,mew=0.2,mfc="None",label="G(r) Data")
        ax1.plot(r, diff, lw=1.2, label="G(r) diff")
        ax1.plot(r,gcalc,'g',label='G(r) calc')
        ax1.set_xlabel(r"r ($\mathrm{\AA}$)")
        ax1.set_ylabel(r"G ($\mathrm{\AA}$$^{-2}$)")
        ax1.tick_params(axis="both",which="major",top=True,right=True)
        ax1.set_xlim(self.rmin, self.rmax)
        ax1.legend(ncol=2)
        fig.tight_layout()
        ax1.set_title(basename+'\n'+f'Rw={res.rw:.4f}')
        # Save plot
        fig.savefig(fig_name.parent / f"{fig_name.name}.png", format="png")
