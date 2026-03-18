"""
PDF Refinement Fast module for rapid structure screening.
"""
from scipy.optimize import least_squares
from diffpy.srfit.fitbase import FitRecipe, FitContribution, Profile, FitResults
from diffpy.srfit.pdf import PDFParser, DebyePDFGenerator
from diffpy.structure import Structure
import numpy as np


class PDFRefinementFast:
    """
    Fast PDF refinement class for STRUCTURE SCREENING.
    Same interface as PDFRefinement, but MUCH faster.
    """

    def __init__(self,
                 pdffile: str,
                 strufile: str,
                 qdamp: float = 0.014,
                 qbroad: float = 0.04,
                 rbins: int = 4,
                 rmin: float = 2.0,
                 rmax_fast: float = 15.0,
                 screening_tag: bool = True):

        self.pdffile = pdffile
        self.strufile = strufile
        self.qdamp = qdamp
        self.qbroad = qbroad
        self.rbins = rbins
        self.rmin = rmin
        self.rmax_fast = rmax_fast
        self.screening_tag = screening_tag

        self.recipe = self._make_fast_recipe()

    # ------------------------------------------------------------

    def _make_fast_recipe(self):
        # --- Structure
        stru = Structure(filename=self.strufile)

        # --- PDF data
        profile = Profile()
        parser = PDFParser()
        parser.parseFile(self.pdffile)
        profile.loadParsedData(parser)

        r = profile.x
        rmax_data = np.max(r)
        rmax = min(self.rmax_fast, rmax_data)

        # Coarsen grid (rbins)
        rstep = (rmax - self.rmin) / (len(r) // self.rbins)

        profile.setCalculationRange(
            xmin=self.rmin,
            xmax=rmax,
            dx=rstep
        )

        # --- Debye generator
        gen = DebyePDFGenerator("G")
        gen.setStructure(stru, periodic=False)
        gen.qdamp.value = self.qdamp
        gen.qbroad.value = self.qbroad

        # --- Contribution
        contrib = FitContribution("cluster")
        contrib.addProfileGenerator(gen)
        contrib.setProfile(profile, xname="r")
        contrib.setEquation("s*G")

        # --- Recipe
        recipe = FitRecipe()
        recipe.addContribution(contrib)

        # --- Minimal parameter set
        recipe.addVar(contrib.s, 1.0, tag="scale")

        phase = gen.phase
        lattice = phase.getLattice()

        recipe.newVar("zoomscale", 1.0, tag="zoomscale")
        recipe.constrain(lattice.a, "zoomscale")
        recipe.constrain(lattice.b, "zoomscale")
        recipe.constrain(lattice.c, "zoomscale")

        # Fix everything except scale + zoomscale
        recipe.fix("all")
        recipe.free("scale")
        recipe.free("zoomscale")

        # Silence output
        recipe.fithooks[0].verbose = 0

        return recipe

    # ------------------------------------------------------------

    def refine(self):
        least_squares(
            self.recipe.residual,
            self.recipe.values,
            x_scale="jac",
            max_nfev=12
        )

        res = FitResults(self.recipe)
        return res.rw
