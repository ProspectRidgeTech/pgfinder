"""Fixtures for various tests."""
import datetime
from pathlib import Path
import pytest
import pandas as pd

import pgfinder.pgio as pgio
import pgfinder.validation as validation

DATA_DIR = Path("tests/resources/data")


# test_matching.py fixtures
@pytest.fixture
def raw_data_filename():
    return str(DATA_DIR / "maxquant_test_data.txt")


@pytest.fixture
def raw_data_no_match_filename():
    return str(DATA_DIR / "maxquant_test_data_no_match.txt")


@pytest.fixture
def theo_masses_filename():
    return str(DATA_DIR / "masses" / "e_coli_monomer_masses.csv")


@pytest.fixture
def raw_data(raw_data_filename):
    my_raw_data = pgio.ms_file_reader(raw_data_filename)
    validation.validate_raw_data_df(my_raw_data)
    return my_raw_data


@pytest.fixture
def raw_data_no_match(raw_data_no_match_filename):
    my_raw_data_no_match = pgio.ms_file_reader(raw_data_no_match_filename)
    validation.validate_raw_data_df(my_raw_data_no_match)
    return my_raw_data_no_match


@pytest.fixture
def theo_masses(theo_masses_filename):
    my_theo_masses = pgio.theo_masses_reader(theo_masses_filename)
    validation.validate_theo_masses_df(my_theo_masses)
    return my_theo_masses


@pytest.fixture
def ipywidgets_upload_output(ftrs_file_name):
    return {
        "name": "ftrs_test_data.ftrs",
        "type": "",
        "size": 14274560,
        "content": open(ftrs_file_name, "rb").read(),
        "last_modified": datetime.datetime(2022, 2, 2, 11, 6, 9, 951000, tzinfo=datetime.timezone.utc),
    }


@pytest.fixture
def ipywidgets_upload_output_theo(theo_masses_file_name):
    return {
        "name": "e_coli_monomer_masses.csv",
        "type": "text/csv",
        "size": 4975,
        "content": open(theo_masses_file_name, "rb").read(),
        "last_modified": datetime.datetime(2022, 3, 13, 19, 47, 12, 102000, tzinfo=datetime.timezone.utc),
    }


@pytest.fixture
def ppm():
    return 10


@pytest.fixture
def obs_theoretical_molecular_weights() -> pd.DataFrame:
    """Provides a simple list of theoretical and observed molecular weights for testing calculate_delta_ppm()."""
    return pd.DataFrame({"mwMonoisotopic": [10, 20, 300], "theo_mwMonoisotopic": [9, "15, 21", "298, 300, 301"]})


# test_regression.py fixtures
@pytest.fixture
def theo_masses_file_name():
    #    return "data/masses/e_coli_monomer_masses.csv"
    return str(DATA_DIR / "masses" / "e_coli_monomer_masses.csv")


@pytest.fixture
def theo_masses_df(theo_masses_file_name):
    return pgio.theo_masses_reader(theo_masses_file_name)


@pytest.fixture
def mod_test():
    """Modifications used in regression testing."""
    return [
        "Sodium",
        "Potassium",
        "Anh",
        "DeAc",
        "DeAc_Anh",
        "Nude",
        "Decay",
        "Amidation",
        "Amidase",
        "Double_Anh",
        "multimers_Glyco",
    ]


@pytest.fixture
def mq_file_name():
    return str(DATA_DIR / "maxquant_test_data.txt")


@pytest.fixture
def mq_test_df(mq_file_name):
    return pgio.ms_file_reader(mq_file_name)


@pytest.fixture
def ftrs_file_name():
    return str(DATA_DIR / "ftrs_test_data.ftrs")


@pytest.fixture
def ftrs_test_df(ftrs_file_name):
    return pgio.ms_file_reader(ftrs_file_name)


@pytest.fixture
def sample_df() -> pd.DataFrame:
    """Return a dummy data frame for tests."""
    return pd.DataFrame({"obs": [5645.35435454, 1, 879546.3924093], "exp": [3954.49849514, 2, 879546.8974916]})


@pytest.fixture
def target_df(sample_df: pd.DataFrame) -> pd.DataFrame:
    """Return a target data frame for tests."""
    DELTA_DF = pd.DataFrame({"diff_ppm": [427577.82345296827, -500000.0, -0.5742528357381609]})
    return pd.concat([sample_df, DELTA_DF], axis=1)
