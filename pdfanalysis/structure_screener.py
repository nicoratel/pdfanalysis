"""
Structure Screener module for screening structures against experimental PDFs.
"""
import os
import glob
import re
from tqdm import tqdm
from .pdf_refinement import PDFRefinement
from .pdf_refinement_fast import PDFRefinementFast


class StructureScreener():
    
    def __init__(self,
                 strufile_dir:str,
                 pdffile_dir:str,
                 qdamp:float =0.014,
                 qbroad:float =0.04,
                 refinement_tags: dict ={'scale_factor': True, 'zoomscale': True, 'delta2': True, 'Uiso': True},
                 save_tag: bool=False,
                 RUN_PARALLEL:bool =True,
                 rbins : int =1,
                 rmin=0.01,
                 rmax_fast=15.0,

                 fast_screening: bool =False,
                 candidate_list: dict =None,
                 threshold_percent: float =5.0):
                 """
                 strufile_dir: path of directory containing structure files
                 pdffile_dir: path of directory containing pdf files
                 refinement_tags: dict ={'scale_factor': True, 'zoomscale': True, 'delta2': True, 'Uiso': True}
                 qdamp:float =0.014
                 qbroad:float =0.04
                 save_tag: bool=False
                 RUN_PARALLEL:bool =True
                 rbins : int =1
                 screening_tag: bool =True
                 candidate_list: dict = None (pass short-list from first screening for refinement)
                 threshold_percent: float = 5.0 (tolerance for candidate selection: min(Rw) ± threshold_percent%)
                 """       
                 self.strufile_dir=strufile_dir
                 self.pdffile_dir=pdffile_dir
                 self.qdamp=qdamp
                 self.qbroad=qbroad
                 self.refinement_tags=refinement_tags
                 self.save_tag=save_tag
                 self.RUN_PARALLEL=RUN_PARALLEL
                 self.rbins=rbins
                 self.rmin = rmin
                 self.screening_tag=True
                 self.logfile=self.strufile_dir+'/structure_screening.log'
                 self.fast_screening=fast_screening
                 self.candidate_list=candidate_list
                 self.threshold_percent=threshold_percent
                 self.rmax_fast=rmax_fast
        
    def get_filename(self,file):
        filename=os.path.basename(file).split('/')[-1]
        return filename.split('.')[0]
    
    def extract_phi(self,filename):
        match = re.search(r'_phi=(\d+)', filename)
    
        # Return the extracted number as an integer
        return int(match.group(1))
    
        

    def run(self):
        """
        PDF refinement of each PDF file in pdffile_dir with each structure file in strufile_dir
        Returns:
            - If fast_screening=True: (best_results, candidate_list) tuple
            - If fast_screening=False: best_results dict only
        """
        best_results={}
        candidate_list = {}
        pdffile_list=glob.glob(os.path.join(self.pdffile_dir,'*.gr'))

        # Get structure list based on screening type
        if self.candidate_list is None:  # First screening (fast or full)
            strufile_list=glob.glob(os.path.join(self.strufile_dir,'*.xyz'))
            strufile_list=sorted(strufile_list,key=self.extract_phi)
        else:  # Second screening with candidate_list
            # Get all unique structures from candidate_list
            all_strufiles = set()
            for pdf_structures in self.candidate_list.values():
                all_strufiles.update(pdf_structures)
            strufile_list = sorted(list(all_strufiles), key=self.extract_phi)
        
        # Check if generator has kept_structures attribute (from auto mode)
        # If yes, use only those structures
        kept_structures_file = os.path.join(self.strufile_dir, 'kept_structures.txt')
        if os.path.exists(kept_structures_file) and self.candidate_list is None:
            with open(kept_structures_file, 'r') as f:
                kept_list = [line.strip() for line in f if line.strip()]
            if kept_list:
                strufile_list = kept_list
                print(f"Using {len(strufile_list)} structures in target diameter range")
        
        line2write= '*****************************************************\n\n'
        line2write+='                 STRUCTURE SCREENING                 \n\n'
        line2write+='*****************************************************\n\n'
        line2write+=f'PDF file       \tStructure file                                   \tRw\n\n'
        j=0
        print(line2write)
        print(f"Number of PDF files to process: {len(pdffile_list)}")
        
        # Calculate total number of refinements for progress bar AFTER determining structures to use
        total_refinements = 0
        for pdffile in pdffile_list:
            if self.candidate_list is not None:
                pdf_key = os.path.basename(pdffile)
                if pdf_key in self.candidate_list:
                    total_refinements += len(self.candidate_list[pdf_key])
            else:
                # Count only structures that will actually be tested
                total_refinements += len(strufile_list)
        
        # Single progress bar for all refinements
        pbar = tqdm(total=total_refinements, desc="Refining structures", ncols=80)
        
        refinement_count = 0  # Track actual refinements
        
        for pdffile in pdffile_list:
            pdfname=self.get_filename(pdffile)
            
            # Determine which structures to test for this PDF
            if self.candidate_list is not None:
                # Use only candidates for this PDF
                pdf_key = os.path.basename(pdffile)
                if pdf_key not in self.candidate_list:
                    j += 1
                    continue
                strufile_list_to_use = self.candidate_list[pdf_key]
            else:
                # Use all structures (already filtered by kept_structures.txt if available)
                strufile_list_to_use = strufile_list
            
            # Store refinement results (Rw and zoomscale) for this PDF
            refinement_results = {}
            
            for strufile in strufile_list_to_use:
                struname=self.get_filename(strufile)
                if self.fast_screening:
                    calc = PDFRefinementFast(
                        pdffile,
                        strufile,
                        rbins=self.rbins,
                        rmin=self.rmin,
                        rmax_fast=self.rmax_fast
                    )
                else:
                    calc=PDFRefinement(pdffile,
                                    strufile,
                                    refinement_tags=self.refinement_tags,
                                    save_tag=self.save_tag,
                                    rbins=self.rbins,
                                    rmin = self.rmin,
                                    screening_tag=self.screening_tag)
                rw=calc.refine()
                # Extract zoomscale from recipe
                zoomscale = calc.recipe.zoomscale.value
                refinement_results[strufile] = {'Rw': rw, 'zoomscale': zoomscale}
                temp=f'{pdfname:15}\t{struname:50}\t{rw:.4f}\tzoomscale={zoomscale:.6f}'
                print(temp)
                line2write+=f'{pdfname:15}\t{struname:50}\t{rw:.4f}\tzoomscale={zoomscale:.6f}\n'
                refinement_count += 1
                pbar.update(1)  # Update progress bar after each refinement
            
            # Only compute candidate list if not already provided
            if self.candidate_list is None:
                # the following code is to extract structures with Min(Rwp) +- threshold%
                min_rw = min(result['Rw'] for result in refinement_results.values())
                threshold_low = min_rw * (1 - self.threshold_percent/100.0)
                threshold_high = min_rw * (1 + self.threshold_percent/100.0)

                pdfname_full = os.path.basename(pdffile)

                best_results_candidates = {}
                best_results_candidates[pdfname_full] = {}

                for strufile, result in refinement_results.items():
                    rw = result['Rw']
                    if threshold_low <= rw <= threshold_high:
                        best_results_candidates[pdfname_full][strufile] = result

                # Affichage trié par Rw croissant
                print("****************************************************\nListe des meilleures structures candidates (min(R_w) ± "+str(self.threshold_percent)+"%) :\n")
                line2write += '*******************************************************\nListe des meilleures structures candidates (min(R_w) ± '+str(self.threshold_percent)+'%) :\n'

                for key, struct_dict in best_results_candidates.items():
                    # Trier par Rw croissant
                    sorted_items = sorted(struct_dict.items(), key=lambda item: item[1]['Rw'])
                    candidate_list[key] = [item[0] for item in sorted_items]  # Store sorted structure paths
                    
                    for file, result in sorted_items:
                        print(f'Fichier PDF : {key}, Structure : {self.get_filename(file)}, Rw = {result["Rw"]:.4f}, zoomscale = {result["zoomscale"]:.6f}\n')
                        line2write += f'Fichier PDF : {key}, Structure : {self.get_filename(file)}, Rw = {result["Rw"]:.4f}, zoomscale = {result["zoomscale"]:.6f}\n'
            
            # Find best results (minimum Rw)
            best_strufile_item = min(refinement_results.items(), key=lambda x: x[1]['Rw'])
            best_strufile = best_strufile_item[0]
            best_result = best_strufile_item[1]
            best_rw = best_result['Rw']
            best_zoomscale = best_result['zoomscale']
            pdfname=os.path.basename(pdffile)
            beststru=os.path.basename(best_strufile)
            best_results[pdffile]={'strufile': best_strufile, 'Rw': best_rw, 'zoomscale': best_zoomscale}
            line2write+='*******************************************************\n'
            line2write+=f'{pdfname}\t best structure={beststru} \t Rw={best_rw:.4f}\t zoomscale={best_zoomscale:.6f}\n\n'
            print("****************************************************\n")
            print(f'{pdfname}\t best structure={beststru} \t Rw={best_rw:.4f}\t zoomscale={best_zoomscale:.6f}\n')
            j+=1
        
        pbar.close()  # Close progress bar
        
        with open(self.logfile,'w') as f:
            f.write(line2write)
        
        # Return candidate_list if fast_screening (for use in refinement pass)
        if self.fast_screening and self.candidate_list is None:
            return best_results, candidate_list
        else:
            return best_results
