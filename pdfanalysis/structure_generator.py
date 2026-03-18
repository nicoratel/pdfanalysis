"""
Structure Generator module for generating nanoparticle structures.
"""
import os
import numpy as np
import math
import re
from ase.io import read
from ase.spacegroup import get_spacegroup, Spacegroup
from ase.cluster import Icosahedron, Octahedron, Decahedron
from scipy.spatial import ConvexHull
from ase import Atoms


class StructureGenerator():
    def __init__(self,pdfpath,cif_file:str=None,size_array:tuple=None, min_params:tuple=[1,1],max_params:tuple=[10,10],sphere_only: bool=False,
                 auto_mode: bool=False, pdf_file: str=None, r_coh: float=None, n_sizes: int=2, tolerance: float=0.1,
                 max_search_param: int=20, derivative_sigma: float=5.0, amplitude_sigma: float=3.0, 
                 window_size: int=10, derivative_weight: float=0.0, noise_window_start: float=0.85, 
                 score_threshold: float=0.001, n_jobs: int=-1):
        """
        pdfpath: directory where pdf are stored
        cif_file: path to cif file (provide Fm-3m SG if N.A. (e.g. icosahedra))
        size_array: tuple array of diameters of envelopping sphere (if None and auto_mode=True, will be auto-determined)
        min_params: tuple array of parameters used to define ase clusters (min values) - ignored in auto_mode
        max_params: tuple array of parameters used to define ase clusters (max values) - ignored in auto_mode
        sphere_only: bool Make Spherical particles only
        auto_mode: bool If True, automatically determine sizes from PDF analysis or r_coh
        pdf_file: str Path to PDF file to analyze (required if auto_mode=True and r_coh=None)
        r_coh: float Coherence length / max particle diameter (Å). If provided, bypasses automatic detection
        n_sizes: int Number of different sizes to generate for spheres in auto mode (default=2)
        tolerance: float Absolute tolerance around r_coh in Angströms (±tolerance Å)
        max_search_param: int Maximum value for p and q parameters when searching in auto mode
        derivative_sigma: float Sigma multiplier for derivative threshold (for auto detection only)
        amplitude_sigma: float Sigma multiplier for amplitude threshold (for auto detection only)
        window_size: int Window size for local statistics in PDF analysis (for auto detection only)
        derivative_weight: float Weight for derivative terms (default=0.0, set >0 to use derivative; if 0, only amplitude is used)
        noise_window_start: float Fraction of r-range where noise reference window starts (default=0.85 = last 15%)
        score_threshold: float Score threshold for r_max detection (default=0.001). Lower values = stricter detection (larger r_max)
        n_jobs: int Number of parallel jobs for structure generation (-1 = all CPU cores, 1 = sequential)
        """
        self.pdfpath=pdfpath
        self.cif_file=cif_file
        self.auto_mode=auto_mode
        self.pdf_file=pdf_file
        self.r_coh=r_coh
        self.n_sizes=n_sizes
        self.tolerance=tolerance
        self.max_search_param=max_search_param
        self.derivative_sigma=derivative_sigma
        self.amplitude_sigma=amplitude_sigma
        self.window_size=window_size
        self.derivative_weight=derivative_weight
        self.noise_window_start=noise_window_start
        self.score_threshold=score_threshold
        self.n_jobs=n_jobs
        
        # Auto mode: determine parameters from r_coh or PDF analysis
        if self.auto_mode:
            if self.r_coh is not None:
                # Manual specification of coherence length
                print(f"Using user-specified r_coh: {self.r_coh:.2f} Å")
                self.r_max = self.r_coh
            else:
                # Automatic detection from PDF (fallback if no r_coh)
                if self.pdf_file is not None:
                    print("No r_coh specified, analyzing PDF to auto-detect r_max...")
                    try:
                        self.r_max = self.analyze_pdf_and_get_rmax()
                    except Exception as e:
                        print(f"⚠️  Auto-detection failed: {e}")
                        print("Using default r_max = 30.0 Å")
                        self.r_max = 30.0
                else:
                    # No r_coh and no pdf_file: use default
                    print("⚠️  No r_coh or pdf_file provided, using default r_max = 30.0 Å")
                    self.r_max = 30.0
            
            self.size_array = self.auto_size_array_from_rmax()
        else:
            if size_array is None:
                raise ValueError("size_array must be provided when auto_mode=False")
            self.size_array=size_array
            self.r_max = None
        
        if self.cif_file is not None:
            self.structure=read(self.cif_file)
            #SG=Spacegroup(structure)
            SG=Spacegroup(get_spacegroup(self.structure))
            
            self.SGNo=SG.no
            self.lattice_parameters=self.structure.get_cell()
            self.a,self.b,self.c=self.lattice_parameters.lengths()
            self.alpha,self.beta,self.gamma=self.lattice_parameters.angles()
            self.atoms=self.structure.get_chemical_symbols()
            self.atom_positions=self.structure.get_scaled_positions()
            self.bravais=self.get_crystal_type()
            print('Crystal structure loaded from cif:')
            print(f'Cell edges: a={self.a:4f}, b={self.b:4f}, c={self.c:4f}')
            print(f'Cell angles: $\\alpha$={self.alpha:.2f},$\\beta$={self.beta:.2f}, $\\gamma$={self.gamma:.2f} ')
            print(f'Bravais unit cell:{self.bravais}')     
            print('Atomic Positions:')
            i=0
            for frac_coord in enumerate(self.atom_positions):
                print(f"Atom {self.atoms[i]}: {frac_coord}")
                i+=1
            pass
        self.min_params=min_params
        self.max_params=max_params
        self.sphere_only=sphere_only
    
    def _get_clean_cifname(self):
        """
        Extrait et nettoie le nom du fichier CIF pour n'avoir que des caractères alphanumériques et underscores.
        
        Returns:
            str: Nom nettoyé (alphanumérique + underscores uniquement)
        """
        cifname = (os.path.basename(self.cif_file).split('/')[-1]).split('.')[0]
        # Remplacer tous les caractères non alphanumériques (sauf underscore) par underscore
        cifname = re.sub(r'[^a-zA-Z0-9_]', '_', cifname)
        return cifname
    
    def analyze_pdf_and_get_rmax(self):
        """
        Analyzes PDF to find r_max where G(r) becomes noise
        Uses strong smoothing then derivative to detect signal->noise transition
        
        Returns:
            r_max: value of r where PDF becomes quasi-null
        """
        from scipy.signal import savgol_filter
        
        # Read PDF (assuming standard .gr format: r, G(r))
        try:
            data = np.loadtxt(self.pdf_file, skiprows=27)
            r = data[:, 0]
            gr = data[:, 1]
        except:
            raise ValueError(f"Cannot read PDF file: {self.pdf_file}")
        
        # STRONG SMOOTHING to eliminate FFT truncation oscillations
        # Use Savitzky-Golay with wide window
        window_length = min(101, len(gr) - 1)  # Must be odd
        if window_length % 2 == 0:
            window_length -= 1
        
        gr_smooth = savgol_filter(gr, window_length=window_length, polyorder=3)
        
        # Find position of main G(r) peak
        idx_max = np.argmax(np.abs(gr_smooth))
        r_max_peak = r[idx_max]
        
        # Calculate derivative of SMOOTHED signal
        dgr_smooth = np.gradient(gr_smooth, r)
        
        # Also smooth the derivative
        dgr_smooth = savgol_filter(dgr_smooth, window_length=window_length, polyorder=2)
        
        # Calculate threshold based on user-defined noise window
        noise_region_start = int(self.noise_window_start * len(r))
        dgr_noise = dgr_smooth[noise_region_start:]
        gr_noise = gr_smooth[noise_region_start:]
        
        # Noise statistics
        noise_deriv_std = np.std(dgr_noise)
        noise_gr_std = np.std(gr_noise)
        noise_gr_mean = np.mean(np.abs(gr_noise))
        
        # Reference values for scoring
        derivative_ref = noise_deriv_std * self.derivative_sigma
        gr_ref = noise_gr_mean + self.amplitude_sigma * noise_gr_std
        
        # Start search AFTER main peak
        # Use CONTINUOUS scoring instead of binary thresholds
        search_window = max(self.window_size, 20)
        
        # Define minimum search radius to avoid early local minima
        # Set to at least 15 Å to avoid detecting artifacts in the first coordination shells
        rmin_search = max(15.0, r_max_peak + 5.0)
        idx_min_search = np.argmin(np.abs(r - rmin_search))
        
        best_candidate = None
        all_scores = []
        
        # Start search from idx_min_search instead of idx_max
        for i in range(max(idx_max, idx_min_search), len(r) - search_window):
            window_deriv = dgr_smooth[i:i+search_window]
            window_gr = gr_smooth[i:i+search_window]
            
            # Window statistics
            std_deriv = np.std(window_deriv)
            mean_abs_gr = np.mean(np.abs(window_gr))
            max_abs_deriv = np.max(np.abs(window_deriv))
            max_abs_gr = np.max(np.abs(window_gr))
            
            # CONTINUOUS score: combination of normalized deviations from noise level
            # Lower score = closer to noise = better candidate
            if self.derivative_weight == 0:
                # Simplified: only use amplitude (most effective according to user tests)
                score = (mean_abs_gr / (gr_ref + 1e-10))**2
            else:
                # Full score with derivative terms weighted
                score = (
                    self.derivative_weight * (max_abs_deriv / (derivative_ref + 1e-10))**2 +
                    (mean_abs_gr / (gr_ref + 1e-10))**2 +
                    self.derivative_weight * ((std_deriv - noise_deriv_std) / (noise_deriv_std + 1e-10))**2
                )
            
            all_scores.append((i, r[i], score))
            
            # NEW STRATEGY: Find FIRST position where score < threshold (not absolute minimum)
            # This makes the detection sensitive to gr_ref value
            if best_candidate is None and score < self.score_threshold:
                best_candidate = i
                detected_score = score
                break  # Stop at first match
        
        # Fallback: if no position meets threshold, use minimum score
        if best_candidate is None:
            min_score = float('inf')
            for idx, r_val, score in all_scores:
                if score < min_score:
                    min_score = score
                    best_candidate = idx
            detected_score = min_score
        
        # Always return best candidate found
        if best_candidate is not None:
            print(f"  r_max detected: {r[best_candidate]:.2f} Å (score: {detected_score:.3f})")
            print(f"  Search started from r = {rmin_search:.1f} Å to avoid early artifacts")
            return r[best_candidate]
        
        # Fallback: return 70% of r_max if no clear detection
        print(f"  No clear transition detected, using 70% of r_max")
        return r[-1] * 0.7
    
    
    
    def auto_size_array_from_rmax(self):
        """
        Génère automatiquement size_array basé sur r_max et la tolérance
        
        Returns:
            size_array: tuple de diamètres pour les sphères
        """
        r_min = self.r_max - self.tolerance
        r_max_tol = self.r_max + self.tolerance
        
        size_array = tuple(np.linspace(r_min, r_max_tol, self.n_sizes))
        
        return size_array
    
    def is_diameter_in_target_range(self, diameter):
        """
        Vérifie si un diamètre tombe dans la fenêtre cible
        
        Args:
            diameter: diamètre à vérifier
            
        Returns:
            bool: True si le diamètre est dans la fenêtre acceptable
        """
        if self.r_max is None:
            return True  # Pas de filtre en mode manuel
        
        d_min = self.r_max - self.tolerance
        d_max = self.r_max + self.tolerance
        
        return d_min <= diameter <= d_max
        
    def get_crystal_type(self):
        """
        Find the Bravais lattice based on the space group number.
        """  
        spacegroup_number=self.SGNo
        # bravais lattice based on space group number https://fr.wikipedia.org/wiki/Groupe_d%27espace
        if 195 <= spacegroup_number <= 230:  # Cubic
            if spacegroup_number == 225:
                return 'fcc'
            elif spacegroup_number == 229:
                return 'bcc'
            else:
                return 'cubic'
        elif 168 <= spacegroup_number <= 194:  # Hexagonal
            return 'hcp'
        elif 75 <= spacegroup_number <= 142:  # Tetragonal
            return 'tetragonal'
        elif 16 <= spacegroup_number <= 74:  # Orthorhombic
            return 'orthorhombic'
        elif 3 <= spacegroup_number <= 15:  # Monoclinic
            return 'monoclinic'
        elif 1 <= spacegroup_number <= 2:  # Triclinic
            return 'triclinic'
        else:
            return 'unknown'

    def diameter_from_Atoms(self,Atoms):
        xyz_coord=Atoms.get_positions()
        x=list(zip(*xyz_coord))[0];y=list(zip(*xyz_coord))[1];z=list(zip(*xyz_coord))[2]
        x_center=np.mean(x);y_center=np.mean(y);z_center=np.mean(z)
        x_ok=x-x_center;y_ok=y-y_center;z_ok=z-z_center
        r=(x_ok**2+y_ok**2+z_ok**2)**(1/2)
        return max(r)  

    def center(self,pos_array):
        output=np.zeros_like(pos_array)
        x=pos_array[:,0];y=pos_array[:,1];z=pos_array[:,2]
        x0=np.mean(x);y0=np.mean(y);z0=np.mean(z)
        i=0
        for pos in pos_array:
            x,y,z=pos
            xok=x-x0;yok=y-y0;zok=z-z0
            output[i]=[xok,yok,zok]
            i+=1
        return output

    def writexyz(self,filename,atoms):
        """atoms ase Atoms object"""
        cifname = self._get_clean_cifname()
        strufile_dir=self.pdfpath+f'/structure_files_{cifname}'
        os.makedirs(strufile_dir,exist_ok=True)
        #write(strufile_dir+f'/{filename}.xyz',atoms)
        element_array=atoms.get_chemical_symbols()
        # extract composition in dict form
        composition={}
        for element in element_array:
            if element in composition:
                composition[element]+=1
            else:
                composition[element]=1
        
        coord=atoms.get_positions()
        natoms=len(element_array)  
        line2write='%d \n'%natoms
        line2write+='%s\n'%str(composition)
        for i in range(natoms):
            line2write+='%s'%str(element_array[i])+'\t %.8f'%float(coord[i,0])+'\t %.8f'%float(coord[i,1])+'\t %.8f'%float(coord[i,2])+'\n'
        with open(strufile_dir+f'/{filename}.xyz','w') as file:
            file.write(line2write)

    def makeSphere(self,phi):
        # makesupercell
        nbcell=np.max([math.ceil(phi/self.a),math.ceil(phi/self.b),math.ceil(phi/self.c)])+1
        scaling_factors=[nbcell,nbcell,nbcell]
        supercell = self.structure.repeat(scaling_factors)
        
        original_positions = supercell.get_positions()

        #positions should be centered around 0
        original_positions=self.center(original_positions)
        atom_names=supercell.get_atomic_numbers()
        
        # atoms to delete
        delAtoms=[]
        for i in range(len(atom_names)):            
            x, y, z = original_positions[i]            
            r = np.sqrt(x**2 + y**2+z**2)
            condition=True
            # Ensure the cylinder is maintained
            if r > phi/2:
                condition=False
            if not condition:
                delAtoms.append(i)
        del supercell[delAtoms]
        nbatoms=len(supercell)
        #write xyz file
        cifname=(os.path.basename(self.cif_file).split('/')[-1]).split('.')[0]
        filename=f'Sphere_phi={int(phi)}_{cifname}_{nbatoms}atoms'
        self.writexyz(filename,supercell)
        return filename,phi,nbatoms
    
    def makeIcosahedron(self,p):
        ico=Icosahedron(self.atoms[0],p,self.a)
        nbatoms=len(ico)
        cifname=(os.path.basename(self.cif_file).split('/')[-1]).split('.')[0]
        filename=f'Ih_{p}shells_phi={int(2*self.diameter_from_Atoms(ico))}_{cifname}_{nbatoms}atoms'
        self.writexyz(filename,ico)
        return filename,2*self.diameter_from_Atoms(ico),nbatoms
    
    def makeDecahedron(self,p,q):
        deca=Decahedron(self.atoms[0],p,q,0,self.a)
        nbatoms=len(deca)
        cifname=(os.path.basename(self.cif_file).split('/')[-1]).split('.')[0]
        filename=f'Dh_{p}_{q}_phi={int(2*self.diameter_from_Atoms(deca))}_{cifname}_{nbatoms}atoms'
        self.writexyz(filename,deca)
        return filename,2*self.diameter_from_Atoms(deca),nbatoms
    
    def makeOctahedron(self,p,q):
        
        octa=Octahedron(self.atoms[0],p,q,self.a)
        nbatoms=len(octa)
        cifname=(os.path.basename(self.cif_file).split('/')[-1]).split('.')[0]
        if q==0:
            filename=f'RegOh_{p}_0_phi={int(2*self.diameter_from_Atoms(octa))}_{cifname}_{nbatoms}atoms'
        if p==2*q+1:
            filename=f'CubOh_{p}_{q}_phi={int(2*self.diameter_from_Atoms(octa))}_{cifname}_{nbatoms}atoms'
        if p==3*q+1:
            filename=f'RegTrOh_{p}_{q}_phi={int(2*self.diameter_from_Atoms(octa))}_{cifname}_{nbatoms}atoms'
        else:
            filename=f'TrOh_{p}_{q}_phi={int(2*self.diameter_from_Atoms(octa))}_{cifname}_{nbatoms}atoms'
        self.writexyz(filename,octa)
        return filename,2*self.diameter_from_Atoms(octa),nbatoms
        
    def returnPointsThatLieInPlanes(self,planes: np.ndarray,
                                coords: np.ndarray,
                                debug: bool=False,
                                threshold: float=1e-3
                                ):
        """
        Finds all points (atoms) that lie within the given planes based on a signed distance criterion.

        Args:
            planes (np.ndarray): A 2D array where each row represents a plane equation [a, b, c, d] for the plane ax + by + cz + d = 0.
            coords (np.ndarray): A 2D array where each row is the coordinates of an atom [x, y, z].
            debug (bool, optional): If True, prints additional debugging information. Defaults to False.
            threshold (float, optional): The tolerance for the distance to the plane to consider a point as lying in the plane. Defaults to 1e-3.
            noOutput (bool, optional): If True, suppresses the output messages. Defaults to False.

        Returns:
            np.ndarray: A boolean array where True indicates that the atom lies in one of the planes.
        """
        
        AtomsInPlane = np.zeros(len(coords), dtype=bool)
        for p in planes:
            for i,c in enumerate(coords):
                signedDistance = self.Pt2planeSignedDistance(p,c)
                AtomsInPlane[i] = AtomsInPlane[i] or np.abs(signedDistance) < threshold
            nOfAtomsInPlane = np.count_nonzero(AtomsInPlane)
            if debug:
                print(f"- plane", [f"{x: .2f}" for x in p],f"> {nOfAtomsInPlane} atoms lie in the planes")
        AtomsInPlane = np.array(AtomsInPlane)
        return AtomsInPlane

    def Pt2planeSignedDistance(self,plane,point):
        '''
        Returns the orthogonal distance of a given point X0 to the plane p in a metric space (projection of X0 on p = P), 
        with the sign determined by whether or not X0 is in the interior of p with respect to the center of gravity [0 0 0]
        Args:
            - plane (numpy array): [u v w h] definition of the P plane 
            - point (numpy array): [x0 y0 z0] coordinates of the X0 point 
        Returns:
            the signed modulus ±||PX0||
        '''
    
        sd = (plane[3] + np.dot(plane[0:3],point))/np.sqrt(plane[0]**2+plane[1]**2+plane[2]**2)
        return sd

    def coreSurface(self,atoms: Atoms,
                threshold=1e-3               
               ):       
    
        coords = atoms.get_positions()
        hull = ConvexHull(coords)
        atoms.trPlanes = hull.equations
        surfaceAtoms = self.returnPointsThatLieInPlanes(atoms.trPlanes,coords,threshold=threshold)
    
        return [hull.vertices,hull.simplices,hull.neighbors,hull.equations], surfaceAtoms
    
    
    def detect_surface_atoms(self,filename,view=False):
        atoms=read(filename+'.xyz')
        _, surfaceAtoms = self.coreSurface(atoms)
        coords = atoms.get_positions()
        hull = ConvexHull(coords)
        surface_indices = hull.vertices
        n_surface_atoms = len(hull.vertices)
        if view:
            from ase.visualize import view
            surface_indices = hull.vertices

            # Create a copy to modify
            atoms_copy = atoms.copy()

            # Option 1: Change color by changing chemical symbols
            # For example, make surface atoms 'O' and others 'C'
            # (you can pick other symbols if you like)
            symbols = ['C'] * len(atoms)
            for idx in surface_indices:
                symbols[idx] = 'O'  # change to oxygen, so it'll show up red
            atoms_copy.set_chemical_symbols(symbols)

            view(atoms_copy)
        return surfaceAtoms.sum()

    def _process_icosahedron(self, p):
        """
        Traite un icosaèdre avec paramètre p (pour parallélisation)
        Retourne None si hors fenêtre, sinon (diameter, filename, size, nbatoms, nbsurfatoms)
        """
        try:
            ico = Icosahedron(self.atoms[0], p, self.a)
            diameter = 2 * self.diameter_from_Atoms(ico)
            
            if self.is_diameter_in_target_range(diameter):
                cifname = (os.path.basename(self.cif_file).split('/')[-1]).split('.')[0]
                strufile_dir = self.pdfpath + f'/structure_files_{cifname}/'
                filename, size, nbatoms = self.makeIcosahedron(p)
                nbsurfatoms = self.detect_surface_atoms(strufile_dir + filename)
                return (diameter, filename, size, nbatoms, nbsurfatoms)
        except Exception as e:
            pass
        return None
    
    def _process_decahedron(self, p, q):
        """
        Traite un décaèdre avec paramètres p, q (pour parallélisation)
        Retourne None si hors fenêtre, sinon (diameter, filename, size, nbatoms, nbsurfatoms)
        """
        try:
            deca = Decahedron(self.atoms[0], p, q, 0, self.a)
            diameter = 2 * self.diameter_from_Atoms(deca)
            
            if self.is_diameter_in_target_range(diameter):
                cifname = (os.path.basename(self.cif_file).split('/')[-1]).split('.')[0]
                strufile_dir = self.pdfpath + f'/structure_files_{cifname}/'
                filename, size, nbatoms = self.makeDecahedron(p, q)
                nbsurfatoms = self.detect_surface_atoms(strufile_dir + filename)
                return (diameter, filename, size, nbatoms, nbsurfatoms)
        except Exception as e:
            pass
        return None
    
    def _process_octahedron(self, p, q):
        """
        Traite un octaèdre avec paramètres p, q (pour parallélisation)
        Retourne None si hors fenêtre, sinon (diameter, filename, size, nbatoms, nbsurfatoms)
        """
        try:
            octa = Octahedron(self.atoms[0], p, q, self.a)
            diameter = 2 * self.diameter_from_Atoms(octa)
            
            if self.is_diameter_in_target_range(diameter):
                cifname = (os.path.basename(self.cif_file).split('/')[-1]).split('.')[0]
                strufile_dir = self.pdfpath + f'/structure_files_{cifname}/'
                filename, size, nbatoms = self.makeOctahedron(p, q)
                nbsurfatoms = self.detect_surface_atoms(strufile_dir + filename)
                return (diameter, filename, size, nbatoms, nbsurfatoms)
        except Exception as e:
            pass
        return None
    

    def run(self):
        """
        Méthode de génération classique (mode manuel)
        """
        if self.auto_mode:
            return self.run_auto()
        
        cifname = self._get_clean_cifname()
        strufile_dir=self.pdfpath+f'/structure_files_{cifname}/'
        logfile=strufile_dir+'/structure_generation.log'
        line2write= '*****************************************************\n\n'
        line2write+='                STRUCTURE GENERATION                 \n\n'
        line2write+='*****************************************************\n\n'
        line2write+='Structure File                                   \tDiameter \tNumber of atoms \tNumber of surface atoms\n'
        print(line2write)
        if not self.sphere_only:
            p_array=np.arange(self.min_params[0],self.max_params[0])
            q_array=np.arange(self.min_params[1],self.max_params[1])
            for p in p_array:
                filename,size,nbatoms=self.makeIcosahedron(p)
                nbsurfatoms=self.detect_surface_atoms(strufile_dir+filename)
                
                print(f'{filename:50}\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}')
                line2write+=f'{filename:50}\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}\n'
                for q in q_array:
                    if q>=1:
                        filename,size,nbatoms=self.makeDecahedron(p,q)
                        nbsurfatoms=self.detect_surface_atoms(strufile_dir+filename)
                        
                        print(f'{filename:50}\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}')
                        line2write+=f'{filename:50}\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}\n'
                    if q<=(p-1)/2:
                        filename,size,nbatoms=self.makeOctahedron(p,q)
                        nbsurfatoms=self.detect_surface_atoms(strufile_dir+filename)
                        
                        print(f'{filename:50}\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}')
                        line2write+=f'{filename:50}\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}\n'
            for size in self.size_array:
                filename,size,nbatoms=self.makeSphere(size)
                nbsurfatoms=self.detect_surface_atoms(strufile_dir+filename)
                
                print(f'{filename:50}\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}')
                line2write+=f'{filename:50}\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}\n'
        else:
            for size in self.size_array:
                filename,size,nbatoms=self.makeSphere(size)
                nbsurfatoms=self.detect_surface_atoms(strufile_dir+filename)
                
                print(f'{filename:30}\t\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}')
                line2write+=f'{filename:30}\t\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}\n'
        with open(logfile,'w')as f:
            f.write(line2write)
        return strufile_dir
    
    def run_auto(self):
        """
        Automatic generation method based on PDF analysis
        Generates candidate structures and keeps only those within diameter window
        Uses multiprocessing for acceleration
        """
        from multiprocessing import Pool, cpu_count
        from tqdm import tqdm
        
        cifname = self._get_clean_cifname()
        strufile_dir=self.pdfpath+f'/structure_files_{cifname}/'
        logfile=strufile_dir+'/structure_generation.log'
        
        # Determine number of processes
        if self.n_jobs == -1:
            n_processes = cpu_count()
        else:
            n_processes = max(1, self.n_jobs)
        
        print(f"\nStarting structure generation with {n_processes} parallel processes")
        print(f"Target diameter range: [{self.r_max-self.tolerance:.2f}, {self.r_max+self.tolerance:.2f}] Å")
        
        line2write= '*****************************************************\n\n'
        line2write+='         STRUCTURE GENERATION (AUTO MODE)            \n\n'
        line2write+='*****************************************************\n\n'
        line2write+=f'PDF analyzed: {os.path.basename(self.pdf_file)}\n'
        line2write+=f'r_max detected: {self.r_max:.2f} Å\n'
        line2write+=f'Target diameter window: [{self.r_max-self.tolerance:.2f}, {self.r_max+self.tolerance:.2f}] Å\n'
        line2write+=f'Tolerance: ±{self.tolerance:.2f} Å\n'
        line2write+=f'Parallel processes: {n_processes}\n\n'
        line2write+='Structure File                                   \tDiameter \tNumber of atoms \tNumber of surface atoms\n'
        
        structures_generated = []
        structures_kept = []
        kept_filenames = []  # Track filenames of kept structures
        results_to_write = []
        
        if not self.sphere_only:
            # Prepare tasks for icosahedra
            ico_tasks = [(p,) for p in range(1, self.max_search_param + 1)]
            
            # Process with progress bar
            print("\nSearching icosahedra...")
            if n_processes > 1:
                with Pool(processes=n_processes) as pool:
                    ico_results = list(tqdm(pool.starmap(self._process_icosahedron, ico_tasks), 
                                           total=len(ico_tasks), desc="Icosahedra", ncols=80))
            else:
                ico_results = [self._process_icosahedron(p) for p in tqdm(range(1, self.max_search_param + 1),
                                                                          desc="Icosahedra", ncols=80)]
            
            # Filter and store results
            for result in ico_results:
                if result is not None:
                    diameter, filename, size, nbatoms, nbsurfatoms = result
                    structures_generated.append(('Icosahedron', None, None, diameter))
                    if self.is_diameter_in_target_range(diameter):
                        structures_kept.append(('Icosahedron', None, None, diameter))
                        kept_filenames.append(strufile_dir + filename + '.xyz')
                        results_to_write.append(f'{filename:50}\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}\n')
            
            # Prepare tasks for decahedra
            deca_tasks = [(p, q) for p in range(1, self.max_search_param + 1) 
                         for q in range(1, self.max_search_param + 1)]
            
            print("Searching decahedra...")
            if n_processes > 1:
                with Pool(processes=n_processes) as pool:
                    deca_results = list(tqdm(pool.starmap(self._process_decahedron, deca_tasks),
                                            total=len(deca_tasks), desc="Decahedra", ncols=80))
            else:
                deca_results = [self._process_decahedron(p, q) for p, q in tqdm(deca_tasks,
                                                                                desc="Decahedra", ncols=80)]
            
            # Filter and store results
            for result in deca_results:
                if result is not None:
                    diameter, filename, size, nbatoms, nbsurfatoms = result
                    structures_generated.append(('Decahedron', None, None, diameter))
                    if self.is_diameter_in_target_range(diameter):
                        structures_kept.append(('Decahedron', None, None, diameter))
                        kept_filenames.append(strufile_dir + filename + '.xyz')
                        results_to_write.append(f'{filename:50}\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}\n')
            
            # Prepare tasks for octahedra
            octa_tasks = [(p, q) for p in range(1, self.max_search_param + 1) 
                         for q in range(0, (p-1)//2 + 1)]
            
            print("Searching octahedra...")
            if n_processes > 1:
                with Pool(processes=n_processes) as pool:
                    octa_results = list(tqdm(pool.starmap(self._process_octahedron, octa_tasks),
                                            total=len(octa_tasks), desc="Octahedra", ncols=80))
            else:
                octa_results = [self._process_octahedron(p, q) for p, q in tqdm(octa_tasks,
                                                                                desc="Octahedra", ncols=80)]
            
            # Filter and store results
            for result in octa_results:
                if result is not None:
                    diameter, filename, size, nbatoms, nbsurfatoms = result
                    structures_generated.append(('Octahedron', None, None, diameter))
                    if self.is_diameter_in_target_range(diameter):
                        structures_kept.append(('Octahedron', None, None, diameter))
                        kept_filenames.append(strufile_dir + filename + '.xyz')
                        results_to_write.append(f'{filename:50}\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}\n')
        
        # Generate spheres with auto-determined sizes
        print("Generating spheres...")
        for size in tqdm(self.size_array, desc="Spheres", ncols=80):
            filename,size,nbatoms=self.makeSphere(size)
            kept_filenames.append(strufile_dir + filename + '.xyz')  # Spheres always kept
            nbsurfatoms=self.detect_surface_atoms(strufile_dir+filename)
            results_to_write.append(f'{filename:50}\t{size:.4f}\t\t{nbatoms}\t\t\t{nbsurfatoms}\n')
        
        # Write all results to log
        line2write += ''.join(results_to_write)
        
        # Statistics
        line2write+='\n*****************************************************\n'
        line2write+=f'STATISTICS:\n'
        line2write+=f'Candidate structures tested: {len(structures_generated)}\n'
        line2write+=f'Structures kept: {len(structures_kept)} polyhedra + {len(self.size_array)} spheres\n'
        line2write+=f'Selection rate: {len(structures_kept)/max(len(structures_generated),1)*100:.1f}%\n'
        line2write+='*****************************************************\n'
        
        print('\n' + '='*60)
        print(f'GENERATION SUMMARY')
        print('='*60)
        print(f'Candidate structures tested: {len(structures_generated)}')
        print(f'Structures kept: {len(structures_kept)} polyhedra + {len(self.size_array)} spheres')
        print(f'Selection rate: {len(structures_kept)/max(len(structures_generated),1)*100:.1f}%')
        print(f'\nLog file: {logfile}')
        print('='*60)
        
        with open(logfile,'w')as f:
            f.write(line2write)
        
        # Save list of kept structures for screening
        kept_structures_file = strufile_dir + 'kept_structures.txt'
        with open(kept_structures_file, 'w') as f:
            for filename in kept_filenames:
                f.write(filename + '\n')
        
        return strufile_dir
