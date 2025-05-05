Note: This README file is Auto Generated.

# Brain Tumor Segmentation (BraTS) Adult Glioma 2023 Challenge Dataset

## Description

**About Dataset:**

Ample multi-institutional routine clinically-acquired multi-parametric MRI (mpMRI) scans of glioma, are used as the training, validation, and testing data for this year’s BraTS challenge.

The training and validation data are the same that were used in BraTS'21; however, the testing dataset used in this year's challenge has been updated with many more routine clinically-acquired mpMRI scans. Ground truth annotations of the tumor sub-regions are created and approved by expert neuroradiologists for every subject included in the training, validation, and testing datasets to quantitatively evaluate the predicted tumor segmentations.

**Imaging Data Description:**

All BraTS mpMRI scans are available as NIfTI files (.nii.gz) and describe a) native (T1) and b) post-contrast T1-weighted (T1Gd), c) T2-weighted (T2), and d) T2 Fluid Attenuated Inversion Recovery (T2-FLAIR) volumes, and were acquired with different clinical protocols and various scanners from multiple data contributing institutions.

All the imaging datasets have been annotated manually, by one to four raters, following the same annotation protocol, and their annotations were approved by experienced neuro-radiologists. Annotations comprise the GD-enhancing tumor (ET — label 3), the peritumoral edematous/invaded tissue (ED — label 2), and the necrotic tumor core (NCR — label 1), as described in the latest BraTS summarizing paper. The ground truth data were created after their pre-processing, i.e., co-registered to the same anatomical template, interpolated to the same resolution (1 mm3) and skull-stripped.

**Avaliability:**

This plugin downloads the (BraTS) Adult Glioma 2023 Challenge Dataset via https://www.synapse.org/ however the dataset is also avaliable on Kaggle. 

Kaggle: https://www.kaggle.com/datasets/shakilrana/brats-2023-adult-glioma


## License

CC0

## Citation

Baid, U., Ghodasara, S., Mohan, S., Bilello, M., Calabrese, E., Colak, E., Farahani, K., Kalpathy-Cramer, J., Kitamura, F. C., Pati, S., & others. (2021). The rsna-asnr-miccai brats 2021 benchmark on brain tumor segmentation and radiogenomic classification. arXiv preprint arXiv:2107.02314.

## Download

https://www.synapse.org/Synapse:syn51156910/wiki/627000

## Dataset Statistics

| Statistic | Value |
| --- | --- |
| Number of Subjects | 1470 |
| Number of Sessions | 1470 |
| Total Number of MRIs | 7131 |
| Number of SEG MRIs | 1251 |
| Number of T1CE MRIs | 1470 |
| Number of T1W MRIs | 1470 |
| Number of T2W MRIs | 1470 |
| Number of FLAIR MRIs | 1470 |

