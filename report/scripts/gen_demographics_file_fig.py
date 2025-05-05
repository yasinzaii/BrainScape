import json
import numpy
from pathlib import Path
import matplotlib.pyplot as plt

# To calculate the center of Age_Group bin.
def center_of_bin(start, end):
    return (start + end) / 2

# To find the best bin for a given subject.
def find_best_bin(dataset_bin_center, canonical_bins):
    """
    canonical_bins: list of (start, end) intervals.
    returns: The best (start, end) from canonical_bins for dataset_bin_center.
    """
    best_bin = None
    best_dist = float("inf")
    for (cstart, cend) in canonical_bins:
        c_center = center_of_bin(cstart, cend)
        dist = abs(dataset_bin_center - c_center)
        if dist < best_dist:
            best_dist = dist
            best_bin = (cstart, cend)
    return best_bin

# To convert bins as string to tuples
def convert_bin_string(bin_input):
    if isinstance(bin_input, str):
        start, end = bin_input.split('-')
        return (int(start), int(end))
    else:
        raise TypeError("Input must be a string or a list of strings")

def gen_demographics(data_dict, out_data_path, out_figure_path):

    datasets_mapping = data_dict["mapping"]
    
    # --------------------------------------------------------------------------
    # Initialize counters for each required variable
    # --------------------------------------------------------------------------
    
    # Race
    white_race_count = 0
    black_race_count = 0
    asian_race_count = 0
    american_indian_race_count = 0
    hawaiian_race_count = 0
    two_more_races_count = 0
    other_race_count = 0
    total_subjects_with_race = 0
    
    # Handedness
    left_handed_count = 0
    right_handed_count = 0
    ambi_handed_count = 0
    total_subjets_with_handedness = 0
    
    # Education
    low_edu_count = 0
    medium_edu_count = 0
    high_edu_count = 0
    total_subjects_with_education = 0
    
    # Socio-Economic
    low_econ_count = 0
    medium_econ_count = 0
    high_econ_count = 0
    total_subjects_with_economic = 0
    
    # Age, Age group, Sex
    total_age_agegroup_sex_count = 0
    total_subjects_with_age = 0
    total_subjects_with_agegroup = 0
    total_subjects_with_sex = 0
    
    age_vector_for_mean_std_age = []
    mean_age_value = 0.0
    std_dev_age_value = 0.0
    median_age_group = "0-0"  
    
    # Sex breakdown
    total_male_count = 0
    total_female_count = 0
    total_other_sex_count = 0
    total_sex_with_no_age = 0
    
    # BMI
    total_with_bmiinfo = 0
    
    # Total
    total_subjects_with_demographics = 0
    total_subjects_without_demographics = 0
    total_subjects_included_after_inspection = 0
    
    # Disorder Counters
    total_disorders_count = 0
    stroke_count = 0
    schizophrenia_count = 0
    depression_count = 0
    adhd_count = 0
    bipolar_count = 0
    prosopagnosia_count = 0
    epilepsy_count = 0
    tumor_count = 0
    acute_ischemic_stroke_count = 0
    fcd_count = 0
    hs_count = 0
    dnt_count = 0
    gl_count = 0
    aneurysm_count = 0

    
    # Age_group/Age sex Histogram
    canonical_bins = [
        ( 0,  5), (5,  10), (10, 15), (15, 20), (20, 25),
        (25, 30), (30, 35), (35, 40), (40, 45), (45, 50),
        (50, 55), (55, 60), (60, 65), (65, 70), (70, 75),
        (75, 80), (80, 85), (85, 90), (90, 95), (95, 100)
    ]

    # Initialize a dictionary to track frequencies per bin and per sex
    age_sex_bins = {}
    for (start, end) in canonical_bins:
        age_sex_bins[(start, end)] = {
            "male": 0,
            "female": 0,
            "other": 0,
            "n/a": 0
        }

    
    for dataset_name, entries in datasets_mapping.items():
        
        unique_participants = set() # to make sure subjects are not repeated
        
        for entry in entries:
            subject_id = entry.get("subject")
            
            # skip if subject is already processed.
            if subject_id in unique_participants:
                continue
            
            unique_participants.add(subject_id)
            total_subjects_included_after_inspection += 1
            
            
            demo = entry.get("demographics", {})
            
            if demo:
                # If there is any demographic info, increment total_subjects_with_demographics
                total_subjects_with_demographics += 1
            else:
                total_subjects_without_demographics += 1
                continue
            
            # RACE
            race_val = demo.get("race", None)
            if race_val and race_val != "n/a":
                total_subjects_with_race += 1
                if race_val == "1":
                    white_race_count += 1
                elif race_val == "2":
                    black_race_count += 1
                elif race_val == "3":
                    asian_race_count += 1
                elif race_val == "4":
                    american_indian_race_count += 1
                elif race_val == "5":
                    hawaiian_race_count += 1
                elif race_val == "7":
                    two_more_races_count += 1
                elif race_val == "8":
                    other_race_count += 1
                else:
                    print("Unexpected Race Value")
                
                
                
            # HANDEDNESS
            hand_val = demo.get("handedness", None)
            if hand_val and hand_val != "n/a":
                total_subjets_with_handedness += 1
                if hand_val == "L":
                    left_handed_count += 1
                elif hand_val == "R":
                    right_handed_count += 1
                elif hand_val == "A":
                    ambi_handed_count += 1
                else:
                    print("Unexpected handedness Value")
            
            # EDUCATION
            edu_val = demo.get("education", None)
            if edu_val and edu_val != "n/a":
                total_subjects_with_education += 1
                if edu_val == "low":
                    low_edu_count += 1
                elif edu_val == "medium":
                    medium_edu_count += 1
                elif edu_val == "high":
                    high_edu_count += 1
                else:
                    print("Unexpected education Value")
            
            # SOCIO-ECONOMIC
            econ_val = demo.get("socio_economic", None)
            if econ_val and econ_val != "n/a":
                total_subjects_with_economic += 1
                if econ_val == "low":
                    low_econ_count += 1
                elif econ_val == "medium":
                    medium_econ_count += 1
                elif econ_val == "high":
                    high_econ_count += 1
                else:
                    print("Unexpected socio_economic Value")
            
            # AGE, AGE_GROUP, SEX
            age_val = demo.get("age", None)
            if age_val and age_val != "n/a":
                total_subjects_with_age += 1
                age_vector_for_mean_std_age.append(float(age_val))
            
            age_group_val = demo.get("age_group", None)
            if age_group_val and age_group_val != "n/a":
                total_subjects_with_agegroup += 1
            
            sex_val = demo.get("sex", None)
            if sex_val and sex_val != "n/a":
                total_subjects_with_sex += 1
                if sex_val == "male":
                    total_male_count += 1
                elif sex_val == "female":
                    total_female_count += 1
                elif sex_val == "other":
                    total_other_sex_count += 1
                else:
                    print("Unexpected sex Value")
            
            # If there is sex value but no age value 
            if not (age_val or age_group_val) and sex_val: 
                total_sex_with_no_age += 1
            
            # If all both (age or age group) and sex info exists
            if (age_val or age_group_val) and sex_val: 
                total_age_agegroup_sex_count += 1
            
            # BMI
            if demo.get("BMI"):
                total_with_bmiinfo += 1
            
            
            # Age Sex Bins
            if (age_group_val and age_group_val != "n/a") or \
                    (age_val and age_val != "n/a"):

                if age_group_val:
                    subject_bin = convert_bin_string(age_group_val)
                    subject_bin_center = center_of_bin(subject_bin[0], subject_bin[1])
                elif age_val:
                    subject_bin_center = float(age_val)
                else:
                    print("Unexcepted value")
                    
                best_mapped_bin = find_best_bin(subject_bin_center, canonical_bins=canonical_bins)
                if sex_val and sex_val != "n/a":
                    age_sex_bins[best_mapped_bin][sex_val] += 1
                else:
                    age_sex_bins[best_mapped_bin]["n/a"] += 1
            
            

            # Counting individual disorders and total disorders
            has_disorder = False  
            for disorder_field in ["stroke", "schizophrenia", "depression", "ADHD", "BIPOLAR",
                       "prosopagnosia", "epilepsy", "tumor", "acuteischaemicstroke",
                       "FCD", "HS", "DNT", "GL", "aneurysm"]:

                if demo.get(disorder_field) == "Y":
                    has_disorder = True
                    if disorder_field == "stroke":
                        stroke_count += 1
                    elif disorder_field == "schizophrenia":
                        schizophrenia_count += 1
                    elif disorder_field == "depression":
                        depression_count += 1
                    elif disorder_field == "ADHD":
                        adhd_count += 1
                    elif disorder_field == "BIPOLAR":
                        bipolar_count += 1
                    elif disorder_field == "prosopagnosia":
                        prosopagnosia_count += 1
                    elif disorder_field == "epilepsy":
                        epilepsy_count += 1
                    elif disorder_field == "tumor":
                        tumor_count += 1
                    elif disorder_field == "acuteischaemicstroke":
                        acute_ischemic_stroke_count += 1
                    elif disorder_field == "FCD":
                        fcd_count += 1
                    elif disorder_field == "HS":
                        hs_count += 1
                    elif disorder_field == "DNT":
                        dnt_count += 1
                    elif disorder_field == "GL":
                        gl_count += 1
                    elif disorder_field == "aneurysm":
                        aneurysm_count += 1
            if has_disorder:
                total_disorders_count += 1
    
    
    # --------------------------------------------------------------------------
    #  Compute percentages - Mean - Std etc
    # --------------------------------------------------------------------------
    
    # For race:
    if total_subjects_with_race > 0:
        white_pct = 100.0 * white_race_count / total_subjects_with_race
        black_pct = 100.0 * black_race_count / total_subjects_with_race
        asian_pct = 100.0 * asian_race_count / total_subjects_with_race
        amind_pct = 100.0 * american_indian_race_count / total_subjects_with_race
        hawaiian_pct = 100.0 * hawaiian_race_count / total_subjects_with_race
        two_more_pct = 100.0 * two_more_races_count / total_subjects_with_race
        other_pct = 100.0 * other_race_count / total_subjects_with_race
    else:
        white_pct = black_pct = asian_pct = amind_pct = hawaiian_pct = two_more_pct = other_pct = 0.0
    
    # For handedness:
    if total_subjets_with_handedness > 0:
        left_hand_pct = 100.0 * left_handed_count / total_subjets_with_handedness
        right_hand_pct = 100.0 * right_handed_count / total_subjets_with_handedness
        ambi_hand_pct = 100.0 * ambi_handed_count / total_subjets_with_handedness
    else:
        left_hand_pct = right_hand_pct = ambi_hand_pct = 0.0
    
    # For education:
    if total_subjects_with_education > 0:
        low_edu_pct = 100.0 * low_edu_count / total_subjects_with_education
        medium_edu_pct = 100.0 * medium_edu_count / total_subjects_with_education
        high_edu_pct = 100.0 * high_edu_count / total_subjects_with_education
    else:
        low_edu_pct = medium_edu_pct = high_edu_pct = 0.0
    
    # For socio-economic:
    if total_subjects_with_economic > 0:
        low_econ_pct = 100.0 * low_econ_count / total_subjects_with_economic
        medium_econ_pct = 100.0 * medium_econ_count / total_subjects_with_economic
        high_econ_pct = 100.0 * high_econ_count / total_subjects_with_economic
    else:
        low_econ_pct = medium_econ_pct = high_econ_pct = 0.0
    
    
    # Mean and Std age values
    age_arr_numpy = numpy.array(age_vector_for_mean_std_age)
    mean_age_value = numpy.mean(age_arr_numpy)
    std_dev_age_value= numpy.std(age_arr_numpy)
    
    # Median Age Group
    total_freq = sum(sum(age_sex_bins[bin_].values()) for bin_ in canonical_bins) # 1) total frequency
    half_freq = total_freq / 2 
    cumulative_freq = 0
    median_bin = canonical_bins[0]
    for bin_ in canonical_bins:  
        bin_freq = sum(age_sex_bins[bin_].values())
        cumulative_freq += bin_freq
        if cumulative_freq >= half_freq:
            median_bin =  bin_
            break
    median_age_group = f"{median_bin[0]}-{median_bin[1]}"
    
    
    # --------------------------------------------------------------------------
    #  Generating Age/Age-Group and Sex histogram
    # --------------------------------------------------------------------------
    out_figure_path = Path(out_figure_path)
    
    bin_labels = [f"{start}-{end}" for (start, end) in canonical_bins]
    
    # Create lists for each sex category
    male_vals   = [age_sex_bins[(start, end)]["male"]   for (start, end) in canonical_bins]
    female_vals = [age_sex_bins[(start, end)]["female"] for (start, end) in canonical_bins]
    # Update - 'other' gender type was added beside sex  - In Publication we are reporting sex only 
    # Merging Other gender with n/a
    #other_vals  = [age_sex_bins[(start, end)]["other"]  for (start, end) in canonical_bins]
    na_vals     = [age_sex_bins[(start, end)]["n/a"] +  age_sex_bins[(start, end)]["other"]   for (start, end) in canonical_bins]
    
    plt.style.use('default')
    fig, ax = plt.subplots(figsize=(10, 6), facecolor='white')
    ax.set_facecolor('white')
    
    x_positions = range(len(canonical_bins))
    
    ax.bar(x_positions, male_vals, label="Male", color="blue") # First stack: male
    
    bottom_female = male_vals
    ax.bar(x_positions, female_vals, bottom=bottom_female, label="Female", color="red") # Second stack: female (goes on top of male)
    
    bottom_other = [m + f for m, f in zip(male_vals, female_vals)]
    #ax.bar(x_positions, other_vals, bottom=bottom_other, label="Other", color="green") # Third stack: other

    bottom_na = [m + f for m, f in zip(male_vals, female_vals)]
    #bottom_na = [mo + o for mo, o in zip(bottom_other, other_vals)]
    ax.bar(x_positions, na_vals, bottom=bottom_na, label="N/A", color="green") # Fourth stack: n/a
    
    ax.set_xticks(list(x_positions))
    ax.set_xticklabels(bin_labels, rotation=90, color='black') 
    
    ax.set_xlabel("Age Bin (years)", color='black')
    ax.set_ylabel("Number of Participants", color='black')
    ax.set_title("Age Range & Sex Distribution", color='black')
    
    ax.tick_params(axis='x', colors='black')
    ax.tick_params(axis='y', colors='black')
    
    ax.legend(loc="upper right")
    fig.tight_layout()
    
    
    fig.savefig(out_figure_path, dpi=300, facecolor=fig.get_facecolor(), edgecolor='none', transparent=False)
    plt.close(fig)

    print(f"Histogram saved to {out_figure_path}")
    
    # --------------------------------------------------------------------------
    # 4) Prepare lines for the .tex file
    # --------------------------------------------------------------------------
    
    content_lines = []
    
    # Race
    content_lines.append(r"\newcommand\TotalSubjectsWithWhiteRaceCount{" + f"{white_race_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithWhiteRacePercentage{" + f"{white_pct:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithBlackRaceCount{" + f"{black_race_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithBlackRacePercentage{" + f"{black_pct:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithAsianRaceCount{" + f"{asian_race_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithAsianRacePercentage{" + f"{asian_pct:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithAmericanIndianAlaskanRaceCount{" + f"{american_indian_race_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithAmericanIndianAlaskanRacePercentage{" + f"{amind_pct:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithHawaiianPacificIslanderRaceCount{" + f"{hawaiian_race_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithHawaiianPacificIslanderRacePercentage{" + f"{hawaiian_pct:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithTwoOrMoreRaceCount{" + f"{two_more_races_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithTwoOrMoreRacePercentage{" + f"{two_more_pct:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithOtherRaceCount{" + f"{other_race_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithOtherRacePercentage{" + f"{other_pct:.2f}" + "}")
    
    # Handedness
    content_lines.append(r"\newcommand\TotalSubjectsWithLeftHandednessCount{" + f"{left_handed_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithLeftHandednessPercentage{" + f"{left_hand_pct:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithRightHandednessCount{" + f"{right_handed_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithRightHandednessPercentage{" + f"{right_hand_pct:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithAmbidextrousHandednessCount{" + f"{ambi_handed_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithAmbidextrousHandednessPercentage{" + f"{ambi_hand_pct:.2f}" + "}")
    
    # Education
    content_lines.append(r"\newcommand\TotalSubjectsWithLowEducationCount{" + f"{low_edu_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithLowEducationPercentage{" + f"{low_edu_pct:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithMediumEducationCount{" + f"{medium_edu_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithMediumEducationPercentage{" + f"{medium_edu_pct:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithHighEducationCount{" + f"{high_edu_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithHighEducationPercentage{" + f"{high_edu_pct:.2f}" + "}")
    
    # Socio-Economic
    content_lines.append(r"\newcommand\TotalSubjectsWithLowEconomicCount{" + f"{low_econ_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithLowEconomicPercentage{" + f"{low_econ_pct:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithMediumEconomicCount{" + f"{medium_econ_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithMediumEconomicPercentage{" + f"{medium_econ_pct:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithHighEconomicCount{" + f"{high_econ_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithHighEconomicPercentage{" + f"{high_econ_pct:.2f}" + "}")
    
    # Age, Age-Group Sex.
    content_lines.append(r"\newcommand\TotalSubjectsWithAgeAgeGroupSexCount{" + f"{total_age_agegroup_sex_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsMeanAgeValue{" + f"{mean_age_value:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsStandardDevAgeValue{" + f"{std_dev_age_value:.2f}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsMedianAgeGroupValue{" + f"{median_age_group}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithSexCountWithoutAgeInfo{" + f"{total_sex_with_no_age}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithMaleSexCount{" + f"{total_male_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithFemaleCount{" + f"{total_female_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithMalePlusFemaleCount{" + f"{total_male_count+total_female_count}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithOtherSexCount{" + f"{total_other_sex_count}" + "}")
    
    content_lines.append(r"\newcommand\TotalSubjectsWithAgeCount{" + f"{total_subjects_with_age}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithAgeGroupCount{" + f"{total_subjects_with_agegroup}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithSexCount{" + f"{total_subjects_with_sex}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithHandednessCount{" + f"{total_subjets_with_handedness}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithRaceCount{" + f"{total_subjects_with_race}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithEducationCount{" + f"{total_subjects_with_education}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithSocioEconomicCount{" + f"{total_subjects_with_economic}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithBodyMassIndexCount{" + f"{total_with_bmiinfo}" + "}")
    
    content_lines.append(r"\newcommand\TotalSubjectsWithDemographicsInfoCount{" + f"{total_subjects_with_demographics}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsWithoutDemographicsInfoCount{" + f"{total_subjects_without_demographics}" + "}")
    content_lines.append(r"\newcommand\TotalSubjectsIncludedAfterInspectionCount{" + f"{total_subjects_included_after_inspection}" + "}")
    
    # Disorders
    content_lines.append(r"\newcommand\TotalSubjectsWithDisordersCount{" + f"{total_disorders_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithStrokeCount{" + f"{stroke_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithSchizophreniaCount{" + f"{schizophrenia_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithDepressionCount{" + f"{depression_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithADHDCount{" + f"{adhd_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithBIPOLARCount{" + f"{bipolar_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithProsopagnosiaCount{" + f"{prosopagnosia_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithEpilepsyCount{" + f"{epilepsy_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithTumorCount{" + f"{tumor_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithAcuteIschemicStrokeCount{" + f"{acute_ischemic_stroke_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithFCDCount{" + f"{fcd_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithHSCount{" + f"{hs_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithDNTCount{" + f"{dnt_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithGLCount{" + f"{gl_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithAneurysmCount{" + f"{aneurysm_count}" + "}")
    content_lines.append(r"\newcommand\SubjectsWithFocalEpilepsyCount{" + f"{fcd_count+hs_count}" + "}")
    
    
    
    # --------------------------------------------------------------------------
    # Write to 'demographics.tex'
    # --------------------------------------------------------------------------
    out_data_path = Path(out_data_path)
    out_data_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(out_data_path, 'wb') as f:
        f.write(("\n".join(content_lines) + "\n").encode('utf-8'))
    
    print(f"Demographics variables file successfully generated at {out_data_path}")
