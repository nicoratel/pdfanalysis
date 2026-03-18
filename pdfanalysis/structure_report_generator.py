"""
Structure Report Generator module for creating comprehensive PDF reports.
"""
import os
import numpy as np
from matplotlib import pyplot as plt


class StructureReportGenerator():
    """
    Generate comprehensive HTML/PDF reports for structure screening results
    """
    
    def __init__(self, strufile_dir, best_results, screening_log=None, all_screening_results=None):
        """
        Parameters:
        -----------
        strufile_dir: str
            Directory containing structure files and generation log
        best_results: dict
            Results from StructureScreener.run()
        screening_log: str, optional
            Path to screening log file
        all_screening_results: dict, optional
            Complete screening results dictionary {pdf_file: {strufile: {'Rw': float, 'zoomscale': float}}}
            If provided, will be used instead of parsing the log file
        """
        self.strufile_dir = strufile_dir
        self.best_results = best_results
        self.generation_log = os.path.join(strufile_dir, 'structure_generation.log')
        self.screening_log = screening_log or os.path.join(strufile_dir, 'structure_screening.log')
        self.all_screening_results = all_screening_results
        
    def parse_generation_log(self):
        """
        Parse structure_generation.log to extract diameter, natoms, surface atoms info
        
        Returns:
        --------
        dict: {structure_filename: {'diameter': float, 'natoms': int, 'surface_atoms': int}}
        """
        structure_info = {}
        
        if not os.path.exists(self.generation_log):
            print(f"Warning: Generation log not found at {self.generation_log}")
            return structure_info
        
        with open(self.generation_log, 'r') as f:
            lines = f.readlines()
        
        # Skip header lines
        data_started = False
        for line in lines:
            if 'Structure File' in line and 'Diameter' in line:
                data_started = True
                continue
            
            if data_started and line.strip():
                try:
                    parts = line.split()
                    if len(parts) >= 4:
                        filename = parts[0]
                        diameter = float(parts[1])
                        natoms = int(parts[2])
                        surface_atoms = int(parts[3])
                        
                        structure_info[filename] = {
                            'diameter': diameter,
                            'natoms': natoms,
                            'surface_atoms': surface_atoms,
                            'surface_fraction': surface_atoms / natoms if natoms > 0 else 0
                        }
                except (ValueError, IndexError):
                    continue
        
        return structure_info
    
    def generate_summary_dict(self):
        """
        Generate a comprehensive summary dictionary for programmatic access
        
        Returns:
        --------
        dict with complete information about screening results
        """
        structure_info = self.parse_generation_log()
        
        summary = {
            'strufile_dir': self.strufile_dir,
            'num_pdfs': len(self.best_results),
            'results': []
        }
        
        for pdf_file, result in self.best_results.items():
            strufile_basename = os.path.basename(result['strufile'])
            stru_info = structure_info.get(strufile_basename, {})
            
            result_dict = {
                'pdf_file': pdf_file,
                'pdf_name': os.path.basename(pdf_file),
                'strufile': result['strufile'],
                'strufile_name': strufile_basename,
                'Rw': result['Rw'],
                'zoomscale': result['zoomscale'],
                'diameter': stru_info.get('diameter'),
                'natoms': stru_info.get('natoms'),
                'surface_atoms': stru_info.get('surface_atoms'),
                'surface_fraction': stru_info.get('surface_fraction')
            }
            
            summary['results'].append(result_dict)
        
        return summary
    
    def parse_screening_log(self):
        """
        Parse structure_screening.log to extract all refinement results
        
        Returns:
        --------
        dict: {pdf_file: {strufile: {'Rw': float, 'zoomscale': float}}}
        """
        all_results = {}
        
        if not os.path.exists(self.screening_log):
            print(f"Warning: Screening log not found at {self.screening_log}")
            return all_results
        
        with open(self.screening_log, 'r') as f:
            lines = f.readlines()
        
        # Skip header lines
        data_started = False
        for line in lines:
            # Skip header and separator lines
            if 'STRUCTURE SCREENING' in line or '*****' in line or 'PDF file' in line:
                if 'PDF file' in line and 'Structure file' in line:
                    data_started = True
                continue
            
            if not data_started:
                continue
            
            line = line.strip()
            if not line or line.startswith('Liste des meilleures') or line.startswith('Fichier PDF'):
                continue
            
            # Parse result lines: PDF_name \t Structure_name \t Rw \t zoomscale=value
            # or: PDF_name \t Structure_name \t Rw
            parts = [p.strip() for p in line.split('\t') if p.strip()]
            
            if len(parts) >= 3:
                try:
                    pdf_name = parts[0]
                    stru_name = parts[1]
                    
                    # Extract Rw and zoomscale from the third part
                    rw_zoomscale_str = parts[2]
                    
                    # Check if zoomscale is in a separate column or in the same
                    if len(parts) >= 4 and 'zoomscale=' in parts[3]:
                        # Format: PDF \t Structure \t Rw \t zoomscale=value
                        rw = float(rw_zoomscale_str)
                        zoomscale_str = parts[3].replace('zoomscale=', '').strip()
                        zoomscale = float(zoomscale_str)
                    elif 'zoomscale=' in rw_zoomscale_str:
                        # Format: PDF \t Structure \t Rw\tzoomscale=value
                        rw_part = rw_zoomscale_str.split('zoomscale=')[0].strip()
                        zoom_part = rw_zoomscale_str.split('zoomscale=')[1].strip()
                        rw = float(rw_part)
                        zoomscale = float(zoom_part)
                    else:
                        # Format: PDF \t Structure \t Rw (no zoomscale)
                        rw = float(rw_zoomscale_str)
                        zoomscale = None
                    
                    # Store results - use PDF basename if it's a full path
                    if '/' in pdf_name:
                        pdf_name = os.path.basename(pdf_name)
                    
                    if pdf_name and stru_name:
                        if pdf_name not in all_results:
                            all_results[pdf_name] = {}
                        all_results[pdf_name][stru_name] = {
                            'Rw': rw,
                            'zoomscale': zoomscale
                        }
                except (ValueError, IndexError) as e:
                    # Debug: print problematic line
                    # print(f"Could not parse line: {line} - Error: {e}")
                    continue
        
        return all_results
    
    def get_top_n_results(self, n=10, pdf_file=None):
        """
        Get top N refinement results sorted by Rw
        
        Parameters:
        -----------
        n: int
            Number of top results to return
        pdf_file: str, optional
            Specific PDF file to analyze. If None, uses first PDF in best_results
            
        Returns:
        --------
        list of dicts with structure info and Rw values
        """
        # Use provided all_screening_results or parse log
        if self.all_screening_results:
            all_results = self.all_screening_results
        else:
            all_results = self.parse_screening_log()
        
        if not all_results:
            print("No results found. Try providing all_screening_results when creating StructureReportGenerator.")
            return []
        
        # Select PDF file
        if pdf_file is None:
            # Get first PDF from best_results
            first_pdf = list(self.best_results.keys())[0]
            pdf_file = os.path.basename(first_pdf)
        else:
            pdf_file = os.path.basename(pdf_file)
        
        # Try different PDF name formats
        pdf_results = None
        if pdf_file in all_results:
            pdf_results = all_results[pdf_file]
        else:
            # Try without extension
            pdf_base = os.path.splitext(pdf_file)[0]
            for key in all_results.keys():
                if pdf_base in key or key in pdf_base:
                    pdf_results = all_results[key]
                    break
        
        if not pdf_results:
            print(f"PDF file {pdf_file} not found in results")
            print(f"Available PDFs: {list(all_results.keys())}")
            return []
        
        # Get structure info
        structure_info = self.parse_generation_log()
        
        # Collect and sort results
        results_list = []
        for stru_name, refinement in pdf_results.items():
            stru_info = structure_info.get(stru_name, {})
            
            result = {
                'structure_name': stru_name,
                'structure_path': os.path.join(self.strufile_dir, stru_name),
                'Rw': refinement['Rw'],
                'zoomscale': refinement.get('zoomscale', 1.0),
                'diameter': stru_info.get('diameter'),
                'natoms': stru_info.get('natoms'),
                'surface_atoms': stru_info.get('surface_atoms'),
                'surface_fraction': stru_info.get('surface_fraction')
            }
            results_list.append(result)
        
        # Sort by Rw and return top N
        results_list.sort(key=lambda x: x['Rw'])
        return results_list[:n]
    
    def generate_structure_thumbnail(self, strufile, zoomscale, output_path, size=(400, 400)):
        """
        Generate a thumbnail image of a structure using matplotlib
        
        Parameters:
        -----------
        strufile: str
            Path to structure file
        zoomscale: float
            Zoomscale to apply
        output_path: str
            Path where to save the thumbnail
        size: tuple
            Size of the image (width, height) in pixels
        """
        # Check if structure file exists
        if not os.path.exists(strufile):
            return None
        
        try:
            
            # Fallback to matplotlib if py3Dmol fails
            from matplotlib import pyplot as plt
            from mpl_toolkits.mplot3d import Axes3D
            from scipy.spatial import distance_matrix
            
            # Dictionnaires des propriétés atomiques
            atomic_radii = {
                'Au': 1.44, 'Ag': 1.45, 'Cu': 1.28, 'Pt': 1.39, 'Pd': 1.37,
                'Fe': 1.26, 'Ni': 1.24, 'Co': 1.25, 'Cr': 1.28, 'Mn': 1.27,
                'Ti': 1.47, 'V': 1.35, 'Zn': 1.34, 'Al': 1.43, 'Si': 1.18,
                'C': 0.77, 'O': 0.73, 'N': 0.71, 'H': 0.53, 'S': 1.04
            }
            
            element_colors = {
                'Au': 'gold', 'Ag': 'silver', 'Cu': 'orange', 'Pt': 'lightgray', 'Pd': 'lightblue',
                'Fe': 'orangered', 'Ni': 'lightgreen', 'Co': 'blue', 'Cr': 'gray', 'Mn': 'violet',
                'Ti': 'silver', 'V': 'darkgray', 'Zn': 'steelblue', 'Al': 'lightgray', 'Si': 'tan',
                'C': 'dimgray', 'O': 'red', 'N': 'blue', 'H': 'white', 'S': 'yellow'
            }
            
            data = np.loadtxt(strufile, skiprows=2, 
                             dtype=[('element', 'U2'), ('x', 'f4'), ('y', 'f4'), ('z', 'f4')])
            coords = np.column_stack([data['x'], data['y'], data['z']]) * zoomscale
            
            # Détecter l'élément principal (le plus fréquent)
            elements, counts = np.unique(data['element'], return_counts=True)
            main_element = elements[np.argmax(counts)]
            main_element = main_element.strip()
            
            # Récupérer les propriétés de l'élément
            atom_radius = atomic_radii.get(main_element, 1.4)  # défaut si élément inconnu
            atom_color = element_colors.get(main_element, 'gray')
            edge_color = 'darkgray' if main_element not in ['Au', 'Ag'] else f'dark{atom_color}'
            
            # Calculer la distance minimale entre atomes voisins pour dimensionner les sphères
            if len(coords) > 1:
                dist_mat = distance_matrix(coords, coords)
                # Mettre la diagonale à inf pour ignorer la distance d'un atome à lui-même
                np.fill_diagonal(dist_mat, np.inf)
                min_dist = np.min(dist_mat)
                # Utiliser 85% de la distance minimale comme rayon pour un léger overlap
                sphere_radius = min_dist * 0.85 / 2.0
            else:
                sphere_radius = atom_radius
            
            fig = plt.figure(figsize=(size[0]/100, size[1]/100), dpi=100)
            ax = fig.add_subplot(111, projection='3d')
            
            # Calculer la plage des axes
            max_range = np.array([coords[:, 0].max()-coords[:, 0].min(),
                                 coords[:, 1].max()-coords[:, 1].min(),
                                 coords[:, 2].max()-coords[:, 2].min()]).max() / 2.0
            
            mid_x = (coords[:, 0].max()+coords[:, 0].min()) * 0.5
            mid_y = (coords[:, 1].max()+coords[:, 1].min()) * 0.5
            mid_z = (coords[:, 2].max()+coords[:, 2].min()) * 0.5
            
            ax.set_xlim(mid_x - max_range, mid_x + max_range)
            ax.set_ylim(mid_y - max_range, mid_y + max_range)
            ax.set_zlim(mid_z - max_range, mid_z + max_range)
            
            # Convertir le rayon physique en taille de point pour scatter
            # La taille s dans scatter est en points^2
            # On calcule la taille en fonction de la plage de l'axe et de la résolution
            fig_size_inches = size[0] / 100  # taille de la figure en inches
            points_per_unit = (fig_size_inches * 72) / (2 * max_range)  # points par unité Å
            sphere_size_points = (sphere_radius * points_per_unit) ** 2
            
            ax.scatter(coords[:, 0], coords[:, 1], coords[:, 2], 
                      c='gold', s=sphere_size_points, alpha=0.9, 
                      edgecolors='darkgoldenrod', linewidths=0.5)
            
            ax.set_xlabel('X (Å)', fontsize=8)
            ax.set_ylabel('Y (Å)', fontsize=8)
            ax.set_zlabel('Z (Å)', fontsize=8)
            ax.grid(False)
            ax.set_facecolor('white')
            # Masquer les axes pour un rendu plus propre
            ax.set_xticks([])
            ax.set_yticks([])
            ax.set_zticks([])
            
            plt.tight_layout()
            plt.savefig(output_path, dpi=100, bbox_inches='tight', facecolor='white')
            plt.close()
            return output_path
        except Exception:
            return None
    
    def generate_pdf_report(self, output_path='structure_screening_report.pdf', n_top=10, pdf_file=None):
        """
        Generate comprehensive PDF report with top N refinement results
        
        Parameters:
        -----------
        output_path: str
            Path for output PDF file
        n_top: int
            Number of top results to include (default: 10)
        pdf_file: str, optional
            Specific PDF file to analyze. If None, uses first PDF in best_results
        """
        try:
            from matplotlib.backends.backend_pdf import PdfPages
            from matplotlib import pyplot as plt
            import matplotlib.patches as mpatches
        except ImportError:
            print("Matplotlib required for PDF generation")
            return None
        
        # Get top N results
        top_results = self.get_top_n_results(n=n_top, pdf_file=pdf_file)
        
        if not top_results:
            print("No results to generate report")
            return None
        
        # Select PDF file name
        if pdf_file is None:
            pdf_file = list(self.best_results.keys())[0]
        pdf_name = os.path.basename(pdf_file)
        
        # Create output directory for thumbnails
        thumb_dir = os.path.join(self.strufile_dir, 'thumbnails')
        os.makedirs(thumb_dir, exist_ok=True)
        
        # Full output path
        output_full_path = os.path.join(self.strufile_dir, output_path)
        
        with PdfPages(output_full_path) as pdf:
            # Page 1: Complete Overview - Fit Curve + Thumbnail + Details
            best_result = top_results[0]
            best_strufile_name = best_result['structure_name']
            
            # Get best structure file path
            if 'structure_path' in best_result and os.path.exists(best_result['structure_path']):
                best_strufile_path = best_result['structure_path']
            else:
                best_strufile_path = os.path.join(self.strufile_dir, best_strufile_name + '.xyz')
            
            # Generate thumbnail for best structure and save it
            best_thumb_path = os.path.join(thumb_dir, f"best_structure_{best_strufile_name}.png")
            
            if os.path.exists(best_strufile_path):
                self.generate_structure_thumbnail(
                    best_strufile_path, 
                    best_result['zoomscale'] if best_result['zoomscale'] else 1.0,
                    best_thumb_path,
                    size=(500, 500)
                )
            
            # Create comprehensive first page
            fig = plt.figure(figsize=(8.5, 11))
            fig.suptitle('Structure Screening Report - Best Result', fontsize=18, fontweight='bold', y=0.98)
            
            # Create grid for layout: [fit curve (top), thumbnail + info (bottom)]
            gs = fig.add_gridspec(2, 2, height_ratios=[1.2, 1], width_ratios=[1.2, 1], 
                                  hspace=0.3, wspace=0.3, left=0.08, right=0.95, top=0.93, bottom=0.05)
            
            # Top: Fit curve (spans both columns)
            ax_fit = fig.add_subplot(gs[0, :])
            
            # Find fit data
            pdf_basename = os.path.basename(pdf_file).replace('.gr', '')
            png_locations = [
                os.path.join(self.strufile_dir, 'fig', f"{pdf_basename}_{best_strufile_name}.png"),
                os.path.join(self.strufile_dir, f"{pdf_basename}_{best_strufile_name}.png")
            ]
            fit_locations = [
                os.path.join(self.strufile_dir, 'fit', f"{pdf_basename}_{best_strufile_name}.fit"),
                os.path.join(self.strufile_dir, f"{pdf_basename}_{best_strufile_name}.fit")
            ]
            
            png_file = None
            for png_loc in png_locations:
                if os.path.exists(png_loc):
                    png_file = png_loc
                    break
            
            fit_file = None
            for fit_loc in fit_locations:
                if os.path.exists(fit_loc):
                    fit_file = fit_loc
                    break
            
            if png_file:
                img = plt.imread(png_file)
                ax_fit.imshow(img)
                ax_fit.axis('off')
                ax_fit.set_title(f'Best Fit: {best_strufile_name} (Rw={best_result["Rw"]:.4f})', 
                                fontsize=12, fontweight='bold')
            elif fit_file:
                data = np.loadtxt(fit_file, skiprows=0)
                r = data[:, 0]
                g_obs = data[:, 1]
                g_calc = data[:, 2]
                diff = g_obs - g_calc
                
                ax_fit.plot(r, g_obs, 'bo', label='Observed', markersize=2, alpha=0.6)
                ax_fit.plot(r, g_calc, 'r-', label='Calculated', linewidth=1.5)
                ax_fit.set_ylabel('G(r) (Å⁻²)', fontsize=10)
                ax_fit.set_xlabel('r (Å)', fontsize=10)
                ax_fit.set_title(f'Best Fit: {best_strufile_name} (Rw={best_result["Rw"]:.4f})', 
                                fontsize=12, fontweight='bold')
                ax_fit.legend(fontsize=8)
                ax_fit.grid(alpha=0.3)
            else:
                ax_fit.text(0.5, 0.5, 'Fit curve not available', 
                           ha='center', va='center', fontsize=10)
                ax_fit.axis('off')
            
            # Bottom left: Structure thumbnail
            ax_thumb = fig.add_subplot(gs[1, 0])
            if os.path.exists(best_thumb_path):
                thumb_img = plt.imread(best_thumb_path)
                ax_thumb.imshow(thumb_img)
                ax_thumb.set_title('3D Structure', fontsize=11, fontweight='bold')
            else:
                ax_thumb.text(0.5, 0.5, 'Thumbnail\nnot available', 
                             ha='center', va='center', fontsize=10)
            ax_thumb.axis('off')
            
            # Bottom right: Detailed information
            ax_info = fig.add_subplot(gs[1, 1])
            ax_info.axis('off')
            
            # Format values
            best_zoomscale = f"{best_result['zoomscale']:.6f}" if best_result['zoomscale'] else 'N/A'
            best_diameter = f"{best_result['diameter']:.2f}" if best_result['diameter'] else 'N/A'
            best_natoms = best_result['natoms'] if best_result['natoms'] else 'N/A'
            best_surface = best_result['surface_atoms'] if best_result['surface_atoms'] else 'N/A'
            best_surf_pct = f"({best_result['surface_fraction']*100:.1f}%)" if best_result['surface_fraction'] else ''
            
            info_text = f"""
PDF: {pdf_name}

═══════════════════════
REFINEMENT RESULTS:
═══════════════════════
Rw: {best_result['Rw']:.4f}
Zoomscale: {best_zoomscale}

═══════════════════════
STRUCTURE PROPERTIES:
═══════════════════════
Name: {best_strufile_name}
Diameter: {best_diameter} Å
Total atoms: {best_natoms}
Surface atoms: {best_surface} {best_surf_pct}

═══════════════════════
REPORT INFO:
═══════════════════════
Generated: {np.datetime64('now')}
Top {n_top} results included
            """
            
            ax_info.text(0.05, 0.95, info_text, fontsize=9, family='monospace',
                        verticalalignment='top', transform=ax_info.transAxes)
            
            pdf.savefig(fig, bbox_inches='tight')
            plt.close()
            
            # Page 2-3: Top N Results Table
            n_per_page = 15
            for page_num, i in enumerate(range(0, len(top_results), n_per_page)):
                fig, ax = plt.subplots(figsize=(8.5, 11))
                ax.axis('off')
                
                page_results = top_results[i:i+n_per_page]
                
                # Create table data
                table_data = [['Rank', 'Structure', 'Rw', 'Zoomscale', 'Diam.(Å)', 'Atoms', 'Surf.%']]
                
                for idx, res in enumerate(page_results, start=i+1):
                    row = [
                        f'{idx}',
                        res['structure_name'][:30],
                        f"{res['Rw']:.4f}",
                        f"{res['zoomscale']:.4f}" if res['zoomscale'] else 'N/A',
                        f"{res['diameter']:.1f}" if res['diameter'] else 'N/A',
                        f"{res['natoms']}" if res['natoms'] else 'N/A',
                        f"{res['surface_fraction']*100:.1f}" if res['surface_fraction'] else 'N/A'
                    ]
                    table_data.append(row)
                
                table = ax.table(cellText=table_data, loc='center', cellLoc='left')
                table.auto_set_font_size(False)
                table.set_fontsize(9)
                table.scale(1, 2)
                
                # Style header row
                for i in range(len(table_data[0])):
                    table[(0, i)].set_facecolor('#3498db')
                    table[(0, i)].set_text_props(weight='bold', color='white')
                
                # Alternate row colors
                for i in range(1, len(table_data)):
                    for j in range(len(table_data[0])):
                        if i % 2 == 0:
                            table[(i, j)].set_facecolor('#f0f0f0')
                
                ax.set_title(f'Top {n_top} Refinement Results (Page {page_num+1})', 
                           fontsize=14, fontweight='bold', pad=20)
                
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()
            
            # Page: Structure Thumbnails (4 per page)
            for page_idx in range(0, min(n_top, 12), 4):
                fig, axes = plt.subplots(2, 2, figsize=(8.5, 11))
                fig.suptitle(f'Structure Visualizations (Rank {page_idx+1}-{page_idx+4})', 
                           fontsize=14, fontweight='bold')
                
                axes = axes.flatten()
                
                for idx in range(4):
                    if page_idx + idx >= len(top_results):
                        axes[idx].axis('off')
                        continue
                    
                    res = top_results[page_idx + idx]
                    
                    # Use structure_path if available, otherwise construct it
                    if 'structure_path' in res and os.path.exists(res['structure_path']):
                        strufile_path = res['structure_path']
                    else:
                        strufile_path = os.path.join(self.strufile_dir, res['structure_name'] + '.xyz')
                    
                    thumb_path = os.path.join(thumb_dir, f"thumb_{page_idx+idx}.png")
                    
                    if os.path.exists(strufile_path):
                        self.generate_structure_thumbnail(
                            strufile_path, 
                            res['zoomscale'] if res['zoomscale'] else 1.0,
                            thumb_path
                        )
                        
                        if os.path.exists(thumb_path):
                            img = plt.imread(thumb_path)
                            axes[idx].imshow(img)
                    
                    axes[idx].axis('off')
                    title_text = f"#{page_idx+idx+1}: Rw={res['Rw']:.4f}\n{res['natoms']} atoms" if res['natoms'] else f"#{page_idx+idx+1}: Rw={res['Rw']:.4f}"
                    axes[idx].set_title(title_text, fontsize=10)
                
                plt.tight_layout()
                pdf.savefig(fig, bbox_inches='tight')
                plt.close()
        
        return output_full_path
