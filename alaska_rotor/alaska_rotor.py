# alaska imports
import alaskaFEBodyModule as alaFEBody

from .alaska_rotor_files import copy_alaska_rotor, generate_rotor_blade_model_file, generate_rotor_blade_submodel_xml_file
from alaska_io import AlaskaXmlFile, AlaskaParameterSetFile, AlaskaH5ResultFile


# os-correct file and path manipulations
from pathlib import Path
# file operations
import shutil

# import to call alaska/Batch
import subprocess


class AlaskaRotor:
    """
    class for Python-generated alaska rotor model.
    
    Attributes
    ----------
    blade_file : Path
        path and filename of blade input file (alaska XML format)
        
    airfoil_file : Path
        path and filenam of airfoil file (alaska XML format)
        
    rotor_model_folder : Path
        path of simulation model 
        
    loadcase_file : AlaskaParameterSetFile
        LoadCase to be used in alaska simution setting up environmental conditions, simulation parameters, etc.
    
    result_file : AlaskaH5ResultFile
        result file of simulation in hdf5 format
        
    alaska_bin_path : str | Path
        path to alaska bin folder 
    """
    
    blade_file : Path
    airfoil_file : Path
    rotor_model_folder : Path
    loadcase_file : AlaskaParameterSetFile
    result_file : AlaskaH5ResultFile
    alaska_bin_path : str | Path

    def __init__(self , blade_file_name : str = None, airfoil_file_name : str = None, rotor_model_folder : str | Path = None):
    
        self.blade_file = Path("")
        self.airfoil_file = Path("")
        self.rotor_model_folder = Path("")    
        self._BladeName          = "FEBlade"        
        
        if blade_file_name is not None:
            self.blade_file = Path(blade_file_name)
        if airfoil_file_name is not None:
            self.airfoil_file = Path(airfoil_file_name)
        if rotor_model_folder is not None:
            self.rotor_model_folder= Path(rotor_model_folder)

        # self.LoadCase : alaPSF | None = None
        self.loadcase_file = AlaskaParameterSetFile()
        self.alaska_bin_path = ""
        self.result_file = AlaskaH5ResultFile()

    def _check_input_files(self) -> bool:
        """
        check input files for rotor model generation
        """
        check = True
        if self.blade_file.is_file():
            print(f"Found blade description file '{self.blade_file}'.")
        else: 
            print(f"Did not find blade description file: {self.blade_file}")
            check = False
        if self.airfoil_file.is_file():
            print(f"Found airfoil file '{self.airfoil_file}'.")
        else: 
            print(f"Did not find airfoil file: {self.airfoil_file}")
            check = False
        return check

    def generate_rotor_model(self) -> None:
        """
        main function generating alaska rotor model using
        - self.rotor_model_folder as destination folder to store simulation model 
        - self.blade_file to generate rotor blade model
        - airfoil_file as airfoil file for rotor blade model
        """
        if not self._check_input_files():
            return
        # ----- copy basic rotor
        print(f"Copy alaska rotor model to folder: {self.rotor_model_folder}")
        copy_alaska_rotor(self.rotor_model_folder)

        # change AerofoilReferences in blade.xml input file to path where airfoil file will be moved        
        blade_file_content = AlaskaXmlFile( filename = str(self.blade_file) )
        if "AerofoilReferences" in blade_file_content.names_variable():
            # blade_file_content.set_variable_value("AerofoilReferences", str(Path("../Blades/") / self.airfoil_file))
            blade_file_content.set_variable_value("AerofoilReferences", str("../Blades/" + str(self.airfoil_file)))
        else:
            print(f"Did not find 'AerofoilReferences' in blade input file: {self.blade_file}. Aborting rotor model creation")
            return

        # add templates for requests
        blade_file_content.add_string_variable("AdditionalTemplateFile", "../Templates/Templates.tpl")
        
        # write blade.xml with adopted AerofoilReferences and additional template
        print("Write alaska rotor blade .xml input with adopted AerofoilReferences.")
        blade_file_aero = str(self.rotor_model_folder / "Blades" /"Blade.xml")
        blade_file_content.write( blade_file_aero )
        
        # get fef content to retrieve Node table
        fef_content_str = alaFEBody.getBladeFef_str(blade_file_aero)
        fef_content_xml = AlaskaXmlFile()
        fef_content_xml.read_from_str(fef_content_str)
        
        node_table = fef_content_xml.get_table("Quaternion")
        nodes = node_table["Content"]
        self._NodeIDs = nodes[:,0]
        self._NodePosX = nodes[:,1]
        frames_table = fef_content_xml.get_table("BeamFramesQuaternion")
        self._FrameIDs = frames_table["Content"][:,0]
        
        additional_template_code = self._generate_additional_template_code()
        
        print("Copy alaska rotor blade .mdl and .xml files.")
        generate_rotor_blade_model_file( self.rotor_model_folder / "Submodels" / "Blade.mdl")
        generate_rotor_blade_submodel_xml_file( self.rotor_model_folder / "SubmodelsData" / "Blade_1.xml", blade_number="1")
        generate_rotor_blade_submodel_xml_file( self.rotor_model_folder / "SubmodelsData" / "Blade_2.xml", blade_number="2")
        generate_rotor_blade_submodel_xml_file( self.rotor_model_folder / "SubmodelsData" / "Blade_3.xml", blade_number="3")
        
        print("Copy airfoil file.")
        shutil.copy2( self.airfoil_file  , self.rotor_model_folder / "Blades"/ Path(self.airfoil_file).name)

        # ----- generate blade model ------------
        print("Generate rotor blade model files (.fef and .tpl) using alaskaFEBodyModule.")
        alaFEBody.generateBladeTemplates(BDFile = blade_file_aero , BladeName = self._BladeName, bladetpl_folder = str(self.rotor_model_folder / "Blades") , rel_fef_path ="../Blades/", AddTplCode= additional_template_code)

        # ----- configure load case file (change environmental conditions and rotor parameters)
        lc_file = str(self.rotor_model_folder / "LoadCases" / "LoadCases.xml")
        self.loadcase_file.read(str (lc_file))

        
    def run_alaska_simulation(self) -> None:
        """
        run alaska simuöation using current alaska rotor model 
        - self.alaska_bin_path is search for ala_batch.exe 
        - self.loadcase_file.filename is used as argument to call ala_batch.exe
        - self.result_file will contain simulation results after finished simulation
        """
        
        ala_batch = Path(self.alaska_bin_path) / "ala_batch.exe"

        if ala_batch.is_file():
            print(f"Found alaska/Batch on path '{self.alaska_bin_path}'.")
        else: 
            print(f"Did not find alaska/Batch on path: {self.alaska_bin_path}")
        

        cmd = [ala_batch, self.loadcase_file.filename]

        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True
            )

        # fetch console logging
        for line in process.stdout:
            print(line, end='')

        process.wait()

        print("Returncode:", process.returncode)

        # setup result file name and build index 
        res_file = "Rotor_"+self.loadcase_file.tables[0]["Content"][0][0] + ".hdf5" 
        self.result_file = AlaskaH5ResultFile(self.rotor_model_folder / "Results" / res_file)


    def load_results(self):
        """
        loads AlaskaH5ResultFile instance 
        
        Returns
        -------
         : tuple
            data, head, units
        
        """
       
        return self.result_file.load_simulation_results("turbine")

    def _generate_additional_template_code(self) -> str:
        """
        generate additional rotor blade template code
        - mainly contains configuration of data export = results/requests
        
        Returns
        -------
        additional_template_code : str
        """
        
        additional_template_code = ""
        
        additional_template_code += "\tTContainer Requests;\n"
        additional_template_code += "\tRequests {\n"        
        
        # blade Node deflections (PosY PosZ RotX)
        for ID in self._NodeIDs[1:]:
            tpl_line = "\t\t"+"TRequestBladeNodeDefl RequestBladeNodeDefl" + ID + "(Body.Nodes.Node"+ID+".Pos, Body.Nodes.Node"+ID+".Rot, "+ ID+");\n"
            additional_template_code += tpl_line
        additional_template_code += "\n"

        # blade loads
        for ID in self._NodeIDs[0:-1]:
            tpl_line = "\t\t"+"TRequestRWTBladeLoads RequestBladeLoads" + ID + "(Body.InternalForces.InternalForce"+ID+".RFrc, Body.InternalForces.InternalForce"+ID+".RTrq, "+ ID+");\n"
            additional_template_code += tpl_line
        additional_template_code += "\n"

        # blade aerodynamic forces
        for ID in self._FrameIDs:
            tpl_line = "\t\t"+"TRequestRWTBladeForce RequestBladeForces" + ID + "(Body.Forces.Force"+ID+".Force[3], Body.Forces.Force"+ID+".Force[2], Body.Forces.Force"+ID+".Torque[1], "+ ID+");\n"
            additional_template_code += tpl_line

        additional_template_code += "\t}\n"        
            
        return additional_template_code
    
        