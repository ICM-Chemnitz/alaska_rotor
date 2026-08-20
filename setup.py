from setuptools import setup

setup(
   use_scm_version=True,
   setup_requires=['setuptools_scm'],
   name='alaska_rotor',
   author='Carsten Schubert',
   author_email='c.schubert@icm-chemnitz.de',
   packages=['alaska_rotor'],
   include_package_data=True,
   package_data={
        "alaska_rotor": [
            "rotor_blade_model.j2",
            "rotor_blade_submodel_xml.j2",
            "PyRotor.zip",
        ],
   },   
   url='https://github.com/ICM-Chemnitz/alaska_rotor',
   license='CC-BY-4.0 License',
   description='Alaska Rotor Python Package',
   long_description=open('README.md').read(),
   install_requires=['jinja2','alaska_io'],
)