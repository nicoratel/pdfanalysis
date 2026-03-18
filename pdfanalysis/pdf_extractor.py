"""
PDF Extractor module for extracting PDFs from experimental data.
"""
import subprocess
import os
import numpy as np
from matplotlib import pyplot as plt


class PDFExtractor:
    def __init__(self,
                 datafilelist,
                 composition, 
                 qmin,
                 qmax,
                 qmaxinst,
                 wavelength=0.7107,
                 dataformat='QA',
                 rmin=0,
                 rmax=50,
                 rstep=0.01,
                 bgscale=1,
                 rpoly=0.9,
                 emptyfile=None):
        self.datafilelist=datafilelist
        self.emptyfile=emptyfile
        self.composition=composition
        self.qmin=qmin
        self.qmax=qmax
        self.qmaxinst=qmaxinst
        self.wl=wavelength
        self.dataformat=dataformat
        self.rmin=rmin
        self.rmax=rmax
        self.rstep=rstep
        self.bgscale=bgscale
        self.rpoly=rpoly


    def writecfg(self):
        """
        datafilelist: list of paths to data files from wich PDF should be extracted
        """

        self.datapath=os.path.dirname(self.datafilelist[0])
        self.pdfpath=self.datapath+'/extracted_PDF'
        
        os.makedirs(self.pdfpath,exist_ok=True)

        cfg=open(self.pdfpath+'/pdfgetX3_GUI.cfg','w')
        cfg.write('[DEFAULT] \n')
        cfg.write('dataformat = %s' %self.dataformat +' \n')
        
        
        
        cfg.write('inputfile='+''.join(os.path.basename(i) +'\n' +'\t'
                                for i in self.datafilelist[:-1]))
        cfg.write('\t %s' %os.path.basename(self.datafilelist[-1])+'\n')
        cfg.write('datapath = %s' % os.path.dirname(self.datafilelist[0])+'/' +'\n')
        if self.emptyfile is not None:
            cfg.write('\t %s' %os.path.dirname(self.emptyfile)+'\n')

            cfg.write('bgscale=%f \n' %self.bgscale)
            cfg.write('backgroundfile=%s' % os.path.basename(self.emptyfile)+'\n')
        
            
        cfg.write('composition= %s \n'%str(self.composition))
        cfg.write('qmin=%f \n' %self.qmin)
        cfg.write('qmax=%f \n' %self.qmax)
        cfg.write('qmaxinst=%f \n' %self.qmaxinst)
        cfg.write('wavelength=%f \n' %self.wl)
        cfg.write('mode = xray \n')
        cfg.write('rpoly=%f \n' %self.rpoly)
        cfg.write('rmin=%f \n' %self.rmin)
        cfg.write('rstep=%f \n' %self.rstep)
        cfg.write('rmax=%f \n' %self.rmax)       
        cfg.write('output=%s' %self.pdfpath +'/@b.@o \n')
        cfg.write('outputtype = sq,gr \n')
        #cfg.write('plot = iq,fq,gr \n' )
        cfg.write('force = yes \n')
        
        cfg.close()
        return
    

    def extractpdf(self):
        self.writecfg()
        command = 'conda run -n py36 pdfgetx3 -c' +self.pdfpath+'/pdfgetX3_GUI.cfg'

        # Use subprocess to execute the command
        subprocess.run(command, shell=True)
        print(f'PDF file(s) extracted in {self.pdfpath}')
        # Plot pdf
        
        fig,ax=plt.subplots()
        for file in self.datafilelist:
            rootname=(os.path.basename(file).split('/')[-1]).split('.')[0]
            pdffile=self.pdfpath+f'/{rootname}.gr'
            r,g=np.loadtxt(pdffile,skiprows=27,unpack=True)
            ax.plot(r,g,label=rootname)
        ax.set_xlabel('r ($\\AA$)')
        ax.set_ylabel('G(r)')
        fig.legend()
        fig.tight_layout()

        return self.pdfpath
