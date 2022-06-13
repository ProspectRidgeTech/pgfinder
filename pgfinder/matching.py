"""Matching functions"""
import re
import logging
from decimal import *

import numpy as np
import pandas as pd

from pgfinder.logs.logs import LOGGER_NAME

LOGGER = logging.getLogger(LOGGER_NAME)


def calc_ppm_tolerance(mw: float, ppm_tol: int = 10) -> float:
    """Calculates ppm tolerance value

    Parameters
    ----------
    mw: float
        ?
    ppm_tol: int
        PPM tolerance

    Returns
    -------
    float
        ?
    """
    return (mw * ppm_tol) / 1000000


def filtered_theo(ftrs_df: pd.DataFrame, theo_list: pd.DataFrame, user_ppm: int) -> pd.DataFrame:
    """Generate list of observed structures from theoretical masses dataframe to reduce search space.

    Parameters
    ----------
    ftrs_df: pd.DataFrame
        Features dataframe.
    theo_list: pd.DataFrame
        Theoretical dataframe.
    user_ppm: int

    Returns
    -------
    pd.DataFrame
        ?
    """
    # Match theoretical structures to raw data to generate a list of observed structures
    matched_df = matching(ftrs_df, theo_list, user_ppm)

    # Create dataframe containing only theo_mwMonoisotopic & inferredStructure columsn from matched_df
    filtered_df = matched_df.loc[:, "theo_mwMonoisotopic":"inferredStructure"]

    # Drop all rows with NaN values in the theo_mwMonoisotopic column
    filtered_df.dropna(subset=["theo_mwMonoisotopic"], inplace=True)

    # Expand dataframe so each inferred structure has its own row and corresponding theo_mwMonoisotopic value
    cols = ["theo_mwMonoisotopic", "inferredStructure"]
    # FIXME : Better to use try: ... except:
    if filtered_df.empty == True:
        raise ValueError(
            "The error messages above indicate that NO MATCHES WERE FOUND for this search. Please check your database or increase mass tolerance."
        )
    exploded_df = (
        pd.concat([filtered_df[col].str.split(",", expand=True) for col in cols], axis=1, keys=cols)
        .stack()
        .reset_index(level=1, drop=True)
    )
    exploded_df.drop_duplicates(subset="inferredStructure", keep="first", inplace=True)

    exploded_df.rename(
        columns={"theo_mwMonoisotopic": "Monoisotopicmass", "inferredStructure": "Structure"}, inplace=True
    )

    return exploded_df


def multimer_builder(theo_list, multimer_type: int = 0):
    """Generate multimers (dimers & trimers) from observed monomers

    Parameters
    ----------
    theo_list:
        ??? (is it a list or dataframe, that a pd.DataFrame is returned suggests it should be the later?)
    multimer_type: int

    Returns
    -------
    pd.DataFrame
        ???
    """

    theo_mw = []
    theo_struct = []
    # Builder sub function - calculates multimer mass and name

    # FIXME : No need to use nested functions
    def builder(name, mass, mult_num: int):
        for idx, row in theo_list.iterrows():
            if (
                len(row.Structure[: len(row.Structure) - 2]) > 2
            ):  # Prevent dimer creation using just gm (input format is XX|n) X = letters n = number
                mw = row.Monoisotopicmass
                acceptor = row.Structure[: len(row.Structure) - 2]
                donor = name
                donor_mw = mass
                theo_mw.append(Decimal(mw) + donor_mw + Decimal("-18.0106"))
                theo_struct.append(acceptor + "-" + donor + "|" + str(mult_num))

    # Calls builder subfunction with different arguements based on multimer type selected

    # Calculates multimers based on peptide bond through side chain

    if multimer_type == 0:
        builder("gm-AEJA", Decimal("941.4075"), 2)
        builder("gm-AEJ", Decimal("870.3704"), 2)
        builder("gm-AEJ-gm-AEJ", Decimal("1722.7302"), 3)
        builder("gm-AEJ-gm-AEJA", Decimal("1793.7673"), 3)
        builder("gm-AEJA-gm-AEJA", Decimal("1864.8044"), 3)

    # Calculates multimers based on glycosidic bond through dissachrides & peptide bonds through side chains
    elif multimer_type == 1:
        builder("gm-AE", Decimal("698.2858"), 2)
        builder("gm-AEJA", Decimal("941.4075"), 2)
        builder("gm-AEJ", Decimal("870.3704"), 2)
        builder("gm-AEJ-gm-AEJ", Decimal("1722.7302"), 3)
        builder("gm-AEJ-gm-AEJA", Decimal("1793.7673"), 3)
        builder("gm-AEJA-gm-AEJA", Decimal("1864.8044"), 3)

        builder("gm-AEJA_(Glyco)", Decimal("939.3919"), 2)
        builder("gm-AEJ_(Glyco)", Decimal("868.3548"), 2)
        builder("gm-AEJ-gm-AEJ_(Glyco)", Decimal("1720.7146"), 3)
        builder("gm-AEJ-gm-AEJA_(Glyco)", Decimal("1791.7517"), 3)
        builder("gm-AEJA-gm-AEJA_(Glyco)", Decimal("1862.7888"), 3)

    # Calculates multimers based on Lactyl peptides (peptide bond via side chain but no dissachrides on muropeptides)
    elif multimer_type == 2:
        builder("Lac-AEJA", Decimal("533.2333"), 2)
        builder("Lac-AEJ", Decimal("462.1962"), 2)
        builder("Lac-AEJ-Lac-AEJ", Decimal("906.3818"), 3)
        builder("Lac-AEJ-Lac-AEJA", Decimal("977.4189"), 3)
        builder("Lac-AEJA-Lac-AEJA", Decimal("1048.4560"), 3)

    # converts lists to dataframe
    multimer_df = pd.DataFrame(list(zip(theo_mw, theo_struct)), columns=["Monoisotopicmass", "Structure"])

    return multimer_df


def modification_generator(filtered_theo_df: pd.DataFrame, mod_type: str) -> pd.DataFrame:
    """Generates modified muropeptides (calculates new mass and add modification tag to structure name)

    Parameters
    ----------
    filtered_theo_df : pd.DataFrame
        Pandas DataFrame of theoretical masses that have been filtered.
    mod_type : str
        Modification type ???.

    Returns
    -------
    pd.DataFrame
        Pandas DataFrame of ???
    """

    # FIXME : Replace with data structure such as dictionary

    if mod_type == "Anh":
        mod_mass = Decimal("-20.0262")
    elif mod_type == "Double_Anh":
        mod_mass = Decimal("-40.0524")
    elif mod_type == "DeAc":
        mod_mass = Decimal("-42.0105")
    elif mod_type == "O-Acetylated":
        mod_mass = Decimal("42.0105")
    elif mod_type == "DeAc_Anh":
        mod_mass = Decimal("-62.0368")
    elif mod_type == "Decay":
        mod_mass = Decimal("-203.0793")
    elif mod_type == "Sodium":
        mod_mass = Decimal("21.9819")
        mod_name = "Na+"
    elif mod_type == "Potassium":
        mod_mass = Decimal("37.9559")
        mod_name = "K+"
    elif mod_type == "Nude":
        mod_mass = Decimal("478.1799")
        mod_name = "gm-"
    elif mod_type == "Amidated":
        mod_mass = Decimal("-0.9840")
        mod_name = "Amidated"
    elif mod_type == "Amidase Product":
        mod_mass = Decimal("-480.1955")
        mod_name = "(Amidase Product)"
    elif mod_type == "Lactyl":
        mod_mass = Decimal("-408.1744")
        mod_name = "(Lactyl)"

    obs_theo_muropeptides_df = filtered_theo_df.copy()
    # Calculate new mass of modified structure
    obs_theo_muropeptides_df["Monoisotopicmass"] = obs_theo_muropeptides_df["Monoisotopicmass"].map(
        lambda Monoisotopicmass: Decimal(Monoisotopicmass) + mod_mass
    )

    # add modification tags to structure name
    if mod_type == "Decay":
        obs_theo_muropeptides_df["Structure"] = obs_theo_muropeptides_df["Structure"].map(
            lambda Structure: Structure[1 : len(Structure)]
        )
    elif mod_type == "Sodium" or mod_type == "Potassium":
        obs_theo_muropeptides_df["Structure"] = obs_theo_muropeptides_df["Structure"].map(
            lambda Structure: mod_name + " " + Structure
        )
    elif mod_type == "Nude":
        obs_theo_muropeptides_df["Structure"] = obs_theo_muropeptides_df["Structure"].map(
            lambda Structure: mod_name + Structure
        )
    else:
        obs_theo_muropeptides_df["Structure"] = obs_theo_muropeptides_df["Structure"].map(
            lambda Structure: Structure[: len(Structure) - 2]
            + " "
            + "("
            + mod_type
            + ")"
            + " "
            + Structure[len(Structure) - 2 : len(Structure)]
        )
    return obs_theo_muropeptides_df


def matching(ftrs_df: pd.DataFrame, matching_df: pd.DataFrame, set_ppm: int):
    """Match theoretical masses to observed masses within ppm tolerance.

    Parameters
    ----------
    ftrs_df: pd.DataFrame
        Features DataFrame
    matching_df: pd.DataFrame
        Matching DataFrame
    set_ppm: int

    Returns
    -------
    pd.DataFrame
        Dataframe of matches.
    """
    raw_data = ftrs_df.copy()
    # Data validation
    if ("Monoisotopicmass" not in matching_df.columns) | ("Structure" not in matching_df.columns):
        print(
            'Header of csv files must have column named "Monoisotopic mass" and another column named "Structure"!!!  Make note of capitalized letters and spacing!!!!'
        )

    # Generates dataframe with matched structures
    for x, row in raw_data.iterrows():
        # Observed monoisotopic mass
        mw = row.mwMonoisotopic
        # ppm tolerance value
        t_tol = calc_ppm_tolerance(mw, set_ppm)
        # create dataframe with values from matching_df within tolerance to observed monoisotopic mass
        t_df = matching_df[
            (matching_df["Monoisotopicmass"] >= mw - t_tol) & (matching_df["Monoisotopicmass"] <= mw + t_tol)
        ]

        # Populate inferred structure and theo_mwMonoisotopic columns with matched values
        if not t_df.empty:
            raw_data.loc[x, "inferredStructure"] = ",".join(t_df.Structure.values)
            raw_data.loc[x, "theo_mwMonoisotopic"] = ",".join(map(str, t_df.Monoisotopicmass.values))

    return raw_data


def clean_up(ftrs_df: pd.DataFrame, mass_to_clean: Decimal, time_delta: float) -> pd.DataFrame:
    """Clean up a DataFrame.

    Parameters
    ----------
    ftrs_df: pd.DataFrame
        Features dataframe?
    matching_df: pd.DataFrame
        ?
    set_ppm: int
        ?

    Returns
    -------
    pd.DataFrame:
        ?
    """
    # Mass values for adducts
    sodiated = Decimal("21.9819")
    potassated = Decimal("37.9559")
    decay = Decimal("203.0793")

    # Selector substrings for generating parent and adduct dataframes
    if mass_to_clean == sodiated:
        parent = "^gm|^m|^Lac"
        target = "^Na+"
    elif mass_to_clean == potassated:
        parent = "^gm|^m|^Lac"
        target = "^K+"
    elif mass_to_clean == decay:
        parent = "^gm"
        target = "^m"

    # Generate parent dataframe - contains parents
    parent_muropeptide_df = ftrs_df[ftrs_df["inferredStructure"].str.contains(parent, na=False)]

    # Generate adduct dataframe - contains adducts
    adducted_muropeptide_df = ftrs_df[ftrs_df["inferredStructure"].str.contains(target, na=False)]

    # Generate copy of rawdata dataframe
    consolidated_decay_df = ftrs_df.copy()

    # Status updates (prints to console)
    if parent_muropeptide_df.empty:
        LOGGER.info(f"No {parent}  muropeptides found")
    if adducted_muropeptide_df.empty:
        LOGGER.info(f"No {target} found")
    elif mass_to_clean == sodiated:
        LOGGER.info(f"Processing {adducted_muropeptide_df.size} Sodium Adducts")
    elif mass_to_clean == potassated:
        LOGGER.info(f"Processing {adducted_muropeptide_df.size} potassium adducts")
    elif mass_to_clean == decay:
        LOGGER.info(f"Processing {adducted_muropeptide_df.size} in source decay products")

    # Consolidate adduct intensity with parent ions intensity
    for y, row in parent_muropeptide_df.iterrows():
        # Get retention time value from row
        rt = row.rt
        # Get theoretical monoisotopic mass value from row as list of values
        intact_mw = list(str(row.theo_mwMonoisotopic).split(","))

        # Work out rt window
        upper_lim_rt = rt + time_delta
        lower_lim_rt = rt - time_delta

        # Get all adduct enteries within rt window
        ins_constrained_df = adducted_muropeptide_df[
            adducted_muropeptide_df["rt"].between(lower_lim_rt, upper_lim_rt, inclusive="both")
        ]

        if not ins_constrained_df.empty:

            for z, ins_row in ins_constrained_df.iterrows():
                ins_mw = list(str(ins_row.theo_mwMonoisotopic).split(","))

                # Compare parent masses to adduct masses
                for mass in intact_mw:
                    for mass_2 in ins_mw:

                        mass_delta = abs(
                            Decimal(mass).quantize(Decimal("0.00001")) - Decimal(mass_2).quantize(Decimal("0.00001"))
                        )

                        # Consolidate intensities
                        if mass_delta == mass_to_clean:

                            consolidated_decay_df.sort_values("ID", inplace=True, ascending=True)

                            insDecay_intensity = ins_row.maxIntensity
                            parent_intensity = row.maxIntensity
                            consolidated_intensity = insDecay_intensity + parent_intensity

                            ID = row.ID
                            drop_ID = ins_row.ID

                            idx = consolidated_decay_df.loc[consolidated_decay_df["ID"] == ID].index[0]
                            try:
                                drop_idx = consolidated_decay_df.loc[consolidated_decay_df["ID"] == drop_ID].index[0]
                                consolidated_decay_df.at[idx, "maxIntensity"] = consolidated_intensity
                                consolidated_decay_df.drop(drop_idx, inplace=True)
                            except IndexError:
                                LOGGER.info(f"Already removed : {drop_idx}")

    return consolidated_decay_df


def data_analysis(
    raw_data_df: pd.DataFrame, theo_masses_df: pd.DataFrame, rt_window: float, enabled_mod_list: list, user_ppm=int
) -> pd.DataFrame:
    """Perform analysis.

    Parameters
    ----------
    raw_data_df : pd.DataFrame
        User data as Pandas DataFrame.
    theo_masses_df : pd.DataFrame
        Theoretical masses as Pandas DataFrame.
    rt_window : float
        ?
    enabled_mod_list : list
        List of modules to enable.
    user_ppm : int
        ?

    Returns
    -------
    pd.DataFrame
    """
    sugar = Decimal("203.0793")
    sodium = Decimal("21.9819")
    potassium = Decimal("37.9559")
    # retention time window to look in for in source decay products (rt of parent ion plus or minus time_delta)
    time_delta_window = rt_window

    # FIXME : Should these be .copy() since Pandas DataFrames will be modified by reference I think and so any change to
    # theo or ff cascades back to theo_masses_df and raw_data_df automatically (unless that is the intention)?
    theo = theo_masses_df
    ff = raw_data_df

    LOGGER.info("Filtering theoretical masses by observed masses")
    obs_monomers_df = filtered_theo(ff, theo, user_ppm)

    if "Multimers" in enabled_mod_list:
        LOGGER.info("Building multimers from obs muropeptides")
        theo_multimers_df = multimer_builder(obs_monomers_df)
        LOGGER.info("Filtering theoretical multimers by observed")
        obs_multimers_df = filtered_theo(ff, theo_multimers_df, user_ppm)
    elif "multimers_Glyco" in enabled_mod_list:
        LOGGER.info("Building multimers from obs muropeptides")
        theo_multimers_df = multimer_builder(obs_monomers_df, 1)
        LOGGER.info("Filtering theoretical multimers by observed")
        obs_multimers_df = filtered_theo(ff, theo_multimers_df, user_ppm)
    elif "Multimers_Lac" in enabled_mod_list:
        LOGGER.info("Building multimers_Lac from obs muropeptides")
        theo_multimers_df = multimer_builder(obs_monomers_df, 2)
        LOGGER.info("Filtering theoretical multimers by observed")
        obs_multimers_df = filtered_theo(ff, theo_multimers_df, user_ppm)
    else:
        obs_multimers_df = pd.DataFrame()

    LOGGER.info("Building custom search file")
    obs_frames = [obs_monomers_df, obs_multimers_df]
    obs_theo_df = pd.concat(obs_frames).reset_index(drop=True)

    LOGGER.info("Generating variants")

    if "Sodium" in enabled_mod_list:
        adducts_sodium_df = modification_generator(obs_theo_df, "Sodium")
    else:
        adducts_sodium_df = pd.DataFrame()

    if "Potassium" in enabled_mod_list:
        adducts_potassium_df = modification_generator(obs_theo_df, "Potassium")
    else:
        adducts_potassium_df = pd.DataFrame()

    if "Anh" in enabled_mod_list:
        anhydro_df = modification_generator(obs_theo_df, "Anh")
    else:
        anhydro_df = pd.DataFrame()

    if "DeAc" in enabled_mod_list:
        deacetyl_df = modification_generator(obs_theo_df, "DeAc")
    else:
        deacetyl_df = pd.DataFrame()

    if "DeAc_Anh" in enabled_mod_list:
        deac_anhy_df = modification_generator(obs_theo_df, "DeAc_Anh")
    else:
        deac_anhy_df = pd.DataFrame()
    if "O-Acetylated" in enabled_mod_list:
        oacetyl_df = modification_generator(obs_theo_df, "O-Acetylated")
    else:
        oacetyl_df = pd.DataFrame()

    if "Nude" in enabled_mod_list:
        nude_df = modification_generator(obs_theo_df, "Nude")
    else:
        nude_df = pd.DataFrame()

    if "Decay" in enabled_mod_list:
        decay_df = modification_generator(obs_theo_df, "Decay")
    else:
        decay_df = pd.DataFrame()

    if "Amidation" in enabled_mod_list:
        ami_df = modification_generator(obs_theo_df, "Amidated")
    else:
        ami_df = pd.DataFrame()

    if "Amidase" in enabled_mod_list:
        deglyco_df = modification_generator(obs_theo_df, "Amidase Product")
    else:
        deglyco_df = pd.DataFrame()

    if "Double_Anh" in enabled_mod_list:
        double_Anhydro_df = modification_generator(obs_theo_df, "Double_Anh")

    else:
        double_Anhydro_df = pd.DataFrame()

    master_frame = [
        obs_theo_df,
        adducts_potassium_df,
        adducts_sodium_df,
        anhydro_df,
        deac_anhy_df,
        deacetyl_df,
        oacetyl_df,
        decay_df,
        nude_df,
        ami_df,
        deglyco_df,
        double_Anhydro_df,
    ]
    master_list = pd.concat(master_frame)
    master_list = master_list.astype({"Monoisotopicmass": float})
    LOGGER.info("Matching")
    matched_data_df = matching(ff, master_list, user_ppm)
    LOGGER.info("Cleaning data")
    cleaned_df = clean_up(matched_data_df, sodium, time_delta_window)
    cleaned_df = clean_up(cleaned_df, potassium, time_delta_window)
    cleaned_data_df = clean_up(cleaned_df, sugar, time_delta_window)

    cleaned_data_df.sort_values("inferredStructure", inplace=True, ascending=True)

    # set metadata
    cleaned_data_df.attrs["file"] = raw_data_df.attrs["file"]
    cleaned_data_df.attrs["masses_file"] = theo_masses_df.attrs["file"]
    cleaned_data_df.attrs["rt_window"] = rt_window
    cleaned_data_df.attrs["modifications"] = enabled_mod_list
    cleaned_data_df.attrs["ppm"] = user_ppm

    return cleaned_data_df


def calculate_delta_ppm(
    matched_df: pd.DataFrame,
    theoretical_col: str = "theo_mwMonoisotopic",
    observed_col: str = "mwMonoisotopic",
    split_on: str = ",",
) -> pd.DataFrame:
    """Calculate the difference between theoretical and observed molecular weights.

    Parameters
    ----------
    matched_df: pd.DataFrame
        DataFrame of matched data (pre or post cleaning), should have two columns denoting the theoretical and observed
    molecular weights.
    theoretical_col: str
        Column name for theoretical molecular weight.
    observed_col: str
        Column name for observed molecular weight.
    split_on: str
        Character to split columns on, default ',' (comma).

    Returns
    -------
    pd.DataFrame
        Returns the dataframe it was passed augmented with a 'delta_ppm' column indicating the difference between the
    observed and theoretical molecular weight.
    """
    expanded_theoretical = matched_df[theoretical_col].str.split(split_on, expand=True)
    expanded_theoretical[0] = expanded_theoretical[0].fillna(matched_df[theoretical_col])
    expanded_theoretical = expanded_theoretical.astype("float")
    max_matches = len(expanded_theoretical.index)
    masses = pd.concat([matched_df[observed_col], expanded_theoretical], axis=1)
    for column in np.arange(0, max_matches):
        masses[f"ppm_{column}"] = (1000000 * (masses[column] - masses[observed_col])) / masses[column]
        masses.drop(column, axis=1)
    masses.drop(observed_col, axis=1, inplace=True)
    masses.drop(range(0, max_matches), axis=1, inplace=True)
    masses["delta_ppm"] = masses.apply(lambda row: ",".join(row.values.astype(str)), axis=1)

    return pd.concat([matched_df, masses["delta_ppm"].str.replace(".nan", "")], axis=1)
