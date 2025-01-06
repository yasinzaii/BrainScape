Note: This README file is Auto Generated.

# The NIMH intramural healthy volunteer dataset

## Description

Note: The Mapping Creates 2 Groups for some of the Subjects. 

The Second Group Just has an extra flair image. 

Note: Regex Mapper divides Data based on 
Sub -> Ses -> Type Which usually have their own directories. 

Then if there are 2 or more MRI of a modality falling in the same directory they are divided into group. 


For this particular dataset I want to ignore the second group.


This setting:

"mapFirstGroupOnly": true,

will only MAP first Group with group index 0. 


The remaining groups will be ignored.


## License

CC0

## Citation

Nugent, A. C., Thomas, A. G., Mahoney, M., Gibbons, A., Smith, J. T., Charles, A. J., Shaw, J. S., Stout, J. D., Namyst, A. M., Basavaraj, A., & others. (2022). The nimh intramural healthy volunteer dataset: a comprehensive meg, mri, and behavioral resource. Scientific Data, 9(1), 518.

## Download

https://openneuro.org/datasets/ds004215

## Dataset Statistics

| Statistic | Value |
| --- | --- |
| Number of Subjects | 247 |
| Number of Sessions | 250 |
| Total Number of MRIs | 737 |
| Number of FLAIR MRIs | 241 |
| Number of T2W MRIs | 247 |
| Number of T1W MRIs | 249 |

