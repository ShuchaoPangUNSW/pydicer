import json
import logging
import os
from pathlib import Path

import pandas as pd
import SimpleITK as sitk

from pydicer.constants import CONVERTED_DIR_NAME

from pydicer.dataset import functions
from pydicer.utils import read_converted_data, map_structure_name

logger = logging.getLogger(__name__)


class PrepareDataset:
    def __init__(self, working_directory="."):
        self.working_directory = Path(working_directory)

    def add_object_to_dataset(self, dataset_name, data_object_row):
        """Add one data object to a dataset.

        Args:
            dataset_name (str): The name of the dataset to add the object to.
            data_object_row (pd.Series): The DataFrame row of the converted object.
        """

        dataset_dir = self.working_directory.joinpath(dataset_name)

        # Create a copy so that we aren't manuipulating the original entry
        data_object_row = data_object_row.copy()

        object_path = Path(data_object_row.path)
        if object_path.is_absolute():
            data_object_row.path = str(object_path.relative_to(self.working_directory))
            object_path = Path(data_object_row.path)

        object_path = Path(data_object_row.path)
        symlink_path = dataset_dir.joinpath(object_path.relative_to(CONVERTED_DIR_NAME))

        rel_part = os.sep.join(
            [".." for _ in symlink_path.parent.relative_to(self.working_directory).parts]
        )
        src_path = Path(f"{rel_part}{os.sep}{object_path}")

        symlink_path.parent.mkdir(parents=True, exist_ok=True)

        if symlink_path.exists():
            logger.debug("Symlink path already exists: %s", symlink_path)
        else:
            symlink_path.symlink_to(src_path)

        pat_id = data_object_row.patient_id
        pat_dir = dataset_dir.joinpath(pat_id)
        pat_converted_csv = pat_dir.joinpath("converted.csv")
        df_pat = pd.DataFrame([data_object_row])
        if pat_converted_csv.exists():

            col_types = {"patient_id": str, "hashed_uid": str}
            df_converted = pd.read_csv(pat_converted_csv, index_col=0, dtype=col_types)

            # Check if this object already exists in the converted dataframe
            if len(df_converted[df_converted.hashed_uid == data_object_row.hashed_uid]) == 0:
                # If not add it
                df_pat = pd.concat([df_converted, df_pat])
            else:
                # Otherwise just leave the converted data as is
                df_pat = df_converted

        df_pat = df_pat.reset_index(drop=True)
        df_pat.to_csv(pat_dir.joinpath("converted.csv"))

    def prepare_from_dataframe(self, dataset_name, df_prepare):
        """Prepare a dataset from a filtered converted dataframe

        Args:
            dataset_name (str): The name of the dataset to generate
            df_prepare (pd.DataFrame): Filtered Pandas DataFrame containing rows of converted data.
        """

        dataset_dir = self.working_directory.joinpath(dataset_name)
        if dataset_dir.exists():
            logger.warning(
                "Dataset directory already exists. Consider using a different dataset name or "
                "remove the existing directory"
            )

        # Remove the working directory part for when we re-save off the filtered converted csv
        df_prepare.path = df_prepare.path.apply(
            lambda p: str(Path(p).relative_to(self.working_directory))
        )

        # For each data object prepare the data in the dataset directory
        for _, row in df_prepare.iterrows():
            self.add_object_to_dataset(dataset_name, row)

    def prepare(self, dataset_name, preparation_function, patients=None, **kwargs):
        """Calls upon an appropriate preparation function to generate a clean dataset ready for
        use. Additional keyword arguments are passed through to the preparation_function.

        Args:
            dataset_name (str): The name of the dataset to generate
            preparation_function (function|str): the function use for preparation
            patients (list): The list of patient IDs to use for dataset. If None then all patients
                will be considered. Defaults to None.

        Raises:
            AttributeError: Raised if preparation_function is not a function or a string defining
              a known preparation function.
        """

        if isinstance(preparation_function, str):

            preparation_function = getattr(functions, preparation_function)

        if not callable(preparation_function):
            raise AttributeError(
                "preparation_function must be a function or a str defined in pydicer.dataset"
            )

        logger.info("Preparing dataset %s using function: %s", dataset_name, preparation_function)

        # Grab the DataFrame containing all the converted data
        df_converted = read_converted_data(self.working_directory, patients=patients)

        # Send to the prepare function which will return a DataFrame of the data objects to use for
        # the dataset
        df_clean_data = preparation_function(df_converted, **kwargs)

        self.prepare_from_dataframe(dataset_name, df_clean_data)


class StructureSet(dict):
    def __init__(self, structure_set_row, structure_mapping=None):

        if not structure_set_row.modality == "RTSTRUCT":
            raise AttributeError("structure_set_row modality must be of RTSTRUCT")

        self.structure_set_path = Path(structure_set_row.path)

        self.structure_names = [
            s.name.replace(".nii.gz", "") for s in self.structure_set_path.glob("*.nii.gz")
        ]

        if structure_mapping is not None:
            self.structure_names = list(structure_mapping.keys())

        self.structure_mapping = structure_mapping
        self.cache = {}

    def __getitem__(self, item):

        if self.structure_mapping is not None:
            item = map_structure_name(item, self.structure_mapping)

        if item not in self.structure_names:
            raise KeyError(f"Structure name {item} not found in structure set.")

        if item in self.cache:
            return self.cache[item]

        structure_path = self.structure_set_path.joinpath(f"{item}.nii.gz")

        result = sitk.ReadImage(str(structure_path))

        self.cache[item] = result
        return result

    def keys(self):
        return self.structure_names

    def create_mapping_json(self, mapping_dict, level="project"):
        """_summary_

        Args:
            mapping_dict (_type_): _description_
            level (str, optional): _description_. Defaults to "project".
        """
        final_map = {}
        final_map["structures"] = mapping_dict

        if level == "project":
            path = self.structure_set_path.parent.parent.parent.parent.joinpath(".pydicer")
        elif level == "patient":
            path = self.structure_set_path.parent.parent
        elif level == "current_structure_set":
            path = self.structure_set_path
        else:
            raise ValueError(
                "level must be one of 'project', 'patient' or 'current_structure_set'."
            )

        # Create the mapping file
        with open(
            path.joinpath("structures_map.json"), "w", encoding="utf8"
        ) as structures_map_file:
            json.dump(final_map, structures_map_file, ensure_ascii=False, indent=4)
