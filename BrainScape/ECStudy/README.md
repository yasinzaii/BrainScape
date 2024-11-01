# ECStudy: Dataset Detail
Only the Anatomical T1W MRIs are extracted from this dataset.

## Original Dataset: The Energetic Costs of the Human Connectome
This dataset consists of quantitative FDG-PET, BOLD-fMRI, and DWI data from 20 right-handed, healthy individuals, 
acquired during rest on a Siemens Biograph mMR 3T PET-MR scanner from three independent cohorts.

### Dataset License
CCO

### Dataset URL
[OpenNeuro Dataset ds004513](https://openneuro.org/datasets/ds004513)

### Dataset Paper
[The energetic costs of the human connectome](https://www.science.org/doi/10.1126/sciadv.adi7632)


{
    "info": "Dataset Specific Settings",
    "isDownloaded": false,
    "downloader": "OpenNeuroDownloader",
    "isDatasetJsonCreated": false,
    "isPreprocessed": false,
    "datasetSource": "OpenNeuro",
    "includeDataset": true,
    "downloadFrom": "s3://openneuro.org/ds004513",
    "download": [
        "CHANGES",
        "README",
        "dataset_description.json",
        "participants.json",
        "participants.tsv",
        "sub-*/ses-*/anat/*"
    ],
    "mapping": {
        "plugin": "RegexMapper",
        "regex": {
            "subject": "^sub-.*$",
            "session": "^ses-.*$",
            "type": "^anat",
            "modality": {
                "t1w": "^.*T1w.nii.gz$"
            }
        },
        "includeSub": [
            "sub-s003",
            "sub-s007"
        ],
        "excludeSub": []
    },
    "other": {
        "participantId": "participant_id",
        "sessionId": "session_id",
        "age": "age",
        "gender": "sex",
        "handedness": "handedness",
        "weight": "body_weight ",
        "height": "body_height",
        "haematocrit": "haematocrit",
        "glucoseConcentration": "glucose_concentration"
    }
}
