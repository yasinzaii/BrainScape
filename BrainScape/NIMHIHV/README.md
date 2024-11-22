The National Institute of Mental Health (NIMH) Intramural Healthy Volunteer Dataset



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


