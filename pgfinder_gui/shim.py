import json
from typing import Dict, List

from pgfinder import matching, pgio, validation
from pgfinder_gui.internal import (
    MASS_LIB_DIR,
    ms_upload_reader,
    theo_masses_upload_reader,
)


def mass_library_index() -> Dict:
    return json.load(open(MASS_LIB_DIR / "index.json"))


def allowed_modifications() -> List:
    return validation.allowed_modifications()


def run_analysis():
    from pyio import (
        cleanupWindow,
        enabledModifications,
        massLibrary,
        msData,
        ppmTolerance,
    )

    theo_masses = theo_masses_upload_reader(massLibrary.to_py())

    def analyze(virt_file):
        ms_data = ms_upload_reader(virt_file)
        matched = matching.data_analysis(ms_data, theo_masses, cleanupWindow, enabledModifications, ppmTolerance)
        return pgio.dataframe_to_csv_metadata(matched, wide=True)

    return {f["name"]: analyze(f) for f in msData.to_py()}
