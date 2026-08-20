from pathlib import Path
import zipfile
from jinja2 import Template


def copy_alaska_rotor(model_folder: str | Path):
    """
    Copy alaska wind turbine rotor model to model_folder
    
    Parameters
    ----------
    model_folder
        folder where alaska rotor model should be copied (relative path to working directory or absolute path)
    """
    zip_name = "PyRotor.zip"
    base_dir = Path(__file__).parent
    zip_path = base_dir / zip_name

    # ensure Path object + absolute path
    model_folder = Path(model_folder).resolve()

    # make directory 
    model_folder.mkdir(parents=True, exist_ok=True)

    # un-zip
    with zipfile.ZipFile(zip_path, 'r') as z:
        z.extractall(model_folder)

    print(f"Archive '{zip_name}' unpacked to: {model_folder}")


def generate_rotor_blade_model_file(
    filename: str | Path,
    blade_template_file : str = "FEBlade.tpl",
    blade_name : str ="Blade",
    blade_template_name : str = "FEBlade"
):
    """
    generate rotor blade model file to instantiate rotor blade model template
    
    Parameters
    ----------
    filename: 
        filename of rotor blade model file
    
    blade_template_file
        filename of rotor blade template file
        
    blade_name 
        name of rotor blade
        
    blade_template_name 
        name of rotor blade template
    """
    base_dir = Path(__file__).parent
    template_path = base_dir / "rotor_blade_model.j2"

    template = Template(template_path.read_text())

    blade_model_file = template.render(
        blade_tpl_name = blade_template_name,
        blade_tpl_file = blade_template_file,
        blade_name = blade_name
    )

    Path(filename).write_text(blade_model_file)


def generate_rotor_blade_submodel_xml_file(
    filename : str | Path,
    blade_role : str = "Blade1",
    blade_number : int = "1"
):
    """
    generate rotor blade model xml file for alaska rotor balde submodel (usually to be stored in SubmodelsData folder)
    
    Parameters
    ----------
    filename: 
        filename of rotor blade model xml file
    
    blade_role
        role of alaska submodel (only important for Workbench alaska/Wind) may be "Blade1", "Blade2", "Blade3" for three-bladed rotor
        
    blade_number
        name of rotor blade
    """

    base_dir = Path(__file__).parent
    template_path = base_dir / "rotor_blade_submodel_xml.j2"

    template = Template(template_path.read_text())

    blade_model_xml_file = template.render(
        blade_role=blade_role,
        blade_number=blade_number
    )

    Path(filename).write_text(blade_model_xml_file)
