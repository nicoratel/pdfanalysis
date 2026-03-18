"""
Structure Custom module for transforming structures with zoomscale and substitutions.
"""
import os
import numpy as np
import random


class StructureCustom():
    def __init__ (self, 
                  strufile: str,
                  zoomscale:float = 1,
                  new_element: str =None,
                  fraction :float=0):
        """
        strufile: str, full path to structure file (xyz file)
        zoomscale: float, coefficient to adjust interatomic distance
        new_element: str, element to insert in the structure (randomly)
        fraction: float, fraction of the new element (between 0 and 1)
        """
        self.strufile=strufile
        self.path=os.path.dirname(self.strufile)
        self.zoomscale=zoomscale
        self.new_element=new_element
        self.fraction=fraction

    def apply_zoomscale(self):        
        self.x=[x*self.zoomscale for x in self.x]
        self.y=[y*self.zoomscale for y in self.y]
        self.z=[z*self.zoomscale for z in self.z]
        return self.x, self.y, self.z
    
    def transform_structure(self):
        # extract data (element,x,y,z) from xyz file
        data=np.loadtxt(self.strufile,skiprows=2,dtype=[('element', 'U2'), ('x', 'f4'), ('y', 'f4'), ('z', 'f4')])
        self.element=data['element']
        self.x=data['x'];self.y=data['y'];self.z=data['z']
        # apply zoomscale coefficient
        self.x, self.y, self.z=self.apply_zoomscale()
        
        # perform random substitution
        initial_elements=np.unique(self.element)
        initcompo=''
        for el in initial_elements:
            initcompo+=el
        N=len(self.element)
        k=N #number of initial elements
        if self.new_element is not None:           
            n=0 #number of new elements inserted in structure        
            while n<=(N*self.fraction):
                random_number = random.randint(0, N-1)
                if self.element[random_number] != self.new_element:
                    self.element[random_number]=self.new_element
                    n+=1
                    k-=1                    
                else: 
                    pass
                final_content='{%s'%initcompo+':%d'%k+',%s'%self.new_element+':%d}'%n
                outputfile=self.strufile.split('.')[0]+f'_zoomscale={self.zoomscale:.2f}_{initcompo}{100*(1-self.fraction):.0f}{self.new_element}{self.fraction*100:.0f}.xyz'
        else: # no random substitution
            final_content='{%s'%initcompo+':%d'%k+'}'
            outputfile=self.strufile.split('.')[0]+f'_zoomscale={self.zoomscale:.2f}.xyz'
        # write transformed structure to xyz file
        line2write=f'{N}\n{final_content}\n'
        for i in range(N):
            line2write += f"{self.element[i]} \t {self.x[i]:.4f} \t {self.y[i]:.4f} \t {self.z[i]:.4f} \n"
        
        with open(outputfile,'w') as f:
            f.write(line2write)
        return outputfile
    
    def writexyz(self,filename,atoms):
        """atoms ase Atoms object"""
        #cifname=(os.path.basename(self.cif_file).split('/')[-1]).split('.')[0]
        
        
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
        with open(f'/{filename}','w') as file:
            file.write(line2write)
    
    def view_structure(self, style='sphere', width=400, height=400, spin=True):
        """
        Visualize structure in 3D using py3Dmol in Jupyter notebook
        
        Parameters:
        -----------
        style: str, default='sphere'
            Visualization style: 'sphere', 'stick', 'cartoon', 'line', 'cross'
        width: int, default=400
            Width of the viewer in pixels
        height: int, default=400
            Height of the viewer in pixels
        spin: bool, default=True
            Enable automatic rotation
            
        Returns:
        --------
        view: py3Dmol.view object
        """
        try:
            import py3Dmol
        except ImportError:
            print("py3Dmol not installed. Install with: pip install py3Dmol")
            return None
        
        # Read structure data
        data = np.loadtxt(self.strufile, skiprows=2, 
                         dtype=[('element', 'U2'), ('x', 'f4'), ('y', 'f4'), ('z', 'f4')])
        
        elements = data['element']
        coords = np.column_stack([data['x'], data['y'], data['z']]) * self.zoomscale
        
        # Create XYZ format string
        xyz_string = f"{len(elements)}\n"
        xyz_string += f"Structure with zoomscale={self.zoomscale}\n"
        for i, elem in enumerate(elements):
            xyz_string += f"{elem} {coords[i,0]:.6f} {coords[i,1]:.6f} {coords[i,2]:.6f}\n"
        
        # Create 3D viewer
        view = py3Dmol.view(width=width, height=height)
        view.addModel(xyz_string, 'xyz')
        
        # Apply style
        view.setStyle({style: {}})
        
        # Enable spin if requested
        if spin:
            view.spin(True)
        
        view.zoomTo()
        return view
    
    def get_structure_info(self):
        """
        Extract structure information including atom count and composition
        
        Returns:
        --------
        dict with keys: 'natoms', 'composition', 'elements'
        """
        data = np.loadtxt(self.strufile, skiprows=2, 
                         dtype=[('element', 'U2'), ('x', 'f4'), ('y', 'f4'), ('z', 'f4')])
        
        elements = data['element']
        composition = {}
        for elem in elements:
            composition[elem] = composition.get(elem, 0) + 1
        
        return {
            'natoms': len(elements),
            'composition': composition,
            'elements': list(composition.keys()),
            'zoomscale': self.zoomscale
        }
