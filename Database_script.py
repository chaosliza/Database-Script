import json
import os
class XYZDatabase:

    # Initializes the database with the given JSON file
    def __init__(self, db_file):
        self.db_file = db_file
        if os.path.exists(db_file):
            with open(db_file, 'r') as file:
                self.data = json.load(file)
        else:
            self.data = {"molecules": []}

    # Saves the database to a JSON file
    def save(self):
        with open(self.db_file, 'w') as file:
            json.dump(self.data, file, indent=4)

    # Check if molecule id already exists in database
    def molecule_id_exists(self, mol_id):
        return any(molecule["id"] == mol_id for molecule in self.data["molecules"])
    
    # Check if conformer id already exists for specific molecule
    def conformer_id_exists(self, mol_id, conf_id):
        for molecule in self.data["molecules"]:
            if molecule["id"] == mol_id:
                return any(conformer["id"] == conf_id for conformer in molecule["conformers"])
        return False
    
    # Adds molecule with name, id and functional groups to database
    def add_molecule(self, name, mol_id, functional_groups):
        if self.molecule_id_exists(mol_id):
            raise ValueError(f"Molecule ID '{mol_id}' already exists")
        functional_groups = ', '.join(sorted(functional_groups.split(', ')))
        molecule = {
            "name": name,
            "id": mol_id,
            "functional_groups" : functional_groups,
            "conformers": []
        }
        self.data["molecules"].append(molecule)

    # Adds conformers to molecule in database
    def add_conformer(self, mol_id, conf_id, energy, xyz_content):
        if not self.molecule_id_exists(mol_id):
            raise ValueError(f"Molecule ID '{mol_id}' not found")
        if self.conformer_id_exists(mol_id, conf_id):
            raise ValueError(f"Conformer ID '{conf_id}' already exists for molecule '{mol_id}'")
        for molecule in self.data["molecules"]:
            if molecule["id"] == mol_id:
                conformer = {
                    "id": conf_id,
                    "energy": energy,
                    "xyz": xyz_content
                }
                molecule["conformers"].append(conformer)
                return
            
    # Delete molecule from database by id
    def delete_molecule(self, mol_id, save=True):
        for i, molecule in enumerate(self.data["molecules"]):
            if molecule["id"] == mol_id:
                del self.data["molecules"][i]
                if save:
                    self.save()
                return
        print(f'Molecule with ID "{mol_id}" not found in Database')

    # Get all data from molecule by id
    def get_molecule(self, mol_id):
        for molecule in self.data["molecules"]:
            if molecule["id"] == mol_id:
                return molecule
        raise ValueError(f"Molecule ID '{mol_id}' not found") 
    
    # Extract xyz file of a specific molecules (by id) from database
    def create_trajectory_xyz(self, mol_id, output_file_name):
        molecule = self.get_molecule(mol_id)
        if molecule is None:
            print(f'Molecule with ID "{mol_id}" not found in Database')
            return
        output_file_name = molecule['name'].replace(' ', '').replace("-","_") + '.xyz'
        with open(output_file_name, 'w') as file:
            for conformer in molecule["conformers"]:
                file.write(conformer["xyz"])

    # Delete conformer from molecule by id
    def delete_conformer(self, mol_id, conf_id, save=True):
        molecule = self.get_molecule(mol_id)
        molecule["conformers"] = [c for c in molecule["conformers"] if c["id"] != conf_id]
        if save:
            self.save()

    # Import an xyz file of molecule with conformers to database
    def import_xyz_file(self, file_path, mol_name, mol_id, functional_groups, base_energy=0.0):
        with open(file_path, 'r') as file:
            lines = file.readlines()
        if not lines:
            raise ValueError("The file is empty")
        self.add_molecule(mol_name, mol_id, functional_groups)
        i = 0
        conf_counter = 1
        while i < len(lines):
            try:
                atom_count = int(lines[i].strip())
            except ValueError:
                raise ValueError("Invalid XYZ file format")
            comment_line = lines[i + 1].strip()
            energy = self.extract_energy_from_comment(comment_line, base_energy)
            xyz_content = "".join(lines[i:i + atom_count + 2])
            conf_id = f"conf{conf_counter}"  
            self.add_conformer(mol_id, conf_id, energy, xyz_content)
            i += atom_count + 2
            conf_counter += 1

    # Extract energy from comment line of xyz file
    def extract_energy_from_comment(self, comment, base_energy):
        # Custom logic to extract energy from the comment line
        # For this example, let's assume the comment line contains "energy=<value>"
        if "energy=" in comment:
            try:
                energy_str = comment.split("energy=")[-1].strip()
                return float(energy_str)
            except ValueError:
                pass
        return base_energy
    
    #Update molecule name in database by id
    def update_molecule_name(self, mol_id, new_name):
        for molecule in self.data["molecules"]:
            if molecule["id"] == mol_id:
                molecule["name"] = new_name
                self.save()
                return
        raise ValueError(f"Molecule ID '{mol_id}' not found")
    
    # Update molecule id in database
    def update_molecule_id(self, old_id, new_id):
        for molecule in self.data["molecules"]:
            if molecule["id"] == old_id:
                molecule["id"] = new_id
                self.save()
                return
        raise ValueError(f"Molecule ID '{old_id}' not found")
    
    # Search for molecules by functional group in database
    def search_by_functional_group(self, functional_group):
        return [molecule for molecule in self.data["molecules"] if functional_group in molecule["functional_groups"]]
    
    # Replaces all the functional groups of a specific molecule (by id) by new ones 
    def update_functional_groups(self, mol_id, new_functional_groups):
        for molecule in self.data["molecules"]:
            if molecule["id"] == mol_id:
                molecule["functional_groups"] = new_functional_groups
                molecule["functional_groups"] = ', '.join(sorted(molecule["functional_groups"].split(', ')))
                self.save()
                return
        raise ValueError(f"Molecule ID '{mol_id}' not found")
    
    # Add new functional groups to the existing ones of a specific molecule (by id)
    def add_functional_groups(self, mol_id, new_functional_groups):
        for molecule in self.data["molecules"]:
            if molecule["id"] == mol_id:
                molecule["functional_groups"] += ", " + new_functional_groups
                molecule["functional_groups"] = ', '.join(sorted(molecule["functional_groups"].split(', ')))
                self.save()
                return
        raise ValueError(f"Molecule ID '{mol_id}' not found")
    
    # Delete functional group from molecule by id
    def delete_functional_group(self, mol_id, functional_group, save=True):
        for molecule in self.data["molecules"]:
            if molecule["id"] == mol_id:
                functional_groups = molecule["functional_groups"].split(", ")
                if functional_group in functional_groups:
                    functional_groups.remove(functional_group)
                    molecule["functional_groups"] = ", ".join(functional_groups).rstrip(", ")
                    if save:
                        self.save()
                else:
                    print(f'Functional group "{functional_group}" not associated with this molecule')
                return
        raise ValueError(f"Molecule ID '{mol_id}' not found")
    
    # Extract all molecules that have a specific functional group to an xyz file
    def create_trajectory_xyz_for_functional_group(self, functional_group):
        output_file_name = functional_group + ".xyz"
        with open(output_file_name, 'w') as file:
            for molecule in self.data["molecules"]:
                if functional_group in molecule["functional_groups"]:
                    for conformer in molecule["conformers"]:
                        lines = conformer["xyz"].split("\n")
                        file.write(lines[0] + "\n")
                        file.write("Molecule: " + molecule["name"] + "\n")
                        file.write("\n".join(lines[2:]))

    # Get list of all molecules from database
    def get_all_molecules(self):
        sorted_molecules = sorted(self.data["molecules"], key=lambda x: x['name'])
        for molecule in sorted_molecules:
            print(f"Name: {molecule['name']}, ID: {molecule['id']}, Functional Groups: {molecule['functional_groups']}")

    # Get list of all functional groups from database
    def get_all_functional_groups(self):
        functional_groups = set()  
        for molecule in self.data["molecules"]:
            groups = molecule["functional_groups"].split(", ")  
            functional_groups.update(groups)
        return sorted(functional_groups)
    
    
# # Adding calculated molecules to db
# db = XYZDatabase("moleculedatabase.json")
# # Import an XYZ file
# try:
#     db.import_xyz_file("/home/lisa/src/Bachelorarbeit/data/Database/calculated_data/Cystine.xyz", "Cystine", "OC(=O)[C@H](CS)[NH2+]([S-])=S", "alcohol, aldehyde, alkane, amine, amino acid, carbonyl, disulfide")
#     db.import_xyz_file("/home/lisa/src/Bachelorarbeit/data/Database/calculated_data/Cytosine.xyz", "Cytosine", "NC1=NC(=O)NC=C1", "N-heterocycle, alkane, alkene, amine, aromatic, carbonyl")
#     db.import_xyz_file("/home/lisa/src/Bachelorarbeit/data/Database/calculated_data/Darginine.xyz", "D-Arginine", "N[C@H](CCCNC(N)=N)C(O)=O", "alcohol, aldehyde, alkane, amine, amino acid, carbonyl, imine")
#     db.import_xyz_file("/home/lisa/src/Bachelorarbeit/data/Database/calculated_data/TPPO.xyz", "Triphenylphosphine oxide", "O=[P](c1ccccc1)(c2ccccc2)c3ccccc3", "alkane, alkene, aromatic, cycle, phosphorus, phosphane, oxide")
#     db.import_xyz_file("/home/lisa/src/Bachelorarbeit/data/Database/calculated_data/Dfructose.xyz", "D-Fructose", "OC[C@@H](O)[C@@H](O)[C@H](O)C(=O)CO", "alcohol, aldehyde, alkane, carbonyl")
#     db.import_xyz_file("/home/lisa/src/Bachelorarbeit/data/Database/calculated_data/diethylsulfide.xyz", "Diethylsulfide", "CCSCC", "alkane, sulfide, thioether")
#     db.import_xyz_file("/home/lisa/src/Bachelorarbeit/data/Database/calculated_data/Dglutamine.xyz", "D-Glutamine", "N[C@H](CCC(N)=O)C(O)=O", "alcohol, aldehyde, alkane, amine, amino acid, carbonyl")
#     db.import_xyz_file("/home/lisa/src/Bachelorarbeit/data/Database/calculated_data/Dlysine.xyz", "D-Lysine", "NCCCC[C@@H](N)C(O)=O", "alcohol, aldehyde, alkane, amine, amino acid, carbonyl")
#     db.import_xyz_file("/home/lisa/src/Bachelorarbeit/data/Database/calculated_data/Dproline.xyz", "D-Proline", "OC(=O)[C@H]1CCCN1", "N-heterocycle, alcohol, aldehyde, alkane, amine, amino acid, carbonyl, cycle")
#     db.import_xyz_file("/home/lisa/src/Bachelorarbeit/data/Database/calculated_data/Dtryptophane.xyz", "D-Tryptophane", "N[C@H](Cc1c[nH]c2ccccc12)C(O)=O", "N-heterocycle, alcohol, aldehyde, alkane, amine, amino acid, aromatic, carbonyl, cycle")
#     db.import_xyz_file("/home/lisa/src/Bachelorarbeit/data/Database/calculated_data/methanol.xyz", "Methanol", "CO", "alcohol")
#     print("Read everything, now lets write...")
#     db.db_file = "moleculedatabase.json"
#     db.save()
# except ValueError as e:
#     print(e)  
  
# db = XYZDatabase("moleculedatabase.json")
# all_functional_groups = db.get_all_functional_groups()
# for group in all_functional_groups:
#     print(group)

# db = XYZDatabase('moleculedatabase.json')
# db.add_functional_groups('Cn1cnc2N(C)C(=O)N(C)C(=O)c12', 'cycle')
# db = XYZDatabase("moleculedatabase.json")
# all_molecules = db.get_all_molecules()

# db = XYZDatabase("moleculedatabase.json")
# db.delete_molecule("CO")

db = XYZDatabase("moleculedatabase.json")
group_counts = db.get_functional_group_counts()
print(group_counts)